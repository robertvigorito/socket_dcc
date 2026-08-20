"""GUI interface for socket-dcc."""

import sys

from PySide6.QtWidgets import QApplication

from socket_dcc.core.gui.signals import setup_signal_handlers
from socket_dcc.core.gui.window import MainWindow


def main() -> None:
    """Launch the socket-dcc GUI application."""
    setup_signal_handlers()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(900, 700)
    window.show()

    sys.exit(app.exec())
