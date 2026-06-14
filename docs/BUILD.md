# Build

## Full Build

Run:

```text
build.bat
```

Output:

```text
dist\DesktopPet\DesktopPet.exe
```

Distribute the whole folder:

```text
dist\DesktopPet\
```

Do not distribute only `DesktopPet.exe`; the `_internal` files and packaged
resources are required.

## Fast Build

For daily development:

```text
build_fast.bat
```

This skips cleanup and reuses PyInstaller cache.

## Clean

Run:

```text
clean.bat
```

This removes build outputs and Python caches.

## Notes

Build scripts use the project-local `.venv`. They call:

```text
scripts\ensure_venv.bat
```

The packaged app includes:

- `config.yaml`
- `data/wordlib/`
- `resources/`

It does not include local settings from `config.local.yaml` or local learning
records from `data/user_data.db`.

## Launch At Login

When the packaged app is running, the `开机自动启动` setting registers the
current `DesktopPet.exe` in the current user's Windows Startup folder.

If you move the packaged folder after enabling launch at login, disable and
enable the setting once so the startup script points to the new location.
