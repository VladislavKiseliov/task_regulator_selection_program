# imports.py

import os
import sys

# Добавляем путь к директории src в sys.path для правильного импорта модулей
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(src_path)

# Импорты стандартных библиотек
import shutil
import itertools
import subprocess
import json
import math
import hashlib
from decimal import Decimal
from pathlib import Path
import logging
from typing import Dict, Any, Optional, List, Callable, Union

# Импорт сторонних библиотек
import openpyxl
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


# Импорты из локальных модулей проекта
# GUI модули
from src.GUI.SelRegulator import SelRegulator
from src.GUI.mainwindow import Ui_MainWindow

# Основные модули
from src.Model import Model
from src.controller import Controller
from src.FoundCorValue import FoundCorValue
from src.DropArea import DropArea
from src.MyLogger import FileWriter

# Утилиты
from src.utils.ExelMethod import ExelMethod
from src.utils.MathMethod import calculated_diametr, calculate_speed
from src.utils.logger_config import setup_logger, create_log_file
from src.utils.CallbackRegister import CallbackRegistry
from src.utils.utils import create_path_folder_for_save, is_int

# Список для экспорта - только реально используемые модули
__all__ = [
    # Стандартные библиотеки
    'os', 'sys', 'shutil', 'itertools', 'subprocess', 'json', 'math', 
    'hashlib', 'Decimal', 'Path', 'logging', 'Dict', 'Any', 'Optional', 
    'List', 'Callable', 'Union',
    
    # Сторонние библиотеки
    'openpyxl', 'SheetImageLoader',
    'QtCore', 'QtGui', 'QtWidgets',
    'QApplication', 'QAction', 'QLabel', 'QTextEdit', 'QVBoxLayout', 
    'QWidget', 'QMainWindow', 'QMessageBox', 'QPushButton', 'QFileDialog', 
    'QListWidget', 'QListWidgetItem', 'QLineEdit', 'QDialog', 'QFrame',
    'QSpinBox', 'QRadioButton', 'QComboBox', 'QMenuBar', 'QStatusBar',
    'Qt', 'QTimer', 'QObject', 'QFont', 'QIcon',
    
    # Локальные модули
    'SelRegulator', 'Ui_MainWindow', 'Model', 'Controller',
    'FoundCorValue', 'DropArea', 'FileWriter',
    'ExelMethod', 'calculated_diametr', 'calculate_speed',
    'setup_logger', 'create_log_file', 'CallbackRegistry',
    'create_path_folder_for_save', 'is_int'
]

