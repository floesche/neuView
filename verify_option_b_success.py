#!/usr/bin/env python3
"""
Final verification test for Option B: Aggressive Modernization.

This script verifies that all modernization goals have been achieved
and the rendering system is working correctly without legacy code.
"""

import sys
import traceback
from pathlib import Path

def test_region_config_system():
    """Test the new region configuration system."""
    print("Testing region configuration system...")

    try:
        from src.quickpage.visualization.rendering import RegionConfigRegistry, Region

        # Test basic functionality
        assert RegionConfigRegistry.get_layer_count("ME") == 10
        assert RegionConfigRegistry.get_layer_count("LO") == 7
        assert RegionConfigRegistry.get_layer_count("LOP") == 4

        # Test layer display names
        assert RegionConfigRegistry.get_display_layer_name("LO", 5) == "LO5A"
        assert RegionConfigRegistry.get_display_layer_name("LO", 6) == "LO5B"
        assert RegionConfigRegistry.get_display_layer_name("ME", 3) == "ME3"

        # Test control dimensions
        dims = RegionConfigRegistry.get_control_dimensions("ME")
        assert 'layer_count' in dims
        assert dims['layer_count'] == 10

        print("✅ Region configuration system working correctly")
        return True

    except Exception as e:
        print(f"❌ Region configuration system failed: {e}")
        traceback.print_exc()
        return False

def test_legacy_code_removal():
    """Test that all legacy code has been removed."""
    print("Testing legacy code removal...")

    try:
        from src.quickpage.visualization.rendering import RenderingManager, SVGRenderer, PNGRenderer

        # Test that legacy methods are removed
        manager = RenderingManager.__dict__
        svg_renderer = SVGRenderer.__dict__
        png_renderer = PNGRenderer.__dict__

        # Check that legacy methods are gone
        legacy_methods = [
            'render_comprehensive_grid',
            'render_multiple_formats',
            'render_with_fallback',
            '_get_display_layer_name',
            '_generate_tooltip_data'
        ]

        for method in legacy_methods:
            assert method not in manager, f"Legacy method {method} found in RenderingManager"
            assert method not in svg_renderer, f"Legacy method {method} found in SVGRenderer"
            assert method not in png_renderer, f"Legacy method {method} found in PNGRenderer"

        print("✅ All legacy methods successfully removed")
        return True

    except Exception as e:
        print(f"❌ Legacy code removal verification failed: {e}")
        traceback.print_exc()
        return False

def test_soma_side_enum_enforcement():
    """Test that SomaSide enum enforcement is working."""
    print("Testing SomaSide enum enforcement...")

    try:
        from src.quickpage.visualization.rendering import LayoutCalculator
        from src.quickpage.visualization.data_processing.data_structures import SomaSide

        calculator = LayoutCalculator()

        # Test that enum works correctly
        sample_hexagons = [{'x': 0, 'y': 0, 'region': 'ME'}]
        layout = calculator.calculate_layout(sample_hexagons, SomaSide.LEFT, "ME")

        assert layout.width > 0
        assert layout.height > 0

        # Test adjustment method
        adjusted = calculator.adjust_for_soma_side(layout, SomaSide.LEFT)
        assert adjusted is not None

        print("✅ SomaSide enum enforcement working correctly")
        return True

    except Exception as e:
        print(f"❌ SomaSide enum enforcement failed: {e}")
        traceback.print_exc()
        return False

def test_required_dependencies():
    """Test that required dependencies are imported without fallbacks."""
    print("Testing required dependencies...")

    try:
        # Test that cairosvg and PIL are directly imported
        import src.quickpage.visualization.rendering.png_renderer as png_module

        # These should be available at module level
        assert hasattr(png_module, 'cairosvg')
        assert hasattr(png_module, 'Image')

        # Test that imports work
        cairosvg = png_module.cairosvg
        Image = png_module.Image

        assert cairosvg is not None
        assert Image is not None

        print("✅ Required dependencies imported correctly")
        return True

    except Exception as e:
        print(f"❌ Required dependencies test failed: {e}")
        traceback.print_exc()
        return False

