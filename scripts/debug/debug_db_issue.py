#!/usr/bin/env python3
"""Debug script to isolate the database corruption issue."""

from seratosync.database import read_database_v2_records, write_database_v2_records
from seratosync.tlv_utils import iter_tlv
from pathlib import Path
import struct
import tempfile

def analyze_database_structure(db_path):
    """Analyze the TLV structure of a database file."""
    print(f"\n=== Analyzing {db_path} ===")
    
    with open(db_path, 'rb') as f:
        chunk_count = {}
        total_chunks = 0
        
        # Analyze first few chunks
        for i, (tag, size, offset) in enumerate(iter_tlv(f)):
            total_chunks += 1
            chunk_count[tag] = chunk_count.get(tag, 0) + 1
            
            if i < 5:  # Show first 5 chunks
                if tag == 'otrk':
                    print(f"  Chunk {i+1}: {tag} (size: {size}) - Track record")
                else:
                    f.seek(offset)
                    content = f.read(min(50, size))
                    print(f"  Chunk {i+1}: {tag} (size: {size}) - {content}")
            
            if total_chunks > 100000:  # Safety break
                break
    
    print(f"  Total chunks: {total_chunks}")
    for tag, count in sorted(chunk_count.items()):
        print(f"  {tag}: {count}")
    
    return chunk_count, total_chunks

def test_read_write_cycle():
    """Test if read/write cycle preserves database structure."""
    print("\n=== Testing Read/Write Cycle ===")
    
    # Read original database
    original_records = read_database_v2_records('E:/_Serato_/database V2 - Copy')
    print(f"Read {len(original_records)} records from original DB")
    
    # Write to temporary file 
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        tmp_path = Path(tmp.name)
    
    write_database_v2_records(tmp_path, original_records)
    print(f"Wrote to temporary file: {tmp_path}")
    
    # Analyze both files
    orig_info = analyze_database_structure('E:/_Serato_/database V2 - Copy')
    temp_info = analyze_database_structure(tmp_path)
    
    # Compare
    print(f"\nStructure comparison:")
    print(f"  Original chunks: {orig_info[1]}")
    print(f"  Rewritten chunks: {temp_info[1]}")
    print(f"  Match: {orig_info[1] == temp_info[1]}")
    
    # Clean up
    tmp_path.unlink()
    
    return orig_info, temp_info

def main():
    """Main debug function."""
    print("Serato Database Corruption Debug Script")
    print("=" * 50)
    
    # First, restore clean backup
    import shutil
    print("Restoring clean backup...")
    shutil.copy2('E:/_Serato_/database V2 - Copy', 'E:/_Serato_/database V2')
    
    # Analyze original
    analyze_database_structure('E:/_Serato_/database V2 - Copy')
    
    # Test read/write cycle
    test_read_write_cycle()
    
    print("\n" + "=" * 50)
    print("Debug complete. Check output for discrepancies.")

if __name__ == "__main__":
    main()
