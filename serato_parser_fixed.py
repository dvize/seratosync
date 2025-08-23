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
    Read a UTF-16BE string field with progressive error recovery.
    Uses multiple strategies to avoid discarding valid tracks.
    Returns (string_value, next_position)
    """
    try:
        # Read length (4 bytes, big-endian)
        if pos + 4 > len(data):
            return None, pos
        
        length = struct.unpack('>I', data[pos:pos+4])[0]
        pos += 4
        
        # Sanity check: length should be reasonable
        if length == 0:
            return "", pos
        if length > 10000:  # Max reasonable path length
            return None, pos
            
        # Check if we have enough data
        if pos + length > len(data):
            available_length = len(data) - pos
            if available_length <= 0:
                return None, pos
            string_data = data[pos:pos + available_length]
            logger.debug(f"Truncated string field at pos {pos}: expected {length}, got {available_length}")
        else:
            string_data = data[pos:pos+length]
        
        # PROGRESSIVE ERROR RECOVERY APPROACH
        # Try multiple decoding strategies, from strictest to most permissive
        
        # Strategy 1: Perfect UTF-16BE decoding
        try:
            # Ensure even number of bytes for UTF-16
            if len(string_data) % 2 != 0:
                string_data = string_data[:-1]
            
            decoded_string = string_data.decode('utf-16be', errors='strict')
            decoded_string = decoded_string.rstrip('\x00')  # Remove null terminators
            
            # Quick validation - allow most characters but filter obvious corruption
            if not any(ord(c) < 32 and c not in '\t\n\r' for c in decoded_string):
                return decoded_string, pos + length
                
        except UnicodeDecodeError:
            pass  # Try next strategy
        
        # Strategy 2: UTF-16BE with replacement characters
        try:
            if len(string_data) % 2 != 0:
                string_data = string_data[:-1]
            
            decoded_string = string_data.decode('utf-16be', errors='replace')
            decoded_string = decoded_string.rstrip('\x00')
            
            # Handle specific corruption patterns we've seen
            if 'ā' in decoded_string:
                corruption_index = decoded_string.find('ā')
                if corruption_index > 0:
                    decoded_string = decoded_string[:corruption_index]
            
            # Clean up but be permissive
            decoded_string = decoded_string.replace('�', '')  # Remove replacement chars
            if decoded_string.strip():  # Return if we got something meaningful
                logger.debug(f"Recovered string with replacements at pos {pos}: {repr(decoded_string[:30])}")
                return decoded_string, pos + length
                
        except:
            pass  # Try next strategy
        
        # Strategy 3: Byte-pair recovery for severely corrupted data
        try:
            recovered_chars = []
            for i in range(0, len(string_data) - 1, 2):
                try:
                    char_bytes = string_data[i:i+2]
                    char = char_bytes.decode('utf-16be')
                    # Be permissive - accept most printable characters
                    if 32 <= ord(char) <= 126 or char in '\t\n\r' or ord(char) > 127:
                        recovered_chars.append(char)
                except:
                    continue  # Skip corrupted character pairs
            
            if recovered_chars:
                decoded_string = ''.join(recovered_chars).rstrip('\x00')
                if decoded_string.strip():
                    logger.debug(f"Partial character recovery at pos {pos}: {repr(decoded_string[:30])}")
                    return decoded_string, pos + length
                    
        except:
            pass
        
        # Strategy 4: Last resort - return empty string to preserve track
        # This prevents losing entire tracks due to one corrupted field
        logger.debug(f"All decoding failed, preserving track with empty field at pos {pos}")
        return "", pos + length
        
    except Exception as e:
        logger.debug(f"Critical error in string field parsing at pos {pos}: {e}")
        return None, pos

def extract_track_from_otrk(data, otrk_pos, chunk_length):
    """
    Extract track information from an otrk chunk with enhanced error recovery.
    Tries to recover as much metadata as possible even from corrupted tracks.
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
        
        # Find pfil (file path) - CRITICAL for track validity
        pfil_pos = data.find(b'pfil', pos, search_end)
        if pfil_pos != -1:
            file_path, _ = read_string_field(data, pfil_pos + 4)
            if file_path:  # Now returns "" instead of None for corrupted fields
                track_info['pfil'] = file_path
        
        # Find tsng (song title) - Use enhanced recovery
        tsng_pos = data.find(b'tsng', pos, search_end)
        if tsng_pos != -1:
            song_title, _ = read_string_field(data, tsng_pos + 4)
            if song_title is not None:  # Accept empty string but not None
                track_info['tsng'] = song_title
        
        # Find tart (artist) - Use enhanced recovery
        tart_pos = data.find(b'tart', pos, search_end)
        if tart_pos != -1:
            artist, _ = read_string_field(data, tart_pos + 4)
            if artist is not None:  # Accept empty string but not None
                track_info['tart'] = artist
        
        # Find talb (album)
        talb_pos = data.find(b'talb', pos, search_end)
        if talb_pos != -1:
            album, _ = read_string_field(data, talb_pos + 4)
            if album is not None:
                track_info['talb'] = album
                
        # Find tgen (genre)
        tgen_pos = data.find(b'tgen', pos, search_end)
        if tgen_pos != -1:
            genre, _ = read_string_field(data, tgen_pos + 4)
            if genre is not None:
                track_info['tgen'] = genre
        
        # Find tbpm (BPM) - CRITICAL ANALYSIS DATA
        tbpm_pos = data.find(b'tbpm', pos, search_end)
        if tbpm_pos != -1:
            bpm, _ = read_string_field(data, tbpm_pos + 4)
            if bpm is not None:
                track_info['tbpm'] = bpm
        
        # Find tkey (Key) - CRITICAL ANALYSIS DATA
        tkey_pos = data.find(b'tkey', pos, search_end)
        if tkey_pos != -1:
            key, _ = read_string_field(data, tkey_pos + 4)
            if key is not None:
                track_info['tkey'] = key
        
        # Find tcom (Comments)
        tcom_pos = data.find(b'tcom', pos, search_end)
        if tcom_pos != -1:
            comments, _ = read_string_field(data, tcom_pos + 4)
            if comments is not None:
                track_info['tcom'] = comments
        
        # Find ttim (Time/Duration)
        ttim_pos = data.find(b'ttim', pos, search_end)
        if ttim_pos != -1:
            duration, _ = read_string_field(data, ttim_pos + 4)
            if duration is not None:
                track_info['ttim'] = duration
        
        # Find tbit (Bitrate)
        tbit_pos = data.find(b'tbit', pos, search_end)
        if tbit_pos != -1:
            bitrate, _ = read_string_field(data, tbit_pos + 4)
            if bitrate is not None:
                track_info['tbit'] = bitrate
        
        # Find tsmp (Sample Rate)
        tsmp_pos = data.find(b'tsmp', pos, search_end)
        if tsmp_pos != -1:
            samplerate, _ = read_string_field(data, tsmp_pos + 4)
            if samplerate is not None:
                track_info['tsmp'] = samplerate
                
        # PRESERVE BINARY ANALYSIS DATA - Critical for Serato functionality
        # Look for beat grid data
        for beat_tag in [b'beatgrid', b'beat', b'begt']:
            beat_pos = data.find(beat_tag, pos, search_end)
            if beat_pos != -1:
                try:
                    if beat_pos + len(beat_tag) + 4 < search_end:
                        beat_length = struct.unpack('>I', data[beat_pos + len(beat_tag):beat_pos + len(beat_tag) + 4])[0]
                        if beat_pos + len(beat_tag) + 4 + beat_length <= search_end and beat_length < 50000:
                            track_info['beat_grid'] = data[beat_pos + len(beat_tag) + 4:beat_pos + len(beat_tag) + 4 + beat_length]
                            break
                except:
                    continue
        
        # Look for overview waveform data  
        overview_pos = data.find(b'overview', pos, search_end)
        if overview_pos != -1:
            try:
                if overview_pos + 8 + 4 < search_end:
                    overview_length = struct.unpack('>I', data[overview_pos + 8:overview_pos + 12])[0]
                    if overview_pos + 12 + overview_length <= search_end and overview_length < 100000:
                        track_info['overview'] = data[overview_pos + 12:overview_pos + 12 + overview_length]
            except:
                pass
        
        # Look for analysis data markers
        analysis_pos = data.find(b'uaml', pos, search_end)  
        if analysis_pos != -1:
            try:
                if analysis_pos + 4 + 4 < search_end:
                    analysis_length = struct.unpack('>I', data[analysis_pos + 4:analysis_pos + 8])[0]
                    if analysis_pos + 8 + analysis_length <= search_end and analysis_length < 10000:
                        track_info['analysis'] = data[analysis_pos + 8:analysis_pos + 8 + analysis_length]
            except:
                pass
        
    except Exception as e:
        # Don't let parsing errors destroy the entire track
        logger.debug(f"Non-critical error extracting track at position {otrk_pos}: {e}")
    
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
