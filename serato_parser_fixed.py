#!/usr/bin/env python3
"""
Fixed Serato Database Parser
Completely rewritten to handle the actual database structure correctly.
"""

import os
import struct
import logging
from io import BytesIO
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('serato_parser_fixed')

def find_otrk_chunks(data):
    """
    Find all 'otrk' chunk positions in the binary data.
    Returns list of (position, length) tuples where otrk chunks start.
    """
    otrk_chunks = []
    otrk_pattern = b'otrk'
    
    pos = 0
    while True:
        pos = data.find(otrk_pattern, pos)
        if pos == -1:
            break
        
        # Check if this is a valid chunk header (4-byte length + 4-byte tag)
        if pos >= 4:
            try:
                length_pos = pos - 4
                chunk_length = struct.unpack('>I', data[length_pos:pos])[0]
                # Sanity check: length should be reasonable (not too big or negative)
                if 0 < chunk_length < 100000:  # Max 100KB per chunk seems reasonable
                    otrk_chunks.append((length_pos, chunk_length))
            except:
                pass
        
        pos += 4
    
    return otrk_chunks

def read_string_field(data, pos):
    """
    Read a UTF-16BE string field from the given position.
    Returns (string_value, next_position)
    """
    try:
        # Read length (4 bytes, big-endian)
        if pos + 4 > len(data):
            return None, pos
        
        length = struct.unpack('>I', data[pos:pos+4])[0]
        pos += 4
        
        if pos + length > len(data):
            return None, pos
            
        # Read the UTF-16BE string
        string_data = data[pos:pos+length]
        # Decode UTF-16BE, handling potential errors
        try:
            decoded_string = string_data.decode('utf-16be').rstrip('\x00')
        except UnicodeDecodeError:
            decoded_string = string_data.decode('utf-16be', errors='ignore').rstrip('\x00')
        
        return decoded_string, pos + length
    except:
        return None, pos

def extract_track_from_otrk(data, otrk_pos, chunk_length):
    """
    Extract track information from an otrk chunk.
    """
    track_info = {}
    
    try:
        # Store the raw chunk data (needed for sync system)
        chunk_end = otrk_pos + 8 + chunk_length
        if chunk_end <= len(data):
            track_info['__raw_chunk'] = data[otrk_pos:chunk_end]
            track_info['__parse_pos'] = otrk_pos
        
        # Skip the otrk length and tag (8 bytes total)
        pos = otrk_pos + 8
        
        # Look for specific field tags within the chunk bounds
        search_end = min(chunk_end, len(data))
        
        # Find pfil (file path)
        pfil_pos = data.find(b'pfil', pos, search_end)
        if pfil_pos != -1:
            file_path, _ = read_string_field(data, pfil_pos + 4)
            if file_path:
                track_info['pfil'] = file_path
        
        # Find tsng (song title)
        tsng_pos = data.find(b'tsng', pos, search_end)
        if tsng_pos != -1:
            song_title, _ = read_string_field(data, tsng_pos + 4)
            if song_title:
                track_info['tsng'] = song_title
        
        # Find tart (artist)
        tart_pos = data.find(b'tart', pos, search_end)
        if tart_pos != -1:
            artist, _ = read_string_field(data, tart_pos + 4)
            if artist:
                track_info['tart'] = artist
        
        # Find talb (album)
        talb_pos = data.find(b'talb', pos, search_end)
        if talb_pos != -1:
            album, _ = read_string_field(data, talb_pos + 4)
            if album:
                track_info['talb'] = album
                
        # Find tgen (genre)
        tgen_pos = data.find(b'tgen', pos, search_end)
        if tgen_pos != -1:
            genre, _ = read_string_field(data, tgen_pos + 4)
            if genre:
                track_info['tgen'] = genre
        
        # Find tbpm (BPM) - CRITICAL ANALYSIS DATA
        tbpm_pos = data.find(b'tbpm', pos, search_end)
        if tbpm_pos != -1:
            bpm, _ = read_string_field(data, tbpm_pos + 4)
            if bpm:
                track_info['tbpm'] = bpm
        
        # Find tkey (Key) - CRITICAL ANALYSIS DATA
        tkey_pos = data.find(b'tkey', pos, search_end)
        if tkey_pos != -1:
            key, _ = read_string_field(data, tkey_pos + 4)
            if key:
                track_info['tkey'] = key
        
        # Find tcom (Comments)
        tcom_pos = data.find(b'tcom', pos, search_end)
        if tcom_pos != -1:
            comments, _ = read_string_field(data, tcom_pos + 4)
            if comments:
                track_info['tcom'] = comments
        
        # Find ttim (Time/Duration)
        ttim_pos = data.find(b'ttim', pos, search_end)
        if ttim_pos != -1:
            duration, _ = read_string_field(data, ttim_pos + 4)
            if duration:
                track_info['ttim'] = duration
        
        # Find tbit (Bitrate)
        tbit_pos = data.find(b'tbit', pos, search_end)
        if tbit_pos != -1:
            bitrate, _ = read_string_field(data, tbit_pos + 4)
            if bitrate:
                track_info['tbit'] = bitrate
        
        # Find tsmp (Sample Rate)
        tsmp_pos = data.find(b'tsmp', pos, search_end)
        if tsmp_pos != -1:
            samplerate, _ = read_string_field(data, tsmp_pos + 4)
            if samplerate:
                track_info['tsmp'] = samplerate
        
    except Exception as e:
        logger.debug(f"Error extracting track at position {otrk_pos}: {e}")
    
    return track_info

