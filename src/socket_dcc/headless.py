"""Run the socket server in a headless Python or Nuke interpreter."""

import errno
import queue
import threading
from collections.abc import Callable

from socket_dcc.defaults import DEFAULT_HOST, get_default_host, get_default_settings
from socket_dcc.server import ExecutionResponse, SocketExecutionServer

ExecutionTask = Callable[[], ExecutionResponse]
PendingExecution = tuple[ExecutionTask, threading.Event, list[ExecutionResponse | BaseException]]


def run_headless_server(
    host: str | None = None,
    port: int | None = None,
    token: str | None = None,
    stop_event: threading.Event | None = None,
) -> SocketExecutionServer:
    """Run the socket server without creating a GUI, executing requests on this thread.

    This is suitable for a regular Python process or a Nuke terminal interpreter. The
    calling thread services execution requests so Nuke API calls do not run on socket
    worker threads. Pass a stop event when embedding this function; otherwise Ctrl+C
    stops the server.

    Args:
        host: Bind address. Defaults to the shared host resolver.
        port: Listening port. Defaults to the shared socket-dcc setting.
        token: Authentication token. Defaults to the shared socket-dcc setting.
        stop_event: Optional event that requests a clean shutdown when set.

    Returns:
        SocketExecutionServer: The stopped server instance, useful for inspection in tests.
    """
    bind_host = host or get_default_host()
    if port is None or token is None:
        default_port, default_token = get_default_settings()
        bind_port = default_port if port is None else port
        auth_token = default_token if token is None else token
    else:
        bind_port = port
        auth_token = token
    if not auth_token:
        raise ValueError("token cannot be empty")

    shutdown_event = threading.Event()
    requested_stop = stop_event if stop_event is not None else threading.Event()
    execution_queue: queue.Queue[PendingExecution] = queue.Queue()

    def dispatch_to_calling_thread(task: ExecutionTask) -> ExecutionResponse:
        completed = threading.Event()
        result: list[ExecutionResponse | BaseException] = []
        execution_queue.put((task, completed, result))
        completed.wait()
        outcome = result[0]
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    def log_output(message: str) -> None:
        """Print execution output in the headless interpreter.

        Args:
            message: Captured output or error text from an executed request.

        Returns:
            None: Writes the message to standard output.
        """
        print(message, flush=True)

    server = SocketExecutionServer(
        log_callback=log_output,
        auth_token=auth_token,
        execution_dispatcher=dispatch_to_calling_thread,
        shutdown_callback=shutdown_event.set,
    )
    try:
        server.start(bind_host, bind_port)
    except OSError as exc:
        if host is not None or bind_host == DEFAULT_HOST or exc.errno != errno.EADDRNOTAVAIL:
            raise
        print(
            f"Default host {bind_host} is not assigned to this machine; retrying on {DEFAULT_HOST}. "
            f"Use --host {DEFAULT_HOST} for local clients, or a valid local address for network access.",
            flush=True,
        )
        bind_host = DEFAULT_HOST
        server.start(bind_host, bind_port)
    print(f"socket-dcc headless server listening on {bind_host}:{bind_port}", flush=True)

    try:
        while not requested_stop.is_set() and not shutdown_event.is_set():
            try:
                task, completed, result = execution_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            try:
                result.append(task())
            except BaseException as exc:
                result.append(exc)
            finally:
                completed.set()
                execution_queue.task_done()
    except KeyboardInterrupt:
        print("Stopping socket-dcc headless server...", flush=True)
    finally:
        server.stop()
    return server
