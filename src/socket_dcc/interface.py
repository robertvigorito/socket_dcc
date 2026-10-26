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
    window.show()

    sys.exit(app.exec())


def load_in_application() -> None:
    """Load the socket-dcc GUI application within an existing QApplication."""
    setup_signal_handlers()

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    window = MainWindow()
    window.show()


load_in_application()