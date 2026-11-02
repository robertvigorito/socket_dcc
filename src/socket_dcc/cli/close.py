"""Request a clean shutdown of the socket server."""

import typer

from socket_dcc.cli.common import resolve_connection_options
from socket_dcc.client import shutdown_server


def close_server(
    host: str | None = typer.Option(None, "--host", help="Override the configured server host."),
    port: int | None = typer.Option(None, "--port", help="Override the configured server port."),
    token: str | None = typer.Option(None, "--token", help="Override the configured authentication token."),
) -> None:
    """Send the authenticated close action to a running headless server.

    Args:
        host: Optional server host override.
        port: Optional server port override.
        token: Optional authentication token override.

    Returns:
        None: Reports whether the server accepted the shutdown request.
    """
    host, port, token = resolve_connection_options(host, port, token)
    try:
        response = shutdown_server(host=host, port=port, token=token)
    except OSError as exc:
        typer.echo(f"Could not connect to socket-dcc at {host}:{port}: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if not response.ok:
        typer.echo(response.output, err=True)
        raise typer.Exit(code=1)
    typer.echo(response.output)


def main() -> int:
    """Run the standalone close command.

    Returns:
        int: Zero after the shutdown request is accepted.
    """
    typer.run(close_server)
    return 0
