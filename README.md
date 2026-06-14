# DesktopPet

一个基于 **Python 3.9+ / PyQt5 / SQLite / PyYAML** 的桌面宠物背单词应用。它会在桌面上显示一个可拖拽的透明宠物，通过气泡提醒推送单词，并用简化版间隔重复算法记录学习进度。

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![PyQt5](https://img.shields.io/badge/GUI-PyQt5-green)
![SQLite](https://img.shields.io/badge/Storage-SQLite-lightgrey)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## Features

- 透明、无边框、置顶的桌面宠物窗口
- 支持 GIF 宠物动画，也支持 PNG/JPG 静态宠物图
- 鼠标拖拽移动宠物，释放后保持位置
- 单词气泡提醒，包含单词、音标、释义、例句和操作按钮
- “记住了 / 再记一次”学习反馈记录
- SQLite 本地存储词汇和学习记录
- 简化版艾宾浩斯复习调度：1 天、3 天、7 天、30 天
- 系统托盘菜单：暂停提醒、切换词库、设置提醒间隔、退出
- 设置窗口支持开机自启、桌宠透明度、置顶行为和点击复习开关
- 夜间免打扰和 Windows 全屏窗口免打扰
- 单实例检测，避免重复启动
- Rotating file logging，日志写入 `logs/app.log`
- 支持 PyInstaller 打包为 Windows exe

## Preview

项目已提供默认托盘图标和默认静态桌宠。如果想替换宠物或图标，可以自行放入资源文件：

- `resources/pets/local_pet.gif`
- `resources/pets/local_pet.png`
- `resources/pets/local_pet.jpg`
- `resources/pets/local_pet.jpeg`
- `resources/pets/pet.gif`
- `resources/pets/pet.png`
- `resources/pets/pet.jpg`
- `resources/pets/pet.jpeg`
- `resources/icons/icon.png`

宠物资源优先级为 `local_pet.*` > `pet.gif` > `pet.png` > `pet.jpg` > `pet.jpeg`。设置窗口中选择的图片会保存为本地 `local_pet.*`，不会覆盖仓库默认图片。如果这些文件都不存在，程序会使用内置绘制的兜底宠物。

## Usage

启动后，宠物默认出现在屏幕右下角：

- 左键拖拽宠物可以移动位置
- 左键点击托盘图标可以显示或隐藏宠物
- 右键托盘图标可以打开菜单
- 点击 `立即复习` 可以马上弹出一个单词气泡
- 点击 `学习记录` 可以查看今日进度、累计学习和最近记录
- 点击 `设置` 可以调整每日目标、提醒间隔、气泡停留时间、桌宠大小和免打扰时间
- 点击 `暂停提醒` / `恢复提醒` 可以控制定时提醒
- 右键桌宠也可以打开同一个菜单
- 点击 `退出程序` 可以关闭应用

## Tech Stack

- Python 3.9+，推荐 3.9-3.12
- PyQt5
- SQLite
- PyYAML
- PyInstaller

## Project Structure

```text
DesktopPet/
├── main.py
├── requirements.txt
├── config.yaml
├── README.md
├── resources/
│   ├── pets/
│   │   └── pet.png
│   └── icons/
│       └── icon.png
├── core/
│   ├── __init__.py
│   ├── init.py
│   ├── pet_window.py
│   ├── bubble_window.py
│   ├── tray_manager.py
│   ├── word_manager.py
│   ├── scheduler.py
│   └── config_manager.py
├── data/
│   ├── wordlib/
│   │   └── cet4.json
│   └── user_data.db
├── utils/
│   ├── __init__.py
│   ├── init.py
│   └── logger.py
└── logs/
    └── app.log
```

`data/user_data.db` 和 `logs/app.log` 会在首次运行时自动生成。

## Quick Start

### Recommended: One-click Local Environment

Windows 下建议直接双击：

```text
run.bat
```

`run.bat` 会自动：

- 检查项目根目录下的 `.venv`
- 如果 `.venv` 不存在或损坏，自动重建
- 优先使用 Python 3.12、3.11、3.10 或 3.9 创建环境；只有更新版本时也会继续尝试
- 安装缺失依赖；默认源失败时会自动尝试清华 PyPI 镜像
- 使用项目自己的 `.venv` 启动程序

如果启动失败，双击：

```text
run_debug.bat
```

它会保留控制台窗口，方便查看错误信息。

### Manual Run on Windows

如果你想手动运行：

```powershell
scripts\ensure_venv.bat
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

运行后，宠物会出现在屏幕右下角。右键系统托盘图标可以打开菜单。

### Manual Run on Linux/macOS

Linux/macOS 不能直接运行 `.bat` 脚本，可以手动创建虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Linux 桌面环境需要可用的图形会话和 Qt 托盘支持。无桌面环境的服务器或纯终端环境无法显示桌宠窗口。

## Environment Troubleshooting

- 如果提示找不到 Python，请安装 Python 3.9+，并在 Windows 安装时勾选 `Add python.exe to PATH`。
- 如果依赖安装失败，先运行 `run_debug.bat` 查看具体错误；脚本会自动尝试一次清华 PyPI 镜像。
- 如果 PyQt5 安装失败，通常是 Python 版本过新、网络源不可用或 pip 被代理/防火墙拦截。
- 如果只是想替换本地宠物图片，优先在设置窗口里选择图片；程序会生成被 Git 忽略的 `resources/pets/local_pet.*`，不会影响仓库默认图片。

## Configuration

默认配置文件位于 `config.yaml`。程序运行时产生的个人设置会写入被 Git 忽略的 `config.local.yaml`：

```yaml
reminder_interval_minutes: 30
word_lib: "cet4.json"
daily_goal: 20
quiet_hours:
  enabled: true
  start: "22:00"
  end: "08:00"
```

### Config Fields

| Field | Type | Description |
| --- | --- | --- |
| `reminder_interval_minutes` | integer | 单词提醒间隔，单位为分钟 |
| `word_lib` | string | 词库文件名，位于 `data/wordlib/` |
| `daily_goal` | integer | 每日学习目标，用于托盘完成提醒 |
| `pet.size` | integer | 桌宠尺寸 |
| `pet.opacity` | integer | 桌宠透明度，范围 20-100 |
| `pet.always_on_top` | boolean | 桌宠是否置顶 |
| `pet.click_to_review` | boolean | 点击桌宠是否立即复习 |
| `quiet_hours.enabled` | boolean | 是否启用夜间免打扰 |
| `quiet_hours.start` | string | 免打扰开始时间 |
| `quiet_hours.end` | string | 免打扰结束时间 |

修改配置也可以通过托盘菜单完成，程序会自动写入 `config.local.yaml`，不会改动仓库里的默认配置。

## Word Library

内置词库位于：

```text
data/wordlib/cet4.json
data/wordlib/cet6.json
data/wordlib/postgraduate.json
```

词库格式为 JSON 数组：

```json
[
  {
    "word": "abandon",
    "phonetic": "/əˈbændən/",
    "meaning": "放弃；遗弃",
    "example": "He abandoned his plan to travel."
  }
]
```

新增词库时，可以在托盘菜单的 `词库选择` 中点击 `导入词库...`，选择符合格式的 JSON 文件。程序会复制为 `data/wordlib/custom_*.json` 并自动切换到该词库；这些本地自定义词库会被 Git 忽略。

也可以手动将 JSON 文件放入 `data/wordlib/`，再在本地 `config.local.yaml` 中把 `word_lib` 改成对应文件名。

## Packaging

### One-click Build

Windows 下可以直接双击运行完整发布构建：

```text
build.bat
```

脚本会自动使用项目根目录下的 `.venv`，必要时创建/修复本地虚拟环境，清理旧的 `build/`、`dist/` 和 `.spec` 文件，然后调用 PyInstaller 打包。
脚本只会打包 `data/wordlib/` 中的词库和 `resources/` 资源，不会把本机运行生成的 `data/user_data.db` 学习记录打进安装包。

打包完成后，程序位于：

```text
dist\DesktopPet\DesktopPet.exe
```

### Fast Build

环境没问题时推荐使用快速增量打包：

```text
build_fast.bat
```

`build_fast.bat` 会跳过依赖安装，不清理 `build/` 和 `dist/`，让 PyInstaller 复用缓存。第一次打包或依赖变化后先运行 `build.bat`，之后改代码通常运行 `build_fast.bat` 更快。

如果遇到奇怪的打包缓存问题，再切回 `build.bat` 做一次干净构建。

### Manual Build

也可以手动使用 PyInstaller 打包为 Windows exe：

```powershell
.\.venv\Scripts\pyinstaller.exe ^
  --noconfirm ^
  --windowed ^
  --name DesktopPet ^
  --add-data "config.yaml;." ^
  --add-data "data\wordlib;data\wordlib" ^
  --add-data "resources;resources" ^
  main.py
```

打包完成后，程序位于：

```text
dist\DesktopPet\DesktopPet.exe
```

## Development

### Run Syntax Check

```powershell
.\.venv\Scripts\python.exe -m compileall -q .
```

### Clean Local Build Outputs

```text
clean.bat
```

该脚本会删除 `build/`、`dist/`、`DesktopPet.spec` 和 `__pycache__/`。

### Validate Word Library

```powershell
.\.venv\Scripts\python.exe -c "import json, pathlib; data=json.loads(pathlib.Path('data/wordlib/cet4.json').read_text(encoding='utf-8')); print(len(data))"
```

### Main Modules

| Module | Responsibility |
| --- | --- |
| `main.py` | 应用入口、单实例检测、异常捕获、对象初始化和优雅退出 |
| `core/pet_window.py` | 桌宠窗口、透明置顶、GIF 动画、拖拽、气泡弹出 |
| `core/bubble_window.py` | 单词气泡 UI、绘制圆角矩形和三角指针、按钮反馈、淡入动画 |
| `core/tray_manager.py` | 系统托盘图标、右键菜单、配置变更入口 |
| `core/word_manager.py` | 词库导入、SQLite 存储、间隔重复、学习记录和统计 |
| `core/scheduler.py` | 定时提醒、暂停恢复、夜间免打扰、全屏检测 |
| `core/config_manager.py` | YAML 配置读取、默认值合并和保存 |
| `utils/logger.py` | logging 初始化和 rotating file handler 配置 |

## Runtime Data

- `data/user_data.db`：SQLite 学习记录数据库，首次运行自动创建
- `logs/app.log`：应用日志，最大 5MB，保留 3 个备份

## GitHub Notes


More docs:

- [Usage](docs/USAGE.md)
- [Build](docs/BUILD.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## FAQ

### 程序启动后没有宠物动画怎么办？

确认 `resources/pets/local_pet.*` 或 `resources/pets/pet.*` 是否存在。如果不存在，程序会显示内置兜底图形。

### 托盘图标不显示怎么办？

确认系统托盘没有隐藏图标；也可以放入自定义图标 `resources/icons/icon.png`。

### 为什么全屏游戏或视频时没有弹窗？

Windows 下程序会检测当前前台窗口是否全屏。如果检测为全屏，会跳过本次提醒并把单词放回待推送队列。

### 如何重置学习记录？

关闭程序后删除 `data/user_data.db`，下次启动会重新创建数据库并导入词库。

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
