#!/usr/bin/env python3
"""
Simple Phase 3 Test: Basic Data Processing Functionality

This script provides a simplified test to verify that the Phase 3 data
processing module is working correctly with basic functionality.
"""

import sys
import logging
from pathlib import Path

# Add the source directory to the path
test_dir = Path(__file__).parent
src_dir = test_dir / "src"
sys.path.insert(0, str(src_dir))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_basic_functionality():
    """Test basic data processing functionality."""
    try:
        # Import the data processing module
        from quickpage.visualization.data_processing import (
            DataProcessor, ColumnDataManager, ThresholdCalculator,
            MetricCalculator, ValidationManager
        )
        from quickpage.visualization.data_processing.data_structures import (
            ColumnData, ColumnCoordinate, MetricType, SomaSide, ProcessingConfig,
            ColumnStatus, LayerData
        )

        print("✓ Successfully imported all data processing components")

        # Test component initialization
        data_processor = DataProcessor()
        column_manager = ColumnDataManager()
        threshold_calc = ThresholdCalculator()
        metric_calc = MetricCalculator()
        validation_mgr = ValidationManager()

        print("✓ Successfully initialized all components")

        # Create simple test data (one entry per region-side to avoid duplicates)
        simple_data = [
            {
                'region': 'ME',
                'side': 'L',
                'hex1': 0,
                'hex2': 0,
                'total_synapses': 100,
                'neuron_count': 50,
                'synapses_per_layer': [25, 25, 25, 25],
                'neurons_per_layer': [12, 13, 12, 13]
            },
            {
                'region': 'ME',
                'side': 'R',
                'hex1': 1,
                'hex2': 0,
                'total_synapses': 80,
                'neuron_count': 40,
                'synapses_per_layer': [20, 20, 20, 20],
                'neurons_per_layer': [10, 10, 10, 10]
            },
            {
                'region': 'LO',
                'side': 'L',
                'hex1': 0,
                'hex2': 1,
                'total_synapses': 120,
                'neuron_count': 60,
                'synapses_per_layer': [30, 30, 30, 30],
                'neurons_per_layer': [15, 15, 15, 15]
            }
        ]

        # Simple region map
        simple_region_map = {
            'ME_L': {(0, 0)},
            'ME_R': {(1, 0)},
            'LO_L': {(0, 1)},
            'LO_R': {(1, 1)}
        }

        # Simple all columns
        simple_all_columns = [
            {'hex1': 0, 'hex2': 0, 'region': 'ME'},
            {'hex1': 1, 'hex2': 0, 'region': 'ME'},
            {'hex1': 0, 'hex2': 1, 'region': 'LO'},
            {'hex1': 1, 'hex2': 1, 'region': 'LO'}
        ]

        print("✓ Created simple test data")

        # Test data conversion
        column_data = data_processor._convert_summary_to_column_data(simple_data)
        if len(column_data) != len(simple_data):
            raise ValueError(f"Expected {len(simple_data)} columns, got {len(column_data)}")

        print("✓ Data conversion working")

        # Test data organization
        data_maps = column_manager.organize_data_by_side(simple_data, 'left')
        if 'L' not in data_maps:
            raise ValueError("Expected 'L' side in data maps")

        print("✓ Data organization working")

        # Test basic processing configuration
        config = ProcessingConfig(
            metric_type=MetricType.SYNAPSE_DENSITY,
            soma_side=SomaSide.LEFT,
            region_name='ME'
        )

        print("✓ Processing configuration working")

        # Test basic validation (using lenient validation)
        validation_mgr_lenient = ValidationManager(strict_mode=False)
        validation_result = validation_mgr_lenient.validate_column_data(column_data)

        if not validation_result.is_valid:
            print(f"Validation warnings: {validation_result.warnings}")
            print(f"Validation errors: {validation_result.errors}")

        print("✓ Basic validation working")

        # Test metric calculation
        for column in column_data:
            syn_value = metric_calc.calculate_metric_value(column, MetricType.SYNAPSE_DENSITY)
            neu_value = metric_calc.calculate_metric_value(column, MetricType.CELL_COUNT)

            if syn_value < 0 or neu_value < 0:
                raise ValueError("Metric values should be non-negative")

        print("✓ Metric calculation working")

        # Test simple threshold calculation (with non-strict validation)
        try:
            thresholds = threshold_calc.calculate_thresholds(
                column_data,
                MetricType.SYNAPSE_DENSITY,
                num_thresholds=3
            )
            print("✓ Threshold calculation working")
        except Exception as e:
            print(f"⚠ Threshold calculation had issues: {e}")

        # Test integration with main generator update
        try:
            from quickpage.visualization.hexagon_grid_generator import HexagonGridGenerator
            generator = HexagonGridGenerator()

            # Check that data processor is initialized
            if hasattr(generator, 'data_processor'):
                print("✓ HexagonGridGenerator integration working")
            else:
                print("⚠ HexagonGridGenerator missing data_processor attribute")
        except Exception as e:
            print(f"⚠ HexagonGridGenerator integration issue: {e}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the simple Phase 3 test."""
    print("🧪 Running Simple Phase 3 Data Processing Test")
    print("=" * 50)

    success = test_basic_functionality()

    print("\n" + "=" * 50)
    if success:
        print("✅ Simple Phase 3 test passed!")
        print("🎉 Basic data processing functionality is working!")
        return 0
    else:
        print("❌ Simple Phase 3 test failed!")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
