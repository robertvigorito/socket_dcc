"""Display socket-dcc settings and previous invocation details."""

import json

import typer
from rich.console import Console
from rich.text import Text

from socket_dcc.cli.common import previous_options_path
from socket_dcc.defaults import get_env_path

console = Console()


def info() -> None:
    """Print the canonical .env file and saved code/path invocation options.

    Returns:
        None: Writes environment settings and previous invocation details.

    Raises:
        typer.BadParameter: If the .env file cannot be read.
    """
    env_path = get_env_path()
    try:
        contents = env_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise typer.BadParameter(f"Could not read environment file: {env_path}") from exc

    console.print(
        Text("Environment file: ", style="bold") + Text(str(env_path), style="cyan"),
        soft_wrap=True,
    )
    for line in contents.splitlines(keepends=True):
        line_content = line.rstrip("\r\n")
        line_ending = line[len(line_content) :]
        if "=" in line_content and not line_content.lstrip().startswith("#"):
            key, value = line_content.split("=", maxsplit=1)
            rendered_line = Text(key, style="cyan") + Text("=") + Text(value, style="green")
        else:
            rendered_line = Text(line_content, style="dim" if line_content.lstrip().startswith("#") else None)
        console.print(rendered_line, end=line_ending)

    for command in ("path", "code"):
        state_path = previous_options_path(command)
        console.print(f"\nPrevious {command} invocation:", style="bold")
        try:
            options = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            console.print("No saved invocation.", style="dim")
            continue
        if not isinstance(options, dict):
            console.print("No saved invocation.", style="dim")
            continue
        for key, value in options.items():
            display_value = "********" if key == "token" and value else str(value)
            console.print(f"  {key}: {display_value}")
