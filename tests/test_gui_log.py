"""Tests for Rich-to-Qt log formatting."""

import Qt
from rich.console import Console
from rich.style import Style

from socket_dcc.core.gui.utils import _char_format, _render_log_message


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


def test_traceback_log_uses_high_contrast_and_emphasizes_exception() -> None:
    """Keep traceback text readable and highlight its final exception line.

    Returns:
        None: This test asserts traceback text and its Qt formatting.
    """
    message = 'Traceback (most recent call last):\n  File "<script>", line 1\nValueError: failed'
    rendered = _render_log_message(message)

    assert rendered.plain == message
    console = Console()
    body_format = _char_format(rendered.get_style_at_offset(console, 0))
    exception_format = _char_format(rendered.get_style_at_offset(console, len(message) - 1))
    assert body_format.foreground().color().name() == "#f2f2f2"
    assert exception_format.foreground().color().name() == "#ff6b6b"
    assert exception_format.fontWeight() > getattr(Qt.QtGui.QFont, "Normal")
