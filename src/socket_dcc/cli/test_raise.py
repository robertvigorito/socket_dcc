"""Intentional server exception test command."""

from socket_dcc.cli.common import send_to_default_server


def test_raise() -> None:
    """Verify the server returns a deliberate Python exception.

    Returns:
        None: Reports whether the expected exception was returned.
    """
    send_to_default_server(
        'raise ValueError("Test exception")',
        "Testing socket-dcc error handling",
        expected_error="ValueError: Test exception",
        wait=True,
    )
