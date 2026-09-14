# -*- coding: utf-8 -*-
"""
Быстрый загрузчик книг Excel на основе pandas + openpyxl.

Проблема: открытие .xlsx через openpyxl и повторное чтение ячеек —
самая медленная часть подбора (листы бывают 25×1025 ячеек). Решение:

  1. Чтение всех листов книги выполняется ОДИН раз функцией read_excel
     с header=None (читает только фактически заполненные ячейки, без
     пресчёта пустых хвостов), результат кладётся в кэш по сигнатуре файла.
  2. Разобранная книга предоставляет тот же интерфейс ``iter_rows`` /
     ``sheetnames`` что и openpyxl, поэтому RegulatorSelector работает
     без изменений, но источник данных — быстрая матрица в памяти.

Если pandas недоступен — используется открытая книга openpyxl напрямую.
"""
from __future__ import annotations

import logging
import os
from typing import Dict, Iterator, List, Optional, Sequence

from src.core.cache import WorkbookCache, get_global_cache

logger = logging.getLogger("App.WorkbookLoader")

# NOTE: pandas is imported LAZILY через __import__, а не через верхнеуровневый
# `import pandas`. Так cx_Freeze не тянет всю экосистему pandas/numpy в собранный
# exe (в замороженной сборке pandas не нужен — по умолчанию читаем openpyxl'ом).
_PANDAS_LOAD_TRIED = False
_PANDAS_OK = False


def _get_pandas():  # pragma: no cover - зависит от окружения
    """Лениво импортирует pandas (только если она реально нужна)."""
    global _PANDAS_LOAD_TRIED, _PANDAS_OK
    if _PANDAS_LOAD_TRIED:
        return _PANDAS_OK
    _PANDAS_LOAD_TRIED = True
    try:
        __import__("pandas")
        _PANDAS_OK = True
    except Exception:  # noqa: BLE001
        _PANDAS_OK = False
    return _PANDAS_OK


class ParsedSheet:
    """Имитирует MinimalSheet-интерфейс openpyxl поверх матрицы значений."""

    __slots__ = ("_rows",)

    def __init__(self, rows: List[Sequence]) -> None:
        self._rows = rows

    def iter_rows(self, values_only: bool = True) -> Iterator[Sequence]:
        if values_only:
            yield from self._rows
        else:
            raise NotImplementedError(
                "ParsedSheet поддертиживает только values_only=True"
            )


class ParsedWorkbook:
    """Книга, разобранная один раз в список строк по каждому листу."""

    __slots__ = ("sheetnames", "_sheets")

    def __init__(self, sheets: Dict[str, ParsedSheet]) -> None:
        self.sheetnames = list(sheets.keys())
        self._sheets = sheets

    def __getitem__(self, name: str) -> ParsedSheet:
        return self._sheets[name]


def _size_hint(rows: List[List[object]]) -> int:
    total = 0
    for row in rows:
        total += len(row)
    return total


def read_workbook_fast(
    path: str,
    cache: Optional[WorkbookCache] = None,
) -> object:
    """Читает книгу через кэш, возвращая openpyxl-совместимый объект.

    Если файл уже был разобран и не менялся — возвращает результат из кэша
    (практически мгновенно).
    """
    cache = cache or get_global_cache()
    cached = cache.get_book(path)
    if cached is not None:
        return cached

    parsed = _load(path)
    cache.put_book(path, parsed)
    return parsed


def _load(path: str) -> ParsedWorkbook:
    """Непосредственная загрузка книги в разобранные строки.

    Парсинг выполняет openpyxl read_only (потоковый, пропускает пустые
    ячейки) — он быстрее pandas на разреженных листах 25×1025. Результат
    кэшируется, поэтому стоимость чтения платится один раз на файл.
    """
    try:
        return _load_with_openpyxl(path)
    except Exception as exc:  # noqa: BLE001
        logger.warning("openpyxl read failed (%s); fallback to pandas", exc)
        if _get_pandas():
            return _load_with_pandas(path)
        raise


def _load_with_pandas(path: str) -> ParsedWorkbook:
    """Чтение всех листов через pandas.read_excel(header=None).

    Используется как запасной/альтернативный backend. Для разреженных
    листов openpyxl read_only обычно быстрее (см. _load).
    """
    sheets: Dict[str, ParsedSheet] = {}
    pd = __import__("pandas")
    with pd.ExcelFile(path, engine="openpyxl") as xl:
        for name in xl.sheet_names:
            frame = pd.read_excel(
                xl, sheet_name=name, header=None, dtype=object
            )
            # Превращаем DataFrame в список строк (значения как есть).
            rows: List[Sequence] = [
                [val for val in row] for row in frame.itertuples(index=False)
            ]
            # Отбрасываем полностью пустые хвосты, чтобы не качать 1025 колонок.
            rows = _trim_empty(rows)
            sheets[name] = ParsedSheet(rows)
    logger.info(
        "pandas прочитал %s; листов=%d, ячеек=%d",
        os.path.basename(path),
        len(sheets),
        sum(_size_hint(s._rows) for s in sheets.values()),
    )
    return ParsedWorkbook(sheets)


def _load_with_openpyxl(path: str) -> ParsedWorkbook:
    """Запасное чтение через openpyxl (без pandas)."""
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        sheets: Dict[str, ParsedSheet] = {}
        for name in wb.sheetnames:
            rows: List[Sequence] = [
                list(row) for row in wb[name].iter_rows(values_only=True)
            ]
            rows = _trim_empty(rows)
            sheets[name] = ParsedSheet(rows)
        return ParsedWorkbook(sheets)
    finally:
        wb.close()


def _trim_empty(rows: List[Sequence]) -> List[Sequence]:
    """Обрезает пустые строки/колонки, не уничтожая смысловые данные."""
    if not rows:
        return []
    num_cols = max((len(r) for r in rows), default=0)
    if num_cols == 0:
        return rows
    # Максимальный индекс, в котором есть хоть одно непустое значение.
    max_c = -1
    for r in rows:
        for ci, val in enumerate(r):
            if val is not None and str(val).strip() != "":
                if ci > max_c:
                    max_c = ci
    if max_c < 0:
        return []
    return [
        list(r[: max_c + 1]) if len(r) > max_c + 1 else list(r)
        for r in rows
    ]