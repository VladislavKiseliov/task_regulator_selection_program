import json
import os
from imports import *


class DropArea(QListWidget):
    """
    Виджет для выбора файлов методом Drag-and-Drop с автоматическим сохранением путей.

    Класс предоставляет графическую область, в которую можно перетаскивать файлы.
    Допустимые форматы (.xlsx, .doc, .docx) сохраняются в конфигурационный файл JSON
    и автоматически загружаются при следующем запуске приложения.
    """

    def __init__(self, parent=None):
        """
        Инициализирует область сброса файлов, настраивает стили и загружает конфиг.

        Args:
            parent: Родительский виджет (по умолчанию None).
        """
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFont(QFont("Arial", 10))
        self.setStyleSheet("QListWidget { background-color : lightgrey; border: 2px dashed black; }")

        self.config_file = "app_config.json"
        self.file_paths = []  # Список для хранения абсолютных путей к файлам
        self.placeholder_text = "Перетащите файлы формата .xlsx сюда"
        self.allowed_extensions = {'.xlsx', '.doc', '.docx'}

        self.load_config()
        self.update_placeholder()

    def save_config(self):
        """
        Сохраняет текущий список путей в JSON-файл конфигурации.

        Записывает данные в формате: {"saved_paths": ["путь1", "путь2", ...]}.
        Вызывается при добавлении или удалении файлов из списка.
        """
        try:
            config = {"saved_paths": self.file_paths}
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка при сохранении конфига: {e}")

    def load_config(self):
        """
        Загружает список путей из JSON-файла при инициализации.

        Проверяет физическое наличие каждого файла на диске перед добавлением в список.
        Если файл был удален или перемещен, он игнорируется.
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    saved_paths = config.get("saved_paths", [])

                    for path in saved_paths:
                        if os.path.exists(path):
                            if path not in self.file_paths:
                                self.file_paths.append(path)
                                self.add_item(path)
            except Exception as e:
                print(f"Ошибка при загрузке конфига: {e}")

    def update_placeholder(self):
        """
        Обновляет визуальное состояние области: показывает или скрывает текст-подсказку.

        Если список файлов пуст, отображается текст placeholder_text.
        Если файлы добавлены, текст-подсказка удаляется.
        """
        if not self.file_paths:
            self.clear()
            item = QListWidgetItem(self.placeholder_text)
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            self.addItem(item)
        else:
            for i in range(self.count()):
                item = self.item(i)
                if item and item.text() == self.placeholder_text:
                    self.takeItem(i)
                    break

    def dragEnterEvent(self, event):
        """Проверяет, содержит ли перетаскиваемый объект ссылки на файлы."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        """Разрешает перемещение объекта внутри области."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """
        Обрабатывает событие сброса файлов в область.

        Извлекает пути к файлам, фильтрует их по расширению, проверяет на дубликаты
        и инициирует сохранение обновленного списка в конфиг.
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            urls = event.mimeData().urls()

            new_files_added = False
            for url in urls:
                path = url.toLocalFile()
                if os.path.isfile(path) and self.is_allowed_file(path):
                    path = os.path.abspath(path)
                    if path not in self.file_paths:
                        self.file_paths.append(path)
                        self.add_item(path)
                        new_files_added = True

            if new_files_added:
                self.update_placeholder()
                self.save_config()

    def is_allowed_file(self, file_path: str) -> bool:
        """
        Проверяет, соответствует ли расширение файла списку разрешенных.

        Args:
            file_path: Полный путь к проверяемому файлу.

        Returns:
            True, если расширение разрешено, иначе False.
        """
        return any(file_path.lower().endswith(ext) for ext in self.allowed_extensions)

    def add_item(self, file_path: str):
        """Добавляет строку с путем файла в визуальный список (виджет)."""
        item = QListWidgetItem(file_path)
        self.addItem(item)

    def remove_selected_file(self):
        """
        Удаляет выделенные пользователем файлы из списка и обновляет конфиг.

        Вызывается обычно при нажатии кнопки 'Удалить' в интерфейсе.
        """
        selected_items = self.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            path = item.text()
            if path in self.file_paths:
                self.file_paths.remove(path)
            self.takeItem(self.row(item))

        self.update_placeholder()
        self.save_config()

    def get_file_paths(self) -> list:
        """
        Возвращает текущий список абсолютных путей к загруженным файлам.

        Returns:
            list: Список строк с путями.
        """
        return self.file_paths