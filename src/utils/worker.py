# -*- coding: utf-8 -*-
"""
Фоновый исполнитель задач на основе QThread.

Позволяет выполнять тяжёлую работу (анализ Excel-файлов, поиск схем)
в отдельном потоке, не блокируя поток графического интерфейса.
UI-обновления выносятся в обратные вызовы finished/failed, которые
выполняются уже в главном потоке (Qt гарантирует это для сигналов).
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from PyQt5.QtCore import QThread, pyqtSignal


class BackgroundWorker(QThread):
    """Выполняет callable в фоновом потоке и сигнализирует о результате."""

    #: Вызывается в главном потоке с (result,) при успехе.
    finished = pyqtSignal(object)
    #: Вызывается в главном потоке с (error_message,) при исключении.
    failed = pyqtSignal(str)

    def __init__(
        self,
        fn: Callable[..., Any],
        *args: Any,
        on_success: Optional[Callable[[Any], None]] = None,
        on_failure: Optional[Callable[[str], None]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Args:
            fn: функция, выполняемая в фоновом потоке.
            on_success: необязательный обработчик результата (в главном потоке).
            on_failure: необязательный обработчик ошибки (в главном потоке).
        """
        super().__init__(parent=None)
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        if on_success is not None:
            self.finished.connect(on_success)
        if on_failure is not None:
            self.failed.connect(on_failure)

    def run(self) -> None:  # noqa: D102
        try:
            result = self._fn(*self._args, **self._kwargs)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
        else:
            self.finished.emit(result)