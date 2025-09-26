#!/usr/bin/env python3
"""
Database cleanup utility for Serato database corruption and duplicates.

This module provides functions to clean up corrupted Serato database entries
and remove duplicates while preserving tracks with proper metadata.
"""

import os
from pathlib import Path
from typing import List, Dict, Set, Tuple
import time
import shutil


def clean_database_records(records: List[dict], remove_duplicates: bool = True, require_metadata: bool = True) -> Tuple[List[dict], dict]:
    """
    Clean database records by removing corrupted entries and duplicates.
    
    Args:
        records: List of track record dictionaries
        remove_duplicates: Whether to remove duplicate tracks
        require_metadata: Whether to require basic metadata (title, artist, or album)
    
    Returns:
        Tuple of (cleaned_records, cleanup_stats)
    """
    stats = {
        'original_count': len(records),
        'removed_no_path': 0,
        'removed_no_metadata': 0,
        'removed_duplicates': 0,
        'removed_corrupted': 0,
        'final_count': 0
    }
    
    cleaned_records = []
    seen_paths = set()
    
    for record in records:
        # Check if record has a valid file path
        if 'pfil' not in record or not record['pfil'].strip():
            stats['removed_no_path'] += 1
            continue
            
        file_path = record['pfil'].strip()
        
        # Check for basic corruption indicators
        if len(file_path) < 3 or file_path.count('\x00') > 0:
            stats['removed_corrupted'] += 1
            continue
        
        # Check if file path looks valid (has extension)
        if '.' not in os.path.basename(file_path):
            stats['removed_corrupted'] += 1
            continue
        
        # Check for required metadata if specified
        if require_metadata:
            has_metadata = any([
                record.get('ttit', '').strip(),  # Title
                record.get('tart', '').strip(),  # Artist
                record.get('talb', '').strip()   # Album
            ])
            
            if not has_metadata:
                stats['removed_no_metadata'] += 1
                continue
        
        # Check for duplicates if specified
        if remove_duplicates:
            # Use normalized file path for duplicate detection
            normalized_path = file_path.replace('\\', '/').lower()
            if normalized_path in seen_paths:
                stats['removed_duplicates'] += 1
                continue
            seen_paths.add(normalized_path)
        
        # Record passed all checks
        cleaned_records.append(record)
    
    stats['final_count'] = len(cleaned_records)
    return cleaned_records, stats


def backup_database(db_path: Path) -> Path:
    """
    Create a backup of the database file.
    
    Args:
        db_path: Path to the original database file
        
    Returns:
        Path to the backup file
    """
    timestamp = int(time.time())
    backup_path = db_path.parent / f"database V2.backup.{timestamp}"
    
    # Copy the original file
    shutil.copy2(db_path, backup_path)
    
    return backup_path


def analyze_database_issues(records: List[dict]) -> Dict[str, any]:
    """
    Analyze database records to identify potential issues.
    
    Args:
        records: List of track record dictionaries
        
    Returns:
        Dictionary with analysis results
    """
    analysis = {
        'total_records': len(records),
        'records_without_path': 0,
        'records_without_metadata': 0,
        'potential_duplicates': 0,
        'corrupted_paths': 0,
        'path_statistics': {},
        'metadata_coverage': {}
    }
    
    seen_paths = {}
    path_extensions = {}
    
    for record in records:
        # Check file path
        if 'pfil' not in record or not record['pfil'].strip():
            analysis['records_without_path'] += 1
            continue
            
        file_path = record['pfil'].strip()
        
        # Check for corruption
        if len(file_path) < 3 or file_path.count('\x00') > 0:
            analysis['corrupted_paths'] += 1
            continue
            
        # Track extensions
        if '.' in os.path.basename(file_path):
            ext = os.path.splitext(file_path)[1].lower()
            path_extensions[ext] = path_extensions.get(ext, 0) + 1
        else:
            analysis['corrupted_paths'] += 1
            continue
        
        # Check for duplicates
        normalized_path = file_path.replace('\\', '/').lower()
        if normalized_path in seen_paths:
            analysis['potential_duplicates'] += 1
        else:
            seen_paths[normalized_path] = record
        
        # Check metadata coverage
        has_title = bool(record.get('ttit', '').strip())
        has_artist = bool(record.get('tart', '').strip())
        has_album = bool(record.get('talb', '').strip())
        
        if not (has_title or has_artist or has_album):
            analysis['records_without_metadata'] += 1
    
    analysis['path_statistics'] = path_extensions
    analysis['metadata_coverage'] = {
        'with_metadata': analysis['total_records'] - analysis['records_without_metadata'],
        'without_metadata': analysis['records_without_metadata']
    }
    
    return analysis
