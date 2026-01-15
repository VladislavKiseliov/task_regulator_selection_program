# imports.py

import os
import sys

# Добавляем путь к директории includes в sys.path
includes_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'includes'))
sys.path.append(includes_path)

# Импорты стандартных библиотек
import tkinter as tk
import shutil
import openpyxl
import tkinter.ttk as ttk
import itertools
import subprocess
import json
import math
import hashlib
from decimal import Decimal
from tkinter import messagebox, filedialog

# Импорт сторонних библиотек
from tkinterdnd2 import DND_FILES, TkinterDnD
from openpyxl_image_loader import SheetImageLoader
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QApplication, QAction, QLabel, QTextEdit, QVBoxLayout, QWidget,
                             QMainWindow, QMessageBox, QPushButton, QFileDialog, QListWidget, 
                             QListWidgetItem, QLineEdit, QDialog)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon


# Импорты из локальных модулей
from src.GUI.mainwindow import Ui_MainWindow
from src.FoundCorValue import FoundCorValue
from src.DropArea import DropArea
from src.MyLogger import FileWriter

# Список для экспорта
__all__ = [
    'tk', 'shutil', 'os', 'openpyxl', 'ttk', 'itertools', 'subprocess', 'json', 'math', 'Decimal', 
    'messagebox', 'filedialog', 'DND_FILES', 'TkinterDnD', 'SheetImageLoader', 'hashlib', 'sys', 'QtCore', 
    'QtGui', 'QtWidgets', 'QApplication', 'QAction', 'QLabel', 'QTextEdit', 'QVBoxLayout', 
    'QWidget', 'QMainWindow', 'QMessageBox', 'QPushButton', 'QFileDialog', 'QListWidget', 
    'QListWidgetItem', 'QLineEdit', 'QDialog', 'Qt', 'QTimer', 'QFont', 'QIcon', 
    'DropArea', 'Ui_MainWindow', 'FoundCorValue', 'FileWriter',
]

