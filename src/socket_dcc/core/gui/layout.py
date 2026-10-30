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
    all_interfaces_button: Qt.QtWidgets.QPushButton
    local_host_icon: Qt.QtGui.QIcon
    all_interfaces_icon: Qt.QtGui.QIcon
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
    all_interfaces_button = Qt.QtWidgets.QPushButton()
    all_interfaces_button.setObjectName("allInterfacesButton")
    all_interfaces_button.setCheckable(True)
    all_interfaces_button.setToolTip("Use 0.0.0.0 to listen on all interfaces")
    all_interfaces_button.setAccessibleName("Toggle between local host and all interfaces")
    all_interfaces_button.setFixedSize(30, 30)
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

    local_host_svg = Qt.QtCore.QByteArray(
        b'<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">'
        b'<path d="M24 44C24 44 39 32 39 19C39 10.7157 32.2843 4 24 4C15.7157 4 9 10.7157 '
        b'9 19C9 32 24 44 24 44Z" fill="#707070" stroke="#dddddd" stroke-width="4" '
        b'stroke-linejoin="round"/><path d="M24 25C27.3137 25 30 22.3137 30 19C30 15.6863 '
        b'27.3137 13 24 13C20.6863 13 18 15.6863 18 19C18 22.3137 20.6863 25 24 25Z" '
        b'fill="#333333" stroke="white" stroke-width="4" stroke-linejoin="round"/></svg>'
    )
    all_interfaces_svg = Qt.QtCore.QByteArray(
        b'<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">'
        b'<path d="M33.9 21.676c-.553-.463-1.186-.695-1.9-.695s-1.352.232-1.912.695s-.994 '
        b"1.293-1.303 2.49c-.405 1.553-.608 4.168-.608 7.846c0 3.675.182 6.203.546 "
        b"7.578c.363 1.375.822 2.291 1.377 2.746c.553.457 1.186.684 1.9.684s1.352-.23 "
        b"1.912-.693c.561-.465.994-1.295 1.303-2.492c.405-1.539.608-4.146.608-7.822c0-3.678-"
        b'.182-6.203-.546-7.58c-.363-1.374-.822-2.294-1.377-2.757" fill="#dddddd"/>'
        b'<path d="M32 2C15.432 2 2 15.432 2 32c0 16.568 13.432 30 30 30s30-13.432 30-30C62 '
        b"15.432 48.568 2 32 2zm6.975 42.795C37.308 46.932 34.983 48 32 48c-2.997 0-5.414-"
        b"1.172-7.248-3.516C22.918 42.139 22 37.961 22 31.948c0-5.9 1.009-10.146 3.025-12.74C"
        b"26.692 17.071 29.017 16 32 16s5.315 1.082 6.996 3.25C40.999 21.815 42 26.069 42 "
        b'32.012c0 5.927-1.009 10.189-3.025 12.783z" fill="#dddddd"/></svg>'
    )
    local_host_renderer = Qt.QtSvg.QSvgRenderer(local_host_svg)
    local_host_pixmap = Qt.QtGui.QPixmap(24, 24)
    local_host_pixmap.fill(getattr(Qt.QtCore.Qt, "transparent"))
    local_host_painter = Qt.QtGui.QPainter(local_host_pixmap)
    local_host_renderer.render(local_host_painter)
    local_host_painter.end()
    local_host_icon = Qt.QtGui.QIcon(local_host_pixmap)

    all_interfaces_renderer = Qt.QtSvg.QSvgRenderer(all_interfaces_svg)
    all_interfaces_pixmap = Qt.QtGui.QPixmap(24, 24)
    all_interfaces_pixmap.fill(getattr(Qt.QtCore.Qt, "transparent"))
    all_interfaces_painter = Qt.QtGui.QPainter(all_interfaces_pixmap)
    all_interfaces_renderer.render(all_interfaces_painter)
    all_interfaces_painter.end()
    all_interfaces_icon = Qt.QtGui.QIcon(all_interfaces_pixmap)
    all_interfaces_button.setIcon(local_host_icon)
    all_interfaces_button.setIconSize(Qt.QtCore.QSize(24, 24))

    details_layout.addWidget(status_title, 0, 0, alignment=getattr(Qt.QtCore.Qt, "AlignRight"))
    details_layout.addWidget(status_value, 0, 1, alignment=getattr(Qt.QtCore.Qt, "AlignLeft"))
    details_layout.addWidget(ip_title, 1, 0, alignment=getattr(Qt.QtCore.Qt, "AlignRight"))
    details_layout.addWidget(ip_value, 1, 1, alignment=getattr(Qt.QtCore.Qt, "AlignLeft"))
    details_layout.addWidget(copy_host_button, 1, 2)
    details_layout.addWidget(all_interfaces_button, 1, 3)
    details_layout.addWidget(port_title, 2, 0, alignment=getattr(Qt.QtCore.Qt, "AlignRight"))
    details_layout.addWidget(port_input, 2, 1, alignment=getattr(Qt.QtCore.Qt, "AlignLeft"))
    details_layout.addWidget(token_title, 3, 0, alignment=getattr(Qt.QtCore.Qt, "AlignRight"))
    details_layout.addWidget(token_input, 3, 1)
    details_layout.addWidget(copy_token_button, 3, 2)
    details_layout.setColumnStretch(4, 1)

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
        all_interfaces_button=all_interfaces_button,
        local_host_icon=local_host_icon,
        all_interfaces_icon=all_interfaces_icon,
        port_input=port_input,
        token_input=token_input,
        copy_token_button=copy_token_button,
        connect_button=connect_button,
        log_output=log_output,
        submitted_code=submitted_code,
    )
    return central, components
