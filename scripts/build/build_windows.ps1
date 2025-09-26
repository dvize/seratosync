# Windows PowerShell Script for Building SeratoSync GUI
# This script sets up the environment and builds the Windows executable

Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host " SeratoSync GUI - Windows Build Script (PowerShell)" -ForegroundColor Cyan  
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Host "✅ $pythonVersion detected" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8 or higher from https://python.org" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Navigate to the project root (two levels up from this script)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
Set-Location $projectRoot

# Check if we're in the right directory
if (-not (Test-Path "seratosync_gui.py")) {
    Write-Host "❌ Cannot find seratosync_gui.py" -ForegroundColor Red
    Write-Host "Make sure you're running this from the correct directory" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Run the Python build script
Write-Host "🚀 Running Python build script..." -ForegroundColor Blue
python scripts\build\build_windows.py

# Check if build was successful
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "====================================================" -ForegroundColor Green
    Write-Host " BUILD SUCCESSFUL!" -ForegroundColor Green
    Write-Host "====================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "The executable has been created in the 'dist' folder." -ForegroundColor Green
    Write-Host "You can now run SeratoSync_GUI.exe" -ForegroundColor Green
    Write-Host ""
    
    # Ask if user wants to open the dist folder
    $openFolder = Read-Host "Open dist folder? (y/n)"
    if ($openFolder -eq "y" -or $openFolder -eq "Y") {
        if (Test-Path "dist") {
            Start-Process "dist"
        }
    }
} else {
    Write-Host ""
    Write-Host "====================================================" -ForegroundColor Red
    Write-Host " BUILD FAILED!" -ForegroundColor Red
    Write-Host "====================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Check the error messages above for details." -ForegroundColor Yellow
    Write-Host ""
}

Read-Host "Press Enter to exit"
