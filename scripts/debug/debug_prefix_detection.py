#!/usr/bin/env python3
"""
Debug script to analyze prefix detection issues on macOS.
This will help identify why new track detection is broken.
"""

import sys
import os
from pathlib import Path
import json

# Add seratosync module to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from seratosync.database import read_database_v2_pfil_set, normalize_prefix, read_database_v2_records
from seratosync.library import scan_library, detect_new_tracks
from seratosync.config import load_config, get_config_file_path

def analyze_prefix_detection():
    """Analyze prefix detection for debugging."""
    print("=== Serato Sync Prefix Detection Debug ===\n")
    
    # Load config
    try:
        config_path = get_config_file_path()
        config = load_config(config_path)
        print(f"Config loaded from: {config_path}")
        print(f"Config: {json.dumps(config, indent=2)}")
    except Exception as e:
        print(f"Error loading config: {e}")
        return
    
    db_path = Path(config['serato_db_path']) / "database V2"
    library_root = Path(config['music_library_path'])
    
    print(f"\nDatabase path: {db_path}")
    print(f"Library root: {library_root}")
    print(f"Database exists: {db_path.exists()}")
    print(f"Library exists: {library_root.exists()}")
    
    if not db_path.exists():
        print("ERROR: Database file not found!")
        return
    
    print("\n=== Database Analysis ===")
    
    # Read database and get prefix info
    pfil_set, inferred_prefix, total_tracks = read_database_v2_pfil_set(db_path, sample_for_prefix=100)
    
    print(f"Total tracks in database: {total_tracks:,}")
    print(f"Inferred prefix from DB: '{inferred_prefix}'")
    
    # Normalize prefix
    final_prefix = normalize_prefix(None, inferred_prefix, library_root)
    print(f"Final normalized prefix: '{final_prefix}'")
    
    print(f"\nSample of database paths (first 10):")
    sample_paths = list(pfil_set)[:10]
    for i, path in enumerate(sample_paths, 1):
        print(f"  {i:2}. {path}")
    
    print(f"\n=== Library Analysis ===")
    
    # Scan library
    try:
        library_structure = scan_library(library_root)
        total_files = sum(len(files) for files in library_structure.values())
        print(f"Library folders: {len(library_structure):,}")
        print(f"Library audio files: {total_files:,}")
        
        print(f"\nSample library paths (first 10):")
        count = 0
        for folder, files in library_structure.items():
            if count >= 10:
                break
            rel_path = folder.relative_to(library_root)
            print(f"  {count+1:2}. {rel_path}")
            count += 1
            
    except Exception as e:
        print(f"Error scanning library: {e}")
        return
    
    print(f"\n=== New Track Detection Analysis ===")
    
    # Test new track detection
    try:
        new_tracks = detect_new_tracks(library_structure, pfil_set, final_prefix)
        print(f"New tracks detected: {len(new_tracks):,}")
        
        if len(new_tracks) > 0:
            print(f"\nSample of new tracks (first 10):")
            for i, track in enumerate(list(new_tracks)[:10], 1):
                print(f"  {i:2}. {track}")
        
        print(f"\n=== Path Comparison Analysis ===")
        print("Checking how paths are constructed vs database paths...")
        
        # Show how library paths would be constructed with current prefix
        sample_lib_files = []
        count = 0
        for folder, files in library_structure.items():
            if count >= 5:
                break
            for file in files[:2]:  # Take first 2 files from each folder
                full_path = folder / file
                rel_path = full_path.relative_to(library_root)
                constructed_path = f"{final_prefix}/{rel_path}".replace("//", "/")
                sample_lib_files.append(constructed_path)
                count += 1
                if count >= 10:
                    break
        
        print(f"\nSample constructed library paths:")
        for i, path in enumerate(sample_lib_files, 1):
            print(f"  {i:2}. {path}")
            
        print(f"\nSample database paths (for comparison):")
        for i, path in enumerate(list(pfil_set)[:10], 1):
            print(f"  {i:2}. {path}")
            
        # Check for matches
        matches = set(sample_lib_files) & pfil_set
        print(f"\nDirect matches found: {len(matches)}")
        for match in list(matches)[:5]:
            print(f"  - {match}")
            
    except Exception as e:
        print(f"Error in new track detection: {e}")
        import traceback
        traceback.print_exc()
        
    print(f"\n=== Path Format Analysis ===")
    
    # Analyze path format differences
    db_paths = list(pfil_set)[:20]
    print("Database path analysis:")
    
    unix_style = sum(1 for p in db_paths if '/' in p and '\\' not in p)
    windows_style = sum(1 for p in db_paths if '\\' in p)
    mixed_style = sum(1 for p in db_paths if '/' in p and '\\' in p)
    
    print(f"  Unix-style paths (/): {unix_style}")
    print(f"  Windows-style paths (\\): {windows_style}")
    print(f"  Mixed paths: {mixed_style}")
    
    print(f"\nPrefix patterns in database:")
    prefixes = {}
    for path in db_paths:
        if '/' in path:
            parts = path.split('/')
            if len(parts) > 0 and parts[0]:
                prefix = parts[0]
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
    
    for prefix, count in sorted(prefixes.items(), key=lambda x: x[1], reverse=True):
        print(f"  '{prefix}': {count} times")

if __name__ == "__main__":
    analyze_prefix_detection()
