"""Tests for Rich-to-Qt log formatting."""

import Qt
from rich.style import Style

from socket_dcc.core.gui.utils import _char_format


def test_char_format_preserves_rich_colors_and_emphasis() -> None:
    """Convert Rich color and emphasis attributes to Qt character formatting.

    Returns:
        None: This test asserts the generated Qt format properties.
    """
    char_format = _char_format(Style(color="red", bgcolor="black", bold=True, underline=True))

    assert char_format.foreground().color().name() == "#800000"
    assert char_format.background().color().name() == "#000000"
    assert char_format.fontWeight() > getattr(Qt.QtGui.QFont, "Normal")
    assert char_format.fontUnderline()
