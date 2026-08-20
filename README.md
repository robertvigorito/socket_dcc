# socket-dcc

Run the desktop app:

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

## VS Code extension

The `vscode-extension/` folder contains a simple extension with these commands:

- `socket-dcc: Open Control Panel`
- `socket-dcc: Send Active Python File`
- `socket-dcc: Save Active Python File`
- `socket-dcc: Run Saved Python File`

Use the control panel to edit the socket host, port, token, and saved file path.
The panel also shows recently executed files.

Those values are stored in VS Code settings under `socketDcc.*` and are restored
after VS Code reloads.