"""Tests for loading socket connection defaults."""

import socket_dcc.defaults as defaults


def test_get_default_settings_loads_values_from_dotenv(monkeypatch, tmp_path) -> None:
    """Load the port and authentication token from the working directory .env file.

    Args:
        monkeypatch: Pytest fixture for environment and working-directory isolation.
        tmp_path: Pytest fixture providing a temporary directory.

    Returns:
        None: Asserts values from .env are returned as defaults.
    """
    monkeypatch.chdir(tmp_path)
    env_file = tmp_path / ".env"
    monkeypatch.setenv("SOCKET_DCC_ENV_FILE", str(env_file))
    monkeypatch.delenv("SOCKET_DCC_PORT", raising=False)
    monkeypatch.delenv("SOCKET_DCC_TOKEN", raising=False)
    env_file.write_text("SOCKET_DCC_PORT=45678\nSOCKET_DCC_TOKEN=dotenv-secret\n", encoding="utf-8")

    assert defaults.get_default_settings() == (45678, "dotenv-secret")


def test_environment_token_overrides_dotenv_token(monkeypatch, tmp_path) -> None:
    """Prefer the environment token over the value stored in .env.

    Args:
        monkeypatch: Pytest fixture for environment and working-directory isolation.
        tmp_path: Pytest fixture providing a temporary directory.

    Returns:
        None: Asserts the environment token is selected.
    """
    monkeypatch.chdir(tmp_path)
    env_file = tmp_path / ".env"
    monkeypatch.setenv("SOCKET_DCC_ENV_FILE", str(env_file))
    monkeypatch.delenv("SOCKET_DCC_PORT", raising=False)
    monkeypatch.setenv("SOCKET_DCC_TOKEN", "environment-secret")
    env_file.write_text("SOCKET_DCC_PORT=45679\nSOCKET_DCC_TOKEN=dotenv-secret\n", encoding="utf-8")

    assert defaults.get_default_settings() == (45679, "environment-secret")


def test_env_path_is_stable_across_working_directories(monkeypatch, tmp_path) -> None:
    """Resolve one canonical .env path regardless of where GUI or CLI starts.

    Args:
        monkeypatch: Pytest fixture for environment and working-directory isolation.
        tmp_path: Pytest fixture providing a temporary directory.

    Returns:
        None: Asserts the configured env path is independent of cwd.
    """
    env_file = tmp_path / "settings" / ".env"
    monkeypatch.setenv("SOCKET_DCC_ENV_FILE", str(env_file))
    monkeypatch.chdir(tmp_path)
    first_path = defaults.get_env_path()
    monkeypatch.chdir(tmp_path.parent)

    assert first_path == env_file
    assert defaults.get_env_path() == first_path
