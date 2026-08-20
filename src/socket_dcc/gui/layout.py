"""UI layout and widget setup for the main window."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


def create_central_widget() -> tuple[QWidget, dict]:
    """Create the central widget and return it with references to key components.

    Returns:
        Tuple of (central_widget, components_dict)
    """
    central = QWidget()
    layout = QVBoxLayout(central)

    # Connection settings row
    connection_row = QGridLayout()
    host_input = QLineEdit("127.0.0.1")
    port_input = QSpinBox()
    port_input.setRange(1, 65535)
    port_input.setValue(5050)
    token_input = QLineEdit()
    token_input.setReadOnly(True)
    status_label = QLabel("Server stopped")

    connection_row.addWidget(QLabel("Host"), 0, 0)
    connection_row.addWidget(host_input, 0, 1)
    connection_row.addWidget(QLabel("Port"), 0, 2)
    connection_row.addWidget(port_input, 0, 3)
    connection_row.addWidget(QLabel("Token"), 1, 0)
    connection_row.addWidget(token_input, 1, 1, 1, 3)

    # Auto-stop row
    auto_stop_checkbox = QCheckBox("Auto-stop server")
    auto_stop_checkbox.setChecked(False)
    auto_stop_timeout = QDoubleSpinBox()
    auto_stop_timeout.setRange(0.1, 60.0)
    auto_stop_timeout.setValue(1.0)
    auto_stop_timeout.setDecimals(1)
    auto_stop_timeout.setSuffix(" min")

    connection_row.addWidget(auto_stop_checkbox, 2, 0)
    connection_row.addWidget(QLabel("Timeout:"), 2, 1)
    connection_row.addWidget(auto_stop_timeout, 2, 2)

    # Buttons row
    button_row = QHBoxLayout()
    start_button = QPushButton("Start Server")
    stop_button = QPushButton("Stop Server")
    run_button = QPushButton("Send Python Command")
    clear_button = QPushButton("Clear Log")
    host_button = QPushButton("Get Host Info")

    button_row.addWidget(start_button)
    button_row.addWidget(stop_button)
    button_row.addWidget(run_button)
    button_row.addWidget(clear_button)
    button_row.addWidget(host_button)

    # Command and log areas
    command_input = QPlainTextEdit("print('hello from socket-dcc')")
    command_input.setPlaceholderText(
        "Enter Python code to execute on the socket server"
    )
    log_output = QPlainTextEdit()
    log_output.setReadOnly(True)

    # Assemble layout
    layout.addLayout(connection_row)
    layout.addWidget(status_label)
    layout.addWidget(QLabel("Python command"))
    layout.addWidget(command_input)
    layout.addLayout(button_row)
    layout.addWidget(QLabel("Log"))
    layout.addWidget(log_output)

    components = {
        "host_input": host_input,
        "port_input": port_input,
        "token_input": token_input,
        "status_label": status_label,
        "auto_stop_checkbox": auto_stop_checkbox,
        "auto_stop_timeout": auto_stop_timeout,
        "start_button": start_button,
        "stop_button": stop_button,
        "run_button": run_button,
        "clear_button": clear_button,
        "host_button": host_button,
        "command_input": command_input,
        "log_output": log_output,
    }

    return central, components
