#!/usr/bin/env python3
"""
Example usage script for HexagonGridGenerator.

This script demonstrates how to use the HexagonGridGenerator class
to create SVG and PNG hexagonal grid visualizations.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from quickpage.visualization import HexagonGridGenerator


def create_sample_data():
    """Create sample column data for demonstration."""
    return [
        {
            'hex1_dec': 31, 'hex2_dec': 16, 'region': 'ME', 'side': 'left',
            'hex1': '1F', 'hex2': '10', 'total_synapses': 1200, 'neuron_count': 45,
            'column_name': 'ME_L_1F_10'
        },
        {
            'hex1_dec': 30, 'hex2_dec': 15, 'region': 'ME', 'side': 'left',
            'hex1': '1E', 'hex2': '0F', 'total_synapses': 980, 'neuron_count': 38,
            'column_name': 'ME_L_1E_0F'
        },
        {
            'hex1_dec': 29, 'hex2_dec': 14, 'region': 'ME', 'side': 'left',
            'hex1': '1D', 'hex2': '0E', 'total_synapses': 1450, 'neuron_count': 52,
            'column_name': 'ME_L_1D_0E'
        },
        {
            'hex1_dec': 28, 'hex2_dec': 13, 'region': 'LO', 'side': 'right',
            'hex1': '1C', 'hex2': '0D', 'total_synapses': 800, 'neuron_count': 30,
            'column_name': 'LO_R_1C_0D'
        },
        {
            'hex1_dec': 27, 'hex2_dec': 12, 'region': 'LO', 'side': 'right',
            'hex1': '1B', 'hex2': '0C', 'total_synapses': 1100, 'neuron_count': 42,
            'column_name': 'LO_R_1B_0C'
        },
        {
            'hex1_dec': 26, 'hex2_dec': 11, 'region': 'LOP', 'side': 'left',
            'hex1': '1A', 'hex2': '0B', 'total_synapses': 650, 'neuron_count': 25,
            'column_name': 'LOP_L_1A_0B'
        },
        {
            'hex1_dec': 25, 'hex2_dec': 10, 'region': 'LOP', 'side': 'left',
            'hex1': '19', 'hex2': '0A', 'total_synapses': 1300, 'neuron_count': 48,
            'column_name': 'LOP_L_19_0A'
        }
    ]


def main():
    """Main function to demonstrate hexagon grid generation."""
    print("HexagonGridGenerator Example Usage")
    print("=" * 40)

    # Initialize the generator
    generator = HexagonGridGenerator()

    # Create sample data
    sample_data = create_sample_data()

    # Create output directory
    output_dir = Path("example_output")
    output_dir.mkdir(exist_ok=True)

    print(f"Generating visualizations to: {output_dir.absolute()}")

    # Example 1: Generate region-specific grids (SVG format)
    print("\n1. Generating region-specific hexagonal grids (SVG)...")
    region_grids_svg = generator.generate_region_hexagonal_grids(
        sample_data,
        neuron_type="T4",
        soma_side="left",
        output_format="svg"
    )

    # Save SVG region grids
    for region, grids in region_grids_svg.items():
        for metric, svg_content in grids.items():
            if svg_content:
                filename = f"{region}_{metric}_grid.svg"
                filepath = output_dir / filename
                with open(filepath, 'w') as f:
                    f.write(svg_content)
                print(f"  Saved: {filename}")

    # Example 2: Generate region-specific grids (PNG format)
    print("\n2. Generating region-specific hexagonal grids (PNG)...")
    region_grids_png = generator.generate_region_hexagonal_grids(
        sample_data,
        neuron_type="T4",
        soma_side="left",
        output_format="png"
    )

    # Save PNG region grids as base64 data
    for region, grids in region_grids_png.items():
        for metric, png_base64 in grids.items():
            if png_base64:
                filename = f"{region}_{metric}_grid_base64.txt"
                filepath = output_dir / filename
                with open(filepath, 'w') as f:
                    f.write(png_base64)
                print(f"  Saved: {filename} (base64 encoded)")

                # Also save as actual PNG file
                import base64
                png_filename = f"{region}_{metric}_grid.png"
                png_filepath = output_dir / png_filename
                try:
                    with open(png_filepath, 'wb') as f:
                        f.write(base64.b64decode(png_base64))
                    print(f"  Saved: {png_filename}")
                except Exception as e:
                    print(f"  Error saving PNG file: {e}")

    # Example 3: Generate a combined hexagonal visualization
    print("\n3. Generating combined hexagonal visualization...")

    # Prepare hexagon data for combined view
    hexagons = []
    generator_instance = HexagonGridGenerator()

    # Calculate ranges for color scaling
    min_synapses = min(col['total_synapses'] for col in sample_data)
    max_synapses = max(col['total_synapses'] for col in sample_data)
    value_range = max_synapses - min_synapses

    for col in sample_data:
        # Use the same coordinate transformation as in the generator
        hex1_coord = col['hex1_dec'] - min(c['hex1_dec'] for c in sample_data)
        hex2_coord = col['hex2_dec'] - min(c['hex2_dec'] for c in sample_data)

        q = -(hex1_coord - hex2_coord) - 3
        r = -hex2_coord

        x = generator_instance.hex_size * generator_instance.spacing_factor * (3/2 * q)
        y = generator_instance.hex_size * generator_instance.spacing_factor * (
            (3**0.5/2 * q + 3**0.5 * r)
        )

        normalized_value = (col['total_synapses'] - min_synapses) / value_range if value_range > 0 else 0
        color = generator_instance._value_to_color(normalized_value)

        hexagons.append({
            'x': x,
            'y': y,
            'value': col['total_synapses'],
            'color': color,
            'region': col['region'],
            'side': col['side'],
            'hex1': col['hex1'],
            'hex2': col['hex2'],
            'neuron_count': col['neuron_count'],
            'column_name': col['column_name']
        })

    # Generate combined SVG using generate_single_region_grid
    combined_svg = generator.generate_single_region_grid(
        sample_data, 'synapse_density', 'Combined',
        min_synapses, max_synapses,
        neuron_type="T4", soma_side="right", output_format="svg"
    )

    if combined_svg:
        combined_svg_path = output_dir / "combined_hexagon_grid.svg"
        with open(combined_svg_path, 'w') as f:
            f.write(combined_svg)
        print(f"  Saved: combined_hexagon_grid.svg")

    # Generate combined PNG using generate_single_region_grid
    combined_png = generator.generate_single_region_grid(
        sample_data, 'synapse_density', 'Combined',
        min_synapses, max_synapses,
        neuron_type="T4", soma_side="right", output_format="png"
    )

    if combined_png:
        combined_png_path = output_dir / "combined_hexagon_grid.png"
        try:
            import base64
            if combined_png.startswith('data:image/png;base64,'):
                png_data = combined_png.split(',', 1)[1]
                with open(combined_png_path, 'wb') as f:
                    f.write(base64.b64decode(png_data))
                print(f"  Saved: combined_hexagon_grid.png")
            else:
                print(f"  Unexpected PNG format: {combined_png[:50]}...")
        except Exception as e:
            print(f"  Error saving combined PNG: {e}")

    print(f"\nExample completed! Check the '{output_dir}' directory for generated files.")
    print("\nGenerated files:")
    for file in sorted(output_dir.glob("*")):
        print(f"  - {file.name}")


if __name__ == "__main__":
    main()
