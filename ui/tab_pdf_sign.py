"""Tab 1: PDF Split & Automatic Signature UI + Rule Editor Dialog."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.i18n import I18n
from core.pdf_sign import (
    DEFAULT_CONFIG_PATH,
    clone_default_rules,
    load_rules,
    run_split_and_sign,
    save_rules,
)
from ui.preview_dialog import SignaturePreviewDialog
from ui.widgets import PathPickerRow, WatermarkTableWidget, WorkerThread


class RuleEditorDialog(QDialog):
    """Modal dialog for creating or editing a single signature rule."""

    def __init__(self, i18n: I18n, rule: Dict[str, Any], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.i18n = i18n
        self.rule = rule
        self.setModal(True)
        self.setFixedWidth(480)
        self.setWindowTitle(self.i18n.t("rule_dialog_title"))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        self.base_combo = QComboBox()
        self.base_combo.addItem(self.i18n.t("val_text"), "text")
        self.base_combo.addItem(self.i18n.t("val_coordinate"), "coordinate")
        current_base = str(rule.get("base", "text")).lower()
        self.base_combo.setCurrentIndex(1 if current_base == "coordinate" else 0)
        form.addRow(self.i18n.t("rule_base_label"), self.base_combo)

        self.enabled_chk = QCheckBox(self.i18n.t("rule_enabled_label"))
        self.enabled_chk.setCursor(Qt.PointingHandCursor)
        self.enabled_chk.setChecked(bool(rule.get("enabled", True)))
        form.addRow("", self.enabled_chk)

        self.anchor_edit = QLineEdit(str(rule.get("anchor", "")))
        form.addRow(self.i18n.t("rule_anchor_label"), self.anchor_edit)

        image_row = QHBoxLayout()
        image_row.setSpacing(6)
        self.image_edit = QLineEdit(str(rule.get("image", "")))
        pick_img_btn = QPushButton(self.i18n.t("btn_browse"))
        pick_img_btn.setCursor(Qt.PointingHandCursor)
        pick_img_btn.clicked.connect(self._pick_image)
        image_row.addWidget(self.image_edit, 1)
        image_row.addWidget(pick_img_btn)
        form.addRow(self.i18n.t("rule_image_label"), image_row)

        self.offset_x_edit = QLineEdit(str(rule.get("offset_x", 0)))
        self.offset_y_edit = QLineEdit(str(rule.get("offset_y", 0)))
        self.width_edit = QLineEdit(str(rule.get("width", 60)))
        self.height_edit = QLineEdit(str(rule.get("height", 43)))
        self.page_edit = QLineEdit(str(rule.get("page", "all")))

        form.addRow(self.i18n.t("rule_offset_x_label"), self.offset_x_edit)
        form.addRow(self.i18n.t("rule_offset_y_label"), self.offset_y_edit)
        form.addRow(self.i18n.t("rule_width_label"), self.width_edit)
        form.addRow(self.i18n.t("rule_height_label"), self.height_edit)
        form.addRow(self.i18n.t("rule_page_label"), self.page_edit)

        layout.addLayout(form)

        help_lbl = QLabel(self.i18n.t("rule_help"))
        help_lbl.setObjectName("PageDesc")
        help_lbl.setWordWrap(True)
        layout.addWidget(help_lbl)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        cancel_btn = QPushButton(self.i18n.t("btn_cancel"))
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton(self.i18n.t("btn_save"))
        save_btn.setObjectName("PrimaryButton")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _pick_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.i18n.t("dlg_pick_image"),
            "",
            "Images (*.png *.jpg *.jpeg)",
        )
        if path:
            self.image_edit.setText(path)

    def _save(self) -> None:
        numeric_fields = [
            ("offset_x", self.offset_x_edit, self.i18n.t("rule_offset_x_label")),
            ("offset_y", self.offset_y_edit, self.i18n.t("rule_offset_y_label")),
            ("width", self.width_edit, self.i18n.t("rule_width_label")),
            ("height", self.height_edit, self.i18n.t("rule_height_label")),
        ]
        parsed: Dict[str, float] = {}
        for key, edit, label in numeric_fields:
            try:
                parsed[key] = float(edit.text().strip())
            except ValueError:
                QMessageBox.critical(
                    self,
                    self.i18n.t("msg_error"),
                    self.i18n.t("err_numeric_field", field=label),
                )
                edit.setFocus()
                return

        self.rule["enabled"] = self.enabled_chk.isChecked()
        self.rule["base"] = self.base_combo.currentData()
        self.rule["anchor"] = self.anchor_edit.text().strip()
        self.rule["image"] = self.image_edit.text().strip()
        self.rule["offset_x"] = parsed["offset_x"]
        self.rule["offset_y"] = parsed["offset_y"]
        self.rule["width"] = parsed["width"]
        self.rule["height"] = parsed["height"]
        self.rule["page"] = self.page_edit.text().strip() or "all"
        self.accept()


class PdfSignTab(QWidget):
    """Module 01: PDF Split & Automatic Signing."""

    def __init__(self, i18n: I18n, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.i18n = i18n
        self.rules: List[Dict[str, Any]] = load_rules()
        self._worker: Optional[WorkerThread] = None
        self._last_output_dir: str = ""

        self._build_ui()
        self.retranslate_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 16)
        root.setSpacing(12)

        # Header
        self.title_lbl = QLabel()
        self.title_lbl.setObjectName("PageTitle")
        self.desc_lbl = QLabel()
        self.desc_lbl.setObjectName("PageDesc")
        self.desc_lbl.setWordWrap(True)
        root.addWidget(self.title_lbl)
        root.addWidget(self.desc_lbl)

        # File pickers card (2x2 grid for compact overview)
        file_card = QFrame()
        file_card.setObjectName("Card")
        grid = QGridLayout(file_card)
        grid.setContentsMargins(14, 12, 14, 12)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(8)

        self.pdf_picker = PathPickerRow(
            "", mode="file", file_filter="PDF Files (*.pdf)", extensions=(".pdf",)
        )
        self.excel_picker = PathPickerRow(
            "", mode="file", file_filter="Excel Files (*.xlsx *.xlsm)", extensions=(".xlsx", ".xlsm")
        )
        self.output_picker = PathPickerRow("", mode="dir")
        self.sig_picker = PathPickerRow("", mode="dir")

        grid.addWidget(self.pdf_picker, 0, 0)
        grid.addWidget(self.excel_picker, 0, 1)
        grid.addWidget(self.output_picker, 1, 0)
        grid.addWidget(self.sig_picker, 1, 1)
        root.addWidget(file_card)

        # Rules header + action strip
        rules_bar = QHBoxLayout()
        self.rules_title_lbl = QLabel()
        self.rules_title_lbl.setObjectName("SectionTitle")
        rules_bar.addWidget(self.rules_title_lbl)
        rules_bar.addStretch(1)

        self.add_btn = QPushButton()
        self.edit_btn = QPushButton()
        self.del_btn = QPushButton()
        self.save_btn = QPushButton()
        self.load_btn = QPushButton()
        self.reset_btn = QPushButton()
        self.preview_sign_btn = QPushButton()

        for btn in (
            self.preview_sign_btn,
            self.add_btn,
            self.edit_btn,
            self.del_btn,
            self.save_btn,
            self.load_btn,
            self.reset_btn,
        ):
            btn.setCursor(Qt.PointingHandCursor)
            rules_bar.addWidget(btn)

        self.preview_sign_btn.clicked.connect(self._open_preview)
        self.add_btn.clicked.connect(self._add_rule)
        self.edit_btn.clicked.connect(self._edit_rule)
        self.del_btn.clicked.connect(self._delete_rule)
        self.save_btn.clicked.connect(self._save_rules)
        self.load_btn.clicked.connect(self._load_rules)
        self.reset_btn.clicked.connect(self._reset_rules)
        root.addLayout(rules_bar)

        # Rules table with watermark
        self.table = WatermarkTableWidget(0, 9)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setMinimumHeight(180)
        self.table.cellDoubleClicked.connect(lambda _r, _c: self._edit_rule())
        root.addWidget(self.table, 3)

        self.empty_rules_lbl = QLabel()
        self.empty_rules_lbl.setObjectName("EmptyHint")
        self.empty_rules_lbl.setAlignment(Qt.AlignCenter)
        root.addWidget(self.empty_rules_lbl)

        # Action & progress bar
        run_bar = QHBoxLayout()
        run_bar.setSpacing(10)

        self.status_banner = QLabel()
        self.status_banner.setObjectName("StatusBanner")
        run_bar.addWidget(self.status_banner, 1)

        self.open_out_btn = QPushButton()
        self.open_out_btn.setCursor(Qt.PointingHandCursor)
        self.open_out_btn.setEnabled(False)
        self.open_out_btn.clicked.connect(self._open_output_dir)
        run_bar.addWidget(self.open_out_btn)

        self.run_btn = QPushButton()
        self.run_btn.setObjectName("PrimaryButton")
        self.run_btn.setCursor(Qt.PointingHandCursor)
        self.run_btn.clicked.connect(self._start_process)
        run_bar.addWidget(self.run_btn)
        root.addLayout(run_bar)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
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
        self.log_box.setMaximumHeight(140)
        root.addWidget(self.log_box, 1)

    def set_dark_mode(self, dark: bool) -> None:
        self.table.set_dark_mode(dark)

    def retranslate_ui(self) -> None:
        t = self.i18n.t
        self.title_lbl.setText(t("pdf_header_title"))
        self.desc_lbl.setText(t("pdf_header_desc"))

        self.pdf_picker.set_texts(t("lbl_source_pdf"), t("btn_browse"), t("not_selected"), t("dlg_pick_pdf"))
        self.excel_picker.set_texts(t("lbl_excel_split"), t("btn_browse"), t("not_selected"), t("dlg_pick_excel"))
        self.output_picker.set_texts(t("lbl_output_dir"), t("btn_browse"), t("not_selected"), t("dlg_pick_output"))
        self.sig_picker.set_texts(t("lbl_sig_dir"), t("btn_browse"), t("not_selected"), t("dlg_pick_sig_dir"))

        self.rules_title_lbl.setText(t("rules_title"))
        self.empty_rules_lbl.setText(t("rules_empty"))
        self.preview_sign_btn.setText(t("btn_preview_sign"))
        self.add_btn.setText(t("btn_add_rule"))
        self.edit_btn.setText(t("btn_edit_rule"))
        self.del_btn.setText(t("btn_delete_rule"))
        self.save_btn.setText(t("btn_save_rules"))
        self.load_btn.setText(t("btn_load_rules"))
        self.reset_btn.setText(t("btn_reset_rules"))

        self.open_out_btn.setText(t("btn_open_folder"))
        self.run_btn.setText(t("btn_run_pdf_sign"))
        self.log_lbl.setText(t("log_title"))
        self.clear_log_btn.setText(t("btn_clear_log"))

        self.table.setHorizontalHeaderLabels(
            [
                t("col_enabled"),
                t("col_base"),
                t("col_anchor"),
                t("col_image"),
                t("col_x"),
                t("col_y"),
                t("col_width"),
                t("col_height"),
                t("col_page"),
            ]
        )
        widths = [64, 92, 185, 145, 58, 58, 62, 62, 78]
        for idx, w in enumerate(widths):
            self.table.setColumnWidth(idx, w)

        if self._worker is None or not self._worker.isRunning():
            self._set_status(t("state_idle"), "idle")

        self._refresh_rules()

    def _set_status(self, message: str, state: str = "idle") -> None:
        self.status_banner.setText(message)
        self.status_banner.setProperty("state", state)
        self.status_banner.style().unpolish(self.status_banner)
        self.status_banner.style().polish(self.status_banner)

    def _refresh_rules(self) -> None:
        t = self.i18n.t
        self.table.setRowCount(len(self.rules))
        self.empty_rules_lbl.setVisible(len(self.rules) == 0)

        for row_idx, rule in enumerate(self.rules):
            enabled_txt = t("val_yes") if rule.get("enabled", True) else t("val_no")
            base_raw = str(rule.get("base", "text")).lower()
            base_txt = t("val_coordinate") if base_raw == "coordinate" else t("val_text")

            page_raw = str(rule.get("page", "all")).strip().lower()
            if page_raw in ("", "all", "semua"):
                page_txt = t("val_page_all")
            elif page_raw == "first":
                page_txt = t("val_page_first")
            elif page_raw == "last":
                page_txt = t("val_page_last")
            else:
                page_txt = page_raw

            image_name = os.path.basename(str(rule.get("image", "")))
            values = [
                enabled_txt,
                base_txt,
                str(rule.get("anchor", "")),
                image_name,
                str(rule.get("offset_x", 0)),
                str(rule.get("offset_y", 0)),
                str(rule.get("width", 60)),
                str(rule.get("height", 43)),
                page_txt,
            ]
            for col_idx, val in enumerate(values):
                item = QTableWidgetItem(val)
                if col_idx in (0, 1, 4, 5, 6, 7, 8):
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, col_idx, item)

    def _selected_row(self) -> Optional[int]:
        row = self.table.currentRow()
        return row if 0 <= row < len(self.rules) else None

    def _open_preview(self) -> None:
        t = self.i18n.t
        pdf_path = self.pdf_picker.path()
        if not pdf_path or not os.path.isfile(pdf_path):
            self._set_status(t("preview_err_no_pdf"), "error")
            QMessageBox.warning(self, t("msg_warning"), t("preview_err_no_pdf"))
            return

        try:
            dlg = SignaturePreviewDialog(
                i18n=self.i18n,
                pdf_path=pdf_path,
                rules=self.rules,
                signature_dir=self.sig_picker.path(),
                parent=self,
            )
        except Exception as exc:
            self._set_status(f"{t('state_error')} {exc}", "error")
            QMessageBox.critical(self, t("msg_error"), str(exc))
            return

        if dlg.exec() == QDialog.Accepted:
            self.rules = dlg.edited_rules
            self._refresh_rules()

    def _add_rule(self) -> None:
        new_rule: Dict[str, Any] = {
            "enabled": True,
            "base": "text",
            "anchor": "",
            "image": "",
            "offset_x": -5.0,
            "offset_y": 18.0,
            "width": 60.0,
            "height": 43.0,
            "page": "all",
        }
        dlg = RuleEditorDialog(self.i18n, new_rule, self)
        if dlg.exec() == QDialog.Accepted:
            self.rules.append(new_rule)
            self._refresh_rules()
            self.table.selectRow(len(self.rules) - 1)

    def _edit_rule(self) -> None:
        row = self._selected_row()
        if row is None:
            QMessageBox.warning(self, self.i18n.t("msg_warning"), self.i18n.t("err_select_rule_first"))
            return
        dlg = RuleEditorDialog(self.i18n, self.rules[row], self)
        if dlg.exec() == QDialog.Accepted:
            self._refresh_rules()
            self.table.selectRow(row)

    def _delete_rule(self) -> None:
        row = self._selected_row()
        if row is None:
            QMessageBox.warning(self, self.i18n.t("msg_warning"), self.i18n.t("err_select_rule_first"))
            return
        del self.rules[row]
        self._refresh_rules()

    def _save_rules(self) -> None:
        saved_path = save_rules(self.rules, DEFAULT_CONFIG_PATH)
        QMessageBox.information(
            self,
            self.i18n.t("msg_info"),
            self.i18n.t("msg_rules_saved", path=saved_path),
        )

    def _load_rules(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.i18n.t("dlg_pick_json"),
            os.path.dirname(DEFAULT_CONFIG_PATH),
            "JSON Files (*.json)",
        )
        if path:
            self.rules = load_rules(path)
            self._refresh_rules()
            QMessageBox.information(
                self,
                self.i18n.t("msg_info"),
                self.i18n.t("msg_rules_loaded", path=path),
            )

    def _reset_rules(self) -> None:
        answer = QMessageBox.question(
            self,
            self.i18n.t("msg_confirm"),
            self.i18n.t("msg_reset_confirm"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer == QMessageBox.Yes:
            self.rules = clone_default_rules()
            self._refresh_rules()

    def _open_output_dir(self) -> None:
        target = self._last_output_dir or self.output_picker.path()
        if target and os.path.isdir(target):
            QDesktopServices.openUrl(QUrl.fromLocalFile(target))

    def _append_log(self, text: str) -> None:
        self.log_box.appendPlainText(text)

    def _set_running(self, running: bool) -> None:
        for widget in (
            self.run_btn,
            self.preview_sign_btn,
            self.add_btn,
            self.edit_btn,
            self.del_btn,
            self.save_btn,
            self.load_btn,
            self.reset_btn,
        ):
            widget.setEnabled(not running)
        self.progress_bar.setVisible(running)
        if running:
            self.progress_bar.setValue(0)

    def _start_process(self) -> None:
        t = self.i18n.t
        pdf_path = self.pdf_picker.path()
        excel_path = self.excel_picker.path()
        output_dir = self.output_picker.path()
        sig_dir = self.sig_picker.path()

        if not pdf_path or not os.path.isfile(pdf_path):
            self._set_status(t("err_select_pdf"), "error")
            QMessageBox.warning(self, t("msg_warning"), t("err_select_pdf"))
            return
        if not excel_path or not os.path.isfile(excel_path):
            self._set_status(t("err_select_excel"), "error")
            QMessageBox.warning(self, t("msg_warning"), t("err_select_excel"))
            return
        if not output_dir:
            self._set_status(t("err_select_output"), "error")
            QMessageBox.warning(self, t("msg_warning"), t("err_select_output"))
            return
        if not sig_dir or not os.path.isdir(sig_dir):
            self._set_status(t("err_select_sig_dir"), "error")
            QMessageBox.warning(self, t("msg_warning"), t("err_select_sig_dir"))
            return

        active_rules = [dict(r) for r in self.rules if r.get("enabled", True)]
        if not active_rules:
            self._set_status(t("err_no_active_rules"), "error")
            QMessageBox.warning(self, t("msg_warning"), t("err_no_active_rules"))
            return

        self.log_box.clear()
        self._append_log(t("log_pdf_start"))
        self._append_log(t("log_pdf_step1"))
        self._set_status(t("state_running"), "running")
        self._set_running(True)

        self._worker = WorkerThread(
            run_split_and_sign,
            pdf_path=pdf_path,
            excel_path=excel_path,
            output_dir=output_dir,
            signature_dir=sig_dir,
            rules=active_rules,
        )
        self._worker.log_signal.connect(self._append_log)
        self._worker.progress_signal.connect(self._on_progress)
        self._worker.finished_signal.connect(self._on_finished)
        self._worker.error_signal.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, current: int, total: int) -> None:
        if total > 0:
            self.progress_bar.setValue(int(current * 100 / total))

    def _on_finished(self, result: Dict[str, Any]) -> None:
        t = self.i18n.t
        self._set_running(False)
        self._last_output_dir = self.output_picker.path()
        self.open_out_btn.setEnabled(True)
        self._append_log(t("log_pdf_done"))
        self._set_status(t("state_done"), "done")
        QMessageBox.information(
            self,
            t("msg_done"),
            t(
                "msg_pdf_done",
                split_dir=result["split_dir"],
                signed_dir=result["signed_dir"],
                count=result["count"],
            ),
        )

    def _on_error(self, message: str) -> None:
        t = self.i18n.t
        self._set_running(False)
        self._append_log(f"[ERROR] {message}")
        self._set_status(f"{t('state_error')} {message}", "error")
        QMessageBox.critical(self, t("msg_error"), message)
