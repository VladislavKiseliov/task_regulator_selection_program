from typing import List

from src.GUI.SelRegulator import *
import logging
from src.utils.CallbackRegister import CallbackRegistry
from src.utils.ExelMethod import ExelMethod
from src.Model import Model


class Controller:
    """
    Контроллер для расчёта параметров газопровода (диаметр, скорость, давление, расход).

    Отвечает за:
    - выбор сценария расчёта (по диаметру или скорости);
    - сбор данных из интерфейса (через `sel_ragulator`);
    - вызов математических методов;
    - обработку ошибок и передачу сообщений в интерфейс.
    """

    def __init__(self, sel_ragulator,callback: CallbackRegistry,excel:ExelMethod,model:Model) -> None:
        """
        Инициализирует контроллер.

        Args:
            sel_ragulator: объект интерфейса/модели, предоставляющий:
                - get_pressure(ioType)
                - get_speed(ioType)
                - get_diameter(ioType)
                - get_bandwidth()
                - set_valve_diametr(ioType, value)
                - set_speed(ioType, value)
                - show_error(message)
        """
        print("контролер запущен")
        self.sel_ragulator = sel_ragulator
        self.logger = logging.getLogger("App.Controller")
        self.logger.info("Главный контроллер запущен")
        self.callback = callback
        self._register_callbacks()
        self.excel = excel
        self.model = model

    def _register_callbacks(self):
        """Register all application callbacks with the callback registry."""
        print("Зарегестрировали функцию")
        self.callback.register("make_calculation", self.make_calculation)
        self.callback.register("replacement_button_pressed", self.replacement_button_pressed)
        self.callback.register("search_sheme",self.search_sheme)

    def make_calculation(self) -> None:
        """
        Основной метод запуска расчёта.

        В зависимости от значения `self.speed_or_diametr` выполняет:
        - расчёт диаметра для входа и выхода (если "diametr");
        - расчёт скорости для входа и выхода (иначе).

        Примечание:
            `self.speed_or_diametr` должен быть установлен извне до вызова метода.
        """
        print("Начали рассчет")
        if self.sel_ragulator.speed_or_diametr == "diametr":
            self.logger.info("Запуск расчёта диаметра для входа")
            self.calculated_diameter("Input")
            self.logger.info("Запуск расчёта диаметра для выхода")
            self.calculated_diameter("Output")
        else:
            print("Начали рассчет скорости ")
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
        print("Собираем данные для расчета диаметра")
        self.logger.info("Начало расчёта диаметра для %s", io_type)

        try:
            pressure = self.sel_ragulator.get_pressure(io_type)
            speed = self.sel_ragulator.get_speed(io_type)
            gas_consumption = self.sel_ragulator.get_bandwidth()
            auto_speed = False

            # Безопасное логирование: используем %r для потенциально None-значений
            self.logger.debug(
                "Параметры для расчёта диаметра (%s): pressure=%.2f МПа, speed=%.2f м/с, "
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
                self.sel_ragulator.set_valve_diametr(io_type, calculated_diameter)
            else:
                self.logger.warning("Расчёт диаметра для %s не удался", io_type)

        except ValueError as e:
            self.logger.exception(e)
            self.sel_ragulator.show_error(e)

        except Exception as e:
            msg = f"Ошибка при расчёте диаметра для {io_type}: {str(e)}"
            self.logger.exception(msg)
            self.sel_ragulator.show_error(msg)

    def calculate_speed(self, io_type: str) -> None:
        """
        Слот для расчёта скорости газа по диаметру трубопровода.

        Собирает данные из интерфейса и запускает расчёт скорости.


        Args:
            io_type: "Input" или "Output" — направление потока.
        """
        self.logger.info("Начало расчёта скорости для трубы %s", io_type)

        try:
            pressure = self.sel_ragulator.get_pressure(io_type)
            diameter = self.sel_ragulator.get_valve_diameter(io_type)
            gas_consumption = self.sel_ragulator.get_bandwidth()

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
                self.sel_ragulator.set_speed(io_type, calculated_speed)
            else:
                self.logger.warning("Расчёт скорости для %s не удался", io_type)

        except ValueError as e:
            self.logger.exception(e)
            self.sel_ragulator.show_error(e)
        except Exception as e:
            msg = f"Ошибка при расчёте скорости для {io_type}: {str(e)}"
            self.logger.exception(msg)
            self.sel_ragulator.show_error(msg)

    def __validate_input_parameters(self)-> tuple[float, float, float]:
        """
            Валидация входных данных для дальнейшего использования
            Надо дописать исключения в методах получения данных с гуи
        """
        try:
            PIn = self.sel_ragulator.get_pressure("Input")
            POt = self.sel_ragulator.get_pressure("Output")
            bandwidth = self.sel_ragulator.get_bandwidth()
            return PIn,POt,bandwidth

        except Exception as e:
            self.sel_ragulator.show_error_message("Введите корректные значения для поиска регулятора")
            self.logger.error("Ошибка получения входных параметров: %s", str(e))
            return

    def replacement_button_pressed(self) -> None:
        """
        Главный метод подбора регулятора.
        """
        self.logger.info("Начинаем подбор регулятора")

        # 1. Получение и логирование путей
        file_paths = self.sel_ragulator.drop_area.get_file_paths()
        self.logger.info("Получили список файлов из drop_area: %s", file_paths)

        # 3. Фильтрация Excel-файлов
        excel_files = self.excel.filter_excel_file(file_paths)  # исправлена опечатка в имени
        self.logger.info("Отфильтрованы Excel-файлы: %s", excel_files)

        if not excel_files:
            self.sel_ragulator.show_error_message("Добавьте файлы с расширением .xlsx")
            self.logger.warning("Нет Excel-файлов для обработки")
            return

        # 4. Валидация ВСЕХ входных параметров (общих для всех файлов)
        try:
            min_load, max_load = self.sel_ragulator.get_loading_range() # Получаем диапазон загрузки
            print(min_load, max_load)
            PIn, POt, bandwidth = self.__validate_input_parameters()
            print(PIn,POt,bandwidth)
            self.logger.info("Входные данные получены")

        except ValueError as e:
            self.sel_ragulator.show_error_message(str(e))
            self.logger.error("Ошибка валидации входных данных: %s", e)
            return

        # 5. Подготовка UI
        # self.__clear_widget_res_in_app()
        # self.update_status_worck("В работе")
        # self.logger.info("Виджет результатов очищен, статус: 'В работе'")

        # 6. Сохранение конфигурации поиска (если нужно)
        # self.__saved_conf_search()

        # 7. Обработка каждого файла
        print("Шаг 7 ")
        total_regulators_found = 0

        for path_file in excel_files:
            if not path_file.strip():  # защита от пустых строк
                continue

            try:
                # self.__save_patch_in_conf(path_file)
                # self.logger.info("Сохранён путь к файлу в конфиг: %s", path_file)

                self.sel_ragulator.show_info_message("Поиск подходящего регулятора запущен")
                self.logger.info("Открываем Excel-файл: %s", path_file)

                workbook = openpyxl.load_workbook(os.path.normpath(path_file), read_only=True, data_only=True)

                # --- Анализ одного файла ---
                print(f"Запуск одного фпйла {workbook} {PIn} {POt} {bandwidth}")
                found:Dict[str,Dict[str,int]] = self.conduct_analysis(workbook, PIn, POt, bandwidth)

                if len(found) == 0:
                    self.logger.warning("Точное совпадение не найдено в файле %s. Ищем ближайшие значения.", path_file)
                    finder = FoundCorValue(workbook, PIn, POt)
                    PIn_adj, POt_adj = finder()
                    found = self.conduct_analysis(workbook, PIn_adj, POt_adj, bandwidth)

                total_regulators_found = len(found)
                self.logger.info("В файле %s найдено %d регуляторов", path_file, len(found))

            except Exception as e:
                error_msg = f"Ошибка при обработке файла: {os.path.basename(path_file)}"
                self.sel_ragulator.show_error_message(error_msg)
                self.logger.exception("Критическая ошибка при анализе файла %s: %s", path_file,e)

        # 8. Финализация
        print("инал поиска")
        self.sel_ragulator.show_found_regulators(found)
        self.sel_ragulator.update_status_worck("Ожидание работы")
        self.logger.info("Подбор завершён. Всего найдено регуляторов: %d", total_regulators_found)

        # Опционально: показать итоговое сообщение
        if total_regulators_found == 0:
            self.sel_ragulator.show_info_message("Подходящие регуляторы не найдены.")
        else:
            self.sel_ragulator.show_info_message(f"Найдено {total_regulators_found} подходящих регуляторов.")

    def conduct_analysis(self, workbook: str,
                         inlet_pressure: float,
                         output_pressure: float,
                         traffic_capacity: float) -> int:
        """Функция conduct_analysis, распарсивает экселевский файл
        и ищет подходящие ячейки по входным данным.
        Возвращает колличество найденных девайсов в файле."""
        self.logger.info("Начинаем анализ Excel-файла: %s", workbook)
        self.logger.debug("Доступные листы в книге: %s", workbook.sheetnames)
        print(f"Параметры для поиска  {inlet_pressure} {output_pressure} {traffic_capacity}")
        regulators_found = {}
        print(f"{workbook.sheetnames=}")

        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            self.logger.debug("Обрабатываем лист: %s", sheet_name)
            print(f"{sheet=}")

            try:
                # Проверяем признак типа таблицы в ячейке C1
                c1_value = sheet["C1"].value
                self.logger.debug("Значение в C1 на листе %s: %r", sheet_name, c1_value)

                if c1_value is None or c1_value == "":
                    self.logger.info("Лист %s: обнаружен формат «один регулятор на лист»", sheet_name)
                    found :Dict[str,Dict[str,int]]= self.excel.search_one_controller_table_algorithm(inlet_pressure, output_pressure, traffic_capacity, sheet)
                    regulators_found.update(found)
                    self.logger.debug("На листе %s найдено регуляторов: %d", sheet_name, len(found))
                else:
                    self.logger.info("Лист %s: обнаружен формат «несколько регуляторов на лист»", sheet_name)
                    found:Dict[str,Dict[str,int]] = self.excel.search_several_controller_table_algorithm(inlet_pressure, output_pressure, traffic_capacity, sheet)
                    regulators_found.update(found)
                    self.logger.debug("На листе %s найдено регуляторов: %d", sheet_name, len(found))

            except Exception as e:
                self.logger.error(
                    "Ошибка при обработке листа %s: %s",
                    sheet_name, str(e), exc_info=True
                )
                continue  # Пропускаем лист при ошибке

        self.logger.info(
            "Анализ файла %s завершён. Найдено подходящих регуляторов: %d",
            workbook, len(regulators_found)
        )
        return regulators_found




    def search_sheme(self):
        self.sel_ragulator.delete_block_result("ShemesLayout")
        regulators: List[str]= self.sel_ragulator.get_selected_regulators()
        print(f"{regulators=}")
        gas_equipment_config = self.sel_ragulator.select_product_type()
        print(" Выозов сборщика имени")
        for regulator in regulators:
            filename = self.model.build_scheme_filepath(gas_equipment_config,regulator)
            parse_file_name : dict = self.model.parse_scheme_filename(filename)
            full_path = self.model.find_scheme_file(parse_file_name)
            print(f"{full_path=}")
            if full_path is not None:
                print("Вставка что нашли")
                message = (f"<b>Результаты подбора схемы для ргеулятора {regulator}:</b><br>"
                           f"Схема {parse_file_name["full_name"]}"
                           f"Полный путь:"
                           f'<a href="file:///{os.path.abspath(full_path)}">{full_path}</a>')
                self.sel_ragulator.show_shemas(message)
            else:
                print("Вставка что не  нашли")
                message = (f"<b>Результаты подбора схемы для ргеулятора {regulator}:</b><br>"
                           f"Схемы {parse_file_name["full_name"]}"
                           f"Полного пути не сущетсвует")
                self.sel_ragulator.show_shemas(message)

            #Вывод ошибки


if __name__ == "__main__":

    pass































    def select_product_type(self) -> None:
        """
        Метод для обработки выбора типа изделия (ГРПБ, ГРПШ, ГРУ).
        Собирает данные о выбранном типе изделия и сохраняет их.
        """
        print(1)
        # # Получаем выбранный тип изделия из комбо-бокса
        selected_product = self.ui.comboBox_product_type.currentText()
        # #
        # # # Сохраняем информацию о выбранном типе изделия
        self.selected_product_type = selected_product
        #
        # # Собираем дополнительную информацию о конфигурации газового оборудования
        gas_equipment_config = {
            "Тип изделия": selected_product,
            "Количество рабочих линий": self.get_count_work_line(),
            "Количество резервных линий": self.get_backup_lines(),
            "Наличие съемной резервной линии": self.get_removable_backup_line(),
            "Исполнение по СТО ГПРГ": self.get_sto_gprg_execution(),
            "Обогрев": self.get_heating_type(),
            "Телеметрия": self.get_telemetry_type(),
            "Климатическое исполнение": self.get_climate_execution(),
            "Оснащение УИРГ": self.get_uirg_equipment_type(),
            "Количество выходов газопроводов": self.get_number_of_gas_pipeline_outlets(),
            "Диаметр запорной арматуры на входе": self.get_valve_diameter("Input"),
            "Диаметр запорной арматуры на выходе": self.get_valve_diameter("Output"),
            "Направление": self.get_direction_type()
        }

        # # Сохраняем всю конфигурацию
        self.gas_equipment_config = gas_equipment_config
        #
        # # Выводим сообщение в строке состояния
        # self.ui.statusbar.showMessage(f"Выбран тип изделия: {selected_product}", 3000)

        print(f"{gas_equipment_config=}")
        self.search_file_name()

        # Здесь можно добавить дополнительную логику обработки выбранного типа изделия
        # Например, изменение интерфейса в зависимости от выбранного типа

    # def search_file_name(self):
    #
    #
    #
    #
    #     # 1. Объединение частей пути с помощью оператора /
    #     # Python сам поставит нужный разделитель: '\' для Windows или '/' для Linux/Mac.
    #     folder = "Каталог"
    #     sub_folder = selected_product
    #     sub_sub_folder = regulator
    #     file_name = stri + ".cdw"
    #
    #     file_path = Path(folder) / sub_folder /sub_sub_folder/ file_name
    #
    #     print(f"Путь: {file_path}")
    #
    #     # 2. Объединение с текущим рабочим каталогом
    #     full_path = Path.cwd() / file_path
    #     print(f"Полный путь: {full_path}")
    #
    #     current_text = self.ui.plainTextEdit_2.toPlainText()
    #     new_text = current_text + "\n" + self.__split_and_insert_newline(str(full_path))
    #     self.ui.plainTextEdit_2.setPlainText(new_text)
    #     if full_path.exists():
    #
    #         print(f"Путь существует: {full_path}")
    #
    #     else:
    #         print(f"Путь не существует: {full_path}")