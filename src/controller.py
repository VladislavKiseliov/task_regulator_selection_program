# -*- coding: utf-8 -*-
"""
Контроллер приложения.

Связывает View (SelRegulator) с чистыми сервисами ядра (src.core).
Основной прогресс против старой версии:
  - подбор регуляторов выполняется накопленно по всем файлам (раньше
    использовался результат только последнего файла);
  - алгоритмы вынесены в src.core (быстрее и надёжнее);
  - подбор ближайших давлений (NearestValues) — детерминированный.
"""
from __future__ import annotations

import logging
import os
from typing import Dict, List, Optional, Tuple

from src.core.models import RegulatorMatch, SelectorResult, SchemeSearchConfig
from src.core.nearest_values import NearestValues
from src.core.regulator_selector import RegulatorSelector
from src.core import calculator
from src.core.cache import get_global_cache
from src.core.workbook import read_workbook_fast
from src.core.scheme_finder import SchemeFinder
from src.utils.worker import BackgroundWorker


class Controller:
    """Контроллер для подбора регуляторов, инженерных расчётов и поиска схем."""

    def __init__(self, sel_regulator, callback, excel, model) -> None:
        self.sel_regulator = sel_regulator
        self.logger = logging.getLogger("App.Controller")
        self.logger.info("Главный контроллер запущен")
        self.callback = callback
        self._register_callbacks()

        # Сервисы ядра
        self.selector = RegulatorSelector()
        self.nearest = NearestValues()
        self.scheme_finder = SchemeFinder(catalog_root="Каталог")
        self._cache = get_global_cache()

        # Совместимость: переданы из точки входа, но напрямую не используются
        # (логика перенесена в src.core).
        self._excel_legacy = excel
        self._model_legacy = model

        # Активный фоновый поток (защищает от повторного запуска/гонок).
        self._worker: Optional[BackgroundWorker] = None
        self._busy = False

    def _register_callbacks(self) -> None:
        """Регистрирует все колбэки приложения."""
        self.callback.register("make_calculation", self.make_calculation)
        self.callback.register("replacement_button_pressed", self.replacement_button_pressed)
        self.callback.register("search_sheme", self.search_sheme)
        self.callback.register("auto_calculate_trigger", self.auto_calculate_trigger)

    # ==================================================================
    # Автовычисление при вводе
    # ==================================================================
    def auto_calculate_trigger(self) -> None:
        """Проверяет наличие всех данных и запускает расчёт без вывода ошибок."""
        try:
            p_in = self.sel_regulator.get_pressure("Input")
            if self.sel_regulator.get_auto_speed_checked("In") and p_in > 0:
                self.sel_regulator.set_speed("Input", calculator.select_speed(p_in))
            p_out = self.sel_regulator.get_pressure("Output")
            if self.sel_regulator.get_auto_speed_checked("Out") and p_out > 0:
                self.sel_regulator.set_speed("Output", calculator.select_speed(p_out))
            consumption = self.sel_regulator.get_bandwidth()
            if p_in > 0 and p_out > 0 and consumption > 0:
                self.make_calculation()
        except Exception:
            # Игнорируем ошибки ввода, пока пользователь заполняет поля
            pass

    # ==================================================================
    # Инженерные расчёты (диаметр / скорость)
    # ==================================================================
    def make_calculation(self) -> None:
        """Запускает расчёт диаметра или скорости в зависимости от режима."""
        mode = getattr(self.sel_regulator, "speed_or_diametr", "diametr")
        if mode == "diametr":
            self.calculated_diameter("Input")
            self.calculated_diameter("Output")
        else:
            self.calculate_speed("Input")
            self.calculate_speed("Output")

    def calculated_diameter(self, io_type: str) -> None:
        """Расчёт диаметра трубопровода по введённым параметрам."""
        self.logger.info("Начало расчёта диаметра для %s", io_type)
        try:
            pressure = self.sel_regulator.get_pressure(io_type)
            speed = self.sel_regulator.get_speed(io_type)
            consumption = self.sel_regulator.get_bandwidth()
            if pressure <= 0 or speed <= 0 or consumption <= 0:
                return
            diameter = calculator.calculated_diameter(
                gas_consumption=consumption,
                gas_pressure_kpa=pressure * 1000,
                gas_speed=speed,
            )
            if diameter is not None:
                self.sel_regulator.set_valve_diameter_calc(io_type, diameter)
        except Exception as e:  # noqa: BLE001
            self.logger.exception("Ошибка расчёта диаметра %s", io_type)
            self.sel_regulator.show_error(str(e))

    def calculate_speed(self, io_type: str) -> None:
        """Расчёт скорости газа по диаметру."""
        self.logger.info("Начало расчёта скорости для %s", io_type)
        try:
            pressure = self.sel_regulator.get_pressure(io_type)
            diameter = self.sel_regulator.get_valve_diameter_calc(io_type)
            consumption = self.sel_regulator.get_bandwidth()
            if pressure <= 0 or diameter <= 0 or consumption <= 0:
                return
            speed = calculator.calculate_speed(
                gas_consumption=consumption,
                gas_pressure_kpa=pressure * 1000,
                diameter_mm=diameter,
            )
            if speed is not None:
                self.sel_regulator.set_speed(io_type, speed)
        except Exception as e:  # noqa: BLE001
            self.logger.exception("Ошибка расчёта скорости %s", io_type)
            self.sel_regulator.show_error(str(e))

    # ==================================================================
    # Подбор регулятора
    # ==================================================================
    def __validate_input_parameters(self) -> Tuple[float, float, float]:
        """Собирает и валидирует входные параметры из интерфейса."""
        p_in = self.sel_regulator.get_pressure("Input")
        p_out = self.sel_regulator.get_pressure("Output")
        bandwidth = self.sel_regulator.get_bandwidth()
        if p_in <= 0 or p_out <= 0 or bandwidth <= 0:
            raise ValueError("Введите положительные значения давления и расхода.")
        if p_in <= p_out:
            raise ValueError(
                "Входное давление (Pвх) должно быть строго выше выходного (Pвых)."
            )
        return p_in, p_out, bandwidth

    def replacement_button_pressed(self) -> None:
        """Главный метод подбора регулятора (кнопка «Подобрать регулятор»).

        Выполняется в фоновом потоке, чтобы не блокировать интерфейс.
        """
        if self._busy:
            self.sel_regulator.show_info_message("Подбор уже выполняется, подождите.")
            return

        self.logger.info("Начинаем подбор регулятора")

        # 1. Пути к файлам + фильтр .xlsx
        file_paths = self.sel_regulator.drop_area.get_file_paths()
        excel_files = [
            p for p in file_paths if os.path.splitext(p)[1].lower() == ".xlsx"
        ]
        self.logger.info("Excel-файлы для обработки: %s", excel_files)
        if not excel_files:
            self.sel_regulator.show_error_message("Добавьте файлы с расширением .xlsx")
            return

        # 2. Валидация параметров (на главном потоке)
        try:
            p_in, p_out, bandwidth = self.__validate_input_parameters()
            min_load, max_load = self.sel_regulator.get_loading_range()
            load_range = (min_load / 100, max_load / 100)
        except ValueError as e:
            self.sel_regulator.show_error_message(str(e))
            return

        self.sel_regulator.show_info_message("Поиск подходящего регулятора запущен")
        self.sel_regulator.update_status_worck("В работе")

        # 3. Тяжёлую работу выполняем в фоне.
        self._busy = True
        self._worker = BackgroundWorker(
            self._select_from_files,
            excel_files, p_in, p_out, bandwidth, load_range,
            on_success=lambda result: self._on_selection_done(
                result, p_in, p_out, bandwidth
            ),
            on_failure=self._on_selection_failed,
        )
        self._worker.finished.connect(self._worker_done)
        self._worker.failed.connect(self._worker_done)
        self._worker.start()

    def _worker_done(self, *args) -> None:
        """Очистка флагов занятости после завершения фоновой задачи."""
        self._busy = False
        self._worker = None
        self.sel_regulator.update_status_worck("Ожидание работы")

    def _select_from_files(
        self,
        excel_files: List[str],
        p_in: float,
        p_out: float,
        bandwidth: float,
        load_range: Tuple[float, float],
    ) -> SelectorResult:
        """Чистая функция: читает файлы (через кэш) и накапливает результат."""
        result = SelectorResult()
        for path_file in excel_files:
            if not path_file.strip():
                continue
            normalized = os.path.normpath(path_file)
            # 1) Кэш результата подбора для этих параметров.
            cache_key = (
                "select", normalized, round(p_in, 6), round(p_out, 6),
                int(bandwidth), tuple(round(v, 4) for v in load_range),
            )
            cached = self._cache.get_selection(cache_key)
            if cached is not None:
                result.merge_file(cached)
                result.source_files += 1
                self.logger.info("Кэш %s: %d регуляторов", normalized, len(cached))
                continue

            # 2) Разобранная книга (pandas/openpyxl, с кэшем по сигнатуре).
            workbook = read_workbook_fast(normalized, cache=self._cache)
            found = self.selector.select(workbook, p_in, p_out, bandwidth, load_range)
            if len(found) == 0:
                p_in_adj, p_out_adj = self.nearest.find(workbook, p_in, p_out)
                found = self.selector.select(
                    workbook, p_in_adj, p_out_adj, bandwidth, load_range
                )
            self._cache.put_selection(cache_key, found)
            result.merge_file(found)
            result.source_files += 1
            self.logger.info("Обработан %s: +%d регуляторов", path_file, len(found))
        return result

    def _on_selection_done(
        self,
        result: SelectorResult,
        p_in: float,
        p_out: float,
        bandwidth: float,
    ) -> None:
        """Отображение результатов подбора (в главном потоке)."""
        # View ожидает словарь {имя: {...}} — конвертируем dataclass.
        regulators_view = {
            name: match.as_dict for name, match in result.regulators.items()
        }
        self.sel_regulator.show_found_regulators(
            regulators_view,
            inlet=p_in,
            outlet=p_out,
            capacity=bandwidth,
        )
        if result.count == 0:
            self.sel_regulator.show_info_message("Подходящие регуляторы не найдены.")
        else:
            self.sel_regulator.show_info_message(
                f"Найдено {result.count} подходящих регуляторов."
            )

    def _on_selection_failed(self, error_text: str) -> None:
        """Обработка сбоя фонового подбора (в главном потоке)."""
        self.logger.error("Критическая ошибка при анализе файлов: %s", error_text)
        self.sel_regulator.show_error_message(f"Ошибка при обработке файла: {error_text}")

    # ==================================================================
    # Поиск схем
    # ==================================================================
    def search_sheme(self) -> None:
        """Поиск и отображение схем выбранных регуляторов (в фоне)."""
        if self._busy:
            self.sel_regulator.show_info_message("Поиск схем уже выполняется, подождите.")
            return

        self.logger.info("Запущен процесс поиска схем")
        self.sel_regulator.delete_block_result("ShemesLayout")

        try:
            regulators: List[str] = self.sel_regulator.get_selected_regulators()
            if not regulators:
                self.sel_regulator.show_info_message(
                    "Выберите хотя бы один регулятор из списка результатов."
                )
                return

            gas_equipment_config = self.sel_regulator.select_product_type()
            self.logger.debug(
                "Конфигурация оборудования: %s", gas_equipment_config
            )
        except Exception as e:  # noqa: BLE001
            self.logger.critical("Критическая ошибка в search_sheme", exc_info=True)
            self.sel_regulator.show_error(
                "Произошла системная ошибка при подборе схем"
            )
            return

        self.sel_regulator.update_status_worck("В работе")
        self._busy = True
        self._worker = BackgroundWorker(
            self._find_schemes,
            regulators, gas_equipment_config,
            on_success=self._on_schemes_done,
            on_failure=self._on_schemes_failed,
        )
        self._worker.finished.connect(self._worker_done)
        self._worker.failed.connect(self._worker_done)
        self._worker.start()

    def _find_schemes(
        self, regulators: List[str], gas_equipment_config: Dict[str, object]
    ) -> List[SchemeSearchResult]:
        """Чистая функция: находит схему для каждого регулятора (без UI)."""
        results: List[SchemeSearchResult] = []
        for regulator in regulators:
            try:
                config = SchemeSearchConfig.from_config_dict(
                    {**gas_equipment_config, "Регулятор": regulator}
                )
                scheme = self.scheme_finder.search(regulator, config)
                results.append(scheme)
            except Exception as e:  # noqa: BLE001
                self.logger.exception("Ошибка регулятора %s", regulator)
                results.append(
                    SchemeSearchResult(
                        regulator_name=regulator,
                        scheme_name="",
                        file_path=None,
                        found=False,
                    )
                )
        return results

    def _on_schemes_done(self, results: List[SchemeSearchResult]) -> None:
        """Отрисовка найденных схем (в главном потоке)."""
        for scheme in results:
            self.sel_regulator.show_shemas(
                regulator_name=scheme.regulator_name,
                scheme_name=scheme.scheme_name,
                file_path=scheme.file_path,
                found=scheme.found,
            )

    def _on_schemes_failed(self, error_text: str) -> None:
        """Обработка сбоя фонового поиска схем (в главном потоке)."""
        self.logger.error("Ошибка фонового поиска схем: %s", error_text)
        self.sel_regulator.show_error(
            f"Произошла системная ошибка при подборе схем: {error_text}"
        )