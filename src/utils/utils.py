import os
from contextlib import contextmanager


def create_path_folder_for_save(self) -> None:
    """Создаём папку для сохранения файлов записей подбора если её нет.
    получаем путь к этой папке."""
    # Получение текущей директории
    self.current_dir = os.getcwd()

    # Сборка пути к папке
    self.folder_save_name = "Записи подбора регуляторов"
    self.folder_path = os.path.join(self.current_dir, self.folder_save_name)

    # Проверка существования папки и создание, если не существует
    if not os.path.exists(self.folder_path):
        os.makedirs(self.folder_path)

def is_int(self, value) -> bool:
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