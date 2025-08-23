#!/usr/bin/env python3
"""
Test the folder scanner to see how many crates it wants to create
"""

import configparser
from folder_scanner import scan_music_folder

def test_folder_scanner():
    config = configparser.ConfigParser()
    config.read('config.ini')
    music_folder = config.get('paths', 'music_folder')
    max_crate_depth = config.getint('options', 'max_crate_depth', fallback=2)
    min_tracks_per_crate = config.getint('options', 'min_tracks_per_crate', fallback=5)
    
    print(f"Scanning music folder: {music_folder}")
    print(f"Max crate depth: {max_crate_depth}")
    print(f"Min tracks per crate: {min_tracks_per_crate}")
    
    music_map = scan_music_folder(music_folder, max_crate_depth, min_tracks_per_crate)
    
    print(f"\nFound {len(music_map)} folders (potential crates):")
    
    # Show first 20 crates
    for i, (crate_name, files) in enumerate(list(music_map.items())[:20]):
        print(f"  {i+1}. '{crate_name}' - {len(files)} tracks")
    
    if len(music_map) > 20:
        print(f"  ... and {len(music_map) - 20} more crates")
    
    print(f"\nTotal tracks across all crates: {sum(len(files) for files in music_map.values())}")

if __name__ == "__main__":
    test_folder_scanner()
