"""Nuke menu setup for socket-dcc."""

import nukescripts  # noqa: I001 -- Nuke provides this host API module.

import nuke

package_menu = (
    nuke.menu("Nuke")
    .addMenu("wgid")
    .addCommand("Socket DCC", "import socket_dcc.interface; app = socket_dcc.interface.load_in_application()")
)


nukescripts.panels.registerWidgetAsPanel("socket_dcc.interface.MainWindow", "Socket DCC Panel", "com.wgid.socket_dcc")
