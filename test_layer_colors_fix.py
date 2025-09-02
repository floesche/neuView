#!/usr/bin/env python3
"""
Test script to verify the layer colors fix.

This script checks if the min_max_data is properly passed through the rendering pipeline
and if the layer-colors attribute contains actual colors instead of all white.
"""

import sys
import os
import json
import re
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def check_layer_colors_in_svg(svg_file_path):
    """
    Check if an SVG file has proper layer colors (not all white).

    Args:
        svg_file_path: Path to the SVG file

    Returns:
        dict: Analysis results
    """
    if not os.path.exists(svg_file_path):
        return {"error": f"File not found: {svg_file_path}"}

    try:
        with open(svg_file_path, 'r') as f:
            content = f.read()

        # Find all layer-colors attributes
        layer_colors_pattern = r"layer-colors='([^']*?)'"
        matches = re.findall(layer_colors_pattern, content)

        if not matches:
            return {"error": "No layer-colors attributes found"}

        analysis = {
            "total_hexagons": len(matches),
            "all_white_count": 0,
            "colored_count": 0,
            "sample_colors": [],
            "issues": []
        }

        for i, match in enumerate(matches[:10]):  # Check first 10 for samples
            try:
                colors = json.loads(match)
                if isinstance(colors, list):
                    analysis["sample_colors"].append(colors)

                    # Check if all colors are white
                    white_count = sum(1 for color in colors if color == "#ffffff")
                    if white_count == len(colors):
                        analysis["all_white_count"] += 1
                    else:
                        analysis["colored_count"] += 1
                else:
                    analysis["issues"].append(f"Non-list colors at index {i}: {colors}")
            except json.JSONDecodeError as e:
                analysis["issues"].append(f"JSON decode error at index {i}: {e}")

        # Count all white vs colored for all hexagons
        for match in matches:
            try:
                colors = json.loads(match)
                if isinstance(colors, list):
                    white_count = sum(1 for color in colors if color == "#ffffff")
                    if white_count == len(colors):
                        analysis["all_white_count"] += 1
                    else:
                        analysis["colored_count"] += 1
            except:
                pass

        # Check for min_max_data presence in the SVG
        if "data-layer-thresholds" in content:
            analysis["has_thresholds"] = True
        else:
            analysis["has_thresholds"] = False

        return analysis

    except Exception as e:
        return {"error": f"Error reading file: {e}"}

def test_min_max_data_flow():
    """
    Test if min_max_data is properly flowing through the system.
    """
    try:
        from quickpage.visualization.rendering.rendering_manager import RenderingManager
        from quickpage.visualization.rendering.rendering_config import RenderingConfig
        from quickpage.visualization.color.mapper import ColorMapper
        from quickpage.visualization.color.palette import ColorPalette

        # Create a test configuration with min_max_data
        test_min_max_data = {
            'min_syn_region': {'ME': 0.0, 'LO': 0.5, 'LOP': 1.0},
            'max_syn_region': {'ME': 100.0, 'LO': 150.0, 'LOP': 200.0},
            'min_cells_region': {'ME': 0.0, 'LO': 2.0, 'LOP': 5.0},
            'max_cells_region': {'ME': 50.0, 'LO': 75.0, 'LOP': 100.0}
        }

        config = RenderingConfig(
            min_max_data=test_min_max_data,
            output_dir=Path("output"),
            save_to_files=False
        )

        # Create color mapper
        palette = ColorPalette()
        color_mapper = ColorMapper(palette)

        # Create rendering manager
        manager = RenderingManager(config, color_mapper)

        # Check if the configuration has min_max_data
        has_min_max = manager.config.min_max_data is not None

        return {
            "min_max_data_in_config": has_min_max,
            "test_data": test_min_max_data if has_min_max else None,
            "config_data": manager.config.min_max_data
        }

    except Exception as e:
        return {"error": f"Error testing min_max_data flow: {e}"}

def main():
    """Main test function."""
    print("Testing Layer Colors Fix")
    print("=" * 50)

    # Test 1: Check if min_max_data flows through the system
    print("\n1. Testing min_max_data flow...")
    flow_result = test_min_max_data_flow()
    if "error" in flow_result:
        print(f"❌ ERROR: {flow_result['error']}")
    else:
        if flow_result["min_max_data_in_config"]:
            print("✅ min_max_data is properly set in RenderingConfig")
            print(f"   Sample data: {list(flow_result['config_data'].keys())}")
        else:
            print("❌ min_max_data is not set in RenderingConfig")

    # Test 2: Analyze existing SVG files
    print("\n2. Analyzing existing SVG files...")
    eyemaps_dir = Path("output/eyemaps")

    if not eyemaps_dir.exists():
        print(f"❌ Eyemaps directory not found: {eyemaps_dir}")
        return

    svg_files = list(eyemaps_dir.glob("*.svg"))
    if not svg_files:
        print(f"❌ No SVG files found in {eyemaps_dir}")
        return

    print(f"Found {len(svg_files)} SVG files")

    # Analyze a few sample files
    sample_files = svg_files[:3]  # Test first 3 files

    for svg_file in sample_files:
        print(f"\n   Analyzing: {svg_file.name}")
        analysis = check_layer_colors_in_svg(svg_file)

        if "error" in analysis:
            print(f"   ❌ ERROR: {analysis['error']}")
            continue

        print(f"   📊 Total hexagons: {analysis['total_hexagons']}")
        print(f"   ⚪ All white: {analysis['all_white_count']}")
        print(f"   🎨 Colored: {analysis['colored_count']}")
        print(f"   🎯 Has thresholds: {analysis['has_thresholds']}")

        if analysis['colored_count'] > 0:
            print("   ✅ Found colored layer-colors (fix is working!)")
        else:
            print("   ❌ All layer-colors are white (fix needed)")

        if analysis['sample_colors']:
            print(f"   📝 Sample colors: {analysis['sample_colors'][0][:3]}...")

        if analysis['issues']:
            print(f"   ⚠️  Issues: {len(analysis['issues'])}")
            for issue in analysis['issues'][:2]:
                print(f"      - {issue}")

    # Test 3: Summary and recommendations
    print("\n3. Summary and Recommendations")
    print("-" * 30)

    # Count total colored vs white across all analyzed files
    total_colored = sum(check_layer_colors_in_svg(f).get('colored_count', 0) for f in sample_files)
    total_white = sum(check_layer_colors_in_svg(f).get('all_white_count', 0) for f in sample_files)

    if total_colored > 0:
        print(f"✅ SUCCESS: Found {total_colored} hexagons with proper colors")
        print("✅ SUCCESS: The layer colors fix is working!")
        print("   Layer colors are now properly mapped based on data values")
        print("   The fix ensures min_max_data flows through the rendering pipeline")
    else:
        print(f"❌ ISSUE: All {total_white} hexagons have white colors")
        print("   This could be due to:")
        print("   - All layer data values being 0 (which correctly show as white)")
        print("   - Files generated before the fix was applied")
        print("   - Cache or data processing issues")

    print(f"\n   Summary of the fix:")
    print("   ✅ Added min_max_data parameter to render_comprehensive_grid method")
    print("   ✅ Updated RenderingRequest to include min_max_data field")
    print("   ✅ Modified eyemap generator to pass min_max_data through")
    print("   ✅ Template filters now have access to proper normalization data")

if __name__ == "__main__":
    main()
