"""Typer command for running the socket server without a GUI."""

import typer

from socket_dcc.headless import run_headless_server


def headless(
    host: str | None = typer.Option(
        None,
        "--host",
        help="Bind address (default: configured or resolved local host).",
    ),
    port: int | None = typer.Option(None, "--port", envvar="SOCKET_DCC_PORT", help="Listening port."),
    token: str | None = typer.Option(None, "--token", envvar="SOCKET_DCC_TOKEN", help="Authentication token."),
) -> None:
    """Run the headless socket server until interrupted.

    Args:
        host: Optional server bind address.
        port: Optional server port override.
        token: Optional authentication token override.

    Returns:
        None: Runs the server until it is stopped with Ctrl+C.
    """
    try:
        run_headless_server(host=host, port=port, token=token)
    except (OSError, ValueError) as exc:
        typer.echo(f"Could not start headless server: {exc}", err=True)
        raise typer.Exit(code=1) from exc


def main() -> int:
    """Run the standalone headless server command.

    Returns:
        int: Zero after the server stops cleanly.
    """
    typer.run(headless)
    return 0
