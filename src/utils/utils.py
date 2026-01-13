import os
from contextlib import contextmanager


def create_path_folder_for_save() -> None:
    """Создаём папку для сохранения файлов записей подбора если её нет.
    получаем путь к этой папке."""
    # Получение текущей директории
    current_dir = os.getcwd()

    # Сборка пути к папке
    folder_save_name = "Записи подбора регуляторов"
    folder_path = os.path.join(current_dir, folder_save_name)

    # Проверка существования папки и создание, если не существует
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

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