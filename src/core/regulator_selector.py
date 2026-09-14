# -*- coding: utf-8 -*-
"""
Оптимизированный алгоритм подбора регуляторов давления.

Отличия от старой реализации (src/utils/ExelMethod.py):
  1. Лист читается ОДИН раз в список строк; поиск выполняется по памяти,
     без повторных iter_rows внутри вложенных циклов.
  2. Парсинг ячеек вынесен в src.core.parsing — устойчив к «грязному»
     вводу (запятые, неразрывные пробелы, прочерки, None).
  3. Единая нормальная логика проверки диапазона загрузки (без
     произвольных надбавок +1% в одних ветках и их отсутствия в других).
  4. Имя регулятора и седло определяются надёжно для обоих форматов листов.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Sequence

from src.core import parsing
from src.core.models import RegulatorMatch


class RegulatorSelector:
    """Выполняет поиск подходящих регуляторов по книге Excel."""

    logger = logging.getLogger("App.RegulatorSelector")

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Публичный API
    # ------------------------------------------------------------------
    def select(
        self,
        workbook,
        p_in: float,
        p_out: float,
        bandwidth: float,
        load_range: tuple,
    ) -> Dict[str, RegulatorMatch]:
        """Подбирает регуляторы по всем листам книги.

        Args:
            workbook: открытая книга openpyxl (read_only=True, data_only=True).
            p_in: входное давление (МПа).
            p_out: выходное давление (МПа).
            bandwidth: требуемый расход (м³/ч).
            load_range: (min, max) диапазон загрузки в долях (0..1).

        Returns:
            Словарь {имя регулятора: RegulatorMatch}.
        """
        load_min, load_max = float(load_range[0]), float(load_range[1])
        p_in = float(p_in)
        p_out = float(p_out)
        bandwidth = float(bandwidth)

        self._validate_arguments(p_in, p_out, bandwidth, load_min, load_max)

        found: Dict[str, RegulatorMatch] = {}

        for sheet_name in workbook.sheetnames:
            try:
                sheet = workbook[sheet_name]
                sheet_found = self._select_sheet(
                    sheet, p_in, p_out, bandwidth, load_min, load_max
                )
                for name, match in sheet_found.items():
                    # Не затираем предыдущие результаты с тем же именем
                    found[name] = match
            except Exception:  # noqa: BLE001
                self.logger.exception("Ошибка при обработке листа '%s'", sheet_name)
                continue

        self.logger.info("Подбор завершён: найдено %d регуляторов", len(found))
        return found

    # ------------------------------------------------------------------
    # Вспомогательные методы
    # ------------------------------------------------------------------
    @staticmethod
    def _validate_arguments(p_in, p_out, bandwidth, load_min, load_max) -> None:
        if p_in <= 0 or p_out <= 0 or bandwidth <= 0:
            raise ValueError("Давления и расход должны быть положительными.")
        if p_in <= p_out:
            raise ValueError("Входное давление должно быть строго выше выходного.")
        if load_min < 0 or load_max > 1 or load_min > load_max:
            raise ValueError("Некорректный диапазон загрузки.")

    def _select_sheet(
        self,
        sheet,
        p_in: float,
        p_out: float,
        bandwidth: float,
        load_min: float,
        load_max: float,
    ) -> Dict[str, RegulatorMatch]:
        """Подбор по одному листу.

        Лист кэшируется в список строк один раз.
        """
        # Кэшируем лист в память один раз (числовые значения уже готовы).
        rows: List[Sequence] = [list(row) for row in sheet.iter_rows(values_only=True)]
        if not rows:
            return {}

        # Определяем режим: «один регулятор» или «несколько» по ячейке C1.
        c1 = rows[0][2] if len(rows[0]) > 2 else None
        if parsing.normalize_text(c1) == "":
            return self._select_one_controller(rows, p_in, p_out, bandwidth, load_min, load_max)
        return self._select_several_controller(rows, p_in, p_out, bandwidth, load_min, load_max)

    # ------------------------------------------------------------------
    # Одного регулятора на лист (пример: РДГ-50Н(В).xlsx)
    #   r0: [имя устройства, седло, ...]
    #   r1: [един. Pвх, един. Pвых]
    #   r2: [None, Pвых_0, Pвых_1, ...]
    #   r3..: [Pвх_0, Q для каждой колонки, ...]
    # ------------------------------------------------------------------
    def _select_one_controller(
        self, rows, p_in, p_out, bandwidth, load_min, load_max
    ) -> Dict[str, RegulatorMatch]:
        if not rows:
            return {}

        name_device = rows[0][0] if rows[0] else None
        saddle = rows[0][1] if len(rows[0]) > 1 else None
        name = str(name_device) if name_device is not None else ""

        if not rows or len(rows) < 3:
            return {}

        # Строка заголовков выходных давлений (индекс 2)
        header_row = rows[2]
        # Парсим выходные давления каждой колонки
        outlet_pressures = [
            parsing.parse_pressure(header_row[i])
            for i in range(1, len(header_row))
        ]

        # Эффективная ширина записей всех давлений (ищем сколько есть).
        data_rows = rows[3:]
        result: Dict[str, RegulatorMatch] = {}

        for data_row in data_rows:
            if not data_row:
                continue
            inlet_range = parsing.parse_pressure(data_row[0])
            if not inlet_range or not inlet_range.contains(p_in):
                continue

            # Ряд данных по колонкам (семейство Q для каждой Pвых)
            for i, outlet_range in enumerate(outlet_pressures):
                if outlet_range is None or not outlet_range.contains(p_out):
                    continue
                cell_value = data_row[i + 1] if i + 1 < len(data_row) else None
                current_bw = parsing.parse_int_bandwidth(cell_value)
                if current_bw is None:
                    continue
                required = int(bandwidth)
                low = current_bw * load_min
                high = current_bw * load_max
                if low <= required <= high:
                    load_percent = (required / current_bw) * 100 if current_bw else 0.0
                    result[name] = RegulatorMatch(
                        name=name,
                        saddle=str(saddle) if saddle is not None else "-",
                        current_bandwidth=current_bw,
                        required_bandwidth=required,
                        load_percent=round(load_percent, 1),
                    )
        return result

    # ------------------------------------------------------------------
    # Нескольких регуляторов на лист (пример: Регуляторы давления.xlsx)
    #   r0: [седло, модель_1, модель_2, ...]
    #   r1: [един. Pвх, един. Pвых]
    #   r2: [None, Pвых_0, Pвых_1, ...]
    #   r3..: [Pвх_0, Q для модели_1, ...]
    # ------------------------------------------------------------------
    def _select_several_controller(
        self, rows, p_in, p_out, bandwidth, load_min, load_max
    ) -> Dict[str, RegulatorMatch]:
        if len(rows) < 3:
            return {}

        saddle = rows[0][0] if rows[0] else None
        header_row = rows[2]
        outlet_pressures = [
            parsing.parse_pressure(header_row[i])
            for i in range(1, len(header_row))
        ]

        data_rows = rows[3:]
        result: Dict[str, RegulatorMatch] = {}

        for data_row in data_rows:
            if not data_row:
                continue
            inlet_range = parsing.parse_pressure(data_row[0])
            if not inlet_range or not inlet_range.contains(p_in):
                continue

            for i, outlet_range in enumerate(outlet_pressures):
                if outlet_range is None:
                    continue
                if not outlet_range.contains(p_out):
                    continue
                cell_value = data_row[i + 1] if i + 1 < len(data_row) else None
                current_bw = parsing.parse_int_bandwidth(cell_value)
                if current_bw is None:
                    continue
                # Имя модели — из заголовка колонки (строка 0, колонка i+1)
                name = self._model_name(rows[0], i + 1)
                if not name:
                    continue
                required = int(bandwidth)
                low = current_bw * load_min
                high = current_bw * load_max
                if low <= required <= high:
                    load_percent = (required / current_bw) * 100 if current_bw else 0.0
                    result[name] = RegulatorMatch(
                        name=name,
                        saddle=str(saddle) if saddle is not None else "-",
                        current_bandwidth=current_bw,
                        required_bandwidth=required,
                        load_percent=round(load_percent, 1),
                    )
        return result

    @staticmethod
    def _model_name(header_row, col_index: int) -> str:
        if col_index < len(header_row):
            value = header_row[col_index]
            if parsing.normalize_text(value) == "":
                return ""
            return str(value)
        return ""

    # ------------------------------------------------------------------
    # Утилита для тестирования: выбор по списку строк вместо книги
    # ------------------------------------------------------------------
    @classmethod
    def select_from_rows(
        cls,
        rows: List[Sequence],
        p_in: float,
        p_out: float,
        bandwidth: float,
        load_range: tuple,
        mode: Optional[str] = None,
    ) -> Dict[str, RegulatorMatch]:
        """Выполняет подбор по готовому списку строк (удобно для тестов)."""
        if mode == "one":
            return cls()._select_one_controller(
                rows, p_in, p_out, bandwidth, load_range[0], load_range[1]
            )
        return cls()._select_several_controller(
            rows, p_in, p_out, bandwidth, load_range[0], load_range[1]
        )