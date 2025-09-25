"""
Command-line interface for Serato crate synchronization.

This module handles argument parsing and orchestrates the main workflow
for syncing library folders to Serato crates.
"""

import argparse
import sys
import time
from pathlib import Path
from typing import List, Optional

from .database import read_database_v2_pfil_set, normalize_prefix
from .library import scan_library, build_crate_plans, detect_new_tracks, get_library_stats
from .crates import write_crate_file, build_crate_payload, AUDIO_EXTS
from .config import load_config, merge_with_args, validate_config_paths, print_config_example, get_config_file_path


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    ap = argparse.ArgumentParser(
        description="Mirror folder hierarchy into Serato crates and detect new tracks"
    )
    ap.add_argument(
        "--config", 
        type=str,
        help="Path to configuration file (optional). If not specified, uses platform default location."
    )
    ap.add_argument(
        "--db", 
        type=Path,
        help="Path to Serato 'Database V2' file (required unless in config file)"
    )
    ap.add_argument(
        "--library-root", 
        type=Path,
        help="Root folder to mirror as crates/subcrates (required unless in config file)"
    )
    ap.add_argument(
        "--serato-root", 
        type=Path,
        help="Path to _Serato_ folder where Subcrates live (required unless in config file)"
    )
    ap.add_argument(
        "--prefix", 
        default=None,
        help="Leading path segment to prepend in crate 'ptrk' (e.g., 'Music'). If omitted, inferred from DB or library-root name."
    )
    ap.add_argument(
        "--exts", 
        default=",".join(sorted(AUDIO_EXTS)),
        help=f"Comma-separated list of audio extensions (default: {','.join(sorted(AUDIO_EXTS))})"
    )
    ap.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Scan and show what would change; do not write crate files"
    )
    ap.add_argument(
        "--update-db", 
        action="store_true", 
        help="(Experimental) Add new tracks to Database V2 with required fields only (creates backup)"
    )
    ap.add_argument(
        "--show-config-example", 
        action="store_true", 
        help="Show example configuration file and exit"
    )
    return ap


def parse_extensions(exts_str: str) -> set[str]:
    """Parse comma-separated extensions string into a set."""
    return {
        e.lower().strip() if e.startswith(".") else "." + e.lower().strip()
        for e in exts_str.split(",") if e.strip()
    }


def validate_paths(args) -> bool:
    """Validate that required paths exist."""
    if not args.db.exists():
        print(f"[ERROR] Database V2 not found: {args.db}", file=sys.stderr)
        return False
    
    if not args.library_root.exists():
        print(f"[ERROR] Library root not found: {args.library_root}", file=sys.stderr)
        return False
    
    if not args.serato_root.exists():
        print(f"[ERROR] Serato root not found: {args.serato_root}", file=sys.stderr)
        return False
    
    return True


def write_crate_files(crate_plans: List[tuple[Path, List[str]]], dry_run: bool) -> int:
    """Write crate files based on the given plans."""
    if dry_run:
        print("[DRY RUN] No crate files written.")
        return 0
    
    written = 0
    for crate_file, ptrks in crate_plans:
        if not ptrks:
            continue
        
        # Check if crate exists and count existing tracks
        existing_count = 0
        if crate_file.exists():
            from .crates import read_crate_file
            existing_tracks = read_crate_file(crate_file)
            existing_count = len(existing_tracks)
        
        # Only rewrite if changed
        new_bytes = build_crate_payload(ptrks)
        if crate_file.exists():
            with open(crate_file, "rb") as f:
                old_bytes = f.read()
            if old_bytes == new_bytes:
                continue
        
        write_crate_file(crate_file, ptrks)
        written += 1
        
        # Log what happened
        action = "Created" if existing_count == 0 else f"Updated (was {existing_count} tracks)"
        print(f"[INFO] {action}: {crate_file.name} ({len(ptrks)} tracks)")
    
    print(f"[INFO] Crates written/updated: {written}")
    return written


