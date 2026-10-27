"""GUI interface for socket-dcc."""

import sys

from Qt import QtWidgets

from socket_dcc.core.gui.signals import setup_signal_handlers
from socket_dcc.core.gui.window import MainWindow


def main(host: str | None = None, port: int | None = None, token: str | None = None) -> int:
    """Launch the socket-dcc GUI application.

    Args:
        host: Optional server host override.
        port: Optional server port override.
        token: Optional authentication token override.

    Returns:
        int: The Qt event-loop exit status.
    """
    setup_signal_handlers()

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    window = MainWindow(host=host, port=port, token=token)
    window.show()

    return app.exec()


def load_in_application() -> object:
    """Create and show the GUI in the host application's Qt event loop.

    Returns:
        object: The main window, which the host should retain for its lifetime.
    """
    setup_signal_handlers()

    if QtWidgets.QApplication.instance() is None:
        QtWidgets.QApplication(sys.argv)

    window = MainWindow()
    window.show()
    return window


if __name__ == "__main__":
    raise SystemExit(main())
