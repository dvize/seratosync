"""
Database V2 parsing functionality for Serato.

This module handles parsing of Serato's Database V2 file format to extract
track information and infer prefixes for path normalization.
"""

from collections import Counter
from pathlib import Path
from typing import Set, Optional, Tuple, List
from .tlv_utils import iter_tlv, iter_nested_tlv
import os
import struct


def read_database_v2_pfil_set(db_path: Path, sample_for_prefix: int = 500) -> Tuple[Set[str], Optional[str], int]:
    """
    Return (pfil_set, inferred_prefix, total_tracks). The inferred_prefix is the
    most common path prefix among 'pfil' values that represents the library root.
    Strings are decoded as UTF‑16BE.
    """
    pfil_set: Set[str] = set()
    path_samples: List[str] = []
    total = 0
    with open(db_path, "rb") as fh:
        # optional: read header
        first = fh.read(8)
        if len(first) == 8:
            tag = first[:4].decode("ascii", errors="ignore")
            size = struct.unpack(">I", first[4:])[0]
            if tag == "vrsn":
                ver = fh.read(size).decode("utf-16-be", errors="ignore")
            else:
                fh.seek(-8, os.SEEK_CUR)

        # iterate
        while True:
            pos = fh.tell()
            hdr = fh.read(8)
            if not hdr or len(hdr) < 8:
                break
            tag = hdr[:4].decode("ascii", errors="ignore")
            size = struct.unpack(">I", hdr[4:])[0]
            val = fh.read(size)
            if tag == "otrk":
                # scan nested props for 'pfil'
                for ntag, nsz, nval in iter_nested_tlv(val):
                    if ntag == "pfil":
                        try:
                            s = nval.decode("utf-16-be").rstrip("\x00")
                        except Exception:
                            continue
                        s = s.replace("\\", "/")
                        pfil_set.add(s)
                        total += 1
                        # Use better sampling: take every Nth record for more diversity
                        if len(path_samples) < sample_for_prefix:
                            # Skip some records to get better distribution
                            sample_interval = max(1, total // 50)  # Sample every 50th record or so
                            if total == 0 or total % sample_interval == 0:
                                path_samples.append(s)
                        break
            # else ignore
    inferred = None
    if path_samples:
        # Find the most common prefix by examining all path samples
        from collections import Counter
        
        # Try different prefix lengths and find the most common one
        prefix_counts = Counter()
        
        for path in path_samples:
            parts = path.split('/')
            # Try prefixes of length 1, 2, 3, etc. (but not the full path)
            # Allow deeper prefixes for better inference (up to 6 levels)
            for prefix_len in range(1, min(len(parts), 7)):  # Max 6 levels deep
                prefix = '/'.join(parts[:prefix_len])
                prefix_counts[prefix] += 1
        
        if prefix_counts:
            # Find the most common prefix that appears in at least 50% of samples
            min_frequency = len(path_samples) // 2
            common_prefixes = [(prefix, count) for prefix, count in prefix_counts.items() 
                             if count >= min_frequency]
            
            if common_prefixes:
                # Choose the longest common prefix that represents the actual library root
                # Sort by frequency first, then by length to get best match
                inferred = max(common_prefixes, key=lambda x: (x[1], len(x[0].split('/'))))[0]

    return pfil_set, inferred, total


def normalize_prefix(prefix: Optional[str], inferred_from_db: Optional[str], library_root: Path) -> str:
    """
    Normalize the prefix used for track paths in crates.
    
    Args:
        prefix: User-specified prefix
        inferred_from_db: Prefix inferred from database
        library_root: Library root path
        
    Returns:
        Normalized prefix string
    """
    if prefix:
        return prefix.strip("/")
    
    # If we have an inferred prefix, check if it makes sense for the library_root
    if inferred_from_db:
        # Convert library_root to the same format as database paths
        # e.g., /Users/dvize/Music/Music Tracks -> Users/dvize/Music/Music Tracks
        lib_path_parts = library_root.parts
        if lib_path_parts[0] == '/':
            lib_path_parts = lib_path_parts[1:]  # Remove leading slash
        
        expected_prefix = '/'.join(lib_path_parts)
        
        # If the database contains paths that match our library structure, use that
        # This handles cases where inferred_from_db is "Users/dvize/Music/MusicUnsorted"
        # but library_root is "/Users/dvize/Music/Music Tracks"
        if library_root.name in ["Music Tracks", "Music", "Library"] and "Music" in expected_prefix:
            return expected_prefix.strip("/")
        
        # Otherwise use the inferred prefix
        return inferred_from_db.strip("/")
    
    # fallback to library root path structure
    lib_path_parts = library_root.parts
    if lib_path_parts[0] == '/':
        lib_path_parts = lib_path_parts[1:]  # Remove leading slash
    return '/'.join(lib_path_parts).strip("/")

def read_database_v2_records(db_path: Path) -> List[dict]:
    """
    Read all track records from Database V2.
    
    Returns a list of dictionaries, each containing the TLV data for a track.
    Each dict has keys like 'pfil', 'ttyp', 'tadd', etc.
    """
    from .tlv_utils import iter_tlv, iter_nested_tlv
    records = []
    
    with open(db_path, "rb") as fh:
        # Skip header if present
        first = fh.read(8)
        if len(first) == 8:
            tag = first[:4].decode("ascii", errors="ignore")
            size = struct.unpack(">I", first[4:])[0]
            if tag == "vrsn":
                fh.read(size)  # Skip version
            else:
                fh.seek(-8, os.SEEK_CUR)

        # Read all records
        while True:
            pos = fh.tell()
            hdr = fh.read(8)
            if not hdr or len(hdr) < 8:
                break
            tag = hdr[:4].decode("ascii", errors="ignore")
            size = struct.unpack(">I", hdr[4:])[0]
            val = fh.read(size)
            if tag == "otrk":
                # Parse nested properties
                record = {}
                for ntag, nsz, nval in iter_nested_tlv(val):
                    try:
                        if ntag in ['pfil', 'ttyp', 'tadd', 'talb', 'tart', 'ttit', 'tgen', 'tkey', 'tcom', 'tgrp', 'tbit', 'tsmp', 'tbpm', 'tlen', 'tadd', 'tmod']:
                            # Text fields
                            record[ntag] = nval.decode("utf-16-be").rstrip("\x00")
                        else:
                            # Keep binary data as-is
                            record[ntag] = nval
                    except Exception:
                        record[ntag] = nval
                if 'pfil' in record:
                    record['pfil'] = record['pfil'].replace("\\", "/")
                records.append(record)
    
    return records


def write_database_v2_records(db_path: Path, records: List[dict]) -> None:
    """
    Write track records back to Database V2.
    
    Args:
        records: List of track record dictionaries
    """
    from .tlv_utils import make_chunk
    
    with open(db_path, "wb") as f:
        # Write version header - must match original exactly
        version = "2.0/Serato Scratch LIVE Database"
        f.write(make_chunk("vrsn", version.encode("utf-16-be") + b"\x00\x00"))
        
        # Write all records
        for record in records:
            inner = bytearray()
            for key, value in record.items():
                if isinstance(value, str):
                    # Encode strings as UTF-16-BE with null terminator
                    inner += make_chunk(key, value.encode("utf-16-be") + b"\x00\x00")
                elif hasattr(value, '__fspath__'):  # Path-like objects
                    # Convert Path objects to strings first
                    path_str = str(value)
                    inner += make_chunk(key, path_str.encode("utf-16-be") + b"\x00\x00")
                else:
                    # Binary data
                    inner += make_chunk(key, value)
            f.write(make_chunk("otrk", inner))
