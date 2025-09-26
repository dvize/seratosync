#!/usr/bin/env python3
"""
Debug script to simulate the prefix detection issue on macOS
Tests the reported scenario where all tracks were incorrectly detected as "new"
"""
import platform

def normalize_path_for_comparison(path):
    """Cross-platform path normalization for comparison"""
    if not path:
        return ""
    
    # Convert to string if Path object
    path_str = str(path)
    
    # Normalize separators to forward slash
    normalized = path_str.replace('\\', '/')
    
    # Handle Windows drive letters - remove them for comparison
    if ':' in normalized and '/' not in normalized[:3]:
        # This is likely a Windows drive letter (e.g., "C:/path")
        if len(normalized) >= 2 and normalized[1] == ':':
            normalized = normalized[2:]  # Remove "C:"
    elif normalized.startswith('/'):
        # Unix-style absolute path, remove leading slash for consistency
        normalized = normalized[1:]
    
    # Remove leading slash if present
    while normalized.startswith('/'):
        normalized = normalized[1:]
    
    # Case-insensitive comparison
    normalized = normalized.lower()
    
    return normalized

def is_path_within_library(db_path, library_root_parts):
    """Check if a database path is within the library root"""
    path_parts = normalize_path_for_comparison(db_path).split('/')
    
    # Check if library root parts appear at the beginning of path parts
    if len(path_parts) < len(library_root_parts):
        return False
    
    for i, lib_part in enumerate(library_root_parts):
        if i >= len(path_parts) or path_parts[i] != lib_part:
            return False
    
    return True

print("============================================================")
print("MACOS SCENARIO DEBUG")
print("============================================================")
print(f"Platform: {platform.system()}")
print()

# Simulate macOS scenario based on the Windows issue
print("Testing with macOS equivalent scenario:")
print("- Inferred prefix: '/Users/dvize/Music/Music Tracks'")
print("- 30,396 tracks in database")
print("- 1,251 existing crates with 30,396 total tracks")
print("- Previous issue: All tracks incorrectly detected as 'new'")
print()

# Sample database paths (macOS style)
sample_db_paths = [
    "/Users/dvize/Music/Classical/Bach/Brandenburg.flac",
    "/Users/dvize/Music/Dance/Calvin Harris/Feel So Close.mp3",
    "/Users/dvize/Music/Hip Hop/Eminem/Lose Yourself.mp3",
    "/Users/dvize/Music/Music Tracks/Electronic/Daft Punk/Get Lucky.m4a",
    "/Users/dvize/Music/Music Tracks/Jazz/Miles Davis/Kind of Blue.wav",
    "/Users/dvize/Music/Music Tracks/Pop/Michael Jackson/Thriller.mp3",
    "/Users/dvize/Music/Music Tracks/Rock/Led Zeppelin/IV/Black Dog.mp3",
    "/Users/dvize/Music/Music Tracks/Rock/Pink Floyd/Dark Side/Money.flac",
]

print("Sample database paths:")
for path in sample_db_paths:
    print(f"  {path}")

print()
print("=" * 40)
print("PREFIX NORMALIZATION TEST")
print("=" * 40)

# Test the library root and prefix detection
library_root = "/Users/dvize/Music/Music Tracks"
inferred_prefix = "/Users/dvize/Music/Music Tracks"

print(f"Library root: {library_root}")
print(f"Inferred prefix: '{inferred_prefix}'")

# Normalize both
normalized_prefix = normalize_path_for_comparison(inferred_prefix)
normalized_library = normalize_path_for_comparison(library_root)

print(f"Normalized prefix: '{normalized_prefix}'")
print()
print(f"Library root normalized: '{normalized_library}'")
print(f"Prefix normalized: '{normalized_prefix}'")
print()

print("=" * 40)
print("PATH FILTERING SIMULATION") 
print("=" * 40)

# Simulate the filtering process
library_parts = normalized_library.split('/')
print(f"Testing each database path:")
print()

filtered_paths = []
for db_path in sample_db_paths:
    normalized_db = normalize_path_for_comparison(db_path)
    path_parts = normalized_db.split('/')
    
    print(f"Database path: {db_path}")
    print(f"  Normalized: {normalized_db}")
    print(f"  Library parts: {library_parts}")
    print(f"  Path parts: {path_parts}")
    
    # Check if path is within library
    within_library = is_path_within_library(db_path, library_parts)
    
    print(f"  Library found in path: {within_library}")
    
    if within_library:
        filtered_paths.append(normalized_db)
        print(f"  ✅ INCLUDED: {normalized_db}")
    else:
        print(f"  ❌ EXCLUDED: Not within library root")
    print()

print("=" * 40)
print("LIBRARY SCAN SIMULATION")
print("=" * 40)

# Simulate what a library scan would find (as normalized paths)
scanned_tracks = [
    "users/dvize/music/music tracks/rock/led zeppelin/iv/black dog.mp3",
    "users/dvize/music/music tracks/rock/pink floyd/dark side/money.flac", 
    "users/dvize/music/music tracks/pop/michael jackson/thriller.mp3",
    "users/dvize/music/music tracks/electronic/daft punk/get lucky.m4a",
    "users/dvize/music/music tracks/jazz/miles davis/kind of blue.wav",
    "users/dvize/music/music tracks/rock/new band/new song.mp3",  # This would be a NEW track
]

print("Sample scanned library tracks (as ptrk paths):")
for track in scanned_tracks:
    print(f"  {track}")

print()
print("=" * 40)
print("NEW TRACK DETECTION TEST")
print("=" * 40)

print(f"Scanned tracks: {len(scanned_tracks)}")
print(f"Database tracks (normalized): {len(filtered_paths)}")
print()

print("Database tracks:")
for track in filtered_paths:
    print(f"  {track}")

print()
print("Scanned tracks:")
for track in scanned_tracks:
    print(f"  {track}")

# Find new tracks
existing_tracks = set()
new_tracks = set()

for scanned in scanned_tracks:
    found_in_db = False
    for db_track in filtered_paths:
        if scanned == db_track:
            existing_tracks.add(scanned)
            found_in_db = True
            break
    
    if not found_in_db:
        new_tracks.add(scanned)

print()
print(f"NEW TRACKS DETECTED: {len(new_tracks)}")
if new_tracks:
    print("New tracks:")
    for track in new_tracks:
        print(f"  ❌ {track}")

print(f"EXISTING TRACKS FOUND: {len(existing_tracks)}")
if existing_tracks:
    print("Existing tracks:")
    for track in existing_tracks:
        print(f"  ✅ {track}")

print()
print("=" * 40)
print("DIAGNOSIS")
print("=" * 40)

total_tracks = len(scanned_tracks)
new_count = len(new_tracks)
existing_count = len(existing_tracks)

print(f"Total scanned tracks: {total_tracks}")
print(f"Detected as new: {new_count}")
print(f"Detected as existing: {existing_count}")

if total_tracks > 0:
    new_percentage = (new_count / total_tracks) * 100
    print(f"New percentage: {new_percentage:.1f}%")
    
    if new_count == total_tracks:
        print("❌ PROBLEM: All tracks detected as new")
    elif new_count == 0:
        print("✅ GOOD: No new tracks detected (all existing)")
    else:
        print("⚠️  PARTIAL: Some tracks detected as new, needs investigation")
else:
    print("❌ ERROR: No tracks scanned")
