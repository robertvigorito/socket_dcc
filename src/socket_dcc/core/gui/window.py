"""Main window for the socket-dcc connection panel."""

import os
import socket

from dotenv import load_dotenv
from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from rich.console import Console

from socket_dcc.core.gui.layout import create_central_widget
from socket_dcc.core.gui.signals import signal_received
from socket_dcc.core.gui.utils import append_log
from socket_dcc.server import SocketExecutionServer

load_dotenv()

console = Console()


class MainWindow(QMainWindow):
    """Small server connection window matching the socket-dcc reference UI."""

    status_requested = Signal(str)
    log_requested = Signal(str)

    def __init__(self) -> None:
        """Initialize the connection panel, menus, and socket server."""
        super().__init__()
        self.setWindowTitle("socket-dcc")
        self.resize(940, 150)
        self.setMinimumSize(940, 150)
        self.setStyleSheet(
            "QMainWindow, QWidget { background-color: #333333; color: #dddddd; }"
            "QMenuBar { background-color: #333333; color: #eeeeee; }"
            "QMenuBar::item { padding: 3px 8px; background: transparent; }"
            "QMenuBar::item:selected, QMenu::item:selected { background-color: #505050; }"
            "QMenu { background-color: #333333; color: #eeeeee; border: 1px solid #555555; }"
            "QLabel { color: #dddddd; }"
            "QLabel#statusValue { color: #ffb13b; }"
            "QSpinBox, QPushButton { background-color: #444444; border: 1px solid #555555; }"
            "QSpinBox { padding: 2px 4px; }"
            "QPushButton { padding: 3px; }"
            "QPushButton:hover { background-color: #505050; }"
        )

        self._ip_address = self._get_local_ip()
        central, components = create_central_widget(self._ip_address)
        self.setCentralWidget(central)
        self.status_value = components["status_value"]
        self.ip_value = components["ip_value"]
        self.port_input = components["port_input"]
        self.connect_button = components["connect_button"]
        self.log_output = components["log_output"]

        self.status_requested.connect(self._set_status)
        self.log_requested.connect(self._append_log)
        self.server = SocketExecutionServer(
            log_callback=self.log_requested.emit,
            status_callback=self.status_requested.emit,
        )
        env_token = os.environ.get("SOCKET_DCC_TOKEN")
        if env_token:
            self.server.auth_token = env_token

        self.connect_button.clicked.connect(self._toggle_connection)
        self._create_menus()

        self.signal_timer = QTimer(self)
        self.signal_timer.timeout.connect(self.check_signal)
        self.signal_timer.start(100)

    @staticmethod
    def _get_local_ip() -> str:
        """Return the host's primary IPv4 address, falling back to loopback.

        Returns:
            str: The IP address to display and bind the server to.
        """
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "127.0.0.1"

    def _create_menus(self) -> None:
        """Create the Help and Settings menus shown in the reference UI.

        Returns:
            None: Adds the menus and their actions to the window.
        """
        help_menu = self.menuBar().addMenu("Help")
        help_menu.addAction("About socket-dcc", self._show_about)

        settings_menu = self.menuBar().addMenu("Settings")
        settings_menu.addAction("Refresh IP address", self._refresh_ip)

        log_menu = self.menuBar().addMenu("Log")
        self.show_log_action = log_menu.addAction("Show Log")
        self.show_log_action.setCheckable(True)
        self.show_log_action.toggled.connect(self._toggle_log)
        log_menu.addAction("Clear Log", self._clear_log)

    def _append_log(self, message: str) -> None:
        """Append a Rich-formatted message to the log panel.

        Args:
            message: Rich markup or plain text to append.

        Returns:
            None: Appends the message to the log and terminal.
        """
        append_log(self.log_output, message)

    def _clear_log(self) -> None:
        """Clear the log panel.

        Returns:
            None: Removes all displayed log messages.
        """
        self.log_output.clear()

    def _toggle_log(self, visible: bool) -> None:
        """Show or hide the log panel and adjust the window size.

        Args:
            visible: Whether the log panel should be visible.

        Returns:
            None: Updates the log visibility and window height.
        """
        self.log_output.setVisible(visible)
        self.resize(self.width(), 300 if visible else 150)

    def _show_about(self) -> None:
        """Show a short description of the application.

        Returns:
            None: Displays an About dialog.
        """
        QMessageBox.about(self, "About socket-dcc", "Socket DCC connection server")

    def _refresh_ip(self) -> None:
        """Refresh the displayed local IP address.

        Returns:
            None: Updates the IP label when the server is disconnected.
        """
        if self.server.is_running:
            return
        self._ip_address = self._get_local_ip()
        self.ip_value.setText(self._ip_address)

    def _toggle_connection(self) -> None:
        """Start or stop the socket server from the main button.

        Returns:
            None: Updates the connection status and button state.
        """
        if self.server.is_running:
            self.server.stop()
            self._set_status("Idle")
            self.connect_button.setText("Connect")
            return

        try:
            self.server.start(self._ip_address, self.port_input.value())
        except OSError as exc:
            self._set_status("Error")
            console.print(f"[red]Failed to connect: {exc}[/red]")
            return

        self._set_status("Connected")
        self.connect_button.setText("Disconnect")
        self._append_log(f"[green]Listening on {self._ip_address}:{self.port_input.value()}[/green]")
        console.print(f"[green]Listening on {self._ip_address}:{self.port_input.value()}[/green]")

    def _set_status(self, message: str) -> None:
        """Set the status text and its reference-matching color.

        Args:
            message: Status text to display.

        Returns:
            None: Updates the status label and its color.
        """
        display = "Connected" if message.startswith("Listening on") else message
        self.status_value.setText(display)
        color = "#ffb13b" if display == "Idle" else "#76c77a" if display == "Connected" else "#ff6b6b"
        self.status_value.setStyleSheet(f"color: {color};")

    def check_signal(self) -> None:
        """Stop the Qt event loop when a termination signal is received.

        Returns:
            None: Quits the application event loop when requested.
        """
        if signal_received():
            self.signal_timer.stop()
            app = QApplication.instance()
            if app is not None:
                app.quit()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Stop the server before closing the window.

        Args:
            event: Qt close event.

        Returns:
            None: Stops the server and accepts the close event.
        """
        if self.server.is_running:
            self.server.stop()
        event.accept()
