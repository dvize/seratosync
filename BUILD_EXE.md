# Building Serato Sync GUI as Windows Executable

This guide explains how to create a standalone Windows executable (.exe) of the Serato Sync GUI application.

## Prerequisites

- Windows 10/11
- Python 3.7 or newer
- All Serato Sync project files

## Method 1: Automated Build (Recommended)

### Quick Build
1. Open Command Prompt or PowerShell in the project directory
2. Run the batch file:
   ```cmd
   build_exe.bat
   ```
3. The executable will be created in `dist\SeratoSync_GUI.exe`

### Python Script Build
Alternatively, use the Python build script:
```cmd
python build_exe.py
```

## Method 2: Manual Build

### Step 1: Install Build Requirements
```cmd
pip install -r requirements_build.txt
```

### Step 2: Build with PyInstaller
```cmd
python -m PyInstaller seratosync_gui.spec
```

### Step 3: Find Your Executable
The executable will be created at: `dist\SeratoSync_GUI.exe`

## Method 3: Custom PyInstaller Command

For advanced users who want to customize the build:

```cmd
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name SeratoSync_GUI ^
    --add-data "seratosync;seratosync" ^
    --hidden-import customtkinter ^
    --hidden-import PIL ^
    --collect-all customtkinter ^
    seratosync_gui.py
```

## Output

### File Details
- **Filename**: `SeratoSync_GUI.exe`
- **Location**: `dist/` directory
- **Size**: Approximately 50-80 MB (includes Python runtime and all dependencies)
- **Type**: Standalone executable (no Python installation required)

### Distribution
The executable is completely self-contained and includes:
- Python runtime
- All required libraries (CustomTkinter, Pillow, etc.)
- The Serato Sync application code
- All dependencies

## Usage Instructions for End Users

### System Requirements
- Windows 10 or newer (64-bit)
- No Python installation required
- Approximately 100 MB free disk space

### Installation
1. Download `SeratoSync_GUI.exe`
2. Place it in any folder (e.g., Desktop, Documents)
3. Double-click to run

### First Run
- The first startup may take 10-30 seconds as Windows extracts the embedded files
- Subsequent runs will be much faster
- Windows Defender may scan the file initially (this is normal)

### Configuration
The executable will create a `config.json` file in the same directory where it's run.

## Troubleshooting

### Build Issues

**Error: "PyInstaller not found"**
```cmd
pip install pyinstaller
```

**Error: "Module not found"**
- Ensure all required packages are installed
- Check that you're in the correct directory with `seratosync_gui.py`

**Build succeeds but exe doesn't run**
- Check Windows Event Viewer for detailed error messages
- Try running from Command Prompt to see error output:
  ```cmd
  dist\SeratoSync_GUI.exe
  ```

### Runtime Issues

**Antivirus False Positives**
- Some antivirus software may flag PyInstaller executables
- Add an exception for the exe file
- This is a known limitation of PyInstaller

**Slow Startup**
- First run extracts files (normal)
- Place exe on SSD for faster startup
- Exclude from real-time antivirus scanning

**Missing Dependencies**
- Rebuild with updated requirements
- Check that all imports are included in the spec file

## Advanced Configuration

### Adding an Icon
1. Create or obtain a `.ico` file
2. Edit `seratosync_gui.spec`:
   ```python
   icon='path/to/your/icon.ico'
   ```
3. Rebuild

### Reducing File Size
- Use `--exclude-module` to remove unused packages
- Consider using UPX compression (already enabled)
- Remove debug information

### Creating an Installer
Consider using tools like:
- NSIS (Nullsoft Scriptable Install System)
- Inno Setup
- WiX Toolset

## Development Notes

### Spec File Configuration
The `seratosync_gui.spec` file contains all build configuration:
- Hidden imports for dynamic modules
- Data files to include
- Exclusions for unused modules
- Output settings

### Testing
Always test the executable on a clean Windows system without Python installed to ensure all dependencies are properly bundled.

## File Structure After Build

```
project/
├── build/              # Temporary build files
├── dist/
│   └── SeratoSync_GUI.exe  # Your standalone executable
├── seratosync_gui.spec     # PyInstaller specification
├── build_exe.py           # Python build script
├── build_exe.bat          # Windows batch file
└── requirements_build.txt  # Build dependencies
```

## Support

For build issues:
1. Check this documentation
2. Verify all prerequisites are installed
3. Try the manual build method
4. Check PyInstaller documentation: https://pyinstaller.org/

The executable provides the same functionality as running the Python script directly, but with the convenience of a standalone application that works on any Windows system.
