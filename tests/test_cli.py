"""Tests for the modular socket-dcc CLI commands."""

from importlib import import_module
from pathlib import Path
from unittest.mock import Mock

from typer.testing import CliRunner

from socket_dcc.cli import common
from socket_dcc.cli import initiate as cli
from socket_dcc.server import ExecutionResponse


def test_generic_test_uses_default_connection_settings(monkeypatch) -> None:
    """Verify the test command sends its generic snippet using shared defaults.

    Args:
        monkeypatch: Pytest fixture used to replace configuration and network calls.

    Returns:
        None: Asserts the default connection settings and test snippet were used.
    """
    send_code = Mock(return_value=ExecutionResponse(True, "helloworld"))
    monkeypatch.setattr(common, "send_code", send_code)
    monkeypatch.setattr(common, "get_default_settings", lambda: (54322, "default-token"))
    monkeypatch.setattr(common, "get_default_host", lambda: "127.0.0.1")

    result = CliRunner().invoke(cli.app, ["test"])

    assert result.exit_code == 0, result.output
    send_code.assert_called_once_with(
        'print("helloworld")',
        host="127.0.0.1",
        port=54322,
        token="default-token",
    )


def test_test_raise_accepts_expected_remote_exception(monkeypatch) -> None:
    """Verify test-raise succeeds only when the expected server exception is returned.

    Args:
        monkeypatch: Pytest fixture used to replace configuration and network calls.

    Returns:
        None: Asserts the exception test code and expected error are handled.
    """
    send_code = Mock(return_value=ExecutionResponse(False, "Traceback...\nValueError: Test exception"))
    monkeypatch.setattr(common, "send_code", send_code)
    monkeypatch.setattr(common, "get_default_settings", lambda: (54322, "default-token"))
    monkeypatch.setattr(common, "get_default_host", lambda: "127.0.0.1")

    result = CliRunner().invoke(cli.app, ["test-raise"])

    assert result.exit_code == 0, result.output
    assert 'raise ValueError("Test exception")' in send_code.call_args.args
    assert "expected error" in result.output


def test_path_sends_resolved_python_path_for_runpy(monkeypatch, tmp_path: Path) -> None:
    """Verify path sends a validated absolute Python path for server-side runpy.

    Args:
        monkeypatch: Pytest fixture used to replace configuration and network calls.
        tmp_path: Temporary directory used to create the Python file.

    Returns:
        None: Asserts the resolved file path and defaults are sent to the server.
    """
    python_file = tmp_path / "example.py"
    python_file.write_text('print("from file")\n', encoding="utf-8")
    monkeypatch.setenv("SOCKET_DCC_STATE_DIR", str(tmp_path / "state"))
    send_code = Mock(return_value=ExecutionResponse(True, "from file"))
    monkeypatch.setattr(common, "send_code", send_code)
    monkeypatch.setattr(common, "get_default_settings", lambda: (54322, "default-token"))
    monkeypatch.setattr(common, "get_default_host", lambda: "127.0.0.1")

    result = CliRunner().invoke(cli.app, ["path", str(python_file)])

    assert result.exit_code == 0, result.output
    send_code.assert_called_once_with(
        str(python_file.resolve()),
        host="127.0.0.1",
        port=54322,
        token="default-token",
    )


def test_path_silent_suppresses_sender_and_server_output(monkeypatch, tmp_path: Path) -> None:
    """Verify --silent suppresses CLI output while still running the file.

    Args:
        monkeypatch: Pytest fixture used to replace configuration and network calls.
        tmp_path: Temporary directory used to create the Python file.

    Returns:
        None: Asserts the request succeeds without printing sender-side output.
    """
    python_file = tmp_path / "quiet.py"
    python_file.write_text('print("quiet output")\n', encoding="utf-8")
    monkeypatch.setenv("SOCKET_DCC_STATE_DIR", str(tmp_path / "state"))
    send_code = Mock(return_value=ExecutionResponse(True, "quiet output"))
    monkeypatch.setattr(common, "send_code", send_code)
    monkeypatch.setattr(common, "get_default_settings", lambda: (54322, "default-token"))
    monkeypatch.setattr(common, "get_default_host", lambda: "127.0.0.1")

    result = CliRunner().invoke(cli.app, ["path", str(python_file), "--silent"])

    assert result.exit_code == 0, result.output
    assert result.output == ""
    send_code.assert_called_once_with(
        str(python_file.resolve()),
        host="127.0.0.1",
        port=54322,
        token="default-token",
    )


