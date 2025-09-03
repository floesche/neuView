#!/usr/bin/env python3
"""
Phase 2 Integration Test

This test validates that Phase 2 changes work correctly in an integrated environment,
testing the removal of legacy patterns and enforcement of strict validation.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_phase2_integration():
    """Test Phase 2 changes in an integrated scenario."""
    print("=" * 60)
    print("PHASE 2 INTEGRATION TEST")
    print("=" * 60)

    # Test 1: DataAdapter strict validation
    print("\n1. Testing DataAdapter strict validation...")

    from quickpage.visualization.data_processing.data_adapter import DataAdapter
    from quickpage.visualization.data_processing.data_structures import SomaSide

    # Valid data should work
    valid_dict = {
        'hex1': 10, 'hex2': 20, 'region': 'ME', 'side': 'L',
        'total_synapses': 150, 'neuron_count': 75,
        'layers': [
            {'layer_index': 0, 'synapse_count': 50, 'neuron_count': 25, 'value': 1.2},
            {'layer_index': 1, 'synapse_count': 100, 'neuron_count': 50, 'value': 2.1}
        ]
    }

    try:
        column_data = DataAdapter._dict_to_column_data(valid_dict)
        assert column_data.side == 'L', f"Expected side 'L', got '{column_data.side}'"
        assert len(column_data.layers) == 2, f"Expected 2 layers, got {len(column_data.layers)}"
        print("✓ Valid data conversion works correctly")
    except Exception as e:
        print(f"✗ Valid data conversion failed: {e}")
        return False

    # Invalid side should fail
    invalid_dict = valid_dict.copy()
    invalid_dict['side'] = 'left'  # Should be 'L' or 'R' only

    try:
        DataAdapter._dict_to_column_data(invalid_dict)
        print("✗ Invalid side validation failed - should have raised error")
        return False
    except ValueError as e:
        if "Invalid side" in str(e):
            print("✓ Invalid side validation works correctly")
        else:
            print(f"✗ Unexpected error for invalid side: {e}")
            return False

    # Test 2: Enum-based soma_side validation
    print("\n2. Testing enum-based soma_side validation...")

    from quickpage.visualization.data_processing.column_data_manager import ColumnDataManager

    manager = ColumnDataManager()

    # Valid enum should work
    try:
        result = manager.organize_structured_data_by_side([column_data], SomaSide.LEFT)
        assert 'L' in result, "Expected 'L' key in result"
        print("✓ SomaSide enum validation works correctly")
    except Exception as e:
        print(f"✗ SomaSide enum validation failed: {e}")
        return False

    # Invalid string should fail
    try:
        manager.organize_structured_data_by_side([column_data], "invalid_enum")
        print("✗ String soma_side validation failed - should have raised error")
        return False
    except TypeError as e:
        if "must be a SomaSide enum" in str(e):
            print("✓ String soma_side validation works correctly")
        else:
            print(f"✗ Unexpected error for invalid soma_side: {e}")
            return False

    # Test 3: Data transfer objects with enum conversion
    print("\n3. Testing data transfer objects with enum conversion...")

    from quickpage.visualization.data_transfer_objects import create_grid_generation_request

    try:
        # Factory function should convert string to enum
        request = create_grid_generation_request(
            column_summary=[valid_dict],
            thresholds_all={},
            all_possible_columns=[],
            region_columns_map={},
            neuron_type='T4',
            soma_side='left'  # String input
        )

        # Should be converted to enum
        assert hasattr(request.soma_side, 'value'), "soma_side should be an enum"
        assert request.soma_side in [SomaSide.LEFT, SomaSide.L], f"Expected SomaSide.LEFT or SomaSide.L, got {request.soma_side}"
        print("✓ Factory function enum conversion works correctly")
    except Exception as e:
        print(f"✗ Factory function enum conversion failed: {e}")
        return False

    # Test 4: Strict side filtering
    print("\n4. Testing strict side filtering...")

    try:
        # Valid side filtering
        filtered = manager.filter_columns_by_side([column_data], 'L')
        assert len(filtered) == 1, f"Expected 1 filtered column, got {len(filtered)}"
        print("✓ Valid side filtering works correctly")

        # Invalid side should fail
        try:
            manager.filter_columns_by_side([column_data], 'left')
            print("✗ Invalid side filtering failed - should have raised error")
            return False
        except ValueError as e:
            if "Invalid side" in str(e):
                print("✓ Invalid side filtering validation works correctly")
            else:
                print(f"✗ Unexpected error for invalid side filtering: {e}")
                return False
    except Exception as e:
        print(f"✗ Side filtering test failed: {e}")
        return False

    # Test 5: Data processor strict type checking
    print("\n5. Testing data processor strict type checking...")

    from quickpage.visualization.data_processing.data_processor import DataProcessor
    from quickpage.visualization.data_processing.data_structures import ProcessingConfig, MetricType

    processor = DataProcessor()

    # Create test configuration
    config = ProcessingConfig(
        metric_type=MetricType.SYNAPSE_DENSITY,
        soma_side=SomaSide.LEFT,
        region_name='ME',
        neuron_type='T4'
    )

    try:
        # Valid structured data should work
        structured_columns = [column_data]
        result = processor.process_column_data(
            structured_columns,
            [{'hex1': 10, 'hex2': 20, 'region': 'ME'}],  # all_possible_columns
            {'ME_L': {(10, 20)}},  # region_columns_map
            config
        )

        assert result.is_successful, f"Processing should be successful. Errors: {result.validation_result.errors}"
        assert len(result.processed_columns) > 0, "Should have processed columns"
        print("✓ Data processor structured input works correctly")
    except Exception as e:
        print(f"✗ Data processor structured input failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ PHASE 2 INTEGRATION TEST PASSED")
    print("=" * 60)
    print("\nPhase 2 Improvements Validated:")
    print("- ✓ Strict side validation enforced")
    print("- ✓ Enum-based parameter validation working")
    print("- ✓ Legacy fallback logic removed")
    print("- ✓ Factory function enum conversion functional")
    print("- ✓ Type safety improvements confirmed")
    print("- ✓ Data integrity maintained")

    return True

def main():
    """Run the Phase 2 integration test."""
    try:
        success = test_phase2_integration()
        if success:
            print("\n🎉 Phase 2 integration test completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Phase 2 integration test failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Phase 2 integration test crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
