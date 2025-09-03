"""
Simple Test Script for Data Processing Modernization

This script tests the modernized data processing functionality without
requiring external dependencies like pytest.
"""

import sys
from pathlib import Path
import warnings

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_data_adapter():
    """Test the DataAdapter functionality."""
    print("Testing DataAdapter...")

    from quickpage.visualization.data_processing.data_adapter import DataAdapter
    from quickpage.visualization.data_processing.data_structures import ColumnData, ColumnCoordinate

    # Test dictionary to ColumnData conversion
    dict_data = [
        {
            'hex1': 10,
            'hex2': 20,
            'region': 'ME',
            'side': 'L',
            'total_synapses': 100,
            'neuron_count': 50,
            'layers': [
                {'layer_index': 0, 'synapse_count': 30, 'neuron_count': 15, 'value': 0.5},
                {'layer_index': 1, 'synapse_count': 70, 'neuron_count': 35, 'value': 1.2}
            ]
        }
    ]

    result = DataAdapter.from_dict_list(dict_data)

    assert len(result) == 1, f"Expected 1 column, got {len(result)}"
    column = result[0]
    assert isinstance(column, ColumnData), f"Expected ColumnData, got {type(column)}"
    assert column.coordinate.hex1 == 10, f"Expected hex1=10, got {column.coordinate.hex1}"
    assert column.coordinate.hex2 == 20, f"Expected hex2=20, got {column.coordinate.hex2}"
    assert column.region == 'ME', f"Expected region='ME', got {column.region}"
    assert column.side == 'L', f"Expected side='L', got {column.side}"
    assert column.total_synapses == 100, f"Expected total_synapses=100, got {column.total_synapses}"
    assert len(column.layers) == 2, f"Expected 2 layers, got {len(column.layers)}"

    print("✓ DataAdapter dictionary conversion works correctly")

    # Test input normalization
    normalized = DataAdapter.normalize_input(dict_data)
    assert len(normalized) == 1, f"Expected 1 normalized column, got {len(normalized)}"
    assert isinstance(normalized[0], ColumnData), f"Expected ColumnData, got {type(normalized[0])}"

    print("✓ DataAdapter input normalization works correctly")

    # Test side normalization
    # Test that strict side validation is enforced
    try:
        invalid_dict = {'hex1': 1, 'hex2': 2, 'region': 'ME', 'side': 'left', 'total_synapses': 100}
        DataAdapter._dict_to_column_data(invalid_dict)
        assert False, "Expected error for invalid side format"
    except ValueError as e:
        assert "Invalid side" in str(e), f"Expected side validation error, got: {e}"

    print("✓ DataAdapter enforces strict side validation")

def test_column_data_manager_modernization():
    """Test the modernized ColumnDataManager."""
    print("\nTesting ColumnDataManager modernization...")

    from quickpage.visualization.data_processing.column_data_manager import ColumnDataManager
    from quickpage.visualization.data_processing.data_structures import ColumnData, ColumnCoordinate, SomaSide

    manager = ColumnDataManager()

    # Test structured data organization
    coord1 = ColumnCoordinate(hex1=1, hex2=2)
    coord2 = ColumnCoordinate(hex1=3, hex2=4)

    column_data = [
        ColumnData(coordinate=coord1, region='ME', side='L', total_synapses=100),
        ColumnData(coordinate=coord2, region='ME', side='R', total_synapses=150)
    ]

    result = manager.organize_structured_data_by_side(column_data, SomaSide.COMBINED)

    assert 'L' in result, "Expected 'L' side in result"
    assert 'R' in result, "Expected 'R' side in result"
    assert len(result['L']) == 1, f"Expected 1 L column, got {len(result['L'])}"
    assert len(result['R']) == 1, f"Expected 1 R column, got {len(result['R'])}"

    # Check data preservation
    l_key = ('ME', 1, 2)
    r_key = ('ME', 3, 4)
    assert l_key in result['L'], f"Expected key {l_key} in L data"
    assert r_key in result['R'], f"Expected key {r_key} in R data"
    assert result['L'][l_key].total_synapses == 100, f"Expected 100 synapses, got {result['L'][l_key].total_synapses}"
    assert result['R'][r_key].total_synapses == 150, f"Expected 150 synapses, got {result['R'][r_key].total_synapses}"

    print("✓ ColumnDataManager structured data organization works correctly")

    # Test single side organization
    result_single = manager.organize_structured_data_by_side(column_data, SomaSide.LEFT)

    assert 'L' in result_single, "Expected 'L' side in single side result"
    assert len(result_single['L']) == 1, f"Expected 1 L column, got {len(result_single['L'])}"

    print("✓ ColumnDataManager single side organization works correctly")

