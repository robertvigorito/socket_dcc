"""Send inline Python code or source read from a local file."""

from pathlib import Path

import typer

from socket_dcc.cli.common import (
    load_previous_options,
    resolve_connection_options,
    save_previous_options,
    send_to_default_server,
)


def send_code_command(
    source: str | None = typer.Argument(None, help="Python code to send, or a path to a local Python file."),
    previous: bool = typer.Option(False, "--previous", help="Repeat the last code command invocation."),
    silent: bool | None = typer.Option(None, "--silent/--no-silent", help="Suppress all output from this command."),
    host: str | None = typer.Option(None, "--host", help="Override the configured server host."),
    port: int | None = typer.Option(None, "--port", help="Override the configured server port."),
    token: str | None = typer.Option(None, "--token", help="Override the configured authentication token."),
) -> None:
    """Send Python source directly or read it from a local Python file.

    Args:
        source: Python code, or a path to an existing .py file whose contents should be sent.
        previous: Whether to reuse the last source and connection options.
        silent: Whether to suppress sender-side output; defaults to True for a new invocation.
        host: Optional server host override.
        port: Optional server port override.
        token: Optional authentication token override.

    Returns:
        None: Sends the source to the configured socket server.

    Raises:
        typer.BadParameter: If the input names an existing non-Python file or cannot be read.
    """
    if previous and source is not None:
        raise typer.BadParameter("Do not provide code or a file when using --previous.")
    if not previous and source is None:
        raise typer.BadParameter("Provide Python code, a file path, or use --previous.")

    saved = load_previous_options("code") if previous else {}
    selected_source = str(saved.get("source", "")) if previous else source
    if not selected_source:
        raise typer.BadParameter("No previous code invocation is saved.")

    source_path = Path(selected_source).expanduser()
    if source_path.exists():
        if not source_path.is_file() or source_path.suffix.lower() != ".py":
            raise typer.BadParameter(f"Expected a Python source file: {source_path}")
        try:
            code = source_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise typer.BadParameter(f"Could not read Python source file: {source_path}") from exc
        title = f"Sending code from {source_path.name}"
    else:
        code = selected_source
        title = "Sending Python code"

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
    save_previous_options(
        "code",
        {
            "source": selected_source,
            "silent": selected_silent,
            "host": selected_host,
            "port": selected_port,
            "token": selected_token,
        },
    )
    send_to_default_server(
        code,
        title,
        silent=selected_silent,
        host=selected_host,
        port=selected_port,
        token=selected_token,
    )
