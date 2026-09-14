# -*- coding: utf-8 -*-
"""
Подбор ближайших значений давлений, которые реально присутствуют в таблицах.

Используется, когда точного совпадения входного/выходного давления в
Excel-данных не нашлось. Старая реализация (src/FoundCorValue.py) шагами
перебирала значения и на каждом шаге заново сканировала весь лист —
это было O(N*M^2) по чтению. Новая версия собирает множества доступных
давлений один раз и находит ближайшие арифметически.
"""
from __future__ import annotations

import logging
from typing import Optional, Set, Tuple

from src.core import parsing


class NearestValues:
    """Определяет ближайшие значения входного и выходного давления,
    присутствующие в таблицах книги.

    Логика повторяет назначение старого FoundCorValue:
      - выходное давление подбираем вверх (не меньше запрошенного),
        не дальше чем 1.5x;
      - входное давление подбираем вниз (не больше запрошенного),
        не дальше чем /1.5.
    """

    logger = logging.getLogger("App.NearestValues")

    MAX_INFLATE = 1.5  # допустимое повышение выходного давления

    def __init__(self) -> None:
        pass

    def find(
        self,
        workbook,
        p_in: float,
        p_out: float,
    ) -> Tuple[float, float]:
        """Возвращает (p_in_adj, p_out_adj) — ближайшие доступные давления.

        Если не удалось подобрать, возвращает исходные значения.
        """
        avail_in, avail_out = self._collect(workbook)
        out_adj = self._round_up_at_least(p_out, avail_out)
        in_adj = self._round_down_at_most(p_in, avail_in)

        self.logger.info(
            "Подбор ближайших давлений: запрошено (Pвх=%.4f, Pвых=%.4f), "
            "подобрано (Pвх=%.4f, Pвых=%.4f)",
            p_in, p_out, in_adj, out_adj,
        )
        return in_adj, out_adj

    # ------------------------------------------------------------------
    @staticmethod
    def _collect(workbook) -> Tuple[Set[float], Set[float]]:
        """Собирает множества всех доступных Pвх и Pвых во всех листах."""
        avail_in: Set[float] = set()
        avail_out: Set[float] = set()

        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            header_collected = False
            for row in sheet.iter_rows(values_only=True):
                # Заголовок выходных давлений — строка индекс 2 (пре-3я).
                # Определяем по наличию Pвх-подобного значения в столбце A
                # в последующих строках; здесь для простоты собираем все
                # числовые значения из колонок 1.. и колонки 0.
                for value in row[1:]:
                    for v in NearestValues._iter_points(value):
                        avail_out.add(v)
                if len(row) > 0:
                    for v in NearestValues._iter_points(row[0]):
                        avail_in.add(v)
        return avail_in, avail_out

    @staticmethod
    def _iter_points(value):
        """Извлекает доступные дискретные точки давления из ячейки.

        Для диапазона «a-b» берём обе границы (и середина не нужна:
        границы достаточно для дальнейшего подбора).
        """
        r = parsing.parse_pressure(value)
        if r is None:
            return
        yield r.min
        if r.is_range:
            yield r.max

    def _round_up_at_least(self, target: float, avail: Set[float]) -> float:
        """Ближайшее доступное значение, не меньше target и не больше 1.5x.

        Если такого нет — возвращаем сам target.
        """
        cap = target * self.MAX_INFLATE
        candidates = [v for v in avail if target <= v <= cap + 1e-9]
        if not candidates:
            return target
        # Берём минимальное из подходящих (т.е. ближайшее сверху)
        return min(candidates)

    def _round_down_at_most(self, target: float, avail: Set[float]) -> float:
        """Ближайшее доступное значение, не больше target и не меньше /1.5."""
        floor = target / self.MAX_INFLATE
        candidates = [v for v in avail if floor - 1e-9 <= v <= target]
        if not candidates:
            return target
        return max(candidates)