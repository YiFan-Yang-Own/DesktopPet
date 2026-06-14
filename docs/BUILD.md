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
