# socket-dcc

## Install

Install the package and its development dependencies with [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

This installs the `socket-dcc` command and the GUI dependencies. Launch the desktop app with:

The GUI uses [Qt.py](https://github.com/mottosso/Qt.py) as a binding-neutral Qt API. Install a Qt
binding supported by your host application (for example PySide2, PySide6, PyQt5, or PyQt6) in the runtime
environment; the development environment includes PySide6 for tests.

```bash
socket-dcc
```

This opens the GUI; the same command also exposes Typer subcommands for sending and saving Python files.

On first launch, socket-dcc generates a shared port and authentication token and stores them in the
project `.env` file. The GUI uses these values as its defaults. The CLI uses them automatically, so a
local send can omit both options:

```bash
socket-dcc send path/to/script.py
socket-dcc send --code 'print("Hello")'
```

Use `--host`, `--port`, or `--token` to override the defaults. `socket-dcc generate-token` regenerates
the token and chooses a new available port, saving both to `.env`.

## Command line

Send a Python file to the running socket server:

```bash
socket-dcc send path/to/script.py
```

Run the previously saved file instead:

```bash
socket-dcc send --previous
```

You can also save a file path without sending it:

```bash
socket-dcc save path/to/script.py
```

For cross-platform networking and WSL 2 setup, see [README_WSL_WIN.md](README_WSL_WIN.md).