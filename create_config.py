#!/usr/bin/env python3
"""
Helper script to create a seratosync configuration file.

This script helps users create a config file by prompting for paths
and validating them before saving.
"""

import json
import sys
from pathlib import Path
from seratosync.config import validate_config_paths


def prompt_path(description: str, default: str = "") -> str:
    """Prompt user for a path with optional default."""
    if default:
        response = input(f"{description} [{default}]: ").strip()
        return response if response else default
    else:
        while True:
            response = input(f"{description}: ").strip()
            if response:
                return response
            print("This field is required. Please enter a path.")


def main():
    """Main function to create config file."""
    print("Serato Sync Configuration File Creator")
    print("=" * 40)
    print()

    # Get paths from user
    config = {}

    print("Please enter the paths for your Serato setup:")
    print("(Use forward slashes '/' on all platforms)")
    print()

    config['db'] = prompt_path("Path to Serato 'Database V2' file")
    config['library_root'] = prompt_path("Path to your music library root folder")
    config['serato_root'] = prompt_path("Path to your _Serato_ folder")

    config['prefix'] = input("Path prefix (optional, press Enter to skip): ").strip() or None
    config['exts'] = input("Audio extensions (optional, press Enter for defaults): ").strip() or None

    # Remove None values
    config = {k: v for k, v in config.items() if v is not None}

    print()
    print("Configuration to be saved:")
    print(json.dumps(config, indent=2))
    print()

    # Validate paths
    is_valid, error_msg = validate_config_paths(config)
    if not is_valid:
        print(f"Error: {error_msg}")
        return 1

    # Confirm save
    default_path = Path.cwd() / "config.json"
    print(f"This will be saved to: {default_path}")
    print("(This is the most portable location - the config file will be in your current directory)")

    response = input("Save configuration? (y/N): ").strip().lower()
    if response not in ('y', 'yes'):
        print("Configuration not saved.")
        return 0

    # Save config to current directory
    try:
        with open(default_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"Configuration saved to: {default_path}")
        print()
        print("You can now run 'python -m seratosync' from this directory without arguments!")
        return 0
    except Exception as e:
        print(f"Error saving configuration: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
