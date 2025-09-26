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
    
    This function provides cross-platform prefix normalization that works consistently
    between Windows and macOS by intelligently matching database paths with library structure.
    
    Args:
        prefix: User-specified prefix
        inferred_from_db: Prefix inferred from database
        library_root: Library root path
        
    Returns:
        Normalized prefix string
    """
    if prefix:
        return prefix.strip("/")
    
    # Convert library_root to normalized path format (forward slashes, no drive letters)
    lib_str = str(library_root).replace("\\", "/")
    
    # Remove drive letters for Windows (e.g., "C:/Users/..." -> "Users/...")
    if len(lib_str) >= 3 and lib_str[1] == ':':
        lib_str = lib_str[3:]  # Remove "C:/" prefix
    
    # Remove leading slash for Unix-style paths
    lib_str = lib_str.lstrip("/")
    
    if inferred_from_db:
        # Clean the inferred prefix
        inferred_clean = inferred_from_db.replace("\\", "/").strip("/")
        
        # Remove drive letters from inferred prefix if present
        if len(inferred_clean) >= 3 and inferred_clean[1] == ':':
            inferred_clean = inferred_clean[3:]
        
        # Check if the inferred prefix is a reasonable match for our library root
        lib_parts = lib_str.split('/')
        inferred_parts = inferred_clean.split('/')
        
        # Strategy 1: Exact match - use inferred (with any casing corrections applied later)
        if lib_str.lower() == inferred_clean.lower():
            return inferred_clean
            
        # Strategy 2: If inferred prefix is contained in library root, use inferred
        # This handles cases where library_root="E:/Music/Music Tracks" but database has "E:/Music/..."
        # In this case, we want to use "Music" as the prefix, not "Music/Music Tracks"
        if lib_str.lower().startswith(inferred_clean.lower() + "/"):
            return inferred_clean
        
        # Strategy 3: If library root is contained in inferred prefix, use inferred (more specific)
        # This handles cases where library_root="E:/Music" but database has "E:/Music/Music Tracks/..."  
        if inferred_clean.lower().startswith(lib_str.lower() + "/"):
            return inferred_clean
            
        # Strategy 3: Find longest common path between inferred and library root
        common_parts = []
        for i, (lib_part, inf_part) in enumerate(zip(lib_parts, inferred_parts)):
            if lib_part.lower() == inf_part.lower():  # Case-insensitive match
                # Preserve the casing from library_root (user's preference)
                common_parts.append(lib_part)
            else:
                break
        
        if common_parts:
            # If inferred has more specificity, use the inferred prefix
            # If library has more specificity, use library prefix  
            # This ensures we use the most specific path that represents actual database structure
            if len(inferred_parts) > len(lib_parts):
                # Inferred is more specific - use it but preserve library root casing for common parts
                result_parts = common_parts + inferred_parts[len(common_parts):]
                return '/'.join(result_parts)
            elif len(lib_parts) >= len(inferred_parts):
                # Library is more specific or equal - use library casing
                return '/'.join(lib_parts)        # Fallback: Use inferred prefix if we can't determine a better match
        return inferred_clean
    
    # Final fallback: Use library root structure
    return lib_str

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
