"""Run a Python file on the socket server using runpy."""

from dataclasses import asdict, dataclass
from pathlib import Path

import typer

from socket_dcc.cli.common import (
    load_previous_options,
    resolve_connection_options,
    save_previous_options,
    send_to_default_server,
)


@dataclass(slots=True)
class PathOptions:
    """Options for a path invocation.

    Attributes:
        file: Resolved Python file to run.
        silent: Whether to suppress sender-side output.
        wait: Whether to wait for the execution result.
        host: Server host.
        port: Server port.
        token: Authentication token.
    """

    file: Path
    silent: bool
    wait: bool
    host: str
    port: int
    token: str

    @classmethod
    def build(cls, previous: bool, **cli: str | int | bool | Path | None) -> "PathOptions":
        """Merge defaults, the previous invocation, and command-line values (in that order).

        Args:
            previous: Whether to start from the previous invocation's saved options.
            **cli: Command-line values; ``None`` values are ignored.

        Returns:
            PathOptions: Validated options.

        Raises:
            typer.BadParameter: If no file is available or it is not an existing Python file.
        """
        saved = load_previous_options("path") if previous else {}
        given = {key: value for key, value in cli.items() if value is not None}
        merged = {"silent": True, "wait": False, **saved, **given}
        if not merged.get("file"):
            raise typer.BadParameter("Provide a Python file or use --previous with a saved invocation.")
        file = Path(str(merged["file"])).expanduser().resolve()
        if not file.is_file() or file.suffix.lower() != ".py":
            raise typer.BadParameter(f"Expected an existing Python file: {file}")
        host, port, token = resolve_connection_options(*(merged.get(key) for key in ("host", "port", "token")))
        return cls(
            file=file,
            silent=bool(merged["silent"]),
            wait=bool(merged["wait"]),
            host=host,
            port=port,
            token=token,
        )

    def to_saved(self) -> dict[str, str | int | bool | None]:
        """Convert the options to the JSON-compatible form used for saving.

        Returns:
            dict[str, str | int | bool | None]: Saved option values.
        """
        return {**asdict(self), "file": str(self.file)}


def run_path(
    file: Path | None = typer.Argument(None, help="Python file to run on the socket server."),
    previous: bool = typer.Option(False, "--previous", help="Repeat the last path command invocation."),
    wait: bool | None = typer.Option(
        None,
        "--wait/--no-wait",
        help="Wait for execution to finish and return its output (default: return immediately).",
    ),
    silent: bool | None = typer.Option(None, "--silent/--no-silent", help="Suppress all output from this command."),
    host: str | None = typer.Option(None, "--host", help="Override the configured server host."),
    port: int | None = typer.Option(None, "--port", help="Override the configured server port."),
    token: str | None = typer.Option(None, "--token", help="Override the configured authentication token."),
) -> bool:
    """Send a Python file path for server-side runpy execution.

    The path is sent unchanged; the server converts it when it is not running inside WSL.

    Args:
        file: Python file accessible to the server process.
        previous: Whether to reuse the last path and connection options.
        wait: Whether to wait for the remote execution result.
        silent: Whether to suppress sender-side output; defaults to True for a new invocation.
        host: Optional server host override.
        port: Optional server port override.
        token: Optional authentication token override.

    Returns:
        bool: True once the path has been sent.

    Raises:
        typer.BadParameter: If the path is not an existing Python file.
    """
    options = PathOptions.build(previous, file=file, wait=wait, silent=silent, host=host, port=port, token=token)
    save_previous_options("path", options.to_saved())
    send_to_default_server(
        options.file.as_posix(),
        f"Running {options.file.name} with runpy",
        silent=options.silent,
        host=options.host,
        port=options.port,
        token=options.token,
        run_path=True,
        wait=options.wait,
    )
    return True
