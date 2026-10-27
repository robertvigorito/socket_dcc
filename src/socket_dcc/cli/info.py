"""Display the contents of the shared socket-dcc environment file."""

import typer
from rich.console import Console
from rich.text import Text

from socket_dcc.defaults import get_env_path

console = Console()


def info() -> None:
    """Print every entry in the canonical .env file.

    Returns:
        None: Writes the .env file path and contents to standard output.

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
