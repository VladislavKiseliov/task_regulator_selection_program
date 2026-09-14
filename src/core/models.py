# -*- coding: utf-8 -*-
"""Доменные модели для подбора регуляторов и поиска схем."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class RegulatorMatch:
    """Найденный подходящий регулятор.

    Attributes:
        name:            Модель/Наименование регулятора.
        saddle:          Диаметр седла (мм), строка как в Excel.
        current_bandwidth: Пропускная способность из таблицы (м³/ч).
        required_bandwidth: Требуемый расход пользователя (м³/ч).
        load_percent:    Процент загрузки (required / current * 100).
    """
    name: str
    saddle: str
    current_bandwidth: int
    required_bandwidth: int
    load_percent: float = 0.0

    @property
    def as_dict(self) -> Dict[str, object]:
        """Представление для обратной совместимости со старой схемой данных."""
        return {
            "saddle": self.saddle,
            "currentBandwidth": self.current_bandwidth,
            "bandwidth": self.required_bandwidth,
        }


@dataclass
class SelectorResult:
    """Результат подбора регуляторов по всем загруженным файлам.

    Attributes:
        regulators:     Словарь {имя: RegulatorMatch} (уникальные имена).
        source_files:   Сколько файлов обработано.
        used_p_in:      Входное давление, реально использованное в подборе
                        (может отличаться от запрошенного после подбора
                        ближайших значений).
        used_p_out:     Выходное давление, реально использованное.
    """
    regulators: Dict[str, RegulatorMatch] = field(default_factory=dict)
    source_files: int = 0
    used_p_in: Optional[float] = None
    used_p_out: Optional[float] = None

    @property
    def count(self) -> int:
        return len(self.regulators)

    def merge_file(self, found: Dict[str, RegulatorMatch]) -> None:
        """Объединяет результаты одного файла, не затирая предыдущие."""
        for name, match in found.items():
            self.regulators[name] = match


@dataclass
class SchemeSearchConfig:
    """Конфигурация газораспределительного оборудования для имени схемы."""
    product_type: str = ""              # Тип изделия (ГРПШ / ГРУ / ГРПБ)
    regulator: str = ""                 # Модель регулятора
    working_lines: object = 0           # Количество рабочих линий
    reserve_lines: object = 0           # Количество резервных линий
    removable_reserve: object = 0       # Наличие съёмной резервной линии
    sto_gprg: object = "0"              # Исполнение по СТО ГПРГ
    heating: object = "0"               # Обогрев
    telemetry: object = "0"             # Телеметрия
    climate: object = "У1"              # Климатическое исполнение
    uirg: object = "0"                  # Оснащение УИРГ
    gas_outputs: object = 1             # Количество выходов газопроводов
    valve_diameter_in: object = "НД"    # Диаметр запорной арматуры на входе
    valve_diameter_out: object = "НД"   # Диаметр запорной арматуры на выходе
    direction: object = "Л-П"           # Направление

    @classmethod
    def from_config_dict(cls, cfg: Dict[str, object]) -> "SchemeSearchConfig":
        return cls(
            product_type=str(cfg.get("Тип изделия", "") or ""),
            regulator=str(cfg.get("Регулятор", "") or ""),
            working_lines=cfg.get("Количество рабочих линий", 0),
            reserve_lines=cfg.get("Количество резервных линий", 0),
            removable_reserve=cfg.get("Наличие съемной резервной линии", 0),
            sto_gprg=cfg.get("Исполнение по СТО ГПРГ", "0"),
            heating=cfg.get("Обогрев", "0"),
            telemetry=cfg.get("Телеметрия", "0"),
            climate=cfg.get("Климатическое исполнение", "У1"),
            uirg=cfg.get("Оснащение УИРГ", "0"),
            gas_outputs=cfg.get("Количество выходов газопроводов", 1),
            valve_diameter_in=cfg.get("Диаметр запорной арматуры на входе", "НД"),
            valve_diameter_out=cfg.get("Диаметр запорной арматуры на выходе", "НД"),
            direction=cfg.get("Направление", "Л-П"),
        )


@dataclass
class SchemeSearchResult:
    """Результат поиска схемы для одного регулятора."""
    regulator_name: str
    scheme_name: str
    file_path: Optional[str]
    found: bool