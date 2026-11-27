"""Reusable widgets: drag-drop path picker, watermark table, and worker thread."""

from __future__ import annotations

import os
from typing import Any, Callable, Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent, QFont, QPainter
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QWidget,
)

from core.i18n import WATERMARK_TEXT


class WorkerThread(QThread):
    """Run blocking file/PDF jobs off the UI thread."""

    log_signal = Signal(str)
    progress_signal = Signal(int, int)
    finished_signal = Signal(object)
    error_signal = Signal(str)

    def __init__(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self) -> None:
        try:
            result = self._fn(
                *self._args,
                log=self.log_signal.emit,
                progress=self.progress_signal.emit,
                **self._kwargs,
            )
            self.finished_signal.emit(result)
        except Exception as exc:
            self.error_signal.emit(str(exc))


class DropPathEdit(QLineEdit):
    """Line edit that accepts file or folder drag-and-drop."""

    path_changed = Signal(str)

    def __init__(self, accept_dirs: bool = False, extensions: tuple[str, ...] = ()) -> None:
        super().__init__()
        self._accept_dirs = accept_dirs
        self._extensions = tuple(ext.lower() for ext in extensions)
        self.setAcceptDrops(True)
        self.setProperty("mono", True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                path = urls[0].toLocalFile()
                if self._accept_dirs and os.path.isdir(path):
                    event.acceptProposedAction()
                    return
                if not self._accept_dirs and os.path.isfile(path):
                    if not self._extensions or path.lower().endswith(self._extensions):
                        event.acceptProposedAction()
                        return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            path = urls[0].toLocalFile()
            self.setText(path)
            self.path_changed.emit(path)


class PathPickerRow(QWidget):
    """Label + drag-drop path input + browse button."""

    path_changed = Signal(str)

    def __init__(
        self,
        label_text: str,
        mode: str = "file",
        file_filter: str = "All Files (*.*)",
        dialog_title: str = "Select",
        placeholder: str = "",
        extensions: tuple[str, ...] = (),
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._mode = mode
        self._file_filter = file_filter
        self._dialog_title = dialog_title

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.label = QLabel(label_text)
        self.label.setObjectName("FieldLabel")
        self.label.setFixedWidth(130)

        self.edit = DropPathEdit(accept_dirs=(mode == "dir"), extensions=extensions)
        self.edit.setPlaceholderText(placeholder)
        self.edit.textChanged.connect(self.path_changed.emit)

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.setCursor(Qt.PointingHandCursor)
        self.browse_btn.setFixedWidth(88)
        self.browse_btn.clicked.connect(self._browse)

        layout.addWidget(self.label)
        layout.addWidget(self.edit, 1)
        layout.addWidget(self.browse_btn)

    def _browse(self) -> None:
        current = self.path()
        start_dir = current if os.path.isdir(current) else (os.path.dirname(current) if current else "")
        if self._mode == "dir":
            selected = QFileDialog.getExistingDirectory(self, self._dialog_title, start_dir)
        else:
            selected, _ = QFileDialog.getOpenFileName(
                self, self._dialog_title, start_dir, self._file_filter
            )
        if selected:
            self.set_path(selected)

    def path(self) -> str:
        return self.edit.text().strip()

    def set_path(self, value: str) -> None:
        self.edit.setText(value)

    def set_texts(self, label_text: str, browse_text: str, placeholder: str, dialog_title: str) -> None:
        self.label.setText(label_text)
        self.browse_btn.setText(browse_text)
        self.edit.setPlaceholderText(placeholder)
        self._dialog_title = dialog_title


class WatermarkTableWidget(QTableWidget):
    """QTableWidget with a subtle 'by 开能能' watermark painted onto the viewport."""

    def __init__(self, rows: int = 0, columns: int = 0, parent: Optional[QWidget] = None) -> None:
        super().__init__(rows, columns, parent)
        self._watermark_text = WATERMARK_TEXT
        self._dark_mode = False

    def set_dark_mode(self, dark: bool) -> None:
        self._dark_mode = dark
        self.viewport().update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        font = QFont("Microsoft YaHei UI", 26)
        font.setItalic(True)
        font.setBold(True)
        painter.setFont(font)

        color = QColor(242, 240, 235, 22) if self._dark_mode else QColor(28, 30, 33, 22)
        painter.setPen(color)

        rect = self.viewport().rect()
        painter.drawText(rect.adjusted(0, 0, -18, -14), Qt.AlignRight | Qt.AlignBottom, self._watermark_text)
        painter.end()
