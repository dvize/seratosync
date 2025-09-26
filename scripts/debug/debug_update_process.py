#!/usr/bin/env python3
"""Debug script to trace the update_database_v2 process step by step."""

from seratosync.database import read_database_v2_records, read_database_v2_pfil_set, write_database_v2_records
from seratosync.library import scan_library, detect_new_tracks
from pathlib import Path
import time
import struct
from seratosync.tlv_utils import make_chunk

def debug_update_process():
    """Debug the entire update process step by step."""
    
    print("=== DEBUGGING UPDATE PROCESS ===")
    
    # Step 1: Read current database
    print("\n1. Reading current database...")
    records = read_database_v2_records('E:/_Serato_/database V2')
    print(f"   Current records: {len(records)}")
    
    # Step 2: Get database paths
    print("\n2. Getting database file paths...")
    db_paths = read_database_v2_pfil_set('E:/_Serato_/database V2')
    print(f"   DB paths count: {len(db_paths)}")
    
    # Step 3: Scan library
    print("\n3. Scanning library...")
    library_root = Path('E:/Music/Music Tracks')
    extensions = ['.mp3', '.m4a', '.flac', '.wav']
    all_tracks = scan_library(library_root, extensions)
    print(f"   Library tracks: {len(all_tracks)}")
    
    # Step 4: Detect new tracks
    print("\n4. Detecting new tracks...")
    new_tracks = detect_new_tracks(all_tracks, db_paths)
    print(f"   New tracks: {len(new_tracks)}")
    
    if new_tracks:
        # LIMIT TO JUST A FEW TRACKS FOR DEBUGGING
        limited_tracks = new_tracks[:3]  # Only process first 3 tracks
        print(f"   Processing only first {len(limited_tracks)} tracks for debugging:")
        for track in limited_tracks:
            print(f"     {track}")
    else:
        print("   No new tracks found!")
        return
    
    # Step 5: Create new record(s)
    print("\n5. Creating new records...")
    
    for p in limited_tracks:
        ext = Path(p).suffix.lower().lstrip(".") or "mp3"
        current_timestamp = str(int(time.time()))
        current_timestamp_int = int(time.time())
        filename = Path(p).stem
        
        record = {
            # Required text fields (basic)
            'ttyp': ext,
            'pfil': p,
            'tadd': current_timestamp,
            
            # Required metadata fields (defaults that Serato will update when analyzing)
            'tart': '',  # Artist (empty - Serato will populate)
            'tbit': '128.0kbps',  # Bitrate (default - Serato will correct)
            'tbpm': '120.00',  # BPM (default - Serato will analyze and correct)
            'tcom': '1A - 120.0',  # Comment/Key combo (default)
            'tgen': '',  # Genre (empty - Serato will populate)
            'tgrp': '',  # Grouping (empty)
            'tkey': '1A',  # Musical key (default - Serato will analyze)
            'tlen': '03:30.00',  # Length (default - Serato will correct)
            'tsmp': '44.1k',  # Sample rate (default)
            
            # Required binary fields (UTF-16BE encoded text)
            'tlbl': ''.encode('utf-16be').ljust(16, b'\x00')[:16],
            'tsiz': '0.0MB'.encode('utf-16be').ljust(10, b'\x00')[:10],
            'tsng': filename[:10].encode('utf-16be').ljust(20, b'\x00')[:20],
            'ttyr': '2025'.encode('utf-16be'),
            
            # Required binary integer fields
            'uadd': struct.pack('>I', current_timestamp_int),
            'utme': struct.pack('>I', current_timestamp_int),
            'utpc': struct.pack('>I', 0),
            'ufsb': struct.pack('>I', 0),
            'ulbl': struct.pack('>I', 0),
            
            # Single-byte boolean flags
            'bhrt': b'\x00', 'bmis': b'\x00', 'bply': b'\x00', 'blop': b'\x00',
            'bitu': b'\x00', 'bovc': b'\x00', 'bcrt': b'\x00', 'biro': b'\x00',
            'bwlb': b'\x00', 'bwll': b'\x00', 'buns': b'\x00', 'bbgl': b'\x00',
            'bkrk': b'\x00'
        }
        
        print(f"   Created record for: {p}")
        print(f"   Record fields: {len(record)}")
        
        # Step 6: Append to records list
        print("\n6. Appending to records list...")
        print(f"   Records before append: {len(records)}")
        records.append(record)
        print(f"   Records after append: {len(records)}")
        
        # Step 7: Write back to database
        print("\n7. Writing back to database...")
        try:
            write_database_v2_records(Path('E:/_Serato_/database V2'), records)
            print(f"   Write successful!")
            
            # Step 8: Verify the write
            print("\n8. Verifying write...")
            verification_records = read_database_v2_records('E:/_Serato_/database V2')
            print(f"   Records after write: {len(verification_records)}")
            
            # Check if our record is actually there
            found = False
            for i, rec in enumerate(verification_records):
                if 'pfil' in rec and 'TestSong123' in rec['pfil']:
                    found = True
                    print(f"   TestSong123 found at index {i}")
                    break
            
            if not found:
                print("   ERROR: TestSong123 NOT found after write!")
            
            if len(verification_records) != len(records):
                print(f"   ERROR: Record count mismatch! Expected {len(records)}, got {len(verification_records)}")
            else:
                print(f"   SUCCESS: Record count matches ({len(verification_records)})")
            
        except Exception as e:
            print(f"   ERROR during write: {e}")

if __name__ == "__main__":
    debug_update_process()
