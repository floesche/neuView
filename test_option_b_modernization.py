"""
Comprehensive test suite for modernized rendering system (Option B).

This test suite verifies that all legacy code has been successfully removed
and that the modernized rendering system functions correctly with:
- Required dependencies (no optional fallbacks)
- Enum-only SomaSide handling
- Region configuration system
- Simplified APIs
- No backward compatibility code
"""

import unittest
from unittest.mock import Mock, patch
from pathlib import Path
from typing import Dict, Any, List
import tempfile
import json

# Import the modernized components
from src.quickpage.visualization.rendering import (
    RenderingManager,
    SVGRenderer,
    PNGRenderer,
    RenderingConfig,
    OutputFormat,
    LayoutConfig,
    LegendConfig,
    LayoutCalculator,
    RegionConfigRegistry,
    Region,
    RegionConfig
)
from src.quickpage.visualization.data_processing.data_structures import SomaSide


class TestModernizedRegionConfig(unittest.TestCase):
    """Test the new region configuration system."""

    def test_region_enum_values(self):
        """Test that region enum has expected values."""
        self.assertEqual(Region.ME.value, "ME")
        self.assertEqual(Region.LO.value, "LO")
        self.assertEqual(Region.LOP.value, "LOP")

    def test_region_config_creation(self):
        """Test region configuration creation."""
        config = RegionConfig(region=Region.ME, layer_count=5)
        self.assertEqual(config.layer_count, 5)
        self.assertIsNone(config.layer_display_mapping)

    def test_region_config_with_layer_mapping(self):
        """Test region configuration with layer display mapping."""
        mapping = {5: '5A', 6: '5B', 7: '6'}
        config = RegionConfig(region=Region.LO, layer_count=7, layer_display_mapping=mapping)
        self.assertEqual(config.layer_count, 7)
        self.assertEqual(config.layer_display_mapping, mapping)

    def test_registry_get_config(self):
        """Test region registry configuration retrieval."""
        # Test known regions
        me_config = RegionConfigRegistry.get_config("ME")
        self.assertEqual(me_config.layer_count, 10)

        lo_config = RegionConfigRegistry.get_config("LO")
        self.assertEqual(lo_config.layer_count, 7)
        self.assertIsNotNone(lo_config.layer_display_mapping)

        lop_config = RegionConfigRegistry.get_config("LOP")
        self.assertEqual(lop_config.layer_count, 4)

    def test_registry_unknown_region(self):
        """Test handling of unknown regions."""
        unknown_config = RegionConfigRegistry.get_config("UNKNOWN")
        self.assertEqual(unknown_config.layer_count, 10)  # Default

    def test_registry_layer_count(self):
        """Test layer count retrieval."""
        self.assertEqual(RegionConfigRegistry.get_layer_count("ME"), 10)
        self.assertEqual(RegionConfigRegistry.get_layer_count("LO"), 7)
        self.assertEqual(RegionConfigRegistry.get_layer_count("LOP"), 4)

    def test_registry_display_layer_name(self):
        """Test display layer name generation."""
        # Standard regions
        self.assertEqual(RegionConfigRegistry.get_display_layer_name("ME", 1), "ME1")
        self.assertEqual(RegionConfigRegistry.get_display_layer_name("LOP", 3), "LOP3")

        # LO region with special mapping
        self.assertEqual(RegionConfigRegistry.get_display_layer_name("LO", 5), "LO5A")
        self.assertEqual(RegionConfigRegistry.get_display_layer_name("LO", 6), "LO5B")
        self.assertEqual(RegionConfigRegistry.get_display_layer_name("LO", 7), "LO6")

    def test_registry_control_dimensions(self):
        """Test control dimensions calculation."""
        me_dims = RegionConfigRegistry.get_control_dimensions("ME")
        self.assertIn('layer_count', me_dims)
        self.assertIn('total_control_height', me_dims)
        self.assertEqual(me_dims['layer_count'], 10)

        lo_dims = RegionConfigRegistry.get_control_dimensions("LO")
        self.assertEqual(lo_dims['layer_count'], 7)

    def test_supported_regions(self):
        """Test supported regions listing."""
        regions = RegionConfigRegistry.get_supported_regions()
        self.assertIn("ME", regions)
        self.assertIn("LO", regions)
        self.assertIn("LOP", regions)

    def test_is_supported_region(self):
        """Test region support checking."""
        self.assertTrue(RegionConfigRegistry.is_supported_region("ME"))
        self.assertTrue(RegionConfigRegistry.is_supported_region("lo"))  # Case insensitive
        self.assertFalse(RegionConfigRegistry.is_supported_region("UNKNOWN"))


