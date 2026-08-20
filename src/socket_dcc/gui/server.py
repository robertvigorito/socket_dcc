"""Server control operations for the GUI."""

from __future__ import annotations

from rich.console import Console

console = Console()


def start_server(
    server,
    host_input,
    port_input,
    auto_stop_checkbox,
    auto_stop_timeout,
    auto_stop_timer,
    start_button,
    stop_button,
    append_log_callback,
) -> None:
    """Start the execution server on configured host and port.

    Args:
        server: SocketExecutionServer instance.
        host_input: QLineEdit with host address.
        port_input: QSpinBox with port number.
        auto_stop_checkbox: QCheckBox for auto-stop.
        auto_stop_timeout: QDoubleSpinBox with timeout.
        auto_stop_timer: QTimer for auto-stop.
        start_button: QPushButton for start.
        stop_button: QPushButton for stop.
        append_log_callback: Callback to append to log.
    """
    try:
        server.start(host_input.text().strip(), int(port_input.value()))
        start_button.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold;"
        )
        start_button.setDown(True)
        stop_button.setStyleSheet("")
        stop_button.setDown(False)
        console.print("[green]✓ Server started successfully[/green]")

        # Start auto-stop timer if enabled
        if auto_stop_checkbox.isChecked():
            timeout_ms = int(auto_stop_timeout.value() * 60 * 1000)
            append_log_callback(
                f"[cyan]Auto-stop enabled: server will stop after {auto_stop_timeout.value():.1f} minutes[/cyan]"
            )
            auto_stop_timer.start(timeout_ms)
    except OSError as exc:
        error_msg = (
            f"[red]✗ Failed to start server[/red]:\n"
            f"  Host: {host_input.text().strip()}\n"
            f"  Port: {port_input.value()}\n"
            f"  Error: {exc}\n\n"
            f"Make sure the port is not already in use."
        )
        append_log_callback(error_msg)
        console.print(error_msg)


def stop_server(server, auto_stop_timer, stop_button, start_button) -> None:
    """Stop the execution server.

    Args:
        server: SocketExecutionServer instance.
        auto_stop_timer: QTimer for auto-stop.
        stop_button: QPushButton for stop.
        start_button: QPushButton for start.
    """
    auto_stop_timer.stop()
    server.stop()
    stop_button.setStyleSheet(
        "background-color: #FF9800; color: white; font-weight: bold;"
    )
    stop_button.setDown(True)
    start_button.setStyleSheet("")
    start_button.setDown(False)
    console.print("[yellow]⊘ Server stopped[/yellow]")
