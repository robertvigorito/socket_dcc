"""Shared helpers for socket-dcc CLI commands."""

import json
import os
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from socket_dcc.client import send_code
from socket_dcc.defaults import get_default_host, get_default_settings

console = Console()
error_console = Console(stderr=True)


def previous_options_path(command: str) -> Path:
    """Return the state file path for a command's previous invocation.

    Args:
        command: Command identifier used to keep invocation state separate.

    Returns:
        Path: State file path under the configured state directory.
    """
    state_dir = Path(os.environ.get("SOCKET_DCC_STATE_DIR", Path.home() / ".config" / "socket-dcc"))
    return state_dir / f"last-{command}.json"


def save_previous_options(command: str, options: dict[str, str | int | bool | None]) -> None:
    """Persist the latest invocation options for a command.

    Args:
        command: Command identifier used to keep invocation state separate.
        options: JSON-compatible command options to persist.

    Returns:
        None: Writes the options with owner-only file permissions.
    """
    state_path = previous_options_path(command)
    state_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    state_path.write_text(json.dumps(options), encoding="utf-8")
    state_path.chmod(0o600)


def load_previous_options(command: str) -> dict[str, str | int | bool | None]:
    """Load a command's previously saved invocation options.

    Args:
        command: Command identifier used to select the state file.

    Returns:
        dict[str, str | int | bool | None]: The persisted command options.

    Raises:
        typer.BadParameter: If the command has no valid previous invocation.
    """
    state_path = previous_options_path(command)
    try:
        options = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise typer.BadParameter(f"No valid previous {command} invocation is saved.") from exc

    if not isinstance(options, dict):
        raise typer.BadParameter(f"No valid previous {command} invocation is saved.")
    return options


def resolve_connection_options(
    host: str | None,
    port: int | None,
    token: str | None,
) -> tuple[str, int, str]:
    """Resolve omitted connection values from shared defaults.

    Args:
        host: Optional server host override.
        port: Optional server port override.
        token: Optional authentication token override.

    Returns:
        tuple[str, int, str]: Effective host, port, and token values.
    """
    if port is None or token is None:
        default_port, default_token = get_default_settings()
        port = default_port if port is None else port
        token = default_token if token is None else token
    host = get_default_host() if host is None else host
    return host, port, token


def send_to_default_server(
    code: str,
    title: str,
    expected_error: str | None = None,
    silent: bool = False,
    host: str | None = None,
    port: int | None = None,
    token: str | None = None,
    run_path: bool = False,
    wait: bool = False,
) -> None:
    """Send code to the configured socket server and report its result.

    Args:
        code: Python code or a file path for server-side execution.
        title: Heading displayed for the command.
        expected_error: Error text required in a successful intentional-failure test.
        silent: Whether to suppress sender-side output.
        host: Optional server host override.
        port: Optional server port override.
        token: Optional authentication token override.
        run_path: Whether the payload is a file path to execute with runpy.
        wait: Whether to wait for the execution result rather than an acceptance response.

    Returns:
        None: Prints the response or exits with a failure status.
    """
    host, port, token = resolve_connection_options(host, port, token)
    if not silent:
        console.print(Panel.fit(title, style="bold blue"))
        console.print("Sending request to the socket server...")
        console.print(f"  [cyan]Host:[/cyan] {host}")
        console.print(f"  [cyan]Port:[/cyan] {port}")

    try:
        send_options: dict[str, bool] = {}
        if run_path:
            send_options["run_path"] = True
        if wait:
            send_options["wait"] = True
        response = send_code(code, host=host, port=port, token=token, **send_options)
    except OSError as exc:
        typer.echo(
            f"Could not connect to socket-dcc at {host}:{port}. "
            "Start the GUI server and verify its displayed port and token.",
            err=True,
        )
        raise typer.Exit(code=1) from exc

    if expected_error is not None:
        if response.ok or expected_error not in response.output:
            if not silent:
                console.print(f"[red]Expected error was not returned by the server:[/red] {response.output}")
            raise typer.Exit(code=1)
        if not silent:
            console.print(f"[green]✓ Server returned the expected error:[/green] {expected_error}")
        return

    if not response.ok:
        output = response.output.replace(r"\\wsl.localhost\Ubuntu", "").replace("\\", "/")
        if response.raised:
            error_console.print(Syntax(output, "pytb", theme="ansi_dark", background_color="default"))
            raise typer.Exit(code=1)
        if not silent:
            console.print(f"[red]Server rejected the request:[/red] {output}")
        return
    if not silent:
        if not wait:
            console.print("Request accepted", style="green")
        console.print(response.output, markup=False, highlight=False)
