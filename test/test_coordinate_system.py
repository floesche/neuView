"""
Unit tests for coordinate system classes.

This module tests the coordinate system components including coordinate
conversions, geometric calculations, and layout management.
"""

import unittest
import math
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from quickpage.visualization.coordinate_system import (
    HexagonPoint,
    AxialCoordinate,
    PixelCoordinate,
    GridBounds,
    HexagonCoordinateSystem,
    HexagonGeometry,
    HexagonGridLayout,
    EyemapCoordinateSystem,
)


class TestHexagonPoint(unittest.TestCase):
    """Test HexagonPoint dataclass."""

    def test_initialization(self):
        """Test HexagonPoint initialization."""
        point = HexagonPoint(5, 10)
        self.assertEqual(point.hex1, 5)
        self.assertEqual(point.hex2, 10)

    def test_to_tuple(self):
        """Test conversion to tuple."""
        point = HexagonPoint(3, 7)
        self.assertEqual(point.to_tuple(), (3, 7))


class TestAxialCoordinate(unittest.TestCase):
    """Test AxialCoordinate dataclass."""

    def test_initialization(self):
        """Test AxialCoordinate initialization."""
        coord = AxialCoordinate(1.5, -2.3)
        self.assertEqual(coord.q, 1.5)
        self.assertEqual(coord.r, -2.3)


class TestPixelCoordinate(unittest.TestCase):
    """Test PixelCoordinate dataclass."""

    def test_initialization(self):
        """Test PixelCoordinate initialization."""
        coord = PixelCoordinate(100.5, 200.7)
        self.assertEqual(coord.x, 100.5)
        self.assertEqual(coord.y, 200.7)


class TestGridBounds(unittest.TestCase):
    """Test GridBounds dataclass."""

    def test_initialization(self):
        """Test GridBounds initialization."""
        bounds = GridBounds(0, 100, 0, 200, 100, 200)
        self.assertEqual(bounds.min_x, 0)
        self.assertEqual(bounds.max_x, 100)
        self.assertEqual(bounds.min_y, 0)
        self.assertEqual(bounds.max_y, 200)
        self.assertEqual(bounds.width, 100)
        self.assertEqual(bounds.height, 200)


class TestHexagonCoordinateSystem(unittest.TestCase):
    """Test HexagonCoordinateSystem class."""

    def setUp(self):
        """Set up test fixtures."""
        self.coord_system = HexagonCoordinateSystem(hex_size=6, spacing_factor=1.1)

    def test_initialization(self):
        """Test HexagonCoordinateSystem initialization."""
        self.assertEqual(self.coord_system.hex_size, 6)
        self.assertEqual(self.coord_system.spacing_factor, 1.1)
        self.assertAlmostEqual(self.coord_system.effective_size, 6.6, places=5)

    def test_hex_to_axial_basic(self):
        """Test basic hexagon to axial coordinate conversion."""
        axial = self.coord_system.hex_to_axial(0, 0)
        self.assertEqual(axial.q, -3)
        self.assertEqual(axial.r, 0)

    def test_hex_to_axial_with_offset(self):
        """Test hexagon to axial conversion with offset."""
        axial = self.coord_system.hex_to_axial(5, 3, min_hex1=2, min_hex2=1)
        # hex1_coord = 5 - 2 = 3, hex2_coord = 3 - 1 = 2
        # q = -(3 - 2) - 3 = -4, r = -2
        self.assertEqual(axial.q, -4)
        self.assertEqual(axial.r, -2)

    def test_axial_to_pixel_no_mirror(self):
        """Test axial to pixel conversion without mirroring."""
        axial = AxialCoordinate(q=2, r=1)
        pixel = self.coord_system.axial_to_pixel(axial)

        expected_x = 6.6 * (3 / 2 * 2)  # 19.8
        expected_y = 6.6 * (
            math.sqrt(3) / 2 * 2 + math.sqrt(3) * 1
        )  # 6.6 * (sqrt(3) + sqrt(3)) = 6.6 * 2 * sqrt(3)

        self.assertAlmostEqual(pixel.x, expected_x, places=5)
        self.assertAlmostEqual(pixel.y, expected_y, places=5)

    def test_axial_to_pixel_with_mirror(self):
        """Test axial to pixel conversion with mirroring."""
        axial = AxialCoordinate(q=2, r=1)
        pixel = self.coord_system.axial_to_pixel(axial, mirror_side="right")

        expected_x = (6.6 * (3 / 2 * 2))  # -19.8
        expected_y = 6.6 * (math.sqrt(3) / 2 * 2 + math.sqrt(3) * 1)

        self.assertAlmostEqual(pixel.x, expected_x, places=5)
        self.assertAlmostEqual(pixel.y, expected_y, places=5)

    def test_hex_to_pixel_direct(self):
        """Test direct hexagon to pixel conversion."""
        pixel = self.coord_system.hex_to_pixel(3, 2, min_hex1=1, min_hex2=1)

        # This should be equivalent to:
        # hex_to_axial(3, 2, 1, 1) -> axial_to_pixel(axial)
        axial = self.coord_system.hex_to_axial(3, 2, 1, 1)
        expected_pixel = self.coord_system.axial_to_pixel(axial)

        self.assertAlmostEqual(pixel.x, expected_pixel.x, places=5)
        self.assertAlmostEqual(pixel.y, expected_pixel.y, places=5)


