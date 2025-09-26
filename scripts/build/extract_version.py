#!/usr/bin/env python3
"""Extract version string from original database."""

from seratosync.tlv_utils import iter_tlv

with open('E:/_Serato_/database V2 - Copy', 'rb') as f:
    # Get first chunk (should be version)
    tag, size, offset = next(iter_tlv(f))
    print(f'Version chunk: {tag}, size: {size}')
    
    f.seek(offset)
    version_data = f.read(size)
    
    print(f'Raw version data: {version_data.hex()}')
    
    # Decode as UTF-16BE 
    clean_data = version_data.rstrip(b'\x00')
    version_str = clean_data.decode('utf-16-be')
    print(f'Decoded version string: "{version_str}"')
