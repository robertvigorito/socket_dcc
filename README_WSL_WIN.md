# socket-dcc: WSL 2 and Windows Host Integration

This guide explains how to connect your Windows PC and WSL 2 so you can run socket-dcc across both systems.

Use `socket-dcc code` to send inline Python or the contents of a client-side `.py` file. Use
`socket-dcc path` when the Python file is accessible to the server process and should be executed there.

## Overview

WSL 2 uses Hyper-V virtualization, creating a separate virtual network for the Linux environment. To communicate between Windows and WSL, you need to:

1. Identify the correct IP addresses
2. Configure the server to listen on the appropriate interface
3. Connect clients to the correct host/port combination

## Finding Your IP Addresses

### Windows Host IP (as seen from WSL)

Inside WSL terminal:
```bash
cat /etc/resolv.conf | grep nameserver
# Output: nameserver 172.31.224.1 (example)
```

This is your Windows host IP. Note it for connecting from WSL.

### WSL IP (as seen from Windows)

In PowerShell on Windows:
```powershell
wsl hostname -I
# Output: 172.31.224.5 (example)
```

This is your WSL IP. Note it for connecting from Windows.

### Verify with Get Host Info

Click "Get Host Info" in the GUI to see:
- **Hostname**: Your machine name
- **Local IP**: The internal network IP
- **Localhost**: 127.0.0.1 (loopback, local-only)

## Setup Scenarios

### Scenario 1: GUI on Windows, CLI in WSL

**Windows side (GUI server):**
1. Launch socket-dcc GUI
2. In the "Host" field, change from `127.0.0.1` to `0.0.0.0`
3. Use the generated port shown in the GUI, or choose a port and set `SOCKET_DCC_PORT` for both processes
4. Click "Start Server"
5. Note the token displayed

**WSL side (CLI client):**
```bash
# Replace 172.31.224.1 with your Windows IP from /etc/resolv.conf
socket-dcc code /path/to/script.py --host 172.31.224.1 --port 5050 --token YOUR_TOKEN
```

To run a script stored in WSL using the Windows GUI server, use `path --wsl` to convert the Linux path with
`wslpath` before sending it:

```bash
socket-dcc path /path/to/script.py --wsl --host 172.31.224.1 --port 5050 --token YOUR_TOKEN
```

Or send code directly:
```bash
socket-dcc code 'print("Hello from WSL")' --host 172.31.224.1 --port 5050 --token YOUR_TOKEN
```

### Scenario 2: GUI in WSL, CLI on Windows

**WSL side (GUI server):**
1. Launch socket-dcc GUI in WSL
2. In the "Host" field, change from `127.0.0.1` to `0.0.0.0`
3. Use the generated port shown in the GUI, or choose a port and set `SOCKET_DCC_PORT` for both processes
4. Click "Start Server"
5. Note the token and WSL IP

**Windows side (CLI client):**
```powershell
# Replace 172.31.224.5 with your WSL IP from 'wsl hostname -I'
socket-dcc code C:\path\to\script.py --host 172.31.224.5 --port 5050 --token YOUR_TOKEN
```

Or send code directly:
```powershell
socket-dcc code 'print("Hello from Windows")' --host 172.31.224.5 --port 5050 --token YOUR_TOKEN
```

## Important: Binding to 0.0.0.0

When connecting across the Windows/WSL boundary:

- ❌ **DON'T use `127.0.0.1`** - This is loopback only, won't accept external connections
- ✅ **DO use `0.0.0.0`** - Listens on all network interfaces, including the WSL virtual network
- ✅ **DO use `localhost`** - If both client and server are on the same machine (not cross-boundary)

## Setting Environment Variables

Store your connection details in `.env`. On first launch, socket-dcc generates a port and token and saves
them as `SOCKET_DCC_PORT` and `SOCKET_DCC_TOKEN`. For client/server use across Windows and WSL, copy
the same values to both environments:

```bash
# In your project root
SOCKET_DCC_TOKEN=your_secure_token_here
SOCKET_DCC_PORT=your_selected_port
```

Or temporarily in terminal:

```bash
# WSL
export SOCKET_DCC_TOKEN=your_token
socket-dcc code /path/to/script.py --host 172.31.224.1 --port 5050

# Windows PowerShell
$env:SOCKET_DCC_TOKEN="your_token"
socket-dcc code C:\path\to\script.py --host 172.31.224.5 --port 5050
```

## Firewall Considerations

### Windows Firewall

If you can't connect from WSL to Windows:
1. Open Windows Defender Firewall
2. Click "Allow an app through firewall"
3. Find Python or your socket-dcc app, ensure it's allowed for Private networks
4. Add port 5050 (or your chosen port) if needed

### WSL Firewall

WSL 2 typically allows inbound connections from Windows without additional configuration. If you encounter issues:

```bash
# Check WSL firewall status
sudo ufw status

# Allow incoming on port 5050 if needed
sudo ufw allow 5050
```

## Troubleshooting

### Connection Refused

- **Problem**: `[red]✗ Connection Failed[/red]: Could not connect to server`
- **Solution**: 
  - Verify server is running on correct IP (use `0.0.0.0` for cross-boundary)
  - Check correct IP address (confirm with `Get Host Info`)
  - Ensure port matches the generated port shown in the GUI
  - Check firewall isn't blocking the port

### File Name Too Long Error

If you see `OSError: [Errno 36] File name too long`:
- The server tried to interpret long code strings as file paths
- This is automatically handled; the code will execute normally
- No action needed

### Token Mismatch

- **Problem**: `Authentication failed`
- **Solution**: Ensure both client and server use the same token
  - Check `.env` file has correct `SOCKET_DCC_TOKEN`
  - Token is displayed in GUI after server starts
  - Copy the exact token, no extra spaces

### IP Address Changed

WSL IP can change when you restart. If connection fails:
1. Run `wsl hostname -I` on Windows to get new WSL IP
2. Or check `cat /etc/resolv.conf` in WSL to get new Windows IP
3. Update the host field in GUI or CLI command

## Quick Reference Table

| Scenario | Host (GUI) | Client Host | Notes |
|----------|-----------|------------|-------|
| Local only (same machine) | 127.0.0.1 | 127.0.0.1 | Fastest, most secure |
| Windows GUI + WSL CLI | 0.0.0.0 | Windows IP | Use IP from `/etc/resolv.conf` |
| WSL GUI + Windows CLI | 0.0.0.0 | WSL IP | Use IP from `wsl hostname -I` |
| Both on same network | Your local IP | Your local IP | Requires firewall rules |

## Example: Complete Workflow

### Setup
```bash
# 1. Find Windows IP from WSL
cat /etc/resolv.conf | grep nameserver
# Output: nameserver 172.31.224.1

# 2. In Windows, start socket-dcc GUI
# - Set Host to: 0.0.0.0
# - Port: 5050
# - Click "Start Server"
# - Copy the token shown
```

### Test
```bash
# 3. From WSL, send a test command
export SOCKET_DCC_TOKEN="your_token_here"
socket-dcc code 'print("Success!")' --host 172.31.224.1 --port 5050

# 4. Check output in Windows GUI or terminal
```

### Send a File
```bash
# 5. From WSL, send a Python file
socket-dcc code ~/my_script.py --host 172.31.224.1 --port 5050 --token your_token_here
```
