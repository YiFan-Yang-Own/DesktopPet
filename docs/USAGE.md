# Usage

## Start

Double-click:

```text
run.bat
```

If the app fails to start, double-click:

```text
run_debug.bat
```

The one-click scripts are for Windows. They create a project-local `.venv`,
install `requirements.txt`, and retry dependency installation with the Tsinghua
PyPI mirror if the default source fails.

Recommended Python versions are 3.9 through 3.12. If Python is missing, install
it from python.org and enable `Add python.exe to PATH`.

On Linux/macOS, create the environment manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

## Pet Controls

- Left-click the pet to show a word immediately.
- Drag the pet to move it.
- Right-click the pet to open the menu.
- Click the tray icon to show or hide the pet.

## Settings

Open the tray or pet context menu, then click `设置`.

Available settings:

- Reminder interval
- Daily goal
- Bubble duration
- Pet size
- Startup reminder
- Quiet hours

## Custom Pet Image

Put your image in:

```text
resources/pets/pet.png
```

Supported priority:

```text
pet.gif > pet.png > pet.jpg > pet.jpeg
```

For best results, use a transparent PNG with a square canvas.
