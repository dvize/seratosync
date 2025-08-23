#!/usr/bin/env python3

"""
Run sync and then check if new tracks actually got added to database.
"""

import os
import configparser
import sys
sys.path.append('.')

import crate_writer
from serato_parser_fixed import parse_serato_database
from crate_writer import _serato_pfil_to_local_path, _norm_for_compare

def test_sync_and_verify():
    """Run sync and check if tracks were actually added."""
    print("=== SYNC AND VERIFY TEST ===")
    
    config = configparser.ConfigParser()
    config.read('config.ini')
    serato_db_path = config.get('paths', 'serato_database')
    
    # Count tracks before sync
    print("--- Before Sync ---")
    db_tree = parse_serato_database(serato_db_path)
    tracks_before = len(db_tree['tracks']) if db_tree and 'tracks' in db_tree else 0
    print(f"Database contains {tracks_before} tracks")
    
    # Look for our test tracks
    test_track_found_before = False
    if db_tree and 'tracks' in db_tree:
        for track in db_tree['tracks']:
            pfil = track.get('pfil', '')
            if 'TestFiles' in pfil:
                print(f"Found TestFiles track BEFORE: {pfil}")
                test_track_found_before = True
    
    if not test_track_found_before:
        print("TestFiles tracks NOT found in database before sync")
    
    # Run sync
    print("\n--- Running Sync ---")
    try:
        crate_writer.main()
        print("Sync completed successfully")
    except Exception as e:
        print(f"Sync failed: {e}")
        return
    
    # Count tracks after sync
    print("\n--- After Sync ---")
    db_tree = parse_serato_database(serato_db_path)
    tracks_after = len(db_tree['tracks']) if db_tree and 'tracks' in db_tree else 0
    print(f"Database contains {tracks_after} tracks")
    print(f"Track count change: {tracks_after - tracks_before:+d}")
    
    # Look for our test tracks
    test_tracks_found_after = []
    if db_tree and 'tracks' in db_tree:
        for track in db_tree['tracks']:
            pfil = track.get('pfil', '')
            if 'TestFiles' in pfil:
                test_tracks_found_after.append(pfil)
                print(f"Found TestFiles track AFTER: {pfil}")
    
    print(f"TestFiles tracks found after sync: {len(test_tracks_found_after)}")
    
    if tracks_after > tracks_before:
        print(f"✅ SUCCESS: {tracks_after - tracks_before} new tracks added!")
    else:
        print(f"❌ PROBLEM: No new tracks added to database")

if __name__ == "__main__":
    test_sync_and_verify()
