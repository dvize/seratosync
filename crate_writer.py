import os
import shutil
import struct
import configparser
from datetime import datetime
import mutagen
import unicodedata
from urllib.parse import urlparse, unquote

from serato_parser_fixed import parse_serato_database
from folder_scanner import scan_music_folder

# --- Helper Functions ---

def _pad_len(n: int) -> int:
    """Return number of padding bytes needed to align to 4-byte boundary."""
    return (-n) & 3

def _write_chunk(f, tag_ascii: str, payload: bytes):
    """Writes a chunk with header, payload, and file-level padding."""
    header = tag_ascii.encode('ascii') + struct.pack('>I', len(payload))
    f.write(header + payload)
    pad = _pad_len(len(payload))
    if pad:
        f.write(b"\x00" * pad)

def _pack_subchunk(tag_ascii: str, payload: bytes) -> bytes:
    """Packs a subchunk for inclusion within a parent chunk's payload."""
    header = tag_ascii.encode('ascii') + struct.pack('>I', len(payload))
    pad = b"\x00" * _pad_len(len(payload))
    return header + payload + pad

def _to_nfc(s: str) -> str:
    """Normalize Unicode string to NFC form for consistency."""
    try:
        return unicodedata.normalize('NFC', s)
    except Exception:
        return s

def _norm_for_compare(path_str: str) -> str:
    """Normalize a path string for reliable comparison."""
    p = os.path.normpath(path_str)
    p = _to_nfc(p)
    return os.path.normcase(p)

def _serato_pfil_to_local_path(pfil_value: str, music_folder: str) -> str:
    """Converts a Serato pfil path string to a local file system path."""
    s = pfil_value.replace('\x00', '').strip()
    
    # Handle file:// URLs
    if s.lower().startswith('file://'):
        try:
            path = unquote(urlparse(s).path)
            # On Windows, file:// URLs might have /C:/ format, fix this
            if os.name == 'nt' and path.startswith('/') and len(path) > 3 and path[2] == ':':
                path = path[1:]  # Remove leading slash for Windows drive letters
            return path
        except Exception:
            pass
    
    # Handle absolute paths
    if s.startswith('/') or (os.name == 'nt' and len(s) > 1 and s[1] == ':'):
        return s
    
    # Handle relative paths - most common case for cross-platform databases
    # Serato often stores paths relative to a base music directory
    if music_folder and not os.path.isabs(s):
        # Try to map relative path to the current music folder
        # Common patterns: "Music/Music Tracks/..." -> "{music_folder}/..."
        
        # If path starts with "Music/Music Tracks/" and our folder ends with "Music Tracks"
        music_tracks_prefix = "Music/Music Tracks/"
        if s.startswith(music_tracks_prefix):
            relative_part = s[len(music_tracks_prefix):]
            candidate_path = os.path.join(music_folder, relative_part)
            return candidate_path
        
        # If path starts with "Music Tracks/"
        music_tracks_prefix2 = "Music Tracks/"  
        if s.startswith(music_tracks_prefix2):
            relative_part = s[len(music_tracks_prefix2):]
            candidate_path = os.path.join(music_folder, relative_part)
            return candidate_path
            
        # Generic fallback - assume it's relative to music folder
        candidate_path = os.path.join(music_folder, s)
        return candidate_path
    
    # Handle old-style Mac paths with colons (rare now)
    if ':' in s and '/' not in s and '\\' not in s:
        parts = s.split(':')
        if len(parts) >= 2:
            if os.name == 'nt':
                # Convert to Windows path format - this is a guess
                return f"/{parts[0]}/{'/'.join(parts[1:])}"
            else:
                return f"/Volumes/{parts[0]}/{'/'.join(parts[1:])}"
    
    return s

# --- Track and Crate Creation ---

