#!/usr/bin/env python3
import serato_parser_fixed as parser

print("Analyzing what data fields are available in database tracks...")
result = parser.parse_serato_database(r'E:\_Serato_\database V2')
tracks = result['tracks']

# Analyze first few tracks to see what data we're preserving vs losing
print(f"Total tracks: {len(tracks)}")

# Collect all unique field names
all_fields = set()
for track in tracks[:100]:  # Check first 100 tracks
    all_fields.update(track.keys())

print(f"\nAll available fields in database tracks:")
for field in sorted(all_fields):
    # Count how many tracks have this field
    count = sum(1 for track in tracks[:100] if field in track and track[field])
    print(f"  {field}: {count}/100 tracks")

print(f"\nFirst track full data:")
if tracks:
    first_track = tracks[0]
    for key, value in first_track.items():
        if key == '__raw_chunk':
            print(f"  {key}: <binary data {len(value)} bytes>")
        elif isinstance(value, str) and len(value) > 100:
            print(f"  {key}: '{value[:50]}...{value[-50:]}'")
        else:
            print(f"  {key}: '{value}'")
