"""
Configuration file handling for seratosync.

This module handles parsing and validation of configuration files that can be
used to set default paths for library-root and serato-root, making the tool
more convenient to use across different platforms.
"""

import json
import os
import platform
from pathlib import Path
from typing import Dict, Optional, Tuple


def get_default_config_path() -> Path:
    """
    Get the default configuration file path based on the operating system.
    
    Checks current working directory first, then falls back to platform-specific locations.
    
    Returns:
        Path to the default config file location
    """
    # First check current working directory (most portable)
    cwd_config = Path.cwd() / "config.json"
    if cwd_config.exists():
        return cwd_config
    
    # Fall back to platform-specific locations
    system = platform.system().lower()
    
    if system == "windows":
        # Windows: %APPDATA%/seratosync/config.json
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "seratosync" / "config.json"
        return Path.home() / "AppData" / "Roaming" / "seratosync" / "config.json"
    elif system == "darwin":
        # macOS: ~/Library/Application Support/seratosync/config.json
        return Path.home() / "Library" / "Application Support" / "seratosync" / "config.json"
    else:
        # Linux and others: ~/.config/seratosync/config.json
        return Path.home() / ".config" / "seratosync" / "config.json"


def get_config_file_path(config_path: Optional[str] = None) -> Path:
    """
    Get the configuration file path, using default if not specified.
    
    Args:
        config_path: Optional path to config file. If None, uses default location.
        
    Returns:
        Path to the configuration file
    """
    if config_path:
        return Path(config_path).resolve()
    return get_default_config_path()


def load_config(config_path: Optional[str] = None) -> Dict[str, str]:
    """
    Load configuration from a JSON file.
    
    Args:
        config_path: Optional path to config file. If None, uses default location.
        
    Returns:
        Dictionary containing configuration values
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is invalid JSON
    """
    config_file = get_config_file_path(config_path)
    
    if not config_file.exists():
        return {}
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Ensure config is a dictionary
    if not isinstance(config, dict):
        raise ValueError(f"Config file {config_file} must contain a JSON object")
    
    return config


def save_config(config: Dict[str, str], config_path: Optional[str] = None) -> None:
    """
    Save configuration to a JSON file.
    
    Args:
        config: Dictionary containing configuration values
        config_path: Optional path to config file. If None, uses default location.
    """
    config_file = get_config_file_path(config_path)
    
    # Create directory if it doesn't exist
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def validate_config_paths(config: Dict[str, str]) -> Tuple[bool, Optional[str]]:
    """
    Validate configuration paths.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_keys = ['library_root', 'serato_root']
    
    for key in required_keys:
        if key not in config:
            return False, f"Missing required key: {key}"
        
        path = Path(config[key])
        if not path.exists():
            return False, f"Path does not exist: {config[key]}"
        
        if key == 'library_root' and not path.is_dir():
            return False, f"Library root must be a directory: {config[key]}"
        
        if key == 'serato_root' and not path.is_dir():
            return False, f"Serato root must be a directory: {config[key]}"
    
    return True, None


def merge_with_args(config: Dict[str, str], args: Dict[str, str]) -> Dict[str, str]:
    """
    Merge configuration with command line arguments.
    Command line arguments take precedence over config file.
    
    Args:
        config: Configuration from file
        args: Command line arguments
        
    Returns:
        Merged configuration with args taking precedence
    """
    merged = config.copy()
    merged.update(args)
    return merged


def create_sample_config() -> Dict[str, str]:
    """
    Create a sample configuration with comments and examples.
    
    Returns:
        Sample configuration dictionary
    """
    return {
        "db": "/path/to/Database V2",
        "library_root": "/path/to/your/music/library",
        "serato_root": "/path/to/your/_Serato_",
        "exts": ".mp3,.m4a,.aac,.flac,.wav"
    }


def print_config_example() -> None:
    """Print an example configuration file."""
    import json
    
    sample_config = create_sample_config()
    print("# Serato Sync Configuration File")
    print("# This file allows you to set default paths for common use.")
    print("# Paths can be absolute or relative to this config file.")
    print("#")
    print("# The tool checks for config.json in this order:")
    print("# 1. Current working directory (./config.json) - most portable")
    print("# 2. Platform-specific user directory:")
    print("#    - Windows: %APPDATA%\\seratosync\\config.json")
    print("#    - macOS: ~/Library/Application Support/seratosync/config.json")
    print("#    - Linux: ~/.config/seratosync/config.json")
    print("#")
    print("# You can specify a custom config file location with:")
    print("#   python -m seratosync --config /path/to/config.json")
    print("#")
    print(json.dumps(sample_config, indent=2, ensure_ascii=False))
