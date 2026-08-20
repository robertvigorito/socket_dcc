"""GUI for socket-dcc code execution server."""

from __future__ import annotations

import os
import signal
import socket
import sys
import threading

from dotenv import load_dotenv
from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from rich.console import Console

from .client import send_code
from .server import SocketExecutionServer

load_dotenv()

console = Console()

# Global flag for signal detection
_signal_received = False


def _signal_handler(signum: int, frame: object) -> None:
    """Handle termination signals by setting a global flag.

    Args:
        signum: Signal number.
        frame: Current stack frame.
    """
    global _signal_received
    _signal_received = True
    if signum == signal.SIGTSTP:
        console.print("[yellow]Ctrl+Z detected[/yellow]")
    elif signum == signal.SIGINT:
        console.print("[yellow]Ctrl+C detected[/yellow]")


class MainWindow(QMainWindow):
    """Main GUI window for socket-dcc server control and code execution.

    Attributes:
        log_requested: Signal emitted when output needs to be logged.
        status_requested: Signal emitted for status updates.
        code_received: Signal emitted when code is received from CLI.
        server: The SocketExecutionServer instance.
    """

    log_requested = Signal(str)
    status_requested = Signal(str)
    code_received = Signal(str)

    def __init__(self) -> None:
        """Initialize the main window with server controls and code editor."""
        super().__init__()
        self.setWindowTitle("socket-dcc")

        self.log_requested.connect(self.append_log)
        self.status_requested.connect(self.set_status)
        self.code_received.connect(self.set_command)
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

        central = QWidget(self)
        layout = QVBoxLayout(central)

        connection_row = QGridLayout()
        self.host_input = QLineEdit("127.0.0.1")
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(5050)
        self.token_input = QLineEdit()
        self.token_input.setReadOnly(True)
        self.status_label = QLabel("Server stopped")
        self.auto_stop_checkbox = QCheckBox("Auto-stop server")
        self.auto_stop_checkbox.setChecked(False)
        self.auto_stop_timeout = QDoubleSpinBox()
        self.auto_stop_timeout.setRange(0.1, 60.0)
        self.auto_stop_timeout.setValue(1.0)
        self.auto_stop_timeout.setDecimals(1)
        self.auto_stop_timeout.setSuffix(" min")

        connection_row.addWidget(QLabel("Host"), 0, 0)
        connection_row.addWidget(self.host_input, 0, 1)
        connection_row.addWidget(QLabel("Port"), 0, 2)
        connection_row.addWidget(self.port_input, 0, 3)
        connection_row.addWidget(QLabel("Token"), 1, 0)
        connection_row.addWidget(self.token_input, 1, 1, 1, 3)
        connection_row.addWidget(self.auto_stop_checkbox, 2, 0)
        connection_row.addWidget(QLabel("Timeout:"), 2, 1)
        connection_row.addWidget(self.auto_stop_timeout, 2, 2)

        button_row = QHBoxLayout()
        self.start_button = QPushButton("Start Server")
        self.stop_button = QPushButton("Stop Server")
        self.run_button = QPushButton("Send Python Command")
        self.clear_button = QPushButton("Clear Log")
        self.host_button = QPushButton("Get Host Info")
        button_row.addWidget(self.start_button)
        button_row.addWidget(self.stop_button)
        button_row.addWidget(self.run_button)
        button_row.addWidget(self.clear_button)
        button_row.addWidget(self.host_button)

        self.command_input = QPlainTextEdit("print('hello from socket-dcc')")
        self.command_input.setPlaceholderText(
            "Enter Python code to execute on the socket server"
        )
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)

        layout.addLayout(connection_row)
        layout.addWidget(self.status_label)
        layout.addWidget(QLabel("Python command"))
        layout.addWidget(self.command_input)
        layout.addLayout(button_row)
        layout.addWidget(QLabel("Log"))
        layout.addWidget(self.log_output)

        self.start_button.clicked.connect(self.start_server)
        self.stop_button.clicked.connect(self.stop_server)
        self.run_button.clicked.connect(self.send_command)
        self.clear_button.clicked.connect(self.clear_log)
        self.host_button.clicked.connect(self.get_host_info)

        self.setCentralWidget(central)
        self.token_input.setText(self.server.auth_token)
        if env_token:
            self.append_log("Token loaded from SOCKET_DCC_TOKEN environment variable")

        # Connect auto-stop checkbox
        self.auto_stop_checkbox.stateChanged.connect(self._handle_auto_stop_toggle)

    def append_log(self, message: str) -> None:
        """Append a message to the log output and print to terminal.

        Args:
            message: Message to append to log.
        """
        if message:
            self.log_output.appendPlainText(message)
            console.print(message)

    def set_status(self, message: str) -> None:
        """Update the status label.

        Args:
            message: Status message to display.
        """
        self.status_label.setText(message)

    def set_command(self, code: str) -> None:
        """Update the command input with code received from CLI.

        Args:
            code: Python code to populate in the command input.
        """
        self.command_input.setPlainText(code)
        self.append_log(f"[CLI] Code received: {len(code)} characters")

    def start_server(self) -> None:
        """Start the execution server on configured host and port."""
        try:
            self.server.start(
                self.host_input.text().strip(), int(self.port_input.value())
            )
            self.start_button.setStyleSheet(
                "background-color: #4CAF50; color: white; font-weight: bold;"
            )
            self.start_button.setDown(True)
            self.stop_button.setStyleSheet("")
            self.stop_button.setDown(False)
            console.print("[green]✓ Server started successfully[/green]")

            # Start auto-stop timer if enabled
            if self.auto_stop_checkbox.isChecked():
                timeout_ms = int(self.auto_stop_timeout.value() * 60 * 1000)
                self.append_log(
                    f"[cyan]Auto-stop enabled: server will stop after {self.auto_stop_timeout.value():.1f} minutes[/cyan]"
                )
                self.auto_stop_timer.start(timeout_ms)
        except OSError as exc:
            error_msg = (
                f"[red]✗ Failed to start server[/red]:\n"
                f"  Host: {self.host_input.text().strip()}\n"
                f"  Port: {self.port_input.value()}\n"
                f"  Error: {exc}\n\n"
                f"Make sure the port is not already in use."
            )
            self.append_log(error_msg)
            console.print(error_msg)

    def stop_server(self) -> None:
        """Stop the execution server."""
        self.auto_stop_timer.stop()
        self.server.stop()
        self.stop_button.setStyleSheet(
            "background-color: #FF9800; color: white; font-weight: bold;"
        )
        self.stop_button.setDown(True)
        self.start_button.setStyleSheet("")
        self.start_button.setDown(False)
        console.print("[yellow]⊘ Server stopped[/yellow]")

    def send_command(self) -> None:
        """Send the code from the command input to the server for execution."""
        code = self.command_input.toPlainText().strip()
        if not code:
            self.append_log("No command to send.")
            return

        if not self.server.is_running:
            error_msg = (
                "[red]✗ Server is not running[/red]. Please click 'Start Server' first."
            )
            self.append_log(error_msg)
            console.print(error_msg)
            return

        console.print("[cyan]>>> Sending code to server...[/cyan]")
        host = self.host_input.text().strip()
        port = int(self.port_input.value())
        token = self.token_input.text()
        threading.Thread(
            target=self._send_command,
            args=(host, port, token, code),
            daemon=True,
        ).start()

    def _send_command(self, host: str, port: int, token: str, code: str) -> None:
        """Send code to the server and handle the response.

        Args:
            host: Server hostname.
            port: Server port.
            token: Authentication token.
            code: Python code to execute.
        """
        try:
            response = send_code(host, port, token, code)
        except OSError as exc:
            error_msg = (
                f"[red]✗ Connection Failed[/red]: Could not connect to server at {host}:{port}\n"
                f"Make sure the server is running and the host/port are correct.\n"
                f"Details: {exc}"
            )
            self.append_log(error_msg)
            return

        if response.ok:
            if response.output:
                self.append_log(response.output)
            else:
                self.append_log("Command executed successfully.")
        else:
            error_msg = response.output or "Command failed"
            self.append_log(f"[bold red]ERROR[/bold red]: {error_msg}")

    def clear_log(self) -> None:
        """Clear the log output."""
        self.log_output.clear()
        console.print("[yellow]Log cleared[/yellow]")

    def get_host_info(self) -> None:
        """Get and display localhost information."""
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            localhost = socket.gethostbyname("localhost")
            info = (
                f"Hostname: {hostname}\nLocal IP: {ip_address}\nLocalhost: {localhost}"
            )
            self.append_log(info)
            console.print(f"[cyan]{info}[/cyan]")
        except OSError as exc:
            error_msg = f"Failed to get host info: {exc}"
            self.append_log(error_msg)
            console.print(f"[red]{error_msg}[/red]")

    def check_signal(self) -> None:
        """Check if a termination signal was received and close the app.

        This method is called periodically by a timer to check if Ctrl+Z or Ctrl+C
        was pressed in the terminal.
        """
        global _signal_received
        if _signal_received:
            self.signal_timer.stop()
            console.print("[yellow]Closing GUI...[/yellow]")
            QApplication.instance().quit()

    def _handle_auto_stop_toggle(self) -> None:
        """Handle the auto-stop checkbox toggle.

        If the server is currently running, restart the timer with the new timeout.
        """
        if self.server.is_running and self.auto_stop_checkbox.isChecked():
            timeout_ms = int(self.auto_stop_timeout.value() * 60 * 1000)
            self.append_log(
                f"[cyan]Auto-stop timeout updated to {self.auto_stop_timeout.value():.1f} minutes[/cyan]"
            )
            self.auto_stop_timer.start(timeout_ms)
        else:
            self.auto_stop_timer.stop()

    def _do_auto_stop(self) -> None:
        """Automatically stop the server after the configured timeout.

        This is called by the auto-stop timer after the timeout duration.
        """
        self.auto_stop_timer.stop()
        self.append_log("[yellow]Auto-stop: Server timeout reached[/yellow]")
        self.stop_server()


def main() -> None:
    """Launch the socket-dcc GUI application."""
    # Set up signal handling
    signal.signal(signal.SIGTSTP, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(900, 700)
    window.show()

    sys.exit(app.exec())
