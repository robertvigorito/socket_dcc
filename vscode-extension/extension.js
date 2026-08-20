const fs = require('fs/promises');
const net = require('net');
const path = require('path');
const vscode = require('vscode');

const output = vscode.window.createOutputChannel('socket-dcc');
const CONTROL_PANEL_VIEW_TYPE = 'socketDcc.controlPanel';
const RECENT_FILES_SETTING = 'recentFiles';
const MAX_RECENT_FILES = 12;

function config() {
  return vscode.workspace.getConfiguration('socketDcc');
}

function getSetting(name, fallback) {
  return config().get(name, fallback);
}

function getRecentFiles() {
  const files = getSetting(RECENT_FILES_SETTING, []);
  return Array.isArray(files) ? files.filter(file => typeof file === 'string' && file.trim()) : [];
}

async function setRecentFiles(files) {
  await config().update(RECENT_FILES_SETTING, files, vscode.ConfigurationTarget.Global);
}

function isPythonDocument(document) {
  return document && (document.languageId === 'python' || document.fileName.endsWith('.py'));
}

function log(message) {
  output.appendLine(message);
  output.show(true);
}

function showError(message) {
  log(`ERROR: ${message}`);
  vscode.window.showErrorMessage(message);
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function getNonce() {
  return Math.random().toString(36).slice(2, 15);
}

async function getToken() {
  const current = String(getSetting('token', '') || '').trim();
  if (current) {
    return current;
  }

  const token = await vscode.window.showInputBox({
    prompt: 'Enter the socket-dcc token',
    password: true,
    ignoreFocusOut: true
  });

  if (!token) {
    throw new Error('Token is required.');
  }

  await config().update('token', token, vscode.ConfigurationTarget.Global);
  return token;
}

async function sendCode(code) {
  const host = String(getSetting('host', '127.0.0.1') || '127.0.0.1');
  const port = Number(getSetting('port', 5050) || 5050);
  const token = await getToken();

  return await new Promise((resolve, reject) => {
    const client = net.createConnection({ host, port }, () => {
      client.write(`${JSON.stringify({ code, token })}\n`);
    });

    client.setEncoding('utf8');
    client.setTimeout(3000, () => client.destroy(new Error(`Timed out connecting to ${host}:${port}`)));

    let response = '';
    client.on('data', chunk => {
      response += chunk;
    });
    client.on('end', () => {
      const line = response.trim();
      if (!line) {
        reject(new Error('No response from server.'));
        return;
      }

      try {
        resolve(JSON.parse(line));
      } catch (error) {
        reject(new Error(`Invalid server response: ${error.message}`));
      }
    });
    client.on('error', reject);
  });
}

async function getActivePythonDocument() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    throw new Error('Open a Python file first.');
  }

  const document = editor.document;
  if (!isPythonDocument(document)) {
    throw new Error('The active file is not a Python file.');
  }

  if (document.isUntitled) {
    throw new Error('Save the file before sending it.');
  }

  return document;
}

async function saveActiveFilePath() {
  const document = await getActivePythonDocument();
  await config().update('savedFile', document.fileName, vscode.ConfigurationTarget.Global);
  log(`Saved file: ${document.fileName}`);
  vscode.window.showInformationMessage(`Saved ${document.fileName}`);
  SocketDccPanel.currentPanel?.refresh();
}

async function recordRecentFile(filePath) {
  const resolvedPath = path.resolve(filePath);
  const recentFiles = getRecentFiles().filter(item => item !== resolvedPath);
  recentFiles.unshift(resolvedPath);
  await setRecentFiles(recentFiles.slice(0, MAX_RECENT_FILES));
}

async function sendFile(filePath, { remember = true, saveAsCurrent = false } = {}) {
  const resolvedPath = path.resolve(filePath);
  try {
    await fs.access(resolvedPath);
  } catch {
    throw new Error(`File not found: ${resolvedPath}`);
  }

  const code = await fs.readFile(resolvedPath, 'utf8');
  const response = await sendCode(code);
  const outputMessage = String(response.output || '').trim();

  if (!response.ok) {
    throw new Error(outputMessage || 'Command failed.');
  }

  if (remember) {
    await recordRecentFile(resolvedPath);
  }

  if (saveAsCurrent) {
    await config().update('savedFile', resolvedPath, vscode.ConfigurationTarget.Global);
  }

  SocketDccPanel.currentPanel?.refresh();

  return outputMessage || `Sent ${resolvedPath}`;
}

