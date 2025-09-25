# Serato Crate Sync

A Python tool to mirror folder hierar#### Creating a Config File

1. Run the tool with `--show-config-example` to see the format:
   ```bash
   python -m seratosync --show-config-example
   ```

2. Create the config file in the appropriate location for your platform

3. Edit the JSON file with your paths:
   ```json
   {
     "db": "/path/to/Database V2",
     "library_root": "/path/to/Music Library",
     "serato_root": "/path/to/_Serato_",
     "exts": ".mp3,.m4a,.aac,.flac,.wav"
   }
   ```

   The `prefix` field is optional - if omitted, it will be automatically inferred from your database or library structure.

#### Config File Locations (in priority order)

The tool checks for `config.json` in this order:

1. **Current working directory** (`./config.json`) - **Most portable, recommended**
2. Platform-specific user directory:
   - Windows: `%APPDATA%\seratosync\config.json`
   - macOS: `~/Library/Application Support/seratosync/config.json`
   - Linux: `~/.config/seratosync/config.json`tes and detect new tracks compared to Serato's "database V2" file.

## Features

- **Safe by default**: Only writes crate files, never modifies Database V2 unless explicitly requested
- **Dry run mode**: See what would change without making any modifications
- **Prefix inference**: Automatically detects the correct path prefix from existing database entries
- **Extensible audio formats**: Configurable audio file extensions
- **Experimental database update**: Optional support for appending new tracks to Database V2

## Installation

### CLI Installation
```bash
pip install -e .
```

### GUI Installation
For the modern graphical interface:
```bash
pip install -e .[gui]
python seratosync_gui.py
```

**GUI Features:**
- 🎯 Modern dark theme with intuitive interface
- 📁 Visual file/directory selection dialogs
- 🔄 Real-time progress tracking and logging
- ⚡ One-click sync and update operations
- 💾 Automatic configuration management
- 🖥️ Cross-platform support (Windows, macOS, Linux)

See `GUI_INSTALLATION.md` for detailed GUI setup and usage instructions.

## Usage

### Basic Usage

```bash
# Using command line arguments
python -m seratosync \
    --db "/path/to/Database V2" \
    --library-root "/path/to/Music Library" \
    --serato-root "/path/to/_Serato_"

# Using config file (recommended for repeated use)
python -m seratosync
```

### With Options

```bash
python -m seratosync \
    --db "/path/to/Database V2" \
    --library-root "/path/to/Music Library" \
    --serato-root "/path/to/_Serato_" \
    --prefix "Music" \
    --exts "mp3,flac,wav,aiff" \
    --dry-run
```

### Configuration File

You can create a configuration file to avoid specifying common paths every time. The tool automatically looks for a config file in platform-specific locations:

- **Windows**: `%APPDATA%\seratosync\config.json`
- **macOS**: `~/Library/Application Support/seratosync/config.json`
- **Linux**: `~/.config/seratosync/config.json`

#### Creating a Config File

**Option 1: Interactive Setup (Recommended)**
```bash
python create_config.py
```

**Option 2: Manual Creation**

1. Run the tool with `--show-config-example` to see the format:
   ```bash
   python -m seratosync --show-config-example
   ```

2. Create the config file in the appropriate location for your platform

3. Edit the JSON file with your paths:
   ```json
   {
     "db": "/path/to/Database V2",
     "library_root": "/path/to/Music Library",
     "serato_root": "/path/to/_Serato_",
     "prefix": "Music",
     "exts": ".mp3,.m4a,.aac,.flac,.wav"
   }
   ```

#### Using Config Files

Once you have a config file, you can run the tool with fewer arguments:

```bash
# Use default config file
python -m seratosync

# Use custom config file location
python -m seratosync --config /path/to/my/config.json

# Override config values with command line arguments
python -m seratosync --library-root "/different/path"
```

**Note**: A default config file has been created for this project at the root level (`config.json`) pointing to the local `database V2` file and current directory. You can modify it or create your own config file for your actual music library.

Command line arguments always take precedence over config file values.

## Path Examples

### macOS
- Database V2: `~/Music/_Serato_/Database V2`
- Serato root: `~/Music/_Serato_`
- Library root: `~/Music`

### Windows
- Database V2: `%USERPROFILE%\Music\\_Serato_\\Database V2`
- Serato root: `%USERPROFILE%\Music\\_Serato_`
- Library root: `%USERPROFILE%\Music`

## Arguments

- `--config`: Path to configuration file (optional, uses platform default if not specified)
- `--db`: Path to Serato 'Database V2' file (required unless in config file)
- `--library-root`: Root folder to mirror as crates/subcrates (required unless in config file)
- `--serato-root`: Path to _Serato_ folder where Subcrates live (required unless in config file)
- `--prefix`: Leading path segment to prepend in crate 'ptrk' (optional, inferred automatically)
- `--exts`: Comma-separated list of audio extensions (default: mp3,m4a,aac,aif,aiff,wav,flac,ogg)
- `--dry-run`: Scan and show what would change; do not write crate files
- `--update-db`: (Experimental) Also append new tracks to Database V2
- `--show-config-example`: Show example configuration file and exit

## Module Structure

The code is organized into logical modules:

- `tlv_utils`: Low-level TLV (tag/length/value) parsing utilities
- `database`: Database V2 file parsing and prefix inference
- `crates`: Crate file writing and path management
- `library`: Library scanning and file discovery
- `cli`: Command-line interface and main orchestration

## Safety

- **Database V2 is never modified** unless you pass `--update-db`
- When `--update-db` is used, a timestamped backup is created first
- Crate files are only rewritten if their content has changed
- The tool is designed to be safe and non-destructive

## Database Update Feature

The `--update-db` feature safely adds new tracks to Serato's Database V2:

### How it works
- **Automatic backup**: Creates a timestamped backup before any changes
- **Safe integration**: Uses the exact Database V2 format that Serato expects
- **Minimal records**: Creates tracks with essential fields only (path, type, date added)
- **Serato compatibility**: New tracks appear in Serato and can be analyzed normally
- **Selective updates**: Only updates crates that contain newly added or modified tracks

### Usage
```bash
# Add new tracks to database and update relevant crates
python -m seratosync --update-db

# Dry run to see what would be added
python -m seratosync --update-db --dry-run
```

### What gets added
New track records include:
- File path and type
- Date added timestamp  
- Default metadata (BPM, key, etc.) that Serato will update when analyzing
- All required binary fields for database integrity

### Performance
The tool is optimized for efficiency:
- Only crates containing new/changed tracks are updated
- Existing crates with no changes are left untouched
- Database operations are batched for speed

## Recent Fixes & Improvements

- ✅ **Fixed database corruption**: Resolved WindowsPath encoding issues and version string mismatch
- ✅ **Selective crate updates**: Only updates crates with actual changes, dramatically improving performance  
- ✅ **Database compatibility**: Ensures 100% compatibility with Serato's expected format
- ✅ **Error handling**: Improved error reporting and recovery
