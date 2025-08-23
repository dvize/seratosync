#!/usr/bin/env python3

"""
Minimal sync test to debug the database corruption issue.
This will test adding just the TestFiles tracks to understand what's breaking.
"""

import os
import sys
sys.path.append('.')

# Import necessary functions
from crate_writer import sync_serato_database

def minimal_sync_test():
    """Run a minimal sync test with just TestFiles."""
    print("=== MINIMAL SYNC TEST ===")
    
    # Create a backup first
    original_db = "E:/_Serato_/database V2"
    backup_db = "E:/_Serato_/database V2.backup_before_minimal_test"
    
    # Backup
    import shutil
    shutil.copy2(original_db, backup_db)
    print(f"Created backup: {backup_db}")
    
    # Get original size
    original_size = os.path.getsize(original_db)
    print(f"Original database size: {original_size:,} bytes")
    
    # Set sync parameters directly
    music_folder = "E:/Music/Music Tracks/"
    serato_db_path = "E:/_Serato_/database V2"
    serato_subcrates_path = "E:/_Serato_/Subcrates"
    exclude_missing_files = False  # Keep all tracks to preserve data
    
    # Run sync with TestFiles folder existing
    test_music_folder = "E:/Music/Music Tracks/SetsBackup/2025/2nd Half/TestFiles"
    
    if os.path.exists(test_music_folder):
        print(f"Testing with folder: {test_music_folder}")
        test_files = [f for f in os.listdir(test_music_folder) if f.endswith('.mp3')]
        print(f"Found {len(test_files)} test files:")
        for f in test_files:
            print(f"  - {f}")
            
        try:
            print("\nRunning minimal sync...")
            sync_serato_database(
                music_folder,
                serato_db_path,
                serato_subcrates_path,
                exclude_missing_files
            )
            
            # Check result
            new_size = os.path.getsize(original_db)
            print(f"New database size: {new_size:,} bytes")
            size_change = new_size - original_size
            print(f"Size change: {size_change:+,} bytes")
            
            if new_size < original_size * 0.8:  # Lost more than 20% of data
                print("*** DATABASE CORRUPTION DETECTED ***")
                print("Restoring from backup...")
                shutil.copy2(backup_db, original_db)
                print("Database restored.")
                return False
            else:
                print("Sync appears successful.")
                return True
                
        except Exception as e:
            print(f"Error during sync: {e}")
            import traceback
            traceback.print_exc()
            # Restore backup
            shutil.copy2(backup_db, original_db)
            print("Database restored from backup.")
            return False
        
    else:
        print(f"Test folder not found: {test_music_folder}")
        return False

if __name__ == "__main__":
    success = minimal_sync_test()
    if success:
        print("Minimal test completed successfully.")
    else:
        print("Minimal test failed - database corruption detected.")
