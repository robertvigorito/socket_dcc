from __future__ import annotations

import contextlib
import io
import json
import secrets
import socketserver
import threading
import traceback
from dataclasses import dataclass
from typing import Callable


@dataclass(slots=True)
class ExecutionResponse:
    ok: bool
    output: str


class SocketExecutionServer:
    def __init__(
        self,
        log_callback: Callable[[str], None] | None = None,
        status_callback: Callable[[str], None] | None = None,
    ) -> None:
        self._server: socketserver.ThreadingTCPServer | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self.auth_token = secrets.token_hex(16)
        self._namespace: dict[str, object] = {
            "__name__": "__socket_dcc__",
            "__builtins__": __builtins__,
        }
        self._log_callback = log_callback
        self._status_callback = status_callback

    def _log(self, message: str) -> None:
        if message and self._log_callback is not None:
            self._log_callback(message)

    def _status(self, message: str) -> None:
        if self._status_callback is not None:
            self._status_callback(message)

    def start(self, host: str, port: int) -> None:
        if self._server is not None:
            return

        server = self

        class ReusableTCPServer(socketserver.ThreadingTCPServer):
            allow_reuse_address = True

        class Handler(socketserver.StreamRequestHandler):
            def handle(self) -> None:  # noqa: D401
                raw = self.rfile.readline()
                if not raw:
                    return
                try:
                    request = json.loads(raw.decode("utf-8"))
                    code = str(request["code"])
                    token = str(request["token"])
                except Exception as exc:  # pragma: no cover - defensive
                    self._send(ExecutionResponse(False, f"Invalid request: {exc}"))
                    return

                if token != server.auth_token:
                    self._send(ExecutionResponse(False, "Authentication failed"))
                    return

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
        if self._server is None:
            return
        self._server.shutdown()
        self._server.server_close()
        self._server = None
        self._thread = None
        self._status("Server stopped")

    def execute(self, code: str) -> ExecutionResponse:
        with self._lock:
            stdout = io.StringIO()
            stderr = io.StringIO()
            try:
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    try:
                        compiled = compile(code, "<socket-dcc>", "eval")
                    except SyntaxError:
                        exec(code, self._namespace, self._namespace)
                    else:
                        result = eval(compiled, self._namespace, self._namespace)
                        if result is not None:
                            print(repr(result))
            except Exception as exc:
                traceback.print_exc(file=stderr)
                output = stdout.getvalue() + stderr.getvalue()
                output = output.rstrip()
                self._log(output)
                return ExecutionResponse(False, output)

            output = (stdout.getvalue() + stderr.getvalue()).rstrip()
            self._log(output or "Command executed.")
            return ExecutionResponse(True, output or "Command executed.")
