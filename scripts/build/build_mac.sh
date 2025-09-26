#!/bin/bash

# Serato Sync GUI - macOS App Builder Script
# This script builds a native macOS application from the Python GUI

echo "🍎 Serato Sync GUI - macOS App Builder"
echo "====================================="

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ Error: This script must be run on macOS"
    echo "Current OS: $OSTYPE"
    exit 1
fi

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Change to project root
cd "$PROJECT_ROOT"

# Check if we're in the right directory
if [[ ! -f "seratosync_gui.py" ]]; then
    echo "❌ Error: seratosync_gui.py not found"
    echo "Please ensure the script can find the project root"
    echo "Project root: $PROJECT_ROOT"
    exit 1
fi

if [[ ! -d "seratosync" ]]; then
    echo "❌ Error: seratosync module directory not found"
    exit 1
fi

echo "📦 Installing build dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install pyinstaller kivy "git+https://github.com/kivymd/KivyMD.git" pillow materialyoucolor asynckivy asyncgui

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "🔨 Building macOS application..."
echo "Using spec file: scripts/build/seratosync_gui_mac.spec"
echo "Project root: $PROJECT_ROOT"
echo "-------------------------------------"

# Clean previous builds
rm -rf build/ dist/

# Build the application
python3 -m PyInstaller --clean scripts/build/seratosync_gui_mac.spec

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build completed successfully!"
    
    if [[ -d "dist/SeratoSync GUI.app" ]]; then
        echo "📁 Application created: dist/SeratoSync GUI.app"
        
        # Calculate size
        SIZE=$(du -sh "dist/SeratoSync GUI.app" | cut -f1)
        echo "📏 App bundle size: $SIZE"
        
        echo ""
        echo "====================================="
        echo "🎉 SUCCESS!"
        echo "Your macOS application is ready:"
        echo "📁 Location: dist/SeratoSync GUI.app"
        echo ""
        echo "📋 To distribute:"
        echo "1. Copy the .app bundle to target Macs"
        echo "2. No Python installation required"
        echo "3. Works on macOS 10.13+ (High Sierra)"
        echo ""
        echo "⚠️  Security Note:"
        echo "First launch may show security warning"
        echo "Users should right-click → Open to bypass"
        echo ""
        
        # Ask about DMG creation
        read -p "📀 Create DMG for distribution? (y/n): " create_dmg
        if [[ $create_dmg =~ ^[Yy]$ ]]; then
            echo "📀 Creating DMG..."
            DMG_NAME="SeratoSync_GUI_macOS.dmg"
            
            # Remove existing DMG
            rm -f "dist/$DMG_NAME"
            
            # Create DMG
            hdiutil create -volname "Serato Sync GUI" -srcfolder "dist/SeratoSync GUI.app" -ov -format UDZO "dist/$DMG_NAME"
            
            if [ $? -eq 0 ]; then
                echo "✅ DMG created: dist/$DMG_NAME"
                DMG_SIZE=$(du -sh "dist/$DMG_NAME" | cut -f1)
                echo "📏 DMG size: $DMG_SIZE"
            else
                echo "❌ Failed to create DMG"
            fi
        fi
        
    else
        echo "❌ Application bundle not found after build"
        exit 1
    fi
else
    echo ""
    echo "❌ Build failed!"
    echo "Check the error messages above for details"
    exit 1
fi
