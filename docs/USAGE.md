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
- Pet opacity
- Always on top
- Click pet to review
- Startup reminder
- Launch at login
- Quiet hours

On Windows, `Launch at login` works in both source and packaged modes. When
running from source, it launches `run.bat`. When running from a PyInstaller
package, it launches the current `DesktopPet.exe`.

## Built-in Pet Skins

Open `设置`, then choose a skin from `默认形象`.

Built-in skins:

- 经典三花
- 暖橘小猫
- 银灰小猫
- 黑白小猫
- 奶茶小猫

Each skin includes happy, sad, walking, sleeping, eating, playing, and resting
states. Local custom images still take priority over built-in skins.

## Custom Pet Image

Put your image in:

```text
resources/pets/local_pet.png
```

Supported priority:

```text
local_pet.* > selected skin pet_STATE.* > classic skin pet_STATE.* > root pet_STATE.* > root pet.*
```

The normal pet uses the happy state. Dragging the pet shows the walking state,
word bubbles show the eating state, pause/quiet hours show the sleeping state,
and fullscreen do-not-disturb shows the resting state. After a word bubble
action, `记住了` briefly shows the happy state and `再记一次` briefly shows the sad
state. Reaching the daily goal briefly shows the playing state.

For best results, use a transparent PNG with a square canvas.
The settings window can copy the selected image into `resources/pets/local_pet.*`.
These local pet files are ignored by Git.

## Custom Word Library

Built-in libraries:

- CET4: `data/wordlib/cet4.json`
- CET6: `data/wordlib/cet6.json`
- Postgraduate: `data/wordlib/postgraduate.json`

Open the tray menu, choose `词库选择`, then click `导入词库...`.

The JSON file must be an array of objects. Each object needs at least:

```json
[
  {
    "word": "abandon",
    "meaning": "放弃；遗弃",
    "phonetic": "/əˈbændən/",
    "example": "He abandoned his plan."
  }
]
```

Imported files are copied to `data/wordlib/custom_*.json` and ignored by Git.