class TestHexagonGeometry(unittest.TestCase):
    """Test HexagonGeometry class."""

    def setUp(self):
        """Set up test fixtures."""
        self.geometry = HexagonGeometry(hex_size=10)

    def test_initialization(self):
        """Test HexagonGeometry initialization."""
        self.assertEqual(self.geometry.hex_size, 10)

    def test_get_hexagon_vertices(self):
        """Test hexagon vertex calculation."""
        vertices = self.geometry.get_hexagon_vertices(precision=1)
        self.assertEqual(len(vertices), 6)

        # Check first vertex (angle = 0)
        # x = 10 * cos(0) = 10, y = 10 * sin(0) = 0
        self.assertEqual(vertices[0], "10.0,0.0")

    def test_get_hexagon_vertices_precision(self):
        """Test hexagon vertex calculation with different precision."""
        vertices = self.geometry.get_hexagon_vertices(precision=3)
        self.assertEqual(len(vertices), 6)

        # Check that precision is applied (first vertex should be at angle 0)
        # x = 10 * cos(0) = 10.000, y = 10 * sin(0) = 0.000
        self.assertEqual(vertices[0], "10.000,0.000")

    def test_get_hexagon_path(self):
        """Test hexagon path generation."""
        path = self.geometry.get_hexagon_path(precision=2)
        vertices = self.geometry.get_hexagon_vertices(precision=2)
        expected_path = " ".join(vertices)

        self.assertEqual(path, expected_path)


class TestHexagonGridLayout(unittest.TestCase):
    """Test HexagonGridLayout class."""

    def setUp(self):
        """Set up test fixtures."""
        self.layout = HexagonGridLayout(hex_size=6, margin=10)

    def test_initialization(self):
        """Test HexagonGridLayout initialization."""
        self.assertEqual(self.layout.hex_size, 6)
        self.assertEqual(self.layout.margin, 10)

    def test_calculate_grid_bounds_empty(self):
        """Test grid bounds calculation with empty coordinates."""
        bounds = self.layout.calculate_grid_bounds([])
        self.assertEqual(bounds.width, 0)
        self.assertEqual(bounds.height, 0)

    def test_calculate_grid_bounds_single_point(self):
        """Test grid bounds calculation with single coordinate."""
        coords = [PixelCoordinate(50, 100)]
        bounds = self.layout.calculate_grid_bounds(coords)

        # min_x = 50 - 6 = 44, max_x = 50 + 6 = 56
        # min_y = 100 - 6 = 94, max_y = 100 + 6 = 106
        # width = 56 - 44 + 20 = 32, height = 106 - 94 + 20 = 32
        self.assertEqual(bounds.min_x, 44)
        self.assertEqual(bounds.max_x, 56)
        self.assertEqual(bounds.min_y, 94)
        self.assertEqual(bounds.max_y, 106)
        self.assertEqual(bounds.width, 32)
        self.assertEqual(bounds.height, 32)

    def test_calculate_grid_bounds_multiple_points(self):
        """Test grid bounds calculation with multiple coordinates."""
        coords = [
            PixelCoordinate(0, 0),
            PixelCoordinate(100, 50),
            PixelCoordinate(50, 100),
        ]
        bounds = self.layout.calculate_grid_bounds(coords)

        # min_x = 0 - 6 = -6, max_x = 100 + 6 = 106
        # min_y = 0 - 6 = -6, max_y = 100 + 6 = 106
        # width = 106 - (-6) + 20 = 132, height = 106 - (-6) + 20 = 132
        self.assertEqual(bounds.min_x, -6)
        self.assertEqual(bounds.max_x, 106)
        self.assertEqual(bounds.min_y, -6)
        self.assertEqual(bounds.max_y, 106)
        self.assertEqual(bounds.width, 132)
        self.assertEqual(bounds.height, 132)

    def test_calculate_legend_position_right(self):
        """Test legend position calculation for right side."""
        bounds = GridBounds(0, 100, 0, 50, 100, 50)
        legend_x, title_x = self.layout.calculate_legend_position(bounds, "right", 12)

        expected_legend_x = 100 - 12 - 5 - int(100 * 0.1)  # 100 - 12 - 5 - 10 = 73
        expected_title_x = expected_legend_x + 12 + 15  # 73 + 12 + 15 = 100

        self.assertEqual(legend_x, expected_legend_x)
        self.assertEqual(title_x, expected_title_x)

    def test_calculate_legend_position_left(self):
        """Test legend position calculation for left side."""
        bounds = GridBounds(0, 100, 0, 50, 100, 50)
        legend_x, title_x = self.layout.calculate_legend_position(bounds, "left", 12)

        expected_legend_x = -20
        expected_title_x = -20 + 12 + 15  # -20 + 12 + 15 = 7

        self.assertEqual(legend_x, expected_legend_x)
        self.assertEqual(title_x, expected_title_x)

    def test_calculate_coordinate_ranges_empty(self):
        """Test coordinate range calculation with empty points."""
        ranges = self.layout.calculate_coordinate_ranges([])
        self.assertEqual(ranges, (0, 0, 0, 0))

    def test_calculate_coordinate_ranges(self):
        """Test coordinate range calculation."""
        points = [
            HexagonPoint(1, 2),
            HexagonPoint(5, 3),
            HexagonPoint(3, 7),
            HexagonPoint(2, 1),
        ]
        min_hex1, max_hex1, min_hex2, max_hex2 = (
            self.layout.calculate_coordinate_ranges(points)
        )

        self.assertEqual(min_hex1, 1)
        self.assertEqual(max_hex1, 5)
        self.assertEqual(min_hex2, 1)
        self.assertEqual(max_hex2, 7)


