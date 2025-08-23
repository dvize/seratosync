#!/usr/bin/env python3

"""
Test if we can now extract the large chunks correctly.
"""

import sys
sys.path.append('.')

from serato_parser_fixed import find_otrk_chunks, extract_track_from_otrk

def test_large_chunk_extraction():
    """Test extracting the first few chunks with the size limit fixed."""
    print("=== TESTING LARGE CHUNK EXTRACTION ===")
    
    db_path = "E:/_Serato_/database V2"
    
    with open(db_path, 'rb') as f:
        data = f.read()
    
    print(f"Database size: {len(data):,} bytes")
    
    # Find chunks
    chunks = find_otrk_chunks(data)
    print(f"Found {len(chunks)} otrk chunks")
    
    # Test first 3 chunks
    for i in range(min(3, len(chunks))):
        pos, length = chunks[i]
        print(f"\n--- Chunk {i+1} ---")
        print(f"Position: {pos}, Length: {length:,} bytes")
        
        # Extract track info
        track_info = extract_track_from_otrk(data, pos, length)  # pos already points to length field
        
        if track_info:
            print(f"File: {track_info.get('pfil', 'N/A')[:80]}")
            print(f"Title: {track_info.get('tsng', 'N/A')[:50]}")
            print(f"Artist: {track_info.get('tart', 'N/A')[:50]}")
            print(f"Raw chunk size: {len(track_info.get('__raw_chunk', b''))} bytes")
            
            if '__raw_chunk' in track_info:
                print("✅ Raw chunk data captured successfully!")
            else:
                print("❌ Raw chunk data missing")
        else:
            print("❌ Failed to extract track info")

if __name__ == "__main__":
    test_large_chunk_extraction()
