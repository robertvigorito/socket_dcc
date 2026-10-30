"""Install the generated Python package into a Rez package release."""

import logging
import os
import shutil
from pathlib import Path

PACKAGE_NAME = "socket_dcc"
LOGGER = logging.getLogger(__name__)


def _remove_target(target: Path) -> bool:
    """Remove an existing target path.

    Args:
        target: Existing path to remove.

    Returns:
        True when the target no longer exists.
    """
    if not (target.exists() or target.is_symlink()):
        return True

    LOGGER.info("Removing existing build target: %s", target)
    if target.is_dir() and not target.is_symlink():
        shutil.rmtree(target)
    else:
        target.unlink()
    return True


def _install_copy(source: Path, target: Path) -> bool:
    """Copy a source directory to a target location.

    Args:
        source: Source directory to install.
        target: Destination path in the Rez install root.

    Returns:
        bool: True when the operation succeeds.
    """
    LOGGER.info("Copying %s to %s", source, target)
    _remove_target(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)
    return True


def build() -> bool:
    """Install the generated package into the Rez package.

    Returns:
        bool: True after the package is installed.
    """
    source = Path(os.environ["REZ_BUILD_SOURCE_PATH"]).resolve()
    install = Path(os.environ["REZ_BUILD_INSTALL_PATH"]).resolve()
    LOGGER.info("Building socket-dcc from %s into %s", source, install)
    source_package = source / "src" / PACKAGE_NAME
    target_package = install / "python" / PACKAGE_NAME
    _install_copy(source_package, target_package)

    source_nuke = source / "src" / "nuke"
    target_nuke = install / "nuke"
    if source_nuke.exists():
        _install_copy(source_nuke, target_nuke)
    else:
        LOGGER.info("Nuke source directory not found; removing target: %s", target_nuke)
        _remove_target(target_nuke)

    LOGGER.info("Build completed successfully")
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    build()
