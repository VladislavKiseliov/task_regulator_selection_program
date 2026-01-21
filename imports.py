# imports.py
import os
import sys
from pathlib import Path

# 1. Настройка путей (ВАЖНО для работы внутри .exe)
if getattr(sys, 'frozen', False):
    # Если запущено из .exe
    bundle_dir = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
else:
    # Если запущено как обычный .py
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

# Добавляем корень проекта и src в пути поиска
src_path = os.path.join(bundle_dir, 'src')
sys.path.append(bundle_dir)
sys.path.append(src_path)

# 2. Импорты стандартных библиотек
import shutil
import itertools
import subprocess
import json
import math
import hashlib
import logging
import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List, Callable, Union

# 3. Импорт сторонних библиотек (должны быть в requirements.txt)
import openpyxl
from openpyxl import load_workbook
from openpyxl_image_loader import SheetImageLoader

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QApplication, QAction, QLabel, QTextEdit, QVBoxLayout, QWidget,
    QMainWindow, QMessageBox, QPushButton, QFileDialog, QListWidget,
    QListWidgetItem, QLineEdit, QDialog, QFrame, QSpinBox, QRadioButton,
    QComboBox, QMenuBar, QStatusBar
)
from PyQt5.QtCore import Qt, QTimer, QObject
from PyQt5.QtGui import QFont, QIcon

# 4. Экспортируем только внешние зависимости
__all__ = [
    'os', 'sys', 'shutil', 'itertools', 'subprocess', 'json', 'math',
    'hashlib', 'Decimal', 'Path', 'logging', 'datetime', 'Dict', 'Any',
    'Optional', 'List', 'Callable', 'Union',
    'openpyxl', 'load_workbook', 'SheetImageLoader',
    'QtCore', 'QtGui', 'QtWidgets', 'QApplication', 'Qt', 'QTimer',
    'QObject', 'QFont', 'QIcon',"QAction","QMessageBox","QFileDialog","QDialog","QVBoxLayout",
    "QTextEdit","QPushButton","QListWidget","QListWidgetItem"
]