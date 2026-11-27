"""Multilingual Auto-Update Dialog and background Qt workers."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.i18n import I18n
from core.updater import (
    DownloadCancelledError,
    NoReleasePublishedError,
    ReleaseInfo,
    download_installer,
    fetch_latest_release,
    launch_installer_for_update,
)
from core.version import APP_VERSION, GITHUB_REPO


class UpdateCheckWorker(QThread):
    """Checks GitHub Releases in the background."""

    result_ready = Signal(object)  # ReleaseInfo
    no_release = Signal()
    failed = Signal(str)

    def __init__(self, repo: str = GITHUB_REPO, current_version: str = APP_VERSION) -> None:
        super().__init__()
        self._repo = repo
        self._current_version = current_version

    def run(self) -> None:
        try:
            info = fetch_latest_release(self._repo, self._current_version)
            self.result_ready.emit(info)
        except NoReleasePublishedError:
            self.no_release.emit()
        except Exception as exc:
            self.failed.emit(str(exc))


class UpdateDownloadWorker(QThread):
    """Downloads the Windows installer .exe in the background with cancel support."""

    progress = Signal(int, int)
    completed = Signal(str)
    cancelled = Signal()
    failed = Signal(str)

    def __init__(self, url: str, filename: str) -> None:
        super().__init__()
        self._url = url
        self._filename = filename
        self._cancel_requested = False

    def request_cancel(self) -> None:
        self._cancel_requested = True

    def run(self) -> None:
        try:
            path = download_installer(
                url=self._url,
                filename=self._filename,
                on_progress=self.progress.emit,
                is_cancelled=lambda: self._cancel_requested,
            )
            self.completed.emit(path)
        except DownloadCancelledError:
            self.cancelled.emit()
        except Exception as exc:
            self.failed.emit(str(exc))


class UpdateDialog(QDialog):
    """Modal dialog presenting update details, download progress, and 1-click install."""

    def __init__(
        self,
        i18n: I18n,
        release: ReleaseInfo,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.i18n = i18n
        self.release = release
        self._downloader: Optional[UpdateDownloadWorker] = None

        self.setModal(True)
        self.setFixedWidth(520)
        self.setWindowTitle(self.i18n.t("update_dlg_title"))

        self._build_ui()

    def _build_ui(self) -> None:
        t = self.i18n.t
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        title_lbl = QLabel(t("update_available_title", version=self.release.tag_name))
        title_lbl.setObjectName("PageTitle")
        root.addWidget(title_lbl)

        # Version comparison strip
        info_card = QFrame()
        info_card.setObjectName("Card")
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(14, 10, 14, 10)
        info_layout.setSpacing(4)

        ver_line = QLabel(
            t(
                "update_version_compare",
                current=f"v{APP_VERSION}",
                latest=self.release.tag_name,
            )
        )
        ver_line.setObjectName("SectionTitle")
        info_layout.addWidget(ver_line)

        if self.release.asset_name and self.release.asset_size > 0:
            size_mb = self.release.asset_size / (1024 * 1024)
            file_line = QLabel(
                t("update_asset_info", name=self.release.asset_name, size=f"{size_mb:.1f} MB")
            )
            file_line.setObjectName("PageDesc")
            info_layout.addWidget(file_line)
        elif not self.release.download_url:
            no_asset_line = QLabel(t("update_no_installer_asset"))
            no_asset_line.setObjectName("PageDesc")
            no_asset_line.setWordWrap(True)
            info_layout.addWidget(no_asset_line)

        root.addWidget(info_card)

        notes_lbl = QLabel(t("update_notes_label"))
        notes_lbl.setObjectName("SectionTitle")
        root.addWidget(notes_lbl)

        self.notes_box = QPlainTextEdit()
        self.notes_box.setReadOnly(True)
        self.notes_box.setMaximumHeight(160)
        self.notes_box.setPlainText(
            self.release.notes if self.release.notes else t("update_notes_empty")
        )
        root.addWidget(self.notes_box)

        self.status_lbl = QLabel("")
        self.status_lbl.setObjectName("StatusBanner")
        self.status_lbl.setVisible(False)
        self.status_lbl.setWordWrap(True)
        root.addWidget(self.status_lbl)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        root.addWidget(self.progress_bar)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.open_page_btn = QPushButton(t("update_btn_open_page"))
        self.open_page_btn.setCursor(Qt.PointingHandCursor)
        self.open_page_btn.clicked.connect(self._open_release_page)
        btn_row.addWidget(self.open_page_btn)

        btn_row.addStretch(1)

        self.later_btn = QPushButton(t("update_btn_later"))
        self.later_btn.setCursor(Qt.PointingHandCursor)
        self.later_btn.clicked.connect(self._on_later_or_cancel)
        btn_row.addWidget(self.later_btn)

        self.install_btn = QPushButton(t("update_btn_now"))
        self.install_btn.setObjectName("PrimaryButton")
        self.install_btn.setCursor(Qt.PointingHandCursor)
        self.install_btn.setDefault(True)
        self.install_btn.setEnabled(bool(self.release.download_url))
        self.install_btn.clicked.connect(self._start_download)
        btn_row.addWidget(self.install_btn)

        root.addLayout(btn_row)

    def _set_status(self, text: str, state: str = "idle") -> None:
        self.status_lbl.setText(text)
        self.status_lbl.setProperty("state", state)
        self.status_lbl.style().unpolish(self.status_lbl)
        self.status_lbl.style().polish(self.status_lbl)
        self.status_lbl.setVisible(True)

    def _open_release_page(self) -> None:
        QDesktopServices.openUrl(QUrl(self.release.html_url))

    def _on_later_or_cancel(self) -> None:
        if self._downloader is not None and self._downloader.isRunning():
            self._downloader.request_cancel()
            self.later_btn.setEnabled(False)
            self._set_status(self.i18n.t("update_cancelling"), "idle")
            return
        self.reject()

    def _start_download(self) -> None:
        if not self.release.download_url:
            return
        t = self.i18n.t
        self.install_btn.setEnabled(False)
        self.open_page_btn.setEnabled(False)
        self.later_btn.setText(t("btn_cancel"))
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self._set_status(t("update_downloading", percent=0, current="0.0", total="?"), "running")

        self._downloader = UpdateDownloadWorker(
            url=self.release.download_url,
            filename=self.release.asset_name or "PDFOrganizeTool_Setup.exe",
        )
        self._downloader.progress.connect(self._on_progress)
        self._downloader.completed.connect(self._on_download_completed)
        self._downloader.cancelled.connect(self._on_download_cancelled)
        self._downloader.failed.connect(self._on_download_failed)
        self._downloader.start()

    def _on_progress(self, downloaded: int, total: int) -> None:
        cur_mb = downloaded / (1024 * 1024)
        if total > 0:
            pct = min(100, int(downloaded * 100 / total))
            tot_mb = total / (1024 * 1024)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(pct)
            self._set_status(
                self.i18n.t(
                    "update_downloading",
                    percent=pct,
                    current=f"{cur_mb:.1f}",
                    total=f"{tot_mb:.1f}",
                ),
                "running",
            )
        else:
            self.progress_bar.setRange(0, 0)
            self._set_status(
                self.i18n.t("update_downloading_unknown", current=f"{cur_mb:.1f}"),
                "running",
            )

    def _on_download_completed(self, installer_path: str) -> None:
        t = self.i18n.t
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self._set_status(t("update_launching_installer"), "done")
        try:
            launch_installer_for_update(installer_path)
            self.accept()
            app = QApplication.instance()
            if app is not None:
                app.quit()
        except Exception as exc:
            self._on_download_failed(str(exc))

    def _on_download_cancelled(self) -> None:
        t = self.i18n.t
        self.progress_bar.setVisible(False)
        self.install_btn.setEnabled(True)
        self.open_page_btn.setEnabled(True)
        self.later_btn.setEnabled(True)
        self.later_btn.setText(t("update_btn_later"))
        self._set_status(t("update_cancelled"), "idle")

    def _on_download_failed(self, error_msg: str) -> None:
        t = self.i18n.t
        self.progress_bar.setVisible(False)
        self.install_btn.setEnabled(True)
        self.open_page_btn.setEnabled(True)
        self.later_btn.setEnabled(True)
        self.later_btn.setText(t("update_btn_later"))
        self._set_status(t("update_download_error", error=error_msg), "error")
        QMessageBox.critical(self, t("msg_error"), t("update_download_error", error=error_msg))

    def closeEvent(self, event) -> None:
        if self._downloader is not None and self._downloader.isRunning():
            self._downloader.request_cancel()
            self._downloader.wait(1500)
        super().closeEvent(event)
