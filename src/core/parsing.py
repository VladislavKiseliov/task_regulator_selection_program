# -*- coding: utf-8 -*-
"""
Устойчивый парсинг ячеек Excel с характеристиками регуляторов.

Excel-данные записаны в человекочитаемом виде с произвольным форматированием:
  - десятичные запятые  ->  "0,03"
  - неразрывные пробелы  ->  "\xa0 0,01"
  - диапазоны            ->  "0,001-0,01"
  - одиночные значения   ->  "0.05"
  - прочерки / пустые     ->  "-", "", None

Все функции в этом модуле нормализуют строку и возвращают устойчивый
результат без исключений при «грязном» вводе.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, Union


def normalize_text(value: object) -> str:
    """Приводит произвольное значение ячейки к нормализованной строке.

    - None / пустые -> пустая строка
    - числа -> строка как есть
    - убираются неразрывные пробелы, обычные пробелы; запятая -> точка
    """
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value)
    # Убираем неразрывные пробелы (\xa0) и обычные пробелы
    s = s.replace("\xa0", "").replace(" ", "")
    # Запятую превращаем в точку (десятичный разделитель)
    s = s.replace(",", ".")
    return s.strip()


def to_float(value: object) -> Optional[float]:
    """Безопасно превращает значение в float (одно число).

    Возвращает None, если это нечисло, пусто или прочерк.
    """
    s = normalize_text(value)
    if not s:
        return None
    if s in ("-", "—", "–", "н/д", "няма"):
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


@dataclass(frozen=True)
class PressureRange:
    """Диапазон давлений либо одиночное значение.

    min == max для одиночного значения; is_range=True только когда
    в ячейке реально записан диапазон «а-б».
    """
    min: float
    max: float
    is_range: bool = False

    def contains(self, value: float) -> bool:
        """True, если value попадает в диапазон (инклюзивно по границам)."""
        return self.min <= value <= self.max


def parse_pressure(value: object) -> Optional[PressureRange]:
    """Разбирает ячейку давления как одиночное значение или диапазон.

    Примеры:
        "0.05"            -> PressureRange(0.05, 0.05, is_range=False)
        "0,001-0,01"      -> PressureRange(0.001, 0.01, is_range=True)
        "-" | "" | None   -> None
        "мусор"           -> None
    """
    s = normalize_text(value)
    if not s:
        return None

    # Прочерки и заполнители
    if s in ("-", "—", "–"):
        return None

    # Пытаемся разбить на диапазон по дефису. Внимание: минус в научной
    # нотации ("1e-3") не должен трактоваться как разделитель диапазона.
    if "-" in s and not any(ch in s for ch in ("e", "E")):
        parts = s.split("-")
        if len(parts) == 2:
            v1 = to_float(parts[0])
            v2 = to_float(parts[1])
            if v1 is not None and v2 is not None:
                return PressureRange(min(v1, v2), max(v1, v2), is_range=True)

    v = to_float(s)
    if v is not None:
        return PressureRange(v, v, is_range=False)

    return None


def parse_int_bandwidth(value: object) -> Optional[int]:
    """Безопасно превращает значение в int (для пропускной способности).

    Если значение вещественное, округляем до целого.
    """
    s = normalize_text(value)
    if not s:
        return None
    if s in ("-", "—", "–"):
        return None
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


def is_range(value: object) -> bool:
    """Возвращает True, если значение является диапазоном вида «а-б»."""
    r = parse_pressure(value)
    return bool(r and r.is_range)