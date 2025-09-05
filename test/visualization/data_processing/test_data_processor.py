#!/usr/bin/env python3
"""
Modernized Data Processor Test Suite

This file replaces the legacy test suite with a comprehensive, modern testing
framework that tests only the current API and data structures.

Legacy methods that have been removed:
- calculate_thresholds_for_data
- calculate_min_max_for_data
- extract_metric_statistics
- validate_input_data
- _convert_summary_to_column_data

Modern methods being tested:
- process_column_data (main processing method)
- get_processing_summary (summary generation)
"""

import sys
import unittest
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from quickpage.visualization.data_processing.data_processor import DataProcessor
from quickpage.visualization.data_processing.data_adapter import DataAdapter
from quickpage.visualization.data_processing.data_structures import (
    ProcessingConfig,
    MetricType,
    SomaSide,
    DataProcessingResult,
    ProcessedColumn,
)


class TestDataProcessor(unittest.TestCase):
    """Test the modernized DataProcessor class."""

    def setUp(self):
        """Set up test fixtures with modern structured data format."""
        self.processor = DataProcessor()
        self.adapter = DataAdapter()

        # Modern structured column data (new format only)
        self.sample_column_summary = [
            {
                "region": "ME",
                "side": "L",
                "hex1": 0,
                "hex2": 0,
                "total_synapses": 100,
                "neuron_count": 50,
                "layers": [
                    {
                        "layer_index": 1,
                        "synapse_count": 20,
                        "neuron_count": 10,
                        "value": 20.0,
                    },
                    {
                        "layer_index": 2,
                        "synapse_count": 30,
                        "neuron_count": 15,
                        "value": 30.0,
                    },
                    {
                        "layer_index": 3,
                        "synapse_count": 25,
                        "neuron_count": 12,
                        "value": 25.0,
                    },
                    {
                        "layer_index": 4,
                        "synapse_count": 25,
                        "neuron_count": 13,
                        "value": 25.0,
                    },
                ],
            },
            {
                "region": "ME",
                "side": "R",
                "hex1": 0,
                "hex2": 0,
                "total_synapses": 80,
                "neuron_count": 40,
                "layers": [
                    {
                        "layer_index": 1,
                        "synapse_count": 15,
                        "neuron_count": 8,
                        "value": 15.0,
                    },
                    {
                        "layer_index": 2,
                        "synapse_count": 25,
                        "neuron_count": 12,
                        "value": 25.0,
                    },
                    {
                        "layer_index": 3,
                        "synapse_count": 20,
                        "neuron_count": 10,
                        "value": 20.0,
                    },
                    {
                        "layer_index": 4,
                        "synapse_count": 20,
                        "neuron_count": 10,
                        "value": 20.0,
                    },
                ],
            },
            {
                "region": "LO",
                "side": "L",
                "hex1": 1,
                "hex2": 0,
                "total_synapses": 120,
                "neuron_count": 60,
                "layers": [
                    {
                        "layer_index": 1,
                        "synapse_count": 25,
                        "neuron_count": 12,
                        "value": 25.0,
                    },
                    {
                        "layer_index": 2,
                        "synapse_count": 35,
                        "neuron_count": 18,
                        "value": 35.0,
                    },
                    {
                        "layer_index": 3,
                        "synapse_count": 30,
                        "neuron_count": 15,
                        "value": 30.0,
                    },
                    {
                        "layer_index": 4,
                        "synapse_count": 30,
                        "neuron_count": 15,
                        "value": 30.0,
                    },
                ],
            },
        ]

        # Sample all possible columns
        self.sample_all_columns = [
            {"hex1": 0, "hex2": 0, "region": "ME"},
            {"hex1": 1, "hex2": 0, "region": "LO"},
            {"hex1": 0, "hex2": 1, "region": "ME"},
            {"hex1": 1, "hex2": 1, "region": "LOP"},
        ]

        # Sample region columns map
        self.sample_region_map = {
            "ME_L": {(0, 0), (0, 1)},
            "ME_R": {(0, 0), (0, 1)},
            "LO_L": {(1, 0)},
            "LO_R": {(1, 0)},
            "LOP_L": {(1, 1)},
            "LOP_R": {(1, 1)},
        }

        # Modern processing config
        self.sample_config = ProcessingConfig(
            metric_type=MetricType.SYNAPSE_DENSITY,
            soma_side=SomaSide.LEFT,
            region_name="ME",
            neuron_type="test_neuron",
            output_format="svg",
        )

    def test_initialization(self):
        """Test DataProcessor initialization."""
        processor = DataProcessor()
        self.assertIsInstance(processor, DataProcessor)

        # Test strict validation mode
        strict_processor = DataProcessor(strict_validation=True)
        self.assertIsInstance(strict_processor, DataProcessor)

    def test_process_column_data_success(self):
        """Test successful column data processing with modern API."""
        # Convert raw data to ColumnData objects using modern format
        column_data = self.adapter.normalize_input(self.sample_column_summary)

        # Process using modern API
        result = self.processor.process_column_data(
            column_data=column_data,
            all_possible_columns=self.sample_all_columns,
            region_columns_map=self.sample_region_map,
            config=self.sample_config,
        )

        self.assertIsInstance(result, DataProcessingResult)
        self.assertTrue(result.is_successful)
        self.assertGreater(result.column_count, 0)

    def test_process_column_data_with_invalid_config(self):
        """Test processing with invalid configuration."""
        column_data = self.adapter.normalize_input(self.sample_column_summary)

        # Test with invalid config - empty region name should fail
        try:
            invalid_config = ProcessingConfig(
                metric_type=MetricType.SYNAPSE_DENSITY,
                soma_side=SomaSide.LEFT,
                region_name="",  # This should trigger validation error
                neuron_type="test_neuron",
                output_format="svg",
            )

            result = self.processor.process_column_data(
                column_data=column_data,
                all_possible_columns=self.sample_all_columns,
                region_columns_map=self.sample_region_map,
                config=invalid_config,
            )

            # If we get here, the result should indicate failure
            self.assertFalse(result.is_successful)

        except ValueError:
            # Config validation caught the error at creation time - this is expected
            pass

    def test_process_column_data_combined_sides(self):
        """Test processing with combined sides."""
        column_data = self.adapter.normalize_input(self.sample_column_summary)

        combined_config = ProcessingConfig(
            metric_type=MetricType.SYNAPSE_DENSITY,
            soma_side=SomaSide.COMBINED,
            region_name="ME",
            neuron_type="test_neuron",
            output_format="svg",
        )

        result = self.processor.process_column_data(
            column_data=column_data,
            all_possible_columns=self.sample_all_columns,
            region_columns_map=self.sample_region_map,
            config=combined_config,
        )

        self.assertIsInstance(result, DataProcessingResult)
        self.assertTrue(result.is_successful)

    def test_process_column_data_with_thresholds(self):
        """Test processing with custom thresholds."""
        column_data = self.adapter.normalize_input(self.sample_column_summary)

        custom_thresholds = {"min_value": 0.0, "max_value": 50.0, "threshold_count": 5}

        result = self.processor.process_column_data(
            column_data=column_data,
            all_possible_columns=self.sample_all_columns,
            region_columns_map=self.sample_region_map,
            config=self.sample_config,
            thresholds=custom_thresholds,
        )

        self.assertIsInstance(result, DataProcessingResult)

    def test_process_column_data_with_min_max_data(self):
        """Test processing with min/max data."""
        column_data = self.adapter.normalize_input(self.sample_column_summary)

        min_max_data = {
            "global_min": 0.0,
            "global_max": 100.0,
            "layer_mins": [5.0, 10.0, 8.0, 10.0],
            "layer_maxs": [30.0, 35.0, 30.0, 30.0],
        }

        result = self.processor.process_column_data(
            column_data=column_data,
            all_possible_columns=self.sample_all_columns,
            region_columns_map=self.sample_region_map,
            config=self.sample_config,
            min_max_data=min_max_data,
        )

        self.assertIsInstance(result, DataProcessingResult)

    def test_get_processing_summary(self):
        """Test processing summary generation."""
        column_data = self.adapter.normalize_input(self.sample_column_summary)

        result = self.processor.process_column_data(
            column_data=column_data,
            all_possible_columns=self.sample_all_columns,
            region_columns_map=self.sample_region_map,
            config=self.sample_config,
        )

        summary = self.processor.get_processing_summary(result)

        self.assertIsInstance(summary, dict)
        self.assertIn("success", summary)
        self.assertIn("total_columns", summary)
        self.assertIn("validation", summary)
        self.assertIn("status_distribution", summary)

    def test_filter_columns_for_side(self):
        """Test filtering columns for specific side."""
        column_data = self.adapter.normalize_input(self.sample_column_summary)

        # Test with LEFT side
        left_config = ProcessingConfig(
            metric_type=MetricType.SYNAPSE_DENSITY,
            soma_side=SomaSide.LEFT,
            region_name="ME",
            neuron_type="test_neuron",
            output_format="svg",
        )

        result = self.processor.process_column_data(
            column_data=column_data,
            all_possible_columns=self.sample_all_columns,
            region_columns_map=self.sample_region_map,
            config=left_config,
        )

        self.assertTrue(result.is_successful)

    def test_empty_input_data(self):
        """Test processing with empty input data."""
        empty_column_data = []

        result = self.processor.process_column_data(
            column_data=empty_column_data,
            all_possible_columns=self.sample_all_columns,
            region_columns_map=self.sample_region_map,
            config=self.sample_config,
        )

        self.assertIsInstance(result, DataProcessingResult)
        self.assertEqual(result.column_count, 0)

    def test_different_metric_types(self):
        """Test processing with different metric types."""
        column_data = self.adapter.normalize_input(self.sample_column_summary)

        metric_types = [MetricType.SYNAPSE_DENSITY, MetricType.CELL_COUNT]

        for metric_type in metric_types:
            with self.subTest(metric_type=metric_type):
                config = ProcessingConfig(
                    metric_type=metric_type,
                    soma_side=SomaSide.LEFT,
                    region_name="ME",
                    neuron_type="test_neuron",
                    output_format="svg",
                )

                result = self.processor.process_column_data(
                    column_data=column_data,
                    all_possible_columns=self.sample_all_columns,
                    region_columns_map=self.sample_region_map,
                    config=config,
                )

                self.assertTrue(result.is_successful)

    def test_different_soma_sides(self):
        """Test processing with different soma sides."""
        column_data = self.adapter.normalize_input(self.sample_column_summary)

        soma_sides = [SomaSide.LEFT, SomaSide.RIGHT, SomaSide.COMBINED]

        for soma_side in soma_sides:
            with self.subTest(soma_side=soma_side):
                config = ProcessingConfig(
                    metric_type=MetricType.SYNAPSE_DENSITY,
                    soma_side=soma_side,
                    region_name="ME",
                    neuron_type="test_neuron",
                    output_format="svg",
                )

                result = self.processor.process_column_data(
                    column_data=column_data,
                    all_possible_columns=self.sample_all_columns,
                    region_columns_map=self.sample_region_map,
                    config=config,
                )

                self.assertTrue(result.is_successful)

    def test_processor_reusability(self):
        """Test that processor can be reused for multiple operations."""
        column_data = self.adapter.normalize_input(self.sample_column_summary)

        # Process multiple times with same processor
        for i in range(3):
            result = self.processor.process_column_data(
                column_data=column_data,
                all_possible_columns=self.sample_all_columns,
                region_columns_map=self.sample_region_map,
                config=self.sample_config,
            )

            self.assertTrue(result.is_successful)

    def test_large_dataset_processing(self):
        """Test processing with a larger dataset."""
        # Create larger dataset
        large_dataset = []

        regions = ["ME", "LO", "LOP"]
        sides = ["L", "R"]

        for region in regions:
            for side in sides:
                for i in range(10):  # 10 columns per region/side combination
                    column = {
                        "region": region,
                        "side": side,
                        "hex1": i % 3,
                        "hex2": i // 3,
                        "total_synapses": 100 + (i * 10),
                        "neuron_count": 50 + (i * 5),
                        "layers": [
                            {
                                "layer_index": 1,
                                "synapse_count": 20 + i,
                                "neuron_count": 10 + i,
                                "value": 20.0 + i,
                            },
                            {
                                "layer_index": 2,
                                "synapse_count": 30 + i,
                                "neuron_count": 15 + i,
                                "value": 30.0 + i,
                            },
                            {
                                "layer_index": 3,
                                "synapse_count": 25 + i,
                                "neuron_count": 12 + i,
                                "value": 25.0 + i,
                            },
                            {
                                "layer_index": 4,
                                "synapse_count": 25 + i,
                                "neuron_count": 13 + i,
                                "value": 25.0 + i,
                            },
                        ],
                    }
                    large_dataset.append(column)

        column_data = self.adapter.normalize_input(large_dataset)

        # Expand region map for larger dataset
        expanded_region_map = {
            "ME_L": {(i % 3, i // 3) for i in range(10)},
            "ME_R": {(i % 3, i // 3) for i in range(10)},
            "LO_L": {(i % 3, i // 3) for i in range(10)},
            "LO_R": {(i % 3, i // 3) for i in range(10)},
            "LOP_L": {(i % 3, i // 3) for i in range(10)},
            "LOP_R": {(i % 3, i // 3) for i in range(10)},
        }

        result = self.processor.process_column_data(
            column_data=column_data,
            all_possible_columns=self.sample_all_columns,
            region_columns_map=expanded_region_map,
            config=self.sample_config,
        )

        self.assertTrue(result.is_successful)
        self.assertEqual(len(column_data), 60)  # 3 regions * 2 sides * 10 columns

    def test_structured_data_integrity(self):
        """Test that structured data maintains integrity through processing."""
        column_data = self.adapter.normalize_input(self.sample_column_summary)

        result = self.processor.process_column_data(
            column_data=column_data,
            all_possible_columns=self.sample_all_columns,
            region_columns_map=self.sample_region_map,
            config=self.sample_config,
        )

        self.assertTrue(result.is_successful)

        # Verify that processed columns maintain layer structure
        for processed_column in result.processed_columns:
            self.assertIsInstance(processed_column, ProcessedColumn)
            if processed_column.layer_values:
                # Verify layer data consistency
                self.assertGreater(len(processed_column.layer_values), 0)

                # Verify layer colors correspond to layer values
                layer_values = processed_column.layer_values
                layer_colors = processed_column.layer_colors

                self.assertEqual(len(layer_values), len(layer_colors))
                self.assertTrue(all(isinstance(v, (int, float)) for v in layer_values))

    def test_deprecated_methods_are_removed(self):
        """Test that deprecated methods have been properly removed."""
        deprecated_methods = [
            "calculate_thresholds_for_data",
            "calculate_min_max_for_data",
            "extract_metric_statistics",
            "validate_input_data",
            "_convert_summary_to_column_data",
        ]

        for method_name in deprecated_methods:
            with self.subTest(method=method_name):
                self.assertFalse(
                    hasattr(self.processor, method_name),
                    f"Deprecated method {method_name} still exists",
                )

    def test_modern_api_methods_available(self):
        """Test that modern API methods are available and callable."""
        modern_methods = ["process_column_data", "get_processing_summary"]

        for method_name in modern_methods:
            with self.subTest(method=method_name):
                self.assertTrue(
                    hasattr(self.processor, method_name),
                    f"Modern method {method_name} not available",
                )
                method = getattr(self.processor, method_name)
                self.assertTrue(
                    callable(method), f"Modern method {method_name} is not callable"
                )


if __name__ == "__main__":
    unittest.main()
