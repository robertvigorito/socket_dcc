"""Main window for socket-dcc GUI."""

import os

from dotenv import load_dotenv
from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QApplication, QMainWindow
from rich.console import Console

from socket_dcc.core.gui.commands import send_command
from socket_dcc.core.gui.layout import create_central_widget
from socket_dcc.core.gui.server import start_server, stop_server
from socket_dcc.core.gui.signals import signal_received
from socket_dcc.core.gui.utils import append_log, clear_log, get_host_info, set_status
from socket_dcc.server import SocketExecutionServer

load_dotenv()

console = Console()


class MainWindow(QMainWindow):
    """Main GUI window for socket-dcc server control and code execution.

    Attributes:
        log_requested: Signal emitted when output needs to be logged.
        status_requested: Signal emitted for status updates.
        code_received: Signal emitted when code is received from CLI.
    """

    log_requested = Signal(str)
    status_requested = Signal(str)
    code_received = Signal(str)

    def __init__(self) -> None:
        """Initialize the main window with server controls and code editor."""
        super().__init__()
        self.setWindowTitle("socket-dcc")

        # Connect signals
        self.log_requested.connect(self._on_log_requested)
        self.status_requested.connect(self._on_status_requested)
        self.code_received.connect(self._on_code_received)

        # Create server
        env_token = os.environ.get("SOCKET_DCC_TOKEN")
        self.server = SocketExecutionServer(
            self.log_requested.emit,
            self.status_requested.emit,
            self.code_received.emit,
            env_token,
        )

        # Set up signal checking timer
        self.signal_timer = QTimer()
        self.signal_timer.timeout.connect(self.check_signal)
        self.signal_timer.start(100)  # Check every 100ms

        # Set up auto-stop timer
        self.auto_stop_timer = QTimer()
        self.auto_stop_timer.timeout.connect(self._do_auto_stop)

        # Create UI
        central, components = create_central_widget()
        self.setCentralWidget(central)

        # Store component references
        self.host_input = components["host_input"]
        self.port_input = components["port_input"]
        self.token_input = components["token_input"]
        self.status_label = components["status_label"]
        self.auto_stop_checkbox = components["auto_stop_checkbox"]
        self.auto_stop_timeout = components["auto_stop_timeout"]
        self.start_button = components["start_button"]
        self.stop_button = components["stop_button"]
        self.run_button = components["run_button"]
        self.clear_button = components["clear_button"]
        self.host_button = components["host_button"]
        self.command_input = components["command_input"]
        self.log_output = components["log_output"]

        # Connect button signals
        self.start_button.clicked.connect(self._start_server)
        self.stop_button.clicked.connect(self._stop_server)
        self.run_button.clicked.connect(self._send_command)
        self.clear_button.clicked.connect(self._clear_log)
        self.host_button.clicked.connect(self._get_host_info)

        # Set token and log
        self.token_input.setText(self.server.auth_token)
        if env_token:
            self._append_log("Token loaded from SOCKET_DCC_TOKEN environment variable")

        # Connect auto-stop checkbox
        self.auto_stop_checkbox.stateChanged.connect(self._handle_auto_stop_toggle)

    def _append_log(self, message: str) -> None:
        """Append a message to log."""
        append_log(self.log_output, message)

    def _on_log_requested(self, message: str) -> None:
        """Handle log requested signal."""
        self._append_log(message)

    def _on_status_requested(self, message: str) -> None:
        """Handle status requested signal."""
        set_status(self.status_label, message)

    def _on_code_received(self, code: str) -> None:
        """Handle code received signal."""
        self.command_input.setPlainText(code)
        self._append_log(f"[CLI] Code received: {len(code)} characters")

    def _start_server(self) -> None:
        """Start the server."""
        start_server(
            self.server,
            self.host_input,
            self.port_input,
            self.auto_stop_checkbox,
            self.auto_stop_timeout,
            self.auto_stop_timer,
            self.start_button,
            self.stop_button,
            self._append_log,
        )

    def _stop_server(self) -> None:
        """Stop the server."""
        stop_server(
            self.server, self.auto_stop_timer, self.stop_button, self.start_button
        )

    def _send_command(self) -> None:
        """Send command to server."""
        send_command(
            self.command_input,
            self.server,
            self.host_input,
            self.port_input,
            self.token_input,
            self._append_log,
        )

    def _clear_log(self) -> None:
        """Clear the log."""
        clear_log(self.log_output)

    def _get_host_info(self) -> None:
        """Get and display host information."""
        try:
            info = get_host_info()
            self._append_log(info)
            console.print(f"[cyan]{info}[/cyan]")
        except Exception as exc:
            error_msg = f"Failed to get host info: {exc}"
            self._append_log(error_msg)
            console.print(f"[red]{error_msg}[/red]")

    def check_signal(self) -> None:
        """Check if a termination signal was received and close the app."""
        if signal_received():
            self.signal_timer.stop()
            console.print("[yellow]Closing GUI...[/yellow]")
            QApplication.instance().quit()

    def _handle_auto_stop_toggle(self) -> None:
        """Handle the auto-stop checkbox toggle."""
        if self.server.is_running and self.auto_stop_checkbox.isChecked():
            timeout_ms = int(self.auto_stop_timeout.value() * 60 * 1000)
            self._append_log(
                f"[cyan]Auto-stop timeout updated to {self.auto_stop_timeout.value():.1f} minutes[/cyan]"
            )
            self.auto_stop_timer.start(timeout_ms)
        else:
            self.auto_stop_timer.stop()

    def _do_auto_stop(self) -> None:
        """Automatically stop the server after timeout."""
        self.auto_stop_timer.stop()
        self._append_log("[yellow]Auto-stop: Server timeout reached[/yellow]")
        self._stop_server()
