# socket-dcc

## Install

Install the package and its development dependencies with [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

This installs the `socket-dcc` command and the GUI dependencies. Launch the desktop app with:

```bash
socket-dcc
```

This opens the GUI; the same command also exposes Typer subcommands for sending and saving Python files.

## Command line

Send a Python file to the running socket server:

```bash
socket-dcc send path/to/script.py --token YOUR_TOKEN
```

Run the previously saved file instead:

```bash
socket-dcc send --previous --token YOUR_TOKEN
```

You can also save a file path without sending it:

```bash
socket-dcc save path/to/script.py
```

For cross-platform networking and WSL 2 setup, see [README_WSL_WIN.md](README_WSL_WIN.md).