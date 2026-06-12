@echo off
setlocal

cd /d "%~dp0"

echo Cleaning build artifacts and Python caches...

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist build_package_data rmdir /s /q build_package_data
if exist DesktopPet.spec del /f /q DesktopPet.spec

for /d /r %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d"
)

echo Done.
pause
