"""
Tests for Data Processor Module

This module contains comprehensive unit tests for the DataProcessor class,
which is the main orchestrator for data processing operations in the
hexagon grid generator.
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Set, Tuple

# Add the source directory to the path for testing
test_dir = Path(__file__).parent
project_root = test_dir.parent.parent.parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

from quickpage.visualization.data_processing.data_processor import DataProcessor
from quickpage.visualization.data_processing.data_structures import (
    ColumnData, ColumnCoordinate, MetricType, SomaSide, ProcessingConfig,
    ValidationResult, DataProcessingResult, ThresholdData, MinMaxData,
    ColumnStatus, LayerData
)


class TestDataProcessor(unittest.TestCase):
    """Test cases for DataProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = DataProcessor()

        # Sample column summary data
        self.sample_column_summary = [
            {
                'region': 'ME',
                'side': 'L',
                'hex1': 0,
                'hex2': 0,
                'total_synapses': 100,
                'neuron_count': 50,
                'layers': [
                    {'layer_index': 1, 'synapse_count': 20, 'neuron_count': 10, 'value': 20.0},
                    {'layer_index': 2, 'synapse_count': 30, 'neuron_count': 15, 'value': 30.0},
                    {'layer_index': 3, 'synapse_count': 25, 'neuron_count': 12, 'value': 25.0},
                    {'layer_index': 4, 'synapse_count': 25, 'neuron_count': 13, 'value': 25.0}
                ]
            },
            {
                'region': 'ME',
                'side': 'R',
                'hex1': 0,
                'hex2': 0,
                'total_synapses': 80,
                'neuron_count': 40,
                'layers': [
                    {'layer_index': 1, 'synapse_count': 15, 'neuron_count': 8, 'value': 15.0},
                    {'layer_index': 2, 'synapse_count': 25, 'neuron_count': 12, 'value': 25.0},
                    {'layer_index': 3, 'synapse_count': 20, 'neuron_count': 10, 'value': 20.0},
                    {'layer_index': 4, 'synapse_count': 20, 'neuron_count': 10, 'value': 20.0}
                ]
            },
            {
                'region': 'LO',
                'side': 'L',
                'hex1': 1,
                'hex2': 0,
                'total_synapses': 120,
                'neuron_count': 60,
                'layers': [
                    {'layer_index': 1, 'synapse_count': 25, 'neuron_count': 12, 'value': 25.0},
                    {'layer_index': 2, 'synapse_count': 35, 'neuron_count': 18, 'value': 35.0},
                    {'layer_index': 3, 'synapse_count': 30, 'neuron_count': 15, 'value': 30.0},
                    {'layer_index': 4, 'synapse_count': 30, 'neuron_count': 15, 'value': 30.0}
                ]
            }
        ]

        # Sample all possible columns
        self.sample_all_columns = [
            {'hex1': 0, 'hex2': 0, 'region': 'ME'},
            {'hex1': 1, 'hex2': 0, 'region': 'LO'},
            {'hex1': 0, 'hex2': 1, 'region': 'ME'},
            {'hex1': 1, 'hex2': 1, 'region': 'LOP'}
        ]

        # Sample region columns map
        self.sample_region_map = {
            'ME_L': {(0, 0), (0, 1)},
            'ME_R': {(0, 0), (0, 1)},
            'LO_L': {(1, 0)},
            'LO_R': {(1, 0)},
            'LOP_L': {(1, 1)},
            'LOP_R': {(1, 1)}
        }

        # Sample processing config
        self.sample_config = ProcessingConfig(
            metric_type=MetricType.SYNAPSE_DENSITY,
            soma_side=SomaSide.LEFT,
            region_name='ME',
            neuron_type='test_neuron',
            output_format='svg'
        )

    def test_initialization(self):
        """Test DataProcessor initialization."""
        processor = DataProcessor()
        self.assertIsNotNone(processor.validation_manager)
        self.assertIsNotNone(processor.threshold_calculator)
        self.assertIsNotNone(processor.metric_calculator)
        self.assertIsNotNone(processor.column_data_manager)

        # Test with strict validation disabled
        processor_lenient = DataProcessor(strict_validation=False)
        self.assertFalse(processor_lenient.validation_manager.strict_mode)

    def test_process_column_data_success(self):
        """Test successful column data processing."""
        result = self.processor.process_column_data(
            self.sample_column_summary,
            self.sample_all_columns,
            self.sample_region_map,
            self.sample_config
        )

        self.assertIsInstance(result, DataProcessingResult)
        self.assertTrue(result.is_successful)
        self.assertGreater(len(result.processed_columns), 0)
        self.assertTrue(result.validation_result.is_valid)

    def test_process_column_data_with_invalid_config(self):
        """Test processing with invalid configuration."""
        invalid_config = ProcessingConfig(
            metric_type=MetricType.SYNAPSE_DENSITY,
            soma_side=SomaSide.LEFT,
            region_name='',  # Invalid empty region
            output_format='invalid_format'  # Invalid format
        )

        result = self.processor.process_column_data(
            self.sample_column_summary,
            self.sample_all_columns,
            self.sample_region_map,
            invalid_config
        )

        self.assertFalse(result.is_successful)
        self.assertFalse(result.validation_result.is_valid)
        self.assertGreater(len(result.validation_result.errors), 0)

    def test_process_column_data_combined_sides(self):
        """Test processing with combined sides."""
        combined_config = ProcessingConfig(
            metric_type=MetricType.CELL_COUNT,
            soma_side=SomaSide.COMBINED,
            region_name='ME'
        )

        result = self.processor.process_column_data(
            self.sample_column_summary,
            self.sample_all_columns,
            self.sample_region_map,
            combined_config
        )

        self.assertTrue(result.is_successful)
        self.assertGreater(len(result.processed_columns), 0)

        # Should have processed both L and R sides
        sides_processed = result.metadata.get('processed_sides', [])
        self.assertIn('L', sides_processed)
        self.assertIn('R', sides_processed)

    def test_process_column_data_with_thresholds(self):
        """Test processing with provided thresholds."""
        thresholds = {'all': [0, 25, 50, 75, 100]}

        result = self.processor.process_column_data(
            self.sample_column_summary,
            self.sample_all_columns,
            self.sample_region_map,
            self.sample_config,
            thresholds=thresholds
        )

        self.assertTrue(result.is_successful)
        # Should use provided thresholds rather than calculating new ones
        self.assertIsNone(result.threshold_data)

    def test_process_column_data_with_min_max_data(self):
        """Test processing with provided min/max data."""
        min_max_data = {
            'min_syn_region': {'ME': 0, 'LO': 5},
            'max_syn_region': {'ME': 200, 'LO': 150}
        }

        result = self.processor.process_column_data(
            self.sample_column_summary,
            self.sample_all_columns,
            self.sample_region_map,
            self.sample_config,
            min_max_data=min_max_data
        )

        self.assertTrue(result.is_successful)
        # Should use provided min/max data rather than calculating new ones
        self.assertIsNone(result.min_max_data)

    def test_calculate_thresholds_for_data(self):
        """Test threshold calculation for data."""
        thresholds = self.processor.calculate_thresholds_for_data(
            self.sample_column_summary,
            MetricType.SYNAPSE_DENSITY
        )

        self.assertIsInstance(thresholds, ThresholdData)
        self.assertGreater(len(thresholds.all_layers), 0)
        self.assertLessEqual(thresholds.min_value, thresholds.max_value)

    def test_calculate_thresholds_different_methods(self):
        """Test threshold calculation with different methods."""
        methods = ['percentile', 'quantile', 'equal', 'std_dev']

        for method in methods:
            with self.subTest(method=method):
                thresholds = self.processor.calculate_thresholds_for_data(
                    self.sample_column_summary,
                    MetricType.SYNAPSE_DENSITY,
                    method=method
                )

                self.assertIsInstance(thresholds, ThresholdData)
                self.assertGreater(len(thresholds.all_layers), 0)

    def test_calculate_min_max_for_data(self):
        """Test min/max calculation for data."""
        min_max_data = self.processor.calculate_min_max_for_data(
            self.sample_column_summary
        )

        self.assertIsInstance(min_max_data, MinMaxData)
        self.assertGreaterEqual(min_max_data.global_max_syn, min_max_data.global_min_syn)
        self.assertGreaterEqual(min_max_data.global_max_cells, min_max_data.global_min_cells)

    def test_calculate_min_max_for_specific_regions(self):
        """Test min/max calculation for specific regions."""
        regions = ['ME', 'LO']
        min_max_data = self.processor.calculate_min_max_for_data(
            self.sample_column_summary,
            regions=regions
        )

        self.assertIsInstance(min_max_data, MinMaxData)
        for region in regions:
            if region in min_max_data.min_syn_region:
                self.assertIn(region, min_max_data.max_syn_region)

    def test_extract_metric_statistics(self):
        """Test metric statistics extraction."""
        stats = self.processor.extract_metric_statistics(
            self.sample_column_summary,
            MetricType.SYNAPSE_DENSITY
        )

        self.assertIsInstance(stats, dict)
        expected_keys = ['count', 'mean', 'median', 'std', 'min', 'max']
        for key in expected_keys:
            self.assertIn(key, stats)
            self.assertIsInstance(stats[key], (int, float))

    def test_validate_input_data(self):
        """Test input data validation."""
        validation_result = self.processor.validate_input_data(
            self.sample_column_summary,
            self.sample_region_map
        )

        self.assertIsInstance(validation_result, ValidationResult)
        self.assertTrue(validation_result.is_valid)

    def test_validate_input_data_with_errors(self):
        """Test input data validation with errors."""
        # Create invalid data
        invalid_data = [
            {
                'region': '',  # Invalid empty region
                'side': 'INVALID',  # Invalid side
                'hex1': 'not_int',  # Invalid coordinate type
                'hex2': 0,
                'total_synapses': -10,  # Invalid negative count
                'neuron_count': 50
            }
        ]

        validation_result = self.processor.validate_input_data(
            invalid_data,
            self.sample_region_map
        )

        self.assertFalse(validation_result.is_valid)
        self.assertGreater(len(validation_result.errors), 0)

    def test_convert_summary_to_column_data(self):
        """Test conversion from summary to ColumnData objects."""
        column_data = self.processor._convert_summary_to_column_data(
            self.sample_column_summary
        )

        self.assertIsInstance(column_data, list)
        self.assertEqual(len(column_data), len(self.sample_column_summary))

        for col in column_data:
            self.assertIsInstance(col, ColumnData)
            self.assertIsInstance(col.coordinate, ColumnCoordinate)
            self.assertGreaterEqual(col.total_synapses, 0)
            self.assertGreaterEqual(col.neuron_count, 0)

    def test_determine_mirror_side(self):
        """Test mirror side determination."""
        test_cases = [
            (SomaSide.LEFT, 'L', 'left'),
            (SomaSide.LEFT, 'R', 'left'),
            (SomaSide.RIGHT, 'L', 'right'),
            (SomaSide.RIGHT, 'R', 'right'),
            (SomaSide.COMBINED, 'L', 'left'),
            (SomaSide.COMBINED, 'R', 'right'),
        ]

        for soma_side, current_side, expected in test_cases:
            with self.subTest(soma_side=soma_side, current_side=current_side):
                result = self.processor._determine_mirror_side(soma_side, current_side)
                self.assertEqual(result, expected)

    def test_filter_columns_for_side(self):
        """Test filtering columns for specific side."""
        filtered = self.processor._filter_columns_for_side(
            self.sample_all_columns,
            self.sample_region_map,
            'ME',
            'L'
        )

        self.assertIsInstance(filtered, list)
        self.assertGreater(len(filtered), 0)

        # All filtered columns should have coordinates that exist in relevant regions
        for col in filtered:
            coord_tuple = (col['hex1'], col['hex2'])
            found_in_relevant_region = False

            # Check if coordinate exists in ME_L or other regions with L side
            for region_side, coords in self.sample_region_map.items():
                if region_side.endswith('_L') and coord_tuple in coords:
                    found_in_relevant_region = True
                    break

            self.assertTrue(found_in_relevant_region)

    def test_get_other_regions_coords(self):
        """Test getting coordinates from other regions."""
        other_coords = self.processor._get_other_regions_coords(
            self.sample_region_map,
            'ME',
            'L'
        )

        self.assertIsInstance(other_coords, set)

        # Should contain coordinates from LO_L and LOP_L but not ME_L
        expected_coords = self.sample_region_map['LO_L'] | self.sample_region_map['LOP_L']
        self.assertEqual(other_coords, expected_coords)

    def test_process_side_data(self):
        """Test processing data for a specific side."""
        # Prepare test data
        side_columns = [{'hex1': 0, 'hex2': 0, 'region': 'ME'}]
        region_coords = {(0, 0)}
        data_map = {
            ('ME', 0, 0): self.processor._convert_summary_to_column_data([self.sample_column_summary[0]])[0]
        }
        other_coords = {(1, 0), (1, 1)}

        result = self.processor._process_side_data(
            side_columns,
            region_coords,
            data_map,
            self.sample_config,
            other_coords,
            None,
            None,
            'left'
        )

        self.assertIsInstance(result, DataProcessingResult)
        self.assertTrue(result.validation_result.is_valid)
        self.assertGreater(len(result.processed_columns), 0)

        # Check processed column properties
        processed_col = result.processed_columns[0]
        self.assertEqual(processed_col.status, ColumnStatus.HAS_DATA)
        self.assertEqual(processed_col.region, 'ME')
        self.assertGreater(processed_col.value, 0)

    def test_get_processing_summary(self):
        """Test getting processing summary."""
        # Create a sample result
        result = self.processor.process_column_data(
            self.sample_column_summary,
            self.sample_all_columns,
            self.sample_region_map,
            self.sample_config
        )

        summary = self.processor.get_processing_summary(result)

        self.assertIsInstance(summary, dict)
        self.assertIn('success', summary)
        self.assertIn('total_columns', summary)
        self.assertIn('validation', summary)
        self.assertIn('status_distribution', summary)

        # Check validation summary
        validation = summary['validation']
        self.assertIn('is_valid', validation)
        self.assertIn('error_count', validation)
        self.assertIn('warning_count', validation)

        # Check status distribution
        status_dist = summary['status_distribution']
        self.assertIsInstance(status_dist, dict)

    def test_empty_input_data(self):
        """Test processing with empty input data."""
        result = self.processor.process_column_data(
            [],  # Empty column summary
            [],  # Empty all columns
            {},  # Empty region map
            self.sample_config
        )

        self.assertIsInstance(result, DataProcessingResult)
        self.assertEqual(len(result.processed_columns), 0)

    def test_malformed_input_data(self):
        """Test processing with malformed input data."""
        malformed_data = [
            {'invalid': 'data'},  # Missing required fields
            {'region': 'ME', 'side': 'L'},  # Missing coordinates
        ]

        result = self.processor.process_column_data(
            malformed_data,
            self.sample_all_columns,
            self.sample_region_map,
            self.sample_config
        )

        # Should handle errors gracefully
        self.assertIsInstance(result, DataProcessingResult)

    @patch('quickpage.visualization.data_processing.data_processor.logger')
    def test_exception_handling(self, mock_logger):
        """Test exception handling in data processing."""
        # Mock threshold calculator to raise an exception
        with patch.object(self.processor.threshold_calculator, 'calculate_thresholds') as mock_calc:
            mock_calc.side_effect = Exception("Test exception")

            result = self.processor.process_column_data(
                self.sample_column_summary,
                self.sample_all_columns,
                self.sample_region_map,
                self.sample_config
            )

            # Should still return a valid result but with warnings
            self.assertIsInstance(result, DataProcessingResult)
            mock_logger.warning.assert_called()

    def test_different_metric_types(self):
        """Test processing with different metric types."""
        metric_types = [MetricType.SYNAPSE_DENSITY, MetricType.CELL_COUNT]

        for metric_type in metric_types:
            with self.subTest(metric_type=metric_type):
                config = ProcessingConfig(
                    metric_type=metric_type,
                    soma_side=SomaSide.LEFT,
                    region_name='ME'
                )

                result = self.processor.process_column_data(
                    self.sample_column_summary,
                    self.sample_all_columns,
                    self.sample_region_map,
                    config
                )

                self.assertTrue(result.is_successful)

                # Check that processed columns have correct metric type
                for col in result.processed_columns:
                    self.assertEqual(col.metric_type, metric_type)

    def test_different_soma_sides(self):
        """Test processing with different soma sides."""
        soma_sides = [SomaSide.LEFT, SomaSide.RIGHT, SomaSide.COMBINED]

        for soma_side in soma_sides:
            with self.subTest(soma_side=soma_side):
                config = ProcessingConfig(
                    metric_type=MetricType.SYNAPSE_DENSITY,
                    soma_side=soma_side,
                    region_name='ME'
                )

                result = self.processor.process_column_data(
                    self.sample_column_summary,
                    self.sample_all_columns,
                    self.sample_region_map,
                    config
                )

                self.assertTrue(result.is_successful)

    def test_processor_reusability(self):
        """Test that processor can be reused for multiple operations."""
        # Process data multiple times with same processor
        for i in range(3):
            with self.subTest(iteration=i):
                result = self.processor.process_column_data(
                    self.sample_column_summary,
                    self.sample_all_columns,
                    self.sample_region_map,
                    self.sample_config
                )

                self.assertTrue(result.is_successful)
                self.assertGreater(len(result.processed_columns), 0)

    def test_large_dataset_processing(self):
        """Test processing with a larger dataset."""
        # Generate larger dataset
        large_summary = []
        large_all_columns = []
        large_region_map = {}

        regions = ['ME', 'LO', 'LOP']
        sides = ['L', 'R']

        for region in regions:
            for side in sides:
                coords = set()
                for hex1 in range(5):
                    for hex2 in range(5):
                        # Add column data
                        layer_value = (hex1 + 1) * (hex2 + 1) * 2
                        neuron_value = (hex1 + 1) * (hex2 + 1)
                        large_summary.append({
                            'region': region,
                            'side': side,
                            'hex1': hex1,
                            'hex2': hex2,
                            'total_synapses': (hex1 + 1) * (hex2 + 1) * 10,
                            'neuron_count': (hex1 + 1) * (hex2 + 1) * 5,
                            'layers': [
                                {'layer_index': i + 1, 'synapse_count': layer_value, 'neuron_count': neuron_value, 'value': float(layer_value)}
                                for i in range(4)
                            ]
                        })

                        # Add to all columns (once per coordinate)
                        if side == 'L':  # Only add once per coordinate
                            large_all_columns.append({
                                'hex1': hex1,
                                'hex2': hex2,
                                'region': region
                            })

                        coords.add((hex1, hex2))

                large_region_map[f"{region}_{side}"] = coords

        result = self.processor.process_column_data(
            large_summary,
            large_all_columns,
            large_region_map,
            self.sample_config
        )

        self.assertTrue(result.is_successful)
        self.assertGreater(len(result.processed_columns), 0)

        # Verify processing was efficient (no timeout or excessive memory usage)
        summary = self.processor.get_processing_summary(result)
        self.assertGreater(summary['total_columns'], 20)  # Should have many columns


if __name__ == '__main__':
    unittest.main()