def test_silent_connection_failure_reports_error(monkeypatch, tmp_path: Path) -> None:
    """Verify silent mode reports a connection failure and exits unsuccessfully.

    Args:
        monkeypatch: Pytest fixture used to replace defaults and the socket sender.
        tmp_path: Temporary directory used to isolate previous-invocation state.

    Returns:
        None: Asserts the failure is visible despite --silent.
    """
    python_file = tmp_path / "unreachable.py"
    python_file.write_text("pass\n", encoding="utf-8")
    monkeypatch.setenv("SOCKET_DCC_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr(common, "get_default_settings", lambda: (54322, "default-token"))
    monkeypatch.setattr(common, "get_default_host", lambda: "127.0.0.1")
    monkeypatch.setattr(common, "send_code", Mock(side_effect=ConnectionRefusedError))

    result = CliRunner().invoke(cli.app, ["path", str(python_file), "--silent"])

    assert result.exit_code == 1
    assert "Could not connect to socket-dcc at 127.0.0.1:54322" in result.output


def test_code_command_sends_inline_python_code(monkeypatch, tmp_path: Path) -> None:
    """Verify code sends literal source with custom connection values and output enabled.

    Args:
        monkeypatch: Pytest fixture used to replace defaults and the socket sender.
        tmp_path: Pytest fixture used to isolate previous-invocation state.

    Returns:
        None: Asserts the literal source was sent to the server.
    """
    send_code = Mock(return_value=ExecutionResponse(True, "2"))
    monkeypatch.setattr(common, "send_code", send_code)
    monkeypatch.setattr(common, "get_default_settings", lambda: (54322, "default-token"))
    monkeypatch.setattr(common, "get_default_host", lambda: "127.0.0.1")
    monkeypatch.setenv("SOCKET_DCC_STATE_DIR", str(tmp_path / "state"))
    source = "print(1 + 1)"

    result = CliRunner().invoke(
        cli.app,
        [
            "code",
            source,
            "--no-silent",
            "--host",
            "192.168.1.50",
            "--port",
            "45678",
            "--token",
            "custom-token",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Sending Python code" in result.output
    send_code.assert_called_once_with(source, host="192.168.1.50", port=45678, token="custom-token")


def test_code_command_reads_python_file_contents(monkeypatch, tmp_path: Path) -> None:
    """Verify a local Python file is read and its source is sent as code.

    Args:
        monkeypatch: Pytest fixture used to replace defaults and the socket sender.
        tmp_path: Pytest fixture used to create an isolated Python file.

    Returns:
        None: Asserts the file contents, not its path, are sent to the server.
    """
    python_file = tmp_path / "example.py"
    source = "print('read locally')\n"
    python_file.write_text(source, encoding="utf-8")
    monkeypatch.setenv("SOCKET_DCC_STATE_DIR", str(tmp_path / "state"))
    send_code = Mock(return_value=ExecutionResponse(True, "read locally"))
    monkeypatch.setattr(common, "send_code", send_code)
    monkeypatch.setattr(common, "get_default_settings", lambda: (54322, "default-token"))
    monkeypatch.setattr(common, "get_default_host", lambda: "127.0.0.1")

    result = CliRunner().invoke(cli.app, ["code", str(python_file)])

    assert result.exit_code == 0, result.output
    send_code.assert_called_once_with(source, host="127.0.0.1", port=54322, token="default-token")


def test_code_previous_reuses_source_and_connection_options(monkeypatch, tmp_path: Path) -> None:
    """Verify --previous reuses the saved code and explicit server options.

    Args:
        monkeypatch: Pytest fixture used to replace defaults and the socket sender.
        tmp_path: Pytest fixture used to isolate previous-invocation state.

    Returns:
        None: Asserts the second invocation reuses the first invocation's options.
    """
    monkeypatch.setenv("SOCKET_DCC_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr(common, "get_default_settings", lambda: (54322, "default-token"))
    monkeypatch.setattr(common, "get_default_host", lambda: "127.0.0.1")
    send_code = Mock(return_value=ExecutionResponse(True, "ok"))
    monkeypatch.setattr(common, "send_code", send_code)
    runner = CliRunner()

    first_result = runner.invoke(
        cli.app,
        ["code", "print('saved')", "--host", "192.168.1.70", "--port", "45679", "--token", "saved-token"],
    )
    previous_result = runner.invoke(cli.app, ["code", "--previous"])

    assert first_result.exit_code == 0, first_result.output
    assert previous_result.exit_code == 0, previous_result.output
    assert send_code.call_count == 2
    send_code.assert_called_with("print('saved')", host="192.168.1.70", port=45679, token="saved-token")


def test_path_previous_reuses_saved_file_and_connection_options(monkeypatch, tmp_path: Path) -> None:
    """Verify --previous reuses the saved path and custom connection options.

    Args:
        monkeypatch: Pytest fixture used to replace defaults and the socket sender.
        tmp_path: Pytest fixture used to create the file and isolate saved state.

    Returns:
        None: Asserts path and connection settings from the first invocation are reused.
    """
    python_file = tmp_path / "saved.py"
    python_file.write_text("print('saved')\n", encoding="utf-8")
    monkeypatch.setenv("SOCKET_DCC_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr(common, "get_default_settings", lambda: (54322, "default-token"))
    monkeypatch.setattr(common, "get_default_host", lambda: "127.0.0.1")
    send_code = Mock(return_value=ExecutionResponse(True, "ok"))
    monkeypatch.setattr(common, "send_code", send_code)
    runner = CliRunner()

    first_result = runner.invoke(
        cli.app,
        ["path", str(python_file), "--host", "192.168.1.71", "--port", "45680", "--token", "path-token"],
    )
    previous_result = runner.invoke(cli.app, ["path", "--previous"])

    assert first_result.exit_code == 0, first_result.output
    assert previous_result.exit_code == 0, previous_result.output
    assert send_code.call_count == 2
    send_code.assert_called_with(
        str(python_file.resolve()),
        host="192.168.1.71",
        port=45680,
        token="path-token",
    )


def test_show_launches_gui_with_selected_connection_settings(monkeypatch) -> None:
    """Verify show forwards GUI settings and startup-connect selection.

    Args:
        monkeypatch: Pytest fixture used to replace the GUI launch function.

    Returns:
        None: Asserts show hands the selected settings to the GUI launcher.
    """
    show_module = import_module("socket_dcc.cli.show")
    launch = Mock(return_value=0)
    monkeypatch.setattr(show_module, "launch", launch)

    result = CliRunner().invoke(
        cli.app,
        ["show", "--host", "192.168.1.20", "--port", "45678", "--token", "cli-token", "--connect"],
    )

    assert result.exit_code == 0, result.output
    launch.assert_called_once_with(host="192.168.1.20", port=45678, token="cli-token", connect=True)


def test_cli_lists_commands_without_implicitly_opening_gui() -> None:
    """Verify no arguments displays help rather than launching the GUI.

    Returns:
        None: Asserts the explicit action commands appear in CLI help.
    """
    result = CliRunner().invoke(cli.app, [])

    assert result.exit_code == 2
    assert "show" in result.output
    assert "test-raise" in result.output
    assert "path" in result.output


def test_configure_saves_values_passed_as_options(monkeypatch) -> None:
    """Verify configure persists host, port, and token supplied through options.

    Args:
        monkeypatch: Pytest fixture used to replace defaults and persistence.

    Returns:
        None: Asserts the supplied values are saved without prompting.
    """
    configure_module = import_module("socket_dcc.cli.configure")
    get_default_host = Mock(return_value="127.0.0.1")
    get_default_settings = Mock(return_value=(54322, "default-token"))
    save_default_settings = Mock()
    monkeypatch.setattr(configure_module, "get_default_host", get_default_host)
    monkeypatch.setattr(configure_module, "get_default_settings", get_default_settings)
    monkeypatch.setattr(configure_module, "save_default_settings", save_default_settings)

    result = CliRunner().invoke(
        cli.app,
        ["configure", "--host", "192.168.1.20", "--port", "45678", "--token", "custom-token"],
    )

    assert result.exit_code == 0, result.output
    save_default_settings.assert_called_once_with(port=45678, token="custom-token", host="192.168.1.20")


def test_configure_prompts_with_defaults_for_omitted_options(monkeypatch) -> None:
    """Verify omitted configure values can accept their current defaults.

    Args:
        monkeypatch: Pytest fixture used to replace defaults and persistence.

    Returns:
        None: Asserts Enter accepts the displayed default values.
    """
    configure_module = import_module("socket_dcc.cli.configure")
    monkeypatch.setattr(configure_module, "get_default_host", lambda: "127.0.0.1")
    monkeypatch.setattr(configure_module, "get_default_settings", lambda: (54322, "default-token"))
    env_file = Path("/tmp/socket-dcc-test-settings.env")
    monkeypatch.setattr(configure_module, "get_env_path", lambda: env_file)
    save_default_settings = Mock()
    monkeypatch.setattr(configure_module, "save_default_settings", save_default_settings)

    result = CliRunner().invoke(cli.app, ["configure"], input="\n\n\n")

    assert result.exit_code == 0, result.output
    save_default_settings.assert_called_once_with(port=54322, token="default-token", host="127.0.0.1")
    assert str(env_file) in result.output
