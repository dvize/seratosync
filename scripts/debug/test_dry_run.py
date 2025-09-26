#!/usr/bin/env python3
"""
Test script to create some temporary files and test the dry run reporting.
"""

import os
import tempfile
from pathlib import Path

# Create a temporary test file in the music library
test_dir = Path("/Users/dvize/Music/Music Tracks/Test_Dry_Run_Demo")
test_dir.mkdir(exist_ok=True)

# Create a test mp3 file
test_file = test_dir / "test_dry_run_track.mp3"
test_file.write_text("fake mp3 content")

print(f"Created test file: {test_file}")
print("Now run the dry run to see it detect the new file and show crate creation.")
print("Run: python -m seratosync.cli --config config.json --dry-run")
print()
print("To clean up afterwards, run:")
print(f"rm -rf '{test_dir}'")
