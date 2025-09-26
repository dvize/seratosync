#!/usr/bin/env python3
"""
Debug script to understand why tracks aren't matching between database and library scan.
"""

import sys
from pathlib import Path
sys.path.insert(0, '.')

from seratosync.database import read_database_v2_pfil_set, normalize_prefix
from seratosync.library import scan_library, build_crate_plans, detect_new_tracks, get_library_stats
from seratosync.crates import AUDIO_EXTS
from seratosync.config import load_config

def debug_path_matching():
    """Debug why paths don't match between database and library."""
    
    print("=== DEBUGGING PATH MATCHING ===")
    
    # Load config
    config = load_config()
    
    # Setup paths
    db_path = Path(config['db'])
    library_root = Path(config['library_root'])
    serato_root = Path(config['serato_root'])
    
    print(f"DB Path: {db_path}")
    print(f"Library Root: {library_root}")
    print(f"Serato Root: {serato_root}")
    print()
    
    # Parse database
    pfil_set_raw, inferred, total = read_database_v2_pfil_set(db_path)
    prefix = normalize_prefix(None, inferred, library_root)
    
    print(f"Raw database tracks: {len(pfil_set_raw)}")
    print(f"Inferred prefix: '{inferred}'")
    print(f"Normalized prefix: '{prefix}'")
    print()
    
    # Show sample raw paths from database
    print("Sample raw database paths:")
    for i, path in enumerate(sorted(pfil_set_raw)[:10]):
        print(f"  {i+1}: '{path}'")
    print()
    
    # TEMPORARY FIX: Force correct prefix for Music Tracks library
    if library_root.name == "Music Tracks" and prefix.endswith("Music"):
        lib_parts = library_root.parts
        if lib_parts[0] == '/':
            lib_parts = lib_parts[1:]
        forced_prefix = '/'.join(lib_parts)
        print(f"Forcing prefix from '{prefix}' to '{forced_prefix}'")
        prefix = forced_prefix
    
    # Normalize database paths
    pfil_set_normalized = set()
    library_root_str = str(library_root).replace("\\", "/")
    library_root_normalized = library_root_str.lstrip("/")
    
    print(f"Library root normalized: '{library_root_normalized}'")
    
    for p_raw in pfil_set_raw:
        p_norm = p_raw.replace("\\", "/")
        
        # Only process tracks within library root
        if library_root_normalized in p_norm:
            if f"{prefix}/" in p_norm:
                p_norm = f"{prefix}/" + p_norm.split(f"{prefix}/", 1)[1]
            pfil_set_normalized.add(p_norm)
    
    print(f"Normalized database tracks: {len(pfil_set_normalized)}")
    print()
    
    # Show sample normalized paths
    print("Sample normalized database paths:")
    for i, path in enumerate(sorted(pfil_set_normalized)[:10]):
        print(f"  {i+1}: '{path}'")
    print()
    
    # Scan library
    allowed_exts = {'.mp3', '.m4a', '.aac', '.flac', '.wav', '.aiff', '.aif', '.ogg'}
    lib_map = scan_library(library_root, allowed_exts)
    num_dirs, num_files = get_library_stats(lib_map)
    
    print(f"Library scan: {num_dirs} folders, {num_files} files")
    
    # Build crate plans
    crate_plans = build_crate_plans(lib_map, prefix, serato_root)
    
    # Get all track paths from crate plans
    all_track_paths = []
    for _, ptrks in crate_plans:
        all_track_paths.extend(ptrks)
    
    print(f"Generated track paths: {len(all_track_paths)}")
    print()
    
    # Show sample generated paths
    print("Sample generated track paths:")
    for i, path in enumerate(sorted(all_track_paths)[:10]):
        print(f"  {i+1}: '{path}'")
    print()
    
    # Find matches and mismatches
    matches = set(all_track_paths) & pfil_set_normalized
    new_tracks = [p for p in all_track_paths if p not in pfil_set_normalized]
    
    print(f"Matches: {len(matches)}")
    print(f"New tracks: {len(new_tracks)}")
    print()
    
    if matches:
        print("Sample matching paths:")
        for i, path in enumerate(sorted(matches)[:5]):
            print(f"  {i+1}: '{path}'")
        print()
    
    if new_tracks:
        print("Sample 'new' tracks (first 10):")
        for i, path in enumerate(sorted(new_tracks)[:10]):
            print(f"  {i+1}: '{path}'")
        print()
        
        # Try to find similar paths in database
        print("Looking for similar paths in database:")
        for new_path in sorted(new_tracks)[:5]:
            print(f"\nNew: '{new_path}'")
            # Find paths that contain the filename
            filename = new_path.split('/')[-1]
            similar = [p for p in pfil_set_normalized if filename in p]
            if similar:
                print(f"  Similar in DB: {similar[:3]}")
            else:
                print(f"  No similar paths found for filename: '{filename}'")


if __name__ == "__main__":
    debug_path_matching()
