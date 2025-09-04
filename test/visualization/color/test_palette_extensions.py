"""
Test suite for ColorPalette extensions added during ColorUtils consolidation.

This module tests the new color conversion methods added to ColorPalette
as part of the ColorUtils consolidation effort.
"""

import unittest
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from quickpage.visualization.color.palette import ColorPalette


class TestColorPaletteExtensions(unittest.TestCase):
    """Test cases for new ColorPalette color conversion methods."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.palette = ColorPalette()

    def test_hex_to_rgb_valid_colors(self):
        """Test hex_to_rgb conversion with valid hex colors."""
        test_cases = [
            ('#ffffff', (255, 255, 255)),  # White
            ('#000000', (0, 0, 0)),        # Black
            ('#ff0000', (255, 0, 0)),      # Red
            ('#00ff00', (0, 255, 0)),      # Green
            ('#0000ff', (0, 0, 255)),      # Blue
            ('#ff5733', (255, 87, 51)),    # Orange
            ('#a50f15', (165, 15, 21)),    # Dark red (from palette)
            ('#fee5d9', (254, 229, 217)),  # Light red (from palette)
            ('#fcbba1', (252, 187, 161)),  # Another palette color
        ]

        for hex_color, expected_rgb in test_cases:
            with self.subTest(hex_color=hex_color):
                result = ColorPalette.hex_to_rgb(hex_color)
                self.assertEqual(result, expected_rgb)
                self.assertEqual(len(result), 3)
                # Verify all values are valid RGB components
                for value in result:
                    self.assertTrue(0 <= value <= 255)

    def test_hex_to_rgb_without_hash(self):
        """Test hex_to_rgb handles colors without hash prefix."""
        test_cases = [
            ('ffffff', (255, 255, 255)),
            ('000000', (0, 0, 0)),
            ('ff5733', (255, 87, 51)),
            ('a50f15', (165, 15, 21)),
        ]

        for hex_color, expected_rgb in test_cases:
            with self.subTest(hex_color=hex_color):
                result = ColorPalette.hex_to_rgb(hex_color)
                self.assertEqual(result, expected_rgb)

    def test_hex_to_rgb_case_insensitive(self):
        """Test hex_to_rgb is case insensitive."""
        test_cases = [
            ('#FFFFFF', '#ffffff'),
            ('#FF5733', '#ff5733'),
            ('#A50F15', '#a50f15'),
            ('ABCDEF', 'abcdef'),
        ]

        for upper_hex, lower_hex in test_cases:
            with self.subTest(upper=upper_hex, lower=lower_hex):
                upper_result = ColorPalette.hex_to_rgb(upper_hex)
                lower_result = ColorPalette.hex_to_rgb(lower_hex)
                self.assertEqual(upper_result, lower_result)

    def test_rgb_to_hex_valid_values(self):
        """Test rgb_to_hex conversion with valid RGB values."""
        test_cases = [
            ((255, 255, 255), '#ffffff'),  # White
            ((0, 0, 0), '#000000'),        # Black
            ((255, 0, 0), '#ff0000'),      # Red
            ((0, 255, 0), '#00ff00'),      # Green
            ((0, 0, 255), '#0000ff'),      # Blue
            ((255, 87, 51), '#ff5733'),    # Orange
            ((165, 15, 21), '#a50f15'),    # Dark red (from palette)
            ((254, 229, 217), '#fee5d9'),  # Light red (from palette)
            ((252, 187, 161), '#fcbba1'),  # Another palette color
        ]

        for rgb_values, expected_hex in test_cases:
            with self.subTest(rgb=rgb_values):
                r, g, b = rgb_values
                result = ColorPalette.rgb_to_hex(r, g, b)
                self.assertEqual(result, expected_hex)
                self.assertTrue(result.startswith('#'))
                self.assertEqual(len(result), 7)

    def test_rgb_to_hex_edge_values(self):
        """Test rgb_to_hex with edge RGB values."""
        edge_cases = [
            ((0, 0, 0), '#000000'),        # All zeros
            ((255, 255, 255), '#ffffff'),  # All max
            ((1, 1, 1), '#010101'),        # All ones
            ((16, 16, 16), '#101010'),     # Low values
            ((240, 240, 240), '#f0f0f0'),  # High values
        ]

        for rgb_values, expected_hex in edge_cases:
            with self.subTest(rgb=rgb_values):
                r, g, b = rgb_values
                result = ColorPalette.rgb_to_hex(r, g, b)
                self.assertEqual(result, expected_hex)

    def test_round_trip_conversion(self):
        """Test that hex->rgb->hex produces identical results."""
        test_hex_colors = [
            '#ffffff', '#000000', '#ff0000', '#00ff00', '#0000ff',
            '#ff5733', '#a50f15', '#fee5d9', '#fcbba1', '#fc9272',
            '#ef6548', '#999999', '#e0e0e0'
        ]

        for original_hex in test_hex_colors:
            with self.subTest(hex_color=original_hex):
                # Convert hex to RGB
                rgb = ColorPalette.hex_to_rgb(original_hex)
                # Convert RGB back to hex
                result_hex = ColorPalette.rgb_to_hex(*rgb)
                # Should match original
                self.assertEqual(result_hex, original_hex.lower())

    def test_round_trip_conversion_rgb_to_hex_to_rgb(self):
        """Test that rgb->hex->rgb produces identical results."""
        test_rgb_values = [
            (255, 255, 255), (0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255),
            (255, 87, 51), (165, 15, 21), (254, 229, 217), (252, 187, 161),
            (252, 146, 114), (239, 101, 72), (153, 153, 153), (224, 224, 224)
        ]

        for original_rgb in test_rgb_values:
            with self.subTest(rgb=original_rgb):
                # Convert RGB to hex
                hex_color = ColorPalette.rgb_to_hex(*original_rgb)
                # Convert hex back to RGB
                result_rgb = ColorPalette.hex_to_rgb(hex_color)
                # Should match original
                self.assertEqual(result_rgb, original_rgb)

    def test_palette_color_consistency(self):
        """Test that palette colors have consistent hex/RGB representations."""
        # Test all colors in the palette
        for i, hex_color in enumerate(self.palette.colors):
            with self.subTest(index=i, hex_color=hex_color):
                # Convert hex to RGB using new method
                calculated_rgb = ColorPalette.hex_to_rgb(hex_color)

                # Get RGB from palette's internal storage
                palette_rgb = self.palette.rgb_at(i)

                # Should match
                self.assertEqual(calculated_rgb, palette_rgb)

                # Convert back to hex
                calculated_hex = ColorPalette.rgb_to_hex(*palette_rgb)

                # Should match original
                self.assertEqual(calculated_hex, hex_color)

    def test_state_color_consistency(self):
        """Test that state colors have consistent representations."""
        state_colors = self.palette.get_state_colors()

        for color_name, hex_color in state_colors.items():
            with self.subTest(color=color_name, hex_color=hex_color):
                # Convert to RGB and back
                rgb = ColorPalette.hex_to_rgb(hex_color)
                hex_back = ColorPalette.rgb_to_hex(*rgb)

                # Should match
                self.assertEqual(hex_back, hex_color)

    def test_static_method_accessibility(self):
        """Test that color conversion methods are accessible as static methods."""
        # Should be callable without instantiation
        rgb = ColorPalette.hex_to_rgb('#ff5733')
        self.assertEqual(rgb, (255, 87, 51))

        hex_color = ColorPalette.rgb_to_hex(255, 87, 51)
        self.assertEqual(hex_color, '#ff5733')

        # Should also be callable from instance
        palette = ColorPalette()
        instance_rgb = palette.hex_to_rgb('#ff5733')
        instance_hex = palette.rgb_to_hex(255, 87, 51)

        self.assertEqual(rgb, instance_rgb)
        self.assertEqual(hex_color, instance_hex)

    def test_hex_to_rgb_error_handling(self):
        """Test hex_to_rgb handles invalid inputs gracefully."""
        # These should raise ValueError or similar for invalid input
        invalid_inputs = [
            '#gggggg',  # Invalid hex characters
            '#12345',   # Wrong length
            '#1234567', # Wrong length
            'notahex',  # Not hex at all
        ]

        for invalid_hex in invalid_inputs:
            with self.subTest(invalid_hex=invalid_hex):
                with self.assertRaises(ValueError):
                    ColorPalette.hex_to_rgb(invalid_hex)

    def test_rgb_to_hex_boundary_validation(self):
        """Test rgb_to_hex validates RGB value boundaries."""
        # Test with values outside valid range
        invalid_rgb_sets = [
            (-1, 0, 0),     # Negative value
            (256, 0, 0),    # Value too high
            (0, -1, 0),     # Negative green
            (0, 256, 0),    # Green too high
            (0, 0, -1),     # Negative blue
            (0, 0, 256),    # Blue too high
        ]

        for r, g, b in invalid_rgb_sets:
            with self.subTest(r=r, g=g, b=b):
                # Should either clamp values or raise an error
                # The exact behavior depends on implementation choice
                try:
                    result = ColorPalette.rgb_to_hex(r, g, b)
                    # If it doesn't raise an error, it should produce a valid hex
                    self.assertTrue(result.startswith('#'))
                    self.assertEqual(len(result), 7)
                except (ValueError, OverflowError):
                    # It's also acceptable to raise an error for invalid values
                    pass

    def test_integration_with_existing_palette_methods(self):
        """Test that new methods integrate well with existing palette functionality."""
        # Test that new methods work with colors from existing methods
        for i in range(len(self.palette.colors)):
            # Get color using existing method
            hex_color = self.palette.get_color_at_index(i)
            rgb_values = self.palette.get_rgb_at_index(i)

            # Test new conversion methods
            converted_rgb = ColorPalette.hex_to_rgb(hex_color)
            converted_hex = ColorPalette.rgb_to_hex(*rgb_values)

            # Should be consistent
            self.assertEqual(converted_rgb, rgb_values)
            self.assertEqual(converted_hex, hex_color)


if __name__ == '__main__':
    unittest.main()
