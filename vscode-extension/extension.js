const fs = require('fs/promises');
const net = require('net');
const vscode = require('vscode');

const output = vscode.window.createOutputChannel('socket-dcc');

function config() {
  return vscode.workspace.getConfiguration('socketDcc');
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

async function getToken() {
  const current = String(config().get('token', '') || '').trim();
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
  const host = String(config().get('host', '127.0.0.1') || '127.0.0.1');
  const port = Number(config().get('port', 5050) || 5050);
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

  return document;
}

async function saveActiveFilePath() {
  const document = await getActivePythonDocument();
  await config().update('savedFile', document.fileName, vscode.ConfigurationTarget.Global);
  log(`Saved file: ${document.fileName}`);
  vscode.window.showInformationMessage(`Saved ${document.fileName}`);
}

async function sendActiveFile() {
  const document = await getActivePythonDocument();
  await config().update('savedFile', document.fileName, vscode.ConfigurationTarget.Global);
  const response = await sendCode(document.getText());
  const outputMessage = String(response.output || '').trim();
  if (response.ok) {
    log(outputMessage || `Sent ${document.fileName}`);
    vscode.window.showInformationMessage(outputMessage || `Sent ${document.fileName}`);
    return;
  }

  throw new Error(outputMessage || 'Command failed.');
}

async function runSavedFile() {
  const saved = String(config().get('savedFile', '') || '').trim();
  if (!saved) {
    throw new Error('No saved file configured. Use "Save Active Python File" first.');
  }

  const code = await fs.readFile(saved, 'utf8');
  const response = await sendCode(code);
  const outputMessage = String(response.output || '').trim();
  if (response.ok) {
    log(outputMessage || `Sent ${saved}`);
    vscode.window.showInformationMessage(outputMessage || `Sent ${saved}`);
    return;
  }

  throw new Error(outputMessage || 'Command failed.');
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
    vscode.commands.registerCommand('socketDcc.sendActiveFile', () => runCommand(sendActiveFile)),
    vscode.commands.registerCommand('socketDcc.saveActiveFile', () => runCommand(saveActiveFilePath)),
    vscode.commands.registerCommand('socketDcc.runSavedFile', () => runCommand(runSavedFile)),
    output
  );
}

function deactivate() {}

module.exports = { activate, deactivate };
