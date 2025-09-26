@echo off
REM Windows Batch Script for Building SeratoSync GUI
REM This script sets up the environment and builds the Windows executable

echo.
echo ====================================================
echo  SeratoSync GUI - Windows Build Script
echo ====================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

REM Navigate to the project root (two levels up from this script)
cd /d "%~dp0..\.."

REM Check if we're in the right directory
if not exist "seratosync_gui.py" (
    echo ERROR: Cannot find seratosync_gui.py
    echo Make sure you're running this from the correct directory
    pause
    exit /b 1
)

REM Run the Python build script
echo Running Python build script...
python scripts\build\build_windows.py

REM Check if build was successful
if %errorlevel% equ 0 (
    echo.
    echo ====================================================
    echo  BUILD SUCCESSFUL!
    echo ====================================================
    echo.
    echo The executable has been created in the 'dist' folder.
    echo You can now run SeratoSync_GUI.exe
    echo.
) else (
    echo.
    echo ====================================================
    echo  BUILD FAILED!
    echo ====================================================
    echo.
    echo Check the error messages above for details.
    echo.
)

pause
