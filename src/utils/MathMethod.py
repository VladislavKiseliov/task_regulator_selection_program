import math


def calculated_diametr(gas_consumption:float, gas_pressure:float, gas_speed:float) -> float:
    """
    Выполняет фактический расчет диаметра газопровода по формуле.

    gas_pressure_kpa: давление в кПа (МПа * 1000)
    """
    # Формула: D = 0.036238 * sqrt(Q * 293 / (0.1 + P_mpa) / V) * 10
    result = (0.036238) * math.sqrt(gas_consumption * 293 / (0.1 + gas_pressure / 1000) / gas_speed) * 10

    return math.ceil(result)  # Округление до следующего целого


def calculate_speed(gas_consumption: float, gas_pressure_kpa: float, diameter_mm: float) -> float:
    """
    Вычисляет скорость газа по формуле, обратной расчету диаметра.

    gas_pressure_kpa: давление в кПа (МПа * 1000)
    diameter_mm: диаметр в мм
    """

    # Конвертация давления в МПа для знаменателя
    gas_pressure_mpa = gas_pressure_kpa / 1000

    # Формула: V = (Q * 293) / ((D / 0.36238)^2 * (0.1 + P_mpa))
    # Примечание: 0.36238 = 0.036238 * 10 (как в исходной формуле)

    numerator = gas_consumption * 293
    denominator = ((diameter_mm / 0.36238) ** 2) * (0.1 + gas_pressure_mpa)

    gas_speed = numerator / denominator

    return math.ceil(gas_speed)  # Округление до следующего целого


def calculate_diameter(gas_consumption, gas_pressure_kpa, gas_speed):
    return None

# Посмотреть и привести к такому
# import math
#
# # Константы расчёта
# PIPELINE_FACTOR = 0.036238  # безразмерный коэффициент
# TEMPERATURE_CONSTANT = 293  # К (абсолютная температура)
# PRESSURE_OFFSET = 0.1  # МПа (базовое давление)
# MM_SCALING = 10  # множитель для перевода в мм
# def calculated_diametr(
#         gas_consumption: float,  # м³/ч (расход газа)
#         gas_pressure: float,  # кПа (давление)
#         gas_speed: float  # м/с (скорость газа)
# ) -> float | None:  # мм (диаметр, округлён вверх)
#     """
#     Рассчитывает диаметр газопровода по формуле:
#
#     D = PIPELINE_FACTOR × √[ (Q × TEMPERATURE_CONSTANT) / ((PRESSURE_OFFSET + P_МПа) × V) ] × MM_SCALING
#
#     Где:
#     - Q — расход газа (м³/ч)
#     - P_МПа — давление в МПа (переводится из кПа)
#     - V — скорость газа (м/с)
#
#     Returns:
#         Диаметр в миллиметрах (округлённый вверх) или None при ошибке.
#     """
#     # Проверка валидности входных данных
#     if (gas_consumption <= 0 or
#             gas_pressure < 0 or
#             gas_speed <= 0):
#         return None
#
#     # Перевод давления в МПа
#     pressure_mpa = gas_pressure / 1000
#
#     # Защита от деления на ноль
#     if PRESSURE_OFFSET + pressure_mpa <= 0:
#         return None
#
#     # Основной расчёт
#     try:
#         diameter_mm = PIPELINE_FACTOR * math.sqrt(
#             (gas_consumption * TEMPERATURE_CONSTANT) /
#             ((PRESSURE_OFFSET + pressure_mpa) * gas_speed)
#         ) * MM_SCALING
#         return math.ceil(diameter_mm)
#     except (ValueError, OverflowError):
#         return None