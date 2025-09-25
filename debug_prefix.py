#!/usr/bin/env python3

from seratosync.database import read_database_v2_records

records = read_database_v2_records('E:/_Serato_/database V2')
path_samples = []
for record in records[:10]:
    pfil = record.get('pfil', '')
    if pfil:
        path_samples.append(pfil.replace('\\', '/'))

print('First 5 path samples:')
for i, p in enumerate(path_samples[:5]):
    print(f'  {i}: {repr(p)}')

if path_samples:
    split_paths = [p.split('/') for p in path_samples]
    min_len = min(len(p) for p in split_paths)
    print(f'Min path length: {min_len}')
    
    common_parts = []
    for i in range(min_len - 1):  # -1 to avoid filename
        first_part = split_paths[0][i]
        all_match = all(p[i] == first_part for p in split_paths)
        print(f'  Part {i}: {repr(first_part)} - Match: {all_match}')
        if all_match:
            common_parts.append(first_part)
        else:
            break
    
    print(f'Common parts: {common_parts}')
    if common_parts:
        print(f'Should be inferred as: {repr("/".join(common_parts))}')
