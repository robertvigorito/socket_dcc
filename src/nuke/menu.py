"""Nuke menu setup for nuix."""

import nuke  # noqa: I001 -- Nuke provides this host API module.


package_menu = nuke.menu("Nuke").addMenu("nuix")
package_menu.addCommand(
    "About",
    lambda: nuke.message("nuix Nuke tools"),
)
