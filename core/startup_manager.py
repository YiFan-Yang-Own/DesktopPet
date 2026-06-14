"""Windows startup registration helpers."""

from __future__ import annotations

import os
import sys
from pathlib import Path


STARTUP_FILE_NAME = "DesktopPet.bat"


def is_supported() -> bool:
    """Return True when startup registration is available."""
    return sys.platform == "win32"


def startup_script_path() -> Path:
    """Return the current user's Windows Startup folder script path."""
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return Path()
    return (
        Path(appdata)
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
        / "Startup"
        / STARTUP_FILE_NAME
    )


def is_enabled() -> bool:
    """Return True when the startup script exists."""
    path = startup_script_path()
    return bool(path) and path.exists()


def set_enabled(enabled: bool, project_dir: Path) -> None:
    """Enable or disable launch-at-login for the current Windows user."""
    if not is_supported():
        return

    path = startup_script_path()
    if not path:
        return
    if not enabled:
        if path.exists():
            path.unlink()
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    run_bat = project_dir / "run.bat"
    path.write_text(
        "\n".join(
            [
                "@echo off",
                f'cd /d "{project_dir}"',
                f'start "" "{run_bat}"',
                "exit /b 0",
                "",
            ]
        ),
        encoding="utf-8",
    )
