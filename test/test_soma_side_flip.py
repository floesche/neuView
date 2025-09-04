#!/usr/bin/env python3
"""
Test script to verify y-axis flipping for left soma side neurons in hexagonal grids.

This script generates hexagonal grids for left and right soma sides with the same
column data to verify that the x-coordinates are properly flipped for left soma side neurons.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from quickpage.visualization import EyemapGenerator


def create_test_data():
    """Create test data with specific columns that will clearly show the flip."""
    return [
        # Left column (should appear on the left for R soma side, right for L soma side)
        {
            'hex1': 25, 'hex2': 15, 'region': 'LO', 'side': 'right',
            'total_synapses': 1000, 'neuron_count': 40,
            'column_name': 'LO_R_25_15'
        },
        # Right column (should appear on the right for R soma side, left for L soma side)
        {
            'hex1': 30, 'hex2': 10, 'region': 'LO', 'side': 'right',
            'total_synapses': 800, 'neuron_count': 35,
            'column_name': 'LO_R_30_10'
        },
        # Center column for reference
        {
            'hex1': 28, 'hex2': 13, 'region': 'LO', 'side': 'right',
            'total_synapses': 1200, 'neuron_count': 45,
            'column_name': 'LO_R_28_13'
        },
        # Additional columns to show more variety
        {
            'hex1': 26, 'hex2': 12, 'region': 'LO', 'side': 'right',
            'total_synapses': 900, 'neuron_count': 38,
            'column_name': 'LO_R_26_12'
        },
        {
            'hex1': 29, 'hex2': 11, 'region': 'LO', 'side': 'right',
            'total_synapses': 1100, 'neuron_count': 42,
            'column_name': 'LO_R_29_11'
        }
    ]


def extract_coordinates_from_svg(svg_content):
    """Extract hexagon coordinates from SVG content for analysis."""
    import re

    # Pattern to match g elements with transform="translate(x,y)" containing hexagon paths
    transform_pattern = r'<g transform="translate\(([^,]+),([^)]+)\)"[^>]*>'

    coordinates = []
    matches = re.finditer(transform_pattern, svg_content)

    for match in matches:
        x = float(match.group(1))
        y = float(match.group(2))
        coordinates.append((x, y))

    return coordinates


def analyze_coordinate_flip(left_coords, right_coords):
    """Analyze whether coordinates are properly flipped between left and right soma sides."""
    print("\nCoordinate Analysis:")
    print("=" * 40)

    print(f"Right soma side coordinates: {len(right_coords)} hexagons")
    for i, (x, y) in enumerate(right_coords):
        print(f"  Hexagon {i+1}: x={x:6.1f}, y={y:6.1f}")

    print(f"\nLeft soma side coordinates: {len(left_coords)} hexagons")
    for i, (x, y) in enumerate(left_coords):
        print(f"  Hexagon {i+1}: x={x:6.1f}, y={y:6.1f}")

    # Check if x-coordinates are flipped (negative)
    if len(left_coords) == len(right_coords):
        print(f"\nFlip verification:")
        flip_correct = True
        for i, ((left_x, left_y), (right_x, right_y)) in enumerate(zip(left_coords, right_coords)):
            expected_left_x = -right_x
            x_diff = abs(left_x - expected_left_x)
            y_diff = abs(left_y - right_y)

            print(f"  Hexagon {i+1}:")
            print(f"    Right: x={right_x:6.1f}, y={right_y:6.1f}")
            print(f"    Left:  x={left_x:6.1f}, y={left_y:6.1f}")
            print(f"    Expected left x: {expected_left_x:6.1f}")
            print(f"    X difference: {x_diff:6.3f}, Y difference: {y_diff:6.3f}")

            if x_diff > 0.1:  # Allow small floating point differences
                flip_correct = False
                print(f"    ❌ X-coordinate flip INCORRECT")
            else:
                print(f"    ✅ X-coordinate flip correct")

            if y_diff > 0.1:  # Y should remain the same
                flip_correct = False
                print(f"    ❌ Y-coordinate changed unexpectedly")
            else:
                print(f"    ✅ Y-coordinate unchanged")

        return flip_correct
    else:
        print("❌ Different number of hexagons between left and right soma sides")
        return False


def main():
    """Main function to test soma side coordinate flipping."""
    print("Soma Side Coordinate Flip Test")
    print("=" * 40)

    # Initialize the generator with modern constructor
    from quickpage.visualization.config_manager import EyemapConfiguration
    config = EyemapConfiguration(save_to_files=False)
    generator = EyemapGenerator(config=config)

    # Create test data
    test_data = create_test_data()

    # Create output directory
    output_dir = Path("test_soma_flip_output")
    output_dir.mkdir(exist_ok=True)

    print(f"Generating test visualizations to: {output_dir.absolute()}")
    print(f"Test data: {len(test_data)} columns in LO region")

    # Generate grid for RIGHT soma side
    print("\n1. Generating grid for RIGHT soma side...")
    right_grids = generator.generate_region_hexagonal_grids(
        test_data,
        neuron_type="TestNeuron",
        soma_side="right",
        output_format="svg",
        save_to_files=False
    )

    # Generate grid for LEFT soma side
    print("2. Generating grid for LEFT soma side...")
    left_grids = generator.generate_region_hexagonal_grids(
        test_data,
        neuron_type="TestNeuron",
        soma_side="left",
        output_format="svg",
        save_to_files=False
    )

    # Save grids for visual inspection
    if 'LO' in right_grids and 'synapse_density' in right_grids['LO']:
        right_svg = right_grids['LO']['synapse_density']
        with open(output_dir / "right_soma_side.svg", 'w') as f:
            f.write(right_svg)
        print("  Saved: right_soma_side.svg")

    if 'LO' in left_grids and 'synapse_density' in left_grids['LO']:
        left_svg = left_grids['LO']['synapse_density']
        with open(output_dir / "left_soma_side.svg", 'w') as f:
            f.write(left_svg)
        print("  Saved: left_soma_side.svg")

    # Extract and analyze coordinates
    if ('LO' in right_grids and 'synapse_density' in right_grids['LO'] and
        'LO' in left_grids and 'synapse_density' in left_grids['LO']):

        right_coords = extract_coordinates_from_svg(right_grids['LO']['synapse_density'])
        left_coords = extract_coordinates_from_svg(left_grids['LO']['synapse_density'])

        flip_correct = analyze_coordinate_flip(left_coords, right_coords)

        print(f"\n" + "=" * 50)
        if flip_correct:
            print("✅ SUCCESS: Y-axis flipping is working correctly!")
            print("   Left soma side hexagons are properly mirrored horizontally.")
        else:
            print("❌ FAILURE: Y-axis flipping is not working correctly!")
            print("   Left soma side hexagons are NOT properly mirrored.")
        print("=" * 50)

    # Create comparison HTML
    html_content = create_comparison_html(right_grids, left_grids, test_data)
    with open(output_dir / "soma_side_comparison.html", 'w') as f:
        f.write(html_content)
    print(f"\n  Saved: soma_side_comparison.html")

    print(f"\nTest completed! Check the '{output_dir}' directory for:")
    print("  - SVG files showing the grids for visual comparison")
    print("  - HTML file for side-by-side comparison")
    print("  - Console output above for coordinate analysis")


def create_comparison_html(right_grids, left_grids, test_data):
    """Create an HTML file comparing right and left soma side grids."""
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Soma Side Coordinate Flip Comparison</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .comparison { display: flex; margin: 20px 0; }
        .grid-container { margin: 10px; border: 1px solid #ccc; padding: 10px; flex: 1; }
        .grid-container h3 { margin-top: 0; text-align: center; }
        .info { background: #f0f8ff; padding: 15px; margin: 20px 0; border-left: 4px solid #4169e1; }
        .test-data { background: #f5f5f5; padding: 10px; margin: 20px 0; }
        .expected { background: #e8f5e8; padding: 10px; margin: 10px 0; border-left: 4px solid #4caf50; }
    </style>
</head>
<body>
    <h1>Soma Side Coordinate Flip Comparison</h1>

    <div class="info">
        <h3>Test Purpose:</h3>
        <p>This test verifies that hexagonal grids are properly flipped along the y-axis for left soma side neurons.
           The same column data is used for left and right soma sides, so the hexagons should appear
           in mirrored positions.</p>
    </div>

    <div class="expected">
        <h3>Expected Result:</h3>
        <ul>
            <li><strong>Column 25,15 (19,0F)</strong>: hex1 < hex2, should appear on the LEFT for right soma side, RIGHT for left soma side</li>
            <li><strong>Column 30,10 (1E,0A)</strong>: hex1 > hex2, should appear on the RIGHT for right soma side, LEFT for left soma side</li>
            <li><strong>Column 28,13 (1C,0D)</strong>: hex1 > hex2, should appear on the RIGHT for right soma side, LEFT for left soma side</li>
            <li><strong>Column 26,12 (1A,0C)</strong>: hex1 > hex2, should appear on the RIGHT for right soma side, LEFT for left soma side</li>
            <li><strong>Column 29,11 (1D,0B)</strong>: hex1 > hex2, should appear on the RIGHT for right soma side, LEFT for left soma side</li>
        </ul>
    </div>

    <div class="test-data">
        <h3>Test Data:</h3>
        <table border="1" style="border-collapse: collapse; margin: 10px 0;">
            <tr><th>Column</th><th>Hex Coordinates</th><th>Decimal Coordinates</th><th>Synapses</th><th>Expected Position</th></tr>
"""

    for data in test_data:
        # Determine expected position based on hex coordinates
        hex1 = data['hex1']
        hex2 = data['hex2']
        diff = hex1 - hex2
        if diff < 0:
            position = "Left side"
        elif diff > 0:
            position = "Right side"
        else:
            position = "Center"

        html += f"""
            <tr>
                <td>{data['column_name']}</td>
                <td>{data['hex1']}, {data['hex2']}</td>
                <td>{data['hex1']}, {data['hex2']}</td>
                <td>{data['total_synapses']}</td>
                <td>{position} (R soma), opposite for L soma</td>
            </tr>
"""

    html += """
        </table>
    </div>

    <div class="comparison">
        <div class="grid-container">
            <h3>Right Soma Side</h3>
"""

    if 'LO' in right_grids and 'synapse_density' in right_grids['LO']:
        html += right_grids['LO']['synapse_density']
    else:
        html += "<p>No right soma side grid available</p>"

    html += """
        </div>
        <div class="grid-container">
            <h3>Left Soma Side</h3>
"""

    if 'LO' in left_grids and 'synapse_density' in left_grids['LO']:
        html += left_grids['LO']['synapse_density']
    else:
        html += "<p>No left soma side grid available</p>"

    html += """
        </div>
    </div>

    <div class="info">
        <h3>How to Verify:</h3>
        <ol>
            <li>Look at the grids side by side</li>
            <li>Compare the positions of the hexagons</li>
            <li>The leftmost hexagon in the right soma side grid should be the rightmost in the left soma side grid</li>
            <li>The rightmost hexagon in the right soma side grid should be the leftmost in the left soma side grid</li>
            <li>The center hexagon should remain in the center for both</li>
        </ol>
    </div>

</body>
</html>
"""
    return html


if __name__ == "__main__":
    main()
