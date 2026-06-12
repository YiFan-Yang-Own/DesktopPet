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

echo [INFO] Starting DesktopPet in debug console mode...
"%DESKTOPPET_PYTHON%" "%cd%\main.py"
echo.
echo [INFO] DesktopPet exited.
pause
