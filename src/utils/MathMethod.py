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