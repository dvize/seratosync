# Serato Sync GUI - Standalone Windows Executable

## 📦 What's Included

- **SeratoSync_GUI.exe** - The complete Serato Sync application in a single executable file
- **Size**: ~26 MB
- **Requirements**: Windows 10/11 (64-bit)
- **Dependencies**: All included (no Python installation needed)

## 🚀 Quick Start

1. **Download**: Copy `SeratoSync_GUI.exe` to any folder on your computer
2. **Run**: Double-click the executable to launch
3. **Configure**: Set your library and Serato paths on first run
4. **Use**: All GUI features are identical to the Python version

## ⚡ First Launch

- Initial startup may take 10-30 seconds (extracting bundled files)
- Subsequent launches will be much faster
- Windows may show security warnings (click "More Info" → "Run anyway")

## 🛠️ Features

This standalone executable includes all the features of Serato Sync:

### Safety Features
- **V2 Database Detection**: Automatically detects Serato database version
- **Compatibility Warnings**: Prevents use with incompatible legacy databases
- **Backup System**: Create timestamped database backups before operations

### Main Operations
- **Dry Run**: Preview changes without modifying your database
- **Update Database**: Add new tracks to Serato database
- **Backup & Restore**: Manage database backups

### User Interface
- **Modern GUI**: CustomTkinter-based interface with dark/light mode support
- **Cross-Platform Paths**: Handles Windows and macOS path formats
- **Tooltips**: Helpful hints for all operations
- **Operation Log**: Real-time feedback and detailed logging

## 📁 Configuration

The application creates a `config.json` file in the same directory where you run it. This stores:
- Library root path
- Serato root path (_Serato_ folder)
- Supported file extensions

## 🔧 Troubleshooting

### Common Issues

**Windows Security Warning**
- Windows Defender may flag unknown executables
- Click "More info" → "Run anyway"
- Add to antivirus exclusions if needed

**Slow Startup**
- First run extracts embedded Python runtime
- Place executable on SSD for faster performance
- Subsequent runs will be much quicker

**Missing Paths**
- Configure library and Serato paths in the GUI
- Use the browse buttons to select correct directories

### Error Messages

**"Database not found"**
- Ensure you've selected the correct _Serato_ folder
- Look for the folder containing "database V2" file

**"Incompatible database version"**
- This tool only works with Serato V2 databases
- Do not use with legacy Serato installations

**"Permission denied"**
- Close Serato DJ before using this tool
- Run as administrator if needed
- Check that files aren't read-only

## 📋 Usage Workflow

1. **Initial Setup**
   - Launch SeratoSync_GUI.exe
   - Click "Browse" for Library Root (your music folder)
   - Click "Browse" for Serato Root (your _Serato_ folder)
   - Click "Save Config"

2. **Create Backup** (Recommended)
   - Click "Backup Database V2"
   - Note the backup file location

3. **Preview Changes**
   - Click "Dry Run" to see what would be added
   - Review the operation log

4. **Update Database**
   - Click "Update Database V2" to apply changes
   - Monitor the operation log for progress

## 🚨 Important Safety Notes

- **Serato V2 Only**: This tool only works with modern Serato installations
- **Backup First**: Always create a backup before making changes
- **Close Serato**: Ensure Serato DJ is closed before operations
- **Test Mode**: Use "Dry Run" to preview changes first

## 📞 Support

For issues or questions:
1. Check the operation log for detailed error messages
2. Verify your Serato version is V2 compatible
3. Ensure proper file permissions and Serato is closed
4. Try running from a different location

## 🔄 Updates

To update to a newer version:
1. Download the new executable
2. Replace the old SeratoSync_GUI.exe
3. Your config.json settings will be preserved

---

**Version**: Serato Sync GUI v2.0  
**Build Date**: September 25, 2025  
**Compatibility**: Serato V2 databases only  
**Platform**: Windows 10/11 (64-bit)
