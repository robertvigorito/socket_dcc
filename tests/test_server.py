"""Tests for socket execution behavior."""

from pathlib import Path

from socket_dcc.server import ExecutionResponse, SocketExecutionServer, _normalize_traceback_paths


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


def test_execution_error_omits_failed_expression_compile_context() -> None:
    """Show the actual execution error without the attempted expression compile error.

    Returns:
        None: Asserts only the useful exception traceback is included.
    """
    server = SocketExecutionServer()

    response = server.execute("import os\nraise NotImplementedError('Panel registration unavailable')")

    assert not response.ok
    assert response.output.count("Traceback (most recent call last):") == 1
    assert "SyntaxError" not in response.output
    assert "NotImplementedError: Panel registration unavailable" in response.output


def test_traceback_wsl_unc_paths_use_forward_slashes() -> None:
    """Normalize Windows-rendered WSL paths to readable forward-slash paths.

    Returns:
        None: Asserts the UNC prefix and path components use forward slashes.
    """
    wsl_path = r"\\wsl.localhost\Ubuntu\home\robert\script.py"
    output = f"  File {wsl_path!r}, line 7, in <module>"

    normalized = _normalize_traceback_paths(output)

    assert "File '//wsl.localhost/Ubuntu/home/robert/script.py', line 7" in normalized


def test_resolve_run_path_converts_mnt_path_on_windows(monkeypatch) -> None:
    """Verify /mnt drive paths become Windows drive paths outside WSL.

    Args:
        monkeypatch: Pytest fixture used to fake the platform.

    Returns:
        None: Asserts the converted path.
    """
    from socket_dcc import server

    monkeypatch.setattr(server.os, "name", "nt")
    monkeypatch.setattr(server, "_is_wsl", lambda: False)

    assert server._resolve_run_path("/mnt/c/proj/a.py") == "C:/proj/a.py"


def test_resolve_run_path_unchanged_in_wsl(monkeypatch) -> None:
    """Verify paths are untouched when the server runs inside WSL.

    Args:
        monkeypatch: Pytest fixture used to fake the platform.

    Returns:
        None: Asserts the path is unchanged.
    """
    from socket_dcc import server

    monkeypatch.setattr(server.os, "name", "nt")
    monkeypatch.setattr(server, "_is_wsl", lambda: True)

    assert server._resolve_run_path("/mnt/c/proj/a.py") == "/mnt/c/proj/a.py"
