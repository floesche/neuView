"""
Test module for color management functionality.

This module contains unit tests for the color management components
used in hexagon grid visualizations, including ColorPalette and ColorMapper.

Test modules:
    test_palette: Tests for ColorPalette class
    test_mapper: Tests for ColorMapper class

Example:
    Run all color tests:
    >>> python -m pytest neuview/test/visualization/color/

    Run specific test module:
    >>> python -m pytest neuview/test/visualization/color/test_palette.py
    >>> python -m pytest neuview/test/visualization/color/test_mapper.py
"""

# Import test classes for easier access
from .test_palette import TestColorPalette
from .test_mapper import TestColorMapper

__all__ = ["TestColorPalette", "TestColorMapper"]
