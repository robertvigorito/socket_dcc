"""Nuke menu setup for socket-dcc."""

import nukescripts  # noqa: I001 -- Nuke provides this host API module.

import nuke
import socket_dcc.interface

package_menu = (
    nuke.menu("Nuke")
    .addMenu("wgid")
    .addCommand("Socket DCC", "import socket_dcc.interface; app = socket_dcc.interface.load_in_application()")
)


# Connect the menu to Nuke as a panel
nukescripts.registerPanel("com.wgid.socket_dcc", "socket_dcc.interface.MainWindow")

PANEL_ID = "com.wgid.socket_dcc"

nukescripts.registerPanel(
    PANEL_ID,
    "socket_dcc.interface.MainWindow",
)

nuke.menu("Pane").addCommand(
    "Socket DCC",
    f"nukescripts.panels.restorePanel('{PANEL_ID}')",
)

import nuke

# Create or access a custom toolbar/menu
toolbar = nuke.toolbar("MyToolbar")

# Add a command or sub-menu to the toolbar

import nukescripts
from Qt import QtWidgets

class MyCustomPanel(QtWidgets.QWidget):
    def __init__(self):
        super(MyCustomPanel, self).__init__()
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Hello from Custom Panel"))

# Register the panel with Nuke
panel_id = "com.mycompany.MyCustomPanel"
panel_name = "My Custom Panel"

def add_my_panel():
    return MyCustomPanel()

nukescripts.panels.registerWidgetAsPanel(
    "add_my_panel", 
    panel_name, 
    panel_id
)

# Optional: Add a menu item to open or spawn the panel
m = nuke.menu("Nuke")
m.addCommand(f"Window/Panels/{panel_name}", f"nukescripts.openPanel('{panel_id}')")

for _ in range(1):
    nuke.createNode("NoOp")