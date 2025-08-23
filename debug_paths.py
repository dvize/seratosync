#!/usr/bin/env python3
"""
Debug script to understand path comparison issues
"""

import os
import configparser
from urllib.parse import urlparse, unquote
import unicodedata

from serato_parser_fixed import parse_serato_database
from folder_scanner import scan_music_folder

def _to_nfc(s: str) -> str:
    """Normalize Unicode string to NFC form for consistency."""
    try:
        return unicodedata.normalize('NFC', s)
    except Exception:
        return s

def _norm_for_compare(path_str: str) -> str:
    """Normalize a path string for reliable comparison."""
    p = os.path.normpath(path_str)
    p = _to_nfc(p)
    return os.path.normcase(p)

def _serato_pfil_to_local_path(pfil_value: str, music_folder: str) -> str:
    """Converts a Serato pfil path string to a local file system path."""
    s = pfil_value.replace('\x00', '').strip()
    
    # Handle file:// URLs
    if s.lower().startswith('file://'):
        try:
            path = unquote(urlparse(s).path)
            # On Windows, file:// URLs might have /C:/ format, fix this
            if os.name == 'nt' and path.startswith('/') and len(path) > 3 and path[2] == ':':
                path = path[1:]  # Remove leading slash for Windows drive letters
            return path
        except Exception:
            pass
    
    # Handle absolute paths
    if s.startswith('/') or (os.name == 'nt' and len(s) > 1 and s[1] == ':'):
        return s
    
    # Handle relative paths - most common case for cross-platform databases
    # Serato often stores paths relative to a base music directory
    if music_folder and not os.path.isabs(s):
        # Try to map relative path to the current music folder
        # Common patterns: "Music/Music Tracks/..." -> "{music_folder}/..."
        
        # If path starts with "Music/Music Tracks/" and our folder ends with "Music Tracks"
        music_tracks_prefix = "Music/Music Tracks/"
        if s.startswith(music_tracks_prefix):
            relative_part = s[len(music_tracks_prefix):]
            candidate_path = os.path.join(music_folder, relative_part)
            return candidate_path
        
        # If path starts with "Music Tracks/"
        music_tracks_prefix2 = "Music Tracks/"  
        if s.startswith(music_tracks_prefix2):
            relative_part = s[len(music_tracks_prefix2):]
            candidate_path = os.path.join(music_folder, relative_part)
            return candidate_path
            
        # Generic fallback - assume it's relative to music folder
        candidate_path = os.path.join(music_folder, s)
        return candidate_path
    
    # Handle old-style Mac paths with colons (rare now)
    if ':' in s and '/' not in s and '\\' not in s:
        parts = s.split(':')
        if len(parts) >= 2:
            if os.name == 'nt':
                # Convert to Windows path format - this is a guess
                return f"/{parts[0]}/{'/'.join(parts[1:])}"
            else:
                return f"/Volumes/{parts[0]}/{'/'.join(parts[1:])}"
    
    return s

def debug_paths():
    config = configparser.ConfigParser()
    config.read('config.ini')
    music_folder = config.get('paths', 'music_folder')
    serato_db_path = config.get('paths', 'serato_database')

    print("=== PATH DEBUG ANALYSIS ===")
    print(f"Music folder: {music_folder}")
    print(f"Serato DB: {serato_db_path}")
    print()

    # Get local tracks
    local_music_map = scan_music_folder(music_folder)
    local_tracks_paths = {file for files in local_music_map.values() for file in files}
    local_norm_map = {_norm_for_compare(p): p for p in local_tracks_paths}
    
    # Get serato tracks
    serato_tracks_map = {}
    if os.path.exists(serato_db_path):
        db_tree = parse_serato_database(serato_db_path)
        if db_tree and 'tracks' in db_tree:
            for track in db_tree['tracks']:
                pfil_value = track.get('pfil')
                if pfil_value:
                    local_path = _serato_pfil_to_local_path(pfil_value, music_folder)
                    norm_path = _norm_for_compare(local_path)
                    serato_tracks_map[norm_path] = pfil_value

    print(f"Local tracks found: {len(local_tracks_paths)}")
    print(f"Serato tracks found: {len(serato_tracks_map)}")
    print()

    # Show sample paths
    print("=== SAMPLE LOCAL PATHS ===")
    for i, path in enumerate(list(local_tracks_paths)[:3]):
        normalized = _norm_for_compare(path)
        print(f"Original: {path}")
        print(f"Normalized: {normalized}")
        print()

    print("=== SAMPLE SERATO PATHS ===")
    for i, (norm_path, orig_pfil) in enumerate(list(serato_tracks_map.items())[:3]):
        local_converted = _serato_pfil_to_local_path(orig_pfil, music_folder)
        print(f"Original pfil: {repr(orig_pfil)}")
        print(f"Local converted: {local_converted}")
        print(f"Normalized: {norm_path}")
        print()

    # Check for matches
    serato_norm_paths = set(serato_tracks_map.keys())
    local_norm_paths = set(local_norm_map.keys())
    matches = serato_norm_paths.intersection(local_norm_paths)
    
    print(f"=== MATCH ANALYSIS ===")
    print(f"Matches found: {len(matches)}")
    
    if len(matches) > 0:
        print("Sample matches:")
        for match in list(matches)[:3]:
            print(f"  Matched: {match}")
            print(f"  Local original: {local_norm_map[match]}")
            print(f"  Serato original: {serato_tracks_map[match]}")
            print()
    
    # Show non-matches to understand the pattern
    print("=== NON-MATCH ANALYSIS ===")
    local_only = local_norm_paths - serato_norm_paths
    serato_only = serato_norm_paths - local_norm_paths
    
    print(f"Local paths not in Serato: {len(local_only)}")
    if len(local_only) > 0:
        print("Sample local-only paths:")
        for path in list(local_only)[:3]:
            print(f"  {path}")
        print()
    
    print(f"Serato paths not in local: {len(serato_only)}")
    if len(serato_only) > 0:
        print("Sample serato-only paths:")
        for path in list(serato_only)[:3]:
            print(f"  {path}")
        print()

if __name__ == "__main__":
    debug_paths()
