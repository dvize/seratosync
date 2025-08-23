#!/usr/bin/env python3

"""
Analyze the overall database structure to understand what we're missing.
"""

import struct
import os

def analyze_database_structure():
    """Analyze the overall structure of the Serato database."""
    print("=== DATABASE STRUCTURE ANALYSIS ===")
    
    db_path = "E:/_Serato_/database V2"
    
    with open(db_path, 'rb') as f:
        data = f.read()
    
    print(f"Database size: {len(data):,} bytes")
    
    # Look for all chunk types (4-byte tags)
    chunk_types = {}
    pos = 0
    
    while pos < len(data) - 8:
        # Try to read a potential chunk header
        try:
            # Look for 4-byte length followed by 4-byte tag
            length_bytes = data[pos:pos+4]
            tag_bytes = data[pos+4:pos+8]
            
            # Check if this looks like a valid chunk
            if len(length_bytes) == 4 and len(tag_bytes) == 4:
                try:
                    length = struct.unpack('>I', length_bytes)[0]
                    tag = tag_bytes.decode('ascii', errors='ignore')
                    
                    # Valid chunk criteria
                    if (0 < length < 50000000 and  # Reasonable length
                        all(32 <= b <= 126 for b in tag_bytes)):  # Printable ASCII tag
                        
                        chunk_types[tag] = chunk_types.get(tag, 0) + 1
                        
                        # Skip to next potential chunk
                        pos += 8 + length
                        # Add padding to align to 4-byte boundary
                        pad = (4 - (length % 4)) % 4
                        pos += pad
                        continue
                        
                except (struct.error, UnicodeDecodeError):
                    pass
                    
        except IndexError:
            break
            
        pos += 1
    
    print(f"\nFound chunk types:")
    for tag, count in sorted(chunk_types.items()):
        print(f"  '{tag}': {count:5d} chunks")
    
    # Calculate total accounted data
    total_accounted = 0
    pos = 0
    
    while pos < len(data) - 8:
        try:
            length_bytes = data[pos:pos+4]
            tag_bytes = data[pos+4:pos+8]
            
            if len(length_bytes) == 4 and len(tag_bytes) == 4:
                try:
                    length = struct.unpack('>I', length_bytes)[0]
                    tag = tag_bytes.decode('ascii', errors='ignore')
                    
                    if (0 < length < 50000000 and
                        all(32 <= b <= 126 for b in tag_bytes)):
                        
                        chunk_size = 8 + length  # Header + payload
                        pad = (4 - (length % 4)) % 4
                        total_chunk_size = chunk_size + pad
                        
                        total_accounted += total_chunk_size
                        pos += total_chunk_size
                        continue
                        
                except (struct.error, UnicodeDecodeError):
                    pass
                    
        except IndexError:
            break
            
        pos += 1
    
    print(f"\nTotal accounted data: {total_accounted:,} bytes")
    print(f"Unaccounted data: {len(data) - total_accounted:,} bytes")
    print(f"Accounted percentage: {100 * total_accounted / len(data):.1f}%")

if __name__ == "__main__":
    analyze_database_structure()
