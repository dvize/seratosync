# Building Serato Sync GUI for macOS

This guide explains how to create a native macOS application (.app bundle) from the Serato Sync GUI.

## Prerequisites

- **macOS 10.13+** (High Sierra or newer)
- **Python 3.7+** with tkinter support
- **Xcode Command Line Tools** (for some dependencies)
- All Serato Sync project files

## Installation of Command Line Tools

If you haven't installed Xcode Command Line Tools:
```bash
xcode-select --install
```

## Method 1: Automated Build (Recommended)

### Using Python Script
```bash
python3 build_mac.py
```

### Using Shell Script
```bash
chmod +x build_mac.sh
./build_mac.sh
```

Both methods will:
1. Install required dependencies
2. Build the .app bundle
3. Optionally create a DMG for distribution

## Method 2: Manual Build

### Step 1: Install Dependencies
```bash
pip3 install pyinstaller customtkinter pillow
```

### Step 2: Build Application
```bash
python3 -m PyInstaller --clean seratosync_gui_mac.spec
```

### Step 3: Find Your App
The application will be created at: `dist/SeratoSync GUI.app`

## Method 3: Custom PyInstaller Build

For advanced users who want to customize:

```bash
python3 -m PyInstaller \
    --name "SeratoSync GUI" \
    --windowed \
    --add-data "seratosync:seratosync" \
    --hidden-import customtkinter \
    --hidden-import PIL \
    --collect-all customtkinter \
    --osx-bundle-identifier com.seratosync.gui \
    seratosync_gui.py
```

## Output Details

### Application Bundle
- **Name**: `SeratoSync GUI.app`
- **Location**: `dist/` directory  
- **Size**: Approximately 40-60 MB
- **Compatibility**: macOS 10.13+ (High Sierra)
- **Architecture**: Matches your Python installation (Intel/Apple Silicon)

### What's Included
- Python runtime (embedded)
- CustomTkinter framework
- PIL/Pillow imaging library
- All Serato Sync modules
- Complete dependency tree

## Distribution Options

### Option 1: App Bundle Only
Distribute the `.app` file directly:
- Users drag to Applications folder
- Right-click → Open on first launch (security)
- No installer needed

### Option 2: DMG Disk Image
Create a professional disk image:
```bash
hdiutil create -volname "Serato Sync GUI" \
    -srcfolder "dist/SeratoSync GUI.app" \
    -ov -format UDZO \
    SeratoSync_GUI_macOS.dmg
```

### Option 3: ZIP Archive
Simple compressed distribution:
```bash
cd dist
zip -r SeratoSync_GUI_macOS.zip "SeratoSync GUI.app"
```

## Code Signing (Optional)

For wider distribution without security warnings:

### Requirements
- Apple Developer Account ($99/year)
- Developer ID Application certificate

### Signing Command
```bash
codesign --force --verify --verbose \
    --sign "Developer ID Application: Your Name" \
    "dist/SeratoSync GUI.app"
```

### Verification
```bash
codesign --verify --verbose "dist/SeratoSync GUI.app"
spctl --assess --verbose "dist/SeratoSync GUI.app"
```

## Notarization (For macOS 10.15+)

For apps distributed outside the App Store:

### Requirements
- Code signed application
- Apple Developer account
- App-specific password

### Notarization Process
```bash
# Create ZIP for notarization
ditto -c -k --keepParent "dist/SeratoSync GUI.app" SeratoSync_GUI.zip

# Submit for notarization
xcrun altool --notarize-app \
    --primary-bundle-id "com.seratosync.gui" \
    --username "your@email.com" \
    --password "@keychain:AC_PASSWORD" \
    --file SeratoSync_GUI.zip

# Check status (use RequestUUID from previous command)
xcrun altool --notarization-info <RequestUUID> \
    --username "your@email.com" \
    --password "@keychain:AC_PASSWORD"

# Staple the ticket (after approval)
xcrun stapler staple "dist/SeratoSync GUI.app"
```

## Troubleshooting

### Common Build Issues

**"tkinter not found"**
- Install Python with tkinter support: `brew install python-tk`
- Or use official Python.org installer

**"Permission denied"**
- Make shell script executable: `chmod +x build_mac.sh`
- Check file permissions in project directory

**"Module not found" during build**
- Ensure all dependencies installed: `pip3 install -r requirements_build.txt`
- Check virtual environment if using one

### Runtime Issues

**"App is damaged" message**
- App needs code signing or user must right-click → Open
- Clear quarantine: `xattr -cr "SeratoSync GUI.app"`

**Slow startup**
- First launch extracts embedded Python (normal)
- Subsequent launches much faster
- Place on SSD for better performance

**"Cannot verify developer"**
- App needs notarization for automatic approval
- User can override: System Preferences → Security → Allow anyway

### Architecture Issues

**Intel vs Apple Silicon**
- Build on target architecture for best performance
- Universal binaries possible but complex
- Intel builds run on Apple Silicon via Rosetta 2

## Testing Checklist

Before distribution, test on:
- [ ] Same macOS version as build machine
- [ ] Different macOS versions (if possible)
- [ ] Clean Mac without Python installed
- [ ] Both Intel and Apple Silicon Macs
- [ ] Network drives and external storage
- [ ] Different user accounts and permissions

## File Structure After Build

```
project/
├── build/                          # Temporary build files
├── dist/
│   ├── SeratoSync GUI.app/         # Your macOS application
│   └── SeratoSync_GUI_macOS.dmg    # Distribution disk image
├── seratosync_gui_mac.spec         # PyInstaller spec for macOS
├── build_mac.py                    # Python build script
└── build_mac.sh                    # Shell build script
```

## Performance Optimization

### Reducing Bundle Size
- Exclude unused modules: `--exclude-module`
- Remove debug symbols: `strip=True` in spec
- Use UPX compression: `upx=True` (already enabled)

### Startup Performance  
- Profile imports to identify slow modules
- Consider lazy imports for non-critical features
- Optimize embedded resource loading

## Deployment Best Practices

### For Internal Use
- Simple .app bundle distribution
- Document security bypass steps
- Provide direct download link

### For Public Distribution
- Code sign and notarize
- Create professional DMG with background image
- Provide clear installation instructions
- Include uninstall information

### For Enterprise
- Consider mobile device management (MDM)
- Create installer packages (.pkg)
- Include configuration management
- Document security policies

## Version Management

Update version in `seratosync_gui_mac.spec`:
```python
app = BUNDLE(
    # ...
    version='2.1.0',
    info_plist={
        'CFBundleShortVersionString': '2.1.0',
        'CFBundleVersion': '2.1.0',
        # ...
    },
)
```

This ensures proper version tracking in macOS.

## Support Resources

- **PyInstaller Documentation**: https://pyinstaller.org/
- **Apple Developer**: https://developer.apple.com/
- **macOS Distribution**: https://developer.apple.com/distribution/
- **Code Signing Guide**: https://developer.apple.com/library/archive/documentation/Security/Conceptual/CodeSigningGuide/

The resulting application provides the same functionality as the Python script but packaged as a native macOS application that can be distributed to users without Python installations.