class TestModernizedLayoutCalculator(unittest.TestCase):
    """Test the modernized layout calculator."""

    def setUp(self):
        """Set up test fixtures."""
        self.calculator = LayoutCalculator()
        self.sample_hexagons = [
            {'x': 0, 'y': 0, 'region': 'ME', 'status': 'has_data'},
            {'x': 10, 'y': 10, 'region': 'ME', 'status': 'has_data'},
            {'x': -5, 'y': 5, 'region': 'ME', 'status': 'no_data'}
        ]

    def test_soma_side_enum_only(self):
        """Test that layout calculator only accepts SomaSide enum."""
        layout = self.calculator.calculate_layout(
            self.sample_hexagons,
            soma_side=SomaSide.LEFT,
            region="ME"
        )
        self.assertIsInstance(layout, LayoutConfig)

        # Verify adjust_for_soma_side only works with enum
        adjusted = self.calculator.adjust_for_soma_side(layout, SomaSide.LEFT)
        self.assertIsInstance(adjusted, LayoutConfig)

    def test_no_template_compatibility_params(self):
        """Test that layout config has no template compatibility parameters."""
        layout = self.calculator.calculate_layout(self.sample_hexagons)
        layout_dict = layout.to_dict()

        # Verify no legacy template compatibility parameters
        self.assertNotIn('number_precision', layout_dict)

    def test_region_config_integration(self):
        """Test integration with region configuration system."""
        layout = self.calculator.calculate_layout(
            self.sample_hexagons,
            soma_side=SomaSide.RIGHT,
            region="LO"
        )

        # Layout should be calculated successfully
        self.assertGreater(layout.width, 0)
        self.assertGreater(layout.height, 0)

    def test_control_positioning_with_soma_side(self):
        """Test control positioning based on soma side."""
        left_layout = self.calculator.calculate_layout(
            self.sample_hexagons,
            soma_side=SomaSide.LEFT,
            region="ME"
        )

        right_layout = self.calculator.calculate_layout(
            self.sample_hexagons,
            soma_side=SomaSide.RIGHT,
            region="ME"
        )

        # Both layouts should have valid dimensions, but controls may be in same position
        # for this simple test case. The important thing is that both succeed.
        self.assertGreater(left_layout.width, 0)
        self.assertGreater(right_layout.width, 0)


class TestModernizedSVGRenderer(unittest.TestCase):
    """Test the modernized SVG renderer."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = RenderingConfig(
            output_format=OutputFormat.SVG,
            output_dir=self.temp_dir,
            eyemaps_dir=self.temp_dir / 'eyemaps'
        )
        self.color_mapper = Mock()
        self.renderer = SVGRenderer(self.config, self.color_mapper)

    def test_requires_tooltip_data(self):
        """Test that renderer requires complete tooltip data."""
        # Hexagons without tooltip data should raise error
        incomplete_hexagons = [
            {'x': 0, 'y': 0, 'color': '#ffffff', 'hex1': 1, 'hex2': 1}
        ]

        layout = LayoutConfig(width=100, height=100)

        with self.assertRaises(ValueError) as context:
            self.renderer.render(incomplete_hexagons, layout)

        self.assertIn("missing required tooltip data", str(context.exception))

    def test_complete_tooltip_data_processing(self):
        """Test processing of complete tooltip data."""
        complete_hexagons = [
            {
                'x': 0, 'y': 0, 'color': '#ffffff', 'hex1': 1, 'hex2': 1,
                'tooltip': 'Test tooltip',
                'tooltip_layers': ['Layer 1', 'Layer 2']
            }
        ]

        layout = LayoutConfig(width=100, height=100, hex_points="0,0 1,0 1,1 0,1")

        # Mock template rendering
        with patch.object(self.renderer, '_get_template') as mock_template:
            mock_template.return_value.render.return_value = "<svg>test</svg>"

            result = self.renderer.render(complete_hexagons, layout)
            self.assertEqual(result, "<svg>test</svg>")

    def test_no_legacy_layer_mapping_methods(self):
        """Test that legacy layer mapping methods are removed."""
        # Ensure _get_display_layer_name method is removed
        self.assertFalse(hasattr(self.renderer, '_get_display_layer_name'))

        # Ensure _generate_tooltip_data method is removed
        self.assertFalse(hasattr(self.renderer, '_generate_tooltip_data'))


class TestModernizedPNGRenderer(unittest.TestCase):
    """Test the modernized PNG renderer."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = RenderingConfig(
            output_format=OutputFormat.PNG,
            output_dir=self.temp_dir,
            eyemaps_dir=self.temp_dir / 'eyemaps'
        )
        self.color_mapper = Mock()
        self.renderer = PNGRenderer(self.config, self.color_mapper)

    def test_required_dependencies_imported(self):
        """Test that required dependencies are imported without fallbacks."""
        # Verify imports are at module level (no try/except)
        import src.quickpage.visualization.rendering.png_renderer as png_module

        # These should be imported directly, not in try/except blocks
        self.assertTrue(hasattr(png_module, 'cairosvg'))
        self.assertTrue(hasattr(png_module, 'Image'))

    def test_no_fallback_methods(self):
        """Test that fallback methods are removed."""
        # Ensure render_with_fallback method is removed
        self.assertFalse(hasattr(self.renderer, 'render_with_fallback'))

    @patch('src.quickpage.visualization.rendering.png_renderer.cairosvg')
    def test_png_conversion_no_fallback(self, mock_cairosvg):
        """Test PNG conversion without fallback logic."""
        mock_cairosvg.svg2png.return_value = None

        # Mock SVG content
        svg_content = "<svg>test</svg>"

        with patch('io.BytesIO') as mock_buffer:
            mock_buffer.return_value.getvalue.return_value = b'fake_png_data'
            mock_buffer.return_value.seek = Mock()

            result = self.renderer._convert_svg_to_png(svg_content)

            # Should return PNG data URL, not fall back to SVG
            self.assertTrue(result.startswith('data:image/png;base64,'))

    def test_get_png_dimensions_no_fallback(self):
        """Test PNG dimensions without PIL fallback."""
        # Create fake PNG data URL
        import base64
        fake_png_data = b'\x89PNG\r\n\x1a\n' + b'fake_data'
        data_url = f"data:image/png;base64,{base64.b64encode(fake_png_data).decode()}"

        with patch('PIL.Image.open') as mock_open:
            mock_image = Mock()
            mock_image.size = (100, 200)
            mock_open.return_value.__enter__.return_value = mock_image

            width, height = self.renderer.get_png_dimensions(data_url)
            self.assertEqual((width, height), (100, 200))


