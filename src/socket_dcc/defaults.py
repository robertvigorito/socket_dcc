"""Shared defaults for the socket server and client."""

import os
import secrets
import socket
from pathlib import Path

from dotenv import load_dotenv, set_key

DEFAULT_HOST = "127.0.0.1"


def get_env_path() -> Path:
    """Resolve the shared socket-dcc .env file independently of the working directory.

    Returns:
        Path: Explicit SOCKET_DCC_ENV_FILE, project-root .env, or user config .env.
    """
    configured_path = os.environ.get("SOCKET_DCC_ENV_FILE")
    if configured_path:
        return Path(configured_path).expanduser().resolve()

    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent / ".env"

    return Path.home() / ".config" / "socket-dcc" / ".env"


def load_default_environment() -> Path:
    """Load shared socket-dcc settings from the canonical .env without overriding exports.

    Returns:
        Path: The resolved .env path used for configuration.
    """
    env_path = get_env_path()
    load_dotenv(dotenv_path=env_path, override=False)
    return env_path


def get_default_host() -> str:
    """Return the configured host or the local interface address used by the GUI server.

    Returns:
        str: The configured host, machine's resolved hostname address, or loopback fallback.
    """
    load_default_environment()
    configured_host = os.environ.get("SOCKET_DCC_HOST")
    if configured_host:
        return configured_host

    try:
        return socket.gethostbyname(socket.gethostname())
    except OSError:
        return DEFAULT_HOST


def generate_port() -> int:
    """Ask the operating system for an available TCP port.

    Returns:
        int: An available ephemeral port number.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as port_socket:
        port_socket.bind((DEFAULT_HOST, 0))
        return int(port_socket.getsockname()[1])


def get_default_settings() -> tuple[int, str]:
    """Load or generate shared port and token defaults in the nearest .env file.

    Returns:
        tuple[int, str]: The configured port and authentication token.
    """
    env_path = load_default_environment()
    env_path.parent.mkdir(parents=True, exist_ok=True)

    port_value = os.environ.get("SOCKET_DCC_PORT")
    token = os.environ.get("SOCKET_DCC_TOKEN")
    port = int(port_value) if port_value else generate_port()
    token = token or secrets.token_hex(16)

    if not port_value:
        set_key(str(env_path), "SOCKET_DCC_PORT", str(port))
        os.environ["SOCKET_DCC_PORT"] = str(port)
    if not os.environ.get("SOCKET_DCC_TOKEN"):
        set_key(str(env_path), "SOCKET_DCC_TOKEN", token)
        os.environ["SOCKET_DCC_TOKEN"] = token

    return port, token


def save_default_settings(port: int | None = None, token: str | None = None, host: str | None = None) -> None:
    """Persist the provided connection defaults for local clients.

    Args:
        port: Optional TCP port the server is listening on.
        token: Optional authentication token accepted by the server.
        host: Optional host used by local clients to reach the server.

    Returns:
        None: Writes provided defaults to the project .env and current process environment.
    """
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("port must be between 1 and 65535")
    if token is not None and not token:
        raise ValueError("token cannot be empty")
    if host is not None and not host.strip():
        raise ValueError("host cannot be empty")

    env_path = get_env_path()
    env_path.parent.mkdir(parents=True, exist_ok=True)
    if port is not None:
        set_key(str(env_path), "SOCKET_DCC_PORT", str(port))
        os.environ["SOCKET_DCC_PORT"] = str(port)
    if token is not None:
        set_key(str(env_path), "SOCKET_DCC_TOKEN", token)
        os.environ["SOCKET_DCC_TOKEN"] = token
    if host is not None:
        set_key(str(env_path), "SOCKET_DCC_HOST", host)
        os.environ["SOCKET_DCC_HOST"] = host
