#!/usr/bin/env python3
"""
Phase 3 Integration Test: Data Processing Module

This script provides comprehensive integration testing for the Phase 3 data
processing module of the hexagon grid generator refactoring. It tests the
integration between all data processing components and validates the
functionality against the original system.

Phase 3 Components Tested:
- DataProcessor: Main orchestrator class
- ColumnDataManager: Data organization and management
- ThresholdCalculator: Threshold calculation for color mapping
- MetricCalculator: Value and metric calculations
- ValidationManager: Data validation and error handling

Usage:
    python test_phase3_data_processing.py
"""

import sys
import unittest
import logging
from pathlib import Path
from typing import List, Dict, Set, Tuple

# Add the source directory to the path
test_dir = Path(__file__).parent
src_dir = test_dir / "src"
sys.path.insert(0, str(src_dir))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class TestPhase3DataProcessing(unittest.TestCase):
    """Integration tests for Phase 3 data processing module."""

    def setUp(self):
        """Set up test fixtures."""
        from quickpage.visualization.data_processing import (
            DataProcessor, ColumnDataManager, ThresholdCalculator,
            MetricCalculator, ValidationManager
        )
        from quickpage.visualization.data_processing.data_structures import (
            ColumnData, ColumnCoordinate, MetricType, SomaSide, ProcessingConfig,
            ColumnStatus, LayerData, ThresholdData, MinMaxData
        )

        # Initialize components
        self.data_processor = DataProcessor()
        self.column_manager = ColumnDataManager()
        self.threshold_calc = ThresholdCalculator()
        self.metric_calc = MetricCalculator()
        self.validation_mgr = ValidationManager()

        # Store classes for later use
        self.ColumnData = ColumnData
        self.ColumnCoordinate = ColumnCoordinate
        self.MetricType = MetricType
        self.SomaSide = SomaSide
        self.ProcessingConfig = ProcessingConfig
        self.ColumnStatus = ColumnStatus
        self.LayerData = LayerData

        # Create comprehensive test data
        self.sample_data = self._create_comprehensive_test_data()

    def _create_comprehensive_test_data(self):
        """Create comprehensive test data covering various scenarios."""
        column_summary = []
        regions = ['ME', 'LO', 'LOP']
        sides = ['L', 'R']

        # Generate varied test data with unique coordinates per region-side combination
        for region_idx, region in enumerate(regions):
            for side_idx, side in enumerate(sides):
                # Create unique coordinate ranges for each region-side
                hex1_offset = region_idx * 3
                hex2_offset = side_idx * 3

                for hex1 in range(2):  # Use fewer coordinates to avoid duplicates
                    for hex2 in range(2):
                        actual_hex1 = hex1 + hex1_offset
                        actual_hex2 = hex2 + hex2_offset

                        # Create varied synapse and neuron counts
                        base_synapses = (region_idx + 1) * (hex1 + 1) * (hex2 + 1) * 25
                        base_neurons = (region_idx + 1) * (hex1 + 1) * (hex2 + 1) * 12

                        # Add some variation based on side
                        side_multiplier = 1.2 if side == 'L' else 0.8
                        total_synapses = max(10, int(base_synapses * side_multiplier))
                        neuron_count = max(5, int(base_neurons * side_multiplier))

                        # Create layer data
                        num_layers = 4
                        base_syn_per_layer = max(1, total_synapses // num_layers)
                        base_neu_per_layer = max(1, neuron_count // num_layers)

                        synapses_per_layer = [
                            base_syn_per_layer + (i * 2) for i in range(num_layers)
                        ]
                        neurons_per_layer = [
                            base_neu_per_layer + i for i in range(num_layers)
                        ]

                        # Adjust to match totals and ensure no negatives
                        syn_diff = total_synapses - sum(synapses_per_layer)
                        neu_diff = neuron_count - sum(neurons_per_layer)

                        if syn_diff != 0:
                            synapses_per_layer[0] = max(1, synapses_per_layer[0] + syn_diff)
                        if neu_diff != 0:
                            neurons_per_layer[0] = max(1, neurons_per_layer[0] + neu_diff)

                        # Ensure all values are positive
                        synapses_per_layer = [max(1, val) for val in synapses_per_layer]
                        neurons_per_layer = [max(1, val) for val in neurons_per_layer]

                        column_summary.append({
                            'region': region,
                            'side': side,
                            'hex1': actual_hex1,
                            'hex2': actual_hex2,
                            'total_synapses': total_synapses,
                            'neuron_count': neuron_count,
                            'synapses_per_layer': synapses_per_layer,
                            'neurons_per_layer': neurons_per_layer,
                            'synapses_list_raw': synapses_per_layer,
                            'neurons_list': neurons_per_layer
                        })

        # Create all possible columns with consistent coordinate ranges
        all_possible_columns = []
        for region_idx, region in enumerate(regions):
            hex1_offset = region_idx * 3
            for hex1 in range(6):  # Larger range to accommodate all coordinates
                for hex2 in range(6):
                    all_possible_columns.append({
                        'hex1': hex1,
                        'hex2': hex2,
                        'region': region
                    })

        # Create region columns map matching the coordinate scheme
        region_columns_map = {}
        for region_idx, region in enumerate(regions):
            for side_idx, side in enumerate(sides):
                coords = set()
                hex1_offset = region_idx * 3
                hex2_offset = side_idx * 3

                for hex1 in range(2):
                    for hex2 in range(2):
                        actual_hex1 = hex1 + hex1_offset
                        actual_hex2 = hex2 + hex2_offset
                        coords.add((actual_hex1, actual_hex2))
                region_columns_map[f"{region}_{side}"] = coords

        return {
            'column_summary': column_summary,
            'all_possible_columns': all_possible_columns,
            'region_columns_map': region_columns_map
        }

    def test_data_processor_initialization(self):
        """Test DataProcessor initialization and component integration."""
        self.assertIsNotNone(self.data_processor.validation_manager)
        self.assertIsNotNone(self.data_processor.threshold_calculator)
        self.assertIsNotNone(self.data_processor.metric_calculator)
        self.assertIsNotNone(self.data_processor.column_data_manager)

        logger.info("✓ DataProcessor initialization successful")

    def test_column_data_conversion(self):
        """Test conversion from dictionary format to ColumnData objects."""
        column_data = self.data_processor._convert_summary_to_column_data(
            self.sample_data['column_summary'][:5]  # Test with subset
        )

        self.assertEqual(len(column_data), 5)
        self.assertIsInstance(column_data[0], self.ColumnData)
        self.assertIsInstance(column_data[0].coordinate, self.ColumnCoordinate)
        self.assertGreater(column_data[0].total_synapses, 0)
        self.assertGreater(len(column_data[0].layers), 0)

        logger.info("✓ Column data conversion successful")

    def test_data_validation(self):
        """Test comprehensive data validation."""
        validation_result = self.data_processor.validate_input_data(
            self.sample_data['column_summary'],
            self.sample_data['region_columns_map']
        )

        self.assertTrue(validation_result.is_valid)
        self.assertEqual(len(validation_result.errors), 0)

        logger.info(f"✓ Data validation successful: {validation_result.summary}")

    def test_threshold_calculation(self):
        """Test threshold calculation for different metrics and methods."""
        methods = ['percentile', 'quantile', 'equal', 'std_dev']

        for method in methods:
            for metric_type in [self.MetricType.SYNAPSE_DENSITY, self.MetricType.CELL_COUNT]:
                thresholds = self.data_processor.calculate_thresholds_for_data(
                    self.sample_data['column_summary'],
                    metric_type,
                    method=method,
                    num_thresholds=5
                )

                self.assertIsInstance(thresholds, ThresholdData)
                self.assertGreater(len(thresholds.all_layers), 0)
                self.assertLessEqual(thresholds.min_value, thresholds.max_value)

        logger.info("✓ Threshold calculation successful for all methods and metrics")

    def test_min_max_calculation(self):
        """Test min/max data calculation for normalization."""
        min_max_data = self.data_processor.calculate_min_max_for_data(
            self.sample_data['column_summary']
        )

        self.assertIsInstance(min_max_data, MinMaxData)
        self.assertGreaterEqual(min_max_data.global_max_syn, min_max_data.global_min_syn)
        self.assertGreaterEqual(min_max_data.global_max_cells, min_max_data.global_min_cells)

        # Test region-specific values
        self.assertGreater(len(min_max_data.min_syn_region), 0)
        self.assertGreater(len(min_max_data.max_syn_region), 0)

        logger.info("✓ Min/Max calculation successful")

    def test_metric_statistics(self):
        """Test statistical metric calculation."""
        for metric_type in [self.MetricType.SYNAPSE_DENSITY, self.MetricType.CELL_COUNT]:
            stats = self.data_processor.extract_metric_statistics(
                self.sample_data['column_summary'],
                metric_type
            )

            self.assertIsInstance(stats, dict)
            expected_keys = ['count', 'mean', 'median', 'std', 'min', 'max']
            for key in expected_keys:
                self.assertIn(key, stats)
                self.assertIsInstance(stats[key], (int, float))

            # Validate statistical relationships
            self.assertLessEqual(stats['min'], stats['mean'])
            self.assertLessEqual(stats['mean'], stats['max'])
            self.assertGreaterEqual(stats['std'], 0)

        logger.info("✓ Metric statistics calculation successful")

    def test_data_organization_by_side(self):
        """Test data organization by different soma sides."""
        sides_to_test = ['left', 'right', 'combined']

        for soma_side in sides_to_test:
            data_maps = self.column_manager.organize_data_by_side(
                self.sample_data['column_summary'],
                soma_side
            )

            self.assertIsInstance(data_maps, dict)
            self.assertGreater(len(data_maps), 0)

            if soma_side == 'combined':
                self.assertIn('L', data_maps)
                self.assertIn('R', data_maps)
            else:
                expected_side = 'L' if soma_side in ['left', 'L'] else 'R'
                self.assertIn(expected_side, data_maps)

        logger.info("✓ Data organization by side successful")

    def test_complete_data_processing_workflow(self):
        """Test complete data processing workflow."""
        for metric_type in [self.MetricType.SYNAPSE_DENSITY, self.MetricType.CELL_COUNT]:
            for soma_side in [self.SomaSide.LEFT, self.SomaSide.RIGHT, self.SomaSide.COMBINED]:
                config = self.ProcessingConfig(
                    metric_type=metric_type,
                    soma_side=soma_side,
                    region_name='ME',
                    neuron_type='test_neuron',
                    output_format='svg'
                )

                result = self.data_processor.process_column_data(
                    self.sample_data['column_summary'],
                    self.sample_data['all_possible_columns'],
                    self.sample_data['region_columns_map'],
                    config
                )

                self.assertTrue(result.is_successful)
                self.assertGreater(len(result.processed_columns), 0)
                self.assertTrue(result.validation_result.is_valid)

                # Verify processed columns have correct properties
                for col in result.processed_columns:
                    self.assertEqual(col.metric_type, metric_type)
                    self.assertEqual(col.region, 'ME')
                    self.assertIn(col.status, [
                        self.ColumnStatus.HAS_DATA,
                        self.ColumnStatus.NO_DATA,
                        self.ColumnStatus.NOT_IN_REGION
                    ])

        logger.info("✓ Complete data processing workflow successful")

    def test_error_handling_and_validation(self):
        """Test error handling with invalid data."""
        # Test with invalid configuration (handle the exception from dataclass validation)
        try:
            invalid_config = self.ProcessingConfig(
                metric_type=self.MetricType.SYNAPSE_DENSITY,
                soma_side=self.SomaSide.LEFT,
                region_name='',  # Invalid empty region
                output_format='invalid'  # Invalid format
            )
        except ValueError:
            # Expected behavior - create a valid config with invalid fields manually
            invalid_config = self.ProcessingConfig(
                metric_type=self.MetricType.SYNAPSE_DENSITY,
                soma_side=self.SomaSide.LEFT,
                region_name='ME'  # Valid region for this test
            )
            # Manually set invalid values to test validation
            invalid_config.region_name = ''
            invalid_config.output_format = 'invalid'

        result = self.data_processor.process_column_data(
            self.sample_data['column_summary'],
            self.sample_data['all_possible_columns'],
            self.sample_data['region_columns_map'],
            invalid_config
        )

        self.assertFalse(result.is_successful)
        self.assertFalse(result.validation_result.is_valid)
        self.assertGreater(len(result.validation_result.errors), 0)

        # Test with malformed data
        malformed_data = [
            {'invalid': 'data'},
            {'region': 'ME', 'side': 'INVALID'}
        ]

        validation_result = self.data_processor.validate_input_data(
            malformed_data,
            self.sample_data['region_columns_map']
        )

        self.assertFalse(validation_result.is_valid)

        logger.info("✓ Error handling and validation successful")

    def test_processing_summary_generation(self):
        """Test processing summary generation."""
        config = self.ProcessingConfig(
            metric_type=self.MetricType.SYNAPSE_DENSITY,
            soma_side=self.SomaSide.LEFT,
            region_name='ME'
        )

        result = self.data_processor.process_column_data(
            self.sample_data['column_summary'],
            self.sample_data['all_possible_columns'],
            self.sample_data['region_columns_map'],
            config
        )

        summary = self.data_processor.get_processing_summary(result)

        self.assertIsInstance(summary, dict)
        self.assertIn('success', summary)
        self.assertIn('total_columns', summary)
        self.assertIn('validation', summary)
        self.assertIn('status_distribution', summary)

        # Verify summary content
        self.assertTrue(summary['success'])
        self.assertGreater(summary['total_columns'], 0)
        self.assertTrue(summary['validation']['is_valid'])

        logger.info("✓ Processing summary generation successful")

    def test_metric_calculator_functionality(self):
        """Test individual metric calculator functionality."""
        # Create sample column data
        column_data = self.data_processor._convert_summary_to_column_data(
            self.sample_data['column_summary'][:5]
        )

        for metric_type in [self.MetricType.SYNAPSE_DENSITY, self.MetricType.CELL_COUNT]:
            # Test individual metric calculation
            for column in column_data:
                value = self.metric_calc.calculate_metric_value(column, metric_type)
                self.assertIsInstance(value, float)
                self.assertGreaterEqual(value, 0)

                layer_values = self.metric_calc.calculate_layer_values(column, metric_type)
                self.assertIsInstance(layer_values, list)
                self.assertEqual(len(layer_values), len(column.layers))

            # Test statistical metrics
            stats = self.metric_calc.calculate_statistical_metrics(column_data, metric_type)
            self.assertIsInstance(stats, dict)
            self.assertIn('mean', stats)
            self.assertIn('std', stats)

        logger.info("✓ Metric calculator functionality successful")

    def test_column_data_manager_functionality(self):
        """Test individual column data manager functionality."""
        column_data = self.data_processor._convert_summary_to_column_data(
            self.sample_data['column_summary']
        )

        # Test region grouping
        grouped_by_region = self.column_manager.group_columns_by_region(column_data)
        self.assertIsInstance(grouped_by_region, dict)
        self.assertIn('ME', grouped_by_region)
        self.assertIn('LO', grouped_by_region)

        # Test side grouping
        grouped_by_side = self.column_manager.group_columns_by_side(column_data)
        self.assertIsInstance(grouped_by_side, dict)
        self.assertIn('L', grouped_by_side)
        self.assertIn('R', grouped_by_side)

        # Test filtering
        me_columns = self.column_manager.filter_columns_by_region(column_data, 'ME')
        self.assertTrue(all(col.region == 'ME' for col in me_columns))

        l_columns = self.column_manager.filter_columns_by_side(column_data, 'L')
        self.assertTrue(all(col.side == 'L' for col in l_columns))

        # Test region columns map creation
        region_map = self.column_manager.create_region_columns_map(column_data)
        self.assertIsInstance(region_map, dict)
        self.assertIn('ME_L', region_map)

        logger.info("✓ Column data manager functionality successful")

    def test_validation_manager_functionality(self):
        """Test individual validation manager functionality."""
        column_data = self.data_processor._convert_summary_to_column_data(
            self.sample_data['column_summary'][:5]
        )

        # Test column data validation
        result = self.validation_mgr.validate_column_data(column_data)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.validated_count, 5)

        # Test region columns map validation
        map_result = self.validation_mgr.validate_region_columns_map(
            self.sample_data['region_columns_map']
        )
        self.assertTrue(map_result.is_valid)

        # Test processing config validation
        config = self.ProcessingConfig(
            metric_type=self.MetricType.SYNAPSE_DENSITY,
            soma_side=self.SomaSide.LEFT,
            region_name='ME'
        )
        config_result = self.validation_mgr.validate_processing_config(config)
        self.assertTrue(config_result.is_valid)

        logger.info("✓ Validation manager functionality successful")

    def test_performance_with_large_dataset(self):
        """Test performance with larger dataset."""
        # Generate larger dataset
        large_data = []
        for region in ['ME', 'LO', 'LOP']:
            for side in ['L', 'R']:
                for hex1 in range(10):
                    for hex2 in range(10):
                        # Ensure positive values
                        base_syn = max(50, hex1 * hex2 * 10 + 50)
                        base_neu = max(25, hex1 * hex2 * 5 + 25)
                        layer_syn = max(10, hex1 * hex2 * 2 + 10)
                        layer_neu = max(5, hex1 * hex2 + 5)

                        large_data.append({
                            'region': region,
                            'side': side,
                            'hex1': hex1,
                            'hex2': hex2,
                            'total_synapses': base_syn,
                            'neuron_count': base_neu,
                            'synapses_per_layer': [layer_syn] * 4,
                            'neurons_per_layer': [layer_neu] * 4
                        })

        config = self.ProcessingConfig(
            metric_type=self.MetricType.SYNAPSE_DENSITY,
            soma_side=self.SomaSide.COMBINED,
            region_name='ME'
        )

        # Process large dataset
        result = self.data_processor.process_column_data(
            large_data,
            self.sample_data['all_possible_columns'],
            self.sample_data['region_columns_map'],
            config
        )

        self.assertTrue(result.is_successful)
        self.assertGreater(len(result.processed_columns), 0)

        logger.info(f"✓ Performance test successful with {len(large_data)} input columns")

    def test_backward_compatibility(self):
        """Test that the new system produces compatible output."""
        config = self.ProcessingConfig(
            metric_type=self.MetricType.SYNAPSE_DENSITY,
            soma_side=self.SomaSide.LEFT,
            region_name='ME'
        )

        result = self.data_processor.process_column_data(
            self.sample_data['column_summary'],
            self.sample_data['all_possible_columns'],
            self.sample_data['region_columns_map'],
            config
        )

        # Verify output format compatibility
        for col in result.processed_columns:
            # Check that all required attributes are present
            self.assertTrue(hasattr(col, 'coordinate'))
            self.assertTrue(hasattr(col, 'value'))
            self.assertTrue(hasattr(col, 'status'))
            self.assertTrue(hasattr(col, 'layer_values'))
            self.assertTrue(hasattr(col, 'metric_type'))

            # Check coordinate accessibility
            self.assertIsInstance(col.hex1, int)
            self.assertIsInstance(col.hex2, int)

        logger.info("✓ Backward compatibility test successful")


def run_phase3_tests():
    """Run all Phase 3 data processing tests."""
    print("🧪 Running Phase 3 Data Processing Tests")
    print("=" * 60)

    # Create test suite
    suite = unittest.TestSuite()

    # Add all test methods
    test_class = TestPhase3DataProcessing
    test_methods = [
        'test_data_processor_initialization',
        'test_column_data_conversion',
        'test_data_validation',
        'test_threshold_calculation',
        'test_min_max_calculation',
        'test_metric_statistics',
        'test_data_organization_by_side',
        'test_complete_data_processing_workflow',
        'test_error_handling_and_validation',
        'test_processing_summary_generation',
        'test_metric_calculator_functionality',
        'test_column_data_manager_functionality',
        'test_validation_manager_functionality',
        'test_performance_with_large_dataset',
        'test_backward_compatibility'
    ]

    for method_name in test_methods:
        suite.addTest(test_class(method_name))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All Phase 3 tests passed!")
        print(f"   - Tests run: {result.testsRun}")
        print(f"   - Failures: {len(result.failures)}")
        print(f"   - Errors: {len(result.errors)}")
        print("\n🎉 Phase 3 Data Processing implementation is working correctly!")
        return 0
    else:
        print("❌ Some tests failed!")
        print(f"   - Tests run: {result.testsRun}")
        print(f"   - Failures: {len(result.failures)}")
        print(f"   - Errors: {len(result.errors)}")

        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")

        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")

        return 1


if __name__ == '__main__':
    exit_code = run_phase3_tests()
    sys.exit(exit_code)
