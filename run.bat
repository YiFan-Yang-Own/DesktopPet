@echo off
setlocal

cd /d "%~dp0"

call scripts\ensure_venv.bat
if errorlevel 1 (
    echo.
    echo [ERROR] Environment setup failed.
    pause
    exit /b 1
)

echo [INFO] Starting DesktopPet with project-local .venv...
start "" "%DESKTOPPET_PYTHONW%" "%cd%\main.py"
exit /b 0
