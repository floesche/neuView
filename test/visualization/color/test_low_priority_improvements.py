"""
Test suite for low priority color module improvements.

This module tests the low priority improvements made to the color system including:
1. ColorPalette RGB/hex duplication removal
2. Jinja filter creation streamlining
3. Method naming convention standardization
"""

import unittest
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from quickpage.visualization.color import ColorPalette, ColorMapper


class TestLowPriorityImprovements(unittest.TestCase):
    """Test cases for low priority color module improvements."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.palette = ColorPalette()
        self.mapper = ColorMapper(self.palette)

    def test_rgb_hex_duplication_removal(self):
        """Test that RGB/hex duplication has been successfully removed."""
        # Should not have internal _color_values attribute anymore
        self.assertFalse(hasattr(self.palette, '_color_values'))

        # Should generate RGB values on-demand via property
        self.assertTrue(hasattr(self.palette, 'color_values'))

        # color_values should be a property, not an attribute
        self.assertIsInstance(type(self.palette).color_values, property)

        # Should still work correctly
        color_values = self.palette.color_values
        self.assertEqual(len(color_values), 5)
        self.assertEqual(color_values[0], (254, 229, 217))
        self.assertEqual(color_values[-1], (165, 15, 21))

    def test_rgb_values_generated_from_hex(self):
        """Test that RGB values are correctly generated from hex colors."""
        for i, hex_color in enumerate(self.palette.colors):
            # Get RGB via property
            property_rgb = self.palette.color_values[i]

            # Get RGB via direct conversion
            direct_rgb = self.palette.hex_to_rgb(hex_color)

            # Should be identical
            self.assertEqual(property_rgb, direct_rgb)

    def test_rgb_generation_consistency(self):
        """Test that RGB generation is consistent across multiple calls."""
        # Get RGB values multiple times
        rgb_values_1 = self.palette.color_values
        rgb_values_2 = self.palette.color_values

        # Should be identical each time
        self.assertEqual(rgb_values_1, rgb_values_2)

        # Should be independent lists (not the same object)
        self.assertIsNot(rgb_values_1, rgb_values_2)

    def test_jinja_filter_streamlining(self):
        """Test that Jinja filter creation has been streamlined."""
        # New method should exist
        self.assertTrue(hasattr(self.mapper, 'jinja_filters'))

        # Should return direct method references
        filters = self.mapper.jinja_filters()

        # Should contain expected filters
        self.assertIn('synapses_to_colors', filters)
        self.assertIn('neurons_to_colors', filters)

        # Should reference actual methods directly
        self.assertEqual(filters['synapses_to_colors'], self.mapper.map_synapse_colors)
        self.assertEqual(filters['neurons_to_colors'], self.mapper.map_neuron_colors)

    def test_jinja_filter_no_wrapper_functions(self):
        """Test that Jinja filters no longer use wrapper functions."""
        filters = self.mapper.jinja_filters()

        # Should be direct method references, not wrapper functions
        synapse_filter = filters['synapses_to_colors']
        neuron_filter = filters['neurons_to_colors']

        # Should be the actual mapper methods (same function, bound to same instance)
        self.assertEqual(synapse_filter.__func__, self.mapper.map_synapse_colors.__func__)
        self.assertEqual(neuron_filter.__func__, self.mapper.map_neuron_colors.__func__)
        self.assertIs(synapse_filter.__self__, self.mapper)
        self.assertIs(neuron_filter.__self__, self.mapper)

        # Should work correctly when called
        test_data = [10, 20, 30]
        synapse_colors = synapse_filter(test_data)
        neuron_colors = neuron_filter(test_data)

        self.assertEqual(len(synapse_colors), 3)
        self.assertEqual(len(neuron_colors), 3)

    def test_standardized_method_naming_palette(self):
        """Test that ColorPalette method naming has been standardized."""
        # New standardized method names should exist
        self.assertTrue(hasattr(self.palette, 'all_colors'))
        self.assertTrue(hasattr(self.palette, 'thresholds'))
        self.assertTrue(hasattr(self.palette, 'state_colors'))
        self.assertTrue(hasattr(self.palette, 'color_at'))
        self.assertTrue(hasattr(self.palette, 'rgb_at'))

        # Test new method names work correctly
        colors = self.palette.all_colors()
        self.assertEqual(len(colors), 5)

        thresholds = self.palette.thresholds()
        self.assertEqual(len(thresholds), 6)

        state_colors = self.palette.state_colors()
        self.assertEqual(len(state_colors), 3)

        color = self.palette.color_at(0)
        self.assertTrue(color.startswith('#'))

        rgb = self.palette.rgb_at(0)
        self.assertEqual(len(rgb), 3)

    def test_standardized_method_naming_mapper(self):
        """Test that ColorMapper method naming has been standardized."""
        # New standardized method names should exist
        self.assertTrue(hasattr(self.mapper, 'color_for_status'))
        self.assertTrue(hasattr(self.mapper, 'jinja_filters'))
        self.assertTrue(hasattr(self.mapper, 'legend_data'))

        # Test new method names work correctly
        status_color = self.mapper.color_for_status('no_data')
        self.assertEqual(status_color, '#ffffff')

        filters = self.mapper.jinja_filters()
        self.assertEqual(len(filters), 2)

        legend = self.mapper.legend_data(0, 100, 'test')
        self.assertIsInstance(legend, dict)

    def test_modern_palette_methods(self):
        """Test that ColorPalette modern methods work correctly after Phase 1 cleanup."""
        # Modern method names should exist and work
        self.assertTrue(hasattr(self.palette, 'all_colors'))
        self.assertTrue(hasattr(self.palette, 'thresholds'))
        self.assertTrue(hasattr(self.palette, 'state_colors'))
        self.assertTrue(hasattr(self.palette, 'color_at'))
        self.assertTrue(hasattr(self.palette, 'rgb_at'))

        # Deprecated methods should be removed
        self.assertFalse(hasattr(self.palette, 'get_all_colors'))
        self.assertFalse(hasattr(self.palette, 'get_thresholds'))
        self.assertFalse(hasattr(self.palette, 'get_state_colors'))
        self.assertFalse(hasattr(self.palette, 'get_color_at_index'))
        self.assertFalse(hasattr(self.palette, 'get_rgb_at_index'))

        # Modern methods should work correctly
        colors = self.palette.all_colors()
        self.assertEqual(len(colors), 5)

        thresholds = self.palette.thresholds()
        self.assertEqual(len(thresholds), 6)

        state_colors = self.palette.state_colors()
        self.assertIn('dark_gray', state_colors)

        color = self.palette.color_at(0)
        self.assertTrue(color.startswith('#'))

        rgb = self.palette.rgb_at(0)
        self.assertEqual(len(rgb), 3)

    def test_modern_mapper_methods(self):
        """Test that ColorMapper modern methods work correctly after Phase 1 cleanup."""
        # Modern method names should exist and work
        self.assertTrue(hasattr(self.mapper, 'color_for_status'))
        self.assertTrue(hasattr(self.mapper, 'jinja_filters'))
        self.assertTrue(hasattr(self.mapper, 'legend_data'))

        # Deprecated methods should be removed
        self.assertFalse(hasattr(self.mapper, 'get_color_for_status'))
        self.assertFalse(hasattr(self.mapper, 'get_jinja_filters'))
        self.assertFalse(hasattr(self.mapper, 'create_jinja_filters'))
        self.assertFalse(hasattr(self.mapper, 'get_legend_data'))

        # Modern methods should work correctly
        status_color = self.mapper.color_for_status('no_data')
        self.assertTrue(status_color.startswith('#'))

        filters = self.mapper.jinja_filters()
        self.assertIn('synapses_to_colors', filters)
        self.assertIn('neurons_to_colors', filters)

        legend = self.mapper.legend_data(0, 100, 'test')
        self.assertIn('colors', legend)
        self.assertIn('values', legend)

    def test_naming_convention_consistency(self):
        """Test that naming conventions are consistent across the module."""
        # ColorPalette methods should follow consistent patterns
        palette_methods = [method for method in dir(self.palette) if not method.startswith('_')]

        # New methods should not have get_ prefix (except backward compatibility)
        new_methods = ['all_colors', 'thresholds', 'state_colors', 'color_at', 'rgb_at']
        for method in new_methods:
            self.assertIn(method, palette_methods)

        # ColorMapper methods should follow consistent patterns
        mapper_methods = [method for method in dir(self.mapper) if not method.startswith('_')]

        # New methods should not have get_ prefix (except backward compatibility)
        new_mapper_methods = ['color_for_status', 'jinja_filters', 'legend_data']
        for method in new_mapper_methods:
            self.assertIn(method, mapper_methods)

    def test_performance_improvement_no_duplication(self):
        """Test that performance has improved by eliminating RGB/hex duplication."""
        # Memory usage should be lower (no stored RGB values)
        import sys

        # Get memory footprint of palette
        palette_size = sys.getsizeof(self.palette.__dict__)

        # Should not contain _color_values
        self.assertNotIn('_color_values', self.palette.__dict__)

        # RGB values should be generated on-demand
        rgb_values = self.palette.color_values
        self.assertEqual(len(rgb_values), 5)

        # Multiple calls should generate fresh lists
        rgb_values_2 = self.palette.color_values
        self.assertEqual(rgb_values, rgb_values_2)
        self.assertIsNot(rgb_values, rgb_values_2)  # Different objects

    def test_code_simplicity_improvements(self):
        """Test that code has been simplified through the improvements."""
        # value_to_color should now directly return from colors array
        normalized_value = 0.5
        color = self.palette.value_to_color(normalized_value)

        # Should be one of the palette colors
        self.assertIn(color, self.palette.colors)

        # Should match expected color for 0.5 (medium range)
        expected_color = self.palette.colors[2]  # 0.4-0.6 range
        self.assertEqual(color, expected_color)

    def test_maintainability_single_source_truth(self):
        """Test that there's now a single source of truth for colors."""
        # Only one color definition should exist (hex in colors array)
        self.assertEqual(len(self.palette.colors), 5)

        # RGB values should be derived from hex
        for i, hex_color in enumerate(self.palette.colors):
            derived_rgb = self.palette.hex_to_rgb(hex_color)
            property_rgb = self.palette.color_values[i]
            method_rgb = self.palette.rgb_at(i)

            # All should be identical
            self.assertEqual(derived_rgb, property_rgb)
            self.assertEqual(derived_rgb, method_rgb)

    def test_api_design_improvements(self):
        """Test that API design has been improved with better method names."""
        # Method names should be more intuitive

        # ColorPalette - shorter, clearer names
        self.assertTrue(callable(self.palette.all_colors))
        self.assertTrue(callable(self.palette.color_at))
        self.assertTrue(callable(self.palette.rgb_at))

        # ColorMapper - more consistent naming
        self.assertTrue(callable(self.mapper.color_for_status))
        self.assertTrue(callable(self.mapper.jinja_filters))
        self.assertTrue(callable(self.mapper.legend_data))

        # Static methods should be easily identifiable
        self.assertTrue(callable(ColorPalette.hex_to_rgb))
        self.assertTrue(callable(ColorPalette.rgb_to_hex))
        self.assertTrue(callable(ColorMapper.normalize_color_value))

    def test_phase1_cleanup_verification(self):
        """Test that Phase 1 cleanup was successful."""
        # Verify deprecated methods are completely removed
        deprecated_palette_methods = [
            'get_all_colors', 'get_thresholds', 'get_state_colors',
            'get_color_at_index', 'get_rgb_at_index'
        ]

        for method in deprecated_palette_methods:
            self.assertFalse(hasattr(self.palette, method),
                           f"Deprecated method {method} still exists in ColorPalette")

        deprecated_mapper_methods = [
            'get_color_for_status', 'get_jinja_filters',
            'create_jinja_filters', 'get_legend_data'
        ]

        for method in deprecated_mapper_methods:
            self.assertFalse(hasattr(self.mapper, method),
                           f"Deprecated method {method} still exists in ColorMapper")

        # Verify modern methods work correctly
        self.assertIsInstance(self.palette.all_colors(), list)
        self.assertIsInstance(self.mapper.color_for_status('has_data'), str)

        # Verify modern methods are callable
        self.assertTrue(callable(self.palette.all_colors))
        self.assertTrue(callable(self.mapper.color_for_status))

    def test_integration_with_existing_tests(self):
        """Test that improvements integrate well with existing functionality."""
        # All existing functionality should still work
        test_data = [10, 25, 40, 55, 70]

        # Color mapping should work
        colors = self.mapper.map_synapse_colors(test_data)
        self.assertEqual(len(colors), 5)

        # Regional mapping should work
        region_colors = self.mapper.map_regional_synapse_colors(
            test_data, 'ME',
            {'min_syn_region': {'ME': 0}, 'max_syn_region': {'ME': 100}}
        )
        self.assertEqual(len(region_colors), 5)

        # Color conversion should work
        rgb = ColorPalette.hex_to_rgb('#ff5733')
        hex_back = ColorPalette.rgb_to_hex(*rgb)
        self.assertEqual(hex_back, '#ff5733')

        # Normalization should work
        norm = ColorMapper.normalize_color_value(50, 0, 100)
        self.assertEqual(norm, 0.5)


if __name__ == '__main__':
    unittest.main()
