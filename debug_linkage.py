#!/usr/bin/env python3
"""
Debug script to compare paths between database and crates
"""

import os
import struct
from serato_parser_fixed import parse_serato_database
from crate_manager import parse_crate_file
import configparser

def debug_path_linkage():
    """Compare paths between database and crate files"""
    
    # Load config
    config = configparser.ConfigParser()
    config.read('config.ini')
    music_folder = config.get('paths', 'music_folder')
    serato_db_path = config.get('paths', 'serato_database')
    subcrates_path = os.path.join(os.path.dirname(serato_db_path), 'Subcrates')
    
    print("=== DEBUGGING PATH LINKAGE BETWEEN DATABASE AND CRATES ===\n")
    
    # Parse database tracks
    print("1. PARSING DATABASE TRACKS...")
    db_tracks = {}
    if os.path.exists(serato_db_path):
        db_tree = parse_serato_database(serato_db_path)
        if db_tree and 'tracks' in db_tree:
            for track in db_tree['tracks']:
                pfil_value = track.get('pfil')
                if pfil_value:
                    db_tracks[pfil_value] = track
    
    print(f"Found {len(db_tracks)} tracks in database")
    
    # Show sample database paths
    print("\nSample database pfil paths:")
    for i, pfil in enumerate(list(db_tracks.keys())[:5]):
        print(f"  {i+1}: '{pfil}'")
    
    # Parse TestFiles crate
    print("\n2. PARSING TESTFILES CRATE...")
    test_crate_path = os.path.join(subcrates_path, "SetsBackup%%2025%%2nd Half%%TestFiles.crate")
    print(f"Looking for crate at: {test_crate_path}")
    
    if os.path.exists(test_crate_path):
        crate_tracks = parse_crate_file(test_crate_path)
        print(f"Found {len(crate_tracks)} tracks in TestFiles crate")
        
        print("\nCrate track paths:")
        for i, track_path in enumerate(crate_tracks):
            print(f"  {i+1}: '{track_path}'")
        
        # Check for matches
        print("\n3. CHECKING PATH MATCHES...")
        matches = 0
        for crate_path in crate_tracks:
            if crate_path in db_tracks:
                matches += 1
                print(f"  ✓ MATCH: '{crate_path}'")
            else:
                print(f"  ✗ NO MATCH: '{crate_path}'")
                
                # Try to find similar paths
                print("    Looking for similar database paths:")
                similar_found = False
                for db_path in list(db_tracks.keys())[:10]:  # Check first 10 db paths
                    if any(part in db_path.lower() for part in crate_path.lower().split('/') if len(part) > 5):
                        print(f"      Similar: '{db_path}'")
                        similar_found = True
                        break
                
                if not similar_found:
                    print("      No similar paths found in database sample")
        
        print(f"\nSummary: {matches}/{len(crate_tracks)} crate tracks matched database tracks")
        
        if matches == 0:
            print("\n4. PATH FORMAT ANALYSIS...")
            print("Database paths format analysis:")
            db_sample = list(db_tracks.keys())[:3]
            for db_path in db_sample:
                print(f"  DB path: '{db_path}'")
                print(f"    - Starts with: '{db_path[:20]}...'")
                print(f"    - Uses separators: {'/' if '/' in db_path else ('\\' if '\\\\' in db_path else 'none')}")
                print(f"    - Is absolute: {os.path.isabs(db_path) if os.name == 'nt' else 'N/A'}")
                print()
            
            print("Crate paths format analysis:")
            for crate_path in crate_tracks[:2]:
                print(f"  Crate path: '{crate_path}'")
                print(f"    - Starts with: '{crate_path[:20]}...'")
                print(f"    - Uses separators: {'/' if '/' in crate_path else ('\\\\' if '\\\\' in crate_path else 'none')}")
                print(f"    - Is absolute: {os.path.isabs(crate_path) if os.name == 'nt' else 'N/A'}")
                print()
    else:
        print(f"TestFiles crate not found at: {test_crate_path}")

def main():
    debug_path_linkage()

if __name__ == "__main__":
    main()
