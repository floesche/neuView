"""
Color utilities compatibility wrapper.

This module provides a ColorUtils class that acts as a compatibility wrapper
around the modern ColorMapper and ColorPalette classes. This allows existing
code to continue working while migrating to the consolidated color system.
"""

from typing import List, Dict, Any
from .mapper import ColorMapper
from .palette import ColorPalette


class ColorUtils:
    """
    Compatibility wrapper for color-related operations.

    This class provides backward compatibility for the legacy ColorUtils interface
    while delegating to the modern ColorMapper and ColorPalette implementations.

    Note: This is a compatibility layer. New code should use ColorMapper directly.
    """

    def __init__(self, eyemap_generator=None):
        """
        Initialize ColorUtils with optional eyemap generator for color conversion.

        Args:
            eyemap_generator: EyemapGenerator instance (for compatibility, not used)
        """
        # Create our own color mapper instead of depending on eyemap_generator
        self.color_mapper = ColorMapper()
        self.palette = ColorPalette()
        # Store reference for compatibility, but don't use it
        self.eyemap_generator = eyemap_generator

    def synapses_to_colors(self, synapses_list: List[float], region: str, min_max_data: Dict[str, Any]) -> List[str]:
        """
        Convert synapses_list to synapse_colors using normalization.

        Args:
            synapses_list: List of synapse counts per layer
            region: Region name (ME, LO, LOP)
            min_max_data: Dict containing min/max values per region

        Returns:
            List of color hex codes
        """
        return self.color_mapper.map_regional_synapse_colors(synapses_list, region, min_max_data)

    def neurons_to_colors(self, neurons_list: List[int], region: str, min_max_data: Dict[str, Any]) -> List[str]:
        """
        Convert neurons_list to neuron_colors using normalization.

        Args:
            neurons_list: List of neuron counts per layer
            region: Region name (ME, LO, LOP)
            min_max_data: Dict containing min/max values per region

        Returns:
            List of color hex codes
        """
        return self.color_mapper.map_regional_neuron_colors(neurons_list, region, min_max_data)

    @staticmethod
    def hex_to_rgb(hex_color: str) -> tuple:
        """
        Convert hex color to RGB tuple.

        Args:
            hex_color: Hex color string (e.g., "#ffffff")

        Returns:
            RGB tuple (r, g, b)
        """
        return ColorPalette.hex_to_rgb(hex_color)

    @staticmethod
    def rgb_to_hex(r: int, g: int, b: int) -> str:
        """
        Convert RGB values to hex color string.

        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)

        Returns:
            Hex color string
        """
        return ColorPalette.rgb_to_hex(r, g, b)

    @staticmethod
    def normalize_color_value(value: float, min_val: float, max_val: float) -> float:
        """
        Normalize a value to 0-1 range for color mapping.

        Args:
            value: Value to normalize
            min_val: Minimum value in range
            max_val: Maximum value in range

        Returns:
            Normalized value between 0 and 1
        """
        return ColorMapper.normalize_color_value(value, min_val, max_val)
