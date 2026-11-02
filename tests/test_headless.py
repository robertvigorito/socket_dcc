"""Tests for the GUI-free headless server runner."""

import errno
import socket
import threading
import time
from unittest.mock import Mock

import socket_dcc.headless as headless_module
from socket_dcc.client import send_code, shutdown_server
from socket_dcc.headless import run_headless_server


def test_headless_server_executes_on_calling_thread_and_stops_cleanly(monkeypatch) -> None:
    """Verify submitted code runs on the runner thread without creating a GUI.

    Args:
        monkeypatch: Pytest fixture used to set the shared host resolver.

    Returns:
        None: Asserts the request response, execution thread, and clean shutdown.
    """
    monkeypatch.setattr(headless_module, "get_default_host", lambda: "127.0.0.1")

    with socket.socket() as port_socket:
        port_socket.bind(("127.0.0.1", 0))
        port = int(port_socket.getsockname()[1])

    token = "headless-test-token"
    stop_event = threading.Event()
    runner_thread_id: list[int] = []
    runner_errors: list[BaseException] = []

    def run_server() -> None:
        runner_thread_id.append(threading.get_ident())
        try:
            run_headless_server(port=port, token=token, stop_event=stop_event)
        except BaseException as exc:
            runner_errors.append(exc)

    server_thread = threading.Thread(target=run_server)
    server_thread.start()
    try:
        deadline = time.monotonic() + 5
        response = None
        while time.monotonic() < deadline:
            try:
                response = send_code(
                    "__import__('threading').get_ident()",
                    host="127.0.0.1",
                    port=port,
                    token=token,
                    wait=True,
                )
                break
            except OSError:
                time.sleep(0.01)

        assert response is not None, "headless server did not start listening"
        assert response.ok
        assert response.output == str(runner_thread_id[0])
    finally:
        stop_event.set()
        server_thread.join(timeout=5)

    assert not server_thread.is_alive(), "headless server did not stop"
    assert not runner_errors


def test_headless_server_falls_back_to_loopback_for_unavailable_default_host(monkeypatch, capsys) -> None:
    """Verify an unavailable automatically resolved address falls back safely.

    Args:
        monkeypatch: Pytest fixture used to replace host resolution and the server.
        capsys: Pytest fixture used to inspect the fallback notice.

    Returns:
        None: Asserts the retry uses loopback and announces the network-address limitation.
    """
    monkeypatch.setattr(headless_module, "get_default_host", lambda: "192.0.2.10")
    server = Mock()
    server.start.side_effect = [OSError(errno.EADDRNOTAVAIL, "Cannot assign requested address"), None]
    monkeypatch.setattr(headless_module, "SocketExecutionServer", Mock(return_value=server))
    stop_event = threading.Event()
    stop_event.set()

    run_headless_server(port=45678, token="headless-token", stop_event=stop_event)

    assert server.start.call_args_list[0].args == ("192.0.2.10", 45678)
    assert server.start.call_args_list[1].args == ("127.0.0.1", 45678)
    assert "Use --host 127.0.0.1 for local clients" in capsys.readouterr().out
    server.stop.assert_called_once_with()


def test_headless_server_can_be_stopped_over_socket(monkeypatch) -> None:
    """Verify the authenticated socket shutdown action stops the headless runner.

    Args:
        monkeypatch: Pytest fixture used to set the shared host resolver.

    Returns:
        None: Asserts shutdown is acknowledged and the runner thread exits.
    """
    monkeypatch.setattr(headless_module, "get_default_host", lambda: "127.0.0.1")
    with socket.socket() as port_socket:
        port_socket.bind(("127.0.0.1", 0))
        port = int(port_socket.getsockname()[1])

    token = "remote-shutdown-token"
    runner_errors: list[BaseException] = []

    def run_server() -> None:
        try:
            run_headless_server(port=port, token=token)
        except BaseException as exc:
            runner_errors.append(exc)

    server_thread = threading.Thread(target=run_server)
    server_thread.start()
    try:
        deadline = time.monotonic() + 5
        response = None
        while time.monotonic() < deadline:
            try:
                response = shutdown_server(host="127.0.0.1", port=port, token=token)
                break
            except OSError:
                time.sleep(0.01)

        assert response is not None, "headless server did not start listening"
        assert response.ok
        assert response.output == "Shutdown requested."
    finally:
        server_thread.join(timeout=5)

    assert not server_thread.is_alive(), "headless server did not stop after shutdown request"
    assert not runner_errors
