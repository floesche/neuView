"""
Color management module for hexagon grid visualizations.

This module provides color palette management and mapping functionality
for consistent color schemes across hexagonal grid visualizations.

Classes:
    ColorPalette: Manages color definitions and basic color operations
    ColorMapper: Handles advanced color mapping logic for different data types

Example:
    >>> from quickpage.visualization.color import ColorPalette, ColorMapper
    >>>
    >>> # Create color palette and mapper
    >>> palette = ColorPalette()
    >>> mapper = ColorMapper(palette)
    >>>
    >>> # Map a value to color
    >>> color = palette.value_to_color(0.75)  # Returns dark red
    >>>
    >>> # Map synapse data to colors
    >>> synapse_counts = [10, 25, 40, 55, 70]
    >>> colors = mapper.map_synapse_colors(synapse_counts)
"""

from .palette import ColorPalette
from .mapper import ColorMapper
from .utils import ColorUtils

__all__ = ['ColorPalette', 'ColorMapper', 'ColorUtils']
