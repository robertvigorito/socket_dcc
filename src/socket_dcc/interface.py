"""GUI interface for socket-dcc."""

import sys
from collections.abc import Callable

from Qt import QtWidgets

from socket_dcc.core.gui.signals import setup_signal_handlers
from socket_dcc.core.gui.window import MainWindow
from socket_dcc.server import ExecutionDispatcher, ExecutionResponse


def _nuke_execution_callbacks() -> tuple[ExecutionDispatcher | None, Callable[[str], None] | None]:
    """Return Nuke's main-thread dispatcher and Script Editor output callback when available.

    Returns:
        tuple: Execution dispatcher and output callback, or ``(None, None)`` outside Nuke.
    """
    try:
        import nuke
    except ImportError:
        return None, None

    def dispatch_to_main_thread(task: Callable[[], ExecutionResponse]) -> ExecutionResponse:
        """Run a callback synchronously on Nuke's main thread.

        Args:
            task: Execution callback to invoke.

        Returns:
            ExecutionResponse: Result returned by the host thread.
        """
        return nuke.executeInMainThreadWithResult(task)

    return dispatch_to_main_thread, nuke.tprint


class NukeMainWindow(MainWindow):
    """Panel widget configured to execute requests on Nuke's main thread."""

    def __init__(
        self,
        parent: object | None = None,
        host: str | None = None,
        port: int | None = None,
        token: str | None = None,
    ) -> None:
        """Create the Nuke panel with Nuke-safe execution and output callbacks.

        Args:
            parent: Optional parent widget supplied by Nuke's panel registry.
            host: Optional server host override.
            port: Optional server port override.
            token: Optional authentication token override.

        Returns:
            None: Initializes the panel and its socket server.
        """
        execution_dispatcher, script_editor_callback = _nuke_execution_callbacks()
        super().__init__(
            host=host,
            port=port,
            token=token,
            parent=parent,
            execution_dispatcher=execution_dispatcher,
            script_editor_callback=script_editor_callback,
        )


def _post_launch(
    host: str | None = None,
    port: int | None = None,
    token: str | None = None,
    connect: bool = False,
    execution_dispatcher: ExecutionDispatcher | None = None,
    script_editor_callback: Callable[[str], None] | None = None,
) -> MainWindow:
    """Create, configure, and show the GUI window.

    Args:
        host: Optional server host override.
        port: Optional server port override.
        token: Optional authentication token override.
        connect: Whether to connect to the socket server after creating the window.
        execution_dispatcher: Optional host-thread execution dispatcher.
        script_editor_callback: Optional callback for output in the host Script Editor.

    Returns:
        MainWindow: The configured and visible application window.
    """
    setup_signal_handlers()
    window = MainWindow(
        host=host,
        port=port,
        token=token,
        execution_dispatcher=execution_dispatcher,
        script_editor_callback=script_editor_callback,
    )
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

    execution_dispatcher, script_editor_callback = _nuke_execution_callbacks()
    window = _post_launch(
        host=host,
        port=port,
        token=token,
        connect=connect,
        execution_dispatcher=execution_dispatcher,
        script_editor_callback=script_editor_callback,
    )
    return window


if __name__ == "__main__":
    raise SystemExit(launch())
