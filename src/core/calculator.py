# -*- coding: utf-8 -*-
"""Инженерные расчёты газопровода: диаметр, скорость, подбор скорости.

Переносит формулы из src/utils/MathMethod.py и src/Model.py в чистое ядро,
исправляя путаницу с единицами измерения.
"""
from __future__ import annotations

import math
from typing import Optional

# Константы расчёта
PIPELINE_FACTOR = 0.036238   # безразмерный коэффициент
TEMPERATURE_CONSTANT = 293   # К (абсолютная температура)
PRESSURE_OFFSET = 0.1        # МПа (базовое давление)
MM_SCALING = 10              # множитель для перевода в мм


def calculated_diameter(
    gas_consumption: float,
    gas_pressure_kpa: float,
    gas_speed: float,
) -> Optional[float]:
    """Диаметр газопровода в мм (округление вверх) или None при ошибке.

    Формула: D = F * sqrt(Q * T / ((0.1 + P_МПа) * V)) * 10

    Args:
        gas_consumption: расход газа (м³/ч).
        gas_pressure_kpa: давление газа (кПа).
        gas_speed: скорость газа (м/с).
    """
    # Валидация
    if gas_consumption <= 0 or gas_pressure_kpa < 0 or gas_speed <= 0:
        return None

    pressure_mpa = gas_pressure_kpa / 1000.0
    if PRESSURE_OFFSET + pressure_mpa <= 0:
        return None

    try:
        diameter_mm = (
            PIPELINE_FACTOR
            * math.sqrt(
                (gas_consumption * TEMPERATURE_CONSTANT)
                / ((PRESSURE_OFFSET + pressure_mpa) * gas_speed)
            )
            * MM_SCALING
        )
        return math.ceil(diameter_mm)
    except (ValueError, OverflowError):
        return None


def calculate_speed(
    gas_consumption: float,
    gas_pressure_kpa: float,
    diameter_mm: float,
) -> Optional[float]:
    """Скорость газа (м/с, округление вверх) или None при ошибке.

    Формула: V = Q * T / ((D / 0.36238)^2 * (0.1 + P_МПа))
    (обратная к расчёту диаметра).
    """
    if gas_consumption <= 0 or gas_pressure_kpa < 0 or diameter_mm <= 0:
        return None

    gas_pressure_mpa = gas_pressure_kpa / 1000.0

    denominator = ((diameter_mm / (PIPELINE_FACTOR * MM_SCALING)) ** 2) * (
        PRESSURE_OFFSET + gas_pressure_mpa
    )
    if denominator <= 0:
        return None
    try:
        gas_speed = (gas_consumption * TEMPERATURE_CONSTANT) / denominator
        return math.ceil(gas_speed)
    except (ValueError, OverflowError):
        return None


def select_speed(pressure_mpa: float) -> float:
    """Выбирает расчётную скорость газа по давлению (МПа).

    Логика:
      - до 50 кПа: 15.0 м/с
      - 50–600 кПа: 25.0 м/с
      - свыше 600 кПа: 30.0 м/с
    """
    gas_pressure_kpa = float(pressure_mpa) * 1000.0
    if gas_pressure_kpa < 0:
        return 0.0
    if gas_pressure_kpa < 50:
        return 15.0
    if gas_pressure_kpa <= 600:
        return 25.0
    return 30.0


def round_up_to_int(value: float) -> int:
    """Округление до следующего целого."""
    return math.ceil(value)