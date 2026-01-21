from typing import List

from src.FoundCorValue import FoundCorValue
from src.GUI.SelRegulator import *
import logging

from src.MyLogger import FileWriter
from src.utils.CallbackRegister import CallbackRegistry
from src.utils.ExelMethod import ExelMethod
from src.Model import Model


class Controller:
    """
    Контроллер для расчёта параметров газопровода (диаметр, скорость, давление, расход).

    Отвечает за:
    - выбор сценария расчёта (по диаметру или скорости);
    - сбор данных из интерфейса (через `sel_regulator`);
    - вызов математических методов;
    - обработку ошибок и передачу сообщений в интерфейс.
    """

    def __init__(self, sel_regulator:SelRegulator,callback: CallbackRegistry,excel:ExelMethod,model:Model) -> None:
        """
        Инициализирует контроллер.

        Args:
            sel_regulator: объект интерфейса/модели, предоставляющий:
                - get_pressure(ioType)
                - get_speed(ioType)
                - get_diameter(ioType)
                - get_bandwidth()
                - set_valve_diametr(ioType, value)
                - set_speed(ioType, value)
                - show_error(message)
        """
        # Контроллер запущен
        self.sel_regulator = sel_regulator
        self.logger = logging.getLogger("App.Controller")
        self.logger.info("Главный контроллер запущен")
        self.callback = callback
        self._register_callbacks()
        self.excel = excel
        self.model = model

    def _register_callbacks(self):
        """Register all application callbacks with the callback registry."""
        # Функции зарегистрированы
        self.callback.register("make_calculation", self.make_calculation)
        self.callback.register("replacement_button_pressed", self.replacement_button_pressed)
        self.callback.register("search_sheme",self.search_sheme)
        self.callback.register("auto_calculate_trigger",self.auto_calculate_trigger)

    def auto_calculate_trigger(self) -> None:
        """Проверяет наличие всех данных и запускает расчет без вывода ошибок."""
        try:
            # Пробуем получить данные. Если в полях пусто или буквы - get_pressure вернет 0 или выкинет ошибку
            p_in = self.sel_regulator.get_pressure("Input")
            # Получено входное давление

            if self.sel_regulator.get_auto_speed_checked("In") and p_in>0:
                speed = self.model.speed_selection(p_in)
                # Получена скорость
                self.sel_regulator.set_speed("Input",speed)
                # Скорость установлена
            p_out = self.sel_regulator.get_pressure("Output")
            # Получено выходное давление

            if self.sel_regulator.get_auto_speed_checked("Out") and p_out>0:
                speed = self.model.speed_selection(p_out)
                # Получена скорость
                self.sel_regulator.set_speed("Output",speed)

            consumption = self.sel_regulator.get_bandwidth()

            # Если все три значения получены (больше нуля)
            if p_in > 0 and p_out > 0 and consumption > 0:
                # Блокируем логирование или уведомления, если нужно, и считаем
                # Запуск расчета
                self.make_calculation()
        except Exception:
            # Просто игнорируем любые ошибки ввода, пока пользователь печатает
            pass


    def make_calculation(self) -> None:
        """
        Основной метод запуска расчёта.

        В зависимости от значения `self.speed_or_diametr` выполняет:
        - расчёт диаметра для входа и выхода (если "diametr");
        - расчёт скорости для входа и выхода (иначе).

        Примечание:
            `self.speed_or_diametr` должен быть установлен извне до вызова метода.
        """
        # Начало расчета
        if self.sel_regulator.speed_or_diametr == "diametr":
            self.logger.info("Запуск расчёта диаметра для входа")
            self.calculated_diameter("Input")
            self.logger.info("Запуск расчёта диаметра для выхода")
            self.calculated_diameter("Output")
        else:
            # Начало расчета скорости
            self.logger.info("Запуск расчёта скорости газа")
            self.calculate_speed("Input")
            self.calculate_speed("Output")

    def calculated_diameter(self, io_type: str) -> None:
        """
        Слот для расчёта диаметра трубопровода по заданным параметрам.

        Собирает данные из интерфейса и вызывает расчёт.

        Args:
            io_type: "Input" или "Output" — направление потока.
        """
        # Сбор данных для расчета диаметра
        self.logger.info("Начало расчёта диаметра для %s", io_type)

        try:
            pressure = self.sel_regulator.get_pressure(io_type)
            speed = self.sel_regulator.get_speed(io_type)
            gas_consumption = self.sel_regulator.get_bandwidth()
            auto_speed = False

            # Безопасное логирование: используем %r для потенциально None-значений
            self.logger.debug(
                "Параметры для расчёта диаметра (%s): pressure=%.3f МПа, speed=%.2f м/с, "
                "gas_consumption=%r м³/ч, auto_speed=%s",
                io_type, pressure, speed, gas_consumption, auto_speed
            )

            calculated_diameter = self.model.calculate_tube_diameter(
                pressure=pressure,
                speed=speed,
                auto_speed=auto_speed,
                gas_consumption=gas_consumption
            )

            if calculated_diameter is not None:
                self.logger.info("Полученный диаметр для %s: %.2f мм", io_type, calculated_diameter)
                self.sel_regulator.set_valve_diameter_calc(io_type, calculated_diameter)
            else:
                self.logger.warning("Расчёт диаметра для %s не удался", io_type)

        except ValueError as e:
            self.logger.exception(e)
            self.sel_regulator.show_error(e)

        except Exception as e:
            msg = f"Ошибка при расчёте диаметра для {io_type}: {str(e)}"
            self.logger.exception(msg)
            self.sel_regulator.show_error(msg)

    def calculate_speed(self, io_type: str) -> None:
        """
        Слот для расчёта скорости газа по диаметру трубопровода.

        Собирает данные из интерфейса и запускает расчёт скорости.


        Args:
            io_type: "Input" или "Output" — направление потока.
        """
        self.logger.info("Начало расчёта скорости для трубы %s", io_type)

        try:
            pressure = self.sel_regulator.get_pressure(io_type)
            diameter = self.sel_regulator.get_valve_diameter_calc(io_type)
            gas_consumption = self.sel_regulator.get_bandwidth()

            self.logger.debug(
                "Параметры для расчёта скорости (%s): "
                "pressure=%.2f МПа, diameter=%.1f мм, gas_consumption=%.2f м³/ч",
                io_type, pressure, diameter, gas_consumption
            )

            calculated_speed = self.model.calculate_gas_speed(
                gas_pressure=pressure,
                diameter=diameter,
                gas_consumption=gas_consumption
            )

            if calculated_speed is not None:
                self.logger.info("Полученная скорость для %s: %.2f м/с", io_type, calculated_speed)
                self.sel_regulator.set_speed(io_type, calculated_speed)
            else:
                self.logger.warning("Расчёт скорости для %s не удался", io_type)

        except ValueError as e:
            self.logger.exception(e)
            self.sel_regulator.show_error(e)
        except Exception as e:
            msg = f"Ошибка при расчёте скорости для {io_type}: {str(e)}"
            self.logger.exception(msg)
            self.sel_regulator.show_error(msg)

    def __validate_input_parameters(self)-> tuple[float, float, float]:
        """
        Сбор данных из GUI и запуск валидации в модели.
        """
        try:
            PIn = self.sel_regulator.get_pressure("Input")
            POt = self.sel_regulator.get_pressure("Output")
            bandwidth = self.sel_regulator.get_bandwidth()

            # ВАЖНО: Вызов валидации из Модели
            self.model.validate_engineering_parameters(PIn, POt, bandwidth)

            return PIn, POt, bandwidth
        except ValueError as e:
            raise e # Пробрасываем инженерную ошибку выше
        except Exception as e:
            self.logger.error("Ошибка получения параметров из GUI: %s", str(e))
            raise ValueError("Убедитесь, что все поля заполнены корректно.")

    def replacement_button_pressed(self) -> None:
        """
        Главный метод подбора регулятора.
        """
        self.logger.info("Начинаем подбор регулятора")

        # 1. Получение и логирование путей
        file_paths = self.sel_regulator.drop_area.get_file_paths()
        self.logger.info("Получили список файлов из drop_area: %s", file_paths)

        # 3. Фильтрация Excel-файлов
        excel_files = self.excel.filter_excel_file(file_paths)  # исправлена опечатка в имени
        self.logger.info("Отфильтрованы Excel-файлы: %s", excel_files)

        if not excel_files:
            self.sel_regulator.show_error_message("Добавьте файлы с расширением .xlsx")
            self.logger.warning("Нет Excel-файлов для обработки")
            return

        # 2. Валидация (Интерфейс + Модель)
        try:
            PIn, POt, bandwidth = self.__validate_input_parameters()
            min_load, max_load = self.sel_regulator.get_loading_range()
            load_range = (min_load / 100, max_load / 100) # Переводим в проценты
        except ValueError as e:
            self.sel_regulator.show_error_message(str(e))
            return

        # 7. Обработка каждого файла
        # Обработка файлов
        total_regulators_found = 0
        self.sel_regulator.show_info_message("Поиск подходящего регулятора запущен")
        for path_file in excel_files:
            if not path_file.strip():  # защита от пустых строк
                continue

            try:

                self.logger.info("Открываем Excel-файл: %s", path_file)


                workbook = openpyxl.load_workbook(os.path.normpath(path_file), read_only=True, data_only=True)

                # --- Анализ одного файла ---
                # Анализ файла
                found:Dict[str,Dict[str,int]] = self.excel.conduct_analysis(workbook, PIn, POt, bandwidth,load_range)

                if len(found) == 0:
                    self.logger.warning("Точное совпадение не найдено в файле %s. Ищем ближайшие значения.", path_file)
                    finder = FoundCorValue(workbook, PIn, POt)
                    PIn_adj, POt_adj = finder()
                    found = self.excel.conduct_analysis(workbook, PIn_adj, POt_adj, bandwidth,load_range)


                total_regulators_found = len(found)
                self.logger.info("В файле %s найдено %d регуляторов", path_file, len(found))

            except Exception as e:
                error_msg = f"Ошибка при обработке файла: {os.path.basename(path_file)}"
                self.sel_regulator.show_error_message(error_msg)
                self.logger.exception("Критическая ошибка при анализе файла %s: %s", path_file,e)


        # 8. Финализация
        # Поиск завершен
        self.sel_regulator.show_found_regulators(found)
        self.sel_regulator.update_status_worck("Ожидание работы")
        self.logger.info("Подбор завершён. Всего найдено регуляторов: %d", total_regulators_found)

        # Опционально: показать итоговое сообщение
        if total_regulators_found == 0:
            self.sel_regulator.show_info_message("Подходящие регуляторы не найдены.")
        else:
            self.sel_regulator.show_info_message(f"Найдено {total_regulators_found} подходящих регуляторов.")

    def search_sheme(self):
        """
        Метод для поиска и отображения схем выбранных регуляторов.
        """
        self.logger.info("Запущен процесс поиска схем")

        # 1. Очистка старых результатов
        self.sel_regulator.delete_block_result("ShemesLayout")

        try:
            # 2. Получение данных из View
            regulators: List[str] = self.sel_regulator.get_selected_regulators()

            if not regulators:
                self.logger.warning("Список регуляторов пуст. Поиск отменен.")
                self.sel_regulator.show_info_message("Выберите хотя бы один регулятор из списка результатов.")
                return

            gas_equipment_config = self.sel_regulator.select_product_type()
            self.logger.debug(f"Конфигурация оборудования получена: {gas_equipment_config}")

            # 3. Основной цикл поиска
            for regulator in regulators:
                try:
                    self.logger.info(f"Обработка регулятора: {regulator}")

                    # Формируем имя файла и ищем его через Модель
                    filename = self.model.build_scheme_filepath(gas_equipment_config, regulator)
                    parse_data = self.model.parse_scheme_filename(filename)
                    full_path = self.model.find_scheme_file(parse_data)

                    if full_path:
                        self.logger.info(f"Схема найдена: {full_path}")
                        # Передаем во View только данные, а не HTML-строку!
                        self.sel_regulator.show_shemas(
                            regulator_name=regulator,
                            scheme_name=parse_data.get("full_name", "Неизвестно"),
                            file_path=os.path.abspath(full_path),
                            found=True
                        )
                    else:
                        self.logger.warning(f"Файл схемы для {regulator} не найден на диске")
                        self.sel_regulator.show_shemas(
                            regulator_name=regulator,
                            scheme_name=parse_data.get("full_name", "Неизвестно"),
                            file_path=None,
                            found=False
                        )

                except Exception as e:
                    # Логируем ошибку конкретного регулятора, чтобы цикл не прервался
                    self.logger.error(f"Ошибка при обработке регулятора {regulator}: {e}", exc_info=True)
                    self.sel_regulator.show_error(f"Ошибка при поиске схемы для {regulator}")

        except Exception as e:
            # Критическая ошибка (например, сбой получения списка или конфигурации)
            self.logger.critical(f"Критическая ошибка в методе search_sheme: {e}", exc_info=True)
            self.sel_regulator.show_error("Произошла системная ошибка при подборе схем")

        self.logger.info("Поиск схем завершен")

if __name__ == "__main__":

    pass



























