"""
Unit tests for ColorPalette class.

This module tests the color palette functionality including color mapping,
value normalization, and palette management operations.
"""

import unittest
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from quickpage.visualization.color.palette import ColorPalette


class TestColorPalette(unittest.TestCase):
    """Test cases for ColorPalette class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.palette = ColorPalette()

    def test_initialization(self):
        """Test ColorPalette initialization."""
        # Test default colors are set
        self.assertEqual(len(self.palette.colors), 5)
        self.assertEqual(self.palette.colors[0], '#fee5d9')
        self.assertEqual(self.palette.colors[-1], '#a50f15')

        # Test RGB values are generated correctly
        color_values = self.palette.color_values
        self.assertEqual(len(color_values), 5)
        self.assertEqual(color_values[0], (254, 229, 217))
        self.assertEqual(color_values[-1], (165, 15, 21))

        # Test state colors
        self.assertEqual(self.palette.dark_gray, '#999999')
        self.assertEqual(self.palette.white, '#ffffff')
        self.assertEqual(self.palette.light_gray, '#e0e0e0')

    def test_value_to_color_valid_inputs(self):
        """Test value_to_color with valid inputs."""
        # Test boundary values
        self.assertEqual(self.palette.value_to_color(0.0), '#fee5d9')  # Lightest
        self.assertEqual(self.palette.value_to_color(0.2), '#fee5d9')  # Still lightest
        self.assertEqual(self.palette.value_to_color(0.3), '#fcbba1')  # Light
        self.assertEqual(self.palette.value_to_color(0.5), '#fc9272')  # Medium
        self.assertEqual(self.palette.value_to_color(0.7), '#ef6548')  # Dark
        self.assertEqual(self.palette.value_to_color(1.0), '#a50f15')  # Darkest

    def test_value_to_color_edge_cases(self):
        """Test value_to_color with edge cases."""
        # Test exact threshold values
        self.assertEqual(self.palette.value_to_color(0.2), '#fee5d9')
        self.assertEqual(self.palette.value_to_color(0.4), '#fcbba1')
        self.assertEqual(self.palette.value_to_color(0.6), '#fc9272')
        self.assertEqual(self.palette.value_to_color(0.8), '#ef6548')

        # Test just above thresholds
        self.assertEqual(self.palette.value_to_color(0.21), '#fcbba1')
        self.assertEqual(self.palette.value_to_color(0.41), '#fc9272')
        self.assertEqual(self.palette.value_to_color(0.61), '#ef6548')
        self.assertEqual(self.palette.value_to_color(0.81), '#a50f15')

    def test_value_to_color_invalid_inputs(self):
        """Test value_to_color with invalid inputs."""
        # Test values outside valid range
        with self.assertRaises(ValueError):
            self.palette.value_to_color(-0.1)

        with self.assertRaises(ValueError):
            self.palette.value_to_color(1.1)

        with self.assertRaises(ValueError):
            self.palette.value_to_color(-1.0)

        with self.assertRaises(ValueError):
            self.palette.value_to_color(2.0)

    def test_get_color_index(self):
        """Test _get_color_index method."""
        # Test all color bins
        self.assertEqual(self.palette._get_color_index(0.0), 0)
        self.assertEqual(self.palette._get_color_index(0.1), 0)
        self.assertEqual(self.palette._get_color_index(0.2), 0)
        self.assertEqual(self.palette._get_color_index(0.3), 1)
        self.assertEqual(self.palette._get_color_index(0.4), 1)
        self.assertEqual(self.palette._get_color_index(0.5), 2)
        self.assertEqual(self.palette._get_color_index(0.6), 2)
        self.assertEqual(self.palette._get_color_index(0.7), 3)
        self.assertEqual(self.palette._get_color_index(0.8), 3)
        self.assertEqual(self.palette._get_color_index(0.9), 4)
        self.assertEqual(self.palette._get_color_index(1.0), 4)

    def test_get_color_at_index(self):
        """Test get_color_at_index method."""
        # Test valid indices
        for i in range(5):
            color = self.palette.get_color_at_index(i)
            self.assertEqual(color, self.palette.colors[i])

        # Test invalid indices
        with self.assertRaises(IndexError):
            self.palette.get_color_at_index(-1)

        with self.assertRaises(IndexError):
            self.palette.get_color_at_index(5)

        with self.assertRaises(IndexError):
            self.palette.get_color_at_index(10)

    def test_get_rgb_at_index(self):
        """Test get_rgb_at_index method."""
        # Test valid indices
        for i in range(5):
            rgb = self.palette.get_rgb_at_index(i)
            expected_rgb = self.palette.color_values[i]
            self.assertEqual(rgb, expected_rgb)
            self.assertEqual(len(rgb), 3)
            self.assertTrue(all(0 <= val <= 255 for val in rgb))

        # Test invalid indices
        with self.assertRaises(IndexError):
            self.palette.get_rgb_at_index(-1)

        with self.assertRaises(IndexError):
            self.palette.get_rgb_at_index(5)

    def test_get_all_colors(self):
        """Test get_all_colors method."""
        colors = self.palette.get_all_colors()

        # Test return type and content
        self.assertIsInstance(colors, list)
        self.assertEqual(len(colors), 5)
        self.assertEqual(colors, self.palette.colors)

        # Test it returns a copy (not the original)
        colors[0] = '#000000'
        self.assertNotEqual(colors[0], self.palette.colors[0])

    def test_get_thresholds(self):
        """Test get_thresholds method."""
        thresholds = self.palette.get_thresholds()

        # Test return type and content
        self.assertIsInstance(thresholds, list)
        self.assertEqual(len(thresholds), 6)
        self.assertEqual(thresholds, [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])

        # Test it returns a copy
        thresholds[0] = -1.0
        self.assertNotEqual(thresholds[0], self.palette._thresholds[0])

    def test_get_state_colors(self):
        """Test get_state_colors method."""
        state_colors = self.palette.get_state_colors()

        # Test return type and content
        self.assertIsInstance(state_colors, dict)
        self.assertEqual(len(state_colors), 3)

        expected_keys = {'dark_gray', 'white', 'light_gray'}
        self.assertEqual(set(state_colors.keys()), expected_keys)

        self.assertEqual(state_colors['dark_gray'], '#999999')
        self.assertEqual(state_colors['white'], '#ffffff')
        self.assertEqual(state_colors['light_gray'], '#e0e0e0')

    def test_color_consistency(self):
        """Test consistency between hex colors and RGB values."""
        for i in range(5):
            hex_color = self.palette.get_color_at_index(i)
            rgb_values = self.palette.get_rgb_at_index(i)

            # Convert RGB to hex and compare
            r, g, b = rgb_values
            expected_hex = f"#{r:02x}{g:02x}{b:02x}"
            self.assertEqual(hex_color, expected_hex)

    def test_immutability_of_internal_structures(self):
        """Test that internal color structures cannot be modified externally."""
        original_colors = self.palette.colors.copy()
        original_color_values = self.palette.color_values.copy()

        # Get copies of internal structures
        colors = self.palette.get_all_colors()
        thresholds = self.palette.get_thresholds()
        state_colors = self.palette.get_state_colors()

        # Modify the copies
        colors[0] = '#000000'
        thresholds[0] = -1.0
        state_colors['dark_gray'] = '#000000'

        # Verify internal structures are unchanged
        self.assertEqual(self.palette.colors, original_colors)
        self.assertEqual(self.palette.color_values, original_color_values)
        self.assertEqual(self.palette.dark_gray, '#999999')


if __name__ == '__main__':
    unittest.main()
