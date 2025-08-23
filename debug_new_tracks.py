#!/usr/bin/env python3

"""
Debug new track detection - see what tracks should be added to the database.
"""

import os
import configparser
import sys
sys.path.append('.')

from folder_scanner import scan_music_folder
from serato_parser_fixed import parse_serato_database
from crate_writer import _serato_pfil_to_local_path, _norm_for_compare

def debug_new_tracks():
    """Debug what new tracks should be detected."""
    print("=== NEW TRACK DETECTION DEBUG ===")
    
    config = configparser.ConfigParser()
    config.read('config.ini')
    music_folder = config.get('paths', 'music_folder')
    serato_db_path = config.get('paths', 'serato_database')
    
    print(f"Music folder: {music_folder}")
    print(f"Database path: {serato_db_path}")
    
    # Scan local music
    print("\n--- Scanning Local Music ---")
    local_music_map = scan_music_folder(music_folder)
    local_tracks_paths = {file for files in local_music_map.values() for file in files}
    local_norm_map = {_norm_for_compare(p): p for p in local_tracks_paths}
    
    print(f"Found {len(local_tracks_paths)} local tracks")
    print(f"First 5 local tracks:")
    for i, path in enumerate(list(local_tracks_paths)[:5]):
        print(f"  {i+1}: {path}")
    
    # Parse Serato database
    print(f"\n--- Parsing Serato Database ---")
    serato_tracks_map = {}
    if os.path.exists(serato_db_path):
        db_tree = parse_serato_database(serato_db_path)
        if db_tree and 'tracks' in db_tree:
            print(f"Database contains {len(db_tree['tracks'])} tracks")
            for track in db_tree['tracks']:
                pfil_value = track.get('pfil')
                if pfil_value and '__raw_chunk' in track:
                    local_path = _serato_pfil_to_local_path(pfil_value, music_folder)
                    norm_path = _norm_for_compare(local_path)
                    serato_tracks_map[norm_path] = track['__raw_chunk']
        
        print(f"Mapped {len(serato_tracks_map)} database tracks to local paths")
        print(f"First 5 database track paths:")
        for i, (norm_path, _) in enumerate(list(serato_tracks_map.items())[:5]):
            print(f"  {i+1}: {norm_path}")
    else:
        print("Database file does not exist!")
        return
    
    # Calculate new tracks
    print(f"\n--- New Track Detection ---")
    serato_norm_paths = set(serato_tracks_map.keys())
    local_norm_paths = set(local_norm_map.keys())
    
    intersection = serato_norm_paths.intersection(local_norm_paths)
    new_norm_paths = local_norm_paths - serato_norm_paths
    missing_norm_paths = serato_norm_paths - local_norm_paths
    
    print(f"Local tracks: {len(local_norm_paths)}")
    print(f"Database tracks: {len(serato_norm_paths)}")
    print(f"Matching tracks: {len(intersection)}")
    print(f"New tracks (local only): {len(new_norm_paths)}")
    print(f"Missing tracks (database only): {len(missing_norm_paths)}")
    
    if new_norm_paths:
        print(f"\nFirst 10 NEW TRACKS that should be added:")
        for i, norm_path in enumerate(list(new_norm_paths)[:10]):
            actual_path = local_norm_map[norm_path]
            print(f"  {i+1}: {actual_path}")
    else:
        print("\n⚠️  NO NEW TRACKS DETECTED - This is the problem!")
    
    if missing_norm_paths:
        print(f"\nFirst 5 MISSING TRACKS (in database but not on disk):")
        for i, norm_path in enumerate(list(missing_norm_paths)[:5]):
            print(f"  {i+1}: {norm_path}")
    
    # Path format comparison
    print(f"\n--- Path Format Analysis ---")
    if serato_norm_paths and local_norm_paths:
        print("Sample database path format:")
        sample_db_path = list(serato_norm_paths)[0]
        print(f"  {sample_db_path}")
        
        print("Sample local path format:")
        sample_local_path = list(local_norm_paths)[0]
        print(f"  {sample_local_path}")
        
        print("Path comparison details:")
        print(f"  DB path starts with: {sample_db_path[:50]}...")
        print(f"  Local path starts with: {sample_local_path[:50]}...")

if __name__ == "__main__":
    debug_new_tracks()
