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
            raise ValueError(
                f"max_val ({max_val}) must be greater than min_val ({min_val})"
            )

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

    def _map_data_to_colors(
        self,
        data: List[Union[int, float]],
        data_type: str,
        thresholds: Optional[Dict] = None,
    ) -> List[str]:
        """
        Generic method for mapping data values to colors.

        Args:
            data: List of numeric data values
            data_type: Type of data being mapped (for error messages)
            thresholds: Optional threshold configuration for normalization

        Returns:
            List of hex color strings corresponding to input data
        """
        if not data:
            return []

        # Filter out invalid data for min/max calculation
        valid_data = []
        for item in data:
            try:
                valid_data.append(float(item))
            except (ValueError, TypeError):
                pass

        # Determine min/max values for normalization
        if thresholds and "all" in thresholds and thresholds["all"]:
            min_val = float(thresholds["all"][0])
            max_val = float(thresholds["all"][-1])
        else:
            min_val = float(min(valid_data)) if valid_data else 0.0
            max_val = float(max(valid_data)) if valid_data else 1.0

        # Map each value to a color
        colors = []
        for value in data:
            try:
                color = self.map_value_to_color(float(value), min_val, max_val)
                colors.append(color)
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to map {data_type} value {value} to color: {e}")
                colors.append(self.palette.white)  # Default to white for invalid data

        return colors

    def map_synapse_colors(
        self, synapse_data: List[Union[int, float]], thresholds: Optional[Dict] = None
    ) -> List[str]:
        """
        Map synapse count data to colors.

        Args:
            synapse_data: List of synapse counts
            thresholds: Optional threshold configuration for normalization

        Returns:
            List of hex color strings corresponding to input data
        """
        return self._map_data_to_colors(synapse_data, "synapse count", thresholds)

    def map_neuron_colors(
        self, neuron_data: List[Union[int, float]], thresholds: Optional[Dict] = None
    ) -> List[str]:
        """
        Map neuron count data to colors.

        Args:
            neuron_data: List of neuron counts
            thresholds: Optional threshold configuration for normalization

        Returns:
            List of hex color strings corresponding to input data
        """
        return self._map_data_to_colors(neuron_data, "neuron count", thresholds)

    def color_for_status(self, status: str) -> str:
        """
        Get the appropriate color for a hexagon status.

        Args:
            status: Status string ('has_data', 'no_data', 'not_in_region', etc.)

        Returns:
            Hex color string
        """
        state_colors = self.palette.state_colors()

        if status == "not_in_region":
            return state_colors["dark_gray"]
        elif status == "no_data":
            return state_colors["white"]
        else:
            # For 'has_data' or unknown status, return white as default
            return state_colors["white"]

    def jinja_filters(self) -> Dict[str, Any]:
        """
        Get Jinja2 filter functions for use in templates.

        Returns:
            Dictionary of filter name to function mappings
        """
        return {
            "synapses_to_colors": self.map_synapse_colors,
            "neurons_to_colors": self.map_neuron_colors,
        }

    def map_regional_synapse_colors(
        self, synapses_list: List[float], region: str, min_max_data: Dict[str, Any]
    ) -> List[str]:
        """
        Convert synapses_list to synapse_colors using region-specific normalization.

        Args:
            synapses_list: List of synapse counts per layer
            region: Region name (ME, LO, LOP)
            min_max_data: Dict containing min/max values per region

        Returns:
            List of color hex codes
        """
        if not synapses_list or not min_max_data:
            return ["#ffffff"] * len(synapses_list)

        syn_min = float(min_max_data.get("min_syn_region", {}).get(region, 0.0))
        syn_max = float(min_max_data.get("max_syn_region", {}).get(region, 0.0))

        colors = []
        for syn_val in synapses_list:
            if syn_val > 0:
                color = self.map_value_to_color(syn_val, syn_min, syn_max)
            else:
                color = "#ffffff"
            colors.append(color)

        return colors

    def map_regional_neuron_colors(
        self, neurons_list: List[int], region: str, min_max_data: Dict[str, Any]
    ) -> List[str]:
        """
        Convert neurons_list to neuron_colors using region-specific normalization.

        Args:
            neurons_list: List of neuron counts per layer
            region: Region name (ME, LO, LOP)
            min_max_data: Dict containing min/max values per region

        Returns:
            List of color hex codes
        """
        if not neurons_list or not min_max_data:
            return ["#ffffff"] * len(neurons_list) if neurons_list else []

        cel_min = float(min_max_data.get("min_cells_region", {}).get(region, 0.0))
        cel_max = float(min_max_data.get("max_cells_region", {}).get(region, 0.0))

        colors = []
        for cel_val in neurons_list:
            if cel_val > 0:
                color = self.map_value_to_color(cel_val, cel_min, cel_max)
            else:
                color = "#ffffff"
            colors.append(color)

        return colors

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

    def legend_data(
        self, min_val: float, max_val: float, metric_type: str
    ) -> Dict[str, Any]:
        """
        Generate legend data for visualization.

        Args:
            min_val: Minimum value for the legend
            max_val: Maximum value for the legend
            metric_type: Type of metric ('synapse_density' or 'cell_count')

        Returns:
            Dictionary containing legend configuration
        """
        thresholds = self.palette.thresholds()
        colors = self.palette.all_colors()

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
            "colors": colors,
            "values": legend_values,
            "thresholds": thresholds,
            "min_val": min_val,
            "max_val": max_val,
            "metric_type": metric_type,
        }
