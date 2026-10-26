"""Compact connection panel layout for the main window."""

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


def create_central_widget(ip_address: str) -> tuple[QWidget, dict[str, Any]]:
    """Create the connection panel and return its interactive components.

    Args:
        ip_address: Local address displayed in the connection panel.

    Returns:
        tuple[QWidget, dict[str, Any]]: Central widget and named component references.
    """
    central = QWidget()
    layout = QVBoxLayout(central)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(5)

    details = QGridLayout()
    details.setContentsMargins(0, 0, 0, 0)
    details.setHorizontalSpacing(5)
    details.setVerticalSpacing(4)

    status_title = QLabel("Status:")
    status_value = QLabel("Idle")
    status_value.setObjectName("statusValue")
    ip_title = QLabel("IP:")
    ip_value = QLabel(ip_address)
    port_title = QLabel("Port:")
    port_input = QSpinBox()
    port_input.setRange(1, 65535)
    port_input.setValue(54322)
    port_input.setFixedWidth(64)

    details.addWidget(status_title, 0, 0, alignment=Qt.AlignmentFlag.AlignRight)
    details.addWidget(status_value, 0, 1, alignment=Qt.AlignmentFlag.AlignLeft)
    details.addWidget(ip_title, 1, 0, alignment=Qt.AlignmentFlag.AlignRight)
    details.addWidget(ip_value, 1, 1, alignment=Qt.AlignmentFlag.AlignLeft)
    details.addWidget(port_title, 2, 0, alignment=Qt.AlignmentFlag.AlignRight)
    details.addWidget(port_input, 2, 1, alignment=Qt.AlignmentFlag.AlignLeft)
    details.setColumnStretch(2, 1)

    connect_button = QPushButton("Connect")
    connect_button.setObjectName("connectButton")
    connect_button.setMinimumHeight(24)

    log_output = QPlainTextEdit()
    log_output.setObjectName("logOutput")
    log_output.setReadOnly(True)
    log_output.setPlaceholderText("Server activity will appear here")
    log_output.setMinimumHeight(120)
    log_output.hide()

    layout.addLayout(details)
    layout.addWidget(connect_button)
    layout.addWidget(log_output)

    components = {
        "status_value": status_value,
        "ip_value": ip_value,
        "port_input": port_input,
        "connect_button": connect_button,
        "log_output": log_output,
    }
    return central, components
