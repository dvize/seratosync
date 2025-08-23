import struct
import sys
from io import BytesIO
import logging
import os

def _setup_logger():
    """Sets up a logger to debug the parsing process."""
    logger = logging.getLogger('serato_parser')
    logger.setLevel(logging.DEBUG)  # Log all levels of messages

    # Create a file handler to write logs to a file
    log_file = os.path.join(os.path.dirname(__file__), 'parser.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    # Create a console handler to output logs to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Only show info level and above in console

    # Create a formatter to specify the log message format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

logger = _setup_logger()

def _pad_len(n: int) -> int:
    """Calculates padding bytes needed to align to a 4-byte boundary."""
    return (-n) & 3

def _read_chunk(data_stream, padded=True):
    """Reads a single chunk and returns its tag, payload, and raw bytes."""
    start_pos = data_stream.tell()
    header = data_stream.read(8)
    if not header or len(header) < 8:
        return None, None, None

    try:
        tag, length = struct.unpack('>4sI', header)
        # Decode and strip whitespace AND null bytes for cleaner tags
        tag = tag.decode('ascii', errors='ignore').strip().strip('\x00')
    except struct.error:
        logger.warning(f"Could not unpack header at position {start_pos}. Not enough data.")
        return None, None, None

    # Use repr() for logging to make null bytes visible
    logger.debug(f"Read chunk header at pos {start_pos}: tag={repr(tag)}, length={length}")

    payload = data_stream.read(length)
    if len(payload) < length:
        logger.warning(f"Incomplete chunk payload for {repr(tag)} at pos {start_pos}. Expected {length}, got {len(payload)}.")
        return None, None, None

    # Padding is only applied to top-level chunks, not fields within a chunk.
    if padded:
        pad = _pad_len(length)
        if pad:
            data_stream.seek(pad, 1)
            logger.debug(f"Skipped {pad} padding bytes after {repr(tag)} chunk.")

    return tag, BytesIO(payload), header + payload

def _parse_otrk_payload(otrk_payload_stream):
    """Parses the fields within a single 'otrk' chunk's payload."""
    track_fields = {}
    payload_size = otrk_payload_stream.getbuffer().nbytes

    while otrk_payload_stream.tell() < payload_size:
        # Fields within an otrk are NOT padded.
        tag, field_payload_stream, _ = _read_chunk(otrk_payload_stream, padded=False)
        if tag is None:
            # This indicates we've likely reached the end of the stream cleanly.
            break
        
        # A list of known tags that are definitely UTF-16BE strings
        string_tags = ['pfil', 'tsng', 'tart', 'talb', 'tgen', 'tlen', 'ttyp', 'typ', 'tkey', 'tbpm', 'tbit', 'tcom', 'tgrp', 'ttyr']
        
        if tag in string_tags:
            track_fields[tag] = field_payload_stream.read().decode('utf-16-be', errors='ignore')
        else:
            # For other tags (like the boolean flags 'bply', etc.), just store the raw bytes.
            track_fields[tag] = field_payload_stream.read()
            
    return track_fields

def _parse_oent_payload(oent_payload_stream, store_raw_tracks=False):
    """Parses the 'otrk' chunks within an 'oent' chunk's payload."""
    tracks = []
    while True:
        tag, otrk_payload_stream, raw_otrk_chunk = _read_chunk(oent_payload_stream)
        if tag is None:
            break

        if tag == 'otrk':
            parsed_track = _parse_otrk_payload(otrk_payload_stream)
            if store_raw_tracks:
                parsed_track['__raw_chunk'] = raw_otrk_chunk
            tracks.append(parsed_track)
            
    return {'tracks': tracks}

def parse_serato_database(db_path):
    """
    Parses the entire Serato database file, handling 'otrk' and 'trk' pairs
    with robust error handling.
    """
    logger.info(f"--- Starting Serato Database Parse: {db_path} ---")
    final_data = {'tracks': []}
    last_parsed_otrk = None

    try:
        if not os.path.exists(db_path):
            logger.error(f"Database file not found at {db_path}")
            return None
        
        with open(db_path, 'rb') as f:
            db_content = BytesIO(f.read())
        
        logger.info(f"Successfully read {db_content.getbuffer().nbytes} bytes from the database file.")

        # Handle the version chunk first.
        vrsn_tag, _, vrsn_raw = _read_chunk(db_content)
        if vrsn_tag == 'vrsn':
            final_data['vrsn_header'] = vrsn_raw[:8]
            final_data['vrsn_data'] = vrsn_raw[8:]
            logger.info(f"Parsed 'vrsn' chunk. Size: {len(vrsn_raw)-8} bytes.")
        else:
            logger.warning("First chunk was not 'vrsn'. Resetting stream to parse from beginning.")
            db_content.seek(0)

        # Main loop to process chunks
        while db_content.tell() < db_content.getbuffer().nbytes:
            current_pos = db_content.tell()
            tag, payload_stream, raw_chunk = _read_chunk(db_content, padded=True)

            if tag is None:
                logger.warning(f"Reading chunk at position {current_pos} failed. Attempting to recover.")
                # Recovery: advance one byte and try to find the next chunk
                db_content.seek(current_pos + 1)
                continue

            # If we have a pending 'otrk' and the new chunk is NOT its 'trk' pair,
            # finalize the pending one before processing the new chunk.
            if last_parsed_otrk and tag != 'trk':
                if last_parsed_otrk.get('pfil'):
                    logger.info(f"Finalizing standalone 'otrk' from pos {last_parsed_otrk['__parse_pos']}.")
                    final_data['tracks'].append(last_parsed_otrk)
                else:
                    logger.warning(f"Discarding standalone 'otrk' from pos {last_parsed_otrk['__parse_pos']} because it has no 'pfil'.")
                last_parsed_otrk = None

            # --- Process the current chunk ---
            if tag == 'otrk':
                parsed_track = _parse_otrk_payload(payload_stream)
                parsed_track['__raw_chunk'] = raw_chunk
                parsed_track['__parse_pos'] = current_pos
                last_parsed_otrk = parsed_track
                logger.debug(f"Parsed and stored temporary 'otrk' from pos {current_pos}.")

            elif tag == 'trk':
                if last_parsed_otrk:
                    # This 'trk' belongs to the previous 'otrk'.
                    # We treat its payload as an opaque data blob and do not parse it.
                    # We just append its raw chunk data for preservation.
                    last_parsed_otrk['__raw_chunk'] += raw_chunk
                    logger.debug(f"Found and merged 'trk' pair at pos {current_pos} for 'otrk' at pos {last_parsed_otrk['__parse_pos']}.")

                    # The pair is now complete. Validate and finalize it.
                    if last_parsed_otrk.get('pfil'):
                        final_data['tracks'].append(last_parsed_otrk)
                        logger.info(f"Finalized 'otrk'/'trk' pair. Found pfil: {last_parsed_otrk.get('pfil')}")
                    else:
                        logger.warning(f"Discarding 'otrk'/'trk' pair from pos {last_parsed_otrk['__parse_pos']} because it has no 'pfil'.")
                    
                    last_parsed_otrk = None # Reset for the next track.
                else:
                    logger.warning(f"Encountered orphan 'trk' chunk at pos {current_pos}. Skipping.")
            
            else:
                # This handles chunks that are not 'vrsn', 'otrk', or 'trk'.
                logger.warning(f"Encountered and skipped unexpected chunk type '{tag}' at position {current_pos}.")

        # After the loop, if a standalone 'otrk' was the last chunk in the file, finalize it.
        if last_parsed_otrk:
            if last_parsed_otrk.get('pfil'):
                logger.info(f"Finalizing last standalone 'otrk' from pos {last_parsed_otrk['__parse_pos']}.")
                final_data['tracks'].append(last_parsed_otrk)
            else:
                logger.warning(f"Discarding last standalone 'otrk' from pos {last_parsed_otrk['__parse_pos']} because it has no 'pfil'.")

        logger.info(f"--- Parse Complete. Found {len(final_data['tracks'])} tracks. ---")
        return final_data

    except Exception as e:
        logger.error(f"An unhandled exception occurred during parsing: {e}", exc_info=True)
        return None

def main(db_path):
    """A simple test function to run the parser directly."""
    parsed_data = parse_serato_database(db_path)

    if parsed_data and parsed_data.get('tracks'):
        print(f"Successfully parsed {len(parsed_data['tracks'])} tracks.")
        print("--- First 5 Tracks ---")
        for i, track in enumerate(parsed_data['tracks'][:5]):
            print(f"\nTrack {i+1}:")
            print(f"  Song: {track.get('tsng', 'N/A')}")
            print(f"  Artist: {track.get('tart', 'N/A')}")
            print(f"  Path: {track.get('pfil', 'N/A')}")
    else:
        print("No tracks found or an error occurred during parsing.")
        if parsed_data is not None:
            print("Parsed data structure:", parsed_data)

if __name__ == "__main__":
    import configparser
    import os

    # The main sync script should be run, but this allows direct testing of the parser.
    # It will look for the config.ini in the same directory as the script.
    try:
        config = configparser.ConfigParser()
        # Assume config.ini is in the project root, which is the parent directory of this script.
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, 'config.ini')
        
        if not os.path.exists(config_path):
            print(f"Error: config.ini not found at {config_path}")
            sys.exit(1)
            
        config.read(config_path)
        database_file = config.get('paths', 'serato_database')
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        print(f"Error reading config file: {e}")
        sys.exit(1)

    print(f"Testing parser with database: {database_file}")
    parsed_data = parse_serato_database(database_file)

    if parsed_data and parsed_data.get('tracks'):
        print(f"\n--- Parser Test Result ---")
        print(f"Successfully parsed {len(parsed_data['tracks'])} tracks.")
        print("--- First 5 Tracks ---")
        for i, track in enumerate(parsed_data['tracks'][:5]):
            print(f"\nTrack {i+1}:")
            print(f"  Song: {track.get('tsng', 'N/A')}")
            print(f"  Artist: {track.get('tart', 'N/A')}")
            print(f"  Path: {track.get('pfil', 'N/A')}")
    else:
        print("\n--- Parser Test Result ---")
        print("No tracks found or an error occurred during parsing.")
        if parsed_data is not None:
            print("Parsed data structure:", parsed_data)
