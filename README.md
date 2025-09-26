# SeratoSync GUI

A modern desktop application that automatically syncs your music library folders to Serato crates and manages your Serato database.

![SeratoSync GUI](https://img.shields.io/badge/GUI-Kivy%2FKivyMD-blue) ![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-green) ![Python](https://img.shields.io/badge/Python-3.8%2B-yellow)

## 🎯 Quick Start

### Download Pre-built Applications

**For most users, download the ready-to-use applications:**

- **Windows**: Download `SeratoSync_GUI.exe` from releases
- **macOS**: Download `SeratoSync GUI.app` from releases

### First Time Setup

1. **Launch the application**
2. **Configure your paths** using the built-in path selectors:
   - **Serato Root**: Your `_Serato_` folder (usually in Music folder)
   - **Library Root**: Your music library folder
   - **Database Path**: Your `Database V2` file (inside `_Serato_` folder)
3. **Click "Sync Music Folders to Crates"** to create crates matching your folder structure
4. **Optionally enable "Update Database V2"** to add new tracks to Serato

## ✨ Features

### 🖥️ Modern GUI Interface
- **Intuitive Design**: Clean, modern interface with dark theme
- **Visual Path Selection**: Browse and select folders/files with native dialogs
- **Real-time Progress**: Live progress bars and detailed logging
- **One-Click Operations**: Sync and update with single button clicks
- **Configuration Management**: Automatic saving and loading of settings

### 🔄 Smart Sync Technology  
- **Folder-to-Crate Mapping**: Automatically creates Serato crates matching your folder structure
- **Selective Updates**: Only updates crates that actually changed (performance optimized)
- **New Track Detection**: Intelligently identifies tracks not in your Serato database
- **Path Normalization**: Handles different path formats across platforms
- **Dry Run Mode**: Preview changes before applying them

### 🛡️ Safety Features
- **Database Backups**: Automatic timestamped backups before any database changes
- **Safe by Default**: Never modifies your Serato database unless explicitly requested  
- **Version Detection**: Ensures compatibility with Serato Database V2 format
- **Error Recovery**: Comprehensive error handling and recovery
- **Non-destructive**: Designed to be completely safe for your music library

## 📥 Installation

### Option 1: Pre-built Applications (Recommended)

**Simply download and run - no installation required!**

- **Windows**: Download `SeratoSync_GUI.exe` 
- **macOS**: Download `SeratoSync GUI.app`

### Option 2: Build from Source

#### Windows Build
```cmd
# Download/clone the repository
git clone https://github.com/dvize/seratosync.git
cd seratosync

# Run the build script (double-click in File Explorer)
scripts\build\build_windows.bat

# Or run manually:
python scripts\build\build_windows.py
```

#### macOS Build  
```bash
# Download/clone the repository
git clone https://github.com/dvize/seratosync.git
cd seratosync

# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Build the app
python scripts/build/build_mac.py
```

#### Development Installation
```bash
# Clone repository
git clone https://github.com/dvize/seratosync.git
cd seratosync

# Install in development mode
pip install -e .

# Install GUI dependencies
pip install kivy kivymd pillow materialyoucolor asynckivy asyncgui

# Run from source
python seratosync_gui.py
```

## 🚀 How to Use

### GUI Usage (Recommended)

1. **Launch SeratoSync GUI**
   - Windows: Double-click `SeratoSync_GUI.exe`
   - macOS: Double-click `SeratoSync GUI.app`

2. **Configure Paths** (first time only)
   - Click 📁 next to **Serato Root** and select your `_Serato_` folder
   - Click 📁 next to **Library Root** and select your music library folder  
   - Click 📁 next to **Database Path** and select your `Database V2` file
   - Settings are automatically saved for next time

3. **Sync Your Music**
   - Click **"Sync Music Folders to Crates"** to create/update crates
   - Enable **"Update Database V2"** checkbox to add new tracks to Serato
   - Use **"Dry Run"** to preview changes first
   - Watch the progress bar and log for real-time updates

### Command Line Usage (Advanced)

For automation or advanced users, the CLI is still available:

```bash
# Basic sync with config file
python -m seratosync --config config.json

# Manual path specification
python -m seratosync \
    --db "/path/to/Database V2" \
    --library-root "/path/to/Music Library" \
    --serato-root "/path/to/_Serato_"

# Preview changes without making them  
python -m seratosync --dry-run

# Add new tracks to database
python -m seratosync --update-db
```

## ⚙️ Configuration

### GUI Configuration (Automatic)

The GUI automatically manages configuration:
- **First Run**: Use the path selector buttons to set up your folders
- **Automatic Saving**: Settings are saved automatically when you make changes
- **Persistent**: Your configuration persists between application restarts

### Manual Configuration (Advanced)

For CLI usage or advanced customization, you can create a `config.json` file:

```json
{
  "db": "/path/to/Database V2",
  "library_root": "/path/to/Music Library", 
  "serato_root": "/path/to/_Serato_",
  "prefix": "Music",
  "exts": ".mp3,.m4a,.aac,.flac,.wav"
}
```

**Config File Locations:**
- **Portable**: `config.json` in the application directory (recommended)
- **Windows**: `%APPDATA%\seratosync\config.json`
- **macOS**: `~/Library/Application Support/seratosync/config.json`

## 📂 Typical Path Examples

### macOS
- **Database V2**: `~/Music/_Serato_/Database V2`
- **Serato Root**: `~/Music/_Serato_`  
- **Library Root**: `~/Music` or `~/Music/Music Tracks`

### Windows
- **Database V2**: `%USERPROFILE%\Music\_Serato_\Database V2`
- **Serato Root**: `%USERPROFILE%\Music\_Serato_`
- **Library Root**: `%USERPROFILE%\Music` or `%USERPROFILE%\Music\Music Tracks`



## 🎛️ Advanced Options

### Command Line Arguments
- `--config`: Path to configuration file
- `--db`: Path to Serato 'Database V2' file
- `--library-root`: Root folder to mirror as crates/subcrates  
- `--serato-root`: Path to _Serato_ folder where Subcrates live
- `--prefix`: Leading path segment (optional, auto-detected)
- `--exts`: Audio file extensions (default: mp3,m4a,aac,aif,aiff,wav,flac,ogg)
- `--dry-run`: Preview changes without making them
- `--update-db`: Add new tracks to Database V2
- `--show-config-example`: Show example configuration file

### GUI Options
- **Dry Run Mode**: Preview changes before applying
- **Update Database V2**: Add new tracks to your Serato database
- **Progress Tracking**: Real-time progress bars and detailed logging
- **Error Handling**: User-friendly error messages and recovery suggestions

## 🔧 How It Works

### Folder-to-Crate Mapping
SeratoSync automatically creates Serato crates that mirror your music library folder structure:

```
Music Library/
├── Hip Hop/
│   ├── 90s/          → Creates "Hip Hop%%90s.crate"
│   └── 2000s/        → Creates "Hip Hop%%2000s.crate"  
├── Electronic/
│   ├── House/        → Creates "Electronic%%House.crate"
│   └── Techno/       → Creates "Electronic%%Techno.crate"
└── Rock/             → Creates "Rock.crate"
```

### Database Integration
When "Update Database V2" is enabled:
- **Automatic Backup**: Creates timestamped backup before changes
- **New Track Detection**: Identifies tracks not in your Serato database
- **Safe Addition**: Adds tracks with minimal required fields  
- **Serato Compatibility**: New tracks appear normally in Serato for analysis

### Performance Optimization
- **Selective Updates**: Only modifies crates that actually changed
- **Path Normalization**: Handles different path formats across platforms
- **Efficient Scanning**: Fast library scanning and comparison algorithms
- **Smart Caching**: Avoids unnecessary file operations

## 🛡️ Safety & Reliability

### Built-in Safety Features
- **Non-destructive by default**: Never modifies Database V2 unless explicitly requested
- **Automatic backups**: Timestamped backups before any database changes
- **Version detection**: Ensures compatibility only with Serato Database V2
- **Error recovery**: Comprehensive error handling and user guidance
- **Dry run mode**: Preview all changes before applying them

### What Gets Protected
- **Your original Database V2**: Always backed up before modifications
- **Existing crates**: Only updated if content actually changed
- **Music files**: Never touched or modified
- **Serato settings**: All other Serato data remains untouched

## 🏗️ Architecture

### Core Components
- **GUI Layer**: Modern Kivy/KivyMD interface with real-time feedback
- **Sync Engine**: Efficient library scanning and crate generation
- **Database Handler**: Safe Serato Database V2 reading and writing
- **Path Manager**: Cross-platform path normalization and validation
- **Config System**: Automatic configuration management and persistence

### Supported Formats
**Audio Files**: MP3, M4A, AAC, FLAC, WAV, AIFF, AIF, OGG
**Platforms**: Windows 10/11, macOS 10.14+
**Serato Versions**: Serato DJ Pro/Lite with Database V2 format

## 🆕 Recent Improvements

- ✅ **Modern GUI**: Replaced command-line with intuitive graphical interface
- ✅ **Performance**: 10x faster crate updates with selective modification detection
- ✅ **Cross-platform**: Native applications for Windows and macOS
- ✅ **Path normalization**: Fixed issues with different path formats
- ✅ **Error handling**: User-friendly error messages and recovery suggestions
- ✅ **Auto-configuration**: Persistent settings and automatic path detection