async function sendActiveFile() {
  const document = await getActivePythonDocument();
  const outputMessage = await sendFile(document.fileName, { remember: true, saveAsCurrent: true });
  log(outputMessage);
  vscode.window.showInformationMessage(outputMessage);
}

async function runSavedFile() {
  const saved = String(getSetting('savedFile', '') || '').trim();
  if (!saved) {
    throw new Error('No saved file configured. Use "Save Active Python File" first.');
  }

  const outputMessage = await sendFile(saved, { remember: true, saveAsCurrent: false });
  log(outputMessage);
  vscode.window.showInformationMessage(outputMessage);
}

async function runRecentFile(filePath) {
  const outputMessage = await sendFile(filePath, { remember: true, saveAsCurrent: false });
  log(outputMessage);
  vscode.window.showInformationMessage(outputMessage);
}

async function updateConnectionSettings(settings) {
  await config().update('host', settings.host, vscode.ConfigurationTarget.Global);
  await config().update('port', Number(settings.port), vscode.ConfigurationTarget.Global);
  await config().update('token', settings.token, vscode.ConfigurationTarget.Global);
  await config().update('savedFile', settings.savedFile, vscode.ConfigurationTarget.Global);
  log('Updated socket-dcc settings.');
  vscode.window.showInformationMessage('socket-dcc settings saved.');
  SocketDccPanel.currentPanel?.refresh();
}

function getPanelState() {
  return {
    host: String(getSetting('host', '127.0.0.1') || '127.0.0.1'),
    port: Number(getSetting('port', 5050) || 5050),
    token: String(getSetting('token', '') || ''),
    savedFile: String(getSetting('savedFile', '') || ''),
    recentFiles: getRecentFiles()
  };
}

function renderRecentFiles(recentFiles) {
  if (!recentFiles.length) {
    return '<li class="empty">No files executed yet.</li>';
  }

  return recentFiles
    .map(filePath => {
      const fileName = path.basename(filePath);
      return `
        <li class="recent-item">
          <span class="recent-path">
            <strong>${escapeHtml(fileName)}</strong>
            <span>${escapeHtml(filePath)}</span>
          </span>
          <button type="button" data-path="${escapeHtml(filePath)}">Run</button>
        </li>`;
    })
    .join('');
}

function getPanelHtml(webview) {
  const state = getPanelState();
  const nonce = getNonce();

  return `<!DOCTYPE html>
  <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src ${webview.cspSource}; style-src 'nonce-${nonce}'; script-src 'nonce-${nonce}';" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>socket-dcc control panel</title>
      <style nonce="${nonce}">
        body {
          font-family: var(--vscode-font-family);
          color: var(--vscode-foreground);
          background: var(--vscode-editor-background);
          margin: 0;
          padding: 16px;
        }
        h1, h2 {
          margin: 0 0 12px;
        }
        .grid {
          display: grid;
          gap: 16px;
          max-width: 920px;
        }
        .card {
          padding: 16px;
          border: 1px solid var(--vscode-editorWidget-border);
          border-radius: 8px;
          background: var(--vscode-sideBar-background);
        }
        label {
          display: grid;
          gap: 6px;
          margin-bottom: 12px;
        }
        input {
          width: 100%;
          box-sizing: border-box;
          color: var(--vscode-input-foreground);
          background: var(--vscode-input-background);
          border: 1px solid var(--vscode-input-border);
          border-radius: 4px;
          padding: 8px 10px;
        }
        .row {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 12px;
        }
        .actions {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }
        button {
          color: var(--vscode-button-foreground);
          background: var(--vscode-button-background);
          border: none;
          border-radius: 4px;
          padding: 8px 12px;
          cursor: pointer;
        }
        button:hover {
          background: var(--vscode-button-hoverBackground);
        }
        ul {
          list-style: none;
          padding: 0;
          margin: 0;
          display: grid;
          gap: 10px;
        }
        .recent-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          padding: 10px 12px;
          border: 1px solid var(--vscode-editorWidget-border);
          border-radius: 6px;
        }
        .recent-path {
          display: grid;
          gap: 3px;
        }
        .recent-path span {
          opacity: 0.8;
          word-break: break-all;
        }
        .empty {
          opacity: 0.75;
        }
      </style>
    </head>
    <body>
      <div class="grid">
        <section class="card">
          <h1>socket-dcc</h1>
          <form id="settings-form">
            <div class="row">
              <label>
                <span>Host</span>
                <input id="host" name="host" value="${escapeHtml(state.host)}" />
              </label>
              <label>
                <span>Port</span>
                <input id="port" name="port" type="number" min="1" max="65535" value="${escapeHtml(state.port)}" />
              </label>
            </div>
            <label>
              <span>Token</span>
              <input id="token" name="token" type="password" value="${escapeHtml(state.token)}" />
            </label>
            <label>
              <span>Saved file</span>
              <input id="savedFile" name="savedFile" value="${escapeHtml(state.savedFile)}" />
            </label>
            <div class="actions">
              <button type="submit">Save settings</button>
            </div>
          </form>
        </section>

        <section class="card">
          <h2>Actions</h2>
          <div class="actions">
            <button type="button" data-action="sendActive">Send active file</button>
            <button type="button" data-action="saveActive">Save active file</button>
            <button type="button" data-action="runSaved">Run saved file</button>
          </div>
        </section>

        <section class="card">
          <h2>Recent files</h2>
          <ul id="recent-files">
            ${renderRecentFiles(state.recentFiles)}
          </ul>
        </section>
      </div>

      <script nonce="${nonce}">
        const vscode = acquireVsCodeApi();

        document.getElementById('settings-form').addEventListener('submit', event => {
          event.preventDefault();
          vscode.postMessage({
            type: 'saveSettings',
            settings: {
              host: document.getElementById('host').value,
              port: document.getElementById('port').value,
              token: document.getElementById('token').value,
              savedFile: document.getElementById('savedFile').value
            }
          });
        });

        document.querySelectorAll('[data-action]').forEach(button => {
          button.addEventListener('click', () => {
            vscode.postMessage({ type: button.dataset.action });
          });
        });

        document.getElementById('recent-files').addEventListener('click', event => {
          const button = event.target.closest('button[data-path]');
          if (!button) {
            return;
          }

          vscode.postMessage({
            type: 'runRecent',
            path: button.dataset.path
          });
        });
      </script>
    </body>
  </html>`;
}

