from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from src.utils import MathMethod


class Model:

    def __init__(self):
        self.logger = logging.getLogger("App.Model")
        self.logger.info("Модуль модели запустился")



    def build_scheme_filepath(self, gas_equipment_config: dict,regulator:str) -> str:
        """
            Формирует номенклатурную строку изделия (например, ГРПШ_РДНК-50-400(1000)_1-1_0_4_0_0_У1_0_1_50-50_Л-П)
            на основе словаря конифигурации gas_equipment_config.
        """

        # # ПРОВЕРКА: Проверка наличия и заполненности словаря
        # if not hasattr(self, 'gas_equipment_config') or not self.gas_equipment_config:
        #     # В случае ошибки возвращаем пустую строку
        #     return ""

        # Получаем конфигурацию
        config: Dict[str, Any] = gas_equipment_config

        # -----------------------------------------------------------
        # 2.1. Расчетные и фиксированные части
        # -----------------------------------------------------------

        # ВАЖНО: Модель регулятора (например, РДНК-50-400(1000)) должна быть определена
        # в другом месте (после подбора) и сохранена, например, в self.regulator_model_name.
        # regulator_part = "РДНК-50-400(1000)"
        regulator_part = regulator

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

        return "_".join(parts)

    def parse_scheme_filename(self, filename: str) -> dict:
        """Парсит имя файла и возвращает структуру."""
        parts = filename.split("_")
        print(f"{parts=}")
        if len(parts) < 11:
            raise ValueError("Некорректный формат имени файла")

        return {
            "product_type": parts[0],
            "regulator_model": parts[1],
            "regulator_base": parts[1].split("-")[0],  # например, "РДНК"
            "full_name": filename
        }

    def find_scheme_file(self,parse_file_name: Dict[str, List[str]]) -> Optional[str]:
        # 1. Объединение частей пути с помощью оператора /
        # Python сам поставит нужный разделитель: '\' для Windows или '/' для Linux/Mac.
        folder = "Каталог"
        sub_folder = parse_file_name["product_type"]
        sub_sub_folder = parse_file_name["regulator_base"]
        file_name = parse_file_name["full_name"] + ".cdw"

        file_path = Path(folder) / sub_folder / sub_sub_folder / file_name

        print(f"Путь: {file_path}")

        # 2. Объединение с текущим рабочим каталогом
        full_path = Path.cwd() / file_path
        print(f"Полный путь: {full_path}")

        if full_path.exists():

            print(f"Путь существует: {full_path}")
            return full_path

        else:
            print(f"Путь не существует: {full_path}")
            return None

    def calculate_tube_diameter(
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
                raise ValueError("Отсутствие расхода или давления — расчёт диаметра прерван")

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
                raise ValueError("Ошибка: скорость газа должна быть > 0.")

            # Чистый расчёт (внешняя функция)
            diameter_mm = MathMethod.calculated_diametr(
                gas_consumption=gas_consumption,
                gas_pressure=gas_pressure_kpa,
                gas_speed=speed
            )

            if diameter_mm is None:
                raise ValueError("Ошибка расчёта диаметра: недопустимые входные данные. ")

            rounded_result = round(diameter_mm, 2)
            return rounded_result

        except ZeroDivisionError:
            raise ZeroDivisionError("Ошибка: деление на ноль в расчёте диаметра.")

        except Exception as e:
            raise Exception(f"Неизвестная ошибка при расчёте диаметра: {str(e)}")

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
                raise ValueError("Отсутствие одного из параметров — расчёт скорости прерван")

            if gas_consumption <= 0 or diameter <= 0:
                raise ValueError("Расход и диаметр должны быть > 0.")

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
                raise ValueError("Ошибка расчёта скорости: недопустимые входные данные.")

            rounded_result = round(speed_ms, 2)
            self.logger.info("Расчётная скорость: %.2f м/с", rounded_result)
            return rounded_result

        except ZeroDivisionError:
            raise ZeroDivisionError("Ошибка: деление на ноль в расчёте скорости.")

        except Exception as e:
            raise Exception("Неизвестная ошибка при расчёте скорости: {str(e)}")