def update_database_v2(db_path: Path, all_tracks: List[str], new_tracks: List[str], library_root: Path) -> bool:
    """
    Update Database V2 with new tracks using minimal required fields only.
    
    Adds only the essential fields (ttyp, pfil, tadd) plus required binary fields 
    that Serato expects for proper database integrity. Does not add metadata fields,
    forcing users to analyze tracks in Serato to populate full metadata.
    
    Args:
        db_path: Path to Database V2 file
        all_tracks: All track paths from the library
        new_tracks: List of genuinely new track paths
        library_root: The root path of the music library
        
    Returns:
        True if successful, False otherwise
    """
    import time
    import struct
    from .tlv_utils import make_chunk
    from .database import read_database_v2_records, write_database_v2_records

    if not new_tracks:
        print("[INFO] No new tracks to add, skipping database update.")
        return True
    
    # Read existing records
    try:
        records = read_database_v2_records(db_path)
        print(f"[INFO] Read {len(records)} existing records from Database V2")
    except Exception as e:
        print(f"[ERROR] Failed to read Database V2: {e}", file=sys.stderr)
        return False
    
    # Create backup
    ts = time.strftime("%Y%m%d-%H%M%S")
    backup = db_path.parent / f"{db_path.name}.bak-{ts}"
    
    try:
        data = db_path.read_bytes()
        backup.write_bytes(data)
        print(f"[INFO] Backup created: {backup}")
    except Exception as e:
        print(f"[ERROR] Failed to create backup: {e}", file=sys.stderr)
        return False
    
    # Create set of current library paths
    current_paths = set(all_tracks)
    
    # Group tracks by directory
    from collections import defaultdict
    current_by_dir = defaultdict(list)
    for p in all_tracks:
        dir_path = p.rsplit('/', 1)[0] if '/' in p else ''
        if dir_path.startswith('Music/'):
            dir_path = dir_path.replace('Music/', 'Music/Music Tracks/', 1)
        current_by_dir[dir_path].append(p)
    
    # Update existing records for renamed tracks
    updated = 0
    for record in records:
        if 'pfil' in record:
            old_path = record['pfil']
            old_dir = old_path.rsplit('/', 1)[0] if '/' in old_path else ''
            
            # Normalize old_dir
            if old_dir.startswith(('E:/', 'C:/', 'D:/')):
                parts = old_dir.split('/')
                try:
                    music_idx = parts.index('Music')
                    old_dir = '/'.join(parts[music_idx:])
                except ValueError:
                    pass
            
            if old_dir in current_by_dir and old_path not in current_paths:
                # This track was renamed, update its path
                new_paths = current_by_dir[old_dir]
                if len(new_paths) == 1:
                    # Simple case: one track in directory
                    record['pfil'] = new_paths[0]
                    updated += 1
                # For multiple tracks, we could try to match by filename similarity, but for now skip
    
    print(f"[INFO] Updated paths for {updated} renamed tracks")
    
    # Add new tracks with ALL required fields that Serato expects
    
    for p in new_tracks:
        # infer type from extension
        ext = Path(p).suffix.lower().lstrip(".") or "mp3"
        
        # Create date added as Unix timestamp string
        current_timestamp = str(int(time.time()))
        current_timestamp_int = int(time.time())
        
        # Get basic file info for defaults
        filename = Path(p).stem  # filename without extension
        
        # Create complete record with ALL fields that working records have
        record = {
            # Required text fields (basic)
            'ttyp': ext,
            'pfil': p,
            'tadd': current_timestamp,
            
            # Required metadata fields (defaults that Serato will update when analyzing)
            'tart': '',  # Artist (empty - Serato will populate)
            'tbit': '128.0kbps',  # Bitrate (default - Serato will correct)
            'tbpm': '120.00',  # BPM (default - Serato will analyze and correct)
            'tcom': '1A - 120.0',  # Comment/Key combo (default)
            'tgen': '',  # Genre (empty - Serato will populate)
            'tgrp': '',  # Grouping (empty)
            'tkey': '1A',  # Musical key (default - Serato will analyze)
            'tlen': '03:30.00',  # Length (default - Serato will correct)
            'tsmp': '44.1k',  # Sample rate (default)
            
            # Required binary fields (UTF-16BE encoded text)
            'tlbl': ''.encode('utf-16be').ljust(16, b'\x00')[:16],  # Label (empty, padded to 16 bytes)
            'tsiz': '0.0MB'.encode('utf-16be').ljust(10, b'\x00')[:10],  # File size (default, padded to 10 bytes)
            'tsng': filename[:10].encode('utf-16be').ljust(20, b'\x00')[:20],  # Song title from filename (max 10 chars = 20 bytes UTF-16BE)
            'ttyr': '2025'.encode('utf-16be'),  # Year (current year)
            
            # Required binary integer fields
            'uadd': struct.pack('>I', current_timestamp_int),  # User added timestamp (4 bytes, big-endian)
            'utme': struct.pack('>I', current_timestamp_int),  # User time (4 bytes, big-endian)
            'utpc': struct.pack('>I', 0),  # User play count (4 bytes, starts at 0)
            'ufsb': struct.pack('>I', 0),  # File size in bytes (4 bytes, default 0)
            'ulbl': struct.pack('>I', 0),  # Label color (4 bytes, default no color)
            
            # Single-byte boolean flags (all start as 0x00 for new tracks)
            'bhrt': b'\x00',  # BPM/heart rate flag
            'bmis': b'\x00',  # Missing/error flag
            'bply': b'\x00',  # Played flag
            'blop': b'\x00',  # Loop flag
            'bitu': b'\x00',  # Beat/time updated flag
            'bovc': b'\x00',  # Overview/waveform flag
            'bcrt': b'\x00',  # Created/imported flag
            'biro': b'\x00',  # Iron/analyzed flag
            'bwlb': b'\x00',  # Waveform low band flag
            'bwll': b'\x00',  # Waveform low-low band flag
            'buns': b'\x00',  # Unsynced flag
            'bbgl': b'\x00',  # Beat grid locked flag
            'bkrk': b'\x00',  # Brick wall/corruption flag
        }

        # Note: These default values ensure Serato can read the database properly.
        # Serato will update all metadata when the user analyzes the tracks.
        
        records.append(record)
    
    # Write back all records
    try:
        write_database_v2_records(db_path, records)
        print(f"[INFO] Wrote {len(records)} records to Database V2")
        if new_tracks:
            print(f"[INFO] Added {len(new_tracks)} new tracks")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to write to Database V2: {e}", file=sys.stderr)
        return False


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args(argv)

    # Handle config file example display
    if args.show_config_example:
        print_config_example()
        return 0

    # Load config file if specified
    config = {}
    if args.config:
        try:
            config = load_config(args.config)
            print(f"[INFO] Loaded config from: {args.config}")
        except FileNotFoundError:
            print(f"[ERROR] Config file not found: {args.config}", file=sys.stderr)
            return 2
        except Exception as e:
            print(f"[ERROR] Failed to load config file: {e}", file=sys.stderr)
            return 2
    else:
        # Try to load default config file
        try:
            config = load_config()
            if config:
                print(f"[INFO] Loaded default config from: {get_config_file_path()}")
        except Exception:
            # No default config file, that's okay
            pass

    # Merge config with command line arguments (args take precedence)
    merged_args = {
        'db': args.db,
        'library_root': args.library_root,
        'serato_root': args.serato_root,
        'prefix': args.prefix,
        'exts': args.exts,
        'dry_run': args.dry_run,
        'update_db': args.update_db
    }

    # Fill in missing values from config
    for key, value in config.items():
        if key in merged_args and merged_args[key] is None:
            if key in ['library_root', 'serato_root', 'db']:
                merged_args[key] = Path(value)
            else:
                merged_args[key] = value

    # Validate required arguments
    required_args = ['db', 'library_root', 'serato_root']
    missing_args = [arg for arg in required_args if merged_args[arg] is None]
    if missing_args:
        print(f"[ERROR] Missing required arguments: {', '.join(missing_args)}", file=sys.stderr)
        print("[INFO] These can be provided via command line or config file", file=sys.stderr)
        return 2

    # Create a namespace object from merged args
    class Args:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    merged_args_obj = Args(**merged_args)

    # Validate paths
    if not validate_paths(merged_args_obj):
        return 2

    # Parse extensions
    allowed_exts = parse_extensions(merged_args_obj.exts)

    # Parse Database V2 for existing pfil paths and infer prefix
    pfil_set_raw, inferred, total = read_database_v2_pfil_set(merged_args_obj.db)
    prefix = normalize_prefix(merged_args_obj.prefix, inferred, merged_args_obj.library_root)
    print(f"[INFO] Database tracks: {total:,}; inferred prefix: '{prefix}'")

    # Normalize the database paths to match the format of scanned paths
    pfil_set_normalized = set()
    for p_raw in pfil_set_raw:
        p_norm = p_raw.replace("\\", "/")
        if f"{prefix}/" in p_norm:
            # Strip everything before the prefix to align paths
            p_norm = f"{prefix}/" + p_norm.split(f"{prefix}/", 1)[1]
        pfil_set_normalized.add(p_norm)

    # Scan library
    lib_map = scan_library(merged_args_obj.library_root, allowed_exts)
    if not lib_map:
        print(f"[WARN] No audio files found under: {merged_args_obj.library_root}")
        return 0

    # Get library statistics
    num_dirs, num_files = get_library_stats(lib_map)
    print(f"[INFO] Library scan: {num_dirs} folders; {num_files} audio files")

    # Build crate plans and detect new tracks
    crate_plans = build_crate_plans(lib_map, prefix, merged_args_obj.serato_root)
    
    # Count existing crates
    existing_crates = 0
    total_existing_tracks = 0
    for crate_file, _ in crate_plans:
        if crate_file.exists():
            from .crates import read_crate_file
            existing_tracks = read_crate_file(crate_file)
            if existing_tracks:
                existing_crates += 1
                total_existing_tracks += len(existing_tracks)
    
    if existing_crates > 0:
        print(f"[INFO] Found {existing_crates} existing crates with {total_existing_tracks} total tracks")
    
    all_track_paths = []
    for _, ptrks in crate_plans:
        all_track_paths.extend(ptrks)
    
    new_tracks = detect_new_tracks(all_track_paths, pfil_set_normalized)
    print(f"[INFO] New (not in DB): {len(new_tracks)} tracks")

    # Write crate files if not dry-run
    write_crate_files(crate_plans, merged_args_obj.dry_run)

    # Update database if requested
    if merged_args_obj.update_db and not merged_args_obj.dry_run:
        if not update_database_v2(merged_args_obj.db, all_track_paths, new_tracks, merged_args_obj.library_root):
            return 4

    return 0


if __name__ == "__main__":
    sys.exit(main())