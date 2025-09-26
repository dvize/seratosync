#!/usr/bin/env python3
"""
Cross-platform debug script to test prefix detection and path normalization.
Works on both Windows and macOS to verify our improvements.
"""

import sys
import platform
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, '.')

from seratosync.database import read_database_v2_pfil_set, normalize_prefix
from seratosync.config import load_config

def debug_cross_platform_prefix():
    """Debug prefix detection and normalization across platforms."""
    
    print("=" * 60)
    print("CROSS-PLATFORM PREFIX DETECTION DEBUG")
    print("=" * 60)
    print(f"Platform: {platform.system()}")
    print(f"Python version: {platform.python_version()}")
    print()
    
    # Try to load config
    try:
        config = load_config()
        print("✅ Config loaded successfully")
        
        # Show config contents
        if config:
            print("Configuration contents:")
            for key, value in config.items():
                print(f"  {key}: {value}")
        else:
            print("  No configuration found or config is empty")
        print()
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        print("Using manual test paths for your platform...")
        
        # Platform-specific test paths
        if platform.system() == "Windows":
            config = {
                'db': 'E:/_Serato_/database V2',
                'library_root': 'E:/Music/Music Tracks',
                'serato_root': 'E:/_Serato_'
            }
        else:  # macOS/Linux
            config = {
                'db': '/Users/dvize/Music/_Serato_/database V2',
                'library_root': '/Users/dvize/Music/Music Tracks', 
                'serato_root': '/Users/dvize/Music/_Serato_'
            }
        
        print("Using test configuration:")
        for key, value in config.items():
            print(f"  {key}: {value}")
        print()
    
    # Setup paths from config
    if 'db' in config:
        db_path = Path(config['db'])
    else:
        print("❌ No database path found in config")
        return
        
    if 'library_root' in config:
        library_root = Path(config['library_root'])
    else:
        print("❌ No library root path found in config")
        return
    
    print(f"Database path: {db_path}")
    print(f"Library root: {library_root}")
    print(f"Database exists: {db_path.exists()}")
    print(f"Library exists: {library_root.exists()}")
    print()
    
    if not db_path.exists():
        print("⚠️  Database file doesn't exist. Testing with sample data...")
        # Create some sample database paths for testing
        if platform.system() == "Windows":
            sample_paths = {
                "E:/Music/Music Tracks/Rock/song1.mp3",
                "E:/Music/Music Tracks/Pop/song2.m4a", 
                "E:/Music/Dance/song3.flac",
                "E:/Music/Jazz/song4.mp3"
            }
            inferred_prefix = "E:/Music"
            total = len(sample_paths)
        else:  # macOS
            sample_paths = {
                "Users/dvize/Music/Music Tracks/Rock/song1.mp3",
                "Users/dvize/Music/Music Tracks/Pop/song2.m4a",
                "Users/dvize/Music/Dance/song3.flac", 
                "Users/dvize/Music/Jazz/song4.mp3"
            }
            inferred_prefix = "Users/dvize/Music"
            total = len(sample_paths)
            
        print(f"Sample database paths ({len(sample_paths)} tracks):")
        for path in sorted(sample_paths):
            print(f"  {path}")
        print(f"Simulated inferred prefix: '{inferred_prefix}'")
    else:
        print("Reading actual database...")
        try:
            sample_paths, inferred_prefix, total = read_database_v2_pfil_set(db_path)
            print(f"✅ Database read successfully")
            print(f"Total tracks: {total}")
            print(f"Inferred prefix: '{inferred_prefix}'")
            
            if sample_paths:
                print("First 5 database paths:")
                for i, path in enumerate(sorted(sample_paths)[:5]):
                    print(f"  {i+1}: {path}")
            else:
                print("No paths found in database")
        except Exception as e:
            print(f"❌ Failed to read database: {e}")
            return
    
    print()
    
    # Test prefix normalization
    print("=" * 40)
    print("PREFIX NORMALIZATION TEST")
    print("=" * 40)
    
    try:
        final_prefix = normalize_prefix(None, inferred_prefix, library_root)
        print(f"✅ Prefix normalization successful")
        print(f"Input inferred prefix: '{inferred_prefix}'")
        print(f"Input library root: '{library_root}'")
        print(f"Final normalized prefix: '{final_prefix}'")
    except Exception as e:
        print(f"❌ Prefix normalization failed: {e}")
        return
    
    print()
    
    # Test path normalization logic (from CLI)
    print("=" * 40) 
    print("PATH MATCHING TEST")
    print("=" * 40)
    
    def normalize_path_for_comparison(path_str):
        """Normalize a path string for cross-platform comparison."""
        # Convert to forward slashes
        normalized = path_str.replace("\\", "/")
        # Remove drive letters (C:, E:, etc.)
        if len(normalized) >= 3 and normalized[1] == ':':
            normalized = normalized[3:]  # Remove "C:/" or "E:/"
        # Remove leading slash
        normalized = normalized.lstrip("/")
        return normalized
    
    # Normalize paths for comparison
    library_root_normalized = normalize_path_for_comparison(str(library_root))
    prefix_normalized = normalize_path_for_comparison(final_prefix)
    
    print(f"Library root normalized: '{library_root_normalized}'") 
    print(f"Prefix normalized: '{prefix_normalized}'")
    print()
    
    # Test path matching with sample paths
    matching_paths = 0
    pfil_set_normalized = set()
    
    print("Testing path matching logic:")
    sample_list = list(sample_paths)[:5] if hasattr(sample_paths, '__iter__') else []
    
    for p_raw in sample_list:
        p_norm = normalize_path_for_comparison(p_raw)
        
        # Check if this database path is within our library root
        lib_parts = [part for part in library_root_normalized.split('/') if part]
        path_parts = [part for part in p_norm.split('/') if part]
        
        # Find if library root path is contained in database path
        library_in_database = False
        
        if len(lib_parts) <= len(path_parts):
            for i in range(len(path_parts) - len(lib_parts) + 1):
                if path_parts[i:i+len(lib_parts)] == lib_parts:
                    library_in_database = True
                    break
        
        print(f"  Path: {p_raw}")
        print(f"    Normalized: {p_norm}")
        print(f"    Library in path: {library_in_database}")
        
        if library_in_database:
            matching_paths += 1
            # Reconstruct path using prefix format
            if prefix_normalized and prefix_normalized in p_norm:
                if not p_norm.startswith(prefix_normalized + "/"):
                    prefix_pos = p_norm.find(prefix_normalized)
                    if prefix_pos >= 0:
                        p_norm = prefix_normalized + "/" + p_norm[prefix_pos + len(prefix_normalized):].lstrip("/")
                pfil_set_normalized.add(p_norm)
                print(f"    Final normalized: {p_norm}")
            else:
                pfil_set_normalized.add(p_norm)
                print(f"    Final normalized: {p_norm}")
        print()
    
    # Summary
    print("=" * 40)
    print("SUMMARY")
    print("=" * 40)
    
    total_test_paths = len(sample_list)
    match_percentage = (matching_paths / total_test_paths * 100) if total_test_paths > 0 else 0
    
    print(f"Platform: {platform.system()}")
    print(f"Total test paths: {total_test_paths}")
    print(f"Matching paths: {matching_paths}")
    print(f"Match percentage: {match_percentage:.1f}%")
    print(f"Normalized database paths: {len(pfil_set_normalized)}")
    
    if match_percentage >= 80:
        print("✅ PASS - Path matching logic works well")
    else:
        print("❌ FAIL - Path matching logic needs improvement")
    
    print(f"Final prefix to use: '{final_prefix}'")
    
    if len(pfil_set_normalized) > 0:
        print("✅ Some database paths successfully normalized")
    else:
        print("⚠️  No database paths were successfully normalized")

if __name__ == "__main__":
    debug_cross_platform_prefix()
