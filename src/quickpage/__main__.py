"""
Main entry point for the QuickPage CLI application.

This module provides the command-line interface for QuickPage using the
simplified architecture while maintaining full backward compatibility.
"""

import sys
from .cli import main

if __name__ == '__main__':
    main()
