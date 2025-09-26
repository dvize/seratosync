# SeratoSync GUI v0.0.1 - macOS Release

## What's Included

- **SeratoSync GUI.app** - The main application
- **config_example.json** - Example configuration file

## Quick Start

### 1. Setup
1. Move `SeratoSync GUI.app` to your Applications folder (optional)
2. Copy `config_example.json` to the same folder as the app and rename it to `config.json`
3. Edit `config.json` with your actual paths (or use the GUI to configure)

### 2. First Run
1. Double-click `SeratoSync GUI.app` to launch
2. If you see a security warning, go to System Preferences > Security & Privacy and click "Open Anyway"
3. Configure your paths using the folder picker buttons in the GUI
4. Click "Sync Music Folders to Crates" to create crates from your music library

### 3. Configuration
Update the paths in `config.json` or use the GUI:

```json
{
  "db": "~/Music/_Serato_/database V2",
  "library_root": "~/Music/Music Tracks", 
  "serato_root": "~/Music/_Serato_",
  "exts": ".mp3,.m4a,.aac,.flac,.wav"
}
```

**Path Examples:**
- Database V2: `/Users/yourusername/Music/_Serato_/database V2`
- Library Root: `/Users/yourusername/Music/Music Tracks`
- Serato Root: `/Users/yourusername/Music/_Serato_`

## Features

- 🎯 **Modern GUI** - Intuitive dark theme interface
- 📁 **Visual Path Selection** - Browse and select folders with native dialogs  
- 🔄 **Smart Sync** - Only updates crates that actually changed
- 🛡️ **Safe Operation** - Automatic database backups before changes
- ⚡ **Fast Performance** - Optimized for large music libraries

## Usage

1. **Sync Crates**: Creates/updates Serato crates to match your folder structure
2. **Update Database**: Optionally adds new tracks to your Serato database
3. **Dry Run**: Preview changes before applying them

## Troubleshooting

**Security Warning**: 
- Go to System Preferences > Security & Privacy > General
- Click "Open Anyway" when the warning appears

**App Won't Launch**:
- Make sure you're running macOS 10.14 or later
- Try running from Terminal: `open "SeratoSync GUI.app"`

**Path Issues**:
- Use the GUI path pickers instead of editing config manually
- Make sure your `_Serato_` folder exists
- Verify Serato DJ is installed and has been run at least once

## Support

For issues or questions:
- Check the main README.md for detailed documentation
- Report bugs on the GitHub repository
- Make sure your music library and Serato paths are correct

## Version Info

- **Version**: 0.0.1
- **Build**: macOS Universal
- **Size**: ~207 MB
- **Requirements**: macOS 10.14+
