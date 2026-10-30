"""Socket-based Python code execution server."""

import ast
import contextlib
import io
import json
import os
import platform
import runpy
import socketserver
import threading
import traceback
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

from socket_dcc.defaults import get_default_settings

_LAST_DISTRO: list[str] = []


@dataclass(slots=True)
class ExecutionResponse:
    """Response from code execution on the server.

    Attributes:
        ok: Whether the execution succeeded.
        output: Output or error message from execution.
        raised: Whether the executed code raised an exception.
    """

    ok: bool
    output: str
    raised: bool = False


def _normalize_traceback_paths(output: str) -> str:
    """Use forward slashes in traceback frame paths, including WSL UNC paths.

    Args:
        output: Formatted Python traceback text.

    Returns:
        str: Traceback text with Python frame paths normalized to forward slashes.
    """
    normalized_lines: list[str] = []
    for line in output.splitlines(keepends=True):
        marker = line.find('File "')
        quote = '"'
        if marker == -1:
            marker = line.find("File '")
            quote = "'"
        if marker == -1:
            normalized_lines.append(line)
            continue

        path_start = marker + len("File ")
        path_end = line.find(f"{quote}, line ", path_start + 1)
        if path_end == -1:
            normalized_lines.append(line)
            continue

        path_literal = line[path_start : path_end + 1]
        try:
            path = ast.literal_eval(path_literal)
        except (SyntaxError, ValueError):
            normalized_lines.append(line)
            continue
        if not isinstance(path, str):
            normalized_lines.append(line)
            continue

        normalized_path = path.replace("\\", "/")
        normalized_lines.append(f"{line[:marker]}File {normalized_path!r}{line[path_end + 1 :]}")
    return "".join(normalized_lines)


def _is_wsl() -> bool:
    """Check whether the current process is running inside WSL.

    Returns:
        bool: True when running inside WSL.
    """
    return "microsoft" in platform.release().lower() or bool(os.environ.get("WSL_DISTRO_NAME"))


def _wsl_distros() -> Iterator[str]:
    """Lazily yield candidate WSL distro names, most likely first.

    The slow WSL share listing is only reached when the cheaper candidates are exhausted.

    Returns:
        Iterator[str]: Distros from the last match, environment, this module's UNC location, ``Ubuntu``, then the share.
    """
    if _LAST_DISTRO:
        yield _LAST_DISTRO[0]
    env_distro = os.environ.get("WSL_DISTRO_NAME")
    if env_distro:
        yield env_distro
    parts = [part for part in __file__.replace("\\", "/").split("/") if part]
    if len(parts) > 1 and parts[0].lower() in {"wsl.localhost", "wsl$"}:
        yield parts[1]
    yield "Ubuntu"
    try:
        yield from os.listdir("//wsl.localhost")
    except OSError:
        return


def _resolve_run_path(path: str) -> str:
    """Convert a WSL-style path to an existing Windows path when the server is not inside WSL.

    ``/mnt/c/dir/file.py`` becomes ``C:/dir/file.py``. Other absolute POSIX paths are tried as
    ``//wsl.localhost/<distro>/...`` for each candidate distro; the first existing file wins and its
    distro is remembered for later calls.

    Args:
        path: Path received from the client.

    Returns:
        str: The first existing candidate, otherwise the ``Ubuntu`` UNC candidate.
    """
    if os.name != "nt" or _is_wsl() or not path.startswith("/"):
        return path
    parts = path.split("/")
    if len(parts) > 2 and parts[1] == "mnt" and len(parts[2]) == 1 and parts[2].isalpha():
        return f"{parts[2].upper()}:/{'/'.join(parts[3:])}"
    for distro in _wsl_distros():
        candidate = f"//wsl.localhost/{distro}{path}"
        if Path(candidate).is_file():
            _LAST_DISTRO[:] = [distro]
            return candidate
    return f"//wsl.localhost/Ubuntu{path}"


