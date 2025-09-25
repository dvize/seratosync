"""
Library scanning and file discovery functionality.

This module handles scanning the music library directory to discover
audio files and organize them by directory structure.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Set
from .crates import is_audio_file


def scan_library(library_root: Path, allowed_exts: Optional[Set[str]] = None) -> Dict[Path, List[Path]]:
    """
    Scan the library directory and return a mapping of relative directories to audio files.
    
    Args:
        library_root: Root directory of the music library
        allowed_exts: Set of allowed file extensions (defaults to standard audio formats)
        
    Returns:
        Dictionary mapping relative directory paths to lists of relative file paths
    """
    root = library_root.resolve()
    mapping: Dict[Path, List[Path]] = {}
    
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        rel_dir = d.relative_to(root)
        
        # Filter audio files
        audio_files = []
        for name in sorted(filenames):
            p = d / name
            if is_audio_file(p, allowed_exts):
                rel_file = p.relative_to(root)
                audio_files.append(rel_file)
        
        if audio_files:
            mapping[rel_dir] = audio_files
    
    return mapping


def get_library_stats(library_map: Dict[Path, List[Path]]) -> tuple[int, int]:
    """
    Get statistics from the library scan results.
    
    Args:
        library_map: Library mapping from scan_library()
        
    Returns:
        Tuple of (number_of_directories, number_of_audio_files)
    """
    num_dirs = len(library_map)
    num_files = sum(len(files) for files in library_map.values())
    return num_dirs, num_files


def build_crate_plans(
    library_map: Dict[Path, List[Path]], 
    prefix: str, 
    serato_root: Path
) -> List[tuple[Path, List[str]]]:
    """
    Build crate file plans based on library structure.
    
    Args:
        library_map: Library mapping from scan_library()
        prefix: Prefix to use for track paths
        serato_root: Path to the _Serato_ folder
        
    Returns:
        List of tuples (crate_file_path, track_paths)
    """
    from .crates import crate_path_for_dir, build_ptrk
    
    crate_plans = []
    for rel_dir, files in sorted(library_map.items()):
        if str(rel_dir) == '.':
            continue # Skip root directory, don't create a crate for it

        # Generate new tracks from directory scan
        new_ptrks = [build_ptrk(prefix, f) for f in files]
        
        crate_file = crate_path_for_dir(serato_root, rel_dir)
        
        # For directory-based crates, just use the current tracks
        # Don't merge with existing to avoid duplicating renamed tracks
        all_ptrks = new_ptrks
        
        crate_plans.append((crate_file, all_ptrks))
    
    return crate_plans


def detect_new_tracks(
    track_paths: List[str], 
    existing_pfil_set: Set[str]
) -> List[str]:
    """
    Detect which tracks are new (not in existing database).
    
    Args:
        track_paths: List of track paths to check
        existing_pfil_set: Set of existing pfil paths from database
        
    Returns:
        List of new track paths
    """
    return [p for p in track_paths if p not in existing_pfil_set]
