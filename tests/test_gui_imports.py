"""Tests for the canonical GUI package and compatibility entry point."""


def test_gui_compatibility_entry_point_uses_canonical_window() -> None:
    """Verify legacy GUI imports resolve to the single canonical window class.

    Returns:
        None: This test compares the compatibility export with the canonical class.
    """
    from socket_dcc.core.gui import MainWindow as canonical_window
    from socket_dcc.gui import MainWindow as compatibility_window

    assert compatibility_window is canonical_window
