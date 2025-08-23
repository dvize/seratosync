#!/usr/bin/env python3

"""
Test the corrected chunk extraction without the padding.
"""

import sys
import os
import struct
sys.path.append('.')

from serato_parser_fixed import parse_serato_database
from crate_writer import _write_chunk

def test_corrected_extraction():
    """Test extracting chunks without the extra padding."""
    print("Testing corrected chunk extraction...")
    
    db_path = "E:/_Serato_/database V2"
    result = parse_serato_database(db_path)
    
    if not result or 'tracks' not in result:
        print("Failed to parse database")
        return
        
    tracks = result['tracks']
    print(f"Loaded {len(tracks)} tracks")
    
    # Test the first track
    track = tracks[0]
    print(f"Testing: {track.get('pfil', 'N/A')}")
    
    raw_chunk = track.get('__raw_chunk')
    if not raw_chunk:
        print("No raw chunk found")
        return
        
    print(f"Original raw chunk size: {len(raw_chunk)} bytes")
    print(f"First 20 bytes: {raw_chunk[:20].hex()}")
    
    # Find the otrk position  
    otrk_pos = raw_chunk.find(b'otrk')
    if otrk_pos == -1:
        print("No 'otrk' found")
        return
        
    print(f"'otrk' found at position: {otrk_pos}")
    
    # Extract the proper chunk (from the length field before otrk)
    if otrk_pos >= 4:
        # Get length field (4 bytes before otrk)
        length_field_pos = otrk_pos - 4
        length_bytes = raw_chunk[length_field_pos:otrk_pos]
        length = struct.unpack('>I', length_bytes)[0]
        print(f"Chunk payload length: {length} bytes")
        
        # Extract the full chunk: length (4) + otrk (4) + payload (length)
        corrected_chunk = raw_chunk[length_field_pos:length_field_pos + 8 + length]
        print(f"Corrected chunk size: {len(corrected_chunk)} bytes")
        print(f"Corrected chunk starts with: {corrected_chunk[:20].hex()}")
        
        # Test writing this chunk to a small file
        test_file = "test_chunk.bin"
        try:
            with open(test_file, 'wb') as f:
                # Write database header
                _write_chunk(f, 'vrsn', '2.0/Serato ScratchLive Database'.encode('utf-16-be'))
                
                # Write one corrected chunk
                f.write(corrected_chunk)
                # Add padding if needed
                pad_len = (4 - (len(corrected_chunk) % 4)) % 4
                if pad_len:
                    f.write(b'\x00' * pad_len)
                    
            print(f"Test file written: {os.path.getsize(test_file)} bytes")
            os.remove(test_file)
            
        except Exception as e:
            print(f"Error writing test file: {e}")
            
    else:
        print("Invalid chunk structure")

if __name__ == "__main__":
    test_corrected_extraction()
