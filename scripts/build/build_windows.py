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

def check_virtual_environment():
    """Check if we're running in a virtual environment."""
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if in_venv:
        print("✅ Running in virtual environment")
        venv_path = sys.prefix
        print(f"📁 Virtual environment: {venv_path}")
    else:
        print("⚠️  Not running in a virtual environment")
        print("   It's recommended to use a virtual environment for building")
    return True

def check_pyinstaller():
    """Check if PyInstaller is installed."""
    try:
        import PyInstaller
        print(f"✅ PyInstaller {PyInstaller.__version__} is already installed")
        return True
    except ImportError:
        print("📦 Installing PyInstaller...")
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller>=5.0"], 
                         check=True, capture_output=True, text=True)
            print("✅ PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install PyInstaller")
            print(f"Error: {e.stderr}")
            return False

def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing/updating dependencies...")
    
    dependencies = [
        "kivy>=2.3.0",
        "git+https://github.com/kivymd/KivyMD.git", 
        "pillow>=9.0.0",
        "pyinstaller>=5.0",
        "materialyoucolor",
        "asynckivy",
        "asyncgui",
    ]
    
    for dep in dependencies:
        print(f"Installing {dep}...")
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                         check=True, capture_output=True, text=True)
            print(f"✅ {dep} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {dep}")
            print(f"Error: {e.stderr}")
            return False
    
    print("✅ Dependencies installation completed")
    return True

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
    
    # Check if spec file exists
    if not spec_file.exists():
        print(f"❌ Spec file not found: {spec_file}")
        return False
    
    # Check if GUI file exists
    gui_file = project_root / "seratosync_gui.py"
    if not gui_file.exists():
        print(f"❌ GUI file not found: {gui_file}")
        return False
    
    print(f"📁 Project root: {project_root}")
    print(f"📄 Spec file: {spec_file}")
    print(f"📄 GUI file: {gui_file}")
    
    # Change to project root directory
    original_cwd = os.getcwd()
    os.chdir(project_root)
    
    try:
        # Build command
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm", 
            str(spec_file)
        ]
        
        print(f"🚀 Running command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Build completed successfully!")
        
        # Print build output for debugging
        if result.stdout:
            print("Build output:")
            print(result.stdout[-1000:])  # Show last 1000 chars
            
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed!")
        print(f"Return code: {e.returncode}")
        print(f"Command: {' '.join(cmd)}")
        if e.stdout:
            print("Standard output:")
            print(e.stdout[-1000:])  # Show last 1000 chars
        if e.stderr:
            print("Error output:")
            print(e.stderr[-1000:])  # Show last 1000 chars
        return False
    finally:
        # Restore original working directory
        os.chdir(original_cwd)

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
    
    check_virtual_environment()
    
    if not check_pyinstaller():
        return False
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        return False
    
    # Clean previous builds
    clean_build_dirs()
    
    # Build the executable
    if not build_executable():
        print("❌ Build process failed")
        return False
    
    # Check the result
    exe_path = os.path.join("dist", "SeratoSync_GUI", "SeratoSync_GUI.exe")
    if os.path.exists(exe_path):
        size = get_exe_size(exe_path)
        print("✅ Executable created successfully!")
        print(f"📊 Executable size: {size}")
        print(f"📁 Location: {os.path.abspath(exe_path)}")
        print("🎉 Build completed successfully!")
        print("You can find the executable in the 'dist/SeratoSync_GUI' folder")
        print("To test: Double-click 'SeratoSync_GUI.exe'")
        return True
    else:
        print("❌ Executable was not created!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
