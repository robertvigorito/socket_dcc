# socket-dcc VS Code extension install

## Requirements

- VS Code 1.85 or newer
- The `socket-dcc` Python app running locally

## Development install

1. Open the repository in VS Code.
2. Open the `vscode-extension/` folder.
3. Press `F5` to launch the extension in an Extension Development Host window.
4. Open the Command Palette and run:
   - `socket-dcc: Open Control Panel`
   - `socket-dcc: Send Active Python File`
   - `socket-dcc: Save Active Python File`
   - `socket-dcc: Run Saved Python File`

## Production install

1. From the `vscode-extension/` folder, install the VS Code packaging tool:

   ```bash
   npm install -g @vscode/vsce
   ```

2. Package the extension into a `.vsix` file:

   ```bash
   vsce package
   ```

3. In VS Code, choose **Extensions → Install from VSIX...**
4. Select the generated `.vsix` file.

## Configure the extension

Use the control panel or VS Code settings to set:

- `socketDcc.host`
- `socketDcc.port`
- `socketDcc.token`
- `socketDcc.savedFile`

The extension also stores recent executed files in `socketDcc.recentFiles`.
