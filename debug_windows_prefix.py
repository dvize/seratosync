#!/usr/bin/env python3
"""
Debug script to analyze prefix detection issues on Windows.
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, '.')

from seratosync.database import read_database_v2_pfil_set, normalize_prefix
from seratosync.config import load_config

def debug_windows_prefix():
    """Debug the prefix detection and normalization for Windows paths."""
    
    print("=== DEBUGGING WINDOWS PREFIX DETECTION ===\n")
    
    # Load config
    config = load_config()
    
    # Setup paths
    db_path = Path(config['db'])
    library_root = Path(config['library_root'])
    
    print(f"Database path: {db_path}")
    print(f"Library root: {library_root}")
    print(f"Library root parts: {library_root.parts}")
    
    if not db_path.exists():
        print(f"ERROR: Database file doesn't exist: {db_path}")
        return
    
    # Parse database
    print(f"\nReading database...")
    pfil_set_raw, inferred, total = read_database_v2_pfil_set(db_path)
    print(f"Total tracks in database: {total}")
    print(f"Inferred prefix from database: '{inferred}'")
    
    # Show some sample paths from database
    print(f"\nFirst 10 paths from database:")
    for i, path in enumerate(sorted(pfil_set_raw)[:10]):
        print(f"  {i+1}: {path}")
    
    # Test normalize_prefix function
    print(f"\n=== PREFIX NORMALIZATION ===")
    final_prefix = normalize_prefix(None, inferred, library_root)
    print(f"Final normalized prefix: '{final_prefix}'")
    
    # Convert library_root to expected format for comparison
    lib_path_parts = library_root.parts
    if lib_path_parts[0] in ['/', 'C:\\', 'E:\\']:  # Remove drive letter or root slash
        lib_path_parts = lib_path_parts[1:]
    expected_prefix = '/'.join(lib_path_parts)
    print(f"Expected prefix based on library_root: '{expected_prefix}'")
    
    # Check if they match
    if final_prefix == expected_prefix:
        print("✅ Prefixes match!")
    else:
        print("❌ PREFIX MISMATCH!")
        print(f"   Final:    '{final_prefix}'")
        print(f"   Expected: '{expected_prefix}'")
    
    # Test path normalization with the current prefix
    print(f"\n=== PATH MATCHING TEST ===")
    print("Testing if database paths match the current prefix logic...")
    
    # Normalize database paths using current logic (from CLI)
    pfil_set_normalized = set()
    library_root_str = str(library_root).replace("\\", "/")
    library_root_normalized = library_root_str.lstrip("/")
    
    matching_paths = 0
    for p_raw in pfil_set_raw:
        p_norm = p_raw.replace("\\", "/")
        if library_root_normalized in p_norm:
            if f"{final_prefix}/" in p_norm:
                p_norm = f"{final_prefix}/" + p_norm.split(f"{final_prefix}/", 1)[1]
            pfil_set_normalized.add(p_norm)
            matching_paths += 1
    
    print(f"Paths that match the prefix logic: {matching_paths}/{total}")
    print(f"Normalized paths: {len(pfil_set_normalized)}")
    
    if matching_paths < total * 0.9:  # Less than 90% match
        print("⚠️  PROBLEM: Most database paths don't match the prefix logic!")
        print("This will cause all tracks to be detected as 'new'")
        
        # Show some examples of mismatched paths
        print("\nExamples of database paths that don't match:")
        mismatch_count = 0
        for p_raw in sorted(pfil_set_raw)[:20]:
            p_norm = p_raw.replace("\\", "/")
            matches_logic = (library_root_normalized in p_norm and f"{final_prefix}/" in p_norm)
            if not matches_logic and mismatch_count < 5:
                print(f"  Database path: {p_raw}")
                print(f"  Looking for:   '{library_root_normalized}' and '{final_prefix}/'")
                mismatch_count += 1
    else:
        print("✅ Most paths match the prefix logic")

if __name__ == "__main__":
    debug_windows_prefix()
