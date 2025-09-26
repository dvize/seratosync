#!/usr/bin/env python3
"""
macOS App Builder for Serato Sync GUI (Kivy Version)

This script creates a native macOS application bundle (.app) from the 
Serato Sync GUI Python application using PyInstaller with Kivy/KivyMD.
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path

def check_macos():
    """Check if running on macOS."""
    if sys.platform != 'darwin':
        print("❌ Error: This script must be run on macOS")
        print(f"Current platform: {sys.platform}")
        return False
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

def install_pyinstaller():
    """Install PyInstaller if not already installed."""
    try:
        import PyInstaller
        print(f"✅ PyInstaller {PyInstaller.__version__} is already installed")
        return True
    except ImportError:
        print("📦 Installing PyInstaller...")
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], 
                                  capture_output=True, text=True, check=True)
            print("✅ PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install PyInstaller")
            print(f"Error: {e.stderr}")
            return False

def install_dependencies():
    """Install required dependencies for macOS build."""
    dependencies = [
        "kivy>=2.3.0",
        "git+https://github.com/kivymd/KivyMD.git",
        "pillow>=9.0.0",
        "pyinstaller>=5.0",
        "materialyoucolor",
        "asynckivy",
        "asyncgui"
    ]
    
    print("📦 Installing/updating dependencies...")
    for dep in dependencies:
        try:
            print(f"Installing {dep}...")
            result = subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                                  capture_output=True, text=True, check=True)
            print(f"✅ {dep} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {dep}")
            print(f"Error: {e.stderr}")
            return False
    
    print("✅ Dependencies installation completed")
    return True

def clean_build_dirs():
    """Clean up previous build directories."""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"🧹 Cleaning {dir_name}...")
            shutil.rmtree(dir_name)


def build_app():
    """Build the macOS application using PyInstaller."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    spec_file = script_dir / "seratosync_gui_mac.spec"
    
    if not spec_file.exists():
        print(f"❌ Error: {spec_file} not found!")
        return False
    
    # Check if GUI file exists
    gui_file = project_root / "seratosync_gui.py"
    if not gui_file.exists():
        print(f"❌ GUI file not found: {gui_file}")
        return False
    
    print(f"📁 Project root: {project_root}")
    print(f"📄 Spec file: {spec_file}")
    print(f"📄 GUI file: {gui_file}")
    
    print("🔨 Building macOS application...")
    
    # Change to project root directory
    original_cwd = os.getcwd()
    os.chdir(project_root)
    
    try:
        # Run PyInstaller with the spec file
        cmd = [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", str(spec_file)]
        print(f"🚀 Running command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Build completed successfully!")
            
            # Print build output for debugging
            if result.stdout:
                print("Build output:")
                print(result.stdout[-1000:])  # Show last 1000 chars
            
            return True
        else:
            print("❌ Build failed!")
            print(f"Return code: {result.returncode}")
            print(f"Command: {' '.join(cmd)}")
            if result.stdout:
                print("Standard output:")
                print(result.stdout[-1000:])  # Show last 1000 chars
            if result.stderr:
                print("Error output:")
                print(result.stderr[-1000:])  # Show last 1000 chars
            return False
            
    except Exception as e:
        print(f"❌ Build failed with error: {e}")
        return False
    finally:
        # Restore original working directory
        os.chdir(original_cwd)

def verify_app():
    """Verify the built application exists and is valid."""
    app_path = "dist/SeratoSync GUI.app"
    
    if not os.path.exists(app_path):
        print("❌ Application bundle not found!")
        return False
    
    # Check if the executable exists
    exe_path = os.path.join(app_path, "Contents/MacOS/SeratoSync_GUI")
    if not os.path.exists(exe_path):
        print("❌ Executable not found in app bundle!")
        return False
    
    # Check app bundle structure
    required_dirs = [
        "Contents",
        "Contents/MacOS", 
        "Contents/Resources"
    ]
    
    for req_dir in required_dirs:
        full_path = os.path.join(app_path, req_dir)
        if not os.path.exists(full_path):
            print(f"❌ Missing required directory: {req_dir}")
            return False
    
    print(f"✅ Application bundle created successfully: {app_path}")
    return True

def get_app_info():
    """Get information about the built application."""
    app_path = "dist/SeratoSync GUI.app"
    
    if os.path.exists(app_path):
        # Get app bundle size
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(app_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        
        size_mb = total_size / (1024 * 1024)
        print(f"📊 App bundle size: {size_mb:.1f} MB")
        print(f"📁 Location: {os.path.abspath(app_path)}")

def main():
    """Main build process."""
    print("🍎 Serato Sync GUI - macOS Kivy App Builder")
    print("=" * 50)
    
    # Check if running on macOS
    if not check_macos():
        return False
    
    check_virtual_environment()
    
    # Install PyInstaller
    if not install_pyinstaller():
        return False
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        return False
    
    # Clean previous builds
    clean_build_dirs()
    
    # Build the application
    if not build_app():
        print("❌ Build process failed")
        return False
    
    # Verify the build
    if not verify_app():
        return False
    
    # Show app info
    get_app_info()
    
    print("🎉 Build completed successfully!")
    print("You can find the app in the 'dist' folder")
    print("To test: Double-click 'Serato Sync GUI.app' in Finder")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
