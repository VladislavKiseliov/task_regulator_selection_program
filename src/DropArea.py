import sys
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QMainWindow, QMessageBox, QPushButton, QFileDialog, QListWidget, QListWidgetItem, QLineEdit
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

class DropArea(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFont(QFont("Arial", 10))
        self.setStyleSheet("QListWidget { background-color : lightgrey; border: 2px dashed black; }")
        
        self.file_paths = []
        self.placeholder_text = "Перетащите файлы сюда"
        self.update_placeholder()

    def update_placeholder(self):
        if not self.file_paths:
            item = QListWidgetItem(self.placeholder_text)
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)  # make it non-selectable
            self.addItem(item)
        else:
            # Remove placeholder item if exists
            for i in range(self.count()):
                if self.item(i).text() == self.placeholder_text:
                    self.takeItem(i)
                    break

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            urls = event.mimeData().urls()
            new_files = [url.toLocalFile() for url in urls if url.isLocalFile()]
            self.file_paths.extend(new_files)
            for file in new_files:
                self.add_item(file)
            self.update_placeholder()

    def add_item(self, file_path):
        item = QListWidgetItem(file_path)
        self.addItem(item)

    def add_file(self, file_path):
        self.file_paths.append(file_path)
        self.add_item(file_path)
        self.update_placeholder()

    def remove_selected_file(self):
        selected_items = self.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            file_path = item.text()
            self.file_paths.remove(file_path)
            self.takeItem(self.row(item))
        self.update_placeholder()

    def get_file_paths(self):
        return self.file_paths