"""PDF整理工具 entry point."""

import ctypes
import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from core.pdf_sign import get_resource_path
from core.version import APP_NAME, APP_VERSION
from ui.main_window import MainWindow


def main() -> int:
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "KaiNengNeng.PDFOrganizeTool.1.0"
            )
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    logo_path = get_resource_path(os.path.join("assets", "applogo.png"))
    if os.path.isfile(logo_path):
        app.setWindowIcon(QIcon(logo_path))

    window = MainWindow(initial_lang="id")
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
