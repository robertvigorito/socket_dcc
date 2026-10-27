"""Typer command-line interface for socket-dcc."""

import os
import secrets
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from socket_dcc.client import send_code
from socket_dcc.defaults import (
    generate_port,
    get_default_host,
    get_default_settings,
    get_env_path,
    load_default_environment,
    save_default_settings,
)
from socket_dcc.interface import main as run_gui

console = Console()

load_default_environment()

app = typer.Typer(add_completion=False, invoke_without_command=True)
LAST_FILE_ENV = "SOCKET_DCC_LAST_FILE"


def _state_path() -> Path:
    """Get the path to the state file storing the last executed file.

    Returns:
        Path: State file path.
    """
    return Path(os.environ.get(LAST_FILE_ENV, Path.home() / ".socket-dcc-last-file"))


def _load_previous_file(state_path: Path) -> Path:
    """Load the previously saved file path from state.

    Args:
        state_path: Path to the state file.

    Returns:
        Path: The previously saved file path.

    Raises:
        typer.BadParameter: If no previous file has been saved.
    """
    if not state_path.exists():
        raise typer.BadParameter("No previous file has been saved yet.")
    return Path(state_path.read_text(encoding="utf-8").strip())


def _save_previous_file(state_path: Path, file_path: Path) -> None:
    """Save a file path to state for later retrieval.

    Args:
        state_path: Path to the state file.
        file_path: File path to save.

    Returns:
        None: Writes the selected file path to the state file.
    """
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(str(file_path), encoding="utf-8")


@app.callback()
def root(
    ctx: typer.Context,
    host: str | None = typer.Option(None, "--host", envvar="SOCKET_DCC_HOST"),
    port: int | None = typer.Option(None, "--port", envvar="SOCKET_DCC_PORT"),
    token: str | None = typer.Option(None, "--token", envvar="SOCKET_DCC_TOKEN"),
) -> None:
    """Launch the GUI when no CLI subcommand was selected.

    Args:
        ctx: Typer context.
        host: Server host; defaults to the local interface used by the GUI.
        port: Server port; defaults to the shared configuration.
        token: Authentication token; defaults to the shared configuration.

    Returns:
        None: Starts the GUI when invoked without a subcommand.
    """
    if ctx.invoked_subcommand is None:
        raise typer.Exit(code=run_gui(host=host, port=port, token=token))


def main() -> int:
    """Run the command-line application.

    Returns:
        int: Zero when the CLI exits successfully.
    """
    app()
    return 0


def _test_connection(
    code: str,
    test_name: str = "Testing socket-dcc",
    host: str | None = None,
    port: int | None = None,
    token: str | None = None,
    expected_error: str | None = None,
) -> None:
    """Send test code to the socket server.

    Args:
        code: Python code to execute for testing.
        test_name: Name of the test to display.
        host: Optional server host override.
        port: Optional server port override.
        token: Optional authentication token override.
        expected_error: Error text expected from an intentional failing snippet.

    Returns:
        None: Prints test details and sends the code to the local server.
    """
    default_port, default_token = get_default_settings()
    target_port = port or default_port
    target_token = token or default_token
    target_host = host or get_default_host()
    console.print(Panel.fit(test_name, style="bold blue"))
    console.print("Sending test code to the socket server...")
    console.print(f"  [cyan]Host:[/cyan] {target_host}")
    console.print(f"  [cyan]Port:[/cyan] {target_port}")
    console.print(f"  [cyan]Token:[/cyan] {target_token}")
    try:
        response = send_code(code, host=target_host, port=target_port, token=target_token)
    except OSError as exc:
        console.print(
            f"[red]Could not connect to socket-dcc at {target_host}:{target_port}.[/red] "
            "Start the GUI server and verify its displayed port and token."
        )
        raise typer.Exit(code=1) from exc

    if expected_error is not None:
        if response.ok or expected_error not in response.output:
            console.print(f"[red]Expected error was not returned by the server:[/red] {response.output}")
            raise typer.Exit(code=1)
        console.print(f"[green]✓ Connected; server returned the expected error:[/green] {expected_error}")
        return

    if not response.ok:
        console.print(f"[red]Server rejected the test:[/red] {response.output}")
        raise typer.Exit(code=1)
    console.print(f"[green]✓ Server response:[/green] {response.output}")


