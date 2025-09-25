#!/usr/bin/env python3
"""
Build script for creating Windows executable of Serato Sync GUI
"""

import subprocess
import sys
import os
from pathlib import Path

def install_pyinstaller():
    """Install PyInstaller if not already installed."""
    try:
        import PyInstaller
        print("✅ PyInstaller is already installed")
    except ImportError:
        print("📦 Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller installed successfully")

def build_executable():
    """Build the standalone executable."""
    
    # Ensure PyInstaller is installed
    install_pyinstaller()
    
    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                    # Single executable file
        "--windowed",                   # No console window
        "--name", "SeratoSync_GUI",     # Output filename
        "--icon", "NONE",               # No icon for now
        "--add-data", "seratosync;seratosync",  # Include seratosync module
        "--hidden-import", "customtkinter",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL._tkinter_finder",
        "--collect-all", "customtkinter",
        "--collect-all", "tkinter",
        "seratosync_gui.py"
    ]
    
    print("🔨 Building executable...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print("✅ Build completed successfully!")
        print(f"📁 Executable created: dist/SeratoSync_GUI.exe")
        
        # Show file size
        exe_path = Path("dist/SeratoSync_GUI.exe")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"📏 File size: {size_mb:.1f} MB")
            
    except subprocess.CalledProcessError as e:
        print("❌ Build failed!")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
        
    return True

if __name__ == "__main__":
    print("🚀 Serato Sync GUI - Windows Executable Builder")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("seratosync_gui.py").exists():
        print("❌ Error: seratosync_gui.py not found in current directory")
        print("Please run this script from the seratosync project root.")
        sys.exit(1)
        
    if not Path("seratosync").exists():
        print("❌ Error: seratosync module directory not found")
        print("Please ensure the seratosync module is present.")
        sys.exit(1)
    
    success = build_executable()
    
    if success:
        print("\n" + "=" * 50)
        print("🎉 SUCCESS!")
        print("Your standalone executable is ready:")
        print("📁 Location: dist/SeratoSync_GUI.exe")
        print("\n📋 To distribute:")
        print("1. Copy SeratoSync_GUI.exe to target computer")
        print("2. No Python installation required on target")
        print("3. The exe includes all dependencies")
        print("\n⚠️  Note: First run may be slow as it extracts files")
    else:
        print("\n❌ Build failed. Check the error messages above.")
        sys.exit(1)
