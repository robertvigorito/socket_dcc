"""Tests for the canonical GUI package and compatibility entry point."""

import sys
from types import SimpleNamespace
from unittest.mock import Mock

import Qt


def test_gui_compatibility_entry_point_uses_canonical_window() -> None:
    """Verify legacy GUI imports resolve to the single canonical window class.

    Returns:
        None: This test compares the compatibility export with the canonical class.
    """
    from socket_dcc.core.gui import MainWindow as canonical_window
    from socket_dcc.gui import MainWindow as compatibility_window

    assert compatibility_window is canonical_window


def test_nuke_panel_window_uses_nuke_execution_callbacks(monkeypatch) -> None:
    """Verify panel construction injects Nuke's main-thread execution hooks.

    Args:
        monkeypatch: Pytest fixture used to provide a fake Nuke host module.

    Returns:
        None: Asserts the registered panel's server uses Nuke's dispatcher and output callback.
    """
    app = Qt.QtWidgets.QApplication.instance() or Qt.QtWidgets.QApplication([])
    script_editor = Mock()
    nuke_module = SimpleNamespace(
        executeInMainThreadWithResult=lambda task: task(),
        tprint=script_editor,
    )
    monkeypatch.setitem(sys.modules, "nuke", nuke_module)

    from socket_dcc.interface import NukeMainWindow

    window = NukeMainWindow()
    expected = object()

    assert window.server._execution_dispatcher(lambda: expected) is expected
    assert window.server._script_editor_callback is script_editor

    window.close()
    app.processEvents()
