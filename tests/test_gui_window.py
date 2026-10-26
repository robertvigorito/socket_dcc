"""Tests for the GUI's optional log panel."""

from PySide6.QtWidgets import QApplication

from socket_dcc.core.gui.window import MainWindow


def test_log_menu_toggles_log_panel() -> None:
    """Verify the Log menu action shows and hides the log panel.

    Returns:
        None: This test asserts the panel visibility and window sizing behavior.
    """
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    log_action = window.show_log_action

    assert window.log_output.isHidden()
    log_action.setChecked(True)
    assert not window.log_output.isHidden()
    assert window.height() >= 300

    log_action.setChecked(False)
    assert window.log_output.isHidden()
    assert window.height() == 150

    window.close()
    app.processEvents()
