import sys
import os
from cx_Freeze import setup, Executable

# Явный список пакетов, которые нам нужны
build_packages = ["os", "sys", "logging", "PyQt5", "openpyxl", "pathlib", "math"]

# Список исключений, чтобы обойти баг с QmlImportsPath
# Добавляем модули Qt, которые вызывают ошибку
build_excludes = [
    "tkinter",
    "unittest",
    "test",
    "PyQt5.QtQml",
    "PyQt5.QtQuick",
    "PyQt5.QtNetwork", # Если не используете интернет-запросы, тоже можно убрать
    "freeze-core",
    "cx_Freeze"
]

build_exe_options = {
    "packages": build_packages,
    "excludes": build_excludes,
    "include_files": [
        "icon.ico",
        "src/",
    ],
    "optimize": 2,
    "include_msvcr": True,
}

base = None
if sys.platform == "win32":
    # Для Python 3.13 лучше пока оставить None, чтобы видеть ошибки в консоли при запуске
    base = None

setup(
    name="RegulatorSelector",
    version="1.0",
    description="Программа подбора регуляторов ГАЗ",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "selRegulator.py",
            base=base,
            icon="icon.ico",
            target_name="RegulatorSelector.exe"
        )
    ]
)