@app.command()
def send(
    file: Path | None = typer.Argument(
        None,
        help="Python file to send to the socket server.",
    ),
    previous: bool = typer.Option(
        False,
        "--previous",
        help="Run the previously sent file instead of a new file.",
    ),
    code: str | None = typer.Option(
        None,
        "--code",
        "-c",
        help="Python code to execute instead of reading a file.",
    ),
    host: str | None = typer.Option(None, "--host", envvar="SOCKET_DCC_HOST"),
    port: int | None = typer.Option(None, "--port", envvar="SOCKET_DCC_PORT"),
    token: str | None = typer.Option(None, "--token", envvar="SOCKET_DCC_TOKEN"),
) -> None:
    """Send Python code or a file to the server for execution.

    Args:
        file: Optional path to a Python file.
        previous: Whether to execute the previously saved file.
        code: Optional Python code to execute directly.
        host: Server hostname; defaults to the local interface used by the GUI.
        port: Server port.
        token: Authentication token.

    Returns:
        None: Prints the execution response or exits with a failure status.
    """
    state_path = _state_path()
    if sum((previous, file is not None, code is not None)) > 1:
        raise typer.BadParameter("Choose only one of --previous, --code, or a file path.")

    file_path: Path | None = None
    if code is not None:
        request_code = code
    elif previous:
        file_path = _load_previous_file(state_path).resolve()
        if not file_path.is_file():
            raise typer.BadParameter(f"File not found: {file_path}")
        request_code = file_path.read_text(encoding="utf-8")
    elif file is not None:
        file_path = file.resolve()
        if not file_path.is_file():
            raise typer.BadParameter(f"File not found: {file_path}")
        request_code = file_path.read_text(encoding="utf-8")
    else:
        raise typer.BadParameter("Provide a file path, pass --previous, or use --code.")

    default_port, default_token = get_default_settings()
    target_host = host or get_default_host()
    target_port = port or default_port
    try:
        response = send_code(request_code, host=target_host, port=target_port, token=token or default_token)
    except OSError as exc:
        console.print(
            f"[red]Could not connect to socket-dcc at {target_host}:{target_port}.[/red] "
            "Start the GUI server and verify the host and port."
        )
        raise typer.Exit(code=1) from exc
    if response.output:
        console.print(Panel(response.output, title="Output", expand=False))

    if response.ok:
        if file_path is not None and not previous:
            _save_previous_file(state_path, file_path)
        console.print("[green]✓ Code executed successfully[/green]")
        return

    console.print("[red]✗ Command failed[/red]")
    raise typer.Exit(code=1)


@app.command()
def save(file: Path = typer.Argument(..., help="Python file to save for later runs.")) -> None:
    """Save a Python file for later execution with the --previous flag.

    Args:
        file: Path to Python file to save.

    Returns:
        None: Stores the resolved path for later use.
    """
    state_path = _state_path()
    file_path = file.resolve()
    if not file_path.exists():
        raise typer.BadParameter(f"File not found: {file_path}")
    _save_previous_file(state_path, file_path)
    console.print(f"[green]✓ Saved[/green] {file_path}")


@app.command()
def test(
    host: str | None = typer.Option(None, "--host", envvar="SOCKET_DCC_HOST"),
    port: int | None = typer.Option(None, "--port", envvar="SOCKET_DCC_PORT"),
    token: str | None = typer.Option(None, "--token", envvar="SOCKET_DCC_TOKEN"),
) -> None:
    """Test the socket server connection by sending a simple print statement.

    Returns:
        None: Sends a test snippet to the local server.
    """
    _test_connection('print("helloworld")', "Testing socket-dcc", host=host, port=port, token=token)


@app.command()
def test_raise(
    host: str | None = typer.Option(None, "--host", envvar="SOCKET_DCC_HOST"),
    port: int | None = typer.Option(None, "--port", envvar="SOCKET_DCC_PORT"),
    token: str | None = typer.Option(None, "--token", envvar="SOCKET_DCC_TOKEN"),
) -> None:
    """Test socket server error handling by sending code that raises an exception.

    Returns:
        None: Sends a test exception and verifies the interface returned it.
    """
    _test_connection(
        'raise ValueError("Test exception")',
        "Testing socket-dcc (Error Condition)",
        host=host,
        port=port,
        token=token,
        expected_error="ValueError: Test exception",
    )


@app.command()
def generate_token(
    prefix: str = typer.Option("", "--prefix", help="Add a prefix to the token."),
    suffix: str = typer.Option("", "--suffix", help="Add a suffix to the token."),
) -> None:
    """Generate and save a new authentication token and port in a .env file.

    Args:
        prefix: Optional prefix to add to the token.
        suffix: Optional suffix to add to the token.

    Returns:
        None: Saves and displays the generated port and token.
    """
    token = secrets.token_hex(16)
    full_token = f"{prefix}{token}{suffix}"
    port = generate_port()
    save_default_settings(port, full_token)
    env_file = get_env_path()
    console.print(Panel.fit("Connection Defaults Generated", style="bold green"))
    console.print(f"[green]✓ Saved to[/green] {env_file}")
    console.print(f"\n[bold]Token:[/bold] [cyan]{full_token}[/cyan]")
    console.print(f"[bold]Port:[/bold] [cyan]{port}[/cyan]")


if __name__ == "__main__":
    raise SystemExit(main())
