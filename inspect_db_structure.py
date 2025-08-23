import struct
import configparser
import os

def _pad_len(n: int) -> int:
    return (-n) & 3

def inspect_database_structure(db_path):
    """
    Reads a Serato database file and prints the hierarchy of top-level chunks.
    """
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return

    print(f"Inspecting database structure for: {db_path}")
    try:
        with open(db_path, 'rb') as f:
            while True:
                header = f.read(8)
                if not header:
                    print("End of file reached.")
                    break
                
                if len(header) < 8:
                    print("Incomplete header found at end of file.")
                    break
                
                try:
                    tag, length = struct.unpack('>4sI', header)
                    # Attempt to decode, but handle potential errors if it's not valid ASCII
                    try:
                        tag_str = tag.decode('ascii')
                    except UnicodeDecodeError:
                        tag_str = f"Unknown ({tag.hex()})"

                    print(f"Found top-level chunk: Tag='{tag_str}', Length={length}")
                    
                    # Skip the chunk's content plus padding to move to the next chunk
                    current_pos = f.tell()
                    f.seek(length, 1)
                    pad = _pad_len(length)
                    if pad:
                        f.seek(pad, 1)
                    
                    # Sanity check to prevent infinite loops on malformed length
                    if f.tell() == current_pos:
                        print("Error: Chunk length is 0, cannot advance. Stopping.")
                        break

                except struct.error:
                    print("Struct unpack error, likely malformed chunk or end of file.")
                    break

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config_path = 'config.ini'
    if not os.path.exists(config_path):
        print(f"Error: Configuration file '{config_path}' not found.")
    else:
        config.read(config_path)
        if 'paths' in config and 'serato_database' in config['paths']:
                serato_database_path = config['paths']['serato_database']
                inspect_database_structure(serato_database_path)
        else:
            print("Error: 'paths' section or 'serato_database' key not found in config.ini")
