#!/usr/bin/env python3
"""
Debug script to understand why 149 new tracks don't result in crate writes.
"""

import sys
from pathlib import Path
sys.path.insert(0, '.')

from seratosync.database import read_database_v2_pfil_set, normalize_prefix
from seratosync.library import scan_library, build_crate_plans, detect_new_tracks, get_library_stats
from seratosync.crates import AUDIO_EXTS, build_crate_payload, read_crate_file
from seratosync.config import load_config

def debug_new_tracks_crates():
    """Debug why new tracks don't result in crate writes."""
    
    print("=== DEBUGGING NEW TRACKS AND CRATES ===")
    
    # Load config
    config = load_config()
    
    # Setup paths
    db_path = Path(config['db'])
    library_root = Path(config['library_root'])
    serato_root = Path(config['serato_root'])
    
    # Parse database
    pfil_set_raw, inferred, total = read_database_v2_pfil_set(db_path)
    prefix = normalize_prefix(None, inferred, library_root)
    
    # TEMPORARY FIX: Force correct prefix for Music Tracks library
    if library_root.name == "Music Tracks" and prefix.endswith("Music"):
        lib_parts = library_root.parts
        if lib_parts[0] == '/':
            lib_parts = lib_parts[1:]
        forced_prefix = '/'.join(lib_parts)
        prefix = forced_prefix
    
    # Normalize database paths
    pfil_set_normalized = set()
    library_root_str = str(library_root).replace("\\", "/")
    library_root_normalized = library_root_str.lstrip("/")
    
    for p_raw in pfil_set_raw:
        p_norm = p_raw.replace("\\", "/")
        if library_root_normalized in p_norm:
            if f"{prefix}/" in p_norm:
                p_norm = f"{prefix}/" + p_norm.split(f"{prefix}/", 1)[1]
            pfil_set_normalized.add(p_norm)
    
    print(f"Database tracks filtered: {len(pfil_set_normalized)}")
    
    # Scan library
    allowed_exts = {'.mp3', '.m4a', '.aac', '.flac', '.wav', '.aiff', '.aif', '.ogg'}
    lib_map = scan_library(library_root, allowed_exts)
    
    # Build crate plans
    crate_plans = build_crate_plans(lib_map, prefix, serato_root)
    
    # Get all track paths from crate plans
    all_track_paths = []
    for _, ptrks in crate_plans:
        all_track_paths.extend(ptrks)
    
    # Detect new tracks
    new_tracks = detect_new_tracks(all_track_paths, pfil_set_normalized)
    print(f"New tracks detected: {len(new_tracks)}")
    
    if new_tracks:
        print("\nFirst 10 new tracks:")
        for i, track in enumerate(sorted(new_tracks)[:10]):
            print(f"  {i+1}: {track}")
        
        # Group new tracks by directory to see which crates they belong to
        from collections import defaultdict
        new_tracks_by_dir = defaultdict(list)
        
        for track in new_tracks:
            # Extract directory path from track path
            if '/' in track:
                dir_part = '/'.join(track.split('/')[:-1])  # Remove filename
                # Remove prefix to get relative dir
                if dir_part.startswith(f"{prefix}/"):
                    rel_dir = dir_part[len(f"{prefix}/"):]
                    new_tracks_by_dir[rel_dir].append(track)
                else:
                    new_tracks_by_dir['<root>'].append(track)
            else:
                new_tracks_by_dir['<root>'].append(track)
        
        print(f"\nNew tracks grouped by directory ({len(new_tracks_by_dir)} directories):")
        for dir_path, tracks in sorted(new_tracks_by_dir.items())[:10]:
            print(f"  {dir_path}: {len(tracks)} tracks")
        
        # Now check which crates these new tracks would affect
        affected_crates = []
        
        for crate_file, ptrks in crate_plans:
            # Check if this crate contains any new tracks
            has_new_track = any(track in new_tracks for track in ptrks)
            if has_new_track:
                new_count = sum(1 for track in ptrks if track in new_tracks)
                
                # Check if crate exists and what would change
                existing_count = 0
                would_change = True
                
                if crate_file.exists():
                    existing_tracks = read_crate_file(crate_file)
                    existing_count = len(existing_tracks)
                    
                    # Check if content would actually change
                    new_bytes = build_crate_payload(ptrks)
                    with open(crate_file, "rb") as f:
                        old_bytes = f.read()
                    would_change = old_bytes != new_bytes
                
                affected_crates.append({
                    'file': crate_file,
                    'new_tracks': new_count,
                    'total_tracks': len(ptrks),
                    'existing_count': existing_count,
                    'would_change': would_change
                })
        
        print(f"\nCrates that would be affected: {len(affected_crates)}")
        print("Details of first 10 affected crates:")
        for i, crate_info in enumerate(affected_crates[:10]):
            status = "CREATE" if crate_info['existing_count'] == 0 else "UPDATE" if crate_info['would_change'] else "NO CHANGE"
            print(f"  {i+1}: {crate_info['file'].name}")
            print(f"      {crate_info['new_tracks']} new tracks, {crate_info['total_tracks']} total")
            print(f"      Existing: {crate_info['existing_count']} tracks")
            print(f"      Action: {status}")
    
    else:
        print("No new tracks found - this explains why no crates would be written.")


if __name__ == "__main__":
    debug_new_tracks_crates()
