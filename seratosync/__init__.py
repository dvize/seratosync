"""
Serato Crate Sync - A tool to mirror folder hierarchy into Serato crates.

This package provides functionality to:
- Parse Serato's Database V2 file format
- Scan music libraries for audio files
- Generate Serato crate files matching the directory structure
- Detect new tracks compared to the existing database
- (Optionally) update the Database V2 file with new tracks

Usage:
    python -m seratosync --db "/path/to/Database V2" --library-root "/path/to/Music" --serato-root "/path/to/_Serato_"
"""

__version__ = "1.0.0"
__author__ = "Serato Crate Sync"

from .cli import main

__all__ = ["main"]
