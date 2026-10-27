"""Initialize and run the socket-dcc command-line application."""

import typer

from socket_dcc.cli.code import send_code_command
from socket_dcc.cli.configure import configure
from socket_dcc.cli.generate_token import generate_token
from socket_dcc.cli.info import info
from socket_dcc.cli.path import run_path
from socket_dcc.cli.show import show
from socket_dcc.cli.test import test
from socket_dcc.cli.test_raise import test_raise
from socket_dcc.defaults import load_default_environment

load_default_environment()

app = typer.Typer(no_args_is_help=True)
app.command(name="show")(show)
app.command(name="test")(test)
app.command(name="test-raise")(test_raise)
app.command(name="code")(send_code_command)
app.command(name="path")(run_path)
app.command(name="configure")(configure)
app.command(name="generate-token")(generate_token)
app.command(name="info")(info)


def main() -> int:
    """Run the socket-dcc command-line application.

    Returns:
        int: Zero when the CLI exits successfully.
    """
    app()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
