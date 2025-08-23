#!/usr/bin/env python3

"""
Test database structure by writing multiple tracks back.
"""

import sys
import os
sys.path.append('.')

from serato_parser_fixed import parse_serato_database
from crate_writer import _write_chunk

def test_multiple_tracks_write():
    """Write multiple tracks back to identify the scaling issue."""
    print("=== MULTIPLE TRACKS WRITE TEST ===")
    
    # Load the database
    db_path = "E:/_Serato_/database V2"
    result = parse_serato_database(db_path)
    
    if not result or 'tracks' not in result:
        print("Failed to parse database")
        return False
        
    tracks = result['tracks']
    print(f"Loaded {len(tracks)} tracks")
    
    # Test with different numbers of tracks
    test_counts = [1, 10, 100, 1000]
    
    for count in test_counts:
        if count > len(tracks):
            count = len(tracks)
            
        print(f"\n--- Testing with {count} tracks ---")
        
        # Get tracks with raw chunk data
        test_tracks = []
        for track in tracks:
            if '__raw_chunk' in track and 'pfil' in track:
                test_tracks.append(track)
                if len(test_tracks) >= count:
                    break
                    
        if len(test_tracks) < count:
            print(f"Only found {len(test_tracks)} valid tracks")
            test_tracks_to_use = test_tracks
        else:
            test_tracks_to_use = test_tracks[:count]
            
        # Create database with these tracks
        test_db_path = f"test_{count}_tracks.db"
        
        try:
            with open(test_db_path, 'wb') as f:
                # Write database header
                _write_chunk(f, 'vrsn', '2.0/Serato ScratchLive Database'.encode('utf-16-be'))
                
                # Create main library payload with multiple tracks
                main_library_payload = b''
                total_raw_size = 0
                
                for track in test_tracks_to_use:
                    raw_chunk = track['__raw_chunk']
                    main_library_payload += raw_chunk
                    total_raw_size += len(raw_chunk)
                
                print(f"Total raw chunks size: {total_raw_size:,} bytes")
                print(f"Main library payload size: {len(main_library_payload):,} bytes")
                
                # Write the main library entry
                _write_chunk(f, 'oent', main_library_payload)
                
            # Check the result
            test_size = os.path.getsize(test_db_path)
            print(f"Test database created: {test_size:,} bytes")
            
            # Try to parse it back
            print(f"Parsing test database with {count} tracks...")
            test_result = parse_serato_database(test_db_path)
            
            if test_result and 'tracks' in test_result:
                parsed_tracks = test_result['tracks']
                print(f"✅ Successfully parsed {len(parsed_tracks)} tracks")
                
                if len(parsed_tracks) != len(test_tracks_to_use):
                    print(f"⚠️  Expected {len(test_tracks_to_use)} tracks, got {len(parsed_tracks)}")
                    
            else:
                print(f"❌ Failed to parse test database with {count} tracks")
                return False
                
        except Exception as e:
            print(f"❌ Error with {count} tracks: {e}")
            return False
        finally:
            # Clean up
            if os.path.exists(test_db_path):
                os.remove(test_db_path)
                
        if count >= 1000:
            break  # Don't test larger numbers if 1000 works
    
    return True

if __name__ == "__main__":
    success = test_multiple_tracks_write()
    if success:
        print("\n🎉 Multiple tracks write test succeeded!")
        print("The issue must be in the sync logic itself, not the database writing.")
    else:
        print("\n💥 Multiple tracks write test failed!")
        print("Found the scaling issue in database writing.")
