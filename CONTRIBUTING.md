# Contributing

Thanks for your interest in DesktopPet.

## Development Setup

On Windows, run:

```bat
run_debug.bat
```

The script creates or repairs the project-local `.venv`, installs dependencies, and starts the app in console mode.

## Checks

Before opening a pull request, run:

```bat
scripts\ensure_venv.bat
.\.venv\Scripts\python.exe -m compileall -q main.py core utils
```

## Pull Requests

- Keep changes focused.
- Do not commit `.venv/`, `build/`, `dist/`, `logs/`, `__pycache__/`, or `data/user_data.db`.
- Do not commit personal photos or private learning records.
- Add or update README/docs when behavior changes.

## Assets

Default assets should be generic and redistributable. User-specific pet images should stay local and should not be committed unless they are intentionally licensed for the project.
