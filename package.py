"""Rez package definition for socket-dcc."""

name = "socket_dcc"
version = "0.1.0"
description = "Socket DCC application for running code from a terminal to a DCC environment."
requires = ["python"]
private_build_requires = []
build_command = "python {root}/rezbuild.py"


def commands() -> bool:
    """Expose the generated package and optional Nuke tools in Rez.

    Returns:
        bool: ``True`` after updating the Rez environment.
    """
    env.PYTHONPATH.append("{root}/python")  # noqa: F821 -- Rez injects ``env`` at runtime.
    env.NUKE_PATH.append("{root}/src/nuke")  # noqa: F821 -- Rez injects ``env`` at runtime.

