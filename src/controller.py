from src.index import *
import src.utils.MathMethod as MathMethod
import logging
from src.utils.CallbackRegister import CallbackRegistry

class Controller:
    """
    Контроллер для расчёта параметров газопровода (диаметр, скорость, давление, расход).

    Отвечает за:
    - выбор сценария расчёта (по диаметру или скорости);
    - сбор данных из интерфейса (через `sel_ragulator`);
    - вызов математических методов;
    - обработку ошибок и передачу сообщений в интерфейс.
    """

    def __init__(self, sel_ragulator,callback: CallbackRegistry) -> None:
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

    def _register_callbacks(self):
        """Register all application callbacks with the callback registry."""
        print("Зарегестрировали функцию")
        self.callback.register("make_calculation", self.make_calculation)

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

    def __calculate_tube_diameter(
        self,
        pressure: float,
        speed: float,
        auto_speed: bool,
        gas_consumption: float
    ) -> float | None:
        """
        Обобщённый метод расчёта диаметра трубопровода.

        Args:
            pressure: давление газа на участке (МПа).
            speed: скорость газа (м/с). Если `auto_speed=True`, может быть переопределена.
            auto_speed: флаг автоматического выбора скорости по давлению.
            gas_consumption: расход газа (м³/ч).

        Returns:
            Рассчитанный диаметр в мм или None при ошибке.


        Raises:
            ValueError: если входные строки не конвертируются в float.
            ZeroDivisionError: если в расчёте возникает деление на ноль.
        """
        try:
            # Проверка обязательных параметров
            if not gas_consumption or not pressure:
                self.logger.warning("Отсутствие расхода или давления — расчёт диаметра прерван")
                return None

            # Конвертация давления: МПа → кПа
            gas_pressure_kpa = float(pressure) * 1000

            # Автовыбор скорости по давлению (если включено)
            if auto_speed:
                if gas_pressure_kpa < 50:
                    speed = 15.0
                elif 50 <= gas_pressure_kpa <= 600:
                    speed = 25.0
                else:
                    speed = 30.0

            # Проверка скорости
            if speed <= 0:
                msg = "Ошибка: скорость газа должна быть > 0."
                self.logger.error(msg)
                self.sel_ragulator.show_error(msg)
                return None

            self.logger.debug(
                "Вызов математического метода расчёта диаметра. "
                "Параметры: gas_consumption=%.2f м³/ч, pressure=%.2f МПа, speed=%.2f м/с",
                gas_consumption, pressure, speed
            )

            # Чистый расчёт (внешняя функция)
            diameter_mm = MathMethod.calculated_diametr(
                gas_consumption=gas_consumption,
                gas_pressure=gas_pressure_kpa,
                gas_speed=speed
            )

            if diameter_mm is None:
                msg = "Ошибка расчёта диаметра: недопустимые входные данные."
                self.logger.error(msg)
                self.sel_ragulator.show_error(msg)
                return None

            rounded_result = round(diameter_mm, 2)
            self.logger.info("Расчётный диаметр: %.2f мм", rounded_result)
            return rounded_result

        except ValueError as e:
            msg = f"Ошибка: неверный формат числа. Проверьте ввод. ({e})"
            self.logger.error(msg)
            self.sel_ragulator.show_error(msg)
            return None
        except ZeroDivisionError:
            msg = "Ошибка: деление на ноль в расчёте диаметра."
            self.logger.error(msg)
            self.sel_ragulator.show_error(msg)
            return None
        except Exception as e:
            msg = f"Неизвестная ошибка при расчёте диаметра: {str(e)}"
            self.logger.exception(msg)  # exception → с трассировкой
            self.sel_ragulator.show_error(msg)
            return None

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

            # Проверка на None перед логированием
            if gas_consumption is None:
                self.logger.warning("gas_consumption равен None для %s", io_type)
                gas_consumption = 0.0  # или пропустите логирование

            # Безопасное логирование: используем %r для потенциально None-значений
            self.logger.debug(
                "Параметры для расчёта диаметра (%s): pressure=%.2f МПа, speed=%.2f м/с, "
                "gas_consumption=%r м³/ч, auto_speed=%s",
                io_type, pressure, speed, gas_consumption, auto_speed
            )

            calculated_diameter = self.__calculate_tube_diameter(
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

        except Exception as e:
            msg = f"Ошибка при расчёте диаметра для {io_type}: {str(e)}"
            self.logger.exception(msg)
            self.sel_ragulator.show_error(msg)

    def calculate_gas_speed(self, gas_pressure: float, diameter: float, gas_consumption: float ) -> float | None:
        """
        Обобщённый метод расчёта скорости газа.

        Args:
            gas_pressure: давление газа (МПа).
            diameter: диаметр трубопровода (мм).
            gas_consumption: расход газа (м³/ч).

        Returns:
            Скорость газа в м/с или None при ошибке.

        Raises:
            ValueError: ошибка конвертации типов.
            ZeroDivisionError: деление на ноль в формуле.
        """
        try:
            # Проверка обязательных параметров
            if not gas_consumption or not gas_pressure or not diameter:
                self.logger.warning("Отсутствие одного из параметров — расчёт скорости прерван")
                return None

            if gas_consumption <= 0 or diameter <= 0:
                msg = "Расход и диаметр должны быть > 0."
                self.logger.error(msg)
                self.sel_ragulator.show_error(msg)
                return None

            # Конвертация давления: МПа → кПа
            gas_pressure_kpa = gas_pressure * 1000

            self.logger.debug(
                "Вызов математического метода расчёта скорости. "
                "Параметры: gas_consumption=%.2f м³/ч, gas_pressure=%.2f МПа (%.1f кПа), diameter=%.1f мм",
                gas_consumption, gas_pressure, gas_pressure_kpa, diameter
            )

            # Чистый расчёт (внешняя функция)
            speed_ms = MathMethod.calculate_speed(
                gas_consumption=gas_consumption,
                gas_pressure_kpa=gas_pressure_kpa,
                diameter_mm=diameter
            )

            if speed_ms is None:
                msg = "Ошибка расчёта скорости: недопустимые входные данные."
                self.logger.error(msg)
                self.sel_ragulator.show_error(msg)
                return None

            rounded_result = round(speed_ms, 2)
            self.logger.info("Расчётная скорость: %.2f м/с", rounded_result)
            return rounded_result

        except ValueError as e:
            msg = f"Ошибка: неверный формат числа. Проверьте ввод. ({e})"
            self.logger.error(msg)
            self.sel_ragulator.show_error(msg)
            return None
        except ZeroDivisionError:
            msg = "Ошибка: деление на ноль в расчёте скорости."
            self.logger.error(msg)
            self.sel_ragulator.show_error(msg)
            return None
        except Exception as e:
            msg = f"Неизвестная ошибка при расчёте скорости: {str(e)}"
            self.logger.exception(msg)  # exception → с трассировкой
            self.sel_ragulator.show_error(msg)
            return None

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

            calculated_speed = self.calculate_gas_speed(
                gas_pressure=pressure,
                diameter=diameter,
                gas_consumption=gas_consumption
            )

            if calculated_speed is not None:
                self.logger.info("Полученная скорость для %s: %.2f м/с", io_type, calculated_speed)
                self.sel_ragulator.set_speed(io_type, calculated_speed)
            else:
                self.logger.warning("Расчёт скорости для %s не удался", io_type)


        except Exception as e:
            msg = f"Ошибка при расчёте скорости для {io_type}: {str(e)}"
            self.logger.exception(msg)
            self.sel_ragulator.show_error(msg)

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

    def search_file_name(self):
        """
            Формирует номенклатурную строку изделия (например, ГРПШ_РДНК-50-400(1000)_1-1_0_4_0_0_У1_0_1_50-50_Л-П)
            на основе словаря self.gas_equipment_config.
            """

        # ПРОВЕРКА: Проверка наличия и заполненности словаря
        if not hasattr(self, 'gas_equipment_config') or not self.gas_equipment_config:
            # В случае ошибки возвращаем пустую строку
            return ""

        # Получаем конфигурацию
        config: Dict[str, Any] = self.gas_equipment_config

        # -----------------------------------------------------------
        # 2.1. Расчетные и фиксированные части
        # -----------------------------------------------------------

        # ВАЖНО: Модель регулятора (например, РДНК-50-400(1000)) должна быть определена
        # в другом месте (после подбора) и сохранена, например, в self.regulator_model_name.
        regulator_part = "РДНК-50-400(1000)"

        # -----------------------------------------------------------
        # 2.2. Преобразование значений из словаря в кодовые части
        # -----------------------------------------------------------

        # 1. Тип изделия: ГРПШ
        product_type = str(config.get("Тип изделия", ""))

        # 2. Блок линий: 1-1_0 (рабочие-резервные_съемная)
        working_lines = str(config.get("Количество рабочих линий", 0))
        reserve_lines = str(config.get("Количество резервных линий", 0))
        removable_reserve = str(config.get("Наличие съемной резервной линии", 0))
        lines_block = f"{working_lines}-{reserve_lines}_{removable_reserve}"

        # 3. Исполнение по СТО: 4
        sto_gprg_full = str(config.get("Исполнение по СТО ГПРГ", "0"))


        # 4. Обогрев: 0
        heating_value = str(config.get("Обогрев", "0"))

        # 5. Телеметрия: 0
        telemetry_value = str(config.get("Телеметрия", "0"))

        # 6. Климатическое исполнение: У1
        climate_code = str(config.get("Климатическое исполнение", "У1"))

        # 7. Оснащение УИРГ: 0
        uirg_equipment_full = str(config.get("Оснащение УИРГ", "0"))

        # 8. Количество выходов: 1
        gas_outputs = str(config.get("Количество выходов газопроводов", 1))

        # 9. Диаметры: 50-50
        valve_diameter_in = str(config.get("Диаметр запорной арматуры на входе", "НД"))
        valve_diameter_out = str(config.get("Диаметр запорной арматуры на выходе", "НД"))
        diameters_block = f"{valve_diameter_in}-{valve_diameter_out}"

        # 10. Направление: Л-П
        direction_value = str(config.get("Направление", "Л-П"))

        # -----------------------------------------------------------
        # 3. Сборка финальной строки в нужной последовательности
        # -----------------------------------------------------------

        parts = [
            product_type,
            regulator_part,
            lines_block,
            sto_gprg_full,
            heating_value,
            telemetry_value,
            climate_code,
            uirg_equipment_full,
            gas_outputs,
            diameters_block,
            direction_value
        ]

        # Объединяем все части через разделитель "_"
        print("_".join(map(str, parts)))
        stri = "_".join(map(str, parts))

        selected_product = stri.split("_")[0]
        regulator = (stri.split("_")[1]).split("-")[0]
        print(selected_product, regulator)



        # 1. Объединение частей пути с помощью оператора /
        # Python сам поставит нужный разделитель: '\' для Windows или '/' для Linux/Mac.
        folder = "Каталог"
        sub_folder = selected_product
        sub_sub_folder = regulator
        file_name = stri + ".cdw"

        file_path = Path(folder) / sub_folder /sub_sub_folder/ file_name

        print(f"Путь: {file_path}")

        # 2. Объединение с текущим рабочим каталогом
        full_path = Path.cwd() / file_path
        print(f"Полный путь: {full_path}")

        current_text = self.ui.plainTextEdit_2.toPlainText()
        new_text = current_text + "\n" + self.__split_and_insert_newline(str(full_path))
        self.ui.plainTextEdit_2.setPlainText(new_text)
        if full_path.exists():

            print(f"Путь существует: {full_path}")

        else:
            print(f"Путь не существует: {full_path}")