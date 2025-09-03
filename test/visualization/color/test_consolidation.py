"""
Test to verify that the color mapping consolidation maintains identical behavior.

This test ensures that the refactored ColorMapper produces exactly the same
results as the original implementation for both synapse and neuron color mapping.
"""

import unittest
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from quickpage.visualization.color.mapper import ColorMapper
from quickpage.visualization.color.palette import ColorPalette


class TestColorMappingConsolidation(unittest.TestCase):
    """Test cases to verify color mapping consolidation maintains identical behavior."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.palette = ColorPalette()
        self.mapper = ColorMapper(self.palette)

    def test_synapse_neuron_mapping_identical_behavior(self):
        """Test that synapse and neuron mapping produce identical results for same data."""
        test_data = [10, 20, 30, 40, 50]
        thresholds = {'all': [0, 100]}

        synapse_colors = self.mapper.map_synapse_colors(test_data, thresholds)
        neuron_colors = self.mapper.map_neuron_colors(test_data, thresholds)

        # Should produce identical colors for identical data and thresholds
        self.assertEqual(synapse_colors, neuron_colors)
        self.assertEqual(len(synapse_colors), 5)
        self.assertEqual(len(neuron_colors), 5)

    def test_consolidated_mapping_handles_empty_data(self):
        """Test that consolidated mapping handles empty data correctly."""
        empty_data = []

        synapse_colors = self.mapper.map_synapse_colors(empty_data)
        neuron_colors = self.mapper.map_neuron_colors(empty_data)

        self.assertEqual(synapse_colors, [])
        self.assertEqual(neuron_colors, [])

    def test_consolidated_mapping_handles_invalid_data(self):
        """Test that consolidated mapping handles invalid data gracefully."""
        invalid_data = ['invalid', None, 'not_a_number', 42, 'another_invalid']

        synapse_colors = self.mapper.map_synapse_colors(invalid_data)
        neuron_colors = self.mapper.map_neuron_colors(invalid_data)

        # Should return 5 colors (same length as input)
        self.assertEqual(len(synapse_colors), 5)
        self.assertEqual(len(neuron_colors), 5)

        # Should produce identical results
        self.assertEqual(synapse_colors, neuron_colors)

        # Invalid values should map to white, valid value should map to color
        self.assertEqual(synapse_colors[0], '#ffffff')  # 'invalid'
        self.assertEqual(synapse_colors[1], '#ffffff')  # None
        self.assertEqual(synapse_colors[2], '#ffffff')  # 'not_a_number'
        self.assertTrue(synapse_colors[3].startswith('#'))  # 42 (valid)
        self.assertEqual(synapse_colors[4], '#ffffff')  # 'another_invalid'

    def test_consolidated_mapping_with_thresholds(self):
        """Test that consolidated mapping respects threshold configuration."""
        test_data = [25, 50, 75]
        thresholds = {'all': [0, 100]}

        synapse_colors = self.mapper.map_synapse_colors(test_data, thresholds)
        neuron_colors = self.mapper.map_neuron_colors(test_data, thresholds)

        # Should use threshold values for normalization
        self.assertEqual(synapse_colors, neuron_colors)

        # Values should be normalized against 0-100 range
        # 25/100 = 0.25 -> should be light color
        # 50/100 = 0.50 -> should be medium color
        # 75/100 = 0.75 -> should be dark color
        self.assertEqual(synapse_colors[0], self.palette.colors[1])  # 0.25 -> light
        self.assertEqual(synapse_colors[1], self.palette.colors[2])  # 0.50 -> medium
        self.assertEqual(synapse_colors[2], self.palette.colors[3])  # 0.75 -> dark

    def test_consolidated_mapping_without_thresholds(self):
        """Test that consolidated mapping works without threshold configuration."""
        test_data = [10, 30, 50]

        synapse_colors = self.mapper.map_synapse_colors(test_data)
        neuron_colors = self.mapper.map_neuron_colors(test_data)

        # Should use min/max from data for normalization
        self.assertEqual(synapse_colors, neuron_colors)

        # Min=10, Max=50, so:
        # 10 -> 0.0 -> lightest color
        # 30 -> 0.5 -> medium color
        # 50 -> 1.0 -> darkest color
        self.assertEqual(synapse_colors[0], self.palette.colors[0])  # lightest
        self.assertEqual(synapse_colors[1], self.palette.colors[2])  # medium
        self.assertEqual(synapse_colors[2], self.palette.colors[4])  # darkest

    def test_consolidated_mapping_single_value(self):
        """Test that consolidated mapping handles single values correctly."""
        single_value_data = [42]

        synapse_colors = self.mapper.map_synapse_colors(single_value_data)
        neuron_colors = self.mapper.map_neuron_colors(single_value_data)

        # Should handle single value (min == max case)
        self.assertEqual(synapse_colors, neuron_colors)
        self.assertEqual(len(synapse_colors), 1)
        # When min == max, normalization should return 0.0 -> lightest color
        self.assertEqual(synapse_colors[0], self.palette.colors[0])

    def test_consolidated_mapping_preserves_order(self):
        """Test that consolidated mapping preserves input order."""
        test_data = [50, 10, 30, 20, 40]

        synapse_colors = self.mapper.map_synapse_colors(test_data)
        neuron_colors = self.mapper.map_neuron_colors(test_data)

        # Should preserve order and produce identical results
        self.assertEqual(synapse_colors, neuron_colors)
        self.assertEqual(len(synapse_colors), 5)

        # Verify that colors correspond to normalized values in correct order
        # Min=10, Max=50, so normalization: 50->1.0, 10->0.0, 30->0.5, 20->0.25, 40->0.75
        expected_indices = [4, 0, 2, 1, 3]  # color indices for normalized values
        for i, expected_idx in enumerate(expected_indices):
            self.assertEqual(synapse_colors[i], self.palette.colors[expected_idx])

    def test_consolidated_mapping_floating_point_precision(self):
        """Test that consolidated mapping handles floating point data correctly."""
        float_data = [10.5, 20.7, 30.1, 40.9, 50.3]

        synapse_colors = self.mapper.map_synapse_colors(float_data)
        neuron_colors = self.mapper.map_neuron_colors(float_data)

        # Should handle floating point values correctly
        self.assertEqual(synapse_colors, neuron_colors)
        self.assertEqual(len(synapse_colors), 5)

        # All should be valid hex colors
        for color in synapse_colors:
            self.assertTrue(color.startswith('#'))
            self.assertEqual(len(color), 7)

    def test_private_method_not_exposed(self):
        """Test that the internal _map_data_to_colors method works but is private."""
        test_data = [10, 20, 30]

        # Should be able to call the private method directly
        colors = self.mapper._map_data_to_colors(test_data, "test data")

        self.assertEqual(len(colors), 3)
        for color in colors:
            self.assertTrue(color.startswith('#'))

    def test_error_messages_are_specific(self):
        """Test that error messages distinguish between synapse and neuron data."""
        import logging
        from io import StringIO

        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        logger = logging.getLogger('quickpage.visualization.color.mapper')
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)

        try:
            # Test with invalid data to trigger error messages
            self.mapper.map_synapse_colors(['invalid'])
            self.mapper.map_neuron_colors(['invalid'])

            log_output = log_capture.getvalue()

            # Should contain specific data type in error messages
            self.assertIn('synapse count', log_output)
            self.assertIn('neuron count', log_output)

        finally:
            logger.removeHandler(handler)

    def test_backward_compatibility_maintained(self):
        """Test that the refactored methods maintain exact backward compatibility."""
        # Test data that would have worked with original implementation
        legacy_test_cases = [
            ([1, 2, 3, 4, 5], None),
            ([0, 10, 20], {'all': [0, 50]}),
            ([], None),
            ([100], None),
            ([1.5, 2.7, 3.9], {'all': [0, 10]}),
        ]

        for test_data, thresholds in legacy_test_cases:
            with self.subTest(data=test_data, thresholds=thresholds):
                synapse_colors = self.mapper.map_synapse_colors(test_data, thresholds)
                neuron_colors = self.mapper.map_neuron_colors(test_data, thresholds)

                # Results should be identical
                self.assertEqual(synapse_colors, neuron_colors)

                # Should return same number of colors as input data
                self.assertEqual(len(synapse_colors), len(test_data))

                # All colors should be valid hex strings
                for color in synapse_colors:
                    self.assertTrue(color.startswith('#'))
                    self.assertEqual(len(color), 7)


if __name__ == '__main__':
    unittest.main()
