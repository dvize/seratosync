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
    Generate the crate file path for a directory using Serato's subcrate naming convention.
    
    Args:
        serato_root: Path to the _Serato_ folder
        dir_rel: Relative path to the directory from library root
        
    Returns:
        Path to the single crate file in the Subcrates directory.
    """
    subcrates_dir = serato_root / "Subcrates"
    
    # Join path components with '%%' for the crate filename
    crate_name = "%%".join(dir_rel.parts) + ".crate"
    
    return (subcrates_dir / crate_name).resolve()


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


def read_crate_file(crate_path: Path) -> List[str]:
    """
    Read an existing crate file and extract track paths.
    
    Args:
        crate_path: Path to the crate file
        
    Returns:
        List of ptrk track paths in the crate
    """
    if not crate_path.exists():
        return []
    
    track_paths = []
    try:
        with open(crate_path, "rb") as fh:
            from .tlv_utils import iter_nested_tlv
            import struct
            import os
            
            # Skip vrsn header if present
            first = fh.read(8)
            if len(first) == 8:
                tag = first[:4].decode("ascii", errors="ignore")
                size = struct.unpack(">I", first[4:])[0]
                if tag == "vrsn":
                    fh.read(size)  # skip version
                else:
                    fh.seek(-8, os.SEEK_CUR)  # rewind
            
            # Parse tracks
            while True:
                pos = fh.tell()
                hdr = fh.read(8)
                if not hdr or len(hdr) < 8:
                    break
                tag = hdr[:4].decode("ascii", errors="ignore")
                size = struct.unpack(">I", hdr[4:])[0]
                val = fh.read(size)
                if tag == "otrk":
                    # scan nested props for 'ptrk'
                    for ntag, nsz, nval in iter_nested_tlv(val):
                        if ntag == "ptrk":
                            try:
                                s = nval.decode("utf-16-be").rstrip("\x00")
                                track_paths.append(s)
                            except Exception:
                                continue
                            break  # Only expect one ptrk per otrk
    except Exception:
        # If we can't read the file, return empty list
        return []
    
    return track_paths
