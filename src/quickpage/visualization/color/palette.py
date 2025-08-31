"""
Color palette management for hexagon grid visualizations.

This module provides color definitions and mapping functionality for
visualizing data in hexagonal grids with consistent color schemes.
"""

from typing import List, Tuple


class ColorPalette:
    """
    Manages color definitions and provides color mapping functionality.

    This class encapsulates the color scheme used for hexagon grid
    visualizations, providing a centralized location for color management
    and consistent color mapping across different visualization contexts.
    """

    def __init__(self):
        """Initialize the color palette with default color schemes."""
        # 5-step red color scheme from lightest to darkest
        self.colors = [
            '#fee5d9',  # Lightest (0.0-0.2)
            '#fcbba1',  # Light (0.2-0.4)
            '#fc9272',  # Medium (0.4-0.6)
            '#ef6548',  # Dark (0.6-0.8)
            '#a50f15'   # Darkest (0.8-1.0)
        ]

        # RGB values for more precise color calculations
        self._color_values = [
            (254, 229, 217),  # Lightest (0.0-0.2)
            (252, 187, 161),  # Light (0.2-0.4)
            (252, 146, 114),  # Medium (0.4-0.6)
            (239, 101, 72),   # Dark (0.6-0.8)
            (165, 15, 21)     # Darkest (0.8-1.0)
        ]

        # Special state colors
        self.dark_gray = '#999999'  # Column doesn't exist in this region
        self.white = '#ffffff'      # Column exists but no data for current dataset
        self.light_gray = '#e0e0e0'  # Alternative gray for different states

        # Color thresholds for binning
        self._thresholds = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

    def value_to_color(self, normalized_value: float) -> str:
        """
        Convert normalized value (0-1) to one of 5 distinct colors from lightest to darkest red.

        This method maps continuous values to discrete color bins, providing
        clear visual distinction between different value ranges.

        Args:
            normalized_value: Value between 0 and 1

        Returns:
            Hex color string

        Raises:
            ValueError: If normalized_value is outside the range [0, 1]
        """
        if not 0 <= normalized_value <= 1:
            raise ValueError(f"normalized_value must be between 0 and 1, got {normalized_value}")

        # Determine which color bin the value falls into
        color_index = self._get_color_index(normalized_value)
        r, g, b = self._color_values[color_index]

        # Convert to hex
        return f"#{r:02x}{g:02x}{b:02x}"

    def _get_color_index(self, normalized_value: float) -> int:
        """
        Determine the color index for a given normalized value.

        Args:
            normalized_value: Value between 0 and 1

        Returns:
            Color index (0-4)
        """
        if normalized_value <= 0.2:
            return 0
        elif normalized_value <= 0.4:
            return 1
        elif normalized_value <= 0.6:
            return 2
        elif normalized_value <= 0.8:
            return 3
        else:
            return 4

    def get_color_at_index(self, index: int) -> str:
        """
        Get the hex color at a specific index.

        Args:
            index: Color index (0-4)

        Returns:
            Hex color string

        Raises:
            IndexError: If index is outside the valid range
        """
        if not 0 <= index < len(self.colors):
            raise IndexError(f"Color index must be between 0 and {len(self.colors)-1}, got {index}")

        return self.colors[index]

    def get_rgb_at_index(self, index: int) -> Tuple[int, int, int]:
        """
        Get the RGB values at a specific index.

        Args:
            index: Color index (0-4)

        Returns:
            RGB tuple (r, g, b)

        Raises:
            IndexError: If index is outside the valid range
        """
        if not 0 <= index < len(self._color_values):
            raise IndexError(f"Color index must be between 0 and {len(self._color_values)-1}, got {index}")

        return self._color_values[index]

    def get_all_colors(self) -> List[str]:
        """
        Get all colors in the palette.

        Returns:
            List of hex color strings
        """
        return self.colors.copy()

    def get_thresholds(self) -> List[float]:
        """
        Get the threshold values used for color binning.

        Returns:
            List of threshold values
        """
        return self._thresholds.copy()

    def get_state_colors(self) -> dict:
        """
        Get colors used for different hexagon states.

        Returns:
            Dictionary mapping state names to hex colors
        """
        return {
            'dark_gray': self.dark_gray,
            'white': self.white,
            'light_gray': self.light_gray
        }
