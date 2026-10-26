# socket-dcc

Socket DCC provides a desktop server and command-line client for sending Python
code from a terminal to a running DCC application.

## Install

Install the package and its development tools:

```sh
uv sync
```

## Quick start

Run the command-line application:

```sh
uv run socket-dcc
```
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
