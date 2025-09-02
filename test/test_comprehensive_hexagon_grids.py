#!/usr/bin/env python3
"""
Test script for comprehensive hexagonal grid generation.

This script demonstrates the new comprehensive hexagonal grid functionality
that shows all possible column coordinates across ME, LO, and LOP regions,
with different colors for:
- Dark gray: Column doesn't exist in this region
- White: Column exists in region but no data for current dataset
- Color-coded: Column has data in this region for current dataset
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from quickpage.visualization import EyemapGenerator


def create_sample_data_with_gaps():
    """Create sample data that demonstrates all three column states."""
    return [
        {
            'hex1': 31, 'hex2': 16, 'region': 'ME', 'side': 'left',
            'total_synapses': 1200, 'neuron_count': 45,
            'column_name': 'ME_L_31_16'
        },
        {
            'hex1': 30, 'hex2': 15, 'region': 'ME', 'side': 'left',
            'total_synapses': 980, 'neuron_count': 38,
            'column_name': 'ME_L_30_15'
        },
        # Gap: Column (29, 14) exists but has no data for this neuron type
        {
            'hex1': 28, 'hex2': 13, 'region': 'LO', 'side': 'right',
            'total_synapses': 800, 'neuron_count': 30,
            'column_name': 'LO_R_28_13'
        },
        {
            'hex1': 27, 'hex2': 12, 'region': 'LO', 'side': 'right',
            'total_synapses': 1100, 'neuron_count': 42,
            'column_name': 'LO_R_27_12'
        },
        # Gap: Column (26, 11) exists but has no data for this neuron type
        {
            'hex1': 25, 'hex2': 10, 'region': 'LOP', 'side': 'left',
            'total_synapses': 1300, 'neuron_count': 48,
            'column_name': 'LOP_L_25_10'
        },
        # Gap: Column (24, 9) exists but has no data for this neuron type
    ]


def create_all_possible_columns():
    """Create list of all possible column coordinates found in the dataset."""
    return [
        # Columns that exist in ME
        {'hex1': 31, 'hex2': 16},
        {'hex1': 30, 'hex2': 15},
        {'hex1': 29, 'hex2': 14},  # Exists in ME but no data

        # Columns that exist in LO
        {'hex1': 28, 'hex2': 13},
        {'hex1': 27, 'hex2': 12},
        {'hex1': 26, 'hex2': 11},  # Exists in LO but no data

        # Columns that exist in LOP
        {'hex1': 25, 'hex2': 10},
        {'hex1': 24, 'hex2': 9},   # Exists in LOP but no data

        # Additional columns that exist in some regions but not others
        {'hex1': 23, 'hex2': 8},   # Only exists in ME
        {'hex1': 22, 'hex2': 7},   # Only exists in LO
        {'hex1': 21, 'hex2': 6},   # Only exists in LOP
    ]


def create_region_columns_map():
    """Create mapping of which columns exist in each region."""
    return {
        'ME': {
            (31, 16),  # 1F, 10 - has data
            (30, 15),  # 1E, 0F - has data
            (29, 14),  # 1D, 0E - exists but no data
            (23, 8),   # 17, 08 - only in ME, no data
        },
        'LO': {
            (28, 13),  # 1C, 0D - has data
            (27, 12),  # 1B, 0C - has data
            (26, 11),  # 1A, 0B - exists but no data
            (22, 7),   # 16, 07 - only in LO, no data
        },
        'LOP': {
            (25, 10),  # 19, 0A - has data
            (24, 9),   # 18, 09 - exists but no data
            (21, 6),   # 15, 06 - only in LOP, no data
        }
    }


def main():
    """Main function to demonstrate comprehensive hexagon grid generation."""
    print("Comprehensive Hexagon Grid Generation Test")
    print("=" * 50)

    # Initialize the generator
    generator = EyemapGenerator()

    # Create test data
    sample_data = create_sample_data_with_gaps()
    all_possible_columns = create_all_possible_columns()
    region_columns_map = create_region_columns_map()

    # Create thresholds for testing
    thresholds_all = {
        'total_synapses': {'all': [0, 50, 100, 150, 200]},
        'neuron_count': {'all': [0, 25, 50, 75, 100]}
    }

    # Create output directory
    output_dir = Path("test_comprehensive_output")
    output_dir.mkdir(exist_ok=True)

    print(f"Generating comprehensive visualizations to: {output_dir.absolute()}")

    # Display data summary
    print(f"\nData Summary:")
    print(f"- Total possible columns: {len(all_possible_columns)}")
    print(f"- Columns with actual data: {len(sample_data)}")
    print(f"- ME_L region columns: {len(region_columns_map['ME_L'])}")
    print(f"- ME_R region columns: {len(region_columns_map['ME_R'])}")
    print(f"- LO_L region columns: {len(region_columns_map['LO_L'])}")
    print(f"- LO_R region columns: {len(region_columns_map['LO_R'])}")
    print(f"- LOP_L region columns: {len(region_columns_map['LOP_L'])}")
    print(f"- LOP_R region columns: {len(region_columns_map['LOP_R'])}")

    # Generate comprehensive region grids (SVG format)
    print("\n1. Generating comprehensive region-specific hexagonal grids (SVG)...")
    comprehensive_grids_svg = generator.generate_comprehensive_region_hexagonal_grids(
        sample_data,
        thresholds_all,
        all_possible_columns,
        region_columns_map,
        neuron_type="T4",
        soma_side="left",
        output_format="svg"
    )

    # Save comprehensive SVG grids
    for region, grids in comprehensive_grids_svg.items():
        for metric, svg_content in grids.items():
            if svg_content:
                filename = f"{region}_comprehensive_{metric}_grid.svg"
                filepath = output_dir / filename
                with open(filepath, 'w') as f:
                    f.write(svg_content)
                print(f"  Saved: {filename}")

    # Generate comprehensive region grids (PNG format)
    print("\n2. Generating comprehensive region-specific hexagonal grids (PNG)...")
    comprehensive_grids_png = generator.generate_comprehensive_region_hexagonal_grids(
        sample_data,
        thresholds_all,
        all_possible_columns,
        region_columns_map,
        neuron_type="T4",
        soma_side="left",
        output_format="png"
    )

    # Save comprehensive PNG grids
    for region, grids in comprehensive_grids_png.items():
        for metric, png_content in grids.items():
            if png_content and png_content.startswith('data:image/png;base64,'):
                # Extract base64 data and save as PNG
                base64_data = png_content.split(',')[1]
                import base64

                png_filename = f"{region}_comprehensive_{metric}_grid.png"
                png_filepath = output_dir / png_filename
                try:
                    with open(png_filepath, 'wb') as f:
                        f.write(base64.b64decode(base64_data))
                    print(f"  Saved: {png_filename}")
                except Exception as e:
                    print(f"  Error saving PNG file: {e}")
            elif png_content:
                # If it's SVG fallback, save as SVG
                svg_filename = f"{region}_comprehensive_{metric}_grid_fallback.svg"
                svg_filepath = output_dir / svg_filename
                with open(svg_filepath, 'w') as f:
                    f.write(png_content)
                print(f"  Saved: {svg_filename} (SVG fallback)")

    # Generate regular grids for comparison
    print("\n3. Generating regular region grids for comparison...")
    regular_grids = generator.generate_region_hexagonal_grids(
        sample_data,
        neuron_type="T4",
        soma_side="left",
        output_format="svg"
    )

    for region, grids in regular_grids.items():
        for metric, svg_content in grids.items():
            if svg_content:
                filename = f"{region}_regular_{metric}_grid.svg"
                filepath = output_dir / filename
                with open(filepath, 'w') as f:
                    f.write(svg_content)
                print(f"  Saved: {filename}")

    # Create a comparison HTML file
    html_content = create_comparison_html(comprehensive_grids_svg, regular_grids, all_possible_columns, region_columns_map)
    html_filepath = output_dir / "comparison.html"
    with open(html_filepath, 'w') as f:
        f.write(html_content)
    print(f"  Saved: comparison.html")

    print(f"\nTest completed! Check the '{output_dir}' directory for generated files.")
    print("\nGenerated files:")
    for file in sorted(output_dir.glob("*")):
        print(f"  - {file.name}")

    print(f"\nKey differences between comprehensive and regular grids:")
    print(f"- Comprehensive grids show ALL possible columns ({len(all_possible_columns)} total)")
    print(f"- Regular grids show only columns with data ({len(sample_data)} total)")
    print(f"- Dark gray hexagons: Column doesn't exist in this region")
    print(f"- White hexagons: Column exists in region but no data for current neuron type")
    print(f"- Colored hexagons: Column has data in this region")


def create_comparison_html(comprehensive_grids, regular_grids, all_possible_columns, region_columns_map):
    """Create an HTML file comparing comprehensive and regular grids."""
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Comprehensive vs Regular Hexagon Grids Comparison</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .comparison { display: flex; margin: 20px 0; }
        .grid-container { margin: 10px; border: 1px solid #ccc; padding: 10px; }
        .grid-container h3 { margin-top: 0; }
        .stats { background: #f5f5f5; padding: 10px; margin: 20px 0; }
        .legend { background: #fffacd; padding: 10px; margin: 20px 0; border-left: 4px solid #ffd700; }
    </style>
</head>
<body>
    <h1>Comprehensive vs Regular Hexagon Grids Comparison</h1>

    <div class="legend">
        <h3>Legend for Comprehensive Grids:</h3>
        <ul>
            <li><strong>Dark Gray:</strong> Column doesn't exist in this region</li>
            <li><strong>White (with border):</strong> Column exists in region but no data for current neuron type</li>
            <li><strong>Colored:</strong> Column has data in this region for current neuron type</li>
        </ul>
    </div>

    <div class="stats">
        <h3>Statistics:</h3>
        <ul>
"""

    html += f"            <li>Total possible columns across all regions: {len(all_possible_columns)}</li>\n"
    for region, coords in region_columns_map.items():
        html += f"            <li>{region} region columns: {len(coords)}</li>\n"

    html += """
        </ul>
    </div>
"""

    # Add grids for each region and metric
    for region in ['ME', 'LO', 'LOP']:
        for metric in ['synapse_density', 'cell_count']:
            html += f"""
    <h2>{region} - {metric.replace('_', ' ').title()}</h2>
    <div class="comparison">
        <div class="grid-container">
            <h3>Comprehensive Grid (All Possible Columns)</h3>
"""
            if region in comprehensive_grids and metric in comprehensive_grids[region]:
                html += comprehensive_grids[region][metric]
            else:
                html += "<p>No comprehensive grid available</p>"

            html += """
        </div>
        <div class="grid-container">
            <h3>Regular Grid (Data Only)</h3>
"""
            if region in regular_grids and metric in regular_grids[region]:
                html += regular_grids[region][metric]
            else:
                html += "<p>No regular grid available</p>"

            html += """
        </div>
    </div>
"""

    html += """
</body>
</html>
"""
    return html


if __name__ == "__main__":
    main()
