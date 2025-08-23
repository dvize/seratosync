#!/usr/bin/env python3
"""
Serato Crate Parser and Manager
Handles reading existing crates and updating them intelligently.
"""

import os
import struct
import logging
from io import BytesIO

logger = logging.getLogger('crate_manager')

def read_existing_crates(subcrates_path):
    """
    Read all existing .crate files and return their track memberships.
    Returns: dict of {crate_name: set(track_paths)}
    """
    crates = {}
    if not os.path.exists(subcrates_path):
        return crates
    
    # Scan only the main Subcrates directory (flat structure)
    for item in os.listdir(subcrates_path):
        item_path = os.path.join(subcrates_path, item)
        if os.path.isfile(item_path) and item.endswith('.crate'):
            # Convert Serato's %% format back to ' / ' format for comparison
            crate_name = item[:-6].replace('%%', ' / ')  # Remove .crate extension and convert %% to ' / '
            try:
                tracks = parse_crate_file(item_path)
                if tracks:
                    crates[crate_name] = set(tracks)
                    logger.info(f"Loaded crate '{crate_name}' with {len(tracks)} tracks")
            except Exception as e:
                logger.warning(f"Could not parse crate {item_path}: {e}")
    
    return crates

def parse_crate_file(crate_path):
    """
    Parse a single .crate file and extract track file paths.
    Returns list of track paths.
    """
    tracks = []
    
    try:
        with open(crate_path, 'rb') as f:
            data = f.read()
        
        if len(data) < 8:
            return tracks
            
        # Find all 'ptrk' (track path) entries
        pos = 0
        while pos < len(data) - 8:
            if data[pos:pos+4] == b'ptrk':
                try:
                    # Read length
                    length = struct.unpack('>I', data[pos+4:pos+8])[0]
                    if pos + 8 + length <= len(data):
                        # Read the track path (UTF-16BE encoded)
                        path_data = data[pos+8:pos+8+length]
                        track_path = path_data.decode('utf-16be').rstrip('\x00')
                        if track_path:
                            tracks.append(track_path)
                        pos += 8 + length
                        # Skip padding
                        while pos < len(data) and data[pos] == 0:
                            pos += 1
                    else:
                        pos += 1
                except:
                    pos += 1
            else:
                pos += 1
                
    except Exception as e:
        logger.debug(f"Error parsing crate {crate_path}: {e}")
    
    return tracks

def should_update_crate(crate_name, existing_tracks, new_tracks):
    """
    Determine if a crate needs to be updated.
    Returns True if tracks have been added or removed.
    """
    if existing_tracks is None:
        return len(new_tracks) > 0  # New crate with tracks
    
    existing_set = set(existing_tracks) if existing_tracks else set()
    new_set = set(new_tracks) if new_tracks else set()
    
    return existing_set != new_set

def create_serato_crate_path(crate_name, base_path):
    """
    Create proper Serato crate filename using %% separator for nesting.
    All crates are stored flat in the Subcrates directory.
    The filename determines nesting in Serato DJ interface.
    """
    # Convert folder path separators to Serato's %% format
    serato_crate_name = crate_name.replace(' / ', '%%')
    
    # Clean the name for filesystem safety
    safe_name = serato_crate_name.replace('/', '_').replace('\\', '_')
    
    # All crates go directly in the base Subcrates directory (flat structure)
    return os.path.join(base_path, f"{safe_name}.crate")

def update_crates_intelligently(local_music_map, subcrates_path):
    """
    Update crates intelligently - only create new crates for new folders or update changed ones.
    Preserves existing crate names and structure.
    """
    logger.info("Reading existing crates...")
    existing_crates = read_existing_crates(subcrates_path)
    
    # Normalize paths for comparison
    def normalize_path_for_crate(path):
        """Convert absolute path to relative for crate storage"""
        if path.startswith('/Users/'):
            return path[1:]  # Remove leading slash
        return path
    
    updated_count = 0
    preserved_count = 0
    new_crate_count = 0
    
    logger.info(f"Found {len(existing_crates)} existing crates")
    logger.info(f"Processing {len(local_music_map)} folder-based crates from file system")
    
    # Process folder-based crates
    for folder_path, track_paths in local_music_map.items():
        # Convert folder path to crate name format (same as existing system)
        crate_name = folder_path.replace(os.path.sep, ' / ')
        
        # Normalize track paths for crate storage
        normalized_tracks = [normalize_path_for_crate(path) for path in track_paths]
        
        existing_tracks = existing_crates.get(crate_name)
        
        if existing_tracks is None:
            # This is a completely new folder - create new crate
            try:
                crate_path = create_serato_crate_path(crate_name, subcrates_path)
                create_crate_file_simple(crate_name, normalized_tracks, crate_path)
                new_crate_count += 1
                logger.info(f"Created new crate for new folder: {crate_name}")
            except Exception as e:
                logger.error(f"Failed to create new crate '{crate_name}': {e}")
        elif should_update_crate(crate_name, existing_tracks, normalized_tracks):
            # Existing crate needs updates (tracks added/removed)
            try:
                crate_path = create_serato_crate_path(crate_name, subcrates_path)
                create_crate_file_simple(crate_name, normalized_tracks, crate_path)
                updated_count += 1
                logger.info(f"Updated existing crate with track changes: {crate_name}")
            except Exception as e:
                logger.error(f"Failed to update crate '{crate_name}': {e}")
        else:
            # Crate exists and doesn't need updates - preserve as-is
            preserved_count += 1
    
    logger.info(f"Crate update complete: {new_crate_count} new, {updated_count} updated, {preserved_count} preserved")

def create_crate_file_simple(crate_name, track_paths, crate_file_path):
    """
    Create a simple crate file with just the track paths.
    This is a minimal implementation focusing on track membership.
    """
    try:
        with open(crate_file_path, 'wb') as f:
            # Write version header
            vrsn_data = "1.0/Serato ScratchLive Crate".encode('utf-16be')
            f.write(b'vrsn')
            f.write(struct.pack('>I', len(vrsn_data)))
            f.write(vrsn_data)
            
            # Write track entries
            for track_path in track_paths:
                if track_path:  # Skip empty paths
                    path_data = track_path.encode('utf-16be')
                    f.write(b'ptrk')
                    f.write(struct.pack('>I', len(path_data)))
                    f.write(path_data)
                    
                    # Add padding to align to 4-byte boundary
                    padding_needed = (4 - (len(path_data) % 4)) % 4
                    if padding_needed > 0:
                        f.write(b'\x00' * padding_needed)
                        
    except Exception as e:
        logger.error(f"Error creating crate file {crate_file_path}: {e}")
        raise
