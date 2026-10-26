"""Command-line interface for socket-dcc code execution."""

import os
import secrets
from pathlib import Path

import typer
from dotenv import load_dotenv, set_key
from rich.console import Console
from rich.panel import Panel

from socket_dcc.client import send_code
from socket_dcc.interface import main as run_gui

console = Console()

load_dotenv()

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
    """
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(str(file_path), encoding="utf-8")


@app.callback()
def root(ctx: typer.Context) -> None:
    """Root callback to launch GUI if no subcommand is provided.

    Args:
        ctx: Typer context.
    """
    if ctx.invoked_subcommand is None:
        raise typer.Exit(code=run_gui())


def main() -> int:
    """Run the CLI application.

    Returns:
        int: Zero when the CLI exits successfully.
    """
    app()
    return 0


def _test_connection(code: str, test_name: str = "Testing socket-dcc") -> None:
    """Send test code to the socket server.

    Args:
        code: Python code to execute for testing.
        test_name: Name of the test to display.
    """
    token = os.environ.get("SOCKET_DCC_TOKEN", "test-token")
    console.print(Panel.fit(test_name, style="bold blue"))
    console.print("Sending test code to the socket server...")
    console.print("  [cyan]Host:[/cyan] 127.0.0.1")
    console.print("  [cyan]Port:[/cyan] 5050")
    console.print(f"  [cyan]Token:[/cyan] {token}")
    send_code("127.0.0.1", 5050, token, code)


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
    host: str = typer.Option("127.0.0.1", "--host", envvar="SOCKET_DCC_HOST"),
    port: int = typer.Option(5050, "--port", envvar="SOCKET_DCC_PORT"),
    token: str = typer.Option(..., "--token", envvar="SOCKET_DCC_TOKEN", prompt=True),
) -> None:
    """Send a Python file to the server for remote execution.

    Args:
        file: Path to Python file to execute.
        previous: Whether to execute the previously sent file.
        code: Optional Python code to execute directly.
        host: Server hostname.
        port: Server port.
        token: Authentication token.
    """
    state_path = _state_path()

    if sum((previous, file is not None, code is not None)) > 1:
        raise typer.BadParameter("Choose only one of --previous, --code, or a file path.")

    file_path: Path | None = None
    if code is not None:
        request_code = code
    elif previous:
        file_path = _load_previous_file(state_path)
        file_path = file_path.resolve()
        if not file_path.is_file():
            raise typer.BadParameter(f"File not found: {file_path}")
        request_code = file_path.read_text(encoding="utf-8")
    elif file is not None:
        file_path = file
        file_path = file_path.resolve()
        if not file_path.is_file():
            raise typer.BadParameter(f"File not found: {file_path}")
        request_code = file_path.read_text(encoding="utf-8")
    else:
        raise typer.BadParameter("Provide a file path, pass --previous, or use --code.")

    response = send_code(host, port, token, request_code)

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
def save(
    file: Path = typer.Argument(..., help="Python file to save for later runs."),
) -> None:
    """Save a Python file for later execution with --previous flag.

    Args:
        file: Path to Python file to save.
    """
    state_path = _state_path()
    file_path = file.resolve()
    if not file_path.exists():
        raise typer.BadParameter(f"File not found: {file_path}")
    _save_previous_file(state_path, file_path)
    console.print(f"[green]✓ Saved[/green] {file_path}")


@app.command()
def test() -> None:
    """Test the socket server connection by sending a simple print statement."""
    _test_connection('print("helloworld")', "Testing socket-dcc")


@app.command()
def test_raise() -> None:
    """Test the socket server error handling by raising an exception."""
    _test_connection('raise ValueError("Test exception")', "Testing socket-dcc (Error Condition)")


@app.command()
def generate_token(
    prefix: str = typer.Option("", "--prefix", help="Add a prefix to the token."),
    suffix: str = typer.Option("", "--suffix", help="Add a suffix to the token."),
) -> None:
    """Generate a new authentication token and save it to .env file.

    Args:
        prefix: Optional prefix to add to the token.
        suffix: Optional suffix to add to the token.
    """
    token = secrets.token_hex(16)
    full_token = f"{prefix}{token}{suffix}"
    env_file = Path.cwd() / ".env"

    set_key(str(env_file), "SOCKET_DCC_TOKEN", full_token)
    console.print(Panel.fit("Token Generated", style="bold green"))
    console.print(f"[green]✓ Saved to[/green] {env_file}")
    console.print(f"\n[bold]Token:[/bold] [cyan]{full_token}[/cyan]")


if __name__ == "__main__":
    main()
