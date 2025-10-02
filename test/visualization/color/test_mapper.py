"""
Unit tests for ColorMapper class.

This module tests the color mapping functionality including value normalization,
synapse and neuron color mapping, and Jinja2 filter creation.
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import patch

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from neuview.visualization.color.mapper import ColorMapper
from neuview.visualization.color.palette import ColorPalette


class TestColorMapper(unittest.TestCase):
    """Test cases for ColorMapper class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.palette = ColorPalette()
        self.mapper = ColorMapper(self.palette)

    def test_initialization_with_palette(self):
        """Test ColorMapper initialization with provided palette."""
        custom_palette = ColorPalette()
        mapper = ColorMapper(custom_palette)
        self.assertEqual(mapper.palette, custom_palette)

    def test_initialization_without_palette(self):
        """Test ColorMapper initialization with default palette."""
        mapper = ColorMapper()
        self.assertIsInstance(mapper.palette, ColorPalette)

    def test_normalize_value_valid_range(self):
        """Test normalize_value with valid inputs."""
        # Test normal range
        self.assertEqual(self.mapper.normalize_value(5, 0, 10), 0.5)
        self.assertEqual(self.mapper.normalize_value(0, 0, 10), 0.0)
        self.assertEqual(self.mapper.normalize_value(10, 0, 10), 1.0)

        # Test negative ranges
        self.assertEqual(self.mapper.normalize_value(-5, -10, 0), 0.5)

        # Test floating point values
        self.assertAlmostEqual(self.mapper.normalize_value(2.5, 0, 10), 0.25)

    def test_normalize_value_edge_cases(self):
        """Test normalize_value with edge cases."""
        # Test equal min and max
        self.assertEqual(self.mapper.normalize_value(5, 5, 5), 0.0)

        # Test values outside range (should be clamped)
        self.assertEqual(self.mapper.normalize_value(-5, 0, 10), 0.0)
        self.assertEqual(self.mapper.normalize_value(15, 0, 10), 1.0)

    def test_normalize_value_invalid_range(self):
        """Test normalize_value with invalid range."""
        with self.assertRaises(ValueError):
            self.mapper.normalize_value(5, 10, 5)  # max < min

    def test_map_value_to_color(self):
        """Test map_value_to_color method."""
        # Test with known values
        color = self.mapper.map_value_to_color(5, 0, 10)
        expected_color = self.palette.value_to_color(0.5)
        self.assertEqual(color, expected_color)

        # Test edge cases
        color_min = self.mapper.map_value_to_color(0, 0, 10)
        self.assertEqual(color_min, self.palette.colors[0])

        color_max = self.mapper.map_value_to_color(10, 0, 10)
        self.assertEqual(color_max, self.palette.colors[-1])

    def test_map_synapse_colors_empty_data(self):
        """Test map_synapse_colors with empty data."""
        result = self.mapper.map_synapse_colors([])
        self.assertEqual(result, [])

    def test_map_synapse_colors_with_thresholds(self):
        """Test map_synapse_colors with threshold configuration."""
        synapse_data = [10, 20, 30, 40, 50]
        thresholds = {"all": [0, 100]}

        colors = self.mapper.map_synapse_colors(synapse_data, thresholds)

        self.assertEqual(len(colors), len(synapse_data))
        # All colors should be valid hex colors
        for color in colors:
            self.assertTrue(color.startswith("#"))
            self.assertEqual(len(color), 7)

    def test_map_synapse_colors_without_thresholds(self):
        """Test map_synapse_colors without threshold configuration."""
        synapse_data = [10, 20, 30, 40, 50]

        colors = self.mapper.map_synapse_colors(synapse_data)

        self.assertEqual(len(colors), len(synapse_data))
        # Should use min/max from data
        self.assertEqual(colors[0], self.palette.colors[0])  # Min value -> lightest
        self.assertEqual(colors[-1], self.palette.colors[-1])  # Max value -> darkest

    def test_map_synapse_colors_invalid_data(self):
        """Test map_synapse_colors with invalid data."""
        with patch.object(
            self.mapper, "map_value_to_color", side_effect=ValueError("Invalid value")
        ):
            synapse_data = ["invalid", 20, None]
            colors = self.mapper.map_synapse_colors(synapse_data)

            # Should handle errors gracefully
            self.assertEqual(len(colors), 3)

    def test_map_neuron_colors_empty_data(self):
        """Test map_neuron_colors with empty data."""
        result = self.mapper.map_neuron_colors([])
        self.assertEqual(result, [])

    def test_map_neuron_colors_with_thresholds(self):
        """Test map_neuron_colors with threshold configuration."""
        neuron_data = [5, 15, 25, 35, 45]
        thresholds = {"all": [0, 50]}

        colors = self.mapper.map_neuron_colors(neuron_data, thresholds)

        self.assertEqual(len(colors), len(neuron_data))
        # All colors should be valid hex colors
        for color in colors:
            self.assertTrue(color.startswith("#"))
            self.assertEqual(len(color), 7)

    def test_map_neuron_colors_without_thresholds(self):
        """Test map_neuron_colors without threshold configuration."""
        neuron_data = [5, 15, 25, 35, 45]

        colors = self.mapper.map_neuron_colors(neuron_data)

        self.assertEqual(len(colors), len(neuron_data))
        # Should use min/max from data
        self.assertEqual(colors[0], self.palette.colors[0])  # Min value -> lightest
        self.assertEqual(colors[-1], self.palette.colors[-1])  # Max value -> darkest

    def test_color_for_status(self):
        """Test color_for_status method."""
        # Test known statuses
        self.assertEqual(self.mapper.color_for_status("not_in_region"), "#999999")
        self.assertEqual(self.mapper.color_for_status("no_data"), "#ffffff")
        self.assertEqual(self.mapper.color_for_status("has_data"), "#ffffff")

        # Test unknown status (should default to white)
        self.assertEqual(self.mapper.color_for_status("unknown"), "#ffffff")

    def test_jinja_filters(self):
        """Test jinja_filters method."""
        filters = self.mapper.jinja_filters()

        # Test return type and content
        self.assertIsInstance(filters, dict)
        self.assertIn("synapses_to_colors", filters)
        self.assertIn("neurons_to_colors", filters)

        # Test that filters are callable
        self.assertTrue(callable(filters["synapses_to_colors"]))
        self.assertTrue(callable(filters["neurons_to_colors"]))

    def test_jinja_synapses_filter(self):
        """Test the synapses_to_colors Jinja2 filter."""
        filters = self.mapper.jinja_filters()
        synapse_filter = filters["synapses_to_colors"]

        # Test with valid data
        synapse_data = [10, 20, 30]
        colors = synapse_filter(synapse_data)

        self.assertEqual(len(colors), 3)
        for color in colors:
            self.assertTrue(color.startswith("#"))

    def test_jinja_neurons_filter(self):
        """Test the neurons_to_colors Jinja2 filter."""
        filters = self.mapper.jinja_filters()
        neuron_filter = filters["neurons_to_colors"]

        # Test with valid data
        neuron_data = [5, 15, 25]
        colors = neuron_filter(neuron_data)

        self.assertEqual(len(colors), 3)
        for color in colors:
            self.assertTrue(color.startswith("#"))

    def test_legend_data(self):
        """Test legend_data method."""
        legend_data = self.mapper.legend_data(0, 100, "synapse_density")

        # Test return type and required keys
        self.assertIsInstance(legend_data, dict)
        required_keys = {
            "colors",
            "values",
            "thresholds",
            "min_val",
            "max_val",
            "metric_type",
        }
        self.assertEqual(set(legend_data.keys()), required_keys)

        # Test values
        self.assertEqual(legend_data["min_val"], 0)
        self.assertEqual(legend_data["max_val"], 100)
        self.assertEqual(legend_data["metric_type"], "synapse_density")

        # Test array lengths
        self.assertEqual(len(legend_data["colors"]), 5)
        self.assertEqual(len(legend_data["values"]), 6)
        self.assertEqual(len(legend_data["thresholds"]), 6)

    def test_legend_data_equal_min_max(self):
        """Test legend_data with equal min and max values."""
        legend_data = self.mapper.legend_data(50, 50, "cell_count")

        # Should handle equal values gracefully
        self.assertEqual(legend_data["min_val"], 50)
        self.assertEqual(legend_data["max_val"], 50)

        # All legend values should be the same
        for value in legend_data["values"]:
            self.assertEqual(value, 50)

    def test_color_mapping_consistency(self):
        """Test that color mapping is consistent across different methods."""
        test_value = 25
        min_val, max_val = 0, 50

        # Get color through direct mapping
        direct_color = self.mapper.map_value_to_color(test_value, min_val, max_val)

        # Get color through synapse mapping
        synapse_colors = self.mapper.map_synapse_colors(
            [test_value], {"all": [min_val, max_val]}
        )

        # Get color through neuron mapping
        neuron_colors = self.mapper.map_neuron_colors(
            [test_value], {"all": [min_val, max_val]}
        )

        # All should produce the same color for the same normalized value
        self.assertEqual(direct_color, synapse_colors[0])
        self.assertEqual(direct_color, neuron_colors[0])

    def test_error_handling_in_color_mapping(self):
        """Test error handling in color mapping methods."""
        # Test with mixed valid and invalid data
        mixed_data = [10, "invalid", 30, None, 50]

        # Should not raise exceptions
        synapse_colors = self.mapper.map_synapse_colors(mixed_data)
        neuron_colors = self.mapper.map_neuron_colors(mixed_data)

        # Should return a list of the same length
        self.assertEqual(len(synapse_colors), len(mixed_data))
        self.assertEqual(len(neuron_colors), len(mixed_data))

    def test_performance_with_large_datasets(self):
        """Test performance with large datasets."""
        # Create large dataset
        large_data = list(range(1000))

        # Should complete without timeout (basic performance test)
        colors = self.mapper.map_synapse_colors(large_data)

        self.assertEqual(len(colors), 1000)
        # All should be valid colors
        for color in colors[:10]:  # Check first 10 for efficiency
            self.assertTrue(color.startswith("#"))
            self.assertEqual(len(color), 7)


if __name__ == "__main__":
    unittest.main()
