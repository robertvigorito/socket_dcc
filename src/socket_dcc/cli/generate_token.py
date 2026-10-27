"""Generate and persist socket-dcc connection defaults."""

import secrets

import typer
from rich.console import Console
from rich.panel import Panel

from socket_dcc.defaults import generate_port, get_env_path, save_default_settings

console = Console()


def generate_token(
    prefix: str = typer.Option("", "--prefix", help="Add a prefix to the token."),
    suffix: str = typer.Option("", "--suffix", help="Add a suffix to the token."),
) -> None:
    """Generate and save a new authentication token and port.

    Args:
        prefix: Optional prefix to add to the generated token.
        suffix: Optional suffix to add to the generated token.

    Returns:
        None: Saves and displays the generated connection defaults.
    """
    token = f"{prefix}{secrets.token_hex(16)}{suffix}"
    port = generate_port()
    save_default_settings(port, token)
    env_file = get_env_path()
    console.print(Panel.fit("Connection Defaults Generated", style="bold green"))
    console.print(f"[green]✓ Saved to[/green] {env_file}")
    console.print(f"\n[bold]Token:[/bold] [cyan]{token}[/cyan]")
    console.print(f"[bold]Port:[/bold] [cyan]{port}[/cyan]")
