"""Client for sending code to the socket execution server."""

import json
import socket

from .server import ExecutionResponse


def send_code(host: str, port: int, token: str, code: str) -> ExecutionResponse:
    """Send code to the server for remote execution.

    Args:
        host: Server hostname or IP address.
        port: Server port number.
        token: Authentication token for the server.
        code: Python code to execute on the server.

    Returns:
        ExecutionResponse: Contains execution status and output.

    Raises:
        socket.error: If connection to server fails.
    """
    with socket.create_connection((host, port), timeout=3) as sock:
        payload = json.dumps({"code": code, "token": token}) + "\n"
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
