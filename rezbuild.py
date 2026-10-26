"""Install the generated Python package into a Rez package release."""

import os
import shutil
from pathlib import Path


def build() -> bool:
    """Install or link the generated package into the Rez package.

    Returns:
        bool: ``True`` after the package is installed or linked.
    """
    source = Path(os.environ["REZ_BUILD_SOURCE_PATH"]).resolve()
    install = Path(os.environ["REZ_BUILD_INSTALL_PATH"]).resolve()
    target = install / "python" / "socket_dcc"
    source_package = source / "src" / "socket_dcc"

    if target.exists() or target.is_symlink():
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        else:
            target.unlink()
    target.parent.mkdir(parents=True, exist_ok=True)

    if os.environ.get("REZ_BUILD_INSTALL") == "1":
        shutil.copytree(source_package, target)
    else:
        target.symlink_to(source_package, target_is_directory=True)

    nuke_target = install / "nuke"
    nuke_source = source / "src" / "nuke"
    if nuke_source.is_dir():
        if nuke_target.exists() or nuke_target.is_symlink():
            if nuke_target.is_dir() and not nuke_target.is_symlink():
                shutil.rmtree(nuke_target)
            else:
                nuke_target.unlink()
        if os.environ.get("REZ_BUILD_INSTALL") == "1":
            shutil.copytree(nuke_source, nuke_target)
        else:
            nuke_target.symlink_to(nuke_source, target_is_directory=True)
    return True


if __name__ == "__main__":
    build()
