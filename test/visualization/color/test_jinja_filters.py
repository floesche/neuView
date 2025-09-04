"""
Test to verify that Jinja filters work correctly after color mapping consolidation.

This test ensures that the Jinja filter functionality remains intact after
the ColorMapper refactoring that consolidated duplicate color mapping logic.
"""

import unittest
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from quickpage.visualization.color.mapper import ColorMapper
from quickpage.visualization.color.palette import ColorPalette


class TestJinjaFiltersAfterConsolidation(unittest.TestCase):
    """Test cases to verify Jinja filters work correctly after consolidation."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.palette = ColorPalette()
        self.mapper = ColorMapper(self.palette)
        self.filters = self.mapper.jinja_filters()

    def test_jinja_filters_created_successfully(self):
        """Test that Jinja filters are created without errors."""
        self.assertIsInstance(self.filters, dict)
        self.assertIn('synapses_to_colors', self.filters)
        self.assertIn('neurons_to_colors', self.filters)

        # Verify filters are callable
        self.assertTrue(callable(self.filters['synapses_to_colors']))
        self.assertTrue(callable(self.filters['neurons_to_colors']))

    def test_synapses_filter_basic_functionality(self):
        """Test that synapses_to_colors filter works correctly."""
        synapses_filter = self.filters['synapses_to_colors']

        test_data = [10, 20, 30, 40, 50]
        colors = synapses_filter(test_data)

        self.assertEqual(len(colors), 5)
        for color in colors:
            self.assertTrue(color.startswith('#'))
            self.assertEqual(len(color), 7)

        # Should produce same result as direct method call
        direct_colors = self.mapper.map_synapse_colors(test_data)
        self.assertEqual(colors, direct_colors)

    def test_neurons_filter_basic_functionality(self):
        """Test that neurons_to_colors filter works correctly."""
        neurons_filter = self.filters['neurons_to_colors']

        test_data = [5, 15, 25, 35, 45]
        colors = neurons_filter(test_data)

        self.assertEqual(len(colors), 5)
        for color in colors:
            self.assertTrue(color.startswith('#'))
            self.assertEqual(len(color), 7)

        # Should produce same result as direct method call
        direct_colors = self.mapper.map_neuron_colors(test_data)
        self.assertEqual(colors, direct_colors)

    def test_filters_handle_empty_data(self):
        """Test that filters handle empty data correctly."""
        synapses_filter = self.filters['synapses_to_colors']
        neurons_filter = self.filters['neurons_to_colors']

        empty_data = []

        synapse_colors = synapses_filter(empty_data)
        neuron_colors = neurons_filter(empty_data)

        self.assertEqual(synapse_colors, [])
        self.assertEqual(neuron_colors, [])

    def test_filters_handle_invalid_data(self):
        """Test that filters handle invalid data gracefully."""
        synapses_filter = self.filters['synapses_to_colors']
        neurons_filter = self.filters['neurons_to_colors']

        invalid_data = ['invalid', None, 42, 'not_a_number']

        synapse_colors = synapses_filter(invalid_data)
        neuron_colors = neurons_filter(invalid_data)

        # Should return same length as input
        self.assertEqual(len(synapse_colors), 4)
        self.assertEqual(len(neuron_colors), 4)

        # Should match direct method calls
        direct_synapse = self.mapper.map_synapse_colors(invalid_data)
        direct_neuron = self.mapper.map_neuron_colors(invalid_data)

        self.assertEqual(synapse_colors, direct_synapse)
        self.assertEqual(neuron_colors, direct_neuron)

    def test_filters_produce_identical_results_for_same_data(self):
        """Test that both filters produce identical results for same input."""
        synapses_filter = self.filters['synapses_to_colors']
        neurons_filter = self.filters['neurons_to_colors']

        test_data = [10, 20, 30, 40, 50]

        synapse_colors = synapses_filter(test_data)
        neuron_colors = neurons_filter(test_data)

        # Should produce identical results since underlying logic is consolidated
        self.assertEqual(synapse_colors, neuron_colors)

    def test_filters_with_various_data_types(self):
        """Test filters with different numeric data types."""
        synapses_filter = self.filters['synapses_to_colors']
        neurons_filter = self.filters['neurons_to_colors']

        # Test with integers
        int_data = [1, 2, 3, 4, 5]
        int_synapse_colors = synapses_filter(int_data)
        int_neuron_colors = neurons_filter(int_data)

        self.assertEqual(len(int_synapse_colors), 5)
        self.assertEqual(len(int_neuron_colors), 5)
        self.assertEqual(int_synapse_colors, int_neuron_colors)

        # Test with floats
        float_data = [1.5, 2.7, 3.2, 4.8, 5.1]
        float_synapse_colors = synapses_filter(float_data)
        float_neuron_colors = neurons_filter(float_data)

        self.assertEqual(len(float_synapse_colors), 5)
        self.assertEqual(len(float_neuron_colors), 5)
        self.assertEqual(float_synapse_colors, float_neuron_colors)

    def test_filters_maintain_performance(self):
        """Test that filters maintain good performance with larger datasets."""
        synapses_filter = self.filters['synapses_to_colors']
        neurons_filter = self.filters['neurons_to_colors']

        # Create larger dataset
        large_data = list(range(100))

        # Should complete without issues
        synapse_colors = synapses_filter(large_data)
        neuron_colors = neurons_filter(large_data)

        self.assertEqual(len(synapse_colors), 100)
        self.assertEqual(len(neuron_colors), 100)
        self.assertEqual(synapse_colors, neuron_colors)

        # Verify all are valid colors
        for color in synapse_colors[:10]:  # Check first 10 for efficiency
            self.assertTrue(color.startswith('#'))
            self.assertEqual(len(color), 7)

    def test_filter_integration_with_template_context(self):
        """Test that filters work correctly in a template-like context."""
        # Simulate how filters would be used in Jinja2 templates
        template_context = {
            'synapse_data': [15, 30, 45, 60, 75],
            'neuron_data': [5, 10, 15, 20, 25],
            'synapses_to_colors': self.filters['synapses_to_colors'],
            'neurons_to_colors': self.filters['neurons_to_colors']
        }

        # Apply filters as they would be in templates
        synapse_colors = template_context['synapses_to_colors'](template_context['synapse_data'])
        neuron_colors = template_context['neurons_to_colors'](template_context['neuron_data'])

        # Verify results
        self.assertEqual(len(synapse_colors), 5)
        self.assertEqual(len(neuron_colors), 5)

        # All should be valid hex colors
        for color_list in [synapse_colors, neuron_colors]:
            for color in color_list:
                self.assertTrue(color.startswith('#'))
                self.assertEqual(len(color), 7)

    def test_filter_consistency_across_multiple_calls(self):
        """Test that filters produce consistent results across multiple calls."""
        synapses_filter = self.filters['synapses_to_colors']
        neurons_filter = self.filters['neurons_to_colors']

        test_data = [25, 50, 75]

        # Call filters multiple times
        synapse_colors_1 = synapses_filter(test_data)
        synapse_colors_2 = synapses_filter(test_data)
        neuron_colors_1 = neurons_filter(test_data)
        neuron_colors_2 = neurons_filter(test_data)

        # Should produce identical results each time
        self.assertEqual(synapse_colors_1, synapse_colors_2)
        self.assertEqual(neuron_colors_1, neuron_colors_2)
        self.assertEqual(synapse_colors_1, neuron_colors_1)

    def test_filter_error_handling_isolation(self):
        """Test that filter errors don't affect other operations."""
        synapses_filter = self.filters['synapses_to_colors']
        neurons_filter = self.filters['neurons_to_colors']

        # Test with problematic data
        problematic_data = [float('inf'), float('-inf'), float('nan'), 42]

        # Should handle errors gracefully without crashing
        try:
            synapse_colors = synapses_filter(problematic_data)
            neuron_colors = neurons_filter(problematic_data)

            # Should return some result (even if some values are white/default)
            self.assertEqual(len(synapse_colors), 4)
            self.assertEqual(len(neuron_colors), 4)

        except Exception as e:
            # If there are exceptions, they should be controlled/expected
            self.fail(f"Filter should handle problematic data gracefully, but got: {e}")

    def test_backward_compatibility_of_filters(self):
        """Test that filters maintain backward compatibility."""
        # Test cases that would have worked before consolidation
        legacy_test_cases = [
            [1, 2, 3],
            [10.5, 20.7, 30.9],
            [100],
            [],
            [0, 50, 100]
        ]

        for test_data in legacy_test_cases:
            with self.subTest(data=test_data):
                synapse_colors = self.filters['synapses_to_colors'](test_data)
                neuron_colors = self.filters['neurons_to_colors'](test_data)

                # Should return correct number of colors
                self.assertEqual(len(synapse_colors), len(test_data))
                self.assertEqual(len(neuron_colors), len(test_data))

                # Should produce identical results (due to consolidation)
                self.assertEqual(synapse_colors, neuron_colors)

                # All colors should be valid
                for color in synapse_colors:
                    self.assertTrue(color.startswith('#'))
                    self.assertEqual(len(color), 7)


if __name__ == '__main__':
    unittest.main()
