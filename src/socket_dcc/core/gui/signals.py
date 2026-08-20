"""Signal handling for GUI."""

import signal

from rich.console import Console

console = Console()

# Global flag for signal detection
_signal_received = False


def _signal_handler(signum: int, frame: object) -> None:
    """Handle termination signals by setting a global flag.

    Args:
        signum: Signal number.
        frame: Current stack frame.
    """
    global _signal_received
    _signal_received = True
    if signum == signal.SIGTSTP:
        console.print("[yellow]Ctrl+Z detected[/yellow]")
    elif signum == signal.SIGINT:
        console.print("[yellow]Ctrl+C detected[/yellow]")


def setup_signal_handlers() -> None:
    """Set up signal handlers for the GUI."""
    signal.signal(signal.SIGTSTP, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)


def signal_received() -> bool:
    """Check if a termination signal was received.

    Returns:
        True if Ctrl+Z or Ctrl+C was pressed, False otherwise.
    """
    return _signal_received
