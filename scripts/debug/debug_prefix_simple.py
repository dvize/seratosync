#!/usr/bin/env python3
"""
Simple debug script to analyze prefix detection issues.
No GUI imports to avoid Kivy conflicts.
"""

import sys
import os
from pathlib import Path
import json

# Add seratosync module to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_prefix_issue():
    """Debug the prefix detection issue."""
    print("=== Serato Sync Prefix Debug (No GUI) ===\n")
    
    # Load config manually
    config_file = Path.home() / "Library/Application Support/SeratoSync/config.json"
    if not config_file.exists():
        config_file = Path("config.json")
    
    if not config_file.exists():
        print("ERROR: No config file found!")
        return
        
    with open(config_file) as f:
        config = json.load(f)
    
    print(f"Config loaded from: {config_file}")
    
    db_path = Path(config['serato_db_path']) / "database V2"
    library_root = Path(config['music_library_path'])
    
    print(f"Database path: {db_path}")
    print(f"Library root: {library_root}")
    
    # Import here to avoid early imports
    from seratosync.database import read_database_v2_pfil_set, normalize_prefix
    from seratosync.library import scan_library, detect_new_tracks
    
    # Read database
    pfil_set, inferred_prefix, total_tracks = read_database_v2_pfil_set(db_path, sample_for_prefix=100)
    final_prefix = normalize_prefix(None, inferred_prefix, library_root)
    
    print(f"\nDatabase analysis:")
    print(f"  Total tracks: {total_tracks:,}")
    print(f"  Inferred prefix: '{inferred_prefix}'")
    print(f"  Final prefix: '{final_prefix}'")
    
    # Show sample database paths
    print(f"\nFirst 10 database paths:")
    for i, path in enumerate(list(pfil_set)[:10], 1):
        print(f"  {i:2}. {path}")
    
    # Scan library
    library_structure = scan_library(library_root)
    total_files = sum(len(files) for files in library_structure.values())
    print(f"\nLibrary analysis:")
    print(f"  Folders: {len(library_structure):,}")
    print(f"  Files: {total_files:,}")
    
    # Show how library paths are constructed
    print(f"\nFirst 10 constructed library paths:")
    count = 0
    constructed_paths = []
    for folder, files in library_structure.items():
        if count >= 10:
            break
        for file in files[:1]:  # One file per folder
            full_path = folder / file
            rel_path = full_path.relative_to(library_root)
            constructed_path = f"{final_prefix}/{rel_path}"
            constructed_paths.append(constructed_path)
            print(f"  {count+1:2}. {constructed_path}")
            count += 1
            if count >= 10:
                break
    
    # Check for direct matches
    print(f"\nPath matching analysis:")
    matches = set(constructed_paths) & pfil_set
    print(f"  Direct matches: {len(matches)}")
    
    if len(matches) > 0:
        print("  Example matches:")
        for match in list(matches)[:3]:
            print(f"    - {match}")
    else:
        print("  NO DIRECT MATCHES FOUND!")
        print("\n  This explains why all tracks are detected as 'new'")
        
        # Let's analyze why there are no matches
        print(f"\n  Database path format analysis:")
        db_sample = list(pfil_set)[:5]
        for path in db_sample:
            print(f"    DB: {repr(path)}")
        
        print(f"\n  Constructed path format analysis:")
        for path in constructed_paths[:5]:
            print(f"    LIB: {repr(path)}")
            
        # Check different prefix combinations
        print(f"\n  Testing alternative prefixes:")
        test_prefixes = ["Music", "Users/dvize/Music", "dvize/Music", "Music Tracks"]
        
        for test_prefix in test_prefixes:
            test_constructed = []
            for folder, files in list(library_structure.items())[:5]:
                for file in files[:1]:
                    full_path = folder / file
                    rel_path = full_path.relative_to(library_root)
                    test_path = f"{test_prefix}/{rel_path}"
                    test_constructed.append(test_path)
            
            test_matches = set(test_constructed) & pfil_set
            print(f"    '{test_prefix}': {len(test_matches)} matches")

if __name__ == "__main__":
    debug_prefix_issue()
