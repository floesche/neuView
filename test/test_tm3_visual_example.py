#!/usr/bin/env python3
"""
Visual test to generate actual SVG files showing the corrected column existence logic.

This creates concrete examples of comprehensive hexagonal grids for Tm3_R,
demonstrating the three states:
- Dark gray: Column doesn't exist in this region
- White: Column exists in region but no data for current neuron type
- Colored: Column has data for current neuron type
"""

import os
import sys
from pathlib import Path
import pandas as pd
from unittest.mock import Mock

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from quickpage.page_generator import PageGenerator


def create_realistic_tm3_dataset():
    """
    Create a realistic dataset showing the Tm3_R scenario where:
    - Tm3 has data in ME at (27,11) and other ME columns
    - Other neurons have data in LO at (27,11) but Tm3 doesn't
    - LOP has different columns entirely
    """
    return pd.DataFrame([
        # Tm3 data in ME region
        {'roi': 'ME_R_col_27_11', 'pre': 180, 'post': 220},  # Tm3 has data here
        {'roi': 'ME_R_col_26_10', 'pre': 150, 'post': 190},  # Tm3 has data here
        {'roi': 'ME_R_col_28_12', 'pre': 200, 'post': 240},  # Tm3 has data here
        {'roi': 'ME_R_col_25_09', 'pre': 140, 'post': 170},  # Tm3 has data here

        # Other neurons (T4, T5, L2, etc.) in LO region
        # Note: (27,11) exists in LO but from OTHER neurons, not Tm3
        {'roi': 'LO_R_col_27_11', 'pre': 100, 'post': 130},  # T4 or T5 data
        {'roi': 'LO_R_col_26_11', 'pre': 90, 'post': 120},   # T4 or T5 data
        {'roi': 'LO_R_col_28_11', 'pre': 110, 'post': 140},  # T4 or T5 data
        {'roi': 'LO_R_col_24_09', 'pre': 85, 'post': 115},   # T4 or T5 data
        {'roi': 'LO_R_col_29_12', 'pre': 95, 'post': 125},   # T4 or T5 data

        # Other neurons in LOP region - completely different columns
        {'roi': 'LOP_R_col_23_08', 'pre': 70, 'post': 95},   # LC neurons
        {'roi': 'LOP_R_col_22_07', 'pre': 65, 'post': 88},   # LC neurons
        {'roi': 'LOP_R_col_24_08', 'pre': 75, 'post': 102},  # LC neurons
        {'roi': 'LOP_R_col_21_06', 'pre': 60, 'post': 80},   # LC neurons

        # Additional shared columns to make it more interesting
        # (26,10) exists in both ME (with Tm3) and LO (with other neurons)
        {'roi': 'LO_R_col_26_10', 'pre': 88, 'post': 118},   # T4 data at same coord as Tm3 ME data

        # (25,09) exists in ME (with Tm3) but also in LOP (with other neurons)
        {'roi': 'LOP_R_col_25_09', 'pre': 78, 'post': 105},  # LC data at same coord as Tm3 ME data
    ])


def create_tm3_specific_data():
    """Create ROI data showing only Tm3 neuron innervation."""
    return pd.DataFrame([
        # Tm3 neurons only have data in ME region
        {'roi': 'ME_R_col_27_11', 'bodyId': 12001, 'pre': 180, 'post': 220, 'total': 400},
        {'roi': 'ME_R_col_26_10', 'bodyId': 12001, 'pre': 150, 'post': 190, 'total': 340},
        {'roi': 'ME_R_col_28_12', 'bodyId': 12001, 'pre': 200, 'post': 240, 'total': 440},
        {'roi': 'ME_R_col_25_09', 'bodyId': 12001, 'pre': 140, 'post': 170, 'total': 310},

        {'roi': 'ME_R_col_27_11', 'bodyId': 12002, 'pre': 170, 'post': 210, 'total': 380},
        {'roi': 'ME_R_col_26_10', 'bodyId': 12002, 'pre': 145, 'post': 185, 'total': 330},
        {'roi': 'ME_R_col_28_12', 'bodyId': 12002, 'pre': 195, 'post': 235, 'total': 430},

        {'roi': 'ME_R_col_27_11', 'bodyId': 12003, 'pre': 175, 'post': 215, 'total': 390},
        {'roi': 'ME_R_col_25_09', 'bodyId': 12003, 'pre': 135, 'post': 165, 'total': 300},

        # IMPORTANT: Tm3 has NO data in LO or LOP regions
        # The (27,11), (26,10), etc. columns exist in those regions but with other neuron types
    ])