class TestEyemapCoordinateSystem(unittest.TestCase):
    """Test EyemapCoordinateSystem class."""

    def setUp(self):
        """Set up test fixtures."""
        self.grid_system = EyemapCoordinateSystem(
            hex_size=6, spacing_factor=1.1, margin=10
        )

    def test_initialization(self):
        """Test EyemapCoordinateSystem initialization."""
        self.assertIsNotNone(self.grid_system.coordinate_system)
        self.assertIsNotNone(self.grid_system.geometry)
        self.assertIsNotNone(self.grid_system.layout)

    def test_convert_column_coordinates_empty(self):
        """Test column coordinate conversion with empty list."""
        result = self.grid_system.convert_column_coordinates([])
        self.assertEqual(result, [])

    def test_convert_column_coordinates(self):
        """Test column coordinate conversion."""
        columns = [
            {"hex1": 1, "hex2": 2, "value": 10},
            {"hex1": 3, "hex2": 4, "value": 20},
        ]

        result = self.grid_system.convert_column_coordinates(columns)

        self.assertEqual(len(result), 2)
        self.assertIn("x", result[0])
        self.assertIn("y", result[0])
        self.assertIn("x", result[1])
        self.assertIn("y", result[1])
        self.assertEqual(result[0]["value"], 10)
        self.assertEqual(result[1]["value"], 20)

    def test_convert_column_coordinates_with_mirror(self):
        """Test column coordinate conversion with mirroring."""
        columns = [{"hex1": 1, "hex2": 2, "value": 10}]

        result_normal = self.grid_system.convert_column_coordinates(columns)
        result_mirrored = self.grid_system.convert_column_coordinates(
            columns, mirror_side="left"
        )

        self.assertEqual(result_normal[0]["x"], -result_mirrored[0]["x"])
        self.assertEqual(result_normal[0]["y"], result_mirrored[0]["y"])

    def test_calculate_svg_layout_empty(self):
        """Test SVG layout calculation with empty columns."""
        result = self.grid_system.calculate_svg_layout([])
        self.assertEqual(result, {})

    def test_calculate_svg_layout(self):
        """Test SVG layout calculation."""
        columns = [{"x": 0, "y": 0}, {"x": 100, "y": 50}]

        result = self.grid_system.calculate_svg_layout(columns)

        self.assertIn("grid_bounds", result)
        self.assertIn("legend_x", result)
        self.assertIn("title_x", result)
        self.assertIn("hex_points", result)
        self.assertIn("width", result)
        self.assertIn("height", result)
        self.assertIn("min_x", result)
        self.assertIn("min_y", result)
        self.assertIn("margin", result)

    def test_calculate_svg_layout_with_soma_side(self):
        """Test SVG layout calculation with different soma sides."""
        columns = [{"x": 50, "y": 50}]

        result_right = self.grid_system.calculate_svg_layout(columns, "right")
        result_left = self.grid_system.calculate_svg_layout(columns, "left")

        self.assertNotEqual(result_right["legend_x"], result_left["legend_x"])
        self.assertNotEqual(result_right["title_x"], result_left["title_x"])


if __name__ == "__main__":
    unittest.main()
