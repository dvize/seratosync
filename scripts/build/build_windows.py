#!/usr/bin/env python3
"""
Windows Build Script for SeratoSync GUI

This script builds a standalone Windows executable using PyInstaller with the Kivy/KivyMD GUI.
Run this on a Windows machine with Python and the required dependencies installed.

Requirements:
- Python 3.8+
- pip
- Virtual environment (recommended)

Usage:
    python scripts/build/build_windows.py
"""

import os
import sys
import subprocess
import shutil
import time
from pathlib import Path

def print_banner():
    """Print the build banner."""
    print("🪟 Serato Sync GUI - Windows App Builder")
    print("=" * 50)

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def check_pyinstaller():
    """Check if PyInstaller is installed."""
    try:
        import PyInstaller
        print("✅ PyInstaller is already installed")
        return True
    except ImportError:
        print("📦 Installing PyInstaller...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller>=5.0"], 
                         check=True, capture_output=True)
            print("✅ PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install PyInstaller: {e}")
            return False

def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing/updating dependencies...")
    
    dependencies = [
        "kivy>=2.3.0",
        "kivymd>=2.0.0", 
        "pillow>=9.0.0",
        "pyinstaller>=5.0",
        "materialyoucolor",
        "asynckivy",
        "asyncgui",
    ]
    
    for dep in dependencies:
        print(f"Installing {dep}...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Warning: Failed to install {dep}: {e}")
    
    print("✅ Dependencies installation completed")

def clean_build_dirs():
    """Clean build and dist directories."""
    print("🧹 Cleaning build directories...")
    
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"🧹 Cleaned {dir_name}")
            except Exception as e:
                print(f"⚠️  Warning: Could not clean {dir_name}: {e}")

def build_executable():
    """Build the Windows executable using PyInstaller."""
    print("🔨 Building Windows application...")
    
    # Get the current script directory and project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    spec_file = script_dir / "seratosync_gui_windows.spec"
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm", 
        str(spec_file)
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed!")
        print(f"Return code: {e.returncode}")
        print(f"Error output: {e.stderr}")
        return False

def get_exe_size(exe_path):
    """Get the size of the executable file."""
    if os.path.exists(exe_path):
        size_bytes = os.path.getsize(exe_path)
        size_mb = size_bytes / (1024 * 1024)
        return f"{size_mb:.1f} MB"
    return "Unknown"

def main():
    """Main build function."""
    print_banner()
    
    # Check requirements
    if not check_python_version():
        return False
    
    if not check_pyinstaller():
        return False
    
    # Install dependencies
    install_dependencies()
    
    # Clean previous builds
    clean_build_dirs()
    
    # Build the executable
    if not build_executable():
        return False
    
    # Check the result
    exe_path = os.path.join("dist", "SeratoSync_GUI.exe")
    if os.path.exists(exe_path):
        size = get_exe_size(exe_path)
        print("✅ Executable created successfully!")
        print(f"📊 Executable size: {size}")
        print(f"📁 Location: {os.path.abspath(exe_path)}")
        print("🎉 Build completed successfully!")
        print("You can find the executable in the 'dist' folder")
        print("To test: Double-click 'SeratoSync_GUI.exe'")
        return True
    else:
        print("❌ Executable was not created!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