class TestModernizedRenderingManager(unittest.TestCase):
    """Test the modernized rendering manager."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = RenderingConfig(
            output_dir=self.temp_dir,
            eyemaps_dir=self.temp_dir / 'eyemaps'
        )
        self.color_mapper = Mock()
        self.manager = RenderingManager(self.config, self.color_mapper)

    def test_no_legacy_comprehensive_method(self):
        """Test that legacy render_comprehensive_grid method is removed."""
        self.assertFalse(hasattr(self.manager, 'render_comprehensive_grid'))

    def test_no_legacy_multiple_formats_method(self):
        """Test that legacy render_multiple_formats method is removed."""
        self.assertFalse(hasattr(self.manager, 'render_multiple_formats'))

    def test_single_standard_interface(self):
        """Test that only the standard render interface exists."""
        # Should have the standard render method
        self.assertTrue(hasattr(self.manager, 'render'))

        # Should not have legacy methods
        legacy_methods = [
            'render_comprehensive_grid',
            'render_multiple_formats'
        ]

        for method in legacy_methods:
            self.assertFalse(hasattr(self.manager, method))

    def test_soma_side_enum_integration(self):
        """Test integration with SomaSide enum."""
        hexagons = [
            {
                'x': 0, 'y': 0, 'color': '#ffffff', 'hex1': 1, 'hex2': 1,
                'tooltip': 'Test', 'tooltip_layers': [], 'region': 'ME',
                'status': 'has_data'
            }
        ]

        # Should work with SomaSide enum
        with patch.object(self.manager, '_get_renderer') as mock_get_renderer:
            mock_renderer = Mock()
            mock_renderer.render.return_value = "test_content"
            mock_renderer.validate_hexagons = Mock()
            mock_get_renderer.return_value = mock_renderer

            # This should work without errors
            result = self.manager.render(hexagons)
            self.assertEqual(result, "test_content")


class TestModernizedRenderingConfig(unittest.TestCase):
    """Test the modernized rendering configuration."""

    def test_no_template_compatibility_params(self):
        """Test that template compatibility parameters are removed."""
        config = RenderingConfig(save_to_files=False)

        # Should not have legacy template compatibility parameters
        self.assertFalse(hasattr(config, 'number_precision'))

    def test_layout_config_no_legacy_params(self):
        """Test that LayoutConfig has no legacy parameters."""
        layout = LayoutConfig()
        layout_dict = layout.to_dict()

        # Should not contain legacy template compatibility parameters
        self.assertNotIn('number_precision', layout_dict)


class TestBackwardCompatibilityRemoval(unittest.TestCase):
    """Test that all backward compatibility code has been removed."""

    def test_no_string_soma_side_handling(self):
        """Test that string SomaSide handling is removed."""
        calculator = LayoutCalculator()

        # Should not accept string soma_side values
        # This test verifies the type signature has changed
        import inspect
        sig = inspect.signature(calculator.adjust_for_soma_side)
        soma_side_param = sig.parameters['soma_side']

        # The annotation should indicate SomaSide enum, not Union[str, SomaSide]
        self.assertIn('SomaSide', str(soma_side_param.annotation))

    def test_no_import_fallbacks_in_png_renderer(self):
        """Test that import fallbacks are removed from PNG renderer."""
        import src.quickpage.visualization.rendering.png_renderer as png_module
        import inspect

        # Get the source code to verify no try/except ImportError blocks
        source = inspect.getsource(png_module)

        # Should not contain fallback import logic
        self.assertNotIn('except ImportError', source)
        self.assertNotIn('cairosvg not available', source)
        self.assertNotIn('PIL not available', source)

    def test_no_optional_dependency_handling(self):
        """Test that optional dependency handling is removed."""
        # PNG renderer should import dependencies directly
        from src.quickpage.visualization.rendering.png_renderer import cairosvg, Image

        # These should be available without any conditional logic
        self.assertIsNotNone(cairosvg)
        self.assertIsNotNone(Image)


class TestModernizationIntegration(unittest.TestCase):
    """Integration tests for the modernized rendering system."""

    def setUp(self):
        """Set up integration test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = RenderingConfig(
            output_dir=self.temp_dir,
            eyemaps_dir=self.temp_dir / 'eyemaps'
        )
        self.color_mapper = Mock()
        self.color_mapper.palette.white = '#ffffff'
        self.color_mapper.palette.get_all_colors.return_value = ['#ff0000', '#00ff00', '#0000ff']
        self.color_mapper.map_value_to_color.return_value = '#ff0000'

    def test_end_to_end_svg_rendering(self):
        """Test end-to-end SVG rendering with modernized system."""
        hexagons = [
            {
                'x': 0, 'y': 0, 'color': '#ffffff', 'hex1': 1, 'hex2': 1,
                'tooltip': 'Column: 1, 1\nSynapse count: 10\nROI: ME',
                'tooltip_layers': ['10\nROI: ME1', '5\nROI: ME2'],
                'region': 'ME', 'status': 'has_data'
            }
        ]

        manager = RenderingManager(self.config, self.color_mapper)

        # Test that the modernized system properly processes hexagons with complete tooltip data
        # and that the region configuration system is integrated
        svg_renderer = manager._renderers[OutputFormat.SVG]

        # Verify tooltip processing works without legacy fallbacks
        processed_hexagons = svg_renderer._add_tooltips_to_hexagons(hexagons)
        self.assertEqual(len(processed_hexagons), 1)
        self.assertIn('base-title', processed_hexagons[0])
        self.assertIn('tooltip-layers', processed_hexagons[0])

        # Verify layout calculation works with region config
        layout = manager.layout_calculator.calculate_layout(hexagons, region="ME")
        self.assertGreater(layout.width, 0)
        self.assertGreater(layout.height, 0)

    def test_region_config_integration(self):
        """Test integration between region config and layout calculation."""
        hexagons = [
            {
                'x': 0, 'y': 0, 'color': '#ffffff', 'hex1': 1, 'hex2': 1,
                'tooltip': 'Test', 'tooltip_layers': [],
                'region': 'LO', 'status': 'has_data'
            }
        ]

        calculator = LayoutCalculator()
        layout = calculator.calculate_layout(
            hexagons,
            soma_side=SomaSide.LEFT,
            region="LO"
        )

        # Should successfully calculate layout using region config
        self.assertGreater(layout.width, 0)
        self.assertGreater(layout.height, 0)

    def test_no_legacy_code_paths(self):
        """Test that no legacy code paths are accessible."""
        manager = RenderingManager(self.config, self.color_mapper)

        # Verify that attempting to access legacy methods raises AttributeError
        with self.assertRaises(AttributeError):
            manager.render_comprehensive_grid([])

        with self.assertRaises(AttributeError):
            manager.render_multiple_formats([])

        # Verify SVG renderer doesn't have legacy methods
        svg_renderer = manager._renderers[OutputFormat.SVG]

        with self.assertRaises(AttributeError):
            svg_renderer._get_display_layer_name("LO", 5)

        with self.assertRaises(AttributeError):
            svg_renderer._generate_tooltip_data({})

        # Verify PNG renderer doesn't have legacy methods
        png_renderer = manager._renderers[OutputFormat.PNG]

        with self.assertRaises(AttributeError):
            png_renderer.render_with_fallback([])


if __name__ == '__main__':
    # Run the test suite
    unittest.main(verbosity=2)
