"""Tests for the GUI's optional log panel."""

import errno
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
    Qt.QtCore.QSettings("socket-dcc", "socket-dcc").clear()
    window = MainWindow()

    assert window.show_log_action.isChecked()
    assert window.show_code_action.isChecked()
    assert not window.log_output.isHidden()
    assert not window.submitted_code.isHidden()
    assert window.token_input.text()
    assert window.port_input.objectName() == "portInput"
    assert "QSpinBox#portInput" in window.styleSheet()
    assert (
        "QSpinBox#portInput, QLineEdit#tokenInput { background-color: transparent; border: none; }"
        in window.styleSheet()
    )
    assert (
        "QPushButton#copyHostButton, QPushButton#copyTokenButton, QPushButton#allInterfacesButton "
        "{ background-color: transparent; border: none; color: #dddddd; }" in window.styleSheet()
    )
    assert "QPushButton#allInterfacesButton" in window.styleSheet()
    assert "QPushButton#allInterfacesButton:hover" in window.styleSheet()
    assert "QPushButton#copyTokenButton" in window.styleSheet()
    assert window.auto_disconnect_action.isCheckable()
    assert window.auto_close_action.isCheckable()
    assert window.always_on_top_action.isCheckable()
    assert window.all_interfaces_button.isCheckable()
    assert not window.all_interfaces_button.icon().isNull()
    assert window.all_interfaces_button.toolTip() == "Use 0.0.0.0 to listen on all interfaces"

    topmost_flag = getattr(Qt.QtCore.Qt, "WindowStaysOnTopHint")
    window.always_on_top_action.setChecked(True)
    assert window.windowFlags() & topmost_flag
    window.always_on_top_action.setChecked(False)
    assert not window.windowFlags() & topmost_flag

    window.show_log_action.setChecked(False)
    assert window.log_output.isHidden()
    window.show_log_action.setChecked(True)
    assert not window.log_output.isHidden()

    window.close()
    app.processEvents()


def test_menu_settings_are_saved_and_restored() -> None:
    """Verify checkable menu settings survive a window close and reopen.

    Returns:
        None: Asserts menu state is restored from saved values.
    """
    app = Qt.QtWidgets.QApplication.instance() or Qt.QtWidgets.QApplication([])
    settings = Qt.QtCore.QSettings("socket-dcc", "socket-dcc")
    settings.clear()

    window = MainWindow()
    window._idle_timeout_seconds = 900
    window.auto_disconnect_action.setChecked(True)
    window.auto_close_action.setChecked(True)
    window.show_log_action.setChecked(False)
    window.show_code_action.setChecked(False)
    window.append_code_action.setChecked(False)
    window.always_on_top_action.setChecked(True)
    window.close()
    app.processEvents()

    restored = MainWindow()
    assert restored._idle_timeout_seconds == 900
    assert restored.auto_disconnect_action.isChecked()
    assert restored.auto_close_action.isChecked()
    assert not restored.show_log_action.isChecked()
    assert not restored.show_code_action.isChecked()
    assert not restored.append_code_action.isChecked()
    assert restored.always_on_top_action.isChecked()
    assert restored.windowFlags() & getattr(Qt.QtCore.Qt, "WindowStaysOnTopHint")

    restored.close()
    settings.clear()
    app.processEvents()


def test_menu_setting_is_saved_when_action_is_triggered() -> None:
    """Verify a menu preference is saved before the window closes.

    Returns:
        None: Asserts the triggered action updates persistent settings immediately.
    """
    app = Qt.QtWidgets.QApplication.instance() or Qt.QtWidgets.QApplication([])
    settings = Qt.QtCore.QSettings("socket-dcc", "socket-dcc")
    settings.clear()

    window = MainWindow()
    window.auto_disconnect_action.trigger()

    assert settings.value(gui_window._MENU_SETTINGS["auto_disconnect"], type=bool)

    window.close()
    settings.clear()
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


def test_all_interfaces_button_switches_bind_host(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify the all-interfaces button selects 0.0.0.0 and toggles back.

    Args:
        monkeypatch: Pytest fixture used to replace the detected local host.

    Returns:
        None: Asserts the button updates the displayed and selected bind address.
    """
    app = Qt.QtWidgets.QApplication.instance() or Qt.QtWidgets.QApplication([])
    monkeypatch.setattr(gui_window, "get_default_host", lambda: "192.168.1.25")
    window = MainWindow()

    window.all_interfaces_button.click()
    assert window._ip_address == "0.0.0.0"
    assert window.ip_value.text() == "0.0.0.0"
    assert window.all_interfaces_button.toolTip() == "Use the local host address instead of 0.0.0.0"

    window.all_interfaces_button.click()
    assert window._ip_address == "192.168.1.25"
    assert window.ip_value.text() == "192.168.1.25"
    assert window.all_interfaces_button.toolTip() == "Use 0.0.0.0 to listen on all interfaces"
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
    terminal_output = capsys.readouterr().out
    assert "print('first')" in terminal_output
    assert "\x1b[" not in terminal_output
    assert "color: #f2f2f2" in window.submitted_code.styleSheet()

    window.append_code_action.setChecked(False)
    window._display_submitted_code("print('replacement')")
    assert window.submitted_code.toPlainText() == "print('replacement')"

    window.submitted_code.clear()
    assert not window.submitted_code.toPlainText()

    window.close()
    app.processEvents()


def test_connect_with_unavailable_ip_suggests_valid_bind_addresses(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify an unavailable bind IP shows actionable address suggestions.

    Args:
        monkeypatch: Pytest fixture used to simulate a bind-address failure.

    Returns:
        None: Asserts the GUI displays localhost and all-interface alternatives.
    """
    app = Qt.QtWidgets.QApplication.instance() or Qt.QtWidgets.QApplication([])
    window = MainWindow(host="192.0.2.1")
    monkeypatch.setattr(
        window.server,
        "start",
        Mock(side_effect=OSError(errno.EADDRNOTAVAIL, "Cannot assign requested address")),
    )

    window._toggle_connection()

    log_text = window.log_output.toPlainText()
    assert "Cannot assign requested address" in log_text
    assert "localhost for local connections" in log_text
    assert "0.0.0.0 to listen on all interfaces" in log_text
    assert window.status_value.text() == "Error"
    window.close()
    app.processEvents()