def parse_serato_database(db_path):
    """
    Parse the Serato database using a completely different approach.
    Find all otrk chunks and extract track information from each.
    """
    logger.info(f"--- Starting Fixed Serato Database Parse: {db_path} ---")
    
    try:
        if not os.path.exists(db_path):
            logger.error(f"Database file not found at {db_path}")
            return None
        
        with open(db_path, 'rb') as f:
            data = f.read()
        
        logger.info(f"Successfully read {len(data)} bytes from the database file.")
        
        # Find all otrk chunk positions
        otrk_chunks = find_otrk_chunks(data)
        logger.info(f"Found {len(otrk_chunks)} potential otrk chunks")
        
        tracks = []
        
        for i, (pos, length) in enumerate(otrk_chunks):
            if i % 1000 == 0:
                logger.info(f"Processing otrk chunk {i+1}/{len(otrk_chunks)}")
                
            track_info = extract_track_from_otrk(data, pos, length)
            
            # Only include tracks that have a file path
            if track_info.get('pfil'):
                tracks.append(track_info)
            
        logger.info(f"--- Parse Complete. Found {len(tracks)} valid tracks with file paths. ---")
        return {'tracks': tracks}
        
    except Exception as e:
        logger.error(f"An unhandled exception occurred during parsing: {e}", exc_info=True)
        return None

def main():
    """Test the fixed parser."""
    import configparser
    
    try:
        config = configparser.ConfigParser()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, 'config.ini')
        
        if not os.path.exists(config_path):
            print(f"Error: config.ini not found at {config_path}")
            return
            
        config.read(config_path)
        database_file = config.get('paths', 'serato_database')
    except Exception as e:
        print(f"Error reading config file: {e}")
        return

    print(f"Testing FIXED parser with database: {database_file}")
    parsed_data = parse_serato_database(database_file)

    if parsed_data and parsed_data.get('tracks'):
        print(f"\n--- Fixed Parser Test Result ---")
        print(f"Successfully parsed {len(parsed_data['tracks'])} tracks.")
        print("--- First 10 Tracks ---")
        for i, track in enumerate(parsed_data['tracks'][:10]):
            print(f"\nTrack {i+1}:")
            print(f"  Song: {track.get('tsng', 'N/A')}")
            print(f"  Artist: {track.get('tart', 'N/A')}")
            print(f"  Album: {track.get('talb', 'N/A')}")  
            print(f"  Genre: {track.get('tgen', 'N/A')}")
            print(f"  Path: {track.get('pfil', 'N/A')}")
    else:
        print("\n--- Fixed Parser Test Result ---")
        print("No tracks found or an error occurred during parsing.")

if __name__ == "__main__":
    main()
