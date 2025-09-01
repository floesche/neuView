#!/usr/bin/env python3
"""
Complete example demonstrating SVG file saving and HTML integration.

This script shows how the EyemapGenerator saves SVG files to static/images/
and how they are loaded in the HTML template.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from quickpage.visualization import EyemapGenerator
from quickpage.page_generator import PageGenerator
from quickpage.config import Config


def create_sample_column_data():
    """Create comprehensive sample column data for demonstration."""
    return [
        # ME region - left side
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
        {
            'hex1': 29, 'hex2': 14, 'region': 'ME', 'side': 'left',
            'total_synapses': 1450, 'neuron_count': 52,
            'column_name': 'ME_L_29_14'
        },

        # LO region - right side
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
        {
            'hex1': 26, 'hex2': 11, 'region': 'LO', 'side': 'right',
            'total_synapses': 750, 'neuron_count': 28,
            'column_name': 'LO_R_26_11'
        },

        # LOP region - mixed sides
        {
            'hex1': 25, 'hex2': 10, 'region': 'LOP', 'side': 'left',
            'total_synapses': 1300, 'neuron_count': 48,
            'column_name': 'LOP_L_25_10'
        },
        {
            'hex1': 24, 'hex2': 9, 'region': 'LOP', 'side': 'right',
            'total_synapses': 650, 'neuron_count': 25,
            'column_name': 'LOP_R_24_9'
        },
        {
            'hex1': 23, 'hex2': 8, 'region': 'LOP', 'side': 'left',
            'total_synapses': 920, 'neuron_count': 35,
            'column_name': 'LOP_L_23_8'
        }
    ]


def demonstrate_svg_file_generation():
    """Demonstrate SVG file generation and saving."""
    print("SVG File Generation and HTML Integration Demo")
    print("=" * 50)

    # Create output directory
    output_dir = Path("demo_output")
    output_dir.mkdir(exist_ok=True)

    print(f"Output directory: {output_dir.absolute()}")

    # Initialize generator with output directory
    generator = EyemapGenerator(output_dir=output_dir)

    # Create sample data
    sample_data = create_sample_column_data()
    print(f"Created sample data with {len(sample_data)} columns")

    # Count regions
    regions = set(col['region'] for col in sample_data)
    print(f"Regions: {', '.join(sorted(regions))}")

    print("\n1. Generating SVG files...")

    # Generate region grids with file saving
    region_grids = generator.generate_region_hexagonal_grids(
        sample_data,
        neuron_type="T4",
        soma_side="left",
        output_format="svg",
        save_to_files=True
    )

    print("\nGenerated SVG files:")
    for region, grids in region_grids.items():
        for metric, file_path in grids.items():
            print(f"  {region} - {metric}: {file_path}")
            # Verify file exists
            full_path = output_dir / file_path
            if full_path.exists():
                print(f"    ✅ File exists ({full_path.stat().st_size} bytes)")
            else:
                print(f"    ❌ File missing")

    print("\n2. Demonstrating HTML template integration...")

    # Create a simplified HTML template content to show integration
    html_template = """<!DOCTYPE html>
