"""Tests for CLI commands that communicate with the running interface."""

from unittest.mock import Mock

from typer.testing import CliRunner

import socket_dcc.cli as cli
from socket_dcc.server import ExecutionResponse


def test_raise_connects_to_interface_and_accepts_expected_remote_error(monkeypatch) -> None:
    """Verify test-raise sends its snippet to the selected interface and reports expected failure.

    Args:
        monkeypatch: Pytest fixture used to isolate connection defaults and socket sending.

    Returns:
        None: Asserts the connection details and successful test command result.
    """
    send_code = Mock(return_value=ExecutionResponse(False, "Traceback...\nValueError: Test exception"))
    monkeypatch.setattr(cli, "send_code", send_code)
    monkeypatch.setattr(cli, "get_default_settings", lambda: (54322, "default-token"))
    runner = CliRunner()

    result = runner.invoke(
        cli.app,
        ["test-raise", "--host", "127.0.0.1", "--port", "45678", "--token", "test-token"],
    )

    assert result.exit_code == 0, result.output
    send_code.assert_called_once_with(
        'raise ValueError("Test exception")',
        host="127.0.0.1",
        port=45678,
        token="test-token",
    )
    assert "expected error" in result.output


def test_root_passes_connection_options_to_gui(monkeypatch) -> None:
    """Verify root GUI options are forwarded to the interface.

    Args:
        monkeypatch: Pytest fixture used to replace the GUI entry point.

    Returns:
        None: Asserts the GUI receives the selected connection settings.
    """
    run_gui = Mock(return_value=0)
    monkeypatch.setattr(cli, "run_gui", run_gui)
    runner = CliRunner()

    result = runner.invoke(cli.app, ["--host", "192.168.1.20", "--port", "45678", "--token", "cli-token"])

    assert result.exit_code == 0, result.output
    run_gui.assert_called_once_with(host="192.168.1.20", port=45678, token="cli-token")
