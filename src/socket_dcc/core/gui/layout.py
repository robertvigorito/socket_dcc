"""Compact connection panel layout for the main window."""

from dataclasses import dataclass
from typing import Any

import Qt


class HoverIconButton(Qt.QtWidgets.QPushButton):
    """Push button that swaps its icon while the pointer is over it."""

    _normal_icon: Qt.QtGui.QIcon
    _hover_icon: Qt.QtGui.QIcon

    def enterEvent(self, event: Any) -> None:
        """Display the hover icon when the pointer enters the button.

        Args:
            event: Qt pointer-enter event.

        Returns:
            None: Updates the icon and forwards the event.
        """
        self.setIcon(self._hover_icon)
        super().enterEvent(event)

    def leaveEvent(self, event: Any) -> None:
        """Restore the normal icon when the pointer leaves the button.

        Args:
            event: Qt pointer-leave event.

        Returns:
            None: Updates the icon and forwards the event.
        """
        self.setIcon(self._normal_icon)
        super().leaveEvent(event)


@dataclass
class CentralWidgetComponents:
    """Interactive widgets exposed by the central connection panel."""

    status_value: Qt.QtWidgets.QLabel
    ip_value: Qt.QtWidgets.QLabel
    copy_host_button: HoverIconButton
    port_input: Qt.QtWidgets.QSpinBox
    token_input: Qt.QtWidgets.QLineEdit
    copy_token_button: HoverIconButton
    connect_button: Qt.QtWidgets.QPushButton
    log_output: Qt.QtWidgets.QPlainTextEdit
    submitted_code: Qt.QtWidgets.QPlainTextEdit


def create_central_widget(ip_address: str, port: int) -> tuple[Qt.QtWidgets.QWidget, CentralWidgetComponents]:
    """Create the connection panel and return its interactive components.

    Args:
        ip_address: Local address displayed in the connection panel.
        port: Default port displayed in the connection panel.

    Returns:
        tuple[Qt.QtWidgets.QWidget, CentralWidgetComponents]: Central widget and its interactive components.
    """
    central = Qt.QtWidgets.QWidget()
    layout = Qt.QtWidgets.QVBoxLayout(central)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(5)

    details_layout = Qt.QtWidgets.QGridLayout()
    details_layout.setContentsMargins(0, 0, 0, 0)
    details_layout.setHorizontalSpacing(2)
    details_layout.setVerticalSpacing(4)

    status_title = Qt.QtWidgets.QLabel("Status:")
    status_value = Qt.QtWidgets.QLabel("Idle")
    status_value.setObjectName("statusValue")
    ip_title = Qt.QtWidgets.QLabel("IP:")
    ip_value = Qt.QtWidgets.QLabel(ip_address)
    copy_host_button = HoverIconButton()
    copy_host_button.setObjectName("copyHostButton")
    copy_host_button.setAccessibleName("Copy host")
    copy_host_button.setToolTip("Copy the server host to the clipboard")
    copy_host_button.setFixedSize(30, 30)
    port_title = Qt.QtWidgets.QLabel("Port:")
    port_input = Qt.QtWidgets.QSpinBox()
    port_input.setObjectName("portInput")
    port_input.setRange(1, 65535)
    port_input.setValue(port)
    port_input.setFixedWidth(64)
    token_title = Qt.QtWidgets.QLabel("Token:")
    token_input = Qt.QtWidgets.QLineEdit()
    token_input.setObjectName("tokenInput")
    token_input.setPlaceholderText("Authentication token")
    token_input.setMinimumWidth(320)
    token_input.setFixedHeight(30)
    copy_token_button = HoverIconButton()
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
    hover_icon_svg = Qt.QtCore.QByteArray(copy_icon_svg)
    hover_icon_svg.replace(b"#dddddd", b"#ffb13b")

    icons = []
    for svg in (copy_icon_svg, hover_icon_svg):
        renderer = Qt.QtSvg.QSvgRenderer(svg)
        pixmap = Qt.QtGui.QPixmap(18, 18)
        pixmap.fill(getattr(Qt.QtCore.Qt, "transparent"))
        painter = Qt.QtGui.QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        icons.append(Qt.QtGui.QIcon(pixmap))
    normal_icon, hover_icon = icons
    for button in (copy_token_button, copy_host_button):
        button._normal_icon = normal_icon
        button._hover_icon = hover_icon
        button.setIcon(normal_icon)
        button.setIconSize(Qt.QtCore.QSize(18, 18))

    details_layout.addWidget(status_title, 0, 0, alignment=getattr(Qt.QtCore.Qt, "AlignRight"))
    details_layout.addWidget(status_value, 0, 1, alignment=getattr(Qt.QtCore.Qt, "AlignLeft"))
    details_layout.addWidget(ip_title, 1, 0, alignment=getattr(Qt.QtCore.Qt, "AlignRight"))
    details_layout.addWidget(ip_value, 1, 1, alignment=getattr(Qt.QtCore.Qt, "AlignLeft"))
    details_layout.addWidget(copy_host_button, 1, 2)
    details_layout.addWidget(port_title, 2, 0, alignment=getattr(Qt.QtCore.Qt, "AlignRight"))
    details_layout.addWidget(port_input, 2, 1, alignment=getattr(Qt.QtCore.Qt, "AlignLeft"))
    details_layout.addWidget(token_title, 3, 0, alignment=getattr(Qt.QtCore.Qt, "AlignRight"))
    details_layout.addWidget(token_input, 3, 1)
    details_layout.addWidget(copy_token_button, 3, 2)
    details_layout.setColumnStretch(3, 1)

    connect_button = Qt.QtWidgets.QPushButton("Connect")
    connect_button.setMinimumHeight(24)

    log_output = Qt.QtWidgets.QPlainTextEdit()
    log_output.setReadOnly(True)
    log_output.setPlaceholderText("Server activity will appear here")
    log_output.setMinimumHeight(80)

    submitted_code = Qt.QtWidgets.QPlainTextEdit()
    submitted_code.setReadOnly(True)
    submitted_code.setPlaceholderText("Submitted Python code will appear here")
    submitted_code.setMinimumHeight(100)
    submitted_code.setStyleSheet("QPlainTextEdit { background-color: #252525; color: #f2f2f2; }")

    output_splitter = Qt.QtWidgets.QSplitter(getattr(Qt.QtCore.Qt, "Vertical"))
    output_splitter.addWidget(log_output)
    output_splitter.addWidget(submitted_code)
    output_splitter.setStretchFactor(0, 1)
    output_splitter.setStretchFactor(1, 1)

    layout.addLayout(details_layout)
    layout.addWidget(connect_button)
    layout.addWidget(output_splitter, stretch=1)

    components = CentralWidgetComponents(
        status_value=status_value,
        ip_value=ip_value,
        copy_host_button=copy_host_button,
        port_input=port_input,
        token_input=token_input,
        copy_token_button=copy_token_button,
        connect_button=connect_button,
        log_output=log_output,
        submitted_code=submitted_code,
    )
    return central, components
