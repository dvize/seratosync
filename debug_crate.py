#!/usr/bin/env python3
"""
Debug script to examine crate file format
"""

import os
import struct
import sys

def debug_crate_file(crate_path):
    """Debug a single crate file and show its contents"""
    print(f"\n=== Debugging crate: {os.path.basename(crate_path)} ===")
    
    if not os.path.exists(crate_path):
        print(f"File does not exist: {crate_path}")
        return
    
    try:
        with open(crate_path, 'rb') as f:
            data = f.read()
        
        print(f"File size: {len(data)} bytes")
        
        if len(data) < 8:
            print("File too small")
            return
            
        pos = 0
        chunk_num = 0
        
        while pos < len(data) - 8:
            # Read chunk tag
            if pos + 4 <= len(data):
                tag = data[pos:pos+4].decode('ascii', errors='ignore')
                print(f"\nChunk {chunk_num}: Tag='{tag}' at position {pos}")
                
                if pos + 8 <= len(data):
                    length = struct.unpack('>I', data[pos+4:pos+8])[0]
                    print(f"  Length: {length}")
                    
                    if pos + 8 + length <= len(data):
                        chunk_data = data[pos+8:pos+8+length]
                        
                        if tag == 'ptrk':
                            # This is a track path entry
                            try:
                                # Try to decode as UTF-16BE
                                track_path = chunk_data.decode('utf-16be').rstrip('\x00')
                                print(f"  Track path: '{track_path}'")
                            except:
                                # Try as UTF-8
                                try:
                                    track_path = chunk_data.decode('utf-8').rstrip('\x00')
                                    print(f"  Track path (UTF-8): '{track_path}'")
                                except:
                                    print(f"  Raw bytes: {chunk_data[:50]}...")
                        
                        elif tag == 'vrsn':
                            # Version string
                            try:
                                version = chunk_data.decode('utf-16be').rstrip('\x00')
                                print(f"  Version: '{version}'")
                            except:
                                print(f"  Version raw: {chunk_data}")
                        
                        else:
                            print(f"  Data preview: {chunk_data[:20]}...")
                        
                        # Move to next chunk (with padding)
                        pos += 8 + length
                        # Skip padding to 4-byte boundary
                        while pos < len(data) and data[pos] == 0:
                            pos += 1
                    else:
                        print("  Data extends beyond file")
                        break
                else:
                    print("  No length field")
                    break
                    
                chunk_num += 1
            else:
                pos += 1
    
    except Exception as e:
        print(f"Error: {e}")

def main():
    subcrates_path = r"E:\_Serato_\Subcrates"
    test_crate = "SetsBackup%%2025%%2nd Half%%TestFiles.crate"
    crate_path = os.path.join(subcrates_path, test_crate)
    
    debug_crate_file(crate_path)
    
    # Also check another crate for comparison
    print("\n" + "="*60)
    print("For comparison, checking 8-22-2025 crate:")
    test_crate2 = "SetsBackup%%2025%%2nd Half%%8-22-2025.crate"
    crate_path2 = os.path.join(subcrates_path, test_crate2)
    debug_crate_file(crate_path2)

if __name__ == "__main__":
    main()
