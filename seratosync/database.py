"""
Database V2 parsing functionality for Serato.

This module handles parsing of Serato's Database V2 file format to extract
track information and infer prefixes for path normalization.
"""

from collections import Counter
from pathlib import Path
from typing import Set, Optional, Tuple
from .tlv_utils import iter_tlv, iter_nested_tlv
import os
import struct


def read_database_v2_pfil_set(db_path: Path, sample_for_prefix: int = 500) -> Tuple[Set[str], Optional[str], int]:
    """
    Return (pfil_set, inferred_prefix, total_tracks). The inferred_prefix is the
    most common first path segment (before the first '/') among 'pfil' values.
    Strings are decoded as UTF‑16BE.
    """
    pfil_set: Set[str] = set()
    seg_counter: Counter[str] = Counter()
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
                        pfil_set.add(s.replace("\\", "/"))
                        total += 1
                        if len(seg_counter) < sample_for_prefix:
                            # count top-level segment for prefix inference
                            seg = s.split("/", 1)[0] if "/" in s else s
                            if seg:
                                seg_counter.update([seg])
                        break
            # else ignore
    inferred = None
    if seg_counter:
        inferred = seg_counter.most_common(1)[0][0]
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
    if inferred_from_db:
        return inferred_from_db.strip("/")
    # fallback to library root last component
    return library_root.name.strip("/")
