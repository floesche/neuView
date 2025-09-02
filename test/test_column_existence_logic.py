#!/usr/bin/env python3
"""
Test for the corrected column existence logic.

This test verifies that the algorithm correctly determines which columns exist
in each region based on actual neuron innervation across all neuron types.

Example scenario: Tm3_R has a column at (27,11) in ME(R). This means:
- LO and LOP should also show (27,11) if ANY neuron has innervation there
- If LO has no innervation at (27,11), it should be dark gray
- If LO has innervation from other neurons but not Tm3, it should be white
- If LO has innervation from Tm3, it should be color-coded
"""

import os
import sys
from pathlib import Path
import pandas as pd
from unittest.mock import Mock

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from quickpage.page_generator import PageGenerator
from quickpage.visualization import EyemapGenerator


def create_mock_dataset_with_shared_columns():
    """
    Create mock dataset that simulates the scenario where:
    - Column (27,11) exists in ME with Tm3 innervation
    - Column (27,11) exists in LO with other neuron innervation (not Tm3)
    - Column (27,11) does not exist in LOP at all
    - Column (28,12) exists only in ME
    """
    return pd.DataFrame([
        # Tm3 neurons in ME at column (27,11)
        {'roi': 'ME_R_col_27_11', 'pre': 150, 'post': 200},
        {'roi': 'ME_R_col_27_11', 'pre': 120, 'post': 180},

        # Tm3 neurons in ME at column (28,12) - unique to ME
        {'roi': 'ME_R_col_28_12', 'pre': 100, 'post': 150},

        # Other neurons (T4, T5, etc.) in LO at column (27,11)
        # This means (27,11) exists in LO but Tm3 has no data there
        {'roi': 'LO_R_col_27_11', 'pre': 80, 'post': 120},
        {'roi': 'LO_R_col_27_11', 'pre': 95, 'post': 140},

        # LO has some other columns
        {'roi': 'LO_R_col_26_10', 'pre': 70, 'post': 90},

        # LOP has different columns entirely (no 27,11)
        {'roi': 'LOP_R_col_25_09', 'pre': 60, 'post': 85},
        {'roi': 'LOP_R_col_24_08', 'pre': 55, 'post': 75},
    ])


def create_tm3_roi_data():
    """Create ROI data specifically for Tm3 neurons (subset of all data)."""
    return pd.DataFrame([
        # Tm3 only has data in ME at (27,11) and (28,12)
        {'roi': 'ME_R_col_27_11', 'bodyId': 1001, 'pre': 150, 'post': 200, 'total': 350},
        {'roi': 'ME_R_col_27_11', 'bodyId': 1002, 'pre': 120, 'post': 180, 'total': 300},
        {'roi': 'ME_R_col_28_12', 'bodyId': 1001, 'pre': 100, 'post': 150, 'total': 250},
        # Note: Tm3 has NO data in LO_R_col_27_11 or any LOP columns
    ])


def create_tm3_neurons_data():
    """Create neurons data for Tm3."""
    return pd.DataFrame([
        {'bodyId': 1001, 'type': 'Tm3', 'instance': 'Tm3_001'},
        {'bodyId': 1002, 'type': 'Tm3', 'instance': 'Tm3_002'},
    ])


