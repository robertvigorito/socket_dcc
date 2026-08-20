"""Utility functions for the GUI."""

import socket

from rich.console import Console

console = Console()


def append_log(log_output, message: str) -> None:
    """Append a message to the log output and print to terminal.

    Args:
        log_output: QPlainTextEdit widget for logging.
        message: Message to append to log.
    """
    if message:
        log_output.appendPlainText(message)
        console.print(message)


def set_status(status_label, message: str) -> None:
    """Update the status label.

    Args:
        status_label: QLabel widget for status display.
        message: Status message to display.
    """
    status_label.setText(message)


def clear_log(log_output) -> None:
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
