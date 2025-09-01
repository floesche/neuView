"""
Color utilities module containing utility functions for color processing and conversion.

This module extracts color-related functionality from the PageGenerator class
to improve code organization and reusability.
"""

from typing import List, Dict, Any


class ColorUtils:
    """Utility class for color-related operations."""

    def __init__(self, eyemap_generator=None):
        """
        Initialize ColorUtils with optional eyemap generator for color conversion.

        Args:
            eyemap_generator: EyemapGenerator instance for color mapping
        """
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
        if not synapses_list or not min_max_data or not self.eyemap_generator:
            return ["#ffffff"] * len(synapses_list)

        syn_min = float(min_max_data.get('min_syn_region', {}).get(region, 0.0))
        syn_max = float(min_max_data.get('max_syn_region', {}).get(region, 0.0))

        colors = []
        for syn_val in synapses_list:
            if syn_val > 0:
                color = self.eyemap_generator.color_mapper.map_value_to_color(syn_val, syn_min, syn_max)
            else:
                color = "#ffffff"
            colors.append(color)

        return colors

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
        if not neurons_list or not min_max_data or not self.eyemap_generator:
            return ["#ffffff"] * len(neurons_list) if neurons_list else []

        cel_min = float(min_max_data.get('min_cells_region', {}).get(region, 0.0))
        cel_max = float(min_max_data.get('max_cells_region', {}).get(region, 0.0))

        colors = []
        for cel_val in neurons_list:
            if cel_val > 0:
                color = self.eyemap_generator.color_mapper.map_value_to_color(cel_val, cel_min, cel_max)
            else:
                color = "#ffffff"
            colors.append(color)

        return colors

    @staticmethod
    def hex_to_rgb(hex_color: str) -> tuple:
        """
        Convert hex color to RGB tuple.

        Args:
            hex_color: Hex color string (e.g., "#ffffff")

        Returns:
            RGB tuple (r, g, b)
        """
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

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
        return f"#{r:02x}{g:02x}{b:02x}"

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
        if max_val == min_val:
            return 0.0
        return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))