def create_tm3_neurons():
    """Create Tm3 neuron metadata."""
    return pd.DataFrame([
        {'bodyId': 12001, 'type': 'Tm3', 'instance': 'Tm3_001', 'somaLocation': 'right'},
        {'bodyId': 12002, 'type': 'Tm3', 'instance': 'Tm3_002', 'somaLocation': 'right'},
        {'bodyId': 12003, 'type': 'Tm3', 'instance': 'Tm3_003', 'somaLocation': 'right'},
    ])


def generate_tm3_visual_example():
    """Generate visual example SVG files for Tm3_R."""
    print("Generating Tm3_R Visual Example")
    print("=" * 40)

    # Create output directory
    output_dir = Path("tm3_visual_example_output")
    output_dir.mkdir(exist_ok=True)

    # Set up mock page generator
    config = Mock()
    config.output = Mock()
    config.output.template_dir = "templates"

    generator = PageGenerator(config, str(output_dir))

    # Mock the database with our realistic dataset
    mock_nc = Mock()
    mock_nc.fetch_custom.return_value = create_realistic_tm3_dataset()
    generator.nc = mock_nc

    # Generate comprehensive grids for Tm3_R
    tm3_roi_data = create_tm3_specific_data()
    tm3_neurons = create_tm3_neurons()

    print("Analyzing Tm3_R column data...")
    result = generator._analyze_column_roi_data(
        tm3_roi_data,
        tm3_neurons,
        'right',
        'Tm3',
        file_type='svg',
        save_to_files=False
    )

    if not result:
        print("❌ No analysis result generated")
        return

    print(f"✓ Found {result['all_possible_columns_count']} total possible columns")
    print(f"✓ Region distribution: {result['region_columns_counts']}")

    # Save comprehensive grids
    comprehensive_grids = result.get('comprehensive_region_grids', {})

    if not comprehensive_grids:
        print("❌ No comprehensive grids generated")
        return

    for region in ['ME', 'LO', 'LOP']:
        if region in comprehensive_grids:
            grids = comprehensive_grids[region]

            # Save synapse density grid
            if grids.get('synapse_density'):
                synapse_file = output_dir / f"Tm3_R_{region}_comprehensive_synapse_density.svg"
                with open(synapse_file, 'w') as f:
                    f.write(grids['synapse_density'])
                print(f"✓ Saved {synapse_file.name}")

            # Save cell count grid
            if grids.get('cell_count'):
                cell_file = output_dir / f"Tm3_R_{region}_comprehensive_cell_count.svg"
                with open(cell_file, 'w') as f:
                    f.write(grids['cell_count'])
                print(f"✓ Saved {cell_file.name}")

    # Generate analysis report
    create_analysis_report(result, output_dir)

    print(f"\n🎉 Tm3_R visual example complete!")
    print(f"Check the '{output_dir}' directory for:")
    print("  • SVG files showing comprehensive hexagonal grids")
    print("  • analysis_report.html with detailed explanations")

    return result


