#!/usr/bin/env python3
"""Debug script to analyze why we're losing data during sync"""

import configparser
from serato_parser_fixed import parse_serato_database
from folder_scanner import scan_music_folder
import os

def _norm_for_compare(path_str):
    """Same normalization function used in crate_writer.py"""
    p = os.path.normpath(path_str)
    # Normalize Unicode to NFC form
    try:
        import unicodedata
        p = unicodedata.normalize('NFC', p)
    except:
        pass
    return os.path.normcase(p)

def _serato_pfil_to_local_path(pfil_value, music_folder):
    """Same path conversion function used in crate_writer.py"""
    s = pfil_value.replace('\x00', '').strip()
    
    # Handle file:// URLs
    if s.lower().startswith('file://'):
        try:
            from urllib.parse import urlparse, unquote
            path = unquote(urlparse(s).path)
            if os.name == 'nt' and path.startswith('/') and len(path) > 3 and path[2] == ':':
                path = path[1:]
            return path
        except Exception:
            pass
    
    # Handle absolute paths
    if s.startswith('/') or (os.name == 'nt' and len(s) > 1 and s[1] == ':'):
        return s
    
    # Handle relative paths
    if music_folder and not os.path.isabs(s):
        music_tracks_prefix = "Music/Music Tracks/"
        if s.startswith(music_tracks_prefix):
            relative_part = s[len(music_tracks_prefix):]
            candidate_path = os.path.join(music_folder, relative_part)
            return candidate_path
        
        music_tracks_prefix2 = "Music Tracks/"  
        if s.startswith(music_tracks_prefix2):
            relative_part = s[len(music_tracks_prefix2):]
            candidate_path = os.path.join(music_folder, relative_part)
            return candidate_path
            
        candidate_path = os.path.join(music_folder, s)
        return candidate_path
    
    return s

def main():
    config = configparser.ConfigParser()
    config.read('config.ini')
    music_folder = config.get('paths', 'music_folder')
    serato_db_path = config.get('paths', 'serato_database')

    print("=== SERATOSYNC DEBUG ANALYSIS ===")
    print(f"Music folder: {music_folder}")
    print(f"Database path: {serato_db_path}")
    
    # Get file system info
    print("\n--- Scanning file system ---")
    local_music_map = scan_music_folder(music_folder)
    local_tracks_paths = {file for files in local_music_map.values() for file in files}
    local_norm_map = {_norm_for_compare(p): p for p in local_tracks_paths}
    print(f"Local tracks found: {len(local_tracks_paths)}")
    
    # Get database info
    print("\n--- Parsing database ---")
    db_tree = parse_serato_database(serato_db_path)
    database_tracks = db_tree['tracks'] if db_tree and 'tracks' in db_tree else []
    print(f"Database tracks parsed: {len(database_tracks)}")
    
    # Analyze path matching
    serato_tracks_map = {}
    serato_raw_paths = []
    local_converted_paths = []
    
    for track in database_tracks:
        pfil_value = track.get('pfil')
        if pfil_value and '__raw_chunk' in track:
            serato_raw_paths.append(pfil_value)
            local_path = _serato_pfil_to_local_path(pfil_value, music_folder)
            local_converted_paths.append(local_path)
            norm_path = _norm_for_compare(local_path)
            serato_tracks_map[norm_path] = track['__raw_chunk']
    
    serato_norm_paths = set(serato_tracks_map.keys())
    local_norm_paths = set(local_norm_map.keys())
    intersection = serato_norm_paths.intersection(local_norm_paths)
    
    print(f"\n--- Path Matching Analysis ---")
    print(f"Database tracks with paths: {len(serato_raw_paths)}")
    print(f"Serato normalized paths: {len(serato_norm_paths)}")
    print(f"Local normalized paths: {len(local_norm_paths)}")
    print(f"Intersection (matches): {len(intersection)}")
    print(f"Serato-only paths: {len(serato_norm_paths - local_norm_paths)}")
    print(f"Local-only paths: {len(local_norm_paths - serato_norm_paths)}")
    
    # Show sample raw database paths
    print(f"\n--- Sample Database Raw Paths (first 10) ---")
    for i, raw_path in enumerate(serato_raw_paths[:10]):
        converted = local_converted_paths[i]
        norm_path = _norm_for_compare(converted)
        exists_local = norm_path in local_norm_paths
        print(f"{i+1:2d}. Raw: '{raw_path}'")
        print(f"     Conv: '{converted}'")
        print(f"     Norm: '{norm_path}'")
        print(f"     Match: {'✓' if exists_local else '✗'}")
        print()
    
    # Show sample unmatched database paths
    unmatched_serato = list(serato_norm_paths - local_norm_paths)[:5]
    print(f"\n--- Sample Unmatched Database Paths ---")
    for i, path in enumerate(unmatched_serato):
        print(f"{i+1}. '{path}'")
    
    # Show sample unmatched local paths
    unmatched_local = list(local_norm_paths - serato_norm_paths)[:5]
    print(f"\n--- Sample Unmatched Local Paths ---")
    for i, path in enumerate(unmatched_local):
        print(f"{i+1}. '{path}'")
    
    # Calculate what would be preserved vs lost
    exclude_missing = config.getboolean('options', 'exclude_missing_files', fallback=True)
    if exclude_missing:
        preserved_count = len(intersection)
        lost_count = len(serato_norm_paths) - preserved_count
    else:
        preserved_count = len(serato_norm_paths)
        lost_count = 0
        
    print(f"\n--- Final Analysis ---")
    print(f"exclude_missing_files = {exclude_missing}")
    print(f"Tracks that will be preserved: {preserved_count}")
    print(f"Tracks that will be lost: {lost_count}")
    print(f"Data preservation rate: {(preserved_count/len(serato_norm_paths)*100):.1f}%")
    
    if lost_count > 0:
        print(f"\nWARNING: {lost_count} tracks will be lost due to path mismatches!")

if __name__ == "__main__":
    main()
