"""Main window for the socket-dcc connection panel."""

from typing import Any, cast

import Qt
from rich.console import Console

from socket_dcc.core.gui.layout import create_central_widget
from socket_dcc.core.gui.signals import signal_received
from socket_dcc.core.gui.utils import append_log
from socket_dcc.defaults import get_default_host, get_default_settings, save_default_settings
from socket_dcc.server import SocketExecutionServer

console = Console()


class MainWindow(Qt.QtWidgets.QMainWindow):
    """Small server connection window matching the socket-dcc reference UI."""

    status_requested = Qt.QtCore.Signal(str)
    log_requested = Qt.QtCore.Signal(str)
    code_requested = Qt.QtCore.Signal(str)

    def __init__(self, host: str | None = None, port: int | None = None, token: str | None = None) -> None:
        """Initialize the connection panel, menus, and socket server.

        Args:
            host: Optional server host override.
            port: Optional server port override.
            token: Optional authentication token override.
        """
        super().__init__()
        self.setWindowTitle("socket-dcc")
        self.resize(940, 470)
        self.setMinimumSize(940, 280)
        self.setStyleSheet(
            "QMainWindow, QWidget { background-color: #333333; color: #dddddd; }"
            "QMenuBar { background-color: #333333; color: #eeeeee; }"
            "QMenuBar::item { padding: 3px 8px; background: transparent; }"
            "QMenuBar::item:selected, QMenu::item:selected { background-color: #505050; }"
            "QMenu { background-color: #333333; color: #eeeeee; border: 1px solid #555555; }"
            "QLabel { color: #dddddd; }"
            "QLabel#statusValue { color: #ffb13b; }"
            "QSpinBox, QLineEdit, QPushButton { background-color: #444444; border: 1px solid #555555; }"
            "QSpinBox, QLineEdit { padding: 2px 4px; }"
            "QPushButton { padding: 3px; }"
            "QPushButton:hover { background-color: #505050; }"
            "QPlainTextEdit { background-color: #252525; color: #dddddd; border: 1px solid #555555; }"
        )

        default_port, default_token = get_default_settings()
        self._ip_address = host or self._get_local_ip()
        central, components = create_central_widget(self._ip_address, port or default_port)
        self.setCentralWidget(central)
        self.status_value = components["status_value"]
        self.ip_value = components["ip_value"]
        self.copy_host_button = components["copy_host_button"]
        self.port_input = components["port_input"]
        self.token_input = components["token_input"]
        self.copy_token_button = components["copy_token_button"]
        self.connect_button = components["connect_button"]
        self.log_output = components["log_output"]
        self.submitted_code = components["submitted_code"]

        cast(Any, self.status_requested).connect(self._set_status)
        cast(Any, self.log_requested).connect(self._append_log)
        cast(Any, self.code_requested).connect(self._display_submitted_code)
        cast(Any, self.code_requested).connect(self._record_socket_activity)
        self.server = SocketExecutionServer(
            log_callback=cast(Any, self.log_requested).emit,
            status_callback=cast(Any, self.status_requested).emit,
            code_received_callback=cast(Any, self.code_requested).emit,
        )
        self.token_input.setText(token or default_token or self.server.auth_token)
        self._idle_timeout_seconds = 600
        self.idle_timer = Qt.QtCore.QTimer(self)
        self.idle_timer.setSingleShot(True)
        cast(Any, self.idle_timer.timeout).connect(self._disconnect_for_idle)

        self.connect_button.clicked.connect(self._toggle_connection)
        self.copy_host_button.clicked.connect(self._copy_host)
        self.copy_token_button.clicked.connect(self._copy_token)
        self._create_menus()
        self._set_status("Idle")

        self.signal_timer = Qt.QtCore.QTimer(self)
        cast(Any, self.signal_timer.timeout).connect(self.check_signal)
        self.signal_timer.start(100)

    @staticmethod
    def _get_local_ip() -> str:
        """Return the host's primary IPv4 address, falling back to loopback.

        Returns:
            str: The IP address to display and bind the server to.
        """
        return get_default_host()

    def _create_menus(self) -> None:
        """Create the Help and Settings menus shown in the reference UI.

        Returns:
            None: Adds the menus and their actions to the window.
        """
        settings_menu = self.menuBar().addMenu("Settings")
        settings_menu.addAction("Refresh IP address", self._refresh_ip)
        settings_menu.addAction("Set idle timeout…", self._set_idle_timeout)
        self.auto_disconnect_action = settings_menu.addAction("Auto-disconnect when idle")
        self.auto_disconnect_action.setCheckable(True)
        self.auto_disconnect_action.toggled.connect(self._toggle_auto_disconnect)
        self.auto_close_action = settings_menu.addAction("Close application after disconnect")
        self.auto_close_action.setCheckable(True)

        log_menu = self.menuBar().addMenu("Log")
        self.show_log_action = log_menu.addAction("Show Log")
        self.show_log_action.setCheckable(True)
        self.show_log_action.setChecked(True)
        self.show_log_action.toggled.connect(self._toggle_log)
        log_menu.addAction("Clear Log", self._clear_log)

        code_menu = self.menuBar().addMenu("Code")
        self.show_code_action = code_menu.addAction("Show Submitted Code")
        self.show_code_action.setCheckable(True)
        self.show_code_action.setChecked(True)
        self.show_code_action.toggled.connect(self._toggle_code)
        self.append_code_action = code_menu.addAction("Append Submitted Code")
        self.append_code_action.setCheckable(True)
        self.append_code_action.setChecked(True)
        code_menu.addAction("Clear Submitted Code", self._clear_submitted_code)

        help_menu = self.menuBar().addMenu("Help")
        help_menu.addAction("About socket-dcc", self._show_about)

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

    @Qt.QtCore.Slot(str)
    def _display_submitted_code(self, code: str) -> None:
        """Display source received from a socket client.

        Args:
            code: Python source received by the server.

        Returns:
            None: Replaces or appends source in the submitted-code pane.
        """
        console.print("Received code:", style="bold cyan")
        console.print(code, style="bright_white", markup=False)
        if self.append_code_action.isChecked():
            existing_code = self.submitted_code.toPlainText()
            if existing_code and not existing_code.endswith("\n"):
                self.submitted_code.insertPlainText("\n")
            self.submitted_code.insertPlainText(code)
            if not code.endswith("\n"):
                self.submitted_code.insertPlainText("\n")
        else:
            self.submitted_code.setPlainText(code)

    def _clear_submitted_code(self) -> None:
        """Clear the submitted-code pane.

        Returns:
            None: Removes all displayed submitted source.
        """
        self.submitted_code.clear()

    def _toggle_code(self, visible: bool) -> None:
        """Show or hide the submitted-code pane.

        Args:
            visible: Whether source should be visible.

        Returns:
            None: Updates submitted-code pane visibility.
        """
        self.submitted_code.setVisible(visible)

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
        Qt.QtWidgets.QMessageBox.about(self, "About socket-dcc", "Socket DCC connection server")

    def _refresh_ip(self) -> None:
        """Refresh the displayed local IP address.

        Returns:
            None: Updates the IP label when the server is disconnected.
        """
        if self.server.is_running:
            return
        self._ip_address = self._get_local_ip()
        self.ip_value.setText(self._ip_address)

    def _copy_token(self) -> None:
        """Copy the current authentication token to the system clipboard.

        Returns:
            None: Copies the token without exposing it in logs.
        """
        Qt.QtWidgets.QApplication.clipboard().setText(self.token_input.text())
        self.copy_token_button.setToolTip("Token copied")
        Qt.QtCore.QTimer.singleShot(
            1500,
            lambda: self.copy_token_button.setToolTip("Copy the authentication token to the clipboard"),
        )

    def _copy_host(self) -> None:
        """Copy the displayed server host to the system clipboard.

        Returns:
            None: Copies the host without exposing it in logs.
        """
        Qt.QtWidgets.QApplication.clipboard().setText(self.ip_value.text())
        self.copy_host_button.setToolTip("Host copied")
        Qt.QtCore.QTimer.singleShot(
            1500,
            lambda: self.copy_host_button.setToolTip("Copy the server host to the clipboard"),
        )

    def _set_idle_timeout(self) -> None:
        """Set the duration without socket activity before auto-disconnecting.

        Returns:
            None: Updates the idle timeout when the user confirms a value.
        """
        dialog = self._create_idle_timeout_dialog()
        if dialog.exec() == getattr(Qt.QtWidgets.QDialog, "Accepted"):
            minutes = dialog.intValue()
            self._idle_timeout_seconds = minutes * 60
            if self.server.is_running and self.auto_disconnect_action.isChecked():
                self._restart_idle_timer()
            self._append_log(f"Idle timeout set to {minutes} minute(s).")

    def _create_idle_timeout_dialog(self) -> Qt.QtWidgets.QInputDialog:
        """Create the borderless dialog used to set the idle timeout.

        Returns:
            QInputDialog: Integer input dialog configured with a frameless window.
        """
        dialog = Qt.QtWidgets.QInputDialog(self)
        dialog.setWindowTitle("Idle timeout")
        dialog.setLabelText("Disconnect after this many idle minutes:")
        dialog.setInputMode(getattr(Qt.QtWidgets.QInputDialog, "IntInput"))
        dialog.setIntRange(1, 1440)
        dialog.setIntValue(max(1, self._idle_timeout_seconds // 60))
        dialog.setWindowFlags(dialog.windowFlags() | getattr(Qt.QtCore.Qt, "FramelessWindowHint"))
        return dialog

    def _toggle_auto_disconnect(self, enabled: bool) -> None:
        """Enable or disable disconnecting after the configured idle period.

        Args:
            enabled: Whether idle auto-disconnect is enabled.

        Returns:
            None: Starts or stops the idle timer as appropriate.
        """
        if enabled and self.server.is_running:
            self._restart_idle_timer()
        else:
            self.idle_timer.stop()

    def _restart_idle_timer(self) -> None:
        """Restart the configured inactivity timer.

        Returns:
            None: Arms the one-shot idle timer.
        """
        self.idle_timer.start(self._idle_timeout_seconds * 1000)

    @Qt.QtCore.Slot(str)
    def _record_socket_activity(self, _code: str) -> None:
        """Restart idle detection after receiving code from a client.

        Args:
            _code: Source received by the socket server.

        Returns:
            None: Restarts auto-disconnect timing when enabled.
        """
        if self.auto_disconnect_action.isChecked():
            self._restart_idle_timer()

    def _disconnect_for_idle(self) -> None:
        """Disconnect the server after the configured idle period.

        Returns:
            None: Disconnects the server and optionally closes the application.
        """
        if self.server.is_running:
            self._disconnect_server("[yellow]Disconnected after reaching the idle timeout.[/yellow]")

    def _toggle_connection(self) -> None:
        """Start or stop the socket server from the main button.

        Returns:
            None: Updates the connection status and button state.
        """
        if self.server.is_running:
            self._disconnect_server("[yellow]Disconnected from the socket server.[/yellow]")
            return

        token = self.token_input.text().strip()
        if not token:
            self._set_status("Error")
            self._append_log("[red]Authentication token cannot be empty.[/red]")
            return

        self.server.auth_token = token
        try:
            self.server.start(self._ip_address, self.port_input.value())
        except OSError as exc:
            self._set_status("Error")
            console.print(f"[red]Failed to connect: {exc}[/red]")
            return

        save_default_settings(self.port_input.value(), token)

        self._set_status("Connected")
        self.connect_button.setText("Disconnect")
        self.token_input.setEnabled(False)
        self.port_input.setEnabled(False)
        if self.auto_disconnect_action.isChecked():
            self._restart_idle_timer()
        self._append_log(f"[green]Listening on {self._ip_address}:{self.port_input.value()}[/green]")
        console.print(f"[green]Listening on {self._ip_address}:{self.port_input.value()}[/green]")

    def _disconnect_server(self, message: str) -> None:
        """Stop the server, update controls, log the reason, and optionally close.

        Args:
            message: Rich-formatted reason to display in the log.

        Returns:
            None: Resets connection controls and honors the close-after-disconnect option.
        """
        self.idle_timer.stop()
        self.server.stop()
        self._append_log(message)
        self._set_status("Idle")
        self.connect_button.setText("Connect")
        self.token_input.setEnabled(True)
        self.port_input.setEnabled(True)
        if self.auto_close_action.isChecked():
            self.close()

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
        button_color = "#d99b2b" if display == "Idle" else "#388e3c" if display == "Connected" else "#a83f3f"
        self.connect_button.setStyleSheet(
            f"QPushButton {{ background-color: {button_color}; border: 1px solid #666666; padding: 3px; }}"
            "QPushButton:hover { background-color: #505050; }"
        )

    def check_signal(self) -> None:
        """Stop the Qt event loop when a termination signal is received.

        Returns:
            None: Quits the application event loop when requested.
        """
        if signal_received():
            self.signal_timer.stop()
            app = Qt.QtWidgets.QApplication.instance()
            if app is not None:
                app.quit()

    def closeEvent(self, event: Qt.QtGui.QCloseEvent) -> None:
        """Stop the server before closing the window.

        Args:
            event: Qt close event.

        Returns:
            None: Stops the server and accepts the close event.
        """
        if self.server.is_running:
            self._disconnect_server("[yellow]Disconnected because the window is closing.[/yellow]")
        event.accept()
