#!/usr/bin/env python3

"""
Analyze the actual chunk size distribution in the database.
"""

import sys
sys.path.append('.')

from serato_parser_fixed import parse_serato_database

def analyze_chunk_sizes():
    """Analyze the distribution of chunk sizes to identify the issue."""
    print("=== CHUNK SIZE ANALYSIS ===")
    
    # Load the database
    result = parse_serato_database("E:/_Serato_/database V2")
    
    if not result or 'tracks' not in result:
        print("Failed to parse database")
        return
        
    tracks = result['tracks']
    print(f"Loaded {len(tracks)} tracks")
    
    # Analyze chunk sizes
    size_distribution = {}
    total_raw_size = 0
    tracks_with_chunks = 0
    
    for track in tracks:
        if '__raw_chunk' in track:
            chunk_size = len(track['__raw_chunk'])
            total_raw_size += chunk_size
            tracks_with_chunks += 1
            
            # Group sizes for distribution analysis
            size_bucket = (chunk_size // 100) * 100  # Round to nearest 100
            size_distribution[size_bucket] = size_distribution.get(size_bucket, 0) + 1
    
    print(f"Tracks with raw chunks: {tracks_with_chunks}")
    print(f"Total raw chunk data: {total_raw_size:,} bytes")
    print(f"Average chunk size: {total_raw_size // tracks_with_chunks:.0f} bytes")
    
    print(f"\nChunk size distribution:")
    for size_bucket in sorted(size_distribution.keys()):
        count = size_distribution[size_bucket]
        print(f"  {size_bucket:4d}-{size_bucket+99:4d} bytes: {count:5d} tracks")
    
    # Check if all chunks are the same size (indicates a problem)
    unique_sizes = set()
    sample_tracks = []
    for track in tracks[:10]:
        if '__raw_chunk' in track:
            size = len(track['__raw_chunk'])
            unique_sizes.add(size)
            sample_tracks.append((track.get('pfil', 'NO PATH'), size))
    
    print(f"\nFirst 10 track chunk sizes:")
    for path, size in sample_tracks:
        print(f"  {size:4d} bytes: {path}")
    
    print(f"\nUnique sizes in first 10 tracks: {sorted(unique_sizes)}")
    
    if len(unique_sizes) == 1:
        print("🚨 PROBLEM IDENTIFIED: All chunks are the same size!")
        print("This suggests the parser is not extracting full chunk data.")
        print("Real Serato tracks should have varying sizes based on analysis data.")
    else:
        print("✅ Chunk sizes vary, which is expected for real track data.")

if __name__ == "__main__":
    analyze_chunk_sizes()
