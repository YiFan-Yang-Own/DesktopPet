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

Python 3.9+ is required. Versions 3.9 through 3.12 are preferred for PyQt5
compatibility, but the script will continue with newer Python versions when
that is all the machine has. If Python is missing, install it from python.org
and enable `Add python.exe to PATH`.

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
resources/pets/local_pet.png
```

Supported priority:

```text
local_pet.gif > local_pet.png > local_pet.jpg > local_pet.jpeg > pet.gif > pet.png > pet.jpg > pet.jpeg
```

For best results, use a transparent PNG with a square canvas.
The settings window can copy the selected image into `resources/pets/local_pet.*`.
These local pet files are ignored by Git.
