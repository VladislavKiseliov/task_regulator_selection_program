# -*- coding: utf-8 -*-
"""
Кэширование разобранных данных книг Excel и результатов подбора.

Чтение и парсинг больших листов (.xlsx, 25 * 1025 ячеек) — самая дорогая
часть работы. Этот модуль запоминает «разобранный формат» книги по цифровой
подписи файла (путь + размер + время изменения) и однократно кэширует его,
поэтому повторные подборы по неизменным файлам работают без перечитывания
диска. Результаты селекции тоже кэшируются (ограниченный LRU), чтобы
повторный ввод одинаковых параметров был мгновенным.
"""
from __future__ import annotations

import os
import threading
from collections import OrderedDict
from typing import Any, Dict, Optional, Tuple


class FileSignature:
    """Позволяет быстро определить, изменился ли файл на диске."""

    __slots__ = ("path", "size", "mtime")

    def __init__(self, path: str) -> None:
        self.path = path
        try:
            stat = os.stat(path)
            self.size = stat.st_size
            self.mtime = stat.st_mtime
        except OSError:
            self.size = -1
            self.mtime = -1.0

    def key(self) -> Tuple[str, int, float]:
        return (self.path, self.size, self.mtime)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, FileSignature) and self.key() == other.key()

    def __hash__(self) -> int:  # pragma: no cover - служебный
        return hash(self.key())


class LRUCache:
    """Потокобезопасный LRU-кэш с верхней границей размера."""

    __slots__ = ("capacity", "_store", "_lock", "_hits", "_misses")

    def __init__(self, capacity: int = 256) -> None:
        self.capacity = max(1, capacity)
        self._store: "OrderedDict[Any, Any]" = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: Any, default: Any = None) -> Any:
        with self._lock:
            try:
                value = self._store.pop(key)
            except KeyError:
                self._misses += 1
                return default
            self._hits += 1
            self._store[key] = value  # перемещаем в конец (недавно использованный)
            return value

    def put(self, key: Any, value: Any) -> None:
        with self._lock:
            try:
                self._store.pop(key)
            except KeyError:
                pass
            self._store[key] = value
            while len(self._store) > self.capacity:
                self._store.popitem(last=False)

    def stats(self) -> Dict[str, int]:
        with self._lock:
            return {"hits": self._hits, "misses": self._misses}

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self._hits = 0
            self._misses = 0


class WorkbookCache:
    """Кэш разобранных книг + кэш результатов подбора.

    Потокобезопасен, подходит для вызова из фонового QThread.
    """

    __slots__ = ("_books", "_selection", "_lock")

    def __init__(self, book_capacity: int = 16, selection_capacity: int = 256) -> None:
        self._books = LRUCache(book_capacity)
        self._selection = LRUCache(selection_capacity)
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Разобранные книги: (path) -> parsed-structure
    # ------------------------------------------------------------------
    def get_book(self, path: str) -> Optional[object]:
        sig = FileSignature(path)
        return self._books.get(sig.key())

    def put_book(self, path: str, parsed: object) -> None:
        sig = FileSignature(path)
        self._books.put(sig.key(), parsed)

    def invalidate(self, path: str) -> None:
        """Принудительно сбрасывает кэш для файла (например, после изменений)."""
        sig = FileSignature(path)
        with self._books._lock:
            self._books._store.pop(sig.key(), None)

    # ------------------------------------------------------------------
    # Результаты подбора: (параметры...) -> Dict[str, RegulatorMatch]
    # ------------------------------------------------------------------
    def get_selection(self, key: Tuple[Any, ...]) -> Optional[object]:
        return self._selection.get(key)

    def put_selection(self, key: Tuple[Any, ...], result: object) -> None:
        self._selection.put(key, result)

    def clear(self) -> None:
        self._books.clear()
        self._selection.clear()


# Единственный глобальный кэш на процесс (переживает несколько запросов).
_global_cache = WorkbookCache()


def get_global_cache() -> WorkbookCache:
    """Возвращает глобальный (процессный) кэш книг и результатов."""
    return _global_cache