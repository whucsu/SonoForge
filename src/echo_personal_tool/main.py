"""Launch the desktop application."""

from __future__ import annotations

import os
import sys

# KDE Sonnet tries to load hspell (Hebrew) on some Linux desktops; ignore if missing.
# KDE sycoca warns about Cursor's custom MIME type when launched from Cursor terminal.
os.environ.setdefault(
    "QT_LOGGING_RULES",
    "kf.sonnet*=false;kf.sonnet.clients.hspell=false;kf.service.sycoca=false",
)

from PySide6.QtWidgets import QApplication

from echo_personal_tool.presentation.main_window import MainWindow
from echo_personal_tool.presentation.pyqtgraph_export import patch_pyqtgraph_export_dialog


def main() -> int:
    patch_pyqtgraph_export_dialog()
    app = QApplication(sys.argv)
    app.setApplicationName("ECHO Personal Tool")
    window = MainWindow()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
