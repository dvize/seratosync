import os
import pprint

def scan_music_folder(root_path, max_depth=0, min_tracks=1):
    """
    Scans a music folder and returns a dictionary mapping subfolders to music files.

    Args:
        root_path (str): The absolute path to the music folder.
        max_depth (int): Maximum folder depth for crate creation (0 = no limit)
        min_tracks (int): Minimum tracks required to create a crate

    Returns:
        dict: A dictionary where keys are relative folder paths (potential crates)
              and values are lists of absolute paths to music files within them.
    """
    if not os.path.isdir(root_path):
        print(f"Error: Directory not found at {root_path}")
        return {}

    music_map = {}
    supported_extensions = ('.mp3', '.wav', '.flac', '.aif', '.aiff', '.m4a', '.ogg')

    for dirpath, _, filenames in os.walk(root_path):
        music_files = []
        for filename in filenames:
            if filename.lower().endswith(supported_extensions):
                # We store the full path to the file
                music_files.append(os.path.join(dirpath, filename))

        if music_files and len(music_files) >= min_tracks:
            # The crate name will be the folder's path relative to the root
            crate_name = os.path.relpath(dirpath, root_path)
            if crate_name == '.':
                # For files in the root of the music folder, use the folder's name
                crate_name = os.path.basename(root_path)
            
            # Check depth limit
            if max_depth > 0:
                depth = len(crate_name.split(os.sep)) if crate_name != '.' else 1
                if depth > max_depth:
                    continue
            
            music_map[crate_name] = music_files

    return music_map

if __name__ == "__main__":
    music_folder_path = "/Users/dvize/Music"
    print(f"Scanning music folder: {music_folder_path}\\n")
    
    music_library = scan_music_folder(music_folder_path)

    if music_library:
        print(f"Found {len(music_library)} folders containing music files.")
        print("--- Here is an example from one folder ---")
        
        # Get the first crate from the library to show as an example
        example_crate = list(music_library.keys())[0]
        example_files = music_library[example_crate]

        print(f"Crate Name: '{example_crate}'")
        print(f"Found {len(example_files)} music file(s) in this crate.")
        print("First 5 files:")
        pprint.pprint(example_files[:5])
    else:
        print("No music files found or the directory does not exist.")
