from cx_Freeze import setup, Executable

# Путь к вашему Python-файлу
target = 'selRegulator.py'

# Создаем исполняемый файл
exe = Executable(script=target)

# Настройки сборки
setup(
    name='selRegulator',
    version='1.0',
    base="Win32GUI",
    description='Программа  selRegulator  предназначена для помощи пользователям в выборе подходящих регуляторов на основе заданных параметров и анализа данных в файлах Excel.',
    executables=[exe],
    icon="icon.ico",
    options={
        'build_exe': {
            'includes': ['api-ms-win-core-path-l1-1-0.dll']
        }
    }
)



