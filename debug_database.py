#!/usr/bin/env python3

"""
Test script to debug database writing issues in SeratoSync.
This script tests the database writing process with a minimal approach.
"""

import os
import struct
import sys
sys.path.append('.')

# Import the necessary functions
from serato_parser_fixed import parse_serato_database
from crate_writer import _write_chunk, create_track_chunk_payload
from crate_manager import normalize_path_for_crate

def test_database_write():
    """Test the database writing process with existing data."""
    print("=== SeratoSync Database Write Test ===")
    
    # Load original database
    original_db = "E:/_Serato_/database V2"
    test_db = "E:/_Serato_/database V2.test"
    
    print("Loading original database...")
    try:
        tracks = parse_serato_database(original_db)
        print(f"Loaded {len(tracks)} tracks from original database")
        
        # Get original file size
        original_size = os.path.getsize(original_db)
        print(f"Original database size: {original_size:,} bytes")
        
    except Exception as e:
        print(f"Error loading database: {e}")
        return False
    
    # Test writing the database back without any changes
    print("\nTesting database write without modifications...")
    try:
        with open(test_db, 'wb') as f:
            # Write database header
            _write_chunk(f, 'vrsn', '2.0/Serato ScratchLive Database'.encode('utf-16-be'))
            
            # Create the main library entry ('oent') containing all existing tracks
            main_library_payload = b''
            
            # This is where the issue likely occurs - we need the raw otrk chunks
            print("Error: We don't have access to raw otrk chunks from parse_serato_database!")
            print("The parser only returns processed track data, not the raw binary chunks.")
            
        os.remove(test_db) if os.path.exists(test_db) else None
        return False
            
    except Exception as e:
        print(f"Error during write test: {e}")
        if os.path.exists(test_db):
            os.remove(test_db)
        return False

def test_new_track_creation():
    """Test creating a new track chunk."""
    print("\n=== Testing New Track Creation ===")
    
    # Test files
    test_files = [
        "E:/Music/Music Tracks/SetsBackup/2025/2nd Half/TestFiles/drake-feat.-central-cee-which-one-onedye-remix-dirty-120-4a.mp3",
        "E:/Music/Music Tracks/SetsBackup/2025/2nd Half/TestFiles/steve-aoki-dimitri-vegas-like-mike-timbaland-ww-cry-me-a-river-150-1a.mp3"
    ]
    
    music_folder = "E:/Music/Music Tracks/"
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\nTesting: {os.path.basename(test_file)}")
            
            try:
                # Normalize path
                normalized_path = normalize_path_for_crate(test_file, music_folder)
                print(f"Normalized path: {normalized_path}")
                
                # Create track chunk payload
                otrk_payload = create_track_chunk_payload(test_file, normalized_path)
                print(f"Created otrk payload: {len(otrk_payload)} bytes")
                
                # Create full otrk chunk
                otrk_header = b'otrk' + struct.pack('>I', len(otrk_payload))
                full_chunk = otrk_header + otrk_payload
                print(f"Full otrk chunk: {len(full_chunk)} bytes")
                
            except Exception as e:
                print(f"Error creating track chunk: {e}")
        else:
            print(f"Test file not found: {test_file}")

if __name__ == "__main__":
    success = test_database_write()
    test_new_track_creation()
    
    if not success:
        print("\n*** IDENTIFIED ISSUE ***")
        print("The problem is that parse_serato_database() returns processed track data,")
        print("but we need the raw binary otrk chunks to rebuild the database properly.")
        print("The sync script tries to combine existing processed data with new raw chunks,")
        print("which causes the database corruption.")
