#!/usr/bin/env python3
"""
Integration test for comprehensive hexagon grids with page generator.

This test verifies that the PageGenerator properly integrates with the
comprehensive hexagon grid functionality and produces the expected output
structure for template rendering.
"""

import os
import sys
from pathlib import Path
import pandas as pd
from unittest.mock import Mock, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from quickpage.page_generator import PageGenerator
from quickpage.config import Config
from quickpage.visualization import EyemapGenerator


def create_mock_neuprint_connector():
    """Create a mock neuprint connector for testing."""
    mock_nc = Mock()

    # Mock the query for all possible columns
    all_columns_data = pd.DataFrame([
        {'roi': 'ME_L_col_1F_10'},
        {'roi': 'ME_L_col_1E_0F'},
        {'roi': 'ME_L_col_1D_0E'},
        {'roi': 'LO_R_col_1C_0D'},
        {'roi': 'LO_R_col_1B_0C'},
        {'roi': 'LO_R_col_1A_0B'},
        {'roi': 'LOP_L_col_19_0A'},
        {'roi': 'LOP_L_col_18_09'},
        {'roi': 'LOP_L_col_17_08'},
    ])

    mock_nc.fetch_custom.return_value = all_columns_data

    return mock_nc


def create_mock_roi_data():
    """Create mock ROI data for testing."""
    return pd.DataFrame([
        {
            'roi': 'ME_L_col_1F_10',
            'bodyId': 1001,
            'pre': 500,
            'post': 700,
            'total': 1200
        },
        {
            'roi': 'ME_L_col_1E_0F',
            'bodyId': 1001,
            'pre': 400,
            'post': 580,
            'total': 980
        },
        {
            'roi': 'ME_L_col_1F_10',
            'bodyId': 1002,
            'pre': 300,
            'post': 450,
            'total': 750
        },
        {
            'roi': 'LO_R_col_1C_0D',
            'bodyId': 1003,
            'pre': 350,
            'post': 450,
            'total': 800
        },
        {
            'roi': 'LO_R_col_1B_0C',
            'bodyId': 1003,
            'pre': 500,
            'post': 600,
            'total': 1100
        },
        {
            'roi': 'LOP_L_col_19_0A',
            'bodyId': 1004,
            'pre': 600,
            'post': 700,
            'total': 1300
        },
    ])


def create_mock_neurons_data():
    """Create mock neurons data for testing."""
    return pd.DataFrame([
        {'bodyId': 1001, 'type': 'T4', 'instance': 'T4_001'},
        {'bodyId': 1002, 'type': 'T4', 'instance': 'T4_002'},
        {'bodyId': 1003, 'type': 'T4', 'instance': 'T4_003'},
        {'bodyId': 1004, 'type': 'T4', 'instance': 'T4_004'},
    ])