def test_column_existence_logic():
    """Test that column existence is correctly determined across regions."""
    print("Testing column existence logic...")

    # Create mock page generator
    config = Mock()
    config.output = Mock()
    config.output.template_dir = "templates"

    generator = PageGenerator.create_with_factory(config, "test_output")

    # Mock the dataset query to return our test data
    mock_nc = Mock()
    mock_nc.client = Mock()
    mock_nc.client.fetch_custom.return_value = create_mock_dataset_with_shared_columns()
    generator.nc = mock_nc

    # Get all possible columns
    all_possible_columns, region_columns_map = generator._get_all_possible_columns_from_dataset(mock_nc)

    print(f"All possible columns found: {len(all_possible_columns)}")
    for col in all_possible_columns:
        print(f"  ({col['hex1']}, {col['hex2']})")

    print(f"\nRegion column mapping:")
    for region, coords in region_columns_map.items():
        coord_list = sorted(list(coords))
        print(f"  {region}: {coord_list}")

    # Verify expected results
    expected_columns = {(27, 11), (28, 12), (26, 10), (25, 9), (24, 8)}
    found_columns = {(col['hex1'], col['hex2']) for col in all_possible_columns}
    assert found_columns == expected_columns, f"Expected {expected_columns}, got {found_columns}"

    # Verify region mappings
    assert (27, 11) in region_columns_map['ME'], "Column (27,11) should exist in ME"
    assert (27, 11) in region_columns_map['LO'], "Column (27,11) should exist in LO (other neurons)"
    assert (27, 11) not in region_columns_map['LOP'], "Column (27,11) should NOT exist in LOP"

    assert (28, 12) in region_columns_map['ME'], "Column (28,12) should exist in ME"
    assert (28, 12) not in region_columns_map['LO'], "Column (28,12) should NOT exist in LO"
    assert (28, 12) not in region_columns_map['LOP'], "Column (28,12) should NOT exist in LOP"

    print("✓ Column existence logic working correctly")
    return all_possible_columns, region_columns_map


def test_tm3_comprehensive_grids():
    """Test comprehensive grids for Tm3 specifically."""
    print("\nTesting Tm3 comprehensive grids...")

    # Create mock page generator
    config = Mock()
    config.output = Mock()
    config.output.template_dir = "templates"

    generator = PageGenerator.create_with_factory(config, "test_output")

    # Mock the dataset query
    mock_nc = Mock()
    mock_nc.client = Mock()
    mock_nc.client.fetch_custom.return_value = create_mock_dataset_with_shared_columns()
    generator.nc = mock_nc

    # Create Tm3 specific data
    tm3_roi_data = create_tm3_roi_data()
    tm3_neurons_data = create_tm3_neurons_data()

    # Analyze Tm3 columns
    result = generator._analyze_column_roi_data(
        tm3_roi_data,
        tm3_neurons_data,
        'right',
        'Tm3',
        mock_nc,
        file_type='svg',
        save_to_files=False
    )

    assert result is not None, "Should return analysis result"

    # Check comprehensive grids
    comprehensive_grids = result['comprehensive_region_grids']
    assert comprehensive_grids, "Should have comprehensive grids"

    print(f"Generated comprehensive grids for regions: {list(comprehensive_grids.keys())}")

    # Test ME grid content
    if 'ME' in comprehensive_grids:
        me_svg = comprehensive_grids['ME']['synapse_density']
        assert '<svg' in me_svg, "ME grid should be SVG"
        assert 'Column: 27, 11' in me_svg, "ME should show column (27,11) with data"
        assert 'Column: 28, 12' in me_svg, "ME should show column (28,12) with data"
        # Should have colored hexagons for Tm3 data
        assert '#ef6548' in me_svg or '#fcbba1' in me_svg or '#fc9272' in me_svg, "ME should have colored hexagons"
        print("✓ ME grid shows Tm3 data correctly")

    # Test LO grid content
    if 'LO' in comprehensive_grids:
        lo_svg = comprehensive_grids['LO']['synapse_density']
        assert '<svg' in lo_svg, "LO grid should be SVG"
        # LO should show (27,11) as white (exists but no Tm3 data)
        assert 'Column: 27, 11' in lo_svg, "LO should show column (27,11)"
        assert 'No data for current neuron type' in lo_svg, "LO should indicate no data for Tm3 at (27,11)"
        # LO should show (28,12) as dark gray (doesn't exist in LO)
        assert 'Not available in LO' in lo_svg, "LO should show some columns as not available"
        assert '#ffffff' in lo_svg, "LO should have white hexagons for existing but empty columns"
        assert '#4a4a4a' in lo_svg, "LO should have dark gray hexagons for non-existent columns"
        print("✓ LO grid shows correct states (white for exists-but-no-data, gray for non-existent)")

    # Test LOP grid content
    if 'LOP' in comprehensive_grids:
        lop_svg = comprehensive_grids['LOP']['synapse_density']
        assert '<svg' in lop_svg, "LOP grid should be SVG"
        # LOP should show (27,11) as dark gray (doesn't exist in LOP)
        assert 'Column: 27, 11' in lop_svg, "LOP should show column (27,11)"
        assert 'Not available in LOP' in lop_svg, "LOP should indicate (27,11) not available"
        assert '#4a4a4a' in lop_svg, "LOP should have dark gray hexagons"
        print("✓ LOP grid shows (27,11) as dark gray (column doesn't exist in LOP)")

    return result


