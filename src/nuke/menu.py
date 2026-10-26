"""Nuke menu setup for socket-dcc."""

import nuke  # noqa: I001 -- Nuke provides this host API module.


package_menu = nuke.menu("Nuke").addMenu("socket-dcc")  # type: ignore[attr-defined]
package_menu.addCommand(
    "About",
    lambda: nuke.message("socket-dcc Nuke tools"),  # type: ignore[attr-defined]
)