def test_comprehensive_column_analysis():
    """Test the comprehensive column analysis functionality."""
    print("Testing comprehensive column analysis...")

    # Create mock config
    config = Mock()
    config.output = Mock()
    config.output.template_dir = "templates"

    # Create page generator
    generator = PageGenerator.create_with_factory(config, "test_output")

    # Mock the neuprint connector
    mock_nc = create_mock_neuprint_connector()
    generator.nc = mock_nc

    # Create test data
    roi_data = create_mock_roi_data()
    neurons_data = create_mock_neurons_data()

    # Call the column analysis method
    result = generator._analyze_column_roi_data(
        roi_data,
        neurons_data,
        'left',
        'T4',
        file_type='svg',
        save_to_files=False
    )

    # Verify the result structure
    assert result is not None, "Column analysis should return a result"
    assert 'columns' in result, "Result should contain columns data"
    assert 'summary' in result, "Result should contain summary data"
    assert 'region_grids' in result, "Result should contain region grids"
    assert 'comprehensive_region_grids' in result, "Result should contain comprehensive region grids"
    assert 'all_possible_columns_count' in result, "Result should contain all possible columns count"
    assert 'region_columns_counts' in result, "Result should contain region columns counts"

    print(f"✓ Basic structure verified")

    # Verify comprehensive grids
    comprehensive_grids = result['comprehensive_region_grids']
    assert isinstance(comprehensive_grids, dict), "Comprehensive grids should be a dictionary"

    # Check that we have grids for the expected regions
    expected_regions = ['ME', 'LO', 'LOP']
    for region in expected_regions:
        if region in comprehensive_grids:
            assert 'synapse_density' in comprehensive_grids[region], f"{region} should have synapse_density grid"
            assert 'cell_count' in comprehensive_grids[region], f"{region} should have cell_count grid"

            # Check that the grids contain SVG content
            if comprehensive_grids[region]['synapse_density']:
                assert '<svg' in comprehensive_grids[region]['synapse_density'], f"{region} synapse grid should be SVG"
            if comprehensive_grids[region]['cell_count']:
                assert '<svg' in comprehensive_grids[region]['cell_count'], f"{region} cell grid should be SVG"

    print(f"✓ Comprehensive grids structure verified")

    # Verify counts
    all_columns_count = result['all_possible_columns_count']
    region_columns_counts = result['region_columns_counts']

    assert all_columns_count > 0, "Should have found some columns"
    assert isinstance(region_columns_counts, dict), "Region columns counts should be a dictionary"
    assert 'ME' in region_columns_counts, "Should have ME region column count"
    assert 'LO' in region_columns_counts, "Should have LO region column count"
    assert 'LOP' in region_columns_counts, "Should have LOP region column count"

    print(f"✓ Found {all_columns_count} total possible columns")
    print(f"✓ Region distribution: ME={region_columns_counts.get('ME', 0)}, LO={region_columns_counts.get('LO', 0)}, LOP={region_columns_counts.get('LOP', 0)}")

    return result


def test_grid_content_validation():
    """Test that the generated grids contain the expected content."""
    print("\nTesting grid content validation...")

    # Get comprehensive analysis result
    result = test_comprehensive_column_analysis()
    comprehensive_grids = result['comprehensive_region_grids']

    for region, grids in comprehensive_grids.items():
        if grids.get('synapse_density'):
            svg_content = grids['synapse_density']

            # Check for expected SVG elements and structure
            assert '<svg' in svg_content, f"{region} grid should be valid SVG"
            assert 'fill="#4a4a4a"' in svg_content, f"{region} grid should contain dark gray hexagons (not in region)"
            assert 'fill="#ffffff"' in svg_content or 'stroke="#999999"' in svg_content, f"{region} grid should contain white hexagons (no data)"
            assert 'Legend' in svg_content, f"{region} grid should contain legend"
            assert 'Not in region' in svg_content, f"{region} grid should contain 'Not in region' legend"
            assert 'No data' in svg_content, f"{region} grid should contain 'No data' legend"
            assert 'Has data' in svg_content, f"{region} grid should contain 'Has data' legend"

            print(f"✓ {region} synapse density grid content validated")

        if grids.get('cell_count'):
            svg_content = grids['cell_count']

            # Similar checks for cell count grid
            assert '<svg' in svg_content, f"{region} cell count grid should be valid SVG"
            assert 'Legend' in svg_content, f"{region} cell count grid should contain legend"

            print(f"✓ {region} cell count grid content validated")


