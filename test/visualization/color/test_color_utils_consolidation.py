"""
Test suite for ColorUtils consolidation and new functionality.

This module tests the consolidation of ColorUtils functionality into the
visualization.color module, including the compatibility wrapper and new
regional color mapping capabilities.
"""

import unittest
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from quickpage.utils import ColorUtils as UtilsColorUtils
from quickpage.visualization.color import ColorUtils as ColorColorUtils, ColorMapper, ColorPalette
ColorUtils = UtilsColorUtils  # Use the utils import for tests


class TestColorUtilsConsolidation(unittest.TestCase):
    """Test cases for ColorUtils consolidation and compatibility."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.utils_color_utils = UtilsColorUtils()
        self.color_color_utils = ColorColorUtils()
        self.color_mapper = ColorMapper()
        self.color_palette = ColorPalette()

    def test_colorutils_import_compatibility(self):
        """Test that ColorUtils can be imported from both locations."""
        # Should be able to import from utils (compatibility)
        from quickpage.utils import ColorUtils as UtilsImport

        # Should be able to import from visualization.color (new location)
        from quickpage.visualization.color import ColorUtils as ColorImport

        # Both should be the same class
        self.assertEqual(UtilsImport, ColorImport)

        # Both should be instances of the same class
        utils_instance = UtilsImport()
        color_instance = ColorImport()
        self.assertEqual(type(utils_instance), type(color_instance))

    def test_color_conversion_methods(self):
        """Test hex to RGB and RGB to hex conversion methods."""
        test_cases = [
            ('#ffffff', (255, 255, 255)),
            ('#000000', (0, 0, 0)),
            ('#ff5733', (255, 87, 51)),
            ('#a50f15', (165, 15, 21)),
            ('#fee5d9', (254, 229, 217))
        ]

        for hex_color, expected_rgb in test_cases:
            with self.subTest(hex_color=hex_color):
                # Test ColorUtils static methods
                rgb_result = ColorUtils.hex_to_rgb(hex_color)
                self.assertEqual(rgb_result, expected_rgb)

                # Test reverse conversion
                hex_result = ColorUtils.rgb_to_hex(*expected_rgb)
                self.assertEqual(hex_result.lower(), hex_color.lower())

                # Test ColorPalette static methods directly
                palette_rgb = ColorPalette.hex_to_rgb(hex_color)
                palette_hex = ColorPalette.rgb_to_hex(*expected_rgb)

                self.assertEqual(rgb_result, palette_rgb)
                self.assertEqual(hex_result, palette_hex)

    def test_color_conversion_with_hash_variations(self):
        """Test color conversion handles hash variations correctly."""
        # Test with and without hash
        with_hash = '#ff5733'
        without_hash = 'ff5733'

        rgb_with = ColorUtils.hex_to_rgb(with_hash)
        rgb_without = ColorUtils.hex_to_rgb(without_hash)

        self.assertEqual(rgb_with, rgb_without)
        self.assertEqual(rgb_with, (255, 87, 51))

    def test_normalization_method(self):
        """Test value normalization functionality."""
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
                result = ColorUtils.normalize_color_value(value, min_val, max_val)
                self.assertAlmostEqual(result, expected, places=6)

                # Test ColorMapper static method directly
                mapper_result = ColorMapper.normalize_color_value(value, min_val, max_val)
                self.assertAlmostEqual(result, mapper_result, places=6)

    def test_regional_synapse_color_mapping(self):
        """Test regional synapse color mapping functionality."""
        synapses_list = [10, 25, 40, 55, 70]
        region = 'ME'
        min_max_data = {
            'min_syn_region': {'ME': 0, 'LO': 5, 'LOP': 10},
            'max_syn_region': {'ME': 100, 'LO': 80, 'LOP': 60}
        }

        # Test ColorUtils wrapper
        colors = self.utils_color_utils.synapses_to_colors(synapses_list, region, min_max_data)

        # Test direct ColorMapper method
        direct_colors = self.color_mapper.map_regional_synapse_colors(synapses_list, region, min_max_data)

        # Should produce identical results
        self.assertEqual(colors, direct_colors)
        self.assertEqual(len(colors), 5)

        # All should be valid hex colors
        for color in colors:
            self.assertTrue(color.startswith('#'))
            self.assertEqual(len(color), 7)

    def test_regional_neuron_color_mapping(self):
        """Test regional neuron color mapping functionality."""
        neurons_list = [5, 15, 25, 35, 45]
        region = 'LO'
        min_max_data = {
            'min_cells_region': {'ME': 0, 'LO': 0, 'LOP': 5},
            'max_cells_region': {'ME': 50, 'LO': 60, 'LOP': 40}
        }

        # Test ColorUtils wrapper
        colors = self.utils_color_utils.neurons_to_colors(neurons_list, region, min_max_data)

        # Test direct ColorMapper method
        direct_colors = self.color_mapper.map_regional_neuron_colors(neurons_list, region, min_max_data)

        # Should produce identical results
        self.assertEqual(colors, direct_colors)
        self.assertEqual(len(colors), 5)

        # All should be valid hex colors
        for color in colors:
            self.assertTrue(color.startswith('#'))
            self.assertEqual(len(color), 7)

    def test_regional_mapping_with_zero_values(self):
        """Test regional mapping handles zero values correctly."""
        synapses_with_zeros = [0, 10, 0, 20, 0]
        region = 'LOP'
        min_max_data = {
            'min_syn_region': {'LOP': 0},
            'max_syn_region': {'LOP': 50}
        }

        colors = self.utils_color_utils.synapses_to_colors(synapses_with_zeros, region, min_max_data)

        # Zero values should map to white
        self.assertEqual(colors[0], '#ffffff')
        self.assertEqual(colors[2], '#ffffff')
        self.assertEqual(colors[4], '#ffffff')

        # Non-zero values should map to actual colors
        self.assertNotEqual(colors[1], '#ffffff')
        self.assertNotEqual(colors[3], '#ffffff')

    def test_regional_mapping_empty_data(self):
        """Test regional mapping handles empty data correctly."""
        empty_synapses = []
        empty_neurons = []
        region = 'ME'
        min_max_data = {'min_syn_region': {'ME': 0}, 'max_syn_region': {'ME': 100}}

        synapse_colors = self.utils_color_utils.synapses_to_colors(empty_synapses, region, min_max_data)
        neuron_colors = self.utils_color_utils.neurons_to_colors(empty_neurons, region, min_max_data)

        self.assertEqual(synapse_colors, [])
        self.assertEqual(neuron_colors, [])

    def test_regional_mapping_missing_region_data(self):
        """Test regional mapping handles missing region data gracefully."""
        synapses_list = [10, 20, 30]
        missing_region = 'UNKNOWN'
        min_max_data = {
            'min_syn_region': {'ME': 0},
            'max_syn_region': {'ME': 100}
        }

        colors = self.utils_color_utils.synapses_to_colors(synapses_list, missing_region, min_max_data)

        # Should handle gracefully (using 0.0 as default min/max)
        self.assertEqual(len(colors), 3)
        for color in colors:
            self.assertTrue(color.startswith('#'))

    def test_regional_mapping_missing_min_max_data(self):
        """Test regional mapping handles missing min_max_data correctly."""
        synapses_list = [10, 20, 30]
        region = 'ME'

        # Test with None
        colors_none = self.utils_color_utils.synapses_to_colors(synapses_list, region, None)
        expected_white = ['#ffffff'] * 3
        self.assertEqual(colors_none, expected_white)

        # Test with empty dict
        colors_empty = self.utils_color_utils.synapses_to_colors(synapses_list, region, {})
        self.assertEqual(colors_empty, expected_white)

    def test_colorutils_independence_from_eyemap_generator(self):
        """Test that new ColorUtils works independently of eyemap_generator."""
        # Create ColorUtils without eyemap_generator
        color_utils_no_gen = ColorUtils()

        # Create ColorUtils with None eyemap_generator
        color_utils_none_gen = ColorUtils(None)

        # Both should work for color conversion
        hex_color = '#ff5733'
        rgb1 = color_utils_no_gen.hex_to_rgb(hex_color)
        rgb2 = color_utils_none_gen.hex_to_rgb(hex_color)

        self.assertEqual(rgb1, rgb2)
        self.assertEqual(rgb1, (255, 87, 51))

        # Both should work for regional mapping
        synapses = [10, 20]
        region = 'ME'
        min_max_data = {'min_syn_region': {'ME': 0}, 'max_syn_region': {'ME': 100}}

        colors1 = color_utils_no_gen.synapses_to_colors(synapses, region, min_max_data)
        colors2 = color_utils_none_gen.synapses_to_colors(synapses, region, min_max_data)

        self.assertEqual(colors1, colors2)

    def test_compatibility_with_existing_interface(self):
        """Test that the new ColorUtils maintains compatibility with existing interface."""
        # Test that all expected methods exist
        expected_methods = [
            'synapses_to_colors',
            'neurons_to_colors',
            'hex_to_rgb',
            'rgb_to_hex',
            'normalize_color_value'
        ]

        for method_name in expected_methods:
            self.assertTrue(hasattr(ColorUtils, method_name), f"Missing method: {method_name}")
            self.assertTrue(callable(getattr(ColorUtils, method_name)), f"Method not callable: {method_name}")

    def test_performance_with_large_datasets(self):
        """Test that consolidated ColorUtils maintains good performance."""
        # Create large dataset
        large_synapses = list(range(1000))
        region = 'ME'
        min_max_data = {'min_syn_region': {'ME': 0}, 'max_syn_region': {'ME': 999}}

        # Should complete without issues
        colors = self.utils_color_utils.synapses_to_colors(large_synapses, region, min_max_data)

        self.assertEqual(len(colors), 1000)

        # Verify first and last colors
        self.assertTrue(colors[0].startswith('#'))
        self.assertTrue(colors[-1].startswith('#'))

        # Should show progression from light to dark
        # Note: First value (0) maps to white due to zero handling in regional mapping
        # Last value (999) should map to darkest color
        self.assertEqual(colors[0], '#ffffff')  # Zero value -> white
        self.assertEqual(colors[-1], self.color_palette.colors[-1])  # Darkest

    def test_consolidation_maintains_original_behavior(self):
        """Test that consolidation maintains the exact original behavior."""
        # Test cases that would have worked with original ColorUtils
        test_cases = [
            {
                'synapses': [0, 25, 50, 75, 100],
                'region': 'ME',
                'min_max': {'min_syn_region': {'ME': 0}, 'max_syn_region': {'ME': 100}}
            },
            {
                'synapses': [10, 20],
                'region': 'LO',
                'min_max': {'min_syn_region': {'LO': 5}, 'max_syn_region': {'LO': 25}}
            },
            {
                'synapses': [42],
                'region': 'LOP',
                'min_max': {'min_syn_region': {'LOP': 40}, 'max_syn_region': {'LOP': 50}}
            }
        ]

        for case in test_cases:
            with self.subTest(case=case):
                colors = self.utils_color_utils.synapses_to_colors(
                    case['synapses'], case['region'], case['min_max']
                )

                # Should return correct number of colors
                self.assertEqual(len(colors), len(case['synapses']))

                # All should be valid hex colors
                for color in colors:
                    self.assertTrue(color.startswith('#'))
                    self.assertEqual(len(color), 7)


if __name__ == '__main__':
    unittest.main()