class SocketDccPanel {
  static currentPanel;

  static createOrShow() {
    if (SocketDccPanel.currentPanel) {
      SocketDccPanel.currentPanel.panel.reveal(vscode.ViewColumn.One);
      SocketDccPanel.currentPanel.refresh();
      return;
    }

    const panel = vscode.window.createWebviewPanel(
      CONTROL_PANEL_VIEW_TYPE,
      'socket-dcc',
      vscode.ViewColumn.One,
      {
        enableScripts: true,
        retainContextWhenHidden: true
      }
    );

    SocketDccPanel.currentPanel = new SocketDccPanel(panel);
  }

  constructor(panel) {
    this.panel = panel;
    this.panel.webview.options = {
      enableScripts: true,
      retainContextWhenHidden: true
    };
    this.panel.onDidDispose(() => this.dispose());
    this.panel.webview.onDidReceiveMessage(message => this.handleMessage(message));
    this.refresh();
  }

  dispose() {
    SocketDccPanel.currentPanel = undefined;
  }

  refresh() {
    this.panel.webview.html = getPanelHtml(this.panel.webview);
  }

  async handleMessage(message) {
    try {
      switch (message.type) {
        case 'saveSettings':
          await updateConnectionSettings(message.settings);
          return;
        case 'sendActive':
          await sendActiveFile();
          return;
        case 'saveActive':
          await saveActiveFilePath();
          return;
        case 'runSaved':
          await runSavedFile();
          return;
        case 'runRecent':
          await runRecentFile(message.path);
          return;
        default:
          return;
      }
    } catch (error) {
      showError(error.message || String(error));
    }
  }
}

async function runCommand(action) {
  try {
    await action();
  } catch (error) {
    showError(error.message || String(error));
  }
}

function activate(context) {
  context.subscriptions.push(
    vscode.commands.registerCommand('socketDcc.openPanel', () => SocketDccPanel.createOrShow()),
    vscode.commands.registerCommand('socketDcc.sendActiveFile', () => runCommand(sendActiveFile)),
    vscode.commands.registerCommand('socketDcc.saveActiveFile', () => runCommand(saveActiveFilePath)),
    vscode.commands.registerCommand('socketDcc.runSavedFile', () => runCommand(runSavedFile)),
    output
  );
}

function deactivate() {}

module.exports = { activate, deactivate };
