"""Main application window combining all 5 workflows with live language & theme switchers."""

from __future__ import annotations

import os
from typing import Dict, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.i18n import I18n, LANGUAGE_LABELS, SUPPORTED_LANGUAGES, WATERMARK_TEXT
from core.pdf_sign import get_resource_path
from core.updater import ReleaseInfo
from core.version import APP_VERSION
from ui.tab_file_mover import FileMoverTab
from ui.tab_list_exporter import ListExporterTab
from ui.tab_logic_mapper import LogicMapperTab
from ui.tab_pdf_sign import PdfSignTab
from ui.theme import build_stylesheet
from ui.update_dialog import UpdateCheckWorker, UpdateDialog


class MainWindow(QMainWindow):
    """Unified PySide6 workbench for PDF整理工具."""

    def __init__(self, initial_lang: str = "id") -> None:
        super().__init__()
        self.i18n = I18n(initial_lang)
        self._theme_mode = "light"
        self._rail_collapsed = False
        self._update_worker: Optional[UpdateCheckWorker] = None
        self._manual_update_check = False

        self.resize(1160, 780)
        self.setMinimumSize(900, 640)

        logo_path = get_resource_path(os.path.join("assets", "applogo.png"))
        if os.path.isfile(logo_path):
            self.setWindowIcon(QIcon(logo_path))

        self._build_ui()
        self._apply_theme("light")
        self._retranslate_all()

        # Silent background update check shortly after window opens
        QTimer.singleShot(1500, lambda: self._check_updates(manual=False))

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        shell = QHBoxLayout(central)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        # Left Navigation Rail
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(228)
        rail_layout = QVBoxLayout(self.sidebar)
        rail_layout.setContentsMargins(14, 18, 14, 16)
        rail_layout.setSpacing(8)

        # Brand block + custom logo + rail collapse button
        brand_row = QHBoxLayout()
        brand_row.setSpacing(8)

        self.brand_logo = QLabel()
        self.brand_logo.setFixedSize(28, 28)
        logo_path = get_resource_path(os.path.join("assets", "applogo.png"))
        if os.path.isfile(logo_path):
            pix = QPixmap(logo_path).scaled(
                28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.brand_logo.setPixmap(pix)
        else:
            self.brand_logo.setVisible(False)

        self.brand_title = QLabel()
        self.brand_title.setObjectName("BrandTitle")

        self.collapse_btn = QPushButton("<<")
        self.collapse_btn.setObjectName("CollapseButton")
        self.collapse_btn.setCursor(Qt.PointingHandCursor)
        self.collapse_btn.setFixedWidth(34)
        self.collapse_btn.setToolTip("Toggle sidebar")
        self.collapse_btn.clicked.connect(self._toggle_rail)

        brand_row.addWidget(self.brand_logo)
        brand_row.addWidget(self.brand_title, 1)
        brand_row.addWidget(self.collapse_btn)
        rail_layout.addLayout(brand_row)

        self.brand_sub = QLabel()
        self.brand_sub.setObjectName("BrandSubtitle")
        self.brand_sub.setWordWrap(True)
        rail_layout.addWidget(self.brand_sub)
        rail_layout.addSpacing(14)

        self.nav_section_lbl = QLabel()
        self.nav_section_lbl.setObjectName("NavSection")
        rail_layout.addWidget(self.nav_section_lbl)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        self.nav_buttons: list[QPushButton] = []
        for idx in range(4):
            btn = QPushButton()
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            self.nav_group.addButton(btn, idx)
            self.nav_buttons.append(btn)
            rail_layout.addWidget(btn)

        self.nav_buttons[0].setChecked(True)
        self.nav_group.idClicked.connect(self._switch_page)

        rail_layout.addStretch(1)

        # Current version label + watermark seal stamp at bottom of rail
        self.version_lbl = QLabel(f"v{APP_VERSION}")
        self.version_lbl.setObjectName("BrandSubtitle")
        self.version_lbl.setAlignment(Qt.AlignCenter)
        rail_layout.addWidget(self.version_lbl)

        self.watermark_stamp = QLabel(WATERMARK_TEXT)
        self.watermark_stamp.setObjectName("WatermarkStamp")
        self.watermark_stamp.setAlignment(Qt.AlignCenter)
        rail_layout.addWidget(self.watermark_stamp)

        shell.addWidget(self.sidebar)

        # Right area: Top bar + Stacked workspace
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Top utility bar (Language Switch + Theme Switch)
        top_bar = QFrame()
        top_bar.setObjectName("TopBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 10, 20, 10)
        top_layout.setSpacing(10)

        self.active_module_lbl = QLabel()
        self.active_module_lbl.setObjectName("SectionTitle")
        top_layout.addWidget(self.active_module_lbl)
        top_layout.addStretch(1)

        self.lang_lbl = QLabel()
        self.lang_lbl.setObjectName("FieldLabel")
        top_layout.addWidget(self.lang_lbl)

        self.lang_group = QButtonGroup(self)
        self.lang_group.setExclusive(True)
        self.lang_buttons: Dict[str, QPushButton] = {}
        for code in SUPPORTED_LANGUAGES:
            btn = QPushButton(LANGUAGE_LABELS[code])
            btn.setObjectName("LangButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            if code == self.i18n.lang:
                btn.setChecked(True)
            btn.clicked.connect(lambda _checked, c=code: self._set_language(c))
            self.lang_group.addButton(btn)
            self.lang_buttons[code] = btn
            top_layout.addWidget(btn)

        self.theme_btn = QPushButton()
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.clicked.connect(self._toggle_theme)
        top_layout.addWidget(self.theme_btn)

        self.update_btn = QPushButton()
        self.update_btn.setCursor(Qt.PointingHandCursor)
        self.update_btn.clicked.connect(lambda: self._check_updates(manual=True))
        top_layout.addWidget(self.update_btn)

        right_layout.addWidget(top_bar)

        # Stacked workflow pages
        self.stack = QStackedWidget()
        self.pdf_tab = PdfSignTab(self.i18n)
        self.mover_tab = FileMoverTab(self.i18n)
        self.export_tab = ListExporterTab(self.i18n)
        self.logic_tab = LogicMapperTab(self.i18n)

        self.stack.addWidget(self.pdf_tab)
        self.stack.addWidget(self.mover_tab)
        self.stack.addWidget(self.export_tab)
        self.stack.addWidget(self.logic_tab)
        right_layout.addWidget(self.stack, 1)

        shell.addWidget(right_panel, 1)

    def _toggle_rail(self) -> None:
        self._rail_collapsed = not self._rail_collapsed
        self.sidebar.setFixedWidth(74 if self._rail_collapsed else 228)
        self.brand_logo.setVisible(not self._rail_collapsed and not self.brand_logo.pixmap().isNull())
        self.brand_title.setVisible(not self._rail_collapsed)
        self.brand_sub.setVisible(not self._rail_collapsed)
        self.nav_section_lbl.setVisible(not self._rail_collapsed)
        self.collapse_btn.setText(">>" if self._rail_collapsed else "<<")
        self._update_nav_labels()

    def _update_nav_labels(self) -> None:
        t = self.i18n.t
        if self._rail_collapsed:
            short_labels = ["01", "02", "03", "04"]
            tooltips = [
                t("nav_pdf_sign"),
                t("nav_file_mover"),
                t("nav_list_export"),
                t("nav_logic_mapper"),
            ]
            for btn, short, tip in zip(self.nav_buttons, short_labels, tooltips):
                btn.setText(short)
                btn.setToolTip(tip)
            self.watermark_stamp.setText("开能能")
        else:
            full_labels = [
                t("nav_pdf_sign"),
                t("nav_file_mover"),
                t("nav_list_export"),
                t("nav_logic_mapper"),
            ]
            for btn, label in zip(self.nav_buttons, full_labels):
                btn.setText(label.replace("&", "&&"))
                btn.setToolTip(label)
            self.watermark_stamp.setText(WATERMARK_TEXT)

    def _switch_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        self._update_active_module_label()

    def _update_active_module_label(self) -> None:
        t = self.i18n.t
        idx = self.stack.currentIndex()
        titles = [
            t("nav_pdf_sign"),
            t("nav_file_mover"),
            t("nav_list_export"),
            t("nav_logic_mapper"),
        ]
        self.active_module_lbl.setText(titles[idx])

    def _set_language(self, lang_code: str) -> None:
        self.i18n.set_lang(lang_code)
        self._retranslate_all()

    def _toggle_theme(self) -> None:
        next_mode = "dark" if self._theme_mode == "light" else "light"
        self._apply_theme(next_mode)
        self._update_theme_button_label()

    def _apply_theme(self, mode: str) -> None:
        self._theme_mode = mode
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(build_stylesheet(mode))
        is_dark = mode == "dark"
        self.pdf_tab.set_dark_mode(is_dark)
        self.mover_tab.set_dark_mode(is_dark)
        self.logic_tab.set_dark_mode(is_dark)

    def _update_theme_button_label(self) -> None:
        key = "theme_light" if self._theme_mode == "dark" else "theme_dark"
        self.theme_btn.setText(self.i18n.t(key))

    def _retranslate_all(self) -> None:
        t = self.i18n.t
        self.setWindowTitle(f"{t('app_title')} ({WATERMARK_TEXT})")
        self.brand_title.setText(t("app_title"))
        self.brand_sub.setText(t("app_subtitle"))
        self.nav_section_lbl.setText(t("nav_section"))
        self.lang_lbl.setText(t("lang_label"))
        self._update_nav_labels()
        self._update_active_module_label()
        self._update_theme_button_label()
        self._update_check_button_label()

        self.pdf_tab.retranslate_ui()
        self.mover_tab.retranslate_ui()
        self.export_tab.retranslate_ui()
        self.logic_tab.retranslate_ui()

    def _update_check_button_label(self) -> None:
        checking = self._update_worker is not None and self._update_worker.isRunning()
        key = "btn_checking_update" if checking else "btn_check_update"
        self.update_btn.setText(self.i18n.t(key))
        self.update_btn.setEnabled(not checking)

    def _check_updates(self, manual: bool = False) -> None:
        if self._update_worker is not None and self._update_worker.isRunning():
            return
        self._manual_update_check = manual
        self._update_worker = UpdateCheckWorker()
        self._update_worker.result_ready.connect(self._on_update_check_result)
        self._update_worker.no_release.connect(self._on_update_no_release)
        self._update_worker.failed.connect(self._on_update_check_failed)
        self._update_worker.finished.connect(self._update_check_button_label)
        self._update_worker.start()
        self._update_check_button_label()

    def _on_update_check_result(self, release: ReleaseInfo) -> None:
        if release.has_update:
            dlg = UpdateDialog(self.i18n, release, self)
            dlg.exec()
            return
        if self._manual_update_check:
            t = self.i18n.t
            QMessageBox.information(
                self,
                t("msg_info"),
                t("update_up_to_date", version=APP_VERSION),
            )

    def _on_update_no_release(self) -> None:
        if self._manual_update_check:
            t = self.i18n.t
            QMessageBox.information(
                self,
                t("msg_info"),
                t("update_no_release_yet", version=APP_VERSION),
            )

    def _on_update_check_failed(self, error_msg: str) -> None:
        if self._manual_update_check:
            t = self.i18n.t
            QMessageBox.warning(
                self,
                t("msg_warning"),
                t("update_check_failed", error=error_msg),
            )
