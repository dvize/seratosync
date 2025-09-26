#!/usr/bin/env python3
"""
Test the improved cross-platform prefix normalization.
"""

import sys
from pathlib import Path
import platform

# Add the current directory to Python path
sys.path.insert(0, '.')

from seratosync.database import normalize_prefix

def test_cross_platform_prefix():
    """Test the improved prefix normalization with various scenarios."""
    
    print(f"=== CROSS-PLATFORM PREFIX NORMALIZATION TEST ===")
    print(f"Current platform: {platform.system()}\n")
    
    # Test scenarios that commonly occur
    test_cases = [
        # Windows scenarios
        {
            "desc": "Windows - Basic case",
            "library_root": Path("E:/Music/Music Tracks"),
            "inferred": "E:/Music/Music Tracks",
            "expected": "Music/Music Tracks"
        },
        {
            "desc": "Windows - Inferred is parent",
            "library_root": Path("E:/Music/Music Tracks"),  
            "inferred": "E:/Music",
            "expected": "Music"
        },
        {
            "desc": "Windows - Inferred has more specificity",
            "library_root": Path("E:/Music"),
            "inferred": "E:/Music/Music Tracks",
            "expected": "Music/Music Tracks"
        },
        # macOS scenarios
        {
            "desc": "macOS - Basic case",
            "library_root": Path("/Users/dvize/Music/Music Tracks"),
            "inferred": "Users/dvize/Music/Music Tracks",
            "expected": "Users/dvize/Music/Music Tracks"
        },
        {
            "desc": "macOS - Inferred is parent",
            "library_root": Path("/Users/dvize/Music/Music Tracks"),
            "inferred": "Users/dvize/Music",
            "expected": "Users/dvize/Music"
        },
        # Mixed case scenarios
        {
            "desc": "Case sensitivity test",
            "library_root": Path("E:/music/Music Tracks"),
            "inferred": "E:/Music/Music Tracks",
            "expected": "music/Music Tracks"  # Should preserve library_root casing
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['desc']}")
        print(f"  Library root: {test['library_root']}")
        print(f"  Inferred:     {test['inferred']}")
        
        result = normalize_prefix(None, test['inferred'], test['library_root'])
        
        print(f"  Result:       {result}")
        print(f"  Expected:     {test['expected']}")
        
        if result == test['expected']:
            print(f"  Status:       ✅ PASS")
        else:
            print(f"  Status:       ❌ FAIL")
        print()

def test_path_normalization():
    """Test the path normalization helper function."""
    print("=== PATH NORMALIZATION TEST ===\n")
    
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
    
    test_paths = [
        "E:/Music/Music Tracks/Rock/song.mp3",
        "C:\\Users\\dvize\\Music\\song.mp3", 
        "/Users/dvize/Music/Music Tracks/song.mp3",
        "Users/dvize/Music/song.mp3",  # Already normalized
        "E:\\Music\\Dance\\song.mp3"
    ]
    
    for path in test_paths:
        normalized = normalize_path_for_comparison(path)
        print(f"Original:   {path}")
        print(f"Normalized: {normalized}")
        print()

if __name__ == "__main__":
    test_cross_platform_prefix()
    test_path_normalization()