<html>
<head>
    <title>Hexagon Grid Demo</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .grid-section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; }
        .region-grid { display: inline-block; margin: 10px; text-align: center; }
        .grid-container {
            border: 1px solid #ccc;
            padding: 10px;
            background: #f9f9f9;
            display: inline-block;
        }
        h1, h2, h3 { color: #333; }
    </style>
</head>
<body>
    <h1>T4 Neuron Column Analysis (Left Hemisphere)</h1>

    <div class="grid-section">
        <h2>Region Hexagon Grids</h2>
        <p>Each hexagon represents a column with color intensity indicating the metric value.</p>

"""

    # Add each region's grids to the HTML
    for region, grids in region_grids.items():
        html_template += f"""        <div class="region-grid">
            <h3>{region} Region</h3>

            <div>
                <h4>Synapse Density</h4>
                <div class="grid-container">
                    <object data="{grids['synapse_density']}" type="image/svg+xml">
                        <img src="{grids['synapse_density']}" alt="{region} Synapse Density Grid" />
                    </object>
                </div>
            </div>

            <div>
                <h4>Cell Count</h4>
                <div class="grid-container">
                    <object data="{grids['cell_count']}" type="image/svg+xml">
                        <img src="{grids['cell_count']}" alt="{region} Cell Count Grid" />
                    </object>
                </div>
            </div>
        </div>

"""

    html_template += """    </div>

    <div class="grid-section">
        <h2>Column Data</h2>
        <table border="1" cellpadding="5" cellspacing="0">
            <thead>
                <tr>
                    <th>Region</th>
                    <th>Side</th>
                    <th>Hex1</th>
                    <th>Hex2</th>
                    <th>Neurons</th>
                    <th>Synapses</th>
                    <th>Column Name</th>
                </tr>
            </thead>
            <tbody>
"""

    # Add column data to the table
    for col in sample_data:
        html_template += f"""                <tr>
                    <td>{col['region']}</td>
                    <td>{col['side'].title()}</td>
                    <td>{col['hex1']}</td>
                    <td>{col['hex2']}</td>
                    <td>{col['neuron_count']}</td>
                    <td>{col['total_synapses']}</td>
                    <td>{col['column_name']}</td>
                </tr>
"""

    html_template += """            </tbody>
        </table>
    </div>
</body>
</html>"""

    # Save the HTML file
    html_path = output_dir / "hexagon_grid_demo.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_template)

    print(f"✅ Demo HTML file created: {html_path}")

    print("\n3. File structure created:")
    for file in sorted(output_dir.rglob("*")):
        if file.is_file():
            relative_path = file.relative_to(output_dir)
            size = file.stat().st_size
            print(f"  {relative_path} ({size} bytes)")

    print(f"\n4. How to view the results:")
    print(f"   Open: {html_path.absolute()}")
    print(f"   All SVG files are in: {(output_dir / 'static' / 'images').absolute()}")

    print("\n5. Integration details:")
    print("   - SVG files are saved to static/images/ directory")
    print("   - HTML uses <object> tags with <img> fallback for SVG display")
    print("   - File paths are relative to the HTML file location")
    print("   - Each region gets separate grids for synapse density and cell count")
    print("   - Color scaling is consistent across all regions")

    return region_grids, html_path


def demonstrate_pageGenerator_integration():
    """Show how this integrates with the full PageGenerator system."""
    print("\n" + "=" * 50)
    print("PageGenerator Integration")
    print("=" * 50)

    print("\nThe new functionality is integrated into PageGenerator as follows:")
    print("\n1. EyemapGenerator is initialized with output directory:")
    print("   self.eyemap_generator = EyemapGenerator(output_dir=self.output_dir)")

    print("\n2. Region grids are generated with file saving enabled:")
    print("   region_grids = self.eyemap_generator.generate_region_hexagonal_grids(")
    print("       column_summary, neuron_type, soma_side, save_to_files=True)")

    print("\n3. Template receives file paths instead of SVG content:")
    print("   context['column_analysis']['region_grids'] = {")
    print("       'ME': {")
    print("           'synapse_density': 'static/images/ME_T4_left_synapse_density.svg',")
    print("           'cell_count': 'static/images/ME_T4_left_cell_count.svg'")
    print("       }")
    print("   }")

    print("\n4. HTML template displays the SVG files:")
    print("   <object data=\"{{ grids.synapse_density }}\" type=\"image/svg+xml\">")
    print("       <img src=\"{{ grids.synapse_density }}\" alt=\"Synapse Grid\" />")
    print("   </object>")

    print("\n5. Benefits of this approach:")
    print("   ✅ Smaller HTML files (no inline SVG)")
    print("   ✅ Cacheable SVG assets")
    print("   ✅ Better browser performance")
    print("   ✅ SVG files can be used independently")
    print("   ✅ Easier debugging and inspection")


def main():
    """Main demonstration function."""
    try:
        region_grids, html_path = demonstrate_svg_file_generation()
        demonstrate_pageGenerator_integration()

        print("\n" + "=" * 50)
        print("Demo completed successfully!")
        print("=" * 50)

        print(f"\n📁 Generated {len([f for region in region_grids.values() for f in region.values()])} SVG files")
        print(f"🌐 Created demo HTML: {html_path.name}")
        print(f"📂 All files in: demo_output/")

        print("\n💡 Next steps:")
        print("   1. Open the HTML file in your browser to see the results")
        print("   2. Examine the SVG files in static/images/")
        print("   3. Use the PageGenerator with real neuron data")

    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
