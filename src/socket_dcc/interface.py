"""GUI interface for socket-dcc."""

import sys

from PySide6.QtWidgets import QApplication

from socket_dcc.core.gui.signals import setup_signal_handlers
from socket_dcc.core.gui.window import MainWindow


def main() -> int:
    """Launch the socket-dcc GUI application.

    Returns:
        int: The Qt event-loop exit status.
    """
    setup_signal_handlers()

    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()

    return app.exec()


def load_in_application() -> object:
    """Create and show the GUI in the host application's Qt event loop.

    Returns:
        object: The main window, which the host should retain for its lifetime.
    """
    setup_signal_handlers()

    if QApplication.instance() is None:
        QApplication(sys.argv)

    window = MainWindow()
    window.show()
    return window


if __name__ == "__main__":
    raise SystemExit(main())