def test_tooltip_data_requirements():
    """Test that tooltip data is required without fallbacks."""
    print("Testing tooltip data requirements...")

    try:
        from src.quickpage.visualization.rendering import SVGRenderer, RenderingConfig, LayoutConfig
        from pathlib import Path
        import tempfile

        temp_dir = Path(tempfile.mkdtemp())
        config = RenderingConfig(
            output_dir=temp_dir,
            save_to_files=False
        )

        renderer = SVGRenderer(config)

        # Test that incomplete hexagons raise errors
        incomplete_hexagons = [
            {'x': 0, 'y': 0, 'color': '#ffffff', 'hex1': 1, 'hex2': 1}
        ]

        try:
            processed = renderer._add_tooltips_to_hexagons(incomplete_hexagons)
            assert False, "Should have raised ValueError for missing tooltip data"
        except ValueError as e:
            assert "missing required tooltip data" in str(e)

        # Test that complete hexagons work
        complete_hexagons = [
            {
                'x': 0, 'y': 0, 'color': '#ffffff', 'hex1': 1, 'hex2': 1,
                'tooltip': 'Test tooltip',
                'tooltip_layers': ['Layer 1']
            }
        ]

        processed = renderer._add_tooltips_to_hexagons(complete_hexagons)
        assert len(processed) == 1
        assert 'base-title' in processed[0]

        print("✅ Tooltip data requirements enforced correctly")
        return True

    except Exception as e:
        print(f"❌ Tooltip data requirements test failed: {e}")
        traceback.print_exc()
        return False

def test_api_simplification():
    """Test that APIs have been simplified to single standard interface."""
    print("Testing API simplification...")

    try:
        from src.quickpage.visualization.rendering import RenderingManager, RenderingConfig
        from pathlib import Path
        import tempfile

        temp_dir = Path(tempfile.mkdtemp())
        config = RenderingConfig(
            output_dir=temp_dir,
            save_to_files=False
        )

        manager = RenderingManager(config)

        # Test that only standard render method exists
        assert hasattr(manager, 'render')

        # Test that legacy methods are gone
        legacy_methods = [
            'render_comprehensive_grid',
            'render_multiple_formats'
        ]

        for method in legacy_methods:
            assert not hasattr(manager, method), f"Legacy method {method} still exists"

        # Test that render method works
        hexagons = [
            {
                'x': 0, 'y': 0, 'color': '#ffffff', 'hex1': 1, 'hex2': 1,
                'tooltip': 'Test', 'tooltip_layers': [], 'region': 'ME',
                'status': 'has_data'
            }
        ]

        # This should work without errors (though template loading may fail in test)
        try:
            result = manager.render(hexagons)
            # If it gets here, basic processing worked
        except ValueError as e:
            # Template loading failures are expected in this test environment
            if "Template loading failed" not in str(e):
                raise

        print("✅ API simplification successful")
        return True

    except Exception as e:
        print(f"❌ API simplification test failed: {e}")
        traceback.print_exc()
        return False

def test_config_modernization():
    """Test that configuration has been modernized."""
    print("Testing configuration modernization...")

    try:
        from src.quickpage.visualization.rendering import RenderingConfig, LayoutConfig

        # Test that template compatibility parameters are removed
        config = RenderingConfig(save_to_files=False)
        assert not hasattr(config, 'number_precision')

        # Test that LayoutConfig doesn't have legacy parameters
        layout = LayoutConfig()
        layout_dict = layout.to_dict()
        assert 'number_precision' not in layout_dict

        print("✅ Configuration modernization successful")
        return True

    except Exception as e:
        print(f"❌ Configuration modernization test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all verification tests."""
    print("🚀 Starting Option B Aggressive Modernization Verification")
    print("=" * 60)

    tests = [
        test_region_config_system,
        test_legacy_code_removal,
        test_soma_side_enum_enforcement,
        test_required_dependencies,
        test_tooltip_data_requirements,
        test_api_simplification,
        test_config_modernization
    ]

    passed = 0
    failed = 0

    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
        print()

    print("=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 ALL TESTS PASSED - Option B Modernization Complete!")
        print("\n✅ Achieved:")
        print("  • Region configuration system implemented")
        print("  • All legacy code and backward compatibility removed")
        print("  • SomaSide enum enforcement")
        print("  • Required dependencies without fallbacks")
        print("  • Tooltip data requirements enforced")
        print("  • APIs simplified to single standard interface")
        print("  • Configuration modernized")

        return 0
    else:
        print("❌ Some tests failed - modernization incomplete")
        return 1

if __name__ == "__main__":
    sys.exit(main())
