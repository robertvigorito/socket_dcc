"""Tests for GUI signal handling."""

import signal

from socket_dcc.core.gui import signals


def test_setup_signal_handlers_without_sigtstp(monkeypatch) -> None:
    """Register SIGINT when the embedded Python build lacks SIGTSTP.

    Args:
        monkeypatch: Pytest fixture for temporarily changing the signal module.

    Returns:
        None: This test asserts the supported handlers are registered.
    """
    registered_signals = []
    monkeypatch.delattr(signal, "SIGTSTP", raising=False)
    monkeypatch.setattr(signal, "signal", lambda signum, handler: registered_signals.append(signum))

    signals.setup_signal_handlers()

    assert registered_signals == [signal.SIGINT]


def test_signal_handler_without_sigtstp(monkeypatch) -> None:
    """Handle SIGINT when the embedded Python build lacks SIGTSTP.

    Args:
        monkeypatch: Pytest fixture for temporarily changing the signal module.

    Returns:
        None: This test asserts SIGINT is handled without an attribute error.
    """
    monkeypatch.delattr(signal, "SIGTSTP", raising=False)
    signals._signal_received = False

    signals._signal_handler(signal.SIGINT, None)

    assert signals.signal_received()
