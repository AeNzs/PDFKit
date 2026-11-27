"""Tab 4: Mapping by Logic (Dual-mode: Create Folders from Raw Files OR Scan Existing Folders)."""

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
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.i18n import I18n
from core.logic_mapper import (
    DEFAULT_LOGIC_CONFIG_PATH,
    LogicMatchEntry,
    build_create_from_files_preview,
    build_logic_preview,
    clone_default_config,
    execute_logic_mapping,
    load_logic_config,
    save_logic_config,
)
from ui.widgets import PathPickerRow, WatermarkTableWidget, WorkerThread


class AliasRuleDialog(QDialog):
    """Modal dialog to create or edit a Code -> Company Name ({PT}) alias row."""

    def __init__(self, i18n: I18n, alias: Dict[str, Any], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.i18n = i18n
        self.alias = alias
        self.setModal(True)
        self.setFixedWidth(480)
        self.setWindowTitle(self.i18n.t("logic_alias_dlg_title"))

        t = self.i18n.t
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        self.enabled_chk = QCheckBox(t("rule_enabled_label"))
        self.enabled_chk.setCursor(Qt.PointingHandCursor)
        self.enabled_chk.setChecked(bool(alias.get("enabled", True)))
        form.addRow("", self.enabled_chk)

        self.code_edit = QLineEdit(str(alias.get("match_code", "")))
        self.code_edit.setProperty("mono", True)
        self.code_edit.setPlaceholderText("PJI-MXZ-26001")
        form.addRow(t("logic_alias_dlg_code"), self.code_edit)

        self.pt_edit = QLineEdit(str(alias.get("pt_name", "")))
        self.pt_edit.setPlaceholderText("TEK")
        form.addRow(t("logic_alias_dlg_pt"), self.pt_edit)

        self.month_edit = QLineEdit(str(alias.get("month_override", "")))
        self.month_edit.setPlaceholderText("{BULAN}中国船")
        form.addRow(t("logic_alias_dlg_month"), self.month_edit)

        layout.addLayout(form)

        help_lbl = QLabel(t("logic_alias_dlg_help"))
        help_lbl.setObjectName("PageDesc")
        help_lbl.setWordWrap(True)
        layout.addWidget(help_lbl)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        cancel_btn = QPushButton(t("btn_cancel"))
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton(t("btn_save"))
        save_btn.setObjectName("PrimaryButton")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _save(self) -> None:
        code = self.code_edit.text().strip()
        pt = self.pt_edit.text().strip()
        if not code or not pt:
            QMessageBox.warning(
                self, self.i18n.t("msg_warning"), self.i18n.t("logic_err_alias_fields")
            )
            return
        self.alias["enabled"] = self.enabled_chk.isChecked()
        self.alias["match_code"] = code
        self.alias["pt_name"] = pt
        self.alias["month_override"] = self.month_edit.text().strip()
        self.accept()


class SourceRuleDialog(QDialog):
    """Modal dialog to create or edit one source folder path rule."""

    def __init__(self, i18n: I18n, rule: Dict[str, Any], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.i18n = i18n
        self.rule = rule
        self.setModal(True)
        self.setFixedWidth(540)
        self.setWindowTitle(self.i18n.t("logic_dlg_title"))

        t = self.i18n.t
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        self.enabled_chk = QCheckBox(t("rule_enabled_label"))
        self.enabled_chk.setCursor(Qt.PointingHandCursor)
        self.enabled_chk.setChecked(bool(rule.get("enabled", True)))
        form.addRow("", self.enabled_chk)

        self.name_edit = QLineEdit(str(rule.get("name", "")))
        form.addRow(t("logic_dlg_name"), self.name_edit)

        dir_row = QHBoxLayout()
        dir_row.setSpacing(6)
        self.dir_edit = QLineEdit(str(rule.get("source_dir", "")))
        self.dir_edit.setProperty("mono", True)
        browse_btn = QPushButton(t("btn_browse"))
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.clicked.connect(self._pick_dir)
        dir_row.addWidget(self.dir_edit, 1)
        dir_row.addWidget(browse_btn)
        form.addRow(t("logic_dlg_dir"), dir_row)

        self.action_combo = QComboBox()
        self.action_combo.addItem(t("logic_act_copy"), "copy")
        self.action_combo.addItem(t("logic_act_move"), "move")
        self.action_combo.setCurrentIndex(
            1 if str(rule.get("action", "copy")).lower() == "move" else 0
        )
        form.addRow(t("logic_dlg_action"), self.action_combo)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem(t("logic_mode_token"), "token")
        self.mode_combo.addItem(t("logic_mode_contains"), "contains")
        self.mode_combo.addItem(t("logic_mode_regex"), "regex")
        mode_map = {"token": 0, "contains": 1, "regex": 2}
        self.mode_combo.setCurrentIndex(
            mode_map.get(str(rule.get("match_mode", "token")).lower(), 0)
        )
        form.addRow(t("logic_dlg_mode"), self.mode_combo)

        self.pattern_edit = QLineEdit(str(rule.get("file_pattern", "")))
        self.pattern_edit.setProperty("mono", True)
        self.pattern_edit.setPlaceholderText("{KEY}")
        form.addRow(t("logic_dlg_pattern"), self.pattern_edit)

        self.conflict_combo = QComboBox()
        self.conflict_combo.addItem(t("logic_conf_skip"), "skip")
        self.conflict_combo.addItem(t("logic_conf_overwrite"), "overwrite")
        self.conflict_combo.setCurrentIndex(
            1 if str(rule.get("conflict", "skip")).lower() == "overwrite" else 0
        )
        form.addRow(t("logic_dlg_conflict"), self.conflict_combo)

        self.sub_chk = QCheckBox(t("logic_dlg_sub"))
        self.sub_chk.setCursor(Qt.PointingHandCursor)
        self.sub_chk.setChecked(bool(rule.get("include_subfolders", False)))
        form.addRow("", self.sub_chk)

        layout.addLayout(form)

        help_lbl = QLabel(t("logic_dlg_help"))
        help_lbl.setObjectName("PageDesc")
        help_lbl.setWordWrap(True)
        layout.addWidget(help_lbl)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)

        cancel_btn = QPushButton(t("btn_cancel"))
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton(t("btn_save"))
        save_btn.setObjectName("PrimaryButton")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _pick_dir(self) -> None:
        current = self.dir_edit.text().strip()
        start = current if os.path.isdir(current) else ""
        selected = QFileDialog.getExistingDirectory(self, self.i18n.t("logic_dlg_dir"), start)
        if selected:
            self.dir_edit.setText(selected)

    def _save(self) -> None:
        src_dir = self.dir_edit.text().strip()
        if not src_dir:
            QMessageBox.warning(self, self.i18n.t("msg_warning"), self.i18n.t("logic_err_empty_dir"))
            self.dir_edit.setFocus()
            return

        name = self.name_edit.text().strip() or os.path.basename(src_dir.rstrip("\\/")) or "Source"
        self.rule["enabled"] = self.enabled_chk.isChecked()
        self.rule["name"] = name
        self.rule["source_dir"] = src_dir
        self.rule["action"] = self.action_combo.currentData()
        self.rule["match_mode"] = self.mode_combo.currentData()
        self.rule["file_pattern"] = self.pattern_edit.text().strip()
        self.rule["conflict"] = self.conflict_combo.currentData()
        self.rule["include_subfolders"] = self.sub_chk.isChecked()
        self.accept()


class LogicMapperTab(QWidget):
    """Module 04: Dual-mode Logic File Mapper (no mapping.xlsx required)."""

    def __init__(self, i18n: I18n, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.i18n = i18n
        cfg = load_logic_config()
        self.work_mode: str = cfg["work_mode"]
        self.month_label: str = cfg["month_label"]
        self.folder_template: str = cfg["folder_template"]
        self.file_fallback_regex: str = cfg["file_fallback_regex"]
        self.ignore_keys: str = cfg["ignore_keys"]
        self.target_regex: str = cfg["target_regex"]
        self.target_scan: str = cfg["target_scan"]
        self.aliases: List[Dict[str, Any]] = cfg["aliases"]
        self.rules: List[Dict[str, Any]] = cfg["rules"]
        self.entries: List[LogicMatchEntry] = []
        self._worker: Optional[WorkerThread] = None

        self._build_ui()
        self.retranslate_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 14)
        root.setSpacing(10)

        self.title_lbl = QLabel()
        self.title_lbl.setObjectName("PageTitle")
        self.desc_lbl = QLabel()
        self.desc_lbl.setObjectName("PageDesc")
        self.desc_lbl.setWordWrap(True)
        root.addWidget(self.title_lbl)
        root.addWidget(self.desc_lbl)

        # Top config card
        top_card = QFrame()
        top_card.setObjectName("Card")
        top_layout = QVBoxLayout(top_card)
        top_layout.setContentsMargins(14, 10, 14, 10)
        top_layout.setSpacing(8)

        mode_row = QHBoxLayout()
        mode_row.setSpacing(8)
        self.wmode_lbl = QLabel()
        self.wmode_lbl.setObjectName("FieldLabel")
        self.wmode_lbl.setFixedWidth(130)
        self.wmode_combo = QComboBox()
        self.wmode_combo.currentIndexChanged.connect(self._on_work_mode_changed)
        mode_row.addWidget(self.wmode_lbl)
        mode_row.addWidget(self.wmode_combo, 1)
        top_layout.addLayout(mode_row)

        self.root_picker = PathPickerRow("", mode="dir")
        top_layout.addWidget(self.root_picker)

        # Mode 1 controls: Month + Folder Template + Fallback Regex + Ignore
        self.create_opts_widget = QWidget()
        co_layout = QVBoxLayout(self.create_opts_widget)
        co_layout.setContentsMargins(0, 0, 0, 0)
        co_layout.setSpacing(6)

        row_a = QHBoxLayout()
        row_a.setSpacing(8)
        self.month_lbl = QLabel()
        self.month_lbl.setObjectName("FieldLabel")
        self.month_lbl.setFixedWidth(130)
        self.month_edit = QLineEdit(self.month_label)
        self.month_edit.setFixedWidth(130)

        self.tpl_lbl = QLabel()
        self.tpl_lbl.setObjectName("FieldLabel")
        self.tpl_edit = QLineEdit(self.folder_template)
        self.tpl_edit.setProperty("mono", True)

        row_a.addWidget(self.month_lbl)
        row_a.addWidget(self.month_edit)
        row_a.addSpacing(8)
        row_a.addWidget(self.tpl_lbl)
        row_a.addWidget(self.tpl_edit, 1)
        co_layout.addLayout(row_a)

        row_b = QHBoxLayout()
        row_b.setSpacing(8)
        self.fb_regex_lbl = QLabel()
        self.fb_regex_lbl.setObjectName("FieldLabel")
        self.fb_regex_lbl.setFixedWidth(130)
        self.fb_regex_edit = QLineEdit(self.file_fallback_regex)
        self.fb_regex_edit.setProperty("mono", True)

        self.ignore_lbl = QLabel()
        self.ignore_lbl.setObjectName("FieldLabel")
        self.ignore_edit = QLineEdit(self.ignore_keys)
        self.ignore_edit.setFixedWidth(150)

        row_b.addWidget(self.fb_regex_lbl)
        row_b.addWidget(self.fb_regex_edit, 1)
        row_b.addSpacing(8)
        row_b.addWidget(self.ignore_lbl)
        row_b.addWidget(self.ignore_edit)
        co_layout.addLayout(row_b)
        top_layout.addWidget(self.create_opts_widget)

        # Mode 2 controls: Reference Regex + Extract From
        self.existing_opts_widget = QWidget()
        eo_row = QHBoxLayout(self.existing_opts_widget)
        eo_row.setContentsMargins(0, 0, 0, 0)
        eo_row.setSpacing(8)

        self.regex_lbl = QLabel()
        self.regex_lbl.setObjectName("FieldLabel")
        self.regex_lbl.setFixedWidth(130)
        self.regex_edit = QLineEdit(self.target_regex)
        self.regex_edit.setProperty("mono", True)

        self.scan_lbl = QLabel()
        self.scan_lbl.setObjectName("FieldLabel")
        self.scan_combo = QComboBox()
        self.scan_combo.setMinimumWidth(165)

        eo_row.addWidget(self.regex_lbl)
        eo_row.addWidget(self.regex_edit, 1)
        eo_row.addSpacing(8)
        eo_row.addWidget(self.scan_lbl)
        eo_row.addWidget(self.scan_combo)
        top_layout.addWidget(self.existing_opts_widget)

        root.addWidget(top_card)

        # Vertical splitter: Config tabs (Sources + Aliases) on top, Preview + Log below
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(8)

        self.cfg_tabs = QTabWidget()

        # --- Sub-tab 1: Source Folder Paths ---
        src_tab = QWidget()
        src_layout = QVBoxLayout(src_tab)
        src_layout.setContentsMargins(10, 8, 10, 8)
        src_layout.setSpacing(6)

        src_bar = QHBoxLayout()
        self.sources_title_lbl = QLabel()
        self.sources_title_lbl.setObjectName("SectionTitle")
        src_bar.addWidget(self.sources_title_lbl)
        src_bar.addStretch(1)

        self.add_src_btn = QPushButton()
        self.edit_src_btn = QPushButton()
        self.del_src_btn = QPushButton()
        self.save_btn = QPushButton()
        self.load_btn = QPushButton()
        self.reset_btn = QPushButton()

        for btn in (
            self.add_src_btn,
            self.edit_src_btn,
            self.del_src_btn,
            self.save_btn,
            self.load_btn,
            self.reset_btn,
        ):
            btn.setCursor(Qt.PointingHandCursor)
            src_bar.addWidget(btn)

        self.add_src_btn.clicked.connect(self._add_rule)
        self.edit_src_btn.clicked.connect(self._edit_rule)
        self.del_src_btn.clicked.connect(self._delete_rule)
        self.save_btn.clicked.connect(self._save_config)
        self.load_btn.clicked.connect(self._load_config)
        self.reset_btn.clicked.connect(self._reset_config)
        src_layout.addLayout(src_bar)

        self.rules_table = WatermarkTableWidget(0, 8)
        self.rules_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.rules_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.rules_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.rules_table.setAlternatingRowColors(True)
        self.rules_table.verticalHeader().setVisible(False)
        self.rules_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.rules_table.horizontalHeader().setStretchLastSection(True)
        self.rules_table.setMinimumHeight(105)
        self.rules_table.cellDoubleClicked.connect(lambda _r, _c: self._edit_rule())
        src_layout.addWidget(self.rules_table, 1)

        self.empty_rules_lbl = QLabel()
        self.empty_rules_lbl.setObjectName("EmptyHint")
        self.empty_rules_lbl.setAlignment(Qt.AlignCenter)
        src_layout.addWidget(self.empty_rules_lbl)

        # --- Sub-tab 2: Code -> Company Alias Table ---
        alias_tab = QWidget()
        alias_layout = QVBoxLayout(alias_tab)
        alias_layout.setContentsMargins(10, 8, 10, 8)
        alias_layout.setSpacing(6)

        alias_bar = QHBoxLayout()
        self.aliases_title_lbl = QLabel()
        self.aliases_title_lbl.setObjectName("SectionTitle")
        alias_bar.addWidget(self.aliases_title_lbl)
        alias_bar.addStretch(1)

        self.add_alias_btn = QPushButton()
        self.edit_alias_btn = QPushButton()
        self.del_alias_btn = QPushButton()
        self.save_alias_btn = QPushButton()
        for btn in (self.add_alias_btn, self.edit_alias_btn, self.del_alias_btn, self.save_alias_btn):
            btn.setCursor(Qt.PointingHandCursor)
            alias_bar.addWidget(btn)

        self.add_alias_btn.clicked.connect(self._add_alias)
        self.edit_alias_btn.clicked.connect(self._edit_alias)
        self.del_alias_btn.clicked.connect(self._delete_alias)
        self.save_alias_btn.clicked.connect(self._save_config)
        alias_layout.addLayout(alias_bar)

        self.alias_table = WatermarkTableWidget(0, 4)
        self.alias_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.alias_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.alias_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.alias_table.setAlternatingRowColors(True)
        self.alias_table.verticalHeader().setVisible(False)
        self.alias_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.alias_table.horizontalHeader().setStretchLastSection(True)
        self.alias_table.setMinimumHeight(105)
        self.alias_table.cellDoubleClicked.connect(lambda _r, _c: self._edit_alias())
        alias_layout.addWidget(self.alias_table, 1)

        self.empty_aliases_lbl = QLabel()
        self.empty_aliases_lbl.setObjectName("EmptyHint")
        self.empty_aliases_lbl.setAlignment(Qt.AlignCenter)
        alias_layout.addWidget(self.empty_aliases_lbl)

        self.cfg_tabs.addTab(src_tab, "")
        self.cfg_tabs.addTab(alias_tab, "")
        splitter.addWidget(self.cfg_tabs)

        # --- Lower pane: Preview table + stats + run controls + log ---
        prev_pane = QWidget()
        prev_layout = QVBoxLayout(prev_pane)
        prev_layout.setContentsMargins(0, 4, 0, 0)
        prev_layout.setSpacing(7)

        action_bar = QHBoxLayout()
        action_bar.setSpacing(8)
        self.prev_title_lbl = QLabel()
        self.prev_title_lbl.setObjectName("SectionTitle")
        action_bar.addWidget(self.prev_title_lbl)
        action_bar.addStretch(1)

        self.preview_btn = QPushButton()
        self.preview_btn.setCursor(Qt.PointingHandCursor)
        self.preview_btn.clicked.connect(self._load_preview)

        self.open_root_btn = QPushButton()
        self.open_root_btn.setCursor(Qt.PointingHandCursor)
        self.open_root_btn.clicked.connect(self._open_root)

        self.run_btn = QPushButton()
        self.run_btn.setObjectName("PrimaryButton")
        self.run_btn.setCursor(Qt.PointingHandCursor)
        self.run_btn.clicked.connect(self._start_mapping)

        action_bar.addWidget(self.preview_btn)
        action_bar.addWidget(self.open_root_btn)
        action_bar.addWidget(self.run_btn)
        prev_layout.addLayout(action_bar)

        self.stats_frame = QWidget()
        stats_layout = QHBoxLayout(self.stats_frame)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(10)
        self.stat_folders_val, self.stat_folders_lbl = self._make_stat_card(stats_layout)
        self.stat_ready_val, self.stat_ready_lbl = self._make_stat_card(stats_layout)
        self.stat_skip_val, self.stat_skip_lbl = self._make_stat_card(stats_layout)
        self.stat_miss_val, self.stat_miss_lbl = self._make_stat_card(stats_layout)
        self.stats_frame.setVisible(False)
        prev_layout.addWidget(self.stats_frame)

        self.preview_table = WatermarkTableWidget(0, 6)
        self.preview_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.preview_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.verticalHeader().setVisible(False)
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        self.preview_table.setMinimumHeight(120)
        prev_layout.addWidget(self.preview_table, 2)

        self.empty_prev_lbl = QLabel()
        self.empty_prev_lbl.setObjectName("EmptyHint")
        self.empty_prev_lbl.setAlignment(Qt.AlignCenter)
        self.empty_prev_lbl.setWordWrap(True)
        prev_layout.addWidget(self.empty_prev_lbl)

        self.status_banner = QLabel()
        self.status_banner.setObjectName("StatusBanner")
        prev_layout.addWidget(self.status_banner)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)
        prev_layout.addWidget(self.progress_bar)

        log_head = QHBoxLayout()
        self.log_lbl = QLabel()
        self.log_lbl.setObjectName("SectionTitle")
        self.clear_log_btn = QPushButton()
        self.clear_log_btn.setCursor(Qt.PointingHandCursor)
        self.clear_log_btn.clicked.connect(lambda: self.log_box.clear())
        log_head.addWidget(self.log_lbl)
        log_head.addStretch(1)
        log_head.addWidget(self.clear_log_btn)
        prev_layout.addLayout(log_head)

        self.log_box = QPlainTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumHeight(85)
        prev_layout.addWidget(self.log_box, 1)

        splitter.addWidget(prev_pane)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        root.addWidget(splitter, 1)

    def _make_stat_card(self, parent_layout: QHBoxLayout) -> tuple[QLabel, QLabel]:
        box = QFrame()
        box.setObjectName("StatCard")
        v = QVBoxLayout(box)
        v.setContentsMargins(10, 6, 10, 6)
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
        self.rules_table.set_dark_mode(dark)
        self.alias_table.set_dark_mode(dark)
        self.preview_table.set_dark_mode(dark)

    def _on_work_mode_changed(self) -> None:
        mode = str(self.wmode_combo.currentData() or "create_from_files")
        self.work_mode = mode
        is_create = mode == "create_from_files"
        self.create_opts_widget.setVisible(is_create)
        self.existing_opts_widget.setVisible(not is_create)

    def retranslate_ui(self) -> None:
        t = self.i18n.t
        self.title_lbl.setText(t("logic_header_title"))
        self.desc_lbl.setText(t("logic_header_desc"))

        self.wmode_lbl.setText(t("logic_lbl_work_mode"))
        current_wmode = self.wmode_combo.currentData() or self.work_mode
        self.wmode_combo.blockSignals(True)
        self.wmode_combo.clear()
        self.wmode_combo.addItem(t("logic_wmode_create"), "create_from_files")
        self.wmode_combo.addItem(t("logic_wmode_existing"), "existing_folders")
        self.wmode_combo.setCurrentIndex(1 if current_wmode == "existing_folders" else 0)
        self.wmode_combo.blockSignals(False)
        self._on_work_mode_changed()

        self.root_picker.set_texts(
            t("logic_lbl_target_root"), t("btn_browse"), t("not_selected"), t("logic_lbl_target_root")
        )
        self.month_lbl.setText(t("logic_lbl_month"))
        self.tpl_lbl.setText(t("logic_lbl_template"))
        self.fb_regex_lbl.setText(t("logic_lbl_fallback_regex"))
        self.ignore_lbl.setText(t("logic_lbl_ignore_keys"))
        self.regex_lbl.setText(t("logic_lbl_regex"))
        self.scan_lbl.setText(t("logic_lbl_scan_mode"))

        current_scan = self.scan_combo.currentData() or self.target_scan
        self.scan_combo.blockSignals(True)
        self.scan_combo.clear()
        self.scan_combo.addItem(t("logic_scan_folder"), "folder")
        self.scan_combo.addItem(t("logic_scan_files"), "files")
        self.scan_combo.addItem(t("logic_scan_both"), "both")
        scan_idx = {"folder": 0, "files": 1, "both": 2}.get(current_scan, 0)
        self.scan_combo.setCurrentIndex(scan_idx)
        self.scan_combo.blockSignals(False)

        self.cfg_tabs.setTabText(0, t("logic_tab_sources"))
        self.cfg_tabs.setTabText(1, t("logic_tab_aliases"))

        self.sources_title_lbl.setText(t("logic_sources_title"))
        self.empty_rules_lbl.setText(t("logic_sources_empty"))
        self.add_src_btn.setText(t("logic_btn_add_src"))
        self.edit_src_btn.setText(t("btn_edit_rule"))
        self.del_src_btn.setText(t("btn_delete_rule"))
        self.save_btn.setText(t("btn_save_rules"))
        self.load_btn.setText(t("btn_load_rules"))
        self.reset_btn.setText(t("btn_reset_rules"))

        self.rules_table.setHorizontalHeaderLabels(
            [
                t("col_enabled"),
                t("logic_col_name"),
                t("logic_col_dir"),
                t("logic_col_action"),
                t("logic_col_mode"),
                t("logic_col_pattern"),
                t("logic_col_sub"),
                t("logic_col_conflict"),
            ]
        )
        for idx, w in enumerate([58, 155, 290, 95, 95, 110, 74, 82]):
            self.rules_table.setColumnWidth(idx, w)

        self.aliases_title_lbl.setText(t("logic_aliases_title"))
        self.empty_aliases_lbl.setText(t("logic_aliases_empty"))
        self.add_alias_btn.setText(t("logic_btn_add_alias"))
        self.edit_alias_btn.setText(t("btn_edit_rule"))
        self.del_alias_btn.setText(t("btn_delete_rule"))
        self.save_alias_btn.setText(t("btn_save_rules"))

        self.alias_table.setHorizontalHeaderLabels(
            [
                t("col_enabled"),
                t("logic_col_match_code"),
                t("logic_col_pt_name"),
                t("logic_col_month_ovr"),
            ]
        )
        for idx, w in enumerate([64, 220, 150]):
            self.alias_table.setColumnWidth(idx, w)

        self.prev_title_lbl.setText(t("logic_prev_title"))
        self.empty_prev_lbl.setText(t("logic_prev_empty"))
        self.preview_btn.setText(t("logic_btn_preview"))
        self.open_root_btn.setText(t("btn_open_folder"))
        self.run_btn.setText(t("logic_btn_run"))

        self.stat_folders_lbl.setText(t("logic_stat_folders"))
        self.stat_ready_lbl.setText(t("logic_stat_ready"))
        self.stat_skip_lbl.setText(t("logic_stat_skip"))
        self.stat_miss_lbl.setText(t("logic_stat_miss"))

        self.preview_table.setHorizontalHeaderLabels(
            [
                t("logic_pcol_folder"),
                t("logic_pcol_key"),
                t("logic_pcol_rule"),
                t("logic_pcol_file"),
                t("logic_pcol_action"),
                t("logic_pcol_status"),
            ]
        )
        for idx, w in enumerate([220, 118, 150, 200, 90]):
            self.preview_table.setColumnWidth(idx, w)

        self.log_lbl.setText(t("log_title"))
        self.clear_log_btn.setText(t("btn_clear_log"))

        if self._worker is None or not self._worker.isRunning():
            self._set_status(t("state_idle"), "idle")

        self._refresh_rules_table()
        self._refresh_alias_table()
        self._render_preview_table()

    def _set_status(self, message: str, state: str = "idle") -> None:
        self.status_banner.setText(message)
        self.status_banner.setProperty("state", state)
        self.status_banner.style().unpolish(self.status_banner)
        self.status_banner.style().polish(self.status_banner)

    def _refresh_rules_table(self) -> None:
        t = self.i18n.t
        self.rules_table.setRowCount(len(self.rules))
        self.empty_rules_lbl.setVisible(len(self.rules) == 0)
        mode_labels = {
            "token": t("logic_mode_token"),
            "contains": t("logic_mode_contains"),
            "regex": t("logic_mode_regex"),
        }

        for row_idx, rule in enumerate(self.rules):
            enabled_txt = t("val_yes") if rule.get("enabled", True) else t("val_no")
            action_txt = (
                t("logic_act_move")
                if str(rule.get("action", "copy")).lower() == "move"
                else t("logic_act_copy")
            )
            mode_txt = mode_labels.get(str(rule.get("match_mode", "token")).lower(), t("logic_mode_token"))
            pattern_txt = str(rule.get("file_pattern", "")).strip() or "{KEY}"
            sub_txt = t("val_yes") if rule.get("include_subfolders", False) else t("val_no")
            conf_txt = (
                t("logic_conf_overwrite")
                if str(rule.get("conflict", "skip")).lower() == "overwrite"
                else t("logic_conf_skip")
            )

            values = [
                enabled_txt,
                str(rule.get("name", "")),
                str(rule.get("source_dir", "")),
                action_txt,
                mode_txt,
                pattern_txt,
                sub_txt,
                conf_txt,
            ]
            for col_idx, val in enumerate(values):
                item = QTableWidgetItem(val)
                if col_idx in (0, 3, 4, 6, 7):
                    item.setTextAlignment(Qt.AlignCenter)
                self.rules_table.setItem(row_idx, col_idx, item)

    def _refresh_alias_table(self) -> None:
        t = self.i18n.t
        self.alias_table.setRowCount(len(self.aliases))
        self.empty_aliases_lbl.setVisible(len(self.aliases) == 0)

        for row_idx, alias in enumerate(self.aliases):
            enabled_txt = t("val_yes") if alias.get("enabled", True) else t("val_no")
            vals = [
                enabled_txt,
                str(alias.get("match_code", "")),
                str(alias.get("pt_name", "")),
                str(alias.get("month_override", "")) or "-",
            ]
            for col_idx, val in enumerate(vals):
                item = QTableWidgetItem(val)
                if col_idx in (0, 2):
                    item.setTextAlignment(Qt.AlignCenter)
                self.alias_table.setItem(row_idx, col_idx, item)

    def _selected_rule_row(self) -> Optional[int]:
        row = self.rules_table.currentRow()
        return row if 0 <= row < len(self.rules) else None

    def _selected_alias_row(self) -> Optional[int]:
        row = self.alias_table.currentRow()
        return row if 0 <= row < len(self.aliases) else None

    def _add_rule(self) -> None:
        new_rule: Dict[str, Any] = {
            "enabled": True,
            "name": "",
            "source_dir": "",
            "action": "copy",
            "match_mode": "token",
            "file_pattern": "",
            "include_subfolders": False,
            "conflict": "skip",
        }
        dlg = SourceRuleDialog(self.i18n, new_rule, self)
        if dlg.exec() == QDialog.Accepted:
            self.rules.append(new_rule)
            self._refresh_rules_table()
            self.rules_table.selectRow(len(self.rules) - 1)

    def _edit_rule(self) -> None:
        row = self._selected_rule_row()
        if row is None:
            QMessageBox.warning(self, self.i18n.t("msg_warning"), self.i18n.t("err_select_rule_first"))
            return
        dlg = SourceRuleDialog(self.i18n, self.rules[row], self)
        if dlg.exec() == QDialog.Accepted:
            self._refresh_rules_table()
            self.rules_table.selectRow(row)

    def _delete_rule(self) -> None:
        row = self._selected_rule_row()
        if row is None:
            QMessageBox.warning(self, self.i18n.t("msg_warning"), self.i18n.t("err_select_rule_first"))
            return
        del self.rules[row]
        self._refresh_rules_table()

    def _add_alias(self) -> None:
        new_alias: Dict[str, Any] = {
            "enabled": True,
            "match_code": "",
            "pt_name": "",
            "month_override": "",
        }
        dlg = AliasRuleDialog(self.i18n, new_alias, self)
        if dlg.exec() == QDialog.Accepted:
            self.aliases.append(new_alias)
            self._refresh_alias_table()
            self.alias_table.selectRow(len(self.aliases) - 1)

    def _edit_alias(self) -> None:
        row = self._selected_alias_row()
        if row is None:
            QMessageBox.warning(self, self.i18n.t("msg_warning"), self.i18n.t("err_select_rule_first"))
            return
        dlg = AliasRuleDialog(self.i18n, self.aliases[row], self)
        if dlg.exec() == QDialog.Accepted:
            self._refresh_alias_table()
            self.alias_table.selectRow(row)

    def _delete_alias(self) -> None:
        row = self._selected_alias_row()
        if row is None:
            QMessageBox.warning(self, self.i18n.t("msg_warning"), self.i18n.t("err_select_rule_first"))
            return
        del self.aliases[row]
        self._refresh_alias_table()

    def _current_config(self) -> Dict[str, Any]:
        return {
            "work_mode": str(self.wmode_combo.currentData() or "create_from_files"),
            "month_label": self.month_edit.text().strip(),
            "folder_template": self.tpl_edit.text().strip(),
            "file_fallback_regex": self.fb_regex_edit.text().strip(),
            "ignore_keys": self.ignore_edit.text().strip(),
            "target_regex": self.regex_edit.text().strip(),
            "target_scan": str(self.scan_combo.currentData() or "folder"),
            "aliases": [dict(a) for a in self.aliases],
            "rules": [dict(r) for r in self.rules],
        }

    def _apply_config_dict(self, cfg: Dict[str, Any]) -> None:
        self.work_mode = cfg["work_mode"]
        self.month_label = cfg["month_label"]
        self.folder_template = cfg["folder_template"]
        self.file_fallback_regex = cfg["file_fallback_regex"]
        self.ignore_keys = cfg["ignore_keys"]
        self.target_regex = cfg["target_regex"]
        self.target_scan = cfg["target_scan"]
        self.aliases = cfg["aliases"]
        self.rules = cfg["rules"]

        self.wmode_combo.setCurrentIndex(1 if self.work_mode == "existing_folders" else 0)
        self.month_edit.setText(self.month_label)
        self.tpl_edit.setText(self.folder_template)
        self.fb_regex_edit.setText(self.file_fallback_regex)
        self.ignore_edit.setText(self.ignore_keys)
        self.regex_edit.setText(self.target_regex)
        scan_idx = {"folder": 0, "files": 1, "both": 2}.get(self.target_scan, 0)
        self.scan_combo.setCurrentIndex(scan_idx)
        self._on_work_mode_changed()
        self._refresh_rules_table()
        self._refresh_alias_table()

    def _save_config(self) -> None:
        saved = save_logic_config(self._current_config(), DEFAULT_LOGIC_CONFIG_PATH)
        QMessageBox.information(
            self,
            self.i18n.t("msg_info"),
            self.i18n.t("logic_msg_saved", path=saved),
        )

    def _load_config(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.i18n.t("dlg_pick_json"),
            os.path.dirname(DEFAULT_LOGIC_CONFIG_PATH),
            "JSON Files (*.json)",
        )
        if path:
            self._apply_config_dict(load_logic_config(path))
            QMessageBox.information(
                self,
                self.i18n.t("msg_info"),
                self.i18n.t("logic_msg_loaded", path=path),
            )

    def _reset_config(self) -> None:
        ans = QMessageBox.question(
            self,
            self.i18n.t("msg_confirm"),
            self.i18n.t("logic_msg_reset_confirm"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if ans == QMessageBox.Yes:
            self._apply_config_dict(clone_default_config())

    def _status_text(self, entry: LogicMatchEntry) -> str:
        t = self.i18n.t
        mapping = {
            "ready": t("logic_st_ready"),
            "exists_skip": t("logic_st_exists_skip"),
            "exists_overwrite": t("logic_st_exists_overwrite"),
            "no_key": t("logic_st_no_key"),
            "no_source_dir": t("logic_st_no_source_dir"),
            "not_found": t("logic_st_not_found"),
            "done": t("logic_st_done"),
            "skipped": t("logic_st_skipped"),
            "error": f"{t('logic_st_error')}: {entry.error_message}" if entry.error_message else t("logic_st_error"),
        }
        return mapping.get(entry.status, entry.status)

    def _render_preview_table(self) -> None:
        t = self.i18n.t
        self.preview_table.setRowCount(len(self.entries))
        self.empty_prev_lbl.setVisible(len(self.entries) == 0)
        self.stats_frame.setVisible(len(self.entries) > 0)

        folders_seen = set()
        ready_or_done = 0
        skipped = 0
        miss_or_err = 0

        for row_idx, entry in enumerate(self.entries):
            if entry.folder_name and entry.folder_name != "-":
                folders_seen.add(entry.folder_name)
            if entry.status in ("ready", "exists_overwrite", "done"):
                ready_or_done += 1
            elif entry.status in ("exists_skip", "skipped"):
                skipped += 1
            else:
                miss_or_err += 1

            act_txt = (
                t("logic_act_move")
                if entry.action == "move"
                else (t("logic_act_copy") if entry.action == "copy" else "-")
            )
            vals = [
                entry.folder_name,
                entry.key or "-",
                entry.rule_name,
                entry.file_name or "-",
                act_txt,
                self._status_text(entry),
            ]
            for col_idx, val in enumerate(vals):
                item = QTableWidgetItem(val)
                if col_idx in (1, 4):
                    item.setTextAlignment(Qt.AlignCenter)
                self.preview_table.setItem(row_idx, col_idx, item)

        self.stat_folders_val.setText(str(len(folders_seen)))
        self.stat_ready_val.setText(str(ready_or_done))
        self.stat_skip_val.setText(str(skipped))
        self.stat_miss_val.setText(str(miss_or_err))

    def _load_preview(self) -> bool:
        t = self.i18n.t
        root_dir = self.root_picker.path()
        if not root_dir or not os.path.isdir(root_dir):
            self._set_status(t("logic_err_select_root"), "error")
            QMessageBox.warning(self, t("msg_warning"), t("logic_err_select_root"))
            return False

        mode = str(self.wmode_combo.currentData() or "create_from_files")
        try:
            if mode == "create_from_files":
                self.entries = build_create_from_files_preview(
                    target_root=root_dir,
                    month_label=self.month_edit.text().strip(),
                    folder_template=self.tpl_edit.text().strip(),
                    file_fallback_regex=self.fb_regex_edit.text().strip(),
                    ignore_keys_str=self.ignore_edit.text().strip(),
                    aliases=self.aliases,
                    rules=self.rules,
                    monthly_rule_label=t("logic_monthly_label"),
                )
            else:
                regex_text = self.regex_edit.text().strip()
                if not regex_text:
                    self._set_status(t("logic_err_empty_regex"), "error")
                    QMessageBox.warning(self, t("msg_warning"), t("logic_err_empty_regex"))
                    return False
                scan_mode = str(self.scan_combo.currentData() or "folder")
                self.entries = build_logic_preview(root_dir, regex_text, scan_mode, self.rules)

            self._render_preview_table()
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
        for btn in (
            self.run_btn,
            self.preview_btn,
            self.add_src_btn,
            self.edit_src_btn,
            self.del_src_btn,
            self.add_alias_btn,
            self.edit_alias_btn,
            self.del_alias_btn,
            self.save_btn,
            self.save_alias_btn,
            self.load_btn,
            self.reset_btn,
        ):
            btn.setEnabled(not running)
        self.progress_bar.setVisible(running)
        if running:
            self.progress_bar.setValue(0)

    def _start_mapping(self) -> None:
        t = self.i18n.t
        if not self._load_preview():
            return

        actionable = sum(1 for e in self.entries if e.status in ("ready", "exists_overwrite"))
        ans = QMessageBox.question(
            self,
            t("msg_confirm"),
            t("logic_msg_confirm", count=actionable),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            return

        self.log_box.clear()
        self._set_status(t("state_running"), "running")
        self._set_running(True)

        self._worker = WorkerThread(execute_logic_mapping, self.entries)
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
        self._render_preview_table()
        self._set_status(t("state_done"), "done")
        QMessageBox.information(
            self,
            t("msg_done"),
            t(
                "logic_msg_done",
                processed=summary["processed"],
                skipped=summary["skipped"],
                missing=summary["missing"],
                errors=summary["errors"],
            ),
        )

    def _on_error(self, message: str) -> None:
        t = self.i18n.t
        self._set_running(False)
        self.log_box.appendPlainText(f"[ERROR] {message}")
        self._set_status(f"{t('state_error')} {message}", "error")
        QMessageBox.critical(self, t("msg_error"), message)
