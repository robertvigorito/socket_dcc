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
    target = install / "python" / "nuix"
    source_package = source / "src" / "nuix"

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
    return True


if __name__ == "__main__":
    build()
