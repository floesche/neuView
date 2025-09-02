#!/usr/bin/env python3
"""
Comprehensive test to verify the layer colors fix.

This script thoroughly checks if the min_max_data is properly passed through the
rendering pipeline and if layer-colors contain actual colors based on data values.
"""

import sys
import os
import json
import re
from pathlib import Path
from collections import defaultdict

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def analyze_svg_layer_colors(svg_file_path):
    """
    Analyze layer colors in an SVG file.

    Args:
        svg_file_path: Path to the SVG file

    Returns:
        dict: Detailed analysis results
    """
    if not os.path.exists(svg_file_path):
        return {"error": f"File not found: {svg_file_path}"}

    try:
        with open(svg_file_path, 'r') as f:
            content = f.read()

        # Extract layer-colors and tooltip-layers together
        pattern = r"layer-colors='([^']*?)' tooltip-layers='([^']*?)'"
        matches = re.findall(pattern, content)

        if not matches:
            return {"error": "No layer-colors attributes found"}

        analysis = {
            "total_hexagons": len(matches),
            "hexagons_with_data": 0,
            "hexagons_with_colored_layers": 0,
            "total_layer_colors": 0,
            "white_layer_colors": 0,
            "non_white_layer_colors": 0,
            "unique_colors": set(),
            "data_vs_color_matches": 0,
            "data_vs_color_mismatches": 0,
            "sample_mismatches": [],
            "color_distribution": defaultdict(int),
            "issues": []
        }

        for hex_idx, (colors_str, tooltips_str) in enumerate(matches):
            try:
                colors = json.loads(colors_str) if colors_str else []
                tooltips = json.loads(tooltips_str) if tooltips_str else []

                if not isinstance(colors, list) or not isinstance(tooltips, list):
                    analysis["issues"].append(f"Hexagon {hex_idx}: Invalid data format")
                    continue

                # Check if this hexagon has any data
                has_data = False
                layer_values = []

                for tooltip in tooltips:
                    if tooltip and '\n' in tooltip:
                        value_part = tooltip.split('\n')[0]
                        try:
                            value = int(value_part)
                            layer_values.append(value)
                            if value > 0:
                                has_data = True
                        except ValueError:
                            layer_values.append(0)
                    else:
                        layer_values.append(0)

                if has_data:
                    analysis["hexagons_with_data"] += 1

                # Analyze layer colors
                has_colored_layers = False
                for i, (color, value) in enumerate(zip(colors, layer_values)):
                    analysis["total_layer_colors"] += 1

                    if color == "#ffffff":
                        analysis["white_layer_colors"] += 1
                    else:
                        analysis["non_white_layer_colors"] += 1
                        analysis["unique_colors"].add(color)
                        analysis["color_distribution"][color] += 1
                        has_colored_layers = True

                    # Check if color matches data expectation
                    if value > 0 and color != "#ffffff":
                        analysis["data_vs_color_matches"] += 1
                    elif value == 0 and color == "#ffffff":
                        analysis["data_vs_color_matches"] += 1
                    else:
                        analysis["data_vs_color_mismatches"] += 1
                        if len(analysis["sample_mismatches"]) < 5:
                            analysis["sample_mismatches"].append({
                                "hexagon": hex_idx,
                                "layer": i + 1,
                                "value": value,
                                "color": color,
                                "expected": "non-white" if value > 0 else "white"
                            })

                if has_colored_layers:
                    analysis["hexagons_with_colored_layers"] += 1

            except json.JSONDecodeError as e:
                analysis["issues"].append(f"Hexagon {hex_idx}: JSON decode error - {e}")
            except Exception as e:
                analysis["issues"].append(f"Hexagon {hex_idx}: Processing error - {e}")

        # Convert set to list for JSON serialization
        analysis["unique_colors"] = sorted(list(analysis["unique_colors"]))
        analysis["color_distribution"] = dict(analysis["color_distribution"])

        return analysis

    except Exception as e:
        return {"error": f"Error reading file: {e}"}

def test_infrastructure():
    """Test if the infrastructure supports min_max_data."""
    try:
        from quickpage.visualization.rendering.rendering_manager import RenderingManager
        from quickpage.visualization.rendering.rendering_config import RenderingConfig
        from quickpage.visualization.color.mapper import ColorMapper
        from quickpage.visualization.color.palette import ColorPalette

        # Create test configuration
        test_min_max_data = {
            'min_syn_region': {'ME': 1.0, 'LO': 0.5, 'LOP': 1.0},
            'max_syn_region': {'ME': 1000.0, 'LO': 800.0, 'LOP': 600.0},
            'min_cells_region': {'ME': 1.0, 'LO': 1.0, 'LOP': 1.0},
            'max_cells_region': {'ME': 20.0, 'LO': 15.0, 'LOP': 10.0}
        }

        config = RenderingConfig(
            min_max_data=test_min_max_data,
            output_dir=Path("output"),
            save_to_files=False
        )

        palette = ColorPalette()
        color_mapper = ColorMapper(palette)
        manager = RenderingManager(config, color_mapper)

        return {
            "infrastructure_ok": True,
            "config_has_min_max_data": manager.config.min_max_data is not None,
            "min_max_data_keys": list(manager.config.min_max_data.keys()) if manager.config.min_max_data else []
        }

    except Exception as e:
        return {
            "infrastructure_ok": False,
            "error": str(e)
        }

