"""Client for sending code to the socket execution server."""

import json
import socket

from socket_dcc.defaults import get_default_host, get_default_settings
from socket_dcc.server import ExecutionResponse


def send_code(
    code: str,
    host: str | None = None,
    port: int | None = None,
    token: str | None = None,
    run_path: bool = False,
    wait: bool = False,
) -> ExecutionResponse:
    """Send code to the server for remote execution.

    Args:
        code: Python code to execute on the server.
        host: Server hostname or IP address.
        port: Server port number. Defaults to the shared configured port.
        token: Authentication token. Defaults to the shared configured token.
        run_path: Whether the payload is a file path to execute with runpy.
        wait: Whether to wait for execution output instead of an immediate acknowledgement.

    Returns:
        ExecutionResponse: Contains execution status and output.

    Raises:
        socket.error: If connection to server fails.
    """
    if host is None or port is None or token is None:
        default_port, default_token = get_default_settings()
        host = get_default_host() if host is None else host
        port = default_port if port is None else port
        token = default_token if token is None else token

    assert host is not None
    assert port is not None
    assert token is not None

    with socket.create_connection((host, port), timeout=3) as sock:
        # The connect timeout must not become a response timeout: execution can take
        # longer than three seconds, especially when running a file remotely.
        sock.settimeout(None)
        request: dict[str, str | bool] = {"code": code, "token": token}
        if run_path:
            request["mode"] = "path"
        request["wait"] = wait
        payload = json.dumps(request) + "\n"
        sock.sendall(payload.encode("utf-8"))
        with sock.makefile("r", encoding="utf-8") as stream:
            response = stream.readline()

    if not response:
        return ExecutionResponse(False, "No response from server.")

    try:
        data = json.loads(response)
    except json.JSONDecodeError as exc:
        return ExecutionResponse(False, f"Invalid server response: {exc}")

    return ExecutionResponse(bool(data.get("ok", False)), str(data.get("output", "")))
