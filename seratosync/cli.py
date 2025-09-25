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
        help="(Experimental) Also append new tracks to Database V2 (makes a backup first)"
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
        
        # Only rewrite if changed
        new_bytes = build_crate_payload(ptrks)
        if crate_file.exists():
            with open(crate_file, "rb") as f:
                old_bytes = f.read()
            if old_bytes == new_bytes:
                continue
        
        write_crate_file(crate_file, ptrks)
        written += 1
    
    print(f"[INFO] Crates written/updated: {written}")
    return written


def update_database_v2(db_path: Path, new_tracks: List[str]) -> bool:
    """
    Experimentally update Database V2 with new tracks.
    
    Args:
        db_path: Path to Database V2 file
        new_tracks: List of new track paths to add
        
    Returns:
        True if successful, False otherwise
    """
    import time
    from .tlv_utils import make_chunk
    
    if not new_tracks:
        return True
    
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

    # Build append buffer
    append_buf = bytearray()
    for p in new_tracks:
        # infer type from extension
        ext = Path(p).suffix.lower().lstrip(".") or "mp3"
        inner = make_chunk("ttyp", p.encode("utf-16-be")[:4]) + \
                make_chunk("pfil", p.encode("utf-16-be"))
        append_buf += make_chunk("otrk", inner)
    
    try:
        with open(db_path, "ab") as f:
            f.write(append_buf)
        print(f"[INFO] Appended {len(new_tracks)} new 'otrk' records to Database V2 (EXPERIMENTAL).")
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
    pfil_set, inferred, total = read_database_v2_pfil_set(merged_args_obj.db)
    prefix = normalize_prefix(merged_args_obj.prefix, inferred, merged_args_obj.library_root)
    print(f"[INFO] Database tracks: {total:,}; inferred prefix: '{prefix}'")

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
    all_track_paths = []
    for _, ptrks in crate_plans:
        all_track_paths.extend(ptrks)
    
    new_tracks = detect_new_tracks(all_track_paths, pfil_set)
    print(f"[INFO] New (not in DB): {len(new_tracks)} tracks")

    # Write crate files if not dry-run
    write_crate_files(crate_plans, merged_args_obj.dry_run)

    # Update database if requested
    if merged_args_obj.update_db and not merged_args_obj.dry_run:
        if not update_database_v2(merged_args_obj.db, new_tracks):
            return 4

    return 0


if __name__ == "__main__":
    sys.exit(main())
