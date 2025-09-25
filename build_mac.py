#!/usr/bin/env python3
"""
macOS App Builder for Serato Sync GUI

This script creates a native macOS application bundle (.app) from the 
Serato Sync GUI Python application using PyInstaller.
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
        "customtkinter>=5.0.0",
        "pillow>=9.0.0",
        "pyinstaller>=5.0"
    ]
    
    print("📦 Installing/updating dependencies...")
    for dep in dependencies:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✅ {dep}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {dep}: {e}")
            return False
    return True

def build_mac_app():
    """Build the macOS application bundle."""
    
    spec_file = "seratosync_gui_mac.spec"
    
    print("🔨 Building macOS application...")
    print(f"Using spec file: {spec_file}")
    print("-" * 50)
    
    cmd = [sys.executable, "-m", "PyInstaller", "--clean", spec_file]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print("✅ Build completed successfully!")
        
        app_path = Path("dist/SeratoSync GUI.app")
        if app_path.exists():
            print(f"📁 Application created: {app_path}")
            
            # Calculate app bundle size
            size_bytes = sum(f.stat().st_size for f in app_path.rglob('*') if f.is_file())
            size_mb = size_bytes / (1024 * 1024)
            print(f"📏 App bundle size: {size_mb:.1f} MB")
            
            return True
        else:
            print("❌ Application bundle not found after build")
            return False
            
    except subprocess.CalledProcessError as e:
        print("❌ Build failed!")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def create_dmg():
    """Create a DMG disk image for distribution (macOS only)."""
    app_path = Path("dist/SeratoSync GUI.app")
    if not app_path.exists():
        print("❌ Application bundle not found. Build the app first.")
        return False
        
    dmg_name = "SeratoSync_GUI_macOS.dmg"
    dmg_path = Path("dist") / dmg_name
    
    # Remove existing DMG
    if dmg_path.exists():
        dmg_path.unlink()
    
    print(f"📀 Creating DMG: {dmg_name}")
    
    # Create DMG using hdiutil
    cmd = [
        "hdiutil", "create",
        "-volname", "Serato Sync GUI",
        "-srcfolder", str(app_path),
        "-ov", "-format", "UDZO",
        str(dmg_path)
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ DMG created: {dmg_path}")
        
        # Show DMG size
        if dmg_path.exists():
            size_mb = dmg_path.stat().st_size / (1024 * 1024)
            print(f"📏 DMG size: {size_mb:.1f} MB")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create DMG: {e}")
        print("Note: DMG creation requires macOS hdiutil command")
        return False

def sign_app(app_path, identity=None):
    """Sign the macOS application (requires Apple Developer account)."""
    if not identity:
        print("ℹ️  Skipping code signing (no identity provided)")
        print("   For distribution, you'll need an Apple Developer certificate")
        return True
        
    print(f"✍️  Signing application with identity: {identity}")
    
    cmd = ["codesign", "--force", "--verify", "--verbose", "--sign", identity, str(app_path)]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Application signed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Code signing failed: {e}")
        print("STDERR:", e.stderr)
        return False

def main():
    print("🍎 Serato Sync GUI - macOS App Builder")
    print("=" * 50)
    
    # Check platform
    if not check_macos():
        sys.exit(1)
    
    # Check if we're in the right directory
    if not Path("seratosync_gui.py").exists():
        print("❌ Error: seratosync_gui.py not found in current directory")
        print("Please run this script from the seratosync project root.")
        sys.exit(1)
        
    if not Path("seratosync").exists():
        print("❌ Error: seratosync module directory not found")
        print("Please ensure the seratosync module is present.")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Build the app
    success = build_mac_app()
    
    if success:
        print("\n" + "=" * 50)
        print("🎉 SUCCESS!")
        print("Your macOS application is ready:")
        print("📁 Location: dist/SeratoSync GUI.app")
        
        # Ask about DMG creation
        try:
            create_dmg_response = input("\n📀 Create DMG for distribution? (y/n): ").lower().strip()
            if create_dmg_response in ['y', 'yes']:
                create_dmg()
        except KeyboardInterrupt:
            print("\n")
        
        print("\n📋 Distribution Notes:")
        print("• The .app bundle works on macOS 10.13+ (High Sierra)")
        print("• No Python installation required on target Macs")
        print("• For App Store distribution, code signing is required")
        print("• Test on different macOS versions before release")
        print("\n⚠️  First launch may show security warning")
        print("   Users should right-click → Open to bypass Gatekeeper")
        
    else:
        print("\n❌ Build failed. Check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
