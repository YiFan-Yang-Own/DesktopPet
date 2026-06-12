@echo off
setlocal

rem One-click build script for DesktopPet.
rem Double-click this file or run it from PowerShell/CMD.

cd /d "%~dp0"

set "APP_NAME=DesktopPet"
set "PACKAGE_DATA=%cd%\build_package_data"

echo ========================================
echo Building %APP_NAME%
echo Project: %cd%
echo ========================================
echo.

call scripts\ensure_venv.bat
if errorlevel 1 (
    echo [ERROR] Environment setup failed.
    pause
    exit /b 1
)

echo [INFO] Python version:
"%DESKTOPPET_PYTHON%" --version
if errorlevel 1 (
    echo [ERROR] Failed to run Python from .venv.
    pause
    exit /b 1
)

echo.
if not exist "%DESKTOPPET_PYINSTALLER%" (
    echo [INFO] Installing build dependencies...
    "%DESKTOPPET_PYTHON%" -m pip install -r requirements-dev.txt
    if errorlevel 1 (
        echo [ERROR] Dependency installation failed.
        pause
        exit /b 1
    )
) else (
    echo [INFO] Dependencies look ready. Skipping pip install.
    echo [INFO] To refresh dependencies, run:
    echo        "%DESKTOPPET_PYTHON%" -m pip install -r requirements-dev.txt --upgrade
)

echo.
echo [INFO] Cleaning previous build outputs...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "%PACKAGE_DATA%" rmdir /s /q "%PACKAGE_DATA%"
if exist "%APP_NAME%.spec" del /f /q "%APP_NAME%.spec"

echo.
echo [INFO] Preparing packaged data...
mkdir "%PACKAGE_DATA%"
mkdir "%PACKAGE_DATA%\data"
mkdir "%PACKAGE_DATA%\data\wordlib"
mkdir "%PACKAGE_DATA%\resources"
xcopy /e /i /y resources "%PACKAGE_DATA%\resources" >nul
xcopy /e /i /y data\wordlib "%PACKAGE_DATA%\data\wordlib" >nul

echo.
echo [INFO] Running PyInstaller...
"%DESKTOPPET_PYINSTALLER%" ^
  --noconfirm ^
  --windowed ^
  --name "%APP_NAME%" ^
  --add-data "config.yaml;." ^
  --add-data "%PACKAGE_DATA%\data;data" ^
  --add-data "%PACKAGE_DATA%\resources;resources" ^
  main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

if exist "%PACKAGE_DATA%" rmdir /s /q "%PACKAGE_DATA%"

echo.
echo ========================================
echo Build finished successfully.
echo EXE: %cd%\dist\%APP_NAME%\%APP_NAME%.exe
echo ========================================
echo.
pause
