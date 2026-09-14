"""Uygulama giriş noktası: `python -m app`."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from app import APP_NAME
from app.core.i18n import tr
from app.core.paths import app_icon_path
from app.ui.main_window import MainWindow
from app.ui.theme import STYLESHEET


def _set_windows_app_id() -> None:
    """Görev çubuğunda genel Python simgesi yerine kendi simgemiz görünsün diye."""
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_NAME)
        except Exception:
            pass


def create_app(argv: list[str] | None = None) -> QApplication:
    _set_windows_app_id()
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("Docon")
    app.setStyle("Fusion")
    icon_path = app_icon_path()
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    app.setStyleSheet(STYLESHEET)
    return app


def main() -> int:
    app = create_app()
    from app.core.system import SingleInstance
    from PySide6.QtWidgets import QMessageBox
    lock = SingleInstance()
    if not lock.acquire():
        QMessageBox.information(None, APP_NAME, tr("{name} zaten açık. Görev çubuğundaki pencereyi kullan.", name=APP_NAME))
        return 0
    window = MainWindow()
    window.show()
    rc = app.exec()
    del lock
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
