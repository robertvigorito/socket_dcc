from __future__ import annotations

import os
from pathlib import Path

import typer

from .client import send_code

app = typer.Typer(add_completion=False, invoke_without_command=True)
LAST_FILE_ENV = "SOCKET_DCC_LAST_FILE"


def _state_path() -> Path:
    return Path(os.environ.get(LAST_FILE_ENV, Path.home() / ".socket-dcc-last-file"))


def _load_previous_file(state_path: Path) -> Path:
    if not state_path.exists():
        raise typer.BadParameter("No previous file has been saved yet.")
    return Path(state_path.read_text(encoding="utf-8").strip())


def _save_previous_file(state_path: Path, file_path: Path) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(str(file_path), encoding="utf-8")


@app.callback()
def main(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        from .gui import main as run_gui

        run_gui()


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
    host: str = typer.Option("127.0.0.1", "--host", envvar="SOCKET_DCC_HOST"),
    port: int = typer.Option(5050, "--port", envvar="SOCKET_DCC_PORT"),
    token: str = typer.Option(..., "--token", envvar="SOCKET_DCC_TOKEN", prompt=True),
) -> None:
    state_path = _state_path()

    if previous and file is not None:
        raise typer.BadParameter("Use either --previous or a file path, not both.")

    if previous:
        file_path = _load_previous_file(state_path)
    elif file is not None:
        file_path = file
    else:
        raise typer.BadParameter("Provide a file path or pass --previous.")

    if not file_path.exists():
        raise typer.BadParameter(f"File not found: {file_path}")

    code = file_path.read_text(encoding="utf-8")
    response = send_code(host, port, token, code)

    if not previous:
        _save_previous_file(state_path, file_path)

    if response.output:
        typer.echo(response.output)

    if response.ok:
        return

    raise typer.Exit(code=1)