def test_visual_states_validation():
    """Test that all three visual states are correctly represented."""
    print("\nTesting visual states validation...")

    result = test_tm3_comprehensive_grids()
    comprehensive_grids = result['comprehensive_region_grids']

    states_found = {
        'has_data': False,      # Colored hexagons
        'no_data': False,       # White hexagons
        'not_in_region': False  # Dark gray hexagons
    }

    # Check each region's SVG for the different states
    for region, grids in comprehensive_grids.items():
        if grids.get('synapse_density'):
            svg_content = grids['synapse_density']

            # Check for colored hexagons (has data)
            color_patterns = ['#ef6548', '#fcbba1', '#fc9272', '#feb24c', '#fed976']
            if any(color in svg_content for color in color_patterns):
                states_found['has_data'] = True
                print(f"✓ Found 'has_data' state in {region}")

            # Check for white hexagons (exists but no data)
            if '#ffffff' in svg_content and 'stroke="#999999"' in svg_content:
                states_found['no_data'] = True
                print(f"✓ Found 'no_data' state in {region}")

            # Check for dark gray hexagons (doesn't exist in region)
            if '#4a4a4a' in svg_content:
                states_found['not_in_region'] = True
                print(f"✓ Found 'not_in_region' state in {region}")

    # Verify all states were found
    for state, found in states_found.items():
        assert found, f"State '{state}' was not found in any comprehensive grid"

    print("✓ All three visual states validated successfully")


def test_scenario_description():
    """Print a detailed description of the test scenario."""
    print("\n" + "="*70)
    print("TEST SCENARIO DESCRIPTION")
    print("="*70)
    print("Simulating the case where Tm3_R has a column at (27,11) in ME(R):")
    print()
    print("Dataset contains:")
    print("  • ME region: (27,11) with Tm3 data, (28,12) with Tm3 data")
    print("  • LO region: (27,11) with OTHER neuron data, (26,10) with other data")
    print("  • LOP region: (25,9) and (24,8) with other data")
    print()
    print("Expected comprehensive grid behavior:")
    print("  • ME grid: (27,11) = COLORED (Tm3 has data)")
    print("           (28,12) = COLORED (Tm3 has data)")
    print("           (26,10) = DARK GRAY (doesn't exist in ME)")
    print("           (25,9), (24,8) = DARK GRAY (don't exist in ME)")
    print()
    print("  • LO grid: (27,11) = WHITE (exists but Tm3 has no data)")
    print("           (26,10) = COLORED (other neurons, not Tm3)")
    print("           (28,12) = DARK GRAY (doesn't exist in LO)")
    print("           (25,9), (24,8) = DARK GRAY (don't exist in LO)")
    print()
    print("  • LOP grid: (25,9) = COLORED (other neurons)")
    print("            (24,8) = COLORED (other neurons)")
    print("            (27,11) = DARK GRAY (doesn't exist in LOP)")
    print("            (28,12) = DARK GRAY (doesn't exist in LOP)")
    print("            (26,10) = DARK GRAY (doesn't exist in LOP)")
    print("="*70)


def main():
    """Run all tests for column existence logic."""
    print("Column Existence Logic Tests")
    print("="*50)

    try:
        test_scenario_description()
        test_column_existence_logic()
        test_tm3_comprehensive_grids()
        test_visual_states_validation()

        print(f"\n🎉 All column existence logic tests passed!")
        print(f"\nKey validations:")
        print(f"  ✓ Column existence determined by ANY neuron innervation")
        print(f"  ✓ Shared columns correctly identified across regions")
        print(f"  ✓ Three visual states properly implemented:")
        print(f"    - COLORED: Current neuron has data in this column")
        print(f"    - WHITE: Column exists but current neuron has no data")
        print(f"    - DARK GRAY: Column doesn't exist in this region at all")
        print(f"  ✓ Tm3_R scenario correctly handled")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
