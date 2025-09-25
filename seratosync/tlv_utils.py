"""
TLV (Tag/Length/Value) utility functions for Serato file format parsing.

This module provides low-level utilities for working with TLV data structures
used in Serato's Database V2 and crate files.
"""

import os
import struct
from typing import Iterator, Tuple, BinaryIO


def be32(i: int) -> bytes:
    """Pack an integer as big-endian 32-bit."""
    return struct.pack(">I", i)


def encode_u16be(s: str) -> bytes:
    """Encode a string as UTF-16BE."""
    return s.encode("utf-16-be")


def write_chunk(tag: str, payload: bytes, out: BinaryIO) -> None:
    """Write a TLV chunk to a file-like object."""
    out.write(tag.encode("ascii"))
    out.write(be32(len(payload)))
    out.write(payload)


def make_chunk(tag: str, payload: bytes) -> bytes:
    """Create a TLV chunk as bytes."""
    return tag.encode("ascii") + be32(len(payload)) + payload


def iter_tlv(fh: BinaryIO) -> Iterator[Tuple[str, int, int]]:
    """
    Iterate over top-level TLV chunks in a file-like object.
    Yields (tag, size, offset_of_value).
    """
    while True:
        hdr = fh.read(8)
        if not hdr or len(hdr) < 8:
            break
        tag = hdr[:4].decode("ascii", errors="replace")
        size = struct.unpack(">I", hdr[4:])[0]
        val_off = fh.tell()
        yield (tag, size, val_off)
        # skip payload
        fh.seek(size, os.SEEK_CUR)


def iter_nested_tlv(buf: bytes) -> Iterator[Tuple[str, int, bytes]]:
    """
    Iterate over nested TLV chunks contained in 'buf' (bytes of a parent value).
    Yields (tag, size, value_bytes).
    """
    pos = 0
    n = len(buf)
    while pos + 8 <= n:
        tag = buf[pos:pos+4].decode("ascii", errors="replace")
        size = struct.unpack(">I", buf[pos+4:pos+8])[0]
        start = pos + 8
        end = start + size
        if end > n:
            break
        yield (tag, size, buf[start:end])
        pos = end
