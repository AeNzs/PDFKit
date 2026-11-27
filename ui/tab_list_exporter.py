"""Tab 3: Folder & File List Exporter (Programs 2, 3, and 5 combined)."""

from __future__ import annotations

import os
from typing import Dict, Optional

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.i18n import I18n
from core.list_exporter import preview_exports, write_exports
from ui.widgets import PathPickerRow


class ListExporterTab(QWidget):
    """Module 03: Export folderlist.txt, filelist.txt, and folder_file_list.txt."""

    def __init__(self, i18n: I18n, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.i18n = i18n
        self._last_preview: Dict[str, str] = {}

        self._build_ui()
        self.retranslate_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 16)
        root.setSpacing(12)

        self.title_lbl = QLabel()
        self.title_lbl.setObjectName("PageTitle")
        self.desc_lbl = QLabel()
        self.desc_lbl.setObjectName("PageDesc")
        self.desc_lbl.setWordWrap(True)
        root.addWidget(self.title_lbl)
        root.addWidget(self.desc_lbl)

        # Split layout: controls on left, live preview tabs on right
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(12)

        left_card = QFrame()
        left_card.setObjectName("Card")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(18, 18, 18, 18)
        left_layout.setSpacing(14)

        self.folder_picker = PathPickerRow("", mode="dir")
        left_layout.addWidget(self.folder_picker)

        self.options_lbl = QLabel()
        self.options_lbl.setObjectName("SectionTitle")
        left_layout.addWidget(self.options_lbl)

        self.chk_folderlist = QCheckBox()
        self.chk_filelist = QCheckBox()
        self.chk_folder_file_list = QCheckBox()

        for chk in (self.chk_folderlist, self.chk_filelist, self.chk_folder_file_list):
            chk.setChecked(True)
            chk.setCursor(Qt.PointingHandCursor)
            left_layout.addWidget(chk)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.preview_btn = QPushButton()
        self.preview_btn.setCursor(Qt.PointingHandCursor)
        self.preview_btn.clicked.connect(self._run_preview)

        self.open_btn = QPushButton()
        self.open_btn.setCursor(Qt.PointingHandCursor)
        self.open_btn.clicked.connect(self._open_folder)

        self.export_btn = QPushButton()
        self.export_btn.setObjectName("PrimaryButton")
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.clicked.connect(self._run_export)

        btn_row.addWidget(self.preview_btn)
        btn_row.addWidget(self.open_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(self.export_btn)
        left_layout.addLayout(btn_row)

        self.status_banner = QLabel()
        self.status_banner.setObjectName("StatusBanner")
        self.status_banner.setWordWrap(True)
        left_layout.addWidget(self.status_banner)
        left_layout.addStretch(1)

        right_card = QFrame()
        right_card.setObjectName("Card")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(16, 14, 16, 14)
        right_layout.setSpacing(10)

        self.preview_title_lbl = QLabel()
        self.preview_title_lbl.setObjectName("SectionTitle")
        right_layout.addWidget(self.preview_title_lbl)

        self.preview_empty_lbl = QLabel()
        self.preview_empty_lbl.setObjectName("EmptyHint")
        self.preview_empty_lbl.setWordWrap(True)
        self.preview_empty_lbl.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.preview_empty_lbl, 1)

        self.preview_tabs = QTabWidget()
        self.preview_tabs.setVisible(False)
        right_layout.addWidget(self.preview_tabs, 1)

        splitter.addWidget(left_card)
        splitter.addWidget(right_card)
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 6)
        root.addWidget(splitter, 1)

    def retranslate_ui(self) -> None:
        t = self.i18n.t
        self.title_lbl.setText(t("export_header_title"))
        self.desc_lbl.setText(t("export_header_desc"))
        self.folder_picker.set_texts(t("lbl_scan_folder"), t("btn_browse"), t("not_selected"), t("lbl_scan_folder"))
        self.options_lbl.setText(t("export_options_title"))
        self.chk_folderlist.setText(t("opt_folderlist"))
        self.chk_filelist.setText(t("opt_filelist"))
        self.chk_folder_file_list.setText(t("opt_folder_file_list"))
        self.preview_btn.setText(t("btn_preview_export"))
        self.open_btn.setText(t("btn_open_folder"))
        self.export_btn.setText(t("btn_run_export"))
        self.preview_title_lbl.setText(t("preview_title"))
        self.preview_empty_lbl.setText(t("preview_empty"))
        self._set_status(t("state_idle"), "idle")

    def _set_status(self, message: str, state: str = "idle") -> None:
        self.status_banner.setText(message)
        self.status_banner.setProperty("state", state)
        self.status_banner.style().unpolish(self.status_banner)
        self.status_banner.style().polish(self.status_banner)

    def _validate(self) -> Optional[str]:
        t = self.i18n.t
        target = self.folder_picker.path()
        if not target or not os.path.isdir(target):
            self._set_status(t("err_select_scan_folder"), "error")
            QMessageBox.warning(self, t("msg_warning"), t("err_select_scan_folder"))
            return None
        if not (
            self.chk_folderlist.isChecked()
            or self.chk_filelist.isChecked()
            or self.chk_folder_file_list.isChecked()
        ):
            self._set_status(t("err_select_export_option"), "error")
            QMessageBox.warning(self, t("msg_warning"), t("err_select_export_option"))
            return None
        return target

    def _show_preview(self, outputs: Dict[str, str]) -> None:
        self._last_preview = outputs
        self.preview_tabs.clear()
        for filename, content in outputs.items():
            editor = QPlainTextEdit()
            editor.setReadOnly(True)
            editor.setPlainText(content if content.strip() else "(empty)")
            self.preview_tabs.addTab(editor, filename)

        has_tabs = len(outputs) > 0
        self.preview_tabs.setVisible(has_tabs)
        self.preview_empty_lbl.setVisible(not has_tabs)

    def _run_preview(self) -> None:
        target = self._validate()
        if not target:
            return
        try:
            outputs = preview_exports(
                target,
                include_folders=self.chk_folderlist.isChecked(),
                include_files=self.chk_filelist.isChecked(),
                include_folder_files=self.chk_folder_file_list.isChecked(),
            )
            self._show_preview(outputs)
            self._set_status(f"{self.i18n.t('state_done')} ({len(outputs)})", "done")
        except Exception as exc:
            self._set_status(f"{self.i18n.t('state_error')} {exc}", "error")
            QMessageBox.critical(self, self.i18n.t("msg_error"), str(exc))

    def _run_export(self) -> None:
        target = self._validate()
        if not target:
            return
        try:
            outputs = preview_exports(
                target,
                include_folders=self.chk_folderlist.isChecked(),
                include_files=self.chk_filelist.isChecked(),
                include_folder_files=self.chk_folder_file_list.isChecked(),
            )
            written = write_exports(
                target,
                include_folders=self.chk_folderlist.isChecked(),
                include_files=self.chk_filelist.isChecked(),
                include_folder_files=self.chk_folder_file_list.isChecked(),
            )
            self._show_preview(outputs)
            self._set_status(self.i18n.t("state_done"), "done")
            QMessageBox.information(
                self,
                self.i18n.t("msg_done"),
                self.i18n.t("msg_export_done", files="\n".join(written)),
            )
        except Exception as exc:
            self._set_status(f"{self.i18n.t('state_error')} {exc}", "error")
            QMessageBox.critical(self, self.i18n.t("msg_error"), str(exc))

    def _open_folder(self) -> None:
        target = self.folder_picker.path()
        if target and os.path.isdir(target):
            QDesktopServices.openUrl(QUrl.fromLocalFile(target))
