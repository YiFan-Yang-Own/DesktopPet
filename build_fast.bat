@echo off
setlocal

rem Fast incremental build script for daily development.
rem It reuses PyInstaller cache and skips dependency installation.

cd /d "%~dp0"

set "APP_NAME=DesktopPet"
set "PACKAGE_DATA=%cd%\build_package_data"

echo ========================================
echo Fast building %APP_NAME%
echo Project: %cd%
echo ========================================
echo.

call scripts\ensure_venv.bat
if errorlevel 1 (
    echo [ERROR] Environment setup failed.
    pause
    exit /b 1
)

if not exist "%DESKTOPPET_PYINSTALLER%" (
    echo [INFO] Installing build dependencies...
    "%DESKTOPPET_PYTHON%" -m pip install -r requirements-dev.txt
    if errorlevel 1 (
        echo [ERROR] Build dependency installation failed.
        pause
        exit /b 1
    )
)

echo [INFO] Python version:
"%DESKTOPPET_PYTHON%" --version

echo.
echo [INFO] Preparing packaged data...
if exist "%PACKAGE_DATA%" rmdir /s /q "%PACKAGE_DATA%"
mkdir "%PACKAGE_DATA%"
mkdir "%PACKAGE_DATA%\data"
mkdir "%PACKAGE_DATA%\data\wordlib"
mkdir "%PACKAGE_DATA%\resources"
xcopy /e /i /y resources "%PACKAGE_DATA%\resources" >nul
xcopy /e /i /y data\wordlib "%PACKAGE_DATA%\data\wordlib" >nul

echo.
echo [INFO] Running PyInstaller with cache reuse...
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
    echo [ERROR] Fast build failed.
    pause
    exit /b 1
)

if exist "%PACKAGE_DATA%" rmdir /s /q "%PACKAGE_DATA%"

echo.
echo ========================================
echo Fast build finished successfully.
echo EXE: %cd%\dist\%APP_NAME%\%APP_NAME%.exe
echo ========================================
echo.
pause
