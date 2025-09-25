# Serato Sync GUI Installation & Usage Guide

## Installation

### Option 1: Install with GUI Support
```bash
pip install -e .[gui]
```

### Option 2: Manual GUI Dependencies
```bash
pip install customtkinter pillow
```

Then install the main package:
```bash
pip install -e .
```

## Running the GUI

### Method 1: Direct Python Execution
```bash
python seratosync_gui.py
```

### Method 2: Through Package (if configured)
```bash
python -m seratosync.gui
```

## GUI Features

### 📁 Configuration Management
- **Simplified Setup**: Only requires Music Library Root and Serato Root Directory
- **Auto-Detection**: Database V2 path is automatically detected from Serato directory
- **Cross-Platform Paths**: Proper path normalization for Windows, macOS, and Linux
- **Auto-Load**: Configuration automatically loads from `config.json` in the application directory
- **Tooltips**: Hover over any field or button for helpful descriptions

### 🔄 Database Operations
- **Dry Run Preview**: See exactly what changes will be made without modifying anything (no database version restrictions)
- **Update Database V2**: Add new/modified tracks to Database V2 (creates automatic backup)
- **Backup/Restore**: Create and restore database backups with timestamping
- **Interactive Tooltips**: Hover over any button for detailed operation descriptions

### 🎯 Modern Interface
- **Cross-Platform**: Works on Windows, macOS, and Linux with native path handling
- **Dark Theme**: Modern dark interface with professional appearance
- **Organized Layout**: Separate sections for Preview, Crate Operations, and Database Operations
- **File Dialogs**: Native system file/directory selection dialogs

### 🛡️ Critical Safety Features
- **Serato V2 Only**: Automatic detection and blocking of legacy database formats
- **Startup Warning**: Clear compatibility warnings when launching
- **Database Version Check**: Real-time verification before any operations
- **Multiple Confirmations**: Extra safety dialogs for database-modifying operations
- **Cross-Platform Paths**: Proper path formatting for Windows, macOS, and Linux

### 📊 Operation Feedback
- **Live Logging**: See detailed operation progress in real-time
- **Status Updates**: Current operation and progress indicators
- **Error Handling**: Clear error messages and troubleshooting guidance

## GUI Workflow

1. **Application Startup**:
   - Read and acknowledge the Serato V2 compatibility warning
   - Confirm you are using Serato V2 (new beta) - NOT legacy versions

2. **First Time Setup**:
   - Enter your Music Library Root directory (hover for tooltip explanation)
   - Enter your Serato Root Directory (hover for tooltip explanation) 
   - Set audio extensions if needed (defaults to .mp3,.m4a,.aac,.flac,.wav)
   - Click "Save Configuration" (auto-saves to config.json with cross-platform paths)

3. **Preview Changes**:
   - Click "Dry Run (Preview Changes)" to see what will be modified (hover for tooltip)
   - Review the detailed output in the expanded log window

4. **Database Operations**:
   - Click "Update Database V2" to add new tracks (hover for tooltip - shows warnings)
   - Use "Backup Database V2" before making database changes (hover for tooltip)
   - Use "Restore Database V2" to recover from backups (hover for tooltip)
   - Monitor progress in the real-time log window

**💡 Tip**: Hover over any field or button to see helpful tooltips explaining what each operation does!

3. **Configuration Changes**:
   - Click "Load Config" to modify existing settings
   - Update paths as needed
   - Save changes with "Save Config"

## Performance Features

### 🚀 Selective Crate Updates
The GUI automatically uses our optimized selective crate updating:
- **Before**: Rewrote all 1251 crates (slow)
- **After**: Only updates affected crates (typically 1-10 crates)
- **Result**: 99%+ performance improvement

### 🎯 Operation Types
- **Dry Run Preview**: See changes without making any modifications (completely safe)
- **Sync Crates (Safe Mode)**: Update only crate files, never touches Database V2 (completely safe)
- **Update Database V2**: Add new tracks to Database V2 (creates automatic backup first)

## Troubleshooting

### Common Issues
1. **"ModuleNotFoundError: customtkinter"**
   - Run: `pip install customtkinter pillow`

2. **GUI doesn't start**
   - Ensure Python 3.7+ is installed
   - Check that all dependencies are installed correctly

3. **File dialog issues**
   - On Linux, ensure tkinter is properly installed
   - Try: `sudo apt-get install python3-tk` (Ubuntu/Debian)

### Error Messages
- **"Config file not found"**: Create a new config first
- **"Invalid Serato directory"**: Ensure the path contains `_Serato_/` folder
- **"Database write failed"**: Check write permissions in sync directory

## Technical Details

### Dependencies
- **customtkinter>=5.2.0**: Modern GUI framework
- **pillow>=9.0.0**: Image processing (required by customtkinter)
- **Standard Library**: pathlib, json, subprocess, threading, tkinter

### File Locations
- **Config File**: `config.json` (in project root)
- **GUI Script**: `seratosync_gui.py`
- **Log Output**: Real-time in GUI log window

### Cross-Platform Compatibility
- **Windows**: Full support with native file dialogs
- **macOS**: Full support with native file dialogs
- **Linux**: Full support (requires python3-tk package)

## Advanced Usage

### Command Line Integration
The GUI uses the same CLI backend, so you can mix GUI and command-line usage:

```bash
# Use GUI for config, CLI for automation
python seratosync_gui.py  # Create config
seratosync --config config.json  # Automated sync
```

### Batch Operations
For automation or scripting, use the CLI with the config created in the GUI:
```bash
seratosync --config config.json --update  # Update only
seratosync --config config.json           # Full sync
```

## Support

For issues or questions:
1. Check the main README.md for CLI documentation
2. Review REFACTORING_SUMMARY.md for technical details
3. Examine log output in GUI for specific error messages

The GUI provides the same powerful Serato sync functionality as the CLI with an intuitive, modern interface perfect for regular use and configuration management.
