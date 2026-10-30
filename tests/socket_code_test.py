"""Integration test for sending source through the socket_dcc protocol."""

import socket
import threading
import time
from pathlib import Path

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
        response = client.send_code(source, wait=True)

        assert response.ok
        assert response.output == "Hello, socket_dcc!"
        assert received_code == [source]
    finally:
        server.stop()


def test_send_code_waits_for_long_running_execution(monkeypatch) -> None:
    """Verify response waiting is not limited by the connection timeout.

    Args:
        monkeypatch: Pytest fixture used to configure the local server connection.

    Returns:
        None: Asserts the eventual response is received after more than three seconds.
    """
    token = "long-execution-test-token"
    server = SocketExecutionServer(auth_token=token)

    with socket.socket() as port_socket:
        port_socket.bind(("127.0.0.1", 0))
        port = port_socket.getsockname()[1]

    monkeypatch.setattr(client, "get_default_settings", lambda: (port, token))
    monkeypatch.setattr(client, "get_default_host", lambda: "127.0.0.1")

    try:
        server.start("127.0.0.1", port)
        response = client.send_code("import time; time.sleep(3.1); print('finished')", wait=True)

        assert response.ok
        assert response.output == "finished"
    finally:
        server.stop()


def test_send_path_mode_executes_file_with_runpy(monkeypatch, tmp_path: Path) -> None:
    """Verify path-mode requests explicitly reach server-side runpy execution.

    Args:
        monkeypatch: Pytest fixture used to configure the local server connection.
        tmp_path: Temporary directory used to create an executable Python file.

    Returns:
        None: Asserts the path request executes the file and captures its output.
    """
    script = tmp_path / "path_mode.py"
    script.write_text("print('runpy path mode')\n", encoding="utf-8")
    token = "path-mode-test-token"
    server = SocketExecutionServer(auth_token=token)

    with socket.socket() as port_socket:
        port_socket.bind(("127.0.0.1", 0))
        port = port_socket.getsockname()[1]

    monkeypatch.setattr(client, "get_default_settings", lambda: (port, token))
    monkeypatch.setattr(client, "get_default_host", lambda: "127.0.0.1")

    try:
        server.start("127.0.0.1", port)
        response = client.send_code(str(script), run_path=True, wait=True)

        assert response.ok
        assert response.output == "runpy path mode"
    finally:
        server.stop()


def test_send_code_returns_before_remote_execution_finishes(monkeypatch) -> None:
    """Verify default sends return immediately while the server finishes in background.

    Args:
        monkeypatch: Pytest fixture used to configure the local server connection.

    Returns:
        None: Asserts the acknowledgement arrives before execution output is logged.
    """
    token = "async-execution-test-token"
    execution_finished = threading.Event()
    logged_output: list[str] = []

    def log_output(message: str) -> None:
        logged_output.append(message)
        execution_finished.set()

    server = SocketExecutionServer(auth_token=token, log_callback=log_output)

    with socket.socket() as port_socket:
        port_socket.bind(("127.0.0.1", 0))
        port = port_socket.getsockname()[1]

    monkeypatch.setattr(client, "get_default_settings", lambda: (port, token))
    monkeypatch.setattr(client, "get_default_host", lambda: "127.0.0.1")

    try:
        server.start("127.0.0.1", port)
        started = time.monotonic()
        response = client.send_code("import time; time.sleep(1.2); print('finished')")
        elapsed = time.monotonic() - started

        assert response.ok
        assert response.output == "Execution started."
        assert elapsed < 1.0
        assert not execution_finished.is_set()
        assert execution_finished.wait(timeout=3)
        assert logged_output == ["finished"]
    finally:
        server.stop()
