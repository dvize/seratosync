#!/usr/bin/env python3
"""Debug why crates are being rewritten when there are no changes."""

from seratosync.crates import read_crate_file, build_crate_payload
from seratosync.library import scan_library, build_crate_plans
from seratosync.database import read_database_v2_pfil_set, normalize_prefix
from pathlib import Path
import json

def debug_crate_writes():
    """Debug why crates are being rewritten unnecessarily."""
    
    print("=== DEBUGGING CRATE REWRITES ===")
    
    # Use same config as main
    library_root = Path('E:/Music/Music Tracks')
    serato_root = Path('E:/_Serato_/Subcrates')
    db_path = Path('E:/_Serato_/database V2')
    allowed_exts = {'.mp3', '.m4a', '.flac', '.wav'}
    
    # Get prefix
    pfil_set_raw, inferred, total = read_database_v2_pfil_set(db_path)
    prefix = normalize_prefix(None, inferred, library_root)
    print(f"Using prefix: '{prefix}'")
    
    # Scan library and build crate plans
    lib_map = scan_library(library_root, allowed_exts)
    crate_plans = build_crate_plans(lib_map, prefix, serato_root)
    
    print(f"Found {len(crate_plans)} crate plans")
    
    # Check specific crates that were reported as "Updated"  
    target_crates = [
        'SetsBackup%%2024%%5-17-2024%%Dance.crate',
        'SetsBackup%%2025%%Test.crate'
    ]
    
    checked = 0
    differences_found = 0
    
    for crate_file, ptrks in crate_plans:
        # Look for target crates or check first few if targets not found
        should_check = (crate_file.name in target_crates or 
                       (len(target_crates) == 0 and checked < 5))
        
        if not should_check or not crate_file.exists():
            continue
        
        if checked >= 10:  # Safety limit
            break
            
        checked += 1
        print(f"\nChecking crate: {crate_file.name}")
        print(f"  Expected tracks: {len(ptrks)}")
        
        # Read existing crate
        existing_tracks = read_crate_file(crate_file)
        print(f"  Current tracks: {len(existing_tracks)}")
        
        # Generate new payload
        new_bytes = build_crate_payload(ptrks)
        
        # Read current payload
        with open(crate_file, "rb") as f:
            old_bytes = f.read()
            
        print(f"  Old payload size: {len(old_bytes)} bytes")
        print(f"  New payload size: {len(new_bytes)} bytes")
        
        if old_bytes == new_bytes:
            print("  ✓ Payloads match - no write needed")
        else:
            differences_found += 1
            print("  ✗ Payloads differ - would rewrite")
            
            # Compare track lists
            if set(existing_tracks) != set(ptrks):
                print("    Track list differences:")
                only_old = set(existing_tracks) - set(ptrks)
                only_new = set(ptrks) - set(existing_tracks)
                if only_old:
                    print(f"    Only in old: {list(only_old)[:3]}...")  # Show first 3
                if only_new:
                    print(f"    Only in new: {list(only_new)[:3]}...")
            else:
                print("    Track lists identical - must be encoding difference")
            
            # Find first binary difference
            min_len = min(len(old_bytes), len(new_bytes))
            for i in range(min_len):
                if old_bytes[i] != new_bytes[i]:
                    print(f"    First diff at byte {i}: old=0x{old_bytes[i]:02x}, new=0x{new_bytes[i]:02x}")
                    
                    # Try to decode around the difference to see what changed
                    start = max(0, i-20)
                    end = min(len(old_bytes), i+20)
                    old_context = old_bytes[start:end]
                    new_context = new_bytes[start:end]
                    
                    try:
                        old_str = old_context.decode('utf-16-be', errors='replace')
                        new_str = new_context.decode('utf-16-be', errors='replace')
                        print(f"    Old context: {repr(old_str)}")
                        print(f"    New context: {repr(new_str)}")
                    except:
                        pass
                    break
            
            if len(old_bytes) != len(new_bytes):
                print(f"    Size difference: {len(new_bytes) - len(old_bytes)} bytes")
    
    print(f"\n=== SUMMARY ===")
    print(f"Crates checked: {checked}")  
    print(f"Differences found: {differences_found}")
    
    if differences_found == 0:
        print("No differences found - crates should NOT be rewritten")
    else:
        print("Differences found - crates WOULD be rewritten")

if __name__ == "__main__":
    debug_crate_writes()
