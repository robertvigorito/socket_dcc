import sys
import io
import traceback
from contextlib import redirect_stdout, redirect_stderr

from PySide6.QtCore import Slot
from PySide6.QtNetwork import QHostAddress, QTcpServer, QTcpSocket
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QLineEdit,
    QSpinBox,
    QPushButton,
    QTextEdit,
    QPlainTextEdit,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
)


class ServerWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.server = QTcpServer()
        self.server.newConnection.connect(self.on_new_connection)

        self.setWindowTitle("Socket DCC Server")

        self.host_edit = QLineEdit("192.168.18.21")
        self.port_edit = QSpinBox()
        self.port_edit.setRange(1, 65535)
        self.port_edit.setValue(5000)

        self.start_btn = QPushButton("Start Server")
        self.start_btn.clicked.connect(self.start_server)

        self.log = QTextEdit()
        self.log.setReadOnly(True)

        form = QGridLayout()
        form.addWidget(QLabel("Host:"), 0, 0)
        form.addWidget(self.host_edit, 0, 1)
        form.addWidget(QLabel("Port:"), 1, 0)
        form.addWidget(self.port_edit, 1, 1)

        buttons = QHBoxLayout()
        buttons.addWidget(self.start_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(buttons)
        layout.addWidget(QLabel("Log:"))
        layout.addWidget(self.log)

    def write_log(self, message: str):
        self.log.append(message)

    @Slot()
    def start_server(self):
        if self.server.isListening():
            self.server.close()

        host_text = self.host_edit.text().strip()
        port = self.port_edit.value()
        address = QHostAddress(host_text)

        if address.isNull():
            self.write_log(f"Invalid host: {host_text}")
            return

        if self.server.listen(address, port):
            self.write_log(f"Listening on {host_text}:{port}")
        else:
            self.write_log(f"Failed to start server: {self.server.errorString()}")

    @Slot()
    def on_new_connection(self):
        while self.server.hasPendingConnections():
            client: QTcpSocket = self.server.nextPendingConnection()
            client.readyRead.connect(lambda c=client: self.on_ready_read(c))
            client.disconnected.connect(client.deleteLater)
            self.write_log("Client connected")

    @Slot()
    def on_ready_read(self, client: QTcpSocket):
        """Handle incoming client data and execute received code."""
        code = bytes(client.readAll()).decode("utf-8", errors="replace").strip()
        self.write_log(f"Received code:\n{code}")

        if not code:
            client.write(b"No code received")
            client.flush()
            return

        stdout = io.StringIO()
        stderr = io.StringIO()
        scope: dict = {}

        try:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                exec(code, scope, scope)
        except BaseException as e:
            error_msg = traceback.format_exc()
            self.write_log("Execution failed:")
            self.write_log(error_msg)
            print(error_msg, file=sys.stderr)
            client.write(error_msg.encode("utf-8"))
            client.flush()
            return

        output = stdout.getvalue().strip()
        errors = stderr.getvalue().strip()

        response = output or errors or "Code executed"
        self.write_log(response)
        client.write(response.encode("utf-8"))
        client.flush()


def run_in_nuke():
    window = ServerWindow()
    window.resize(520, 500)
    window.show()
    return window


w = run_in_nuke()
