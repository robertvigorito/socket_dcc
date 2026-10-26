"""Tests for socket execution behavior."""

from pathlib import Path

from socket_dcc.server import ExecutionResponse, SocketExecutionServer


def test_execute_code_snippet() -> None:
    """Execute a code snippet and capture its printed output.

    Returns:
        None: This test asserts the returned response and captured output.
    """
    server = SocketExecutionServer()

    response = server.execute('print("hello")')

    assert response == ExecutionResponse(True, "hello")


def test_execute_python_file(tmp_path: Path) -> None:
    """Execute a Python file by path and capture its printed output.

    Args:
        tmp_path: Pytest fixture providing an isolated temporary directory.

    Returns:
        None: This test asserts the returned response.
    """
    script = tmp_path / "example.py"
    script.write_text('print("file executed")\n', encoding="utf-8")
    server = SocketExecutionServer()

    response = server.execute(str(script))

    assert response == ExecutionResponse(True, "file executed")
