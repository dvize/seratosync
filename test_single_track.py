#!/usr/bin/env python3

"""
Test database structure by writing just one track back.
"""

import sys
import os
import struct
sys.path.append('.')

from serato_parser_fixed import parse_serato_database
from crate_writer import _write_chunk

def test_single_track_write():
    """Write just one track back to understand the structure."""
    print("=== SINGLE TRACK WRITE TEST ===")
    
    # Load the database
    db_path = "E:/_Serato_/database V2"
    result = parse_serato_database(db_path)
    
    if not result or 'tracks' not in result:
        print("Failed to parse database")
        return False
        
    tracks = result['tracks']
    print(f"Loaded {len(tracks)} tracks")
    
    # Get one track with raw chunk data
    test_track = None
    for track in tracks[:10]:  # Check first 10 tracks
        if '__raw_chunk' in track and 'pfil' in track:
            test_track = track
            break
            
    if not test_track:
        print("No suitable test track found")
        return False
        
    print(f"Test track: {test_track['pfil']}")
    raw_chunk = test_track['__raw_chunk']
    print(f"Raw chunk size: {len(raw_chunk)} bytes")
    
    # Create a minimal database with just the version and one track
    test_db_path = "test_single_track.db"
    
    try:
        with open(test_db_path, 'wb') as f:
            # Write database header
            _write_chunk(f, 'vrsn', '2.0/Serato ScratchLive Database'.encode('utf-16-be'))
            
            # Create main library payload with just one track
            main_library_payload = raw_chunk
            
            # Write the main library entry
            _write_chunk(f, 'oent', main_library_payload)
            
        # Check the result
        test_size = os.path.getsize(test_db_path)
        print(f"Test database created: {test_size} bytes")
        
        # Try to parse it back
        print("Attempting to parse test database...")
        test_result = parse_serato_database(test_db_path)
        
        if test_result and 'tracks' in test_result:
            parsed_tracks = test_result['tracks']
            print(f"Successfully parsed {len(parsed_tracks)} tracks from test database")
            
            if parsed_tracks:
                parsed_track = parsed_tracks[0]
                print(f"Parsed track: {parsed_track.get('pfil', 'NO PATH')}")
                print("✅ Single track write test PASSED")
                success = True
            else:
                print("❌ No tracks found in parsed test database")
                success = False
        else:
            print("❌ Failed to parse test database")
            success = False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    # Clean up
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    return success

if __name__ == "__main__":
    success = test_single_track_write()
    if success:
        print("\n🎉 Single track write test succeeded!")
        print("The database structure and raw chunks appear to be correct.")
    else:
        print("\n💥 Single track write test failed!")
        print("There's an issue with the database structure or chunk format.")
