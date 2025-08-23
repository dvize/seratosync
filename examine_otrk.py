#!/usr/bin/env python3

"""
Examine the binary data around otrk chunks to understand the real structure.
"""

import struct

def examine_otrk_environment():
    """Look at the data around otrk chunks to understand the true structure."""
    print("=== OTRK ENVIRONMENT ANALYSIS ===")
    
    db_path = "E:/_Serato_/database V2"
    
    with open(db_path, 'rb') as f:
        data = f.read()
    
    print(f"Database size: {len(data):,} bytes")
    
    # Find first few otrk occurrences
    otrk_positions = []
    pos = 0
    for _ in range(5):  # Just examine first 5
        pos = data.find(b'otrk', pos)
        if pos == -1:
            break
        otrk_positions.append(pos)
        pos += 4
    
    print(f"Found {len(otrk_positions)} otrk positions for analysis")
    
    for i, otrk_pos in enumerate(otrk_positions):
        print(f"\n--- OTRK {i+1} at position {otrk_pos} ---")
        
        # Look at data before and after this otrk
        start_pos = max(0, otrk_pos - 100)
        end_pos = min(len(data), otrk_pos + 1000)
        
        context = data[start_pos:end_pos]
        otrk_offset = otrk_pos - start_pos
        
        # Print hex dump around the otrk
        print(f"Context from {start_pos} to {end_pos}:")
        for j in range(0, len(context), 16):
            line = context[j:j+16]
            hex_str = ' '.join(f'{b:02x}' for b in line)
            ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in line)
            
            pos_marker = ''
            if start_pos + j <= otrk_pos < start_pos + j + 16:
                pos_marker = f' <-- otrk at {otrk_pos}'
            
            print(f'{start_pos + j:08x}: {hex_str:<48} {ascii_str}{pos_marker}')
        
        # Try to parse the chunk length
        if otrk_pos >= 4:
            length_pos = otrk_pos - 4
            try:
                chunk_length = struct.unpack('>I', data[length_pos:otrk_pos])[0]
                print(f"Stated chunk length: {chunk_length} bytes")
                
                # Show what's in the chunk payload
                payload_start = otrk_pos + 4
                payload_end = min(payload_start + chunk_length, len(data))
                payload = data[payload_start:payload_end]
                
                print(f"Chunk payload ({len(payload)} bytes):")
                
                # Look for interesting fields in the payload
                fields_found = []
                for field in [b'pfil', b'tsng', b'tart', b'talb', b'tgen', b'tkey', b'tbpm', b'tlen', b'tbit', b'ttyp']:
                    if field in payload:
                        field_pos = payload.find(field)
                        fields_found.append(f"{field.decode('ascii')}@{field_pos}")
                
                print(f"Fields found: {', '.join(fields_found)}")
                
                # Check what comes after this chunk
                next_pos = otrk_pos + 4 + chunk_length
                if next_pos < len(data) - 8:
                    next_data = data[next_pos:next_pos + 16]
                    print(f"Next 16 bytes after chunk: {next_data.hex()}")
                    
                    # Check if there's another otrk nearby
                    search_range = data[next_pos:next_pos + 1000]
                    next_otrk = search_range.find(b'otrk')
                    if next_otrk != -1:
                        print(f"Next otrk found {next_otrk} bytes later")
                    else:
                        print("No otrk found in next 1000 bytes")
                
            except (struct.error, IndexError) as e:
                print(f"Error reading chunk length: {e}")

if __name__ == "__main__":
    examine_otrk_environment()
