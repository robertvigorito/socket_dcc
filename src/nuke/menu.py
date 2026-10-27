"""Nuke menu setup for socket-dcc."""

import nuke  # noqa: I001 -- Nuke provides this host API module.


package_menu = (
    nuke.menu("Nuke")
    .addMenu("wgid")
    .addCommand("Socket DCC", "import socket_dcc.interface; socket_dcc.interface.load_in_application()")
)
