"""GUI for socket-dcc code execution server."""

from __future__ import annotations

import signal
import sys

from PySide6.QtWidgets import QApplication

from .window import MainWindow


def main() -> None:
    """Launch the socket-dcc GUI application."""
    from .signals import setup_signal_handlers

    setup_signal_handlers()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(900, 700)
    window.show()

    sys.exit(app.exec())
