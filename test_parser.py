#!/usr/bin/env python3
import serato_parser_fixed as parser

print("Testing the improved parser...")
result = parser.parse_serato_database(r'E:\_Serato_\database V2')
tracks = result['tracks']

print(f"Total tracks found: {len(tracks)}")

# Show first few tracks
print("\nFirst 5 tracks:")
for i, track in enumerate(tracks[:5]):
    artist = track.get('tart', 'N/A')
    title = track.get('tsng', 'N/A') 
    filepath = track.get('pfil', 'N/A')
    print(f"{i+1}. Artist: '{artist}' - Title: '{title}'")
    if len(filepath) > 80:
        print(f"   File: {filepath[:40]}...{filepath[-40:]}")
    else:
        print(f"   File: {filepath}")

print(f"\nTotal valid tracks recovered: {len(tracks)}")
