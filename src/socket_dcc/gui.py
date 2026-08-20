from __future__ import annotations

import json
import socket
import sys
import threading

from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QPlainTextEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Signal

from .server import SocketExecutionServer


class MainWindow(QMainWindow):
    log_requested = Signal(str)
    status_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("socket-dcc")

        self.log_requested.connect(self.append_log)
        self.status_requested.connect(self.set_status)
        self.server = SocketExecutionServer(self.log_requested.emit, self.status_requested.emit)

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

        connection_row.addWidget(QLabel("Host"), 0, 0)
        connection_row.addWidget(self.host_input, 0, 1)
        connection_row.addWidget(QLabel("Port"), 0, 2)
        connection_row.addWidget(self.port_input, 0, 3)
        connection_row.addWidget(QLabel("Token"), 1, 0)
        connection_row.addWidget(self.token_input, 1, 1, 1, 3)

        button_row = QHBoxLayout()
        self.start_button = QPushButton("Start Server")
        self.stop_button = QPushButton("Stop Server")
        self.run_button = QPushButton("Send Python Command")
        button_row.addWidget(self.start_button)
        button_row.addWidget(self.stop_button)
        button_row.addWidget(self.run_button)

        self.command_input = QPlainTextEdit("print('hello from socket-dcc')")
        self.command_input.setPlaceholderText("Enter Python code to execute on the socket server")
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

        self.setCentralWidget(central)
        self.token_input.setText(self.server.auth_token)

    def append_log(self, message: str) -> None:
        if message:
            self.log_output.appendPlainText(message)

    def set_status(self, message: str) -> None:
        self.status_label.setText(message)

    def start_server(self) -> None:
        try:
            self.server.start(self.host_input.text().strip(), int(self.port_input.value()))
        except OSError as exc:
            self.append_log(f"Failed to start server: {exc}")

    def stop_server(self) -> None:
        self.server.stop()

    def send_command(self) -> None:
        code = self.command_input.toPlainText().strip()
        if not code:
            self.append_log("No command to send.")
            return

        host = self.host_input.text().strip()
        port = int(self.port_input.value())
        token = self.token_input.text()
        threading.Thread(
            target=self._send_command,
            args=(host, port, token, code),
            daemon=True,
        ).start()

    def _send_command(self, host: str, port: int, token: str, code: str) -> None:
        try:
            with socket.create_connection((host, port), timeout=3) as sock:
                payload = json.dumps({"code": code, "token": token}) + "\n"
                sock.sendall(payload.encode("utf-8"))
                with sock.makefile("r", encoding="utf-8") as stream:
                    response = stream.readline()
        except OSError as exc:
            self.log_requested.emit(f"Socket error: {exc}")
            return

        if not response:
            self.log_requested.emit("No response from server.")
            return

        try:
            data = json.loads(response)
        except json.JSONDecodeError as exc:
            self.log_requested.emit(f"Invalid server response: {exc}")
            return
        output = data.get("output", "")
        if data.get("ok", False):
            if output:
                self.log_requested.emit(output)
        else:
            self.log_requested.emit(f"ERROR: {output or 'Command failed'}")


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(900, 700)
    window.show()
    sys.exit(app.exec())
