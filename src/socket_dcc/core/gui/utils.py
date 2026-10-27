"""Utility functions for the GUI."""

import socket
from typing import Any

import Qt
from rich.console import Console
from rich.style import Style
from rich.terminal_theme import DEFAULT_TERMINAL_THEME

console = Console()


def append_log(log_output: Any, message: str) -> None:
    """Append a message to the log output and print to terminal.

    Args:
        log_output: QPlainTextEdit widget for logging.
        message: Message to append to log.

    Returns:
        None: Appends styled text to the log and prints it to the terminal.
    """
    if message:
        text = console.render_str(message)
        cursor = log_output.textCursor()
        cursor.movePosition(getattr(Qt.QtGui.QTextCursor, "End"))
        if not log_output.document().isEmpty():
            cursor.insertBlock()

        for segment in text.render(console):
            char_format = _char_format(segment.style)
            cursor.insertText(segment.text, char_format)

        log_output.setTextCursor(cursor)
        log_output.ensureCursorVisible()
        console.print(message)


def _char_format(style: Style | None) -> Qt.QtGui.QTextCharFormat:
    """Convert a Rich style to a Qt character format.

    Args:
        style: Rich style for a text segment.

    Returns:
        Qt.QtGui.QTextCharFormat: Qt formatting matching the Rich foreground/background and emphasis.
    """
    char_format = Qt.QtGui.QTextCharFormat()
    if style is None:
        return char_format

    if style.color is not None:
        color = style.color.get_truecolor(DEFAULT_TERMINAL_THEME)
        char_format.setForeground(Qt.QtGui.QColor(color.red, color.green, color.blue))
    if style.bgcolor is not None:
        color = style.bgcolor.get_truecolor(DEFAULT_TERMINAL_THEME)
        char_format.setBackground(Qt.QtGui.QColor(color.red, color.green, color.blue))
    if style.bold:
        char_format.setFontWeight(getattr(Qt.QtGui.QFont, "Bold"))
    if style.italic:
        char_format.setFontItalic(True)
    if style.underline:
        char_format.setFontUnderline(True)
    if style.strike:
        char_format.setFontStrikeOut(True)
    return char_format


def set_status(status_label: Any, message: str) -> None:
    """Update the status label.

    Args:
        status_label: QLabel widget for status display.
        message: Status message to display.
    """
    status_label.setText(message)


def clear_log(log_output: Any) -> None:
    """Clear the log output.

    Args:
        log_output: QPlainTextEdit widget to clear.
    """
    log_output.clear()
    console.print("[yellow]Log cleared[/yellow]")


def get_host_info() -> str:
    """Get and return localhost information.

    Returns:
        Formatted string with hostname, IP address, and localhost.

    Raises:
        socket.error: If unable to retrieve host information.
    """
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    localhost = socket.gethostbyname("localhost")
    return f"Hostname: {hostname}\nLocal IP: {ip_address}\nLocalhost: {localhost}"
