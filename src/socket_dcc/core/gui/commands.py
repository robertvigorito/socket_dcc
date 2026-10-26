"""Command sending operations for the GUI."""

import threading
from typing import Any

from rich.console import Console

from socket_dcc.client import send_code

console = Console()


def send_command(
    command_input: Any,
    server: Any,
    host_input: Any,
    port_input: Any,
    token_input: Any,
    append_log_callback: Any,
) -> None:
    """Send the code from the command input to the server for execution.

    Args:
        command_input: QPlainTextEdit with Python code.
        server: SocketExecutionServer instance.
        host_input: QLineEdit with host address.
        port_input: QSpinBox with port number.
        token_input: QLineEdit with authentication token.
        append_log_callback: Callback to append to log.
    """
    code = command_input.toPlainText().strip()
    if not code:
        append_log_callback("No command to send.")
        return

    if not server.is_running:
        error_msg = "[red]✗ Server is not running[/red]. Please click 'Start Server' first."
        append_log_callback(error_msg)
        console.print(error_msg)
        return

    console.print("[cyan]>>> Sending code to server...[/cyan]")
    host = host_input.text().strip()
    port = int(port_input.value())
    token = token_input.text()
    threading.Thread(
        target=_send_command_impl,
        args=(host, port, token, code, append_log_callback),
        daemon=True,
    ).start()


def _send_command_impl(host: str, port: int, token: str, code: str, append_log_callback: Any) -> None:
    """Send code to the server and handle the response.

    Args:
        host: Server hostname.
        port: Server port.
        token: Authentication token.
        code: Python code to execute.
        append_log_callback: Callback to append to log.
    """
    try:
        response = send_code(host, port, token, code)
    except OSError as exc:
        error_msg = (
            f"[red]✗ Connection Failed[/red]: Could not connect to server at {host}:{port}\n"
            f"Make sure the server is running and the host/port are correct.\n"
            f"Details: {exc}"
        )
        append_log_callback(error_msg)
        return

    if response.ok:
        if response.output:
            append_log_callback(response.output)
        else:
            append_log_callback("Command executed successfully.")
    else:
        error_msg = response.output or "Command failed"
        append_log_callback(f"[bold red]ERROR[/bold red]: {error_msg}")
