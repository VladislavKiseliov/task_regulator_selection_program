# -*- coding: utf-8 -*-
"""
Единая QSS-тема приложения.

Применяется к главному окну в SelRegulator.__init__ через setStyleSheet.
Даёт современный, аккуратный и однородный вид всем стандартным виджетам
PyQt5, не требуя перегенерации .ui.
"""
GLOBAL_QSS = """
/* ===== Окно и фон ===== */
QMainWindow { background-color: #f4f6fa; }
QWidget#centralwidget { background-color: #f4f6fa; }

/* ===== Группы (карточки-секции) ===== */
QGroupBox {
    font-weight: 600;
    font-size: 12px;
    color: #2c3e50;
    border: 1px solid #d3dbe6;
    border-radius: 10px;
    margin-top: 12px;
    padding-top: 6px;
    background-color: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 8px;
}

/* ===== Кнопки ===== */
QPushButton {
    background-color: #2e86de;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton:hover { background-color: #2471b8; }
QPushButton:pressed { background-color: #1b5fa0; }
QPushButton:disabled { background-color: #b8c2cf; color: #ffffff; }

/* Проверяемые кнопки (флаги режима) */
QPushButton:checked {
    background-color: #16a085;
    color: #ffffff;
    border-left: 3px solid #0f7c6b;
}
QPushButton:unchecked {
    background-color: #e9edf2;
    color: #55606e;
    border: 1px solid #ccd4df;
}

/* ===== Поля ввода ===== */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #ffffff;
    border: 1px solid #c9d3e0;
    border-radius: 6px;
    padding: 5px;
    selection-background-color: #2e86de;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 2px solid #2e86de;
}
QComboBox::drop-down { border: none; width: 24px; }
QComboBox::down-arrow {
    image: none;
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-top: 6px solid #2c3e50;
    margin-right: 5px;
}

/* ===== Метки ===== */
QLabel { color: #2c3e50; font-size: 12px; }

/* ===== Чекбоксы и радио ===== */
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; }
QCheckBox::indicator:unchecked { border: 2px solid #c0c9d4; background-color: #ffffff; }
QCheckBox::indicator:checked {
    border: 2px solid #2e86de;
    background-color: #2e86de;
}
QRadioButton::indicator { width: 16px; height: 16px; }
QRadioButton::indicator:unchecked { border: 2px solid #c0c9d4; border-radius: 8px; }
QRadioButton::indicator:checked {
    border: 2px solid #2e86de;
    border-radius: 8px;
    background-color: #2e86de;
}

/* ===== Списки / дроп-зона ===== */
QListWidget {
    background-color: #ffffff;
    border: 2px dashed #aab6c4;
    border-radius: 8px;
    padding: 8px;
    color: #55606e;
}
QListWidget::item {
    padding: 6px;
    background-color: transparent;
}
QListWidget::item:selected { background-color: #dbe7f6; color: #1b4e7a; }

/* ===== Меню ===== */
QMenuBar { background-color: #e8ecf2; color: #2c3e50; }
QMenuBar::item { background-color: transparent; padding: 5px 12px; }
QMenuBar::item:selected { background-color: #d5e3f4; }

/* ===== Скроллбары ===== */
QScrollBar:vertical { background: #e8ecf2; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #aebccb; border-radius: 5px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: #2e86de; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: #e8ecf2; height: 10px; margin: 0; }
QScrollBar::handle:horizontal { background: #aebccb; border-radius: 5px; min-width: 24px; }
QScrollBar::handle:horizontal:hover { background: #2e86de; }

/* ===== Табы ===== */
QTabWidget::pane { border: 1px solid #d3dbe6; background-color: #ffffff; }
QTabBar::tab {
    background-color: #e9edf2;
    color: #55606e;
    padding: 7px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #ffffff;
    color: #1b4e7a;
    border-top: 2px solid #2e86de;
}
"""


def apply_theme(widget) -> None:
    """Применяет глобальную тему к главному окну (или любому виджету)."""
    try:
        widget.setStyleSheet(GLOBAL_QSS)
    except Exception:  # noqa: BLE001 - не критично для запуска
        pass