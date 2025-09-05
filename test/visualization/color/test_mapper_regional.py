"""
Test suite for ColorMapper regional color mapping functionality.

This module tests the new regional color mapping methods added to ColorMapper
as part of the ColorUtils consolidation effort.
"""

import unittest
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from quickpage.visualization.color.mapper import ColorMapper
from quickpage.visualization.color.palette import ColorPalette


class TestColorMapperRegional(unittest.TestCase):
    """Test cases for ColorMapper regional color mapping methods."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.palette = ColorPalette()
        self.mapper = ColorMapper(self.palette)

    def test_map_regional_synapse_colors_basic(self):
        """Test basic regional synapse color mapping functionality."""
        synapses_list = [10, 25, 40, 55, 70]
        region = 'ME'
        min_max_data = {
            'min_syn_region': {'ME': 0, 'LO': 5, 'LOP': 10},
            'max_syn_region': {'ME': 100, 'LO': 80, 'LOP': 60}
        }

        colors = self.mapper.map_regional_synapse_colors(synapses_list, region, min_max_data)

        # Should return correct number of colors
        self.assertEqual(len(colors), 5)

        # All should be valid hex colors
        for color in colors:
            self.assertTrue(color.startswith('#'))
            self.assertEqual(len(color), 7)

        # Should use ME region's min/max (0-100)
        # Values should map to appropriate color intensities
        expected_colors = [
            self.palette.colors[0],  # 10/100 = 0.1 -> lightest (0.0-0.2)
            self.palette.colors[1],  # 25/100 = 0.25 -> light (0.2-0.4)
            self.palette.colors[1],  # 40/100 = 0.4 -> light (0.2-0.4)
            self.palette.colors[2],  # 55/100 = 0.55 -> medium (0.4-0.6)
            self.palette.colors[3],  # 70/100 = 0.7 -> dark (0.6-0.8)
        ]

        self.assertEqual(colors, expected_colors)

    def test_map_regional_neuron_colors_basic(self):
        """Test basic regional neuron color mapping functionality."""
        neurons_list = [5, 15, 25, 35, 45]
        region = 'LO'
        min_max_data = {
            'min_cells_region': {'ME': 0, 'LO': 0, 'LOP': 5},
            'max_cells_region': {'ME': 50, 'LO': 60, 'LOP': 40}
        }

        colors = self.mapper.map_regional_neuron_colors(neurons_list, region, min_max_data)

        # Should return correct number of colors
        self.assertEqual(len(colors), 5)

        # All should be valid hex colors
        for color in colors:
            self.assertTrue(color.startswith('#'))
            self.assertEqual(len(color), 7)

        # Should use LO region's min/max (0-60)
        # Values should map to appropriate color intensities
        expected_colors = [
            self.palette.colors[0],  # 5/60 ≈ 0.08 -> lightest
            self.palette.colors[1],  # 15/60 = 0.25 -> light
            self.palette.colors[2],  # 25/60 ≈ 0.42 -> medium
            self.palette.colors[2],  # 35/60 ≈ 0.58 -> medium
            self.palette.colors[3],  # 45/60 = 0.75 -> dark
        ]

        self.assertEqual(colors, expected_colors)

    def test_regional_mapping_with_zero_values(self):
        """Test regional mapping handles zero values correctly."""
        synapses_with_zeros = [0, 10, 0, 20, 0]
        region = 'LOP'
        min_max_data = {
            'min_syn_region': {'LOP': 0},
            'max_syn_region': {'LOP': 50}
        }

        colors = self.mapper.map_regional_synapse_colors(synapses_with_zeros, region, min_max_data)

        # Zero values should map to white
        self.assertEqual(colors[0], '#ffffff')
        self.assertEqual(colors[2], '#ffffff')
        self.assertEqual(colors[4], '#ffffff')

        # Non-zero values should map to actual colors
        self.assertNotEqual(colors[1], '#ffffff')
        self.assertNotEqual(colors[3], '#ffffff')

        # Verify non-zero mappings
        self.assertEqual(colors[1], self.palette.colors[0])  # 10/50 = 0.2 -> lightest (threshold 0.2)
        self.assertEqual(colors[3], self.palette.colors[1])  # 20/50 = 0.4 -> light (threshold 0.4)

    def test_regional_mapping_empty_data(self):
        """Test regional mapping handles empty data correctly."""
        empty_synapses = []
        empty_neurons = []
        region = 'ME'
        min_max_data = {
            'min_syn_region': {'ME': 0},
            'max_syn_region': {'ME': 100},
            'min_cells_region': {'ME': 0},
            'max_cells_region': {'ME': 50}
        }

        synapse_colors = self.mapper.map_regional_synapse_colors(empty_synapses, region, min_max_data)
        neuron_colors = self.mapper.map_regional_neuron_colors(empty_neurons, region, min_max_data)

        self.assertEqual(synapse_colors, [])
        self.assertEqual(neuron_colors, [])

    def test_regional_mapping_missing_region_data(self):
        """Test regional mapping handles missing region data gracefully."""
        synapses_list = [10, 20, 30]
        neurons_list = [5, 10, 15]
        missing_region = 'UNKNOWN'
        min_max_data = {
            'min_syn_region': {'ME': 0},
            'max_syn_region': {'ME': 100},
            'min_cells_region': {'ME': 0},
            'max_cells_region': {'ME': 50}
        }

        synapse_colors = self.mapper.map_regional_synapse_colors(synapses_list, missing_region, min_max_data)
        neuron_colors = self.mapper.map_regional_neuron_colors(neurons_list, missing_region, min_max_data)

        # Should handle gracefully (using 0.0 as default min/max)
        self.assertEqual(len(synapse_colors), 3)
        self.assertEqual(len(neuron_colors), 3)

        # With min=max=0, all non-zero values should map to lightest color
        for color in synapse_colors:
            self.assertEqual(color, self.palette.colors[0])

        for color in neuron_colors:
            self.assertEqual(color, self.palette.colors[0])

    def test_regional_mapping_missing_min_max_data(self):
        """Test regional mapping handles missing min_max_data correctly."""
        synapses_list = [10, 20, 30]
        neurons_list = [5, 10, 15]
        region = 'ME'

        # Test with None
        synapse_colors_none = self.mapper.map_regional_synapse_colors(synapses_list, region, None)
        neuron_colors_none = self.mapper.map_regional_neuron_colors(neurons_list, region, None)

        expected_white_synapses = ['#ffffff'] * 3
        expected_white_neurons = ['#ffffff'] * 3

        self.assertEqual(synapse_colors_none, expected_white_synapses)
        self.assertEqual(neuron_colors_none, expected_white_neurons)

        # Test with empty dict
        synapse_colors_empty = self.mapper.map_regional_synapse_colors(synapses_list, region, {})
        neuron_colors_empty = self.mapper.map_regional_neuron_colors(neurons_list, region, {})

        self.assertEqual(synapse_colors_empty, expected_white_synapses)
        self.assertEqual(neuron_colors_empty, expected_white_neurons)

    def test_regional_mapping_different_regions(self):
        """Test regional mapping works correctly with different regions."""
        test_data = [10, 30, 50]
        min_max_data = {
            'min_syn_region': {'ME': 0, 'LO': 10, 'LOP': 20},
            'max_syn_region': {'ME': 100, 'LO': 40, 'LOP': 60},
            'min_cells_region': {'ME': 0, 'LO': 5, 'LOP': 10},
            'max_cells_region': {'ME': 50, 'LO': 35, 'LOP': 25}
        }

        # Test different regions produce different results
        me_colors = self.mapper.map_regional_synapse_colors(test_data, 'ME', min_max_data)
        lo_colors = self.mapper.map_regional_synapse_colors(test_data, 'LO', min_max_data)
        lop_colors = self.mapper.map_regional_synapse_colors(test_data, 'LOP', min_max_data)

        # Should be different due to different min/max ranges
        self.assertNotEqual(me_colors, lo_colors)
        self.assertNotEqual(me_colors, lop_colors)
        self.assertNotEqual(lo_colors, lop_colors)

        # All should be valid
        for colors in [me_colors, lo_colors, lop_colors]:
            self.assertEqual(len(colors), 3)
            for color in colors:
                self.assertTrue(color.startswith('#'))

    def test_regional_mapping_edge_cases(self):
        """Test regional mapping with edge case values."""
        edge_cases = [
            # Single value
            ([42], 'ME', {'min_syn_region': {'ME': 40}, 'max_syn_region': {'ME': 50}}),
            # All same values
            ([25, 25, 25], 'LO', {'min_syn_region': {'LO': 25}, 'max_syn_region': {'LO': 25}}),
            # Very large numbers
            ([1000000], 'LOP', {'min_syn_region': {'LOP': 0}, 'max_syn_region': {'LOP': 2000000}}),
            # Floating point values
            ([10.5, 20.7, 30.1], 'ME', {'min_syn_region': {'ME': 10}, 'max_syn_region': {'ME': 31}}),
        ]

        for data, region, min_max in edge_cases:
            with self.subTest(data=data, region=region):
                colors = self.mapper.map_regional_synapse_colors(data, region, min_max)

                # Should return correct number of colors
                self.assertEqual(len(colors), len(data))

                # All should be valid hex colors
                for color in colors:
                    self.assertTrue(color.startswith('#'))
                    self.assertEqual(len(color), 7)

    def test_normalize_color_value_static_method(self):
        """Test the static normalize_color_value method."""
        test_cases = [
            # (value, min_val, max_val, expected)
            (50, 0, 100, 0.5),
            (0, 0, 100, 0.0),
            (100, 0, 100, 1.0),
            (25, 0, 100, 0.25),
            (75, 0, 100, 0.75),
            (5, 0, 10, 0.5),
            (-5, -10, 0, 0.5),
            (15, 10, 20, 0.5),
            # Edge cases
            (50, 50, 50, 0.0),  # min == max
            (-5, 0, 10, 0.0),   # value < min (should clamp)
            (15, 0, 10, 1.0),   # value > max (should clamp)
        ]

        for value, min_val, max_val, expected in test_cases:
            with self.subTest(value=value, min_val=min_val, max_val=max_val):
                result = ColorMapper.normalize_color_value(value, min_val, max_val)
                self.assertAlmostEqual(result, expected, places=6)

    def test_regional_mapping_consistency_with_direct_mapping(self):
        """Test that regional mapping produces consistent results with direct mapping."""
        synapses = [20, 40, 60, 80]
        region = 'ME'
        min_max_data = {
            'min_syn_region': {'ME': 0},
            'max_syn_region': {'ME': 100}
        }

        # Get colors using regional mapping
        regional_colors = self.mapper.map_regional_synapse_colors(synapses, region, min_max_data)

        # Get colors using direct mapping with same min/max
        direct_colors = []
        for synapse_val in synapses:
            if synapse_val > 0:
                color = self.mapper.map_value_to_color(synapse_val, 0, 100)
            else:
                color = "#ffffff"
            direct_colors.append(color)

        # Should produce identical results
        self.assertEqual(regional_colors, direct_colors)

    def test_performance_with_large_regional_datasets(self):
        """Test regional mapping performance with large datasets."""
        # Create large dataset
        large_synapses = list(range(1000))
        large_neurons = list(range(500))
        region = 'ME'
        min_max_data = {
            'min_syn_region': {'ME': 0},
            'max_syn_region': {'ME': 999},
            'min_cells_region': {'ME': 0},
            'max_cells_region': {'ME': 499}
        }

        # Should complete without issues
        synapse_colors = self.mapper.map_regional_synapse_colors(large_synapses, region, min_max_data)
        neuron_colors = self.mapper.map_regional_neuron_colors(large_neurons, region, min_max_data)

        self.assertEqual(len(synapse_colors), 1000)
        self.assertEqual(len(neuron_colors), 500)

        # Verify first and last colors for synapses
        self.assertEqual(synapse_colors[0], '#ffffff')  # 0 -> white
        self.assertEqual(synapse_colors[-1], self.palette.colors[-1])  # 999 -> darkest

        # Verify first and last colors for neurons
        self.assertEqual(neuron_colors[0], '#ffffff')  # 0 -> white
        self.assertEqual(neuron_colors[-1], self.palette.colors[-1])  # 499 -> darkest

    def test_regional_mapping_maintains_order(self):
        """Test that regional mapping preserves input order."""
        # Use unordered input to verify order preservation
        unordered_data = [50, 10, 30, 20, 40]
        region = 'ME'
        min_max_data = {
            'min_syn_region': {'ME': 0},
            'max_syn_region': {'ME': 60}
        }

        colors = self.mapper.map_regional_synapse_colors(unordered_data, region, min_max_data)

        # Should preserve order and produce expected colors
        expected_normalized = [50/60, 10/60, 30/60, 20/60, 40/60]  # [0.83, 0.17, 0.5, 0.33, 0.67]
        expected_indices = [4, 0, 2, 1, 3]  # color indices for normalized values

        for i, expected_idx in enumerate(expected_indices):
            self.assertEqual(colors[i], self.palette.colors[expected_idx])


if __name__ == '__main__':
    unittest.main()