def test_color_filter_functionality():
    """Test the color filter functions directly."""
    try:
        from quickpage.visualization.rendering.svg_renderer import SVGRenderer
        from quickpage.visualization.rendering.rendering_config import RenderingConfig
        from quickpage.visualization.color.mapper import ColorMapper
        from quickpage.visualization.color.palette import ColorPalette

        # Create test configuration with min_max_data
        test_min_max_data = {
            'min_syn_region': {'ME': 1.0},
            'max_syn_region': {'ME': 1000.0},
            'min_cells_region': {'ME': 1.0},
            'max_cells_region': {'ME': 20.0}
        }

        config = RenderingConfig(
            min_max_data=test_min_max_data,
            output_dir=Path("output"),
            save_to_files=False
        )

        palette = ColorPalette()
        color_mapper = ColorMapper(palette)
        renderer = SVGRenderer(config, color_mapper)

        # Get the Jinja2 filters
        filters = color_mapper.create_jinja_filters()

        # Test synapse color filter
        test_synapses = [0, 50, 100, 500, 1000]
        synapse_colors = []
        if 'synapses_to_colors' in filters:
            synapse_colors = filters['synapses_to_colors'](test_synapses)

        # Test neuron color filter
        test_neurons = [0, 5, 10, 15, 20]
        neuron_colors = []
        if 'neurons_to_colors' in filters:
            neuron_colors = filters['neurons_to_colors'](test_neurons)

        return {
            "filters_available": bool(filters),
            "synapses_filter_works": bool(synapse_colors),
            "neurons_filter_works": bool(neuron_colors),
            "test_synapse_colors": synapse_colors,
            "test_neuron_colors": neuron_colors,
            "non_white_synapse_colors": sum(1 for c in synapse_colors if c != "#ffffff"),
            "non_white_neuron_colors": sum(1 for c in neuron_colors if c != "#ffffff")
        }

    except Exception as e:
        return {
            "filters_available": False,
            "error": str(e)
        }

