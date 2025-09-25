@echo off
echo ========================================
echo Serato Sync GUI - Windows EXE Builder
echo ========================================
echo.

echo Installing build requirements...
python -m pip install -r requirements_build.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install requirements
    pause
    exit /b 1
)

echo.
echo Building standalone executable...
python -m PyInstaller seratosync_gui.spec
if %errorlevel% neq 0 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS! Executable created:
echo Location: dist\SeratoSync_GUI.exe
echo ========================================
echo.
echo The executable is now ready for distribution.
echo No Python installation required on target computers.
echo.

pause
