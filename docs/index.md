# socket-dcc

Socket DCC provides a desktop server and command-line client for sending Python
code from a terminal to a running DCC application.

## Install

Install the package and its development tools:

```sh
uv sync
```

## Quick start

Launch the GUI:

```sh
uv run socket-dcc show
```

Use `uv run socket-dcc --help` to see the available commands. The `code` command sends inline Python or
the contents of a local `.py` file; `path` runs a file by path in the server process.

## Package layout

The installable Python package is located in `src/socket_dcc/`. Its client, server, configuration
defaults, and application interface are top-level modules. CLI commands are implemented in
`src/socket_dcc/cli/`, and the modular GUI is in `src/socket_dcc/core/gui/`. The Nuke startup hooks
under `src/nuke/` are separate from the Python package and are installed as Nuke files by the Rez build.
## Documentation development

Preview the documentation locally with live reload:

```sh
uv run mkdocs serve
```

Build the static site into `dist/docs/`:

```sh
uv run mkdocs build
```

This site uses Material for MkDocs and starts in dark mode. Use its built-in palette control to
switch to light mode; your choice is remembered in the browser.
