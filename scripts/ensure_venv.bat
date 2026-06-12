@echo off
setlocal EnableExtensions

rem Ensure DesktopPet uses the project-local virtual environment.
rem Usage:
rem   call scripts\ensure_venv.bat
rem After call, parent scripts can use:
rem   %DESKTOPPET_PYTHON%
rem   %DESKTOPPET_PYTHONW%
rem   %DESKTOPPET_PYINSTALLER%

set "PROJECT_DIR=%~dp0.."
for %%I in ("%PROJECT_DIR%") do set "PROJECT_DIR=%%~fI"

set "VENV_DIR=%PROJECT_DIR%\.venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "PYTHONW_EXE=%VENV_DIR%\Scripts\pythonw.exe"
set "PYINSTALLER_EXE=%VENV_DIR%\Scripts\pyinstaller.exe"

if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" --version >nul 2>&1
    if errorlevel 1 (
        echo [WARN] Existing .venv is broken. Recreating it...
        rmdir /s /q "%VENV_DIR%"
    )
)

if not exist "%PYTHON_EXE%" (
    echo [INFO] Creating project-local virtual environment...
    call :find_python
    if errorlevel 1 exit /b 1
    call :check_base_python_version
    if errorlevel 1 exit /b 1
    "%BASE_PYTHON%" -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create .venv.
        echo [HINT] Install Python 3.9+ and make sure python is available in PATH.
        exit /b 1
    )
)

echo [INFO] Using project Python:
"%PYTHON_EXE%" --version
if errorlevel 1 exit /b 1
call :check_venv_python_version
if errorlevel 1 exit /b 1

"%PYTHON_EXE%" -c "import PyQt5, yaml" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing runtime dependencies into project .venv...
    call :install_runtime_dependencies
    if errorlevel 1 exit /b 1
)

endlocal & (
    set "DESKTOPPET_PROJECT_DIR=%PROJECT_DIR%"
    set "DESKTOPPET_PYTHON=%PYTHON_EXE%"
    set "DESKTOPPET_PYTHONW=%PYTHONW_EXE%"
    set "DESKTOPPET_PYINSTALLER=%PYINSTALLER_EXE%"
)
exit /b 0

:find_python
set "BASE_PYTHON="

where py >nul 2>&1
if not errorlevel 1 (
    for %%V in (3.12 3.11 3.10 3.9) do (
        py -%%V --version >nul 2>&1
        if not errorlevel 1 (
            set "BASE_PYTHON=py -%%V"
            exit /b 0
        )
    )
    py -3 --version >nul 2>&1
    if not errorlevel 1 (
        set "BASE_PYTHON=py -3"
        exit /b 0
    )
)

where python >nul 2>&1
if not errorlevel 1 (
    python --version >nul 2>&1
    if not errorlevel 1 (
        set "BASE_PYTHON=python"
        exit /b 0
    )
)

echo [ERROR] Could not find Python.
echo [HINT] Install Python 3.9+ from https://www.python.org/downloads/
echo [HINT] On Windows, enable "Add python.exe to PATH" during installation.
exit /b 1

:check_base_python_version
%BASE_PYTHON% -c "import sys; raise SystemExit(0 if (3, 9) <= sys.version_info < (3, 13) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.9 - 3.12 is required.
    %BASE_PYTHON% --version
    echo [HINT] Install Python 3.9 - 3.12 for the best compatibility.
    exit /b 1
)
exit /b 0

:check_venv_python_version
"%PYTHON_EXE%" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.9+ is required.
    "%PYTHON_EXE%" --version
    echo [HINT] Delete .venv and rerun run.bat after installing Python 3.9 - 3.12.
    exit /b 1
)
exit /b 0

:install_runtime_dependencies
"%PYTHON_EXE%" -m ensurepip --upgrade >nul 2>&1
"%PYTHON_EXE%" -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is not available in this Python environment.
    echo [HINT] Reinstall Python and make sure pip is selected.
    exit /b 1
)

"%PYTHON_EXE%" -m pip install --upgrade pip
if errorlevel 1 (
    echo [WARN] pip upgrade failed. Continuing with the existing pip...
)

"%PYTHON_EXE%" -m pip install -r "%PROJECT_DIR%\requirements.txt"
if not errorlevel 1 exit /b 0

echo.
echo [WARN] Dependency installation failed with the default PyPI source.
echo [INFO] Retrying with Tsinghua PyPI mirror...
"%PYTHON_EXE%" -m pip install -r "%PROJECT_DIR%\requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple
if not errorlevel 1 exit /b 0

echo.
echo [ERROR] Dependency installation failed.
echo [HINT] Check your network, proxy, or VPN, then rerun run_debug.bat.
echo [HINT] You can also run manually:
echo        "%PYTHON_EXE%" -m pip install -r "%PROJECT_DIR%\requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple
exit /b 1
