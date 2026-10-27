"""Compact connection panel layout for the main window."""

from typing import Any

import Qt


def create_central_widget(ip_address: str, port: int) -> tuple[Qt.QtWidgets.QWidget, dict[str, Any]]:
    """Create the connection panel and return its interactive components.

    Args:
        ip_address: Local address displayed in the connection panel.
        port: Default port displayed in the connection panel.

    Returns:
        tuple[Qt.QtWidgets.QWidget, dict[str, Any]]: Central widget and named component references.
    """
    central = Qt.QtWidgets.QWidget()
    layout = Qt.QtWidgets.QVBoxLayout(central)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(5)

    details = Qt.QtWidgets.QGridLayout()
    details.setContentsMargins(0, 0, 0, 0)
    details.setHorizontalSpacing(5)
    details.setVerticalSpacing(4)

    status_title = Qt.QtWidgets.QLabel("Status:")
    status_value = Qt.QtWidgets.QLabel("Idle")
    status_value.setObjectName("statusValue")
    ip_title = Qt.QtWidgets.QLabel("IP:")
    ip_value = Qt.QtWidgets.QLabel(ip_address)
    copy_host_button = Qt.QtWidgets.QPushButton()
    copy_host_button.setObjectName("copyHostButton")
    copy_host_button.setAccessibleName("Copy host")
    copy_host_button.setToolTip("Copy the server host to the clipboard")
    copy_host_button.setFixedSize(30, 30)
    port_title = Qt.QtWidgets.QLabel("Port:")
    port_input = Qt.QtWidgets.QSpinBox()
    port_input.setRange(1, 65535)
    port_input.setValue(port)
    port_input.setFixedWidth(64)
    token_title = Qt.QtWidgets.QLabel("Token:")
    token_input = Qt.QtWidgets.QLineEdit()
    token_input.setObjectName("tokenInput")
    token_input.setPlaceholderText("Authentication token")
    token_input.setMinimumWidth(320)
    token_input.setFixedHeight(30)
    copy_token_button = Qt.QtWidgets.QPushButton()
    copy_token_button.setObjectName("copyTokenButton")
    copy_token_button.setAccessibleName("Copy token")
    copy_token_button.setToolTip("Copy the authentication token to the clipboard")
    copy_token_button.setFixedSize(30, 30)
    copy_icon_svg = Qt.QtCore.QByteArray(
        b'<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">'
        b'<path d="M8 4V16C8 17.1046 8.89543 18 10 18L18 18C19.1046 18 20 17.1046 '
        b"20 16V7.24162C20 6.7034 19.7831 6.18789 19.3982 5.81161L16.0829 "
        b"2.56999C15.7092 2.2046 15.2074 2 14.6847 2H10C8.89543 2 8 2.89543 "
        b'8 4Z" fill="none" stroke="#dddddd" stroke-width="2" stroke-linecap="round" '
        b'stroke-linejoin="round"/><path d="M16 18V20C16 21.1046 15.1046 22 14 22H6C4.89543 '
        b'22 4 21.1046 4 20V9C4 7.89543 4.89543 7 6 7H8" fill="none" stroke="#dddddd" '
        b'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    )
    renderer = Qt.QtSvg.QSvgRenderer(copy_icon_svg)
    pixmap = Qt.QtGui.QPixmap(18, 18)
    pixmap.fill(getattr(Qt.QtCore.Qt, "transparent"))
    painter = Qt.QtGui.QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    copy_token_button.setIcon(Qt.QtGui.QIcon(pixmap))
    copy_token_button.setIconSize(pixmap.size())
    copy_host_button.setIcon(Qt.QtGui.QIcon(pixmap))
    copy_host_button.setIconSize(pixmap.size())

    details.addWidget(status_title, 0, 0, alignment=getattr(Qt.QtCore.Qt, "AlignRight"))
    details.addWidget(status_value, 0, 1, alignment=getattr(Qt.QtCore.Qt, "AlignLeft"))
    details.addWidget(ip_title, 1, 0, alignment=getattr(Qt.QtCore.Qt, "AlignRight"))
    details.addWidget(ip_value, 1, 1, alignment=getattr(Qt.QtCore.Qt, "AlignLeft"))
    details.addWidget(copy_host_button, 1, 2)
    details.addWidget(port_title, 2, 0, alignment=getattr(Qt.QtCore.Qt, "AlignRight"))
    details.addWidget(port_input, 2, 1, alignment=getattr(Qt.QtCore.Qt, "AlignLeft"))
    details.addWidget(token_title, 3, 0, alignment=getattr(Qt.QtCore.Qt, "AlignRight"))
    details.addWidget(token_input, 3, 1)
    details.addWidget(copy_token_button, 3, 2)
    details.setColumnStretch(3, 1)

    connect_button = Qt.QtWidgets.QPushButton("Connect")
    connect_button.setObjectName("connectButton")
    connect_button.setMinimumHeight(24)

    log_output = Qt.QtWidgets.QPlainTextEdit()
    log_output.setObjectName("logOutput")
    log_output.setReadOnly(True)
    log_output.setPlaceholderText("Server activity will appear here")
    log_output.setMinimumHeight(80)

    submitted_code = Qt.QtWidgets.QPlainTextEdit()
    submitted_code.setObjectName("submittedCode")
    submitted_code.setReadOnly(True)
    submitted_code.setPlaceholderText("Submitted Python code will appear here")
    submitted_code.setMinimumHeight(100)
    submitted_code.setStyleSheet("QPlainTextEdit { background-color: #252525; color: #f2f2f2; }")

    layout.addLayout(details)
    layout.addWidget(connect_button)
    layout.addWidget(log_output)
    layout.addWidget(submitted_code)

    components = {
        "status_value": status_value,
        "ip_value": ip_value,
        "copy_host_button": copy_host_button,
        "port_input": port_input,
        "token_input": token_input,
        "copy_token_button": copy_token_button,
        "connect_button": connect_button,
        "log_output": log_output,
        "submitted_code": submitted_code,
    }
    return central, components
