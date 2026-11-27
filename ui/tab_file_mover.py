"""Tab 2: Universal File Mover via mapping.xlsx (Program 4)."""

from __future__ import annotations

import os
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.file_mover import MoveEntry, execute_file_moves, find_mapping_excel, load_move_entries
from core.i18n import I18n
from ui.widgets import PathPickerRow, WatermarkTableWidget, WorkerThread


class FileMoverTab(QWidget):
    """Module 02: Batch File Mover using Excel mapping."""

    def __init__(self, i18n: I18n, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.i18n = i18n
        self.entries: List[MoveEntry] = []
        self._worker: Optional[WorkerThread] = None

        self._build_ui()
        self.retranslate_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 16)
        root.setSpacing(12)

        self.title_lbl = QLabel()
        self.title_lbl.setObjectName("PageTitle")
        self.desc_lbl = QLabel()
        self.desc_lbl.setObjectName("PageDesc")
        self.desc_lbl.setWordWrap(True)
        root.addWidget(self.title_lbl)
        root.addWidget(self.desc_lbl)

        # Input card
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(8)

        self.root_picker = PathPickerRow("", mode="dir")
        self.mapping_picker = PathPickerRow(
            "", mode="file", file_filter="Excel Files (*.xlsx *.xlsm)", extensions=(".xlsx", ".xlsm")
        )
        card_layout.addWidget(self.root_picker)
        card_layout.addWidget(self.mapping_picker)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        self.auto_find_btn = QPushButton()
        self.auto_find_btn.setCursor(Qt.PointingHandCursor)
        self.auto_find_btn.clicked.connect(self._auto_find_mapping)

        self.preview_btn = QPushButton()
        self.preview_btn.setCursor(Qt.PointingHandCursor)
        self.preview_btn.clicked.connect(self._load_preview)

        self.open_root_btn = QPushButton()
        self.open_root_btn.setCursor(Qt.PointingHandCursor)
        self.open_root_btn.clicked.connect(self._open_root)

        self.move_btn = QPushButton()
        self.move_btn.setObjectName("PrimaryButton")
        self.move_btn.setCursor(Qt.PointingHandCursor)
        self.move_btn.clicked.connect(self._start_move)

        action_row.addWidget(self.auto_find_btn)
        action_row.addWidget(self.preview_btn)
        action_row.addWidget(self.open_root_btn)
        action_row.addStretch(1)
        action_row.addWidget(self.move_btn)
        card_layout.addLayout(action_row)
        root.addWidget(card)

        # Real summary metrics strip (hidden until preview/move has real data)
        self.stats_frame = QWidget()
        stats_layout = QHBoxLayout(self.stats_frame)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(10)

        self.stat_total_val, self.stat_total_lbl = self._make_stat_card(stats_layout)
        self.stat_moved_val, self.stat_moved_lbl = self._make_stat_card(stats_layout)
        self.stat_missing_val, self.stat_missing_lbl = self._make_stat_card(stats_layout)
        self.stat_error_val, self.stat_error_lbl = self._make_stat_card(stats_layout)
        self.stats_frame.setVisible(False)
        root.addWidget(self.stats_frame)

        # Preview table with watermark
        self.table = WatermarkTableWidget(0, 4)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setMinimumHeight(180)
        root.addWidget(self.table, 3)

        self.empty_lbl = QLabel()
        self.empty_lbl.setObjectName("EmptyHint")
        self.empty_lbl.setAlignment(Qt.AlignCenter)
        self.empty_lbl.setWordWrap(True)
        root.addWidget(self.empty_lbl)

        # Status + progress
        self.status_banner = QLabel()
        self.status_banner.setObjectName("StatusBanner")
        root.addWidget(self.status_banner)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)
        root.addWidget(self.progress_bar)

        # Log area
        log_head = QHBoxLayout()
        self.log_lbl = QLabel()
        self.log_lbl.setObjectName("SectionTitle")
        self.clear_log_btn = QPushButton()
        self.clear_log_btn.setCursor(Qt.PointingHandCursor)
        self.clear_log_btn.clicked.connect(lambda: self.log_box.clear())
        log_head.addWidget(self.log_lbl)
        log_head.addStretch(1)
        log_head.addWidget(self.clear_log_btn)
        root.addLayout(log_head)

        self.log_box = QPlainTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumHeight(130)
        root.addWidget(self.log_box, 1)

    def _make_stat_card(self, parent_layout: QHBoxLayout) -> tuple[QLabel, QLabel]:
        box = QFrame()
        box.setObjectName("StatCard")
        v = QVBoxLayout(box)
        v.setContentsMargins(12, 8, 12, 8)
        v.setSpacing(2)
        val_lbl = QLabel("0")
        val_lbl.setObjectName("StatValue")
        name_lbl = QLabel("")
        name_lbl.setObjectName("StatLabel")
        v.addWidget(val_lbl)
        v.addWidget(name_lbl)
        parent_layout.addWidget(box, 1)
        return val_lbl, name_lbl

    def set_dark_mode(self, dark: bool) -> None:
        self.table.set_dark_mode(dark)

    def retranslate_ui(self) -> None:
        t = self.i18n.t
        self.title_lbl.setText(t("mover_header_title"))
        self.desc_lbl.setText(t("mover_header_desc"))
        self.root_picker.set_texts(t("lbl_root_folder"), t("btn_browse"), t("not_selected"), t("lbl_root_folder"))
        self.mapping_picker.set_texts(
            t("lbl_mapping_excel"), t("btn_browse"), t("not_selected"), t("dlg_pick_excel")
        )
        self.auto_find_btn.setText(t("btn_auto_find"))
        self.preview_btn.setText(t("btn_preview_mapping"))
        self.open_root_btn.setText(t("btn_open_folder"))
        self.move_btn.setText(t("btn_run_move"))
        self.empty_lbl.setText(t("mover_empty"))

        self.stat_total_lbl.setText(t("mover_stat_total"))
        self.stat_moved_lbl.setText(t("mover_stat_moved"))
        self.stat_missing_lbl.setText(t("mover_stat_missing"))
        self.stat_error_lbl.setText(t("mover_stat_error"))

        self.table.setHorizontalHeaderLabels(
            [
                t("mover_col_row"),
                t("mover_col_file"),
                t("mover_col_dest"),
                t("mover_col_status"),
            ]
        )
        self.table.setColumnWidth(0, 64)
        self.table.setColumnWidth(1, 290)
        self.table.setColumnWidth(2, 230)

        self.log_lbl.setText(t("log_title"))
        self.clear_log_btn.setText(t("btn_clear_log"))

        if self._worker is None or not self._worker.isRunning():
            self._set_status(t("state_idle"), "idle")

        self._render_table()

    def _set_status(self, message: str, state: str = "idle") -> None:
        self.status_banner.setText(message)
        self.status_banner.setProperty("state", state)
        self.status_banner.style().unpolish(self.status_banner)
        self.status_banner.style().polish(self.status_banner)

    def _status_text(self, status: str, err: str = "") -> str:
        t = self.i18n.t
        mapping = {
            "ready": t("mover_status_ready"),
            "missing": t("mover_status_missing"),
            "moved": t("mover_status_moved"),
            "error": f"{t('mover_status_error')}: {err}" if err else t("mover_status_error"),
        }
        return mapping.get(status, status)

    def _render_table(self) -> None:
        self.table.setRowCount(len(self.entries))
        self.empty_lbl.setVisible(len(self.entries) == 0)
        self.stats_frame.setVisible(len(self.entries) > 0)

        moved = 0
        missing = 0
        errors = 0
        for row_idx, entry in enumerate(self.entries):
            if entry.status == "moved":
                moved += 1
            elif entry.status == "missing":
                missing += 1
            elif entry.status == "error":
                errors += 1

            vals = [
                str(entry.row),
                entry.filename,
                entry.folder_name,
                self._status_text(entry.status, entry.error_message),
            ]
            for col_idx, val in enumerate(vals):
                item = QTableWidgetItem(val)
                if col_idx == 0:
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, col_idx, item)

        self.stat_total_val.setText(str(len(self.entries)))
        self.stat_moved_val.setText(str(moved))
        self.stat_missing_val.setText(str(missing))
        self.stat_error_val.setText(str(errors))

    def _auto_find_mapping(self) -> None:
        t = self.i18n.t
        start = self.root_picker.path() or os.getcwd()
        found = find_mapping_excel(start)
        if not found:
            self._set_status(t("err_mapping_not_found"), "error")
            QMessageBox.warning(self, t("msg_warning"), t("err_mapping_not_found"))
            return
        self.mapping_picker.set_path(found)
        self.root_picker.set_path(os.path.dirname(found))
        QMessageBox.information(self, t("msg_info"), t("msg_mapping_found", path=found))
        self._load_preview()

    def _load_preview(self) -> bool:
        t = self.i18n.t
        root_dir = self.root_picker.path()
        mapping_path = self.mapping_picker.path()

        if not root_dir or not os.path.isdir(root_dir):
            self._set_status(t("err_select_root"), "error")
            QMessageBox.warning(self, t("msg_warning"), t("err_select_root"))
            return False
        if not mapping_path or not os.path.isfile(mapping_path):
            self._set_status(t("err_select_mapping"), "error")
            QMessageBox.warning(self, t("msg_warning"), t("err_select_mapping"))
            return False

        try:
            self.entries = load_move_entries(root_dir, mapping_path)
            self._render_table()
            self._set_status(f"{t('state_idle')} ({len(self.entries)})", "idle")
            return True
        except Exception as exc:
            self._set_status(f"{t('state_error')} {exc}", "error")
            QMessageBox.critical(self, t("msg_error"), str(exc))
            return False

    def _open_root(self) -> None:
        target = self.root_picker.path()
        if target and os.path.isdir(target):
            QDesktopServices.openUrl(QUrl.fromLocalFile(target))

    def _set_running(self, running: bool) -> None:
        for btn in (self.move_btn, self.preview_btn, self.auto_find_btn):
            btn.setEnabled(not running)
        self.progress_bar.setVisible(running)
        if running:
            self.progress_bar.setValue(0)

    def _start_move(self) -> None:
        t = self.i18n.t
        if not self._load_preview():
            return

        ready_count = sum(1 for e in self.entries if e.status == "ready")
        answer = QMessageBox.question(
            self,
            t("msg_confirm"),
            t("msg_move_confirm", ready=ready_count),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        self.log_box.clear()
        self._set_status(t("state_running"), "running")
        self._set_running(True)

        self._worker = WorkerThread(execute_file_moves, self.entries)
        self._worker.log_signal.connect(self.log_box.appendPlainText)
        self._worker.progress_signal.connect(self._on_progress)
        self._worker.finished_signal.connect(self._on_finished)
        self._worker.error_signal.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, current: int, total: int) -> None:
        if total > 0:
            self.progress_bar.setValue(int(current * 100 / total))

    def _on_finished(self, summary: Dict[str, int]) -> None:
        t = self.i18n.t
        self._set_running(False)
        self._render_table()
        self._set_status(t("state_done"), "done")
        QMessageBox.information(
            self,
            t("msg_done"),
            t(
                "msg_move_done",
                moved=summary["moved"],
                not_found=summary["not_found"],
                errors=summary["errors"],
            ),
        )

    def _on_error(self, message: str) -> None:
        t = self.i18n.t
        self._set_running(False)
        self.log_box.appendPlainText(f"[ERROR] {message}")
        self._set_status(f"{t('state_error')} {message}", "error")
        QMessageBox.critical(self, t("msg_error"), message)