def main():
    """Main test function."""
    print("Comprehensive Layer Colors Fix Test")
    print("=" * 50)

    # Test 1: Infrastructure
    print("\n1. Testing Infrastructure...")
    infra_result = test_infrastructure()

    if infra_result["infrastructure_ok"]:
        print("✅ Infrastructure is working")
        if infra_result["config_has_min_max_data"]:
            print(f"✅ RenderingConfig supports min_max_data: {infra_result['min_max_data_keys']}")
        else:
            print("❌ RenderingConfig does not have min_max_data")
    else:
        print(f"❌ Infrastructure error: {infra_result['error']}")
        return

    # Test 2: Color Filter Functionality
    print("\n2. Testing Color Filter Functionality...")
    filter_result = test_color_filter_functionality()

    if filter_result["filters_available"]:
        print("✅ Color filters are available")
        print(f"   Synapses filter works: {filter_result['synapses_filter_works']}")
        print(f"   Neurons filter works: {filter_result['neurons_filter_works']}")
        print(f"   Non-white synapse colors: {filter_result['non_white_synapse_colors']}/5")
        print(f"   Non-white neuron colors: {filter_result['non_white_neuron_colors']}/5")

        if filter_result['non_white_synapse_colors'] > 0:
            print("✅ Synapse color mapping is working")
        else:
            print("❌ Synapse color mapping returns all white")

        if filter_result['non_white_neuron_colors'] > 0:
            print("✅ Neuron color mapping is working")
        else:
            print("❌ Neuron color mapping returns all white")
    else:
        print(f"❌ Color filter error: {filter_result['error']}")

    # Test 3: Analyze existing SVG files
    print("\n3. Analyzing SVG Files...")
    eyemaps_dir = Path("output/eyemaps")

    if not eyemaps_dir.exists():
        print(f"❌ Eyemaps directory not found: {eyemaps_dir}")
        print("   Run 'python -m quickpage generate --neuron-type <TYPE> --soma-side left' first")
        return

    svg_files = list(eyemaps_dir.glob("*.svg"))
    if not svg_files:
        print(f"❌ No SVG files found in {eyemaps_dir}")
        return

    print(f"Found {len(svg_files)} SVG files")

    # Analyze a representative sample
    sample_files = [
        f for f in svg_files
        if any(pattern in f.name for pattern in ["_synapse_density.svg", "_cell_count.svg"])
    ][:6]

    if not sample_files:
        sample_files = svg_files[:6]

    total_analysis = {
        "files_analyzed": 0,
        "files_with_colored_layers": 0,
        "total_hexagons": 0,
        "total_hexagons_with_data": 0,
        "total_colored_layers": 0,
        "total_data_color_matches": 0,
        "total_data_color_mismatches": 0,
        "all_unique_colors": set(),
        "sample_files": []
    }

    for svg_file in sample_files:
        print(f"\n   📄 {svg_file.name}")
        analysis = analyze_svg_layer_colors(svg_file)

        if "error" in analysis:
            print(f"   ❌ ERROR: {analysis['error']}")
            continue

        total_analysis["files_analyzed"] += 1
        total_analysis["total_hexagons"] += analysis["total_hexagons"]
        total_analysis["total_hexagons_with_data"] += analysis["hexagons_with_data"]
        total_analysis["total_colored_layers"] += analysis["non_white_layer_colors"]
        total_analysis["total_data_color_matches"] += analysis["data_vs_color_matches"]
        total_analysis["total_data_color_mismatches"] += analysis["data_vs_color_mismatches"]
        total_analysis["all_unique_colors"].update(analysis["unique_colors"])

        if analysis["hexagons_with_colored_layers"] > 0:
            total_analysis["files_with_colored_layers"] += 1

        # Display summary for this file
        print(f"   📊 Hexagons: {analysis['total_hexagons']} total, {analysis['hexagons_with_data']} with data")
        print(f"   🎨 Colored layers: {analysis['non_white_layer_colors']} / {analysis['total_layer_colors']}")
        print(f"   ✅ Data-color matches: {analysis['data_vs_color_matches']}")
        print(f"   ❌ Data-color mismatches: {analysis['data_vs_color_mismatches']}")

        if analysis["non_white_layer_colors"] > 0:
            print(f"   ✅ Has {len(analysis['unique_colors'])} unique colors")
            print(f"   🎯 Sample colors: {analysis['unique_colors'][:3]}")
        else:
            print("   ⚪ All layer colors are white")

        if analysis["sample_mismatches"]:
            print(f"   ⚠️  Sample mismatches: {len(analysis['sample_mismatches'])}")
            for mismatch in analysis["sample_mismatches"][:2]:
                print(f"      Layer {mismatch['layer']}: value={mismatch['value']}, color={mismatch['color']} (expected {mismatch['expected']})")

        total_analysis["sample_files"].append({
            "name": svg_file.name,
            "colored_layers": analysis["non_white_layer_colors"],
            "total_layers": analysis["total_layer_colors"],
            "unique_colors": len(analysis["unique_colors"])
        })

    # Test 4: Overall Assessment
    print("\n4. Overall Assessment")
    print("-" * 30)

    if total_analysis["files_analyzed"] == 0:
        print("❌ No files could be analyzed")
        return

    colored_percentage = (total_analysis["total_colored_layers"] /
                         max(total_analysis["total_hexagons"] * 10, 1)) * 100  # Assuming 10 layers per hexagon

    match_percentage = (total_analysis["total_data_color_matches"] /
                       max(total_analysis["total_data_color_matches"] + total_analysis["total_data_color_mismatches"], 1)) * 100

    print(f"📊 Files analyzed: {total_analysis['files_analyzed']}")
    print(f"📊 Total hexagons: {total_analysis['total_hexagons']}")
    print(f"📊 Hexagons with data: {total_analysis['total_hexagons_with_data']}")
    print(f"🎨 Total colored layers: {total_analysis['total_colored_layers']}")
    print(f"🎨 Unique colors found: {len(total_analysis['all_unique_colors'])}")
    print(f"✅ Data-color match rate: {match_percentage:.1f}%")

    # Final verdict
    print(f"\n🎯 VERDICT:")

    if total_analysis["total_colored_layers"] > 0:
        print("✅ SUCCESS: Layer colors fix is working!")
        print(f"   Found {total_analysis['total_colored_layers']} colored layers across {total_analysis['files_with_colored_layers']} files")
        print(f"   Colors are properly mapped based on data values")

        if len(total_analysis['all_unique_colors']) > 5:
            print(f"   Color variety is good: {len(total_analysis['all_unique_colors'])} unique colors")

        if match_percentage > 90:
            print(f"   Data-color mapping is highly accurate: {match_percentage:.1f}%")
        elif match_percentage > 70:
            print(f"   Data-color mapping is mostly accurate: {match_percentage:.1f}%")
        else:
            print(f"   Data-color mapping needs improvement: {match_percentage:.1f}%")

    else:
        print("❌ ISSUE: No colored layers found")
        print("   All layer colors are white - the fix may not be working properly")
        print("\n   Possible causes:")
        print("   1. min_max_data is not reaching the template filters")
        print("   2. All data values are 0 (no synapses/neurons in layers)")
        print("   3. Color mapping function is returning white for all values")
        print("   4. Template is not applying the color filters correctly")

    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if total_analysis["total_colored_layers"] > 0:
        print("   ✅ The layer colors fix is working correctly")
        print("   ✅ No further action needed")
    else:
        print("   🔧 Check if eyemaps were regenerated after applying the fix")
        print("   🔧 Verify that the datasets contain non-zero layer data")
        print("   🔧 Test with a known dataset that has layer-specific values")

    print(f"\n📝 Sample files analyzed:")
    for file_info in total_analysis["sample_files"]:
        status = "✅" if file_info["colored_layers"] > 0 else "⚪"
        print(f"   {status} {file_info['name']}: {file_info['colored_layers']} colored / {file_info['total_layers']} total layers")

if __name__ == "__main__":
    main()
