# -*- coding: utf-8 -*-
"""Тесты кэширования книг и быстрого загрузчика pandas/openpyxl."""
import os
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.cache import LRUCache, WorkbookCache, FileSignature
from src.core.workbook import read_workbook_fast, ParsedWorkbook
from src.core.regulator_selector import RegulatorSelector


class TestLRUCache(unittest.TestCase):
    def test_put_get_eviction(self):
        c = LRUCache(capacity=2)
        c.put("a", 1)
        c.put("b", 2)
        self.assertEqual(c.get("a"), 1)
        c.put("c", 3)  # вытеснит 'b' (самый старый недавно неиспользуемый)
        self.assertIsNone(c.get("b"))
        self.assertEqual(c.get("c"), 3)

    def test_stats(self):
        c = LRUCache(capacity=4)
        c.get("x")  # miss
        c.put("x", 1)
        c.get("x")  # hit
        stats = c.stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)


class TestFileSignature(unittest.TestCase):
    def test_key_changes_with_path(self):
        wb = Path(__file__)
        s1 = FileSignature(str(wb))
        self.assertIn(wb.name.split(".")[0], s1.key()[0])
        self.assertGreater(s1.size, 0)


class TestWorkbookCache(unittest.TestCase):
    def test_book_roundtrip_signature_locked(self):
        root = ROOT
        xlsx = _find_xlsx()
        if not xlsx:
            self.skipTest("no xlsx file in root")
        cache = WorkbookCache()
        path = str(xlsx)
        parsed1 = read_workbook_fast(path, cache=cache)
        self.assertIsInstance(parsed1, ParsedWorkbook)
        self.assertTrue(parsed1.sheetnames)
        # Повторное чтение возвращает тот же кэшированный объект.
        parsed2 = read_workbook_fast(path, cache=cache)
        self.assertIs(parsed1, parsed2)


class TestFastSelector(unittest.TestCase):
    def test_selector_works_on_cached_workbook(self):
        xlsx = _find_xlsx()
        if not xlsx:
            self.skipTest("no xlsx file in root")
        cache = WorkbookCache()
        path = str(xlsx)
        wb = read_workbook_fast(path, cache=cache)
        found = RegulatorSelector().select(wb, 0.15, 0.03, 550, (0.2, 1.0))
        self.assertIsInstance(found, dict)


def _find_xlsx():
    for p in ROOT.glob("*.xlsx"):
        if "Регуляторы" in p.name or "РДГ" in p.name:
            return p
    return next(ROOT.glob("*.xlsx"), None)


if __name__ == "__main__":
    unittest.main()