"""Generic server connectivity test command."""

from socket_dcc.cli.common import send_to_default_server


def test() -> None:
    """Send a generic print statement to the configured server.

    Returns:
        None: Prints the server output or exits if the request fails.
    """
    send_to_default_server('print("helloworld")', "Testing socket-dcc", wait=True)
