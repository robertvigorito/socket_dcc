"""GUI launch command."""

import typer

from socket_dcc.interface import launch


def show(
    host: str | None = typer.Option(None, "--host", envvar="SOCKET_DCC_HOST", help="Server host override."),
    port: int | None = typer.Option(None, "--port", envvar="SOCKET_DCC_PORT", help="Server port override."),
    token: str | None = typer.Option(None, "--token", envvar="SOCKET_DCC_TOKEN", help="Authentication token."),
    connect: bool = typer.Option(True, "--connect/--no-connect", help="Connect to the server when the GUI opens."),
) -> None:
    """Show the socket-dcc GUI.

    Args:
        host: Optional server host override.
        port: Optional server port override.
        token: Optional authentication token override.
        connect: Whether to connect when the GUI opens.

    Returns:
        None: Exits with the GUI event-loop status.
    """
    raise typer.Exit(code=launch(host=host, port=port, token=token, connect=connect))