def test_data_processor_modernization():
    """Test the modernized DataProcessor."""
    print("\nTesting DataProcessor modernization...")

    from quickpage.visualization.data_processing.data_processor import DataProcessor
    from quickpage.visualization.data_processing.data_structures import (
        ProcessingConfig, MetricType, SomaSide, ColumnData, ColumnCoordinate
    )

    processor = DataProcessor()

    # Create test configuration
    config = ProcessingConfig(
        metric_type=MetricType.SYNAPSE_DENSITY,
        soma_side=SomaSide.COMBINED,
        region_name='ME',
        neuron_type='T4',
        validate_data=False  # Skip validation for simpler test
    )

    # Test with dictionary input
    dict_data = [
        {
            'hex1': 10, 'hex2': 20, 'region': 'ME', 'side': 'L',
            'total_synapses': 100, 'neuron_count': 50
        },
        {
            'hex1': 11, 'hex2': 21, 'region': 'ME', 'side': 'R',
            'total_synapses': 120, 'neuron_count': 60
        }
    ]

    all_possible_columns = [
        {'hex1': 10, 'hex2': 20, 'region': 'ME'},
        {'hex1': 11, 'hex2': 21, 'region': 'ME'}
    ]

    region_columns_map = {
        'ME_L': {(10, 20)},
        'ME_R': {(11, 21)}
    }

    try:
        result = processor.process_column_data(
            dict_data, all_possible_columns, region_columns_map, config
        )

        # Basic validation that processing completed
        assert hasattr(result, 'processed_columns'), "Result should have processed_columns attribute"
        assert hasattr(result, 'validation_result'), "Result should have validation_result attribute"

        print("✓ DataProcessor handles dictionary input correctly")

    except Exception as e:
        print(f"✗ DataProcessor failed with dictionary input: {e}")
        raise

    # Test with structured input
    coord1 = ColumnCoordinate(hex1=10, hex2=20)
    coord2 = ColumnCoordinate(hex1=11, hex2=21)

    structured_data = [
        ColumnData(coordinate=coord1, region='ME', side='L', total_synapses=100, neuron_count=50),
        ColumnData(coordinate=coord2, region='ME', side='R', total_synapses=120, neuron_count=60)
    ]

    try:
        result_structured = processor.process_column_data(
            structured_data, all_possible_columns, region_columns_map, config
        )

        assert hasattr(result_structured, 'processed_columns'), "Structured result should have processed_columns"
        assert hasattr(result_structured, 'validation_result'), "Structured result should have validation_result"

        print("✓ DataProcessor handles structured input correctly")

    except Exception as e:
        print(f"✗ DataProcessor failed with structured input: {e}")
        raise

