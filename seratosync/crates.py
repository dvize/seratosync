"""
Crate file management for Serato.

This module handles writing and managing Serato crate files, including
path generation and track entry formatting.
"""

from pathlib import Path
from typing import List, Optional, Set
from .tlv_utils import write_chunk, make_chunk, encode_u16be

# Supported audio file extensions
AUDIO_EXTS = {".mp3", ".m4a", ".aac", ".aif", ".aiff", ".wav", ".flac", ".ogg"}

# Crate file version string
CRATE_VRSN = "1.0/Serato ScratchLive Crate"


def is_audio_file(p: Path, allowed_exts: Optional[Set[str]] = None) -> bool:
    """Check if a path is an audio file with allowed extension."""
    exts = allowed_exts or AUDIO_EXTS
    return p.is_file() and p.suffix.lower() in exts


def crate_path_for_dir(serato_root: Path, dir_rel: Path) -> Path:
    """
    Generate the crate file path for a directory.
    
    Args:
        serato_root: Path to the _Serato_ folder
        dir_rel: Relative path to the directory from library root
        
    Returns:
        Path to the crate file
    """
    # Subcrates mirror nested directories. The crate filename is the last folder name.
    subcrates_dir = serato_root / "Subcrates"
    return (subcrates_dir / dir_rel / (dir_rel.name + ".crate")).resolve()


def build_ptrk(prefix: str, rel_file: Path) -> str:
    """
    Build a ptrk (track path) string for a relative file.
    
    Args:
        prefix: Prefix to prepend to the path
        rel_file: Relative path to the audio file
        
    Returns:
        ptrk string with forward slashes
    """
    # ptrk/pfil use forward slashes. On Windows/mac this is fine.
    parts = [prefix] if prefix else []
    parts.extend(rel_file.parts)
    return "/".join(parts)


def write_crate_file(outfile: Path, track_paths: List[str]) -> None:
    """
    Write a crate file with the given track paths.
    
    Args:
        outfile: Path to the crate file to write
        track_paths: List of ptrk track paths to include
    """
    outfile.parent.mkdir(parents=True, exist_ok=True)
    with open(outfile, "wb") as f:
        write_chunk("vrsn", encode_u16be(CRATE_VRSN), f)
        for path_str in track_paths:
            inner = make_chunk("ptrk", encode_u16be(path_str))
            write_chunk("otrk", inner, f)


def build_crate_payload(track_paths: List[str]) -> bytes:
    """
    Build the complete payload for a crate file as bytes.
    
    Args:
        track_paths: List of ptrk track paths to include
        
    Returns:
        Complete crate file payload as bytes
    """
    payload = make_chunk("vrsn", encode_u16be(CRATE_VRSN))
    for path_str in track_paths:
        inner = make_chunk("ptrk", encode_u16be(path_str))
        payload += make_chunk("otrk", inner)
    return payload
