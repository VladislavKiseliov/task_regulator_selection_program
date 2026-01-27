# -*- coding: utf-8 -*-
import os
from contextlib import contextmanager
from pathlib import Path
import sys

def is_int(value) -> bool:
    """Функция is_int, принимает значение
    и если это число возвращает True,
    иначе False"""
    try:
        int(value)
        return True
    except ValueError:
        return False


def split_and_insert_newline(self, text) -> None:
    """Функция для разделения строчки на двое если одна длинее 5 слов"""
    words = text.split()  # Разделение строки на список слов
    result = text
    if len(words) > 5:
        half_length = len(words) // 2
        first_half = ' '.join(words[:half_length])  # Объединение слов до середины
        second_half = ' '.join(words[half_length:])  # Объединение слов после середины
        result = f"{first_half}\n{second_half}"
    return result


@contextmanager
def block_signals(widget):
    widget.blockSignals(True)
    try:
        yield widget
    finally:
        widget.blockSignals(False)


# Ensure project root is on sys.path so "imports.py" resolves when запуск из подкаталогов.
_root = Path(__file__).resolve()
for _ in range(4):
    if (_root / "imports.py").exists():
        break
    _root = _root.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from imports import *

def calculate_hash(string:str) -> str:
    # Создаем объект хеша
    hash_object = hashlib.sha256()

    # Обновляем хеш с данными из строки
    hash_object.update(string.encode('utf-8'))

    # Получаем хеш-сумму в виде шестнадцатеричной строки
    hash_string = hash_object.hexdigest()

    return hash_string
