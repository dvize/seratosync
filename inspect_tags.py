import mutagen
import os
import pprint

def inspect_mp3_tags(file_path):
    """
    Opens an MP3 file and prints all of its ID3 tags, paying special
    attention to custom 'TXXX' tags that Serato might use.
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    print(f"--- Inspecting Tags for: {os.path.basename(file_path)} ---\n")
    
    try:
        audio = mutagen.File(file_path)
        if not audio.tags:
            print("No tags found in this file.")
            return

        # mutagen provides tags as a dictionary-like object
        # We can iterate through it to see everything.
        tags = audio.tags.items()
        
        if not tags:
            print("No tags found.")
            return

        print("Found the following tags:")
        for key, value in tags:
            # TXXX frames are for "User defined text information"
            # They have a 'desc' (description) and 'text' attribute.
            if key.startswith('TXXX'):
                print(f"  Tag: {key}")
                print(f"    Description: {value.desc}")
                # The text is often a list, so we'll print the list
                print(f"    Text: {value.text}")
            # Other common tags
            else:
                print(f"  Tag: {key}, Value: {value}")

    except Exception as e:
        print(f"An error occurred while reading the file: {e}")

if __name__ == "__main__":
    # Using a file from your library that has likely been analyzed by Serato
    target_file = "/Users/dvize/Music/MusicUnsorted/She Knows (Intro).mp3"
    inspect_mp3_tags(target_file)