def create_track_chunk_payload(file_path):
    """Creates the inner payload for an 'otrk' chunk."""
    try:
        audio = mutagen.File(file_path, easy=False)
        info = audio.info if audio else None
    except Exception as e:
        print(f"Warning: Could not read metadata for {os.path.basename(file_path)}: {e}")
        audio = None
        info = None

    # Mandatory file path
    payload = _pack_subchunk('pfil', file_path.encode('utf-16-be'))

    if audio and audio.tags:
        # Standard metadata
        tags_map = {'tsng': 'TIT2', 'tart': 'TPE1', 'talb': 'TALB', 'tgen': 'TCON', 'tkey': 'TKEY', 'tbpm': 'TBPM'}
        for p_tag, m_tag in tags_map.items():
            value = audio.tags.get(m_tag)
            if value and value.text:
                payload += _pack_subchunk(p_tag, value.text[0].encode('utf-16-be'))

        # Serato-specific GEOB data
        geob_map = {'ovrv': 'GEOB:Serato Overview', 'grid': 'GEOB:Serato BeatGrid', 'mark': 'GEOB:Serato Markers2', 'adat': 'GEOB:Serato Analysis'}
        for p_tag, desc in geob_map.items():
            geob = audio.tags.get(desc)
            if geob and getattr(geob, 'data', None):
                payload += _pack_subchunk(p_tag, geob.data)

    if info:
        # Track length and bitrate
        if hasattr(info, 'length'):
            len_str = f"{int(info.length // 60)}:{info.length % 60:05.2f}"
            payload += _pack_subchunk('tlen', len_str.encode('utf-16-be'))
        if hasattr(info, 'bitrate') and info.bitrate:
            br_str = str(info.bitrate // 1000)
            payload += _pack_subchunk('tbit', br_str.encode('utf-16-be'))

    # File type
    ext = os.path.splitext(file_path)[1].lower().strip('.')
    payload += _pack_subchunk('ttyp', ext.encode('utf-16-be'))
    
    return payload

def create_crate_file(crate_name, track_paths, serato_subcrates_path):
    """Creates a .crate file for a given list of tracks."""
    crate_path = os.path.join(serato_subcrates_path, f"{crate_name}.crate")
    print(f"Creating crate: {os.path.basename(crate_path)}")

    try:
        with open(crate_path, 'wb') as f:
            # Crate header
            _write_chunk(f, 'vrsn', '1.0/Serato ScratchLive Crate'.encode('utf-16-be'))
            
            # Sorting columns
            sort_payload = b''
            columns = [b'tvcn', b'tvcA', b'tvcB', b'tvcC', b'tvcG', b'tvcH', b'tvcI', b'tvcL', b'tvcM', b'tvcN', b'tvcO']
            for col_tag in columns:
                sort_payload += _pack_subchunk(col_tag, b'\x00\x00\x00\x01' if col_tag == b'tvcA' else b'\x00\x00\x00\x00')
            _write_chunk(f, 'osrt', sort_payload)

            # Add each track path to the crate
            for track_path in track_paths:
                ptfs_payload = _pack_subchunk('pfil', track_path.encode('utf-16-be'))
                _write_chunk(f, 'ptfs', ptfs_payload)
                
    except Exception as e:
        print(f"Error writing crate file {crate_path}: {e}")

# --- Main Sync Logic ---

def main():
    config = configparser.ConfigParser()
    config.read('config.ini')
    music_folder = config.get('paths', 'music_folder')
    serato_db_path = config.get('paths', 'serato_database')
    exclude_missing_files = config.getboolean('options', 'exclude_missing_files', fallback=True)
    serato_folder = os.path.dirname(serato_db_path)
    serato_subcrates_path = os.path.join(serato_folder, 'Subcrates')

    # Ensure Subcrates directory exists
    os.makedirs(serato_subcrates_path, exist_ok=True)

    # Backup existing database
    backup_path = serato_db_path + f".bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        print(f"Backing up database to {backup_path}...")
        shutil.copy2(serato_db_path, backup_path)
    except FileNotFoundError:
        print("No existing database to back up. A new one will be created.")
    except Exception as e:
        print(f"Error creating backup: {e}. Aborting.")
        return

    # --- Analysis Phase ---
    print("\n--- Analyzing Libraries ---")
    local_music_map = scan_music_folder(music_folder)
    local_tracks_paths = {file for files in local_music_map.values() for file in files}
    local_norm_map = {_norm_for_compare(p): p for p in local_tracks_paths}
    
    serato_tracks_map = {}
    if os.path.exists(serato_db_path):
        db_tree = parse_serato_database(serato_db_path)
        if db_tree and 'tracks' in db_tree:
            for track in db_tree['tracks']:
                pfil_value = track.get('pfil')
                if pfil_value and '__raw_chunk' in track:
                    local_path = _serato_pfil_to_local_path(pfil_value, music_folder)
                    norm_path = _norm_for_compare(local_path)
                    serato_tracks_map[norm_path] = track['__raw_chunk']
    
    print(f"Found {len(local_tracks_paths)} tracks in local music folder.")
    print(f"Found {len(serato_tracks_map)} tracks in Serato database.")

    # --- Sync Calculation ---
    valid_tracks_to_write = []
    serato_norm_paths = set(serato_tracks_map.keys())
    local_norm_paths = set(local_norm_map.keys())
    
    # Debug: Show path matching statistics
    intersection = serato_norm_paths.intersection(local_norm_paths)
    print(f"\nPATH MATCHING DEBUG:")
    print(f"  Serato normalized paths: {len(serato_norm_paths)}")
    print(f"  Local normalized paths: {len(local_norm_paths)}")
    print(f"  Intersection (matches): {len(intersection)}")
    print(f"  Serato-only paths: {len(serato_norm_paths - local_norm_paths)}")
    print(f"  Local-only paths: {len(local_norm_paths - serato_norm_paths)}")
    
    # Debug: Show sample paths to understand normalization differences
    print(f"\nSAMPLE PATH COMPARISON:")
    serato_samples = list(serato_norm_paths)[:3]
    local_samples = list(local_norm_paths)[:3]
    print("Sample Serato normalized paths:")
    for i, path in enumerate(serato_samples):
        print(f"  {i+1}: {path}")
    print("Sample Local normalized paths:")  
    for i, path in enumerate(local_samples):
        print(f"  {i+1}: {path}")
        
    # Check if any paths that should match are missing
    serato_only_samples = list(serato_norm_paths - local_norm_paths)[:3]
    local_only_samples = list(local_norm_paths - serato_norm_paths)[:3]
    print("Sample Serato-only paths:")
    for i, path in enumerate(serato_only_samples):
        print(f"  {i+1}: {path}")
    print("Sample Local-only paths:")
    for i, path in enumerate(local_only_samples):
        print(f"  {i+1}: {path}")
        
    # Debug: Check for potential near-matches (truncated extensions)
    print(f"\nCHECKING FOR TRUNCATION ISSUES:")
    truncation_matches = 0
    for serato_path in list(serato_only_samples):
        for local_path in list(local_only_samples):
            if local_path.startswith(serato_path) and local_path.endswith('.mp3'):
                print(f"  TRUNCATION: '{serato_path}' should be '{local_path}'")
                truncation_matches += 1
                break
    print(f"  Found {truncation_matches} potential truncation matches in sample")

    if exclude_missing_files:
        # Only keep database tracks that have corresponding local files
        for norm_path in serato_norm_paths:
            if norm_path in local_norm_paths:
                valid_tracks_to_write.append(serato_tracks_map[norm_path])
        
        # Identify new tracks (only add tracks that aren't already in database)
        new_norm_paths = local_norm_paths - serato_norm_paths
        new_track_paths = {local_norm_map[p] for p in new_norm_paths}
        
        print(f"\nFiltering database: Keeping {len(valid_tracks_to_write)} tracks with local files (excluding {len(serato_norm_paths) - len(valid_tracks_to_write)} missing files).")
        print(f"Adding {len(new_track_paths)} new tracks from disk.")
    else:
        # Keep ALL existing tracks from database (preserve analysis data!)
        for norm_path in serato_norm_paths:
            valid_tracks_to_write.append(serato_tracks_map[norm_path])

        # Identify new tracks (only add tracks that aren't already in database)
        new_norm_paths = local_norm_paths - serato_norm_paths
        new_track_paths = {local_norm_map[p] for p in new_norm_paths}

        print(f"\nPreserving ALL {len(valid_tracks_to_write)} existing database tracks.")
        print(f"Adding {len(new_track_paths)} new tracks from disk.")

    if exclude_missing_files:
        removed_tracks = len(serato_norm_paths) - len(serato_norm_paths.intersection(local_norm_paths))
        if removed_tracks > 0:
            print(f"Note: {removed_tracks} tracks removed from database (no local files found).")
    else:
        removed_tracks = len(serato_norm_paths) - len(serato_norm_paths.intersection(local_norm_paths))
        if removed_tracks > 0:
            print(f"Note: {removed_tracks} tracks exist in database but not on disk (preserving them anyway).")

    # --- Writing Phase ---
    print("\n--- Rebuilding Database and Crates ---")
    new_db_path = serato_db_path + ".tmp"
    try:
        with open(new_db_path, 'wb') as f:
            # Write database header
            _write_chunk(f, 'vrsn', '2.0/Serato ScratchLive Database'.encode('utf-16-be'))
            
            # Create the main library entry ('oent') containing all tracks
            main_library_payload = b''
            # Add existing tracks
            for track_chunk in valid_tracks_to_write:
                main_library_payload += track_chunk
            # Add new tracks
            for i, path in enumerate(new_track_paths):
                if (i + 1) % 100 == 0:
                    print(f"  ...processed {i+1}/{len(new_track_paths)} new tracks...")
                
                otrk_payload = create_track_chunk_payload(path)
                otrk_header = b'otrk' + struct.pack('>I', len(otrk_payload))
                main_library_payload += otrk_header + otrk_payload
                # The otrk chunk itself does not get padded here, its subchunks are already padded.
            
            _write_chunk(f, 'oent', main_library_payload)

        # Atomically replace the old database
        os.replace(new_db_path, serato_db_path)
        print("\nDatabase sync complete!")

    except Exception as e:
        print(f"\nAn error occurred while writing the new database: {e}")
        if os.path.exists(new_db_path):
            os.remove(new_db_path)
        return

    # --- Crate Generation ---
    print("\n--- Updating Crates ---")
    # Use intelligent crate management instead of regenerating everything
    
    # Import our intelligent crate manager
    from crate_manager import update_crates_intelligently
    
    # Create subcrates directory if it doesn't exist
    if not os.path.exists(serato_subcrates_path):
        os.makedirs(serato_subcrates_path)
        print(f"Created Subcrates directory: {serato_subcrates_path}")
    
    # Use intelligent crate updates - only update crates that need it
    update_crates_intelligently(local_music_map, serato_subcrates_path, music_folder)
    
    print("\nCrate generation complete.")
    print("SeratoSync finished successfully!")


if __name__ == "__main__":
    main()