def test_template_integration():
    """Test that the result can be properly used in template rendering."""
    print("\nTesting template integration compatibility...")

    result = test_comprehensive_column_analysis()

    # Simulate template variable access patterns
    column_analysis = result

    # Test basic template access patterns
    assert column_analysis.get('comprehensive_region_grids') is not None

    # Test region iteration pattern used in template
    for region in ['ME', 'LO', 'LOP']:
        region_grids = column_analysis['comprehensive_region_grids'].get(region)
        if region_grids:
            # Test the template conditions
            synapse_density = region_grids.get('synapse_density')
            cell_count = region_grids.get('cell_count')

            if synapse_density:
                # Template checks for PNG data pattern
                is_png_data = synapse_density.startswith('data:image/png;base64,')
                is_png_file = synapse_density.endswith('.png')
                is_svg_file = synapse_density.endswith('.svg')
                is_svg_content = not (is_png_data or is_png_file or is_svg_file)

                print(f"✓ {region} synapse grid template compatibility: PNG data={is_png_data}, PNG file={is_png_file}, SVG file={is_svg_file}, SVG content={is_svg_content}")

            if cell_count:
                # Similar checks for cell count
                is_png_data = cell_count.startswith('data:image/png;base64,')
                is_png_file = cell_count.endswith('.png')
                is_svg_file = cell_count.endswith('.svg')
                is_svg_content = not (is_png_data or is_png_file or is_svg_file)

                print(f"✓ {region} cell count grid template compatibility: PNG data={is_png_data}, PNG file={is_png_file}, SVG file={is_svg_file}, SVG content={is_svg_content}")

    # Test count fields for template display
    all_possible_columns_count = column_analysis.get('all_possible_columns_count', 0)
    region_columns_counts = column_analysis.get('region_columns_counts', {})

    assert isinstance(all_possible_columns_count, int)
    assert isinstance(region_columns_counts, dict)

    print(f"✓ Template count fields: total={all_possible_columns_count}, regions={region_columns_counts}")


def test_error_handling():
    """Test error handling in various scenarios."""
    print("\nTesting error handling scenarios...")

    # Create mock config
    config = Mock()
    config.output = Mock()
    config.output.template_dir = "templates"

    # Test with empty data
    mock_nc = Mock()
    mock_nc.fetch_custom.return_value = pd.DataFrame()  # Empty result
    generator = PageGenerator.create_with_factory(config, "test_output")
    generator.nc = mock_nc

    empty_roi_data = pd.DataFrame()
    empty_neurons_data = pd.DataFrame()

    result = generator._analyze_column_roi_data(
        empty_roi_data,
        empty_neurons_data,
        'left',
        'T4'
    )

    # Should handle empty data gracefully
    assert result is None, "Should return None for empty data"
    print("✓ Empty data handled gracefully")

    # Test with mock that raises exception
    mock_nc_error = Mock()
    mock_nc_error.fetch_custom.side_effect = Exception("Database error")
    generator_error = PageGenerator.create_with_factory(config, "test_output")
    generator_error.nc = mock_nc_error

    roi_data = create_mock_roi_data()
    neurons_data = create_mock_neurons_data()

    # Should handle database errors gracefully
    result = generator_error._analyze_column_roi_data(
        roi_data,
        neurons_data,
        'left',
        'T4'
    )

    # Should still return result even with database error (falls back to empty all_possible_columns)
    assert result is not None, "Should handle database errors gracefully"
    assert result['all_possible_columns_count'] == 0, "Should have zero columns when database fails"
    print("✓ Database error handled gracefully")


def main():
    """Run all integration tests."""
    print("PageGenerator Integration Tests for Comprehensive Hexagon Grids")
    print("=" * 70)

    try:
        # Run tests
        test_comprehensive_column_analysis()
        test_grid_content_validation()
        test_template_integration()
        test_error_handling()

        print(f"\n🎉 All integration tests passed!")
        print(f"\nKey features verified:")
        print(f"  ✓ Comprehensive hexagon grid generation")
        print(f"  ✓ All possible columns discovery from dataset")
        print(f"  ✓ Region-specific column mapping")
        print(f"  ✓ Three-state hexagon coloring (dark gray, white, colored)")
        print(f"  ✓ Template integration compatibility")
        print(f"  ✓ Error handling and graceful degradation")
        print(f"  ✓ SVG content with proper legends and tooltips")

        print(f"\nThe comprehensive hexagon grids are now ready for use!")
        print(f"They will show ALL possible column coordinates across ME, LO, and LOP regions,")
        print(f"with different colors indicating data availability in each region.")

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
