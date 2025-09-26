#!/usr/bin/env python3
"""
Test the path normalization issue and create a fix.
"""

# Test current normalization logic
def test_current_normalization():
    # Database paths (what we have)
    db_paths = [
        "Users/dvize/Music/Music Tracks/By Genre/A-F/Funk/80s/The Fatback Band - I Found Lovin (Intro Clean).mp3",
        "Users/dvize/Music/Music Tracks/By Genre/A-F/Future House/No Scrubs (Marat Leon Remix) (Intro Clean).mp3"
    ]
    
    # Current inferred prefix
    prefix = "Users/dvize/Music"
    
    print("=== Current Normalization Logic ===")
    print(f"Prefix: {prefix}")
    
    pfil_set_normalized = set()
    for p_raw in db_paths:
        p_norm = p_raw.replace("\\", "/")
        if f"{prefix}/" in p_norm:
            # Strip everything before the prefix to align paths - PROBLEM IS HERE
            p_norm = f"{prefix}/" + p_norm.split(f"{prefix}/", 1)[1]
        pfil_set_normalized.add(p_norm)
        print(f"Raw: {p_raw}")
        print(f"Normalized: {p_norm}")
        print()
    
    # Now test what library paths would be constructed as
    print("=== Library Path Construction ===")
    library_relative_paths = [
        "By Genre/A-F/Funk/80s/The Fatback Band - I Found Lovin (Intro Clean).mp3",
        "By Genre/A-F/Future House/No Scrubs (Marat Leon Remix) (Intro Clean).mp3"
    ]
    
    constructed_paths = []
    for rel_path in library_relative_paths:
        constructed = f"{prefix}/{rel_path}"
        constructed_paths.append(constructed)
        print(f"Relative: {rel_path}")
        print(f"Constructed: {constructed}")
        print()
    
    # Check matches
    matches = set(constructed_paths) & pfil_set_normalized
    print(f"Matches: {len(matches)}")
    for match in matches:
        print(f"  - {match}")

def test_fixed_normalization():
    print("\n=== FIXED Normalization Logic ===")
    
    # Database paths (what we have)
    db_paths = [
        "Users/dvize/Music/Music Tracks/By Genre/A-F/Funk/80s/The Fatback Band - I Found Lovin (Intro Clean).mp3",
        "Users/dvize/Music/Music Tracks/By Genre/A-F/Future House/No Scrubs (Marat Leon Remix) (Intro Clean).mp3"
    ]
    
    # The prefix should match what's actually in the DB
    # Instead of inferring "Users/dvize/Music", we should infer "Users/dvize/Music/Music Tracks"
    correct_prefix = "Users/dvize/Music/Music Tracks"
    
    print(f"Fixed Prefix: {correct_prefix}")
    
    # With the correct prefix, no normalization should be needed
    pfil_set_normalized = set()
    for p_raw in db_paths:
        p_norm = p_raw.replace("\\", "/")
        pfil_set_normalized.add(p_norm)  # No normalization needed!
        print(f"Raw: {p_raw}")
        print(f"Normalized: {p_norm}")
        print()
    
    # Now test what library paths would be constructed as
    print("=== Library Path Construction with Fixed Prefix ===")
    library_relative_paths = [
        "By Genre/A-F/Funk/80s/The Fatback Band - I Found Lovin (Intro Clean).mp3",
        "By Genre/A-F/Future House/No Scrubs (Marat Leon Remix) (Intro Clean).mp3"
    ]
    
    constructed_paths = []
    for rel_path in library_relative_paths:
        constructed = f"{correct_prefix}/{rel_path}"
        constructed_paths.append(constructed)
        print(f"Relative: {rel_path}")
        print(f"Constructed: {constructed}")
        print()
    
    # Check matches
    matches = set(constructed_paths) & pfil_set_normalized
    print(f"Matches: {len(matches)}")
    for match in matches:
        print(f"  - {match}")

if __name__ == "__main__":
    test_current_normalization()
    test_fixed_normalization()
