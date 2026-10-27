"""GUI interface for socket-dcc."""

import sys

from Qt import QtWidgets

from socket_dcc.core.gui.signals import setup_signal_handlers
from socket_dcc.core.gui.window import MainWindow


def _post_launch(
    host: str | None = None, port: int | None = None, token: str | None = None, connect: bool = False
) -> MainWindow:
    """Create, configure, and show the GUI window.

    Args:
        host: Optional server host override.
        port: Optional server port override.
        token: Optional authentication token override.
        connect: Whether to connect to the socket server after creating the window.

    Returns:
        MainWindow: The configured and visible application window.
    """
    setup_signal_handlers()
    window = MainWindow(host=host, port=port, token=token)
    if connect:
        window.connect_button.click()
    window.show()
    return window


def launch(
    host: str | None = None,
    port: int | None = None,
    token: str | None = None,
    connect: bool = False,
) -> int:
    """Launch the socket-dcc GUI application.

    Args:
        host: Optional server host override.
        port: Optional server port override.
        token: Optional authentication token override.
        connect: Whether to connect to the socket server when the GUI opens.

    Returns:
        int: The Qt event-loop exit status.
    """
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    window = _post_launch(host=host, port=port, token=token, connect=connect)
    window.raise_()
    return app.exec()


def load_in_application(
    host: str | None = None,
    port: int | None = None,
    token: str | None = None,
    connect: bool = False,
) -> object:
    """Create and show the GUI in the host application's Qt event loop.

    Args:
        host: Optional server host override.
        port: Optional server port override.
        token: Optional authentication token override.
        connect: Whether to connect to the socket server after creating the window.

    Returns:
        MainWindow: The main window, which the host should retain for its lifetime.
    """
    if QtWidgets.QApplication.instance() is None:
        QtWidgets.QApplication(sys.argv)

    window = _post_launch(host=host, port=port, token=token, connect=connect)
    return window


if __name__ == "__main__":
    raise SystemExit(launch())
