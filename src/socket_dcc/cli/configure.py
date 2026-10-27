"""Configure shared socket-dcc connection defaults."""

import typer
from rich.console import Console
from rich.prompt import IntPrompt, Prompt

from socket_dcc.defaults import get_default_host, get_default_settings, get_env_path, save_default_settings

console = Console()


def configure(
    host: str | None = typer.Option(None, "--host", help="Host clients use to reach the socket server."),
    port: int | None = typer.Option(None, "--port", help="Socket server port."),
    token: str | None = typer.Option(None, "--token", help="Socket server authentication token."),
) -> None:
    """Prompt for and save the host, port, and token defaults.

    Args:
        host: Optional host value; prompts with the current default when omitted.
        port: Optional port value; prompts with the current default when omitted.
        token: Optional token value; prompts with the current default when omitted.

    Returns:
        None: Persists the selected connection defaults.

    Raises:
        typer.BadParameter: If the selected port or host is invalid.
    """
    default_host = get_default_host()
    default_port, default_token = get_default_settings()

    selected_host = host if host is not None else Prompt.ask("[cyan]Host[/cyan]", default=default_host)
    selected_port = port if port is not None else IntPrompt.ask("[cyan]Port[/cyan]", default=default_port)
    if token is None:
        console.print("[cyan]Token[/cyan] (input hidden; press Enter to keep the current token)")
    selected_token = token if token is not None else typer.prompt("Token", default=default_token, hide_input=True)

    try:
        save_default_settings(port=selected_port, token=selected_token, host=selected_host)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    console.print("[green]Connection defaults saved.[/green]")
    console.print(f"  [cyan]Host:[/cyan] {selected_host}")
    console.print(f"  [cyan]Port:[/cyan] {selected_port}")
    console.print("  [cyan]Token:[/cyan] saved")
    console.print(f"  [cyan]Settings file:[/cyan] {get_env_path()}")
