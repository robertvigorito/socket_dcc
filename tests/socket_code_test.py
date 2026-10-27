"""Integration test for sending source through the socket_dcc protocol."""

import socket

import socket_dcc.client as client
from socket_dcc.server import SocketExecutionServer


def test_send_code_to_socket_server(monkeypatch) -> None:
    """Send Python source to a local socket_dcc server and verify receipt.

    Returns:
        None: Asserts the execution response and received-code callback.
    """
    source = 'print("Hello, socket_dcc!")'
    token = "integration-test-token"
    received_code: list[str] = []
    server = SocketExecutionServer(
        auth_token=token,
        code_received_callback=received_code.append,
    )

    with socket.socket() as port_socket:
        port_socket.bind(("127.0.0.1", 0))
        port = port_socket.getsockname()[1]

    monkeypatch.setattr(client, "get_default_settings", lambda: (port, token))
    monkeypatch.setattr(client, "get_default_host", lambda: "127.0.0.1")

    try:
        server.start("127.0.0.1", port)
        response = client.send_code(source)

        assert response.ok
        assert response.output == "Hello, socket_dcc!"
        assert received_code == [source]
    finally:
        server.stop()