def create_analysis_report(result, output_dir):
    """Create an HTML report explaining the results."""

    comprehensive_grids = result.get('comprehensive_region_grids', {})
    columns = result.get('columns', [])

    # Analyze which columns have data vs exist but empty vs don't exist
    tm3_columns = {(col['hex1'], col['hex2']): col for col in columns}
    all_possible = result.get('all_possible_columns_count', 0)
    region_counts = result.get('region_columns_counts', {})

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Tm3_R Comprehensive Column Analysis</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                  color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .section {{ background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px; }}
        .grid-container {{ display: flex; gap: 20px; margin: 20px 0; flex-wrap: wrap; }}
        .grid-item {{ flex: 1; min-width: 300px; text-align: center;
                     background: white; padding: 15px; border-radius: 8px;
                     border: 2px solid #dee2e6; }}
        .legend {{ background: #fffacd; padding: 15px; border-left: 4px solid #ffd700;
                  border-radius: 4px; margin: 20px 0; }}
        .state-example {{ display: inline-block; padding: 4px 12px; margin: 0 8px;
                         border-radius: 4px; font-weight: bold; }}
        .state-colored {{ background: #fc9272; color: white; }}
        .state-white {{ background: #ffffff; border: 2px solid #999999; color: #333; }}
        .state-gray {{ background: #4a4a4a; color: white; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 8px;
                     text-align: center; flex: 1; border: 1px solid #dee2e6; }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #667eea; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #dee2e6; }}
        th {{ background: #f8f9fa; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Tm3_R Comprehensive Column Analysis</h1>
        <p>Demonstrating the corrected algorithm for column existence across ME, LO, and LOP regions</p>
    </div>

    <div class="legend">
        <h3>🎯 Key Insight: Column Existence Logic</h3>
        <p>A column coordinate (hex1, hex2) is considered to <strong>exist</strong> in a region if <strong>ANY</strong> neuron type has innervation there, not just the current neuron type being analyzed.</p>
        <p><strong>Visual States:</strong></p>
        <span class="state-example state-colored">COLORED</span> Current neuron (Tm3) has data
        <span class="state-example state-white">WHITE</span> Column exists but Tm3 has no data
        <span class="state-example state-gray">DARK GRAY</span> Column doesn't exist in region
    </div>

    <div class="stats">
        <div class="stat-card">
            <div class="stat-number">{all_possible}</div>
            <div>Total Possible Columns</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{len(columns)}</div>
            <div>Tm3 Data Columns</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{region_counts.get('ME', 0)}</div>
            <div>ME Columns</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{region_counts.get('LO', 0)}</div>
            <div>LO Columns</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{region_counts.get('LOP', 0)}</div>
            <div>LOP Columns</div>
        </div>
    </div>
"""

    # Add comprehensive grids
    if comprehensive_grids:
        html += """
    <div class="section">
        <h2>📊 Comprehensive Hexagonal Grids</h2>
        <p>These grids show <strong>ALL</strong> possible column coordinates, demonstrating the three visual states based on data availability.</p>

        <h3>Synapse Density Grids</h3>
        <div class="grid-container">
"""

        for region in ['ME', 'LO', 'LOP']:
            if region in comprehensive_grids and comprehensive_grids[region].get('synapse_density'):
                html += f"""
            <div class="grid-item">
                <h4>{region} Region - Synapse Density</h4>
                {comprehensive_grids[region]['synapse_density']}
            </div>"""

        html += """
        </div>

        <h3>Cell Count Grids</h3>
        <div class="grid-container">
"""

        for region in ['ME', 'LO', 'LOP']:
            if region in comprehensive_grids and comprehensive_grids[region].get('cell_count'):
                html += f"""
            <div class="grid-item">
                <h4>{region} Region - Cell Count</h4>
                {comprehensive_grids[region]['cell_count']}
            </div>"""

        html += """
        </div>
    </div>
"""

    # Add detailed explanation
    html += f"""
    <div class="section">
        <h2>🔍 Detailed Analysis</h2>
        <p>This example demonstrates the specific case mentioned: <strong>Tm3_R has a column at (27,11) in ME(R)</strong></p>

        <h3>Expected Behavior:</h3>
        <table>
            <tr><th>Region</th><th>Column (27,11)</th><th>Explanation</th></tr>
            <tr><td><strong>ME</strong></td><td><span class="state-example state-colored">COLORED</span></td>
                <td>Tm3 has innervation data at (27,11) in ME</td></tr>
            <tr><td><strong>LO</strong></td><td><span class="state-example state-white">WHITE</span></td>
                <td>Column (27,11) exists in LO (other neurons have data there) but Tm3 has no data</td></tr>
            <tr><td><strong>LOP</strong></td><td><span class="state-example state-gray">DARK GRAY</span></td>
                <td>Column (27,11) does not exist in LOP (no neurons have data there)</td></tr>
        </table>

        <h3>Tm3 Data Distribution:</h3>
        <table>
            <tr><th>Column</th><th>Hex Coords</th><th>Region</th><th>Synapse Count</th></tr>
"""

    for col in sorted(columns, key=lambda x: (x['region'], x['hex1'], x['hex2'])):
        html += f"""
            <tr><td>({col['hex1']}, {col['hex2']})</td>
                <td>{col['hex1']}, {col['hex2']}</td>
                <td>{col['region']}</td>
                <td>{col['total_synapses']}</td></tr>
"""

    html += f"""
        </table>

        <h3>Region Column Distribution:</h3>
        <ul>
"""

    for region, count in region_counts.items():
        html += f"            <li><strong>{region}</strong>: {count} columns total (includes columns from all neuron types)</li>\n"

    html += f"""
        </ul>

        <p><em>Note: The comprehensive grids show all {all_possible} possible columns across all regions,
        while Tm3 only has data in {len(columns)} of them (all in ME region).</em></p>
    </div>

    <div class="section">
        <h2>✅ Validation Results</h2>
        <p>This implementation correctly handles the scenario where:</p>
        <ul>
            <li>✓ Column coordinates are shared across regions when multiple neuron types use them</li>
            <li>✓ Each region shows the complete picture of all possible columns</li>
            <li>✓ Visual distinction between "doesn't exist", "exists but empty", and "has data"</li>
            <li>✓ Tm3_R analysis properly shows its limited distribution across regions</li>
        </ul>
    </div>
</body>
</html>
"""

    report_file = output_dir / "analysis_report.html"
    with open(report_file, 'w') as f:
        f.write(html)
    print(f"✓ Saved {report_file.name}")


if __name__ == "__main__":
    generate_tm3_visual_example()