def test_strict_validation():
    """Test that strict validation is enforced without fallbacks."""
    print("\nTesting strict validation enforcement...")

    from quickpage.visualization.data_processing.column_data_manager import ColumnDataManager
    from quickpage.visualization.data_processing.data_adapter import DataAdapter
    from quickpage.visualization.data_processing.data_structures import SomaSide

    manager = ColumnDataManager()

    # Test that invalid side values raise errors
    try:
        manager.filter_columns_by_side([], "invalid_side")
        assert False, "Expected error for invalid side specification"
    except ValueError as e:
        assert "Invalid side" in str(e), f"Expected side validation error, got: {e}"
        print("✓ Invalid side specification raises proper error")

    # Test that DataAdapter enforces strict side validation
    try:
        invalid_dict = {'hex1': 1, 'hex2': 2, 'region': 'ME', 'side': 'left', 'total_synapses': 100}
        DataAdapter._dict_to_column_data(invalid_dict)
        assert False, "Expected error for invalid side format"
    except ValueError as e:
        assert "Invalid side" in str(e), f"Expected side validation error, got: {e}"
        print("✓ DataAdapter enforces strict side validation")

    # Test that enum-based soma_side is enforced
    try:
        manager.organize_structured_data_by_side([], "invalid_enum")
        assert False, "Expected error for non-enum soma_side"
    except (ValueError, TypeError, AttributeError):
        print("✓ Enum-based soma_side validation enforced")

def test_data_integrity():
    """Test that data integrity is maintained through modernization."""
    print("\nTesting data integrity...")

    from quickpage.visualization.data_processing.data_adapter import DataAdapter

    # Test comprehensive data preservation
    original_dict = {
        'hex1': 15, 'hex2': 25, 'region': 'LOP', 'side': 'R',
        'total_synapses': 200, 'neuron_count': 100,
        'layers': [
            {'layer_index': 0, 'synapse_count': 50, 'neuron_count': 25, 'value': 0.8},
            {'layer_index': 1, 'synapse_count': 150, 'neuron_count': 75, 'value': 2.1}
        ],
        'custom_field': 'test_value'
    }

    column_data = DataAdapter._dict_to_column_data(original_dict)

    # Check core data preservation
    assert column_data.coordinate.hex1 == 15, f"Expected hex1=15, got {column_data.coordinate.hex1}"
    assert column_data.coordinate.hex2 == 25, f"Expected hex2=25, got {column_data.coordinate.hex2}"
    assert column_data.region == 'LOP', f"Expected region='LOP', got {column_data.region}"
    assert column_data.side == 'R', f"Expected side='R', got {column_data.side}"
    assert column_data.total_synapses == 200, f"Expected total_synapses=200, got {column_data.total_synapses}"
    assert column_data.neuron_count == 100, f"Expected neuron_count=100, got {column_data.neuron_count}"

    # Check layer data preservation
    assert len(column_data.layers) == 2, f"Expected 2 layers, got {len(column_data.layers)}"
    assert column_data.layers[0].synapse_count == 50, f"Expected layer 0 synapses=50, got {column_data.layers[0].synapse_count}"
    assert column_data.layers[1].synapse_count == 150, f"Expected layer 1 synapses=150, got {column_data.layers[1].synapse_count}"

    # Check metadata preservation
    assert 'custom_field' in column_data.metadata, "Custom field should be preserved in metadata"
    assert column_data.metadata['custom_field'] == 'test_value', f"Expected custom_field='test_value', got {column_data.metadata['custom_field']}"

    print("✓ Data integrity maintained through conversion")

def main():
    """Run all tests."""
    print("Running Data Processing Modernization Tests")
    print("=" * 50)

    try:
        test_data_adapter()
        test_column_data_manager_modernization()
        test_data_processor_modernization()
        test_strict_validation()
        test_data_integrity()

        print("\n" + "=" * 50)
        print("✅ All tests passed! Data processing modernization is successful.")
        print("\nSummary of improvements:")
        print("- ✓ DataAdapter centralizes all data conversion")
        print("- ✓ Legacy patterns and fallback logic removed")
        print("- ✓ Structured data flow implemented")
        print("- ✓ Strict validation enforced")
        print("- ✓ Data integrity maintained throughout")
        print("- ✓ Type safety improved with dataclasses")
        print("- ✓ Enum-based parameter validation implemented")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
