"""Socket-based Python code execution server."""

import contextlib
import io
import json
import os
import runpy
import secrets
import socketserver
import threading
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ExecutionResponse:
    """Response from code execution on the server.

    Attributes:
        ok: Whether the execution succeeded.
        output: Output or error message from execution.
    """

    ok: bool
    output: str


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
        self.auth_token = auth_token or os.environ.get("SOCKET_DCC_TOKEN") or secrets.token_hex(16)
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
                except (KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                    self._send(ExecutionResponse(False, f"Invalid request: {exc}"))
                    return

                if token != server.auth_token:
                    self._send(ExecutionResponse(False, "Authentication failed"))
                    return

                if server._code_received_callback is not None:
                    server._code_received_callback(code)

                response = server.execute(code)
                self._send(response)

            def _send(self, response: ExecutionResponse) -> None:
                payload = json.dumps({"ok": response.ok, "output": response.output}) + "\n"
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

    def execute(self, code: str) -> ExecutionResponse:
        """Execute Python code or file in a protected environment.

        If code is a valid file path, executes it as a module using runpy.
        Otherwise, executes it as Python code.

        Args:
            code: Python code to execute or path to a Python file.

        Returns:
            ExecutionResponse: Execution status and output/error message.
        """
        with self._lock:
            stdout = io.StringIO()
            stderr = io.StringIO()

            # Check if code is a file path
            is_file = False
            file_path = None
            try:
                file_path = Path(code.strip())
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
                            exec(code, self._namespace, self._namespace)
                        else:
                            result = eval(compiled, self._namespace, self._namespace)
                            if result is not None:
                                print(repr(result))
            except Exception:
                traceback.print_exc(file=stderr)
                output = stdout.getvalue() + stderr.getvalue()
                output = output.rstrip()
                self._log(output)
                return ExecutionResponse(False, output)

            output = (stdout.getvalue() + stderr.getvalue()).rstrip()
            self._log(output or "Command executed.")
            return ExecutionResponse(True, output or "Command executed.")
