#!/usr/bin/env python3

"""
Simple test to check what the serato parser actually returns.
"""

import sys
sys.path.append('.')

from serato_parser_fixed import parse_serato_database

def test_parser():
    """Test what the parser returns."""
    print("Testing Serato database parser...")
    
    db_path = "E:/_Serato_/database V2"
    result = parse_serato_database(db_path)
    
    print(f"Parser returned: {type(result)}")
    
    if isinstance(result, dict):
        print(f"Keys in result: {list(result.keys())}")
        if 'tracks' in result:
            tracks = result['tracks']
            print(f"Number of tracks: {len(tracks)}")
            
            if tracks:
                sample_track = tracks[0]
                print(f"\nSample track keys: {list(sample_track.keys())}")
                
                # Check for raw chunk
                if '__raw_chunk' in sample_track:
                    raw_chunk = sample_track['__raw_chunk']
                    print(f"Raw chunk exists: {len(raw_chunk)} bytes")
                    print(f"First 20 bytes: {raw_chunk[:20]}")
                else:
                    print("No raw chunk found in sample track!")
                
                # Check for file path
                if 'pfil' in sample_track:
                    print(f"File path: {sample_track['pfil']}")
                    
                # Show all fields to debug what's missing
                print(f"All track fields: {sample_track}")
    else:
        print(f"Unexpected result type: {result}")

if __name__ == "__main__":
    test_parser()