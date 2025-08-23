#!/usr/bin/env python3

"""
Debug the raw chunk extraction to identify the database write issue.
"""

import sys
import os
sys.path.append('.')

from serato_parser_fixed import parse_serato_database

def analyze_raw_chunks():
    """Analyze the first few raw chunks to understand the structure."""
    print("Analyzing raw chunk extraction...")
    
    db_path = "E:/_Serato_/database V2"
    result = parse_serato_database(db_path)
    
    if not result or 'tracks' not in result:
        print("Failed to parse database")
        return
        
    tracks = result['tracks']
    print(f"Loaded {len(tracks)} tracks")
    
    # Analyze first 3 tracks
    for i, track in enumerate(tracks[:3]):
        print(f"\n--- Track {i+1} ---")
        print(f"File: {track.get('pfil', 'N/A')}")
        
        raw_chunk = track.get('__raw_chunk')
        if raw_chunk:
            print(f"Raw chunk size: {len(raw_chunk)} bytes")
            print(f"First 32 bytes: {raw_chunk[:32]}")
            print(f"First 32 bytes hex: {raw_chunk[:32].hex()}")
            
            # Check for otrk header
            otrk_pos = raw_chunk.find(b'otrk')
            if otrk_pos != -1:
                print(f"'otrk' found at position: {otrk_pos}")
                # Check length field (4 bytes before otrk)
                if otrk_pos >= 4:
                    length_bytes = raw_chunk[otrk_pos-4:otrk_pos]
                    import struct
                    try:
                        length = struct.unpack('>I', length_bytes)[0]
                        print(f"Chunk length: {length} bytes")
                        print(f"Expected total chunk size: {8 + length} bytes (header + payload)")
                    except:
                        print("Could not decode length")
            else:
                print("No 'otrk' found in raw chunk - this is the problem!")
        else:
            print("No raw chunk found")

if __name__ == "__main__":
    analyze_raw_chunks()
