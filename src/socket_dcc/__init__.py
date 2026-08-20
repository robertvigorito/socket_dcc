"""Socket DCC - Execute Python code remotely via socket connection."""


def main() -> None:
    """Entry point for the socket-dcc CLI application."""
    from .cli import main as run

    run()
