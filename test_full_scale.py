#!/usr/bin/env python3

"""
Test the full-scale database write to identify the real issue.
This simulates the actual sync process with all tracks.
"""

import sys
import os
sys.path.append('.')

from serato_parser_fixed import parse_serato_database
from crate_writer import _write_chunk, create_track_chunk_payload
from crate_manager import normalize_path_for_crate
import struct

def test_full_scale_sync():
    """Test writing all tracks plus new ones like the real sync."""
    print("=== FULL SCALE SYNC TEST ===")
    
    # Create backup first
    original_db = "E:/_Serato_/database V2"
    backup_db = f"{original_db}.backup_full_test"
    
    import shutil
    shutil.copy2(original_db, backup_db)
    print(f"Created backup: {backup_db}")
    
    # Load the database
    result = parse_serato_database(original_db)
    
    if not result or 'tracks' not in result:
        print("Failed to parse database")
        return False
        
    tracks = result['tracks']
    print(f"Loaded {len(tracks)} tracks")
    
    # Get tracks with raw chunk data (like the sync process does)
    valid_tracks_to_write = []
    for track in tracks:
        if '__raw_chunk' in track and 'pfil' in track:
            valid_tracks_to_write.append(track['__raw_chunk'])
    
    print(f"Found {len(valid_tracks_to_write)} valid tracks with raw chunks")
    
    # Simulate adding new tracks (like the sync process)
    test_music_folder = "E:/Music/Music Tracks/"
    test_files = [
        "E:/Music/Music Tracks/SetsBackup/2025/2nd Half/TestFiles/drake-feat.-central-cee-which-one-onedye-remix-dirty-120-4a.mp3",
        "E:/Music/Music Tracks/SetsBackup/2025/2nd Half/TestFiles/steve-aoki-dimitri-vegas-like-mike-timbaland-ww-cry-me-a-river-150-1a.mp3"
    ]
    
    new_tracks_data = []
    for path in test_files:
        if os.path.exists(path):
            print(f"Adding new track: {os.path.basename(path)}")
            normalized_path = normalize_path_for_crate(path, test_music_folder)
            otrk_payload = create_track_chunk_payload(path, normalized_path)
            otrk_header = b'otrk' + struct.pack('>I', len(otrk_payload))
            full_chunk = otrk_header + otrk_payload
            new_tracks_data.append(full_chunk)
        else:
            print(f"Test file not found: {path}")
    
    print(f"Created {len(new_tracks_data)} new track chunks")
    
    # Now write the database exactly like the sync process does
    test_db_path = f"{original_db}.test_full"
    
    try:
        print("Writing full database...")
        with open(test_db_path, 'wb') as f:
            # Write database header
            _write_chunk(f, 'vrsn', '2.0/Serato ScratchLive Database'.encode('utf-16-be'))
            
            # Create the main library entry ('oent') containing all tracks
            main_library_payload = b''
            
            # Add existing tracks
            existing_size = 0
            for track_chunk in valid_tracks_to_write:
                main_library_payload += track_chunk
                existing_size += len(track_chunk)
            
            # Add new tracks
            new_size = 0
            for new_chunk in new_tracks_data:
                main_library_payload += new_chunk
                new_size += len(new_chunk)
            
            print(f"Existing tracks payload: {existing_size:,} bytes")
            print(f"New tracks payload: {new_size:,} bytes")
            print(f"Total main library payload: {len(main_library_payload):,} bytes")
            
            # Write the main library entry
            _write_chunk(f, 'oent', main_library_payload)
        
        # Check the result
        test_size = os.path.getsize(test_db_path)
        original_size = os.path.getsize(original_db)
        print(f"Original database: {original_size:,} bytes")
        print(f"Test database: {test_size:,} bytes")
        print(f"Size change: {test_size - original_size:+,} bytes")
        
        if test_size < original_size * 0.8:
            print("❌ CORRUPTION DETECTED - Test database too small!")
            return False
        
        # Try to parse it back
        print("Parsing test database...")
        test_result = parse_serato_database(test_db_path)
        
        if test_result and 'tracks' in test_result:
            parsed_tracks = test_result['tracks']
            print(f"✅ Successfully parsed {len(parsed_tracks)} tracks")
            
            expected_tracks = len(tracks) + len(new_tracks_data)
            if len(parsed_tracks) >= len(tracks):  # Should have at least original count
                print("✅ Full scale test PASSED!")
                success = True
            else:
                print(f"❌ Expected at least {len(tracks)} tracks, got {len(parsed_tracks)}")
                success = False
                
        else:
            print("❌ Failed to parse test database")
            success = False
            
    except Exception as e:
        print(f"❌ Error during full scale test: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    finally:
        # Clean up test file
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
    
    return success

if __name__ == "__main__":
    success = test_full_scale_sync()
    if success:
        print("\n🎉 Full scale sync test succeeded!")
        print("The database writing should work correctly in the real sync.")
    else:
        print("\n💥 Full scale sync test failed!")
        print("Found the issue that causes database corruption.")
