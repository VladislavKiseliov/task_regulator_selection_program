import sys
import os
from cx_Freeze import setup, Executable

# 1. Основные пакеты
build_packages = [
    "os", "sys", "logging", "PyQt5", "openpyxl",
    "pathlib", "math", "datetime", "shutil"
]

# 2. Исключения (убираем ошибки совместимости)
build_excludes = [
    "unittest", "test", "PyQt5.QtQml",
    "PyQt5.QtQuick", "PyQt5.QtNetwork", "freeze-core"
]

# 3. Список файлов для сборки
include_files = [
    "icon.ico",
    "src/",             # Исходники логики
    "instruction.txt",  # Файл инструкции
    "Каталог/",         # Папка со схемами (чертежами)
]

# Создаем нужные папки перед сборкой
for folder in ["Каталог", "logs"]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# 4. Настройки сборщика
build_exe_options = {
    "packages": build_packages,
    "excludes": build_excludes,
    "include_files": include_files,
    "include_msvcr": True,
    "zip_include_packages": ["*"],
    "zip_exclude_packages": [],
}

# 5. Скрытие консоли
base = None
if sys.platform == "win32":
    base = "gui"

setup(
    name="RegulatorSelector",
    version="1.0",
    description="Программа подбора регуляторов давления газа",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "selRegulator.py",
            base=base,
            target_name="RegulatorSelector.exe",
            icon="icon.ico"
        )
    ]
)