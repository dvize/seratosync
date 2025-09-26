#!/usr/bin/env python3
"""
Windows-specific debug script using the actual paths mentioned by the user.
Tests the scenario: inferred prefix 'E:/Music/Music Tracks', 30,396 tracks, 1251 existing crates.
"""

import sys
import platform
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, '.')

from seratosync.database import read_database_v2_pfil_set, normalize_prefix
from seratosync.library import scan_library, build_crate_plans, detect_new_tracks

def debug_windows_scenario():
    """Debug the specific Windows scenario where all tracks are detected as new."""
    
    print("=" * 60)
    print("WINDOWS SCENARIO DEBUG")  
    print("=" * 60)
    print(f"Platform: {platform.system()}")
    print()
    
    # Use the paths mentioned in the user's issue
    print("Testing with reported issue scenario:")
    print("- Inferred prefix: 'E:/Music/Music Tracks'")
    print("- 30,396 tracks in database")
    print("- 1,251 existing crates with 30,396 total tracks")
    print("- All tracks incorrectly detected as 'new'")
    print()
    
    # Simulate the problematic scenario with test data
    simulated_library_root = Path("E:/Music/Music Tracks")
    simulated_inferred_prefix = "E:/Music/Music Tracks"
    
    # Create sample database paths that would exist in a real database
    sample_db_paths = {
        "E:/Music/Music Tracks/Rock/Led Zeppelin/IV/Black Dog.mp3",
        "E:/Music/Music Tracks/Rock/Pink Floyd/Dark Side/Money.flac", 
        "E:/Music/Music Tracks/Pop/Michael Jackson/Thriller.mp3",
        "E:/Music/Music Tracks/Electronic/Daft Punk/Get Lucky.m4a",
        "E:/Music/Music Tracks/Jazz/Miles Davis/Kind of Blue.wav",
        "E:/Music/Dance/Calvin Harris/Feel So Close.mp3",  # Outside Music Tracks
        "E:/Music/Hip Hop/Eminem/Lose Yourself.mp3",      # Outside Music Tracks  
        "E:/Music/Classical/Bach/Brandenburg.flac"         # Outside Music Tracks
    }
    
    print("Sample database paths:")
    for path in sorted(sample_db_paths):
        print(f"  {path}")
    print()
    
    # Test prefix normalization
    print("=" * 40)
    print("PREFIX NORMALIZATION TEST")
    print("=" * 40)
    
    normalized_prefix = normalize_prefix(None, simulated_inferred_prefix, simulated_library_root)
    print(f"Library root: {simulated_library_root}")
    print(f"Inferred prefix: '{simulated_inferred_prefix}'")  
    print(f"Normalized prefix: '{normalized_prefix}'")
    print()
    
    # Test path normalization function
    def normalize_path_for_comparison(path_str):
        """Normalize a path string for cross-platform comparison."""
        normalized = path_str.replace("\\", "/")
        if len(normalized) >= 3 and normalized[1] == ':':
            normalized = normalized[3:]
        normalized = normalized.lstrip("/")
        return normalized
    
    library_root_normalized = normalize_path_for_comparison(str(simulated_library_root))
    prefix_normalized = normalize_path_for_comparison(normalized_prefix)
    
    print(f"Library root normalized: '{library_root_normalized}'")
    print(f"Prefix normalized: '{prefix_normalized}'")
    print()
    
    # Simulate the path filtering logic from CLI
    print("=" * 40)
    print("PATH FILTERING SIMULATION")
    print("=" * 40)
    
    pfil_set_normalized = set()
    
    print("Testing each database path:")
    for p_raw in sorted(sample_db_paths):
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
        
        print(f"\nDatabase path: {p_raw}")
        print(f"  Normalized: {p_norm}")
        print(f"  Library parts: {lib_parts}")
        print(f"  Path parts: {path_parts}")
        print(f"  Library found in path: {library_in_database}")
        
        if library_in_database:
            # Reconstruct path using prefix format
            if prefix_normalized and prefix_normalized in p_norm:
                if not p_norm.startswith(prefix_normalized + "/"):
                    prefix_pos = p_norm.find(prefix_normalized)
                    if prefix_pos >= 0:
                        p_norm = prefix_normalized + "/" + p_norm[prefix_pos + len(prefix_normalized):].lstrip("/")
                pfil_set_normalized.add(p_norm)
                print(f"  ✅ INCLUDED: {p_norm}")
            else:
                pfil_set_normalized.add(p_norm)
                print(f"  ✅ INCLUDED: {p_norm}")
        else:
            print(f"  ❌ EXCLUDED: Not within library root")
    
    print()
    print("=" * 40)
    print("LIBRARY SCAN SIMULATION")
    print("=" * 40)
    
    # Simulate library scan - create sample track paths that would be found
    sample_library_tracks = [
        simulated_library_root / "Rock/Led Zeppelin/IV/Black Dog.mp3",
        simulated_library_root / "Rock/Pink Floyd/Dark Side/Money.flac",
        simulated_library_root / "Pop/Michael Jackson/Thriller.mp3", 
        simulated_library_root / "Electronic/Daft Punk/Get Lucky.m4a",
        simulated_library_root / "Jazz/Miles Davis/Kind of Blue.wav",
        # Add a new track that's not in database
        simulated_library_root / "Rock/New Band/New Song.mp3"
    ]
    
    # Convert to ptrk format (what build_crate_plans would create)
    def build_ptrk_simulation(prefix, rel_file):
        parts = [prefix] if prefix else []
        parts.extend(rel_file.parts)
        return "/".join(parts)
    
    all_track_paths = []
    for track_path in sample_library_tracks:
        # Calculate relative path from library root
        rel_path = track_path.relative_to(simulated_library_root)
        ptrk = build_ptrk_simulation(normalized_prefix, rel_path)
        all_track_paths.append(ptrk)
    
    print("Sample scanned library tracks (as ptrk paths):")
    for ptrk in all_track_paths:
        print(f"  {ptrk}")
    print()
    
    # Test new track detection
    print("=" * 40) 
    print("NEW TRACK DETECTION TEST")
    print("=" * 40)
    
    print(f"Scanned tracks: {len(all_track_paths)}")
    print(f"Database tracks (normalized): {len(pfil_set_normalized)}")
    print()
    
    print("Database tracks:")
    for db_track in sorted(pfil_set_normalized):
        print(f"  {db_track}")
    print()
    
    print("Scanned tracks:") 
    for scan_track in all_track_paths:
        print(f"  {scan_track}")
    print()
    
    # Detect new tracks
    new_tracks = []
    for track in all_track_paths:
        if track not in pfil_set_normalized:
            new_tracks.append(track)
    
    print(f"NEW TRACKS DETECTED: {len(new_tracks)}")
    if new_tracks:
        print("New tracks:")
        for new_track in new_tracks:
            print(f"  ❌ {new_track}")
    
    existing_tracks = []
    for track in all_track_paths:
        if track in pfil_set_normalized:
            existing_tracks.append(track)
            
    print(f"EXISTING TRACKS FOUND: {len(existing_tracks)}")
    if existing_tracks:
        print("Existing tracks:")
        for existing_track in existing_tracks:
            print(f"  ✅ {existing_track}")
    
    print()
    print("=" * 40)
    print("DIAGNOSIS")
    print("=" * 40)
    
    total_scanned = len(all_track_paths)
    total_new = len(new_tracks)
    total_existing = len(existing_tracks)
    
    print(f"Total scanned tracks: {total_scanned}")
    print(f"Detected as new: {total_new}")
    print(f"Detected as existing: {total_existing}")
    print(f"New percentage: {(total_new/total_scanned*100):.1f}%")
    
    if total_new == total_scanned:
        print("❌ PROBLEM: ALL TRACKS DETECTED AS NEW!")
        print("   This matches the reported issue.")
        print()
        print("Likely causes:")
        print("1. Path format mismatch between database and scanned paths")
        print("2. Incorrect prefix normalization") 
        print("3. Path filtering excludes too many database tracks")
        
        # Compare sample paths to identify mismatch
        if pfil_set_normalized and all_track_paths:
            db_sample = list(pfil_set_normalized)[0]
            scan_sample = all_track_paths[0]
            print(f"\nSample comparison:")
            print(f"Database format: {db_sample}")
            print(f"Scanned format:  {scan_sample}")
            
            if db_sample != scan_sample and db_sample.split('/')[-1] == scan_sample.split('/')[-1]:
                print("❌ Path formats don't match but refer to same file!")
                print("   This indicates a path normalization issue.")
                
    elif total_new < total_scanned * 0.1:
        print("✅ GOOD: Most tracks correctly detected as existing")
    else:
        print("⚠️  PARTIAL: Some tracks detected as new, needs investigation")

if __name__ == "__main__":
    debug_windows_scenario()