class SocketExecutionServer:
    """Server for executing Python code sent over a socket connection.

    Attributes:
        auth_token: Authentication token required for code execution.
    """

    def __init__(
        self,
        log_callback: Callable[[str], None] | None = None,
        status_callback: Callable[[str], None] | None = None,
        code_received_callback: Callable[[str], None] | None = None,
        auth_token: str | None = None,
    ) -> None:
        """Initialize the socket execution server.

        Args:
            log_callback: Optional callback for logging output.
            status_callback: Optional callback for server status updates.
            code_received_callback: Optional callback when code is received.
            auth_token: Optional authentication token; generates one if not provided.
        """
        self._server: socketserver.ThreadingTCPServer | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self.auth_token = auth_token or os.environ.get("SOCKET_DCC_TOKEN") or get_default_settings()[1]
        self._namespace: dict[str, object] = {
            "__name__": "__socket_dcc__",
            "__builtins__": __builtins__,
        }
        self._log_callback = log_callback
        self._status_callback = status_callback
        self._code_received_callback = code_received_callback

    @property
    def is_running(self) -> bool:
        """Check if the server is currently running.

        Returns:
            True if the server is running, False otherwise.
        """
        return self._server is not None

    def _log(self, message: str) -> None:
        """Log a message using the log callback.

        Args:
            message: Message to log.
        """
        if message and self._log_callback is not None:
            self._log_callback(message)

    def _status(self, message: str) -> None:
        """Emit a status update using the status callback.

        Args:
            message: Status message to emit.
        """
        if self._status_callback is not None:
            self._status_callback(message)

    def start(self, host: str, port: int) -> None:
        """Start the socket server listening on the specified host and port.

        Args:
            host: Hostname or IP address to bind to.
            port: Port number to listen on.
        """
        if self._server is not None:
            return

        server = self

        class ReusableTCPServer(socketserver.ThreadingTCPServer):
            allow_reuse_address = True

        class Handler(socketserver.StreamRequestHandler):
            def handle(self) -> None:
                raw = self.rfile.readline()
                if not raw:
                    return
                try:
                    request = json.loads(raw.decode("utf-8"))
                    code = str(request["code"])
                    token = str(request["token"])
                    mode = request.get("mode", "code")
                    wait = request.get("wait", True)
                except (KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                    self._send(ExecutionResponse(False, f"Invalid request: {exc}"))
                    return

                if not isinstance(mode, str) or mode not in {"code", "path"}:
                    self._send(ExecutionResponse(False, f"Invalid execution mode: {mode}"))
                    return
                if not isinstance(wait, bool):
                    self._send(ExecutionResponse(False, "Invalid wait setting"))
                    return

                if token != server.auth_token:
                    self._send(ExecutionResponse(False, "Authentication failed"))
                    return

                if server._code_received_callback is not None:
                    server._code_received_callback(code)

                if not wait:
                    self._send(ExecutionResponse(True, "Execution started."))
                response = server.execute(code, run_path=mode == "path")
                if wait:
                    self._send(response)

            def _send(self, response: ExecutionResponse) -> None:
                payload = json.dumps({"ok": response.ok, "output": response.output, "raised": response.raised}) + "\n"
                self.wfile.write(payload.encode("utf-8"))
                self.wfile.flush()

        self._server = ReusableTCPServer((host, port), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        self._status(f"Listening on {host}:{port}")

    def stop(self) -> None:
        """Stop the socket server."""
        if self._server is None:
            return
        self._server.shutdown()
        self._server.server_close()
        self._server = None
        self._thread = None
        self._status("Server stopped")

    def execute(self, code: str, run_path: bool = False) -> ExecutionResponse:
        """Execute Python code or file in a protected environment.

        If code is a valid file path, executes it as a module using runpy.
        Otherwise, executes it as Python code.

        Args:
            code: Python code to execute or path to a Python file.
            run_path: Whether to treat the payload as a path without code detection.

        Returns:
            ExecutionResponse: Execution status and output/error message.
        """
        with self._lock:
            stdout = io.StringIO()
            stderr = io.StringIO()

            file_path: Path | None = None
            is_file = run_path
            if run_path:
                file_path = Path(_resolve_run_path(code.strip()))
            else:
                try:
                    stripped = code.strip()
                    file_path = Path(_resolve_run_path(stripped) if "\n" not in stripped else stripped)
                    is_file = file_path.exists() and file_path.is_file() and file_path.suffix == ".py"
                except (OSError, ValueError):
                    # OSError: file name too long (code is actually code, not a path)
                    # ValueError: invalid path characters
                    pass

            try:
                with (
                    contextlib.redirect_stdout(stdout),
                    contextlib.redirect_stderr(stderr),
                ):
                    if is_file and file_path is not None:
                        # Execute as a file module
                        runpy.run_path(str(file_path), run_name="__main__")
                    else:
                        # Execute as code snippet
                        try:
                            compiled = compile(code, "<socket-dcc>", "eval")
                        except SyntaxError:
                            compiled = None
                        if compiled is None:
                            compiled = compile(code, "<socket-dcc>", "exec")
                            exec(compiled, self._namespace, self._namespace)
                        else:
                            result = eval(compiled, self._namespace, self._namespace)
                            if result is not None:
                                print(repr(result))
            except Exception:
                output = traceback.format_exc()
                stderr.write(_normalize_traceback_paths(output))
                output = (stdout.getvalue() + stderr.getvalue()).rstrip()
                self._log(output)
                return ExecutionResponse(False, output, raised=True)

            output = (stdout.getvalue() + stderr.getvalue()).rstrip()
            self._log(output or "Command executed.")
            return ExecutionResponse(True, output or "Command executed.")
