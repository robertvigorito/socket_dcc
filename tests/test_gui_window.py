"""Tests for the GUI's optional log panel."""

from unittest.mock import Mock

import pytest
import Qt

import socket_dcc.core.gui.window as gui_window
from socket_dcc.core.gui.window import MainWindow


def test_log_and_code_panes_are_visible_by_default() -> None:
    """Verify log and submitted-code panes are visible when the GUI opens.

    Returns:
        None: This test asserts the default menu and pane states.
    """
    app = Qt.QtWidgets.QApplication.instance() or Qt.QtWidgets.QApplication([])
    window = MainWindow()

    assert window.show_log_action.isChecked()
    assert window.show_code_action.isChecked()
    assert not window.log_output.isHidden()
    assert not window.submitted_code.isHidden()
    assert window.token_input.text()
    assert "#d99b2b" in window.connect_button.styleSheet()
    assert window.auto_disconnect_action.isCheckable()
    assert window.auto_close_action.isCheckable()

    window.show_log_action.setChecked(False)
    assert window.log_output.isHidden()
    window.show_log_action.setChecked(True)
    assert not window.log_output.isHidden()

    window.close()
    app.processEvents()


def test_disconnect_logs_reason_and_resets_connection_controls() -> None:
    """Verify disconnect records a message and restores editable controls.

    Returns:
        None: This test asserts the log message and disconnected UI state.
    """
    app = Qt.QtWidgets.QApplication.instance() or Qt.QtWidgets.QApplication([])
    window = MainWindow()
    window.server = Mock()
    window.server.is_running = True
    window.server.stop.side_effect = lambda: setattr(window.server, "is_running", False)
    window.token_input.setEnabled(False)
    window.port_input.setEnabled(False)
    window.connect_button.setText("Disconnect")

    window._disconnect_server("[yellow]Disconnected from the socket server.[/yellow]")

    assert "Disconnected from the socket server." in window.log_output.toPlainText()
    assert window.connect_button.text() == "Connect"
    assert window.token_input.isEnabled()
    assert window.port_input.isEnabled()
    assert window.status_value.text() == "Idle"
    window.close()
    app.processEvents()


def test_connect_persists_active_port_and_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify GUI connection defaults are synchronized for local clients.

    Args:
        monkeypatch: Pytest fixture for replacing server and persistence behavior.

    Returns:
        None: Asserts the active port and token are persisted on connect.
    """
    app = Qt.QtWidgets.QApplication.instance() or Qt.QtWidgets.QApplication([])
    window = MainWindow()
    port = 45678
    token = "gui-selected-token"
    window.port_input.setValue(port)
    window.token_input.setText(token)
    monkeypatch.setattr(window.server, "start", Mock())
    persist_settings = Mock()
    monkeypatch.setattr(gui_window, "save_default_settings", persist_settings)

    window._toggle_connection()

    persist_settings.assert_called_once_with(port, token)
    assert window.status_value.text() == "Connected"
    window.close()
    app.processEvents()


def test_copy_token_button_copies_current_token() -> None:
    """Verify the token copy button writes the current value to the clipboard.

    Returns:
        None: Asserts the clipboard contents and button feedback.
    """
    app = Qt.QtWidgets.QApplication.instance() or Qt.QtWidgets.QApplication([])
    window = MainWindow()
    token = "token-to-copy"
    window.token_input.setText(token)

    window.copy_token_button.click()

    assert Qt.QtWidgets.QApplication.clipboard().text() == token
    assert not window.copy_token_button.text()
    assert not window.copy_token_button.icon().isNull()
    assert window.copy_token_button.height() == window.token_input.height()
    assert window.copy_token_button.toolTip() == "Token copied"
    window.close()
    app.processEvents()


def test_copy_host_button_copies_displayed_host() -> None:
    """Verify the host copy button writes the displayed host to the clipboard.

    Returns:
        None: Asserts the clipboard contents and button feedback.
    """
    app = Qt.QtWidgets.QApplication.instance() or Qt.QtWidgets.QApplication([])
    window = MainWindow(host="192.168.1.20")

    window.copy_host_button.click()

    assert Qt.QtWidgets.QApplication.clipboard().text() == "192.168.1.20"
    assert not window.copy_host_button.text()
    assert not window.copy_host_button.icon().isNull()
    assert window.copy_host_button.toolTip() == "Host copied"
    window.close()
    app.processEvents()


def test_idle_timeout_dialog_is_borderless() -> None:
    """Verify the idle timeout input uses a frameless window.

    Returns:
        None: This test asserts the dialog window flags.
    """
    app = Qt.QtWidgets.QApplication.instance() or Qt.QtWidgets.QApplication([])
    window = MainWindow()
    dialog = window._create_idle_timeout_dialog()

    assert dialog.windowFlags() & getattr(Qt.QtCore.Qt, "FramelessWindowHint")

    window.close()
    app.processEvents()


def test_submitted_code_can_append_replace_and_clear(capsys) -> None:
    """Verify submitted code display supports append, replace, and clear.

    Args:
        capsys: Pytest fixture used to capture and inspect terminal output.

    Returns:
        None: This test asserts the submitted-code view contents.
    """
    app = Qt.QtWidgets.QApplication.instance() or Qt.QtWidgets.QApplication([])
    window = MainWindow()

    window._display_submitted_code("print('first')")
    window._display_submitted_code("print('second')")
    assert window.submitted_code.toPlainText() == "print('first')\nprint('second')\n"
    assert "print('first')" in capsys.readouterr().out
    assert "color: #f2f2f2" in window.submitted_code.styleSheet()

    window.append_code_action.setChecked(False)
    window._display_submitted_code("print('replacement')")
    assert window.submitted_code.toPlainText() == "print('replacement')"

    window._clear_submitted_code()
    assert not window.submitted_code.toPlainText()

    window.close()
    app.processEvents()
