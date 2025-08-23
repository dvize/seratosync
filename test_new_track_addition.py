#!/usr/bin/env python3

"""
Test sync with detailed logging to see what happens to the 2 new tracks.
"""

import os
import configparser
import sys
sys.path.append('.')

from folder_scanner import scan_music_folder
from serato_parser_fixed import parse_serato_database
from crate_writer import _serato_pfil_to_local_path, _norm_for_compare, create_track_chunk_payload

def test_new_track_addition():
    """Test what happens when we try to add the 2 new tracks."""
    print("=== TESTING NEW TRACK ADDITION ===")
    
    config = configparser.ConfigParser()
    config.read('config.ini')
    music_folder = config.get('paths', 'music_folder')
    serato_db_path = config.get('paths', 'serato_database')
    
    # Find the 2 new tracks
    local_music_map = scan_music_folder(music_folder)
    local_tracks_paths = {file for files in local_music_map.values() for file in files}
    local_norm_map = {_norm_for_compare(p): p for p in local_tracks_paths}
    
    serato_tracks_map = {}
    if os.path.exists(serato_db_path):
        db_tree = parse_serato_database(serato_db_path)
        if db_tree and 'tracks' in db_tree:
            for track in db_tree['tracks']:
                pfil_value = track.get('pfil')
                if pfil_value and '__raw_chunk' in track:
                    local_path = _serato_pfil_to_local_path(pfil_value, music_folder)
                    norm_path = _norm_for_compare(local_path)
                    serato_tracks_map[norm_path] = track['__raw_chunk']
    
    serato_norm_paths = set(serato_tracks_map.keys())
    local_norm_paths = set(local_norm_map.keys())
    new_norm_paths = local_norm_paths - serato_norm_paths
    new_track_paths = {local_norm_map[p] for p in new_norm_paths}
    
    print(f"Found {len(new_track_paths)} new tracks to test:")
    for i, path in enumerate(new_track_paths):
        print(f"  {i+1}: {path}")
        
        # Test track chunk creation
        try:
            from crate_manager import normalize_path_for_crate
            normalized_path = normalize_path_for_crate(path, music_folder)
            print(f"     Normalized path: {normalized_path}")
            
            # Try to create track chunk
            otrk_payload = create_track_chunk_payload(path, normalized_path)
            print(f"     Created chunk payload: {len(otrk_payload)} bytes")
            
            # Verify file exists and is readable
            if os.path.exists(path):
                size = os.path.getsize(path)
                print(f"     File exists: {size:,} bytes")
            else:
                print(f"     ⚠️  File does not exist!")
                
        except Exception as e:
            print(f"     ❌ Error creating track chunk: {e}")

if __name__ == "__main__":
    test_new_track_addition()
