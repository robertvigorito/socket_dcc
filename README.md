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
socket-dcc show
```

The command-line app also provides `code` to send inline Python or the contents of a local `.py` file, and
`path` to ask the server process to execute a Python file accessible to it. Use `socket-dcc --help` or
`socket-dcc <command> --help` for command options.

For testing without opening Nuke's GUI, start the server with `socket-dcc headless` or the standalone
`socket-dcc-headless` command from an environment using Nuke's Python interpreter. Its default bind
address follows the shared host setting and matches the GUI server; use `--host 127.0.0.1` to restrict
it to loopback. If the resolved default address is unavailable, the server retries on loopback; use
`--host` with a valid local interface address when network clients need access. It accepts the same
`code` and `path` requests as the GUI server. Press Ctrl+C to stop it.
You can also start the headless server from a Nuke terminal interpreter or test harness with
`socket_dcc.headless.run_headless_server()`; pass a `threading.Event` as `stop_event` when embedding it
so the server can be stopped programmatically.

```bash
socket-dcc-headless --host 127.0.0.1 --port 54322 --token your-token
socket-dcc code 'print("Hello from headless Nuke")' --host 127.0.0.1 --port 54322 --token your-token --wait
```

The headless runner creates no Qt application. It services execution requests on the calling thread,
which lets code sent to it use Nuke APIs from Nuke's terminal-mode interpreter.
Stop a headless server remotely with `socket-dcc close` (or `socket-dcc-close`), using the same
host, port, and token as the server. Remote shutdown is enabled only on the headless runner; GUI servers
continue to be stopped from their panel.

In the GUI, enable **Log → Clear Log Before New Send** to clear previous log entries when each new code
or path request arrives. The setting is off by default and is saved between sessions.

Code and path requests return as soon as the server accepts them; the server continues executing and
displays the eventual output or errors in its GUI log. Add `--wait` to either command when the caller
needs to wait for completion and receive the execution output.

On first launch, socket-dcc generates a shared port and authentication token and stores them in the
project `.env` file. The GUI uses these values as its defaults. The CLI uses them automatically, so a
local send can omit both options:

```bash
socket-dcc code path/to/script.py
socket-dcc code 'print("Hello")'
```

Use `--host`, `--port`, or `--token` to override the defaults. `socket-dcc generate-token` regenerates
the token and chooses a new available port, saving both to `.env`.

## Package layout

The installable Python package is under `src/socket_dcc/`. Its top-level modules provide the client,
server, defaults, and application interface. The command-line implementation is in `cli/`, while the
modular GUI lives in `core/gui/`. Nuke startup hooks are kept separately in `src/nuke/`; they are not
part of the `socket_dcc` Python package and are installed as Nuke files by the Rez build.

## Command line

Send the contents of a local Python file to the running socket server:

```bash
socket-dcc code path/to/script.py
```

Send inline Python code:

```bash
socket-dcc code 'print("Hello from socket-dcc")'
```

To execute a file by path in the server process, use `path`. The file must be accessible from the
server's environment:

```bash
socket-dcc path path/to/script.py
```

For cross-platform networking and WSL 2 setup, see [README_WSL_WIN.md](README_WSL_WIN.md).