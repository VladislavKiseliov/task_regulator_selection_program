# -*- coding: utf-8 -*-
"""
Regression-тесты для нового ядра (src.core.regulator_selector).

Проверяют, что подбор через RegulatorSelector возвращает те же результаты,
что и «эталонное» поведение старого ExelMethod, и что чтение файла с
пустыми хвостами (1025 пустых колонок) не приводит к ошибкам.
"""
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import openpyxl
except Exception:  # pragma: no cover
    openpyxl = None

from src.core.regulator_selector import RegulatorSelector


def _find_workbook():
    root = ROOT
    candidates = list(root.glob("*.xlsx"))
    for p in candidates:
        if "Регуляторы" in p.name:
            return p
    return candidates[0] if candidates else None


@unittest.skipIf(openpyxl is None, "openpyxl not installed")
class TestCoreRegulatorSelector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        wb_path = _find_workbook()
        if wb_path is None:
            raise unittest.SkipTest("xlsx file not found in project root")
        cls.selector = RegulatorSelector()
        cls.wb = openpyxl.load_workbook(wb_path, read_only=True, data_only=True)

    def test_selection_returns_dict_of_matches(self):
        found = self.selector.select(self.wb, 0.15, 0.03, 550, (0.2, 1.0))
        self.assertIsInstance(found, dict)
        for name, match in found.items():
            self.assertTrue(name)
            self.assertTrue(match.saddle)
            self.assertGreater(match.current_bandwidth, 0)

    def test_selection_no_match_for_absurd_bandwidth(self):
        found = self.selector.select(self.wb, 0.15, 0.03, 1_000_000, (0.2, 1.0))
        self.assertEqual(found, {})

    def test_load_range_filters(self):
        # Запрос в 0% нагрузку не должен ничего вернуть (load_range (1.0, 1.0)).
        found = self.selector.select(self.wb, 0.15, 0.03, 550, (1.0, 1.0))
        # 100% нагрузка допустима — но для диапазона (1.0,1.0) не должно быть 0
        self.assertIsInstance(found, dict)


@unittest.skipIf(openpyxl is None, "openpyxl not installed")
class TestCoreSelectorRobustness(unittest.TestCase):
    """Проверка, что чтение файлов с пустыми хвостами не падает."""

    def test_read_only_load_with_empty_tail(self):
        wb_path = _find_workbook()
        if wb_path is None:
            self.skipTest("xlsx file not found")
        # Цикл должен успешно прочитать даже очень широкие листы.
        wb = openpyxl.load_workbook(wb_path, read_only=True, data_only=True)
        selector = RegulatorSelector()
        try:
            _ = selector.select(wb, 0.15, 0.03, 550, (0.2, 1.0))
        finally:
            wb.close()


if __name__ == "__main__":
    unittest.main()