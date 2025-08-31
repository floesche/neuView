"""
Color mapping functionality for hexagon grid visualizations.

This module provides specialized color mapping logic for different data types
(synapses, neurons) with support for threshold-based coloring and normalization.
"""

from typing import List, Dict, Optional, Union, Any
import logging

from .palette import ColorPalette

logger = logging.getLogger(__name__)


class ColorMapper:
    """
    Handles color mapping logic for different data types in hexagon visualizations.

    This class provides specialized methods for mapping synapse and neuron data
    to colors, with support for threshold-based normalization and different
    visualization modes.
    """

    def __init__(self, palette: Optional[ColorPalette] = None):
        """
        Initialize the color mapper.

        Args:
            palette: ColorPalette instance. If None, creates a default palette.
        """
        self.palette = palette or ColorPalette()

    def normalize_value(self, value: float, min_val: float, max_val: float) -> float:
        """
        Normalize a value to the range [0, 1].

        Args:
            value: Value to normalize
            min_val: Minimum value in the range
            max_val: Maximum value in the range

        Returns:
            Normalized value between 0 and 1

        Raises:
            ValueError: If max_val <= min_val
        """
        if max_val <= min_val:
            if max_val == min_val:
                return 0.0
            raise ValueError(f"max_val ({max_val}) must be greater than min_val ({min_val})")

        value_range = max_val - min_val
        normalized = (value - min_val) / value_range

        # Clamp to [0, 1] range
        return max(0.0, min(1.0, normalized))

    def map_value_to_color(self, value: float, min_val: float, max_val: float) -> str:
        """
        Map a single value to a color using normalization.

        Args:
            value: Value to map
            min_val: Minimum value for normalization
            max_val: Maximum value for normalization

        Returns:
            Hex color string
        """
        normalized = self.normalize_value(value, min_val, max_val)
        return self.palette.value_to_color(normalized)

    def map_synapse_colors(self, synapse_data: List[Union[int, float]],
                          thresholds: Optional[Dict] = None) -> List[str]:
        """
        Map synapse count data to colors.

        Args:
            synapse_data: List of synapse counts
            thresholds: Optional threshold configuration for normalization

        Returns:
            List of hex color strings corresponding to input data
        """
        if not synapse_data:
            return []

        # Filter out invalid data for min/max calculation
        valid_data = []
        for item in synapse_data:
            try:
                valid_data.append(float(item))
            except (ValueError, TypeError):
                pass

        # Determine min/max values for normalization
        if thresholds and 'all' in thresholds and thresholds['all']:
            min_val = float(thresholds['all'][0])
            max_val = float(thresholds['all'][-1])
        else:
            min_val = float(min(valid_data)) if valid_data else 0.0
            max_val = float(max(valid_data)) if valid_data else 1.0

        # Map each value to a color
        colors = []
        for count in synapse_data:
            try:
                color = self.map_value_to_color(float(count), min_val, max_val)
                colors.append(color)
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to map synapse count {count} to color: {e}")
                colors.append(self.palette.white)  # Default to white for invalid data

        return colors

    def map_neuron_colors(self, neuron_data: List[Union[int, float]],
                         thresholds: Optional[Dict] = None) -> List[str]:
        """
        Map neuron count data to colors.

        Args:
            neuron_data: List of neuron counts
            thresholds: Optional threshold configuration for normalization

        Returns:
            List of hex color strings corresponding to input data
        """
        if not neuron_data:
            return []

        # Filter out invalid data for min/max calculation
        valid_data = []
        for item in neuron_data:
            try:
                valid_data.append(float(item))
            except (ValueError, TypeError):
                pass

        # Determine min/max values for normalization
        if thresholds and 'all' in thresholds and thresholds['all']:
            min_val = float(thresholds['all'][0])
            max_val = float(thresholds['all'][-1])
        else:
            min_val = float(min(valid_data)) if valid_data else 0.0
            max_val = float(max(valid_data)) if valid_data else 1.0

        # Map each value to a color
        colors = []
        for count in neuron_data:
            try:
                color = self.map_value_to_color(float(count), min_val, max_val)
                colors.append(color)
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to map neuron count {count} to color: {e}")
                colors.append(self.palette.white)  # Default to white for invalid data

        return colors

    def get_color_for_status(self, status: str) -> str:
        """
        Get the appropriate color for a hexagon status.

        Args:
            status: Status string ('has_data', 'no_data', 'not_in_region', etc.)

        Returns:
            Hex color string
        """
        state_colors = self.palette.get_state_colors()

        if status == 'not_in_region':
            return state_colors['dark_gray']
        elif status == 'no_data':
            return state_colors['white']
        else:
            # For 'has_data' or unknown status, return white as default
            return state_colors['white']

    def create_jinja_filters(self) -> Dict[str, callable]:
        """
        Create Jinja2 filter functions for use in templates.

        Returns:
            Dictionary of filter name to function mappings
        """
        def synapses_to_colors(synapse_list: List[Union[int, float]]) -> List[str]:
            """
            Jinja2 filter to convert synapse counts to colors.

            Args:
                synapse_list: List of synapse counts

            Returns:
                List of hex color strings
            """
            return self.map_synapse_colors(synapse_list)

        def neurons_to_colors(neuron_list: List[Union[int, float]]) -> List[str]:
            """
            Jinja2 filter to convert neuron counts to colors.

            Args:
                neuron_list: List of neuron counts

            Returns:
                List of hex color strings
            """
            return self.map_neuron_colors(neuron_list)

        return {
            'synapses_to_colors': synapses_to_colors,
            'neurons_to_colors': neurons_to_colors
        }

    def get_legend_data(self, min_val: float, max_val: float,
                       metric_type: str) -> Dict[str, Any]:
        """
        Generate legend data for visualization.

        Args:
            min_val: Minimum value for the legend
            max_val: Maximum value for the legend
            metric_type: Type of metric ('synapse_density' or 'cell_count')

        Returns:
            Dictionary containing legend configuration
        """
        thresholds = self.palette.get_thresholds()
        colors = self.palette.get_all_colors()

        # Calculate actual values for each threshold
        value_range = max_val - min_val if max_val > min_val else 1
        legend_values = []

        for threshold in thresholds:
            if max_val == min_val:
                actual_value = min_val
            else:
                actual_value = min_val + (threshold * value_range)
            legend_values.append(actual_value)

        return {
            'colors': colors,
            'values': legend_values,
            'thresholds': thresholds,
            'min_val': min_val,
            'max_val': max_val,
            'metric_type': metric_type
        }
