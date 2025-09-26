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

def install_pyinstaller():
    """Install PyInstaller if not already installed."""
    try:
        import PyInstaller
        print("✅ PyInstaller is already installed")
        return True
    except ImportError:
        print("📦 Installing PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✅ PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install PyInstaller: {e}")
            return False

def install_dependencies():
    """Install required dependencies for macOS build."""
    dependencies = [
        "kivy>=2.3.0",
        "kivymd>=2.0.0",
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
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Warning: Failed to install {dep}: {e}")
    
    print("✅ Dependencies installation completed")

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
    spec_file = script_dir / "seratosync_gui_mac.spec"
    
    if not spec_file.exists():
        print(f"❌ Error: {spec_file} not found!")
        return False
    
    print("🔨 Building macOS application...")
    try:
        # Run PyInstaller with the spec file
        cmd = [sys.executable, "-m", "PyInstaller", "--clean", str(spec_file)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Build completed successfully!")
            return True
        else:
            print("❌ Build failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed with error: {e}")
        return False

def verify_app():
    """Verify the built application exists and is valid."""
    app_path = "dist/SeratoSync GUI.app"
    
    if not os.path.exists(app_path):
        print("❌ Application bundle not found!")
        return False
    
    # Check if the executable exists
    exe_path = os.path.join(app_path, "Contents/MacOS/SeratoSync_GUI_Kivy")
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
    
    # Install PyInstaller
    if not install_pyinstaller():
        return False
    
    # Install dependencies
    install_dependencies()
    
    # Clean previous builds
    clean_build_dirs()
    
    # Build the application
    if not build_app():
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
