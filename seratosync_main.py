#!/usr/bin/env python3
"""
Main entry point for seratosync.

This script provides a backward-compatible entry point for users who expect
to run the script directly rather than as a module.
"""

import sys
from seratosync.cli import main

if __name__ == "__main__":
    sys.exit(main())
