"""Run a Python file on the socket server using runpy."""

from pathlib import Path

import typer

from socket_dcc.cli.common import (
    load_previous_options,
    resolve_connection_options,
    save_previous_options,
    send_to_default_server,
)


def run_path(
    file: Path | None = typer.Argument(None, help="Python file to run on the socket server."),
    previous: bool = typer.Option(False, "--previous", help="Repeat the last path command invocation."),
    silent: bool | None = typer.Option(None, "--silent/--no-silent", help="Suppress all output from this command."),
    host: str | None = typer.Option(None, "--host", help="Override the configured server host."),
    port: int | None = typer.Option(None, "--port", help="Override the configured server port."),
    token: str | None = typer.Option(None, "--token", help="Override the configured authentication token."),
) -> None:
    """Send a Python file path for server-side runpy execution.

    Args:
        file: Python file accessible to the server process.
        previous: Whether to reuse the last path and connection options.
        silent: Whether to suppress sender-side output; defaults to True for a new invocation.
        host: Optional server host override.
        port: Optional server port override.
        token: Optional authentication token override.

    Returns:
        None: Prints the server output or exits if execution fails.

    Raises:
        typer.BadParameter: If the path is not an existing Python file.
    """
    if previous and file is not None:
        raise typer.BadParameter("Do not provide a file when using --previous.")
    if not previous and file is None:
        raise typer.BadParameter("Provide a Python file or use --previous.")

    saved = load_previous_options("path") if previous else {}
    selected_file = str(saved.get("file", "")) if previous else str(file)
    if not selected_file:
        raise typer.BadParameter("No previous path invocation is saved.")
    file_path = Path(selected_file).expanduser().resolve()
    if not file_path.is_file() or file_path.suffix.lower() != ".py":
        raise typer.BadParameter(f"Expected an existing Python file: {file_path}")

    selected_silent = silent if silent is not None else bool(saved.get("silent", True)) if previous else True
    selected_host: str | None = host
    selected_port: int | None = port
    selected_token: str | None = token
    if previous:
        saved_host = saved.get("host")
        saved_port = saved.get("port")
        saved_token = saved.get("token")
        if selected_host is None and isinstance(saved_host, str):
            selected_host = saved_host
        if selected_port is None and isinstance(saved_port, int):
            selected_port = saved_port
        if selected_token is None and isinstance(saved_token, str):
            selected_token = saved_token
    selected_host, selected_port, selected_token = resolve_connection_options(
        selected_host,
        selected_port,
        selected_token,
    )
    options: dict[str, str | int | bool | None] = {
        "file": str(file_path),
        "silent": selected_silent,
        "host": selected_host,
        "port": selected_port,
        "token": selected_token,
    }
    save_previous_options("path", options)
    send_to_default_server(
        str(file_path),
        f"Running {file_path.name} with runpy",
        silent=selected_silent,
        host=selected_host,
        port=selected_port,
        token=selected_token,
    )
