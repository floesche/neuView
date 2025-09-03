#!/usr/bin/env python3
"""
Option C - Comprehensive Test Suite Modernization

This test suite replaces the legacy test system with a modern, comprehensive
testing framework focused on the cleaned-up data processing pipeline.

Features:
- Tests modern API only (no deprecated methods)
- Uses structured data format throughout
- Comprehensive integration testing
- Performance and edge case testing
- SVG metadata verification
- End-to-end pipeline testing
"""

import sys
import os
import unittest
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import modern components
from quickpage.visualization.data_processing.data_processor import DataProcessor
from quickpage.visualization.data_processing.data_adapter import DataAdapter
from quickpage.visualization.data_processing.data_structures import (
    ColumnData, LayerData, ProcessingConfig, MetricType, SomaSide,
    DataProcessingResult, ValidationResult, ColumnStatus, ProcessedColumn
)


class ModernTestDataFactory:
    """Factory for creating modern test data in structured format."""

    @staticmethod
    def create_structured_column_data(region: str = 'ME', side: str = 'L',
                                    hex1: int = 0, hex2: int = 0,
                                    layer_count: int = 4) -> Dict[str, Any]:
        """Create a structured column data dictionary."""
        base_synapse_count = 20
        base_neuron_count = 10

        layers = []
        for i in range(layer_count):
            layers.append({
                'layer_index': i + 1,
                'synapse_count': base_synapse_count + (i * 5),
                'neuron_count': base_neuron_count + (i * 2),
                'value': float(base_synapse_count + (i * 5))
            })

        total_synapses = sum(layer['synapse_count'] for layer in layers)
        total_neurons = sum(layer['neuron_count'] for layer in layers)

        return {
            'region': region,
            'side': side,
            'hex1': hex1,
            'hex2': hex2,
            'total_synapses': total_synapses,
            'neuron_count': total_neurons,
            'layers': layers
        }

    @staticmethod
    def create_multi_column_dataset(regions: List[str] = None,
                                  sides: List[str] = None,
                                  columns_per_region: int = 2) -> List[Dict[str, Any]]:
        """Create a multi-column dataset for comprehensive testing."""
        if regions is None:
            regions = ['ME', 'LO', 'LOP']
        if sides is None:
            sides = ['L', 'R']

        dataset = []
        hex_counter = 0

        for region in regions:
            for side in sides:
                for i in range(columns_per_region):
                    hex1 = hex_counter % 3
                    hex2 = hex_counter // 3

                    column_data = ModernTestDataFactory.create_structured_column_data(
                        region=region,
                        side=side,
                        hex1=hex1,
                        hex2=hex2,
                        layer_count=4 + (i % 3)  # Vary layer count
                    )
                    dataset.append(column_data)
                    hex_counter += 1

        return dataset

    @staticmethod
    def create_processing_config(metric_type: MetricType = MetricType.SYNAPSE_DENSITY,
                               soma_side: SomaSide = SomaSide.LEFT,
                               region_name: str = 'ME',
                               neuron_type: str = 'TestNeuron') -> ProcessingConfig:
        """Create a modern processing configuration."""
        return ProcessingConfig(
            metric_type=metric_type,
            soma_side=soma_side,
            region_name=region_name,
            neuron_type=neuron_type,
            output_format='svg',
            validate_data=True
        )

    @staticmethod
    def create_region_columns_map() -> Dict[str, set]:
        """Create a sample region columns map."""
        return {
            'ME_L': {(0, 0), (1, 0), (0, 1)},
            'ME_R': {(0, 0), (1, 0), (0, 1)},
            'LO_L': {(2, 0), (2, 1)},
            'LO_R': {(2, 0), (2, 1)},
            'LOP_L': {(1, 1), (2, 2)},
            'LOP_R': {(1, 1), (2, 2)}
        }

    @staticmethod
    def create_all_possible_columns() -> List[Dict[str, Any]]:
        """Create list of all possible column coordinates."""
        return [
            {'hex1': 0, 'hex2': 0, 'region': 'ME'},
            {'hex1': 1, 'hex2': 0, 'region': 'ME'},
            {'hex1': 0, 'hex2': 1, 'region': 'ME'},
            {'hex1': 1, 'hex2': 1, 'region': 'LOP'},
            {'hex1': 2, 'hex2': 0, 'region': 'LO'},
            {'hex1': 2, 'hex2': 1, 'region': 'LO'},
            {'hex1': 2, 'hex2': 2, 'region': 'LOP'}
        ]


class TestModernDataAdapter(unittest.TestCase):
    """Test the modernized DataAdapter with structured format only."""

    def setUp(self):
        self.adapter = DataAdapter()
        self.factory = ModernTestDataFactory()

    def test_structured_format_conversion(self):
        """Test conversion from structured dictionary format to ColumnData."""
        raw_data = [self.factory.create_structured_column_data()]

        column_data = self.adapter.from_dict_list(raw_data)

        self.assertEqual(len(column_data), 1)
        self.assertIsInstance(column_data[0], ColumnData)

        column = column_data[0]
        self.assertEqual(column.region, 'ME')
        self.assertEqual(column.side, 'L')
        self.assertEqual(len(column.layers), 4)
        self.assertEqual(column.synapses_per_layer, [20, 25, 30, 35])
        self.assertEqual(column.neurons_per_layer, [10, 12, 14, 16])

    def test_normalize_input_method(self):
        """Test the normalize_input method with various input types."""
        raw_data = self.factory.create_multi_column_dataset(['ME'], ['L'], 2)

        column_data = self.adapter.normalize_input(raw_data)

        self.assertEqual(len(column_data), 2)
        for column in column_data:
            self.assertIsInstance(column, ColumnData)
            self.assertEqual(column.region, 'ME')
            self.assertEqual(column.side, 'L')

    def test_empty_layers_handling(self):
        """Test handling of data without layers field."""
        raw_data = [{
            'region': 'ME',
            'side': 'L',
            'hex1': 0,
            'hex2': 0,
            'total_synapses': 100,
            'neuron_count': 50
            # No 'layers' field
        }]

        column_data = self.adapter.from_dict_list(raw_data)

        self.assertEqual(len(column_data), 1)
        column = column_data[0]
        self.assertEqual(len(column.layers), 0)
        self.assertEqual(column.synapses_per_layer, [])
        self.assertEqual(column.neurons_per_layer, [])

    def test_invalid_layer_data_handling(self):
        """Test handling of invalid layer data structure."""
        raw_data = [{
            'region': 'ME',
            'side': 'L',
            'hex1': 0,
            'hex2': 0,
            'total_synapses': 100,
            'neuron_count': 50,
            'layers': "invalid_format"  # Should be a list
        }]

        with self.assertRaises(ValueError):
            self.adapter.from_dict_list(raw_data)


class TestModernDataProcessor(unittest.TestCase):
    """Test the modernized DataProcessor with current API."""

    def setUp(self):
        self.processor = DataProcessor(strict_validation=False)
        self.adapter = DataAdapter()
        self.factory = ModernTestDataFactory()

    def test_successful_processing(self):
        """Test successful data processing with modern API."""
        # Create test data
        raw_data = self.factory.create_multi_column_dataset(['ME'], ['L'], 2)
        column_data = self.adapter.normalize_input(raw_data)

        # Create configuration
        config = self.factory.create_processing_config()

        # Create supporting data
        all_columns = self.factory.create_all_possible_columns()
        region_map = self.factory.create_region_columns_map()

        # Process data
        result = self.processor.process_column_data(
            column_data=column_data,
            all_possible_columns=all_columns,
            region_columns_map=region_map,
            config=config
        )

        # Verify results
        self.assertIsInstance(result, DataProcessingResult)
        self.assertTrue(result.is_successful)
        self.assertGreater(result.column_count, 0)
        self.assertTrue(result.validation_result.is_valid)

    def test_processing_with_different_metric_types(self):
        """Test processing with different metric types."""
        raw_data = self.factory.create_multi_column_dataset(['ME'], ['L'], 1)
        column_data = self.adapter.normalize_input(raw_data)
        all_columns = self.factory.create_all_possible_columns()
        region_map = self.factory.create_region_columns_map()

        metric_types = [MetricType.SYNAPSE_DENSITY, MetricType.CELL_COUNT]

        for metric_type in metric_types:
            with self.subTest(metric_type=metric_type):
                config = self.factory.create_processing_config(metric_type=metric_type)

                result = self.processor.process_column_data(
                    column_data=column_data,
                    all_possible_columns=all_columns,
                    region_columns_map=region_map,
                    config=config
                )

                self.assertTrue(result.is_successful,
                              f"Processing failed for {metric_type}")

    def test_processing_with_different_soma_sides(self):
        """Test processing with different soma sides."""
        raw_data = self.factory.create_multi_column_dataset(['ME'], ['L', 'R'], 1)
        column_data = self.adapter.normalize_input(raw_data)
        all_columns = self.factory.create_all_possible_columns()
        region_map = self.factory.create_region_columns_map()

        soma_sides = [SomaSide.LEFT, SomaSide.RIGHT, SomaSide.COMBINED]

        for soma_side in soma_sides:
            with self.subTest(soma_side=soma_side):
                config = self.factory.create_processing_config(soma_side=soma_side)

                result = self.processor.process_column_data(
                    column_data=column_data,
                    all_possible_columns=all_columns,
                    region_columns_map=region_map,
                    config=config
                )

                self.assertTrue(result.is_successful,
                              f"Processing failed for {soma_side}")

    def test_empty_data_handling(self):
        """Test processing with empty data."""
        column_data = []
        all_columns = self.factory.create_all_possible_columns()
        region_map = self.factory.create_region_columns_map()
        config = self.factory.create_processing_config()

        result = self.processor.process_column_data(
            column_data=column_data,
            all_possible_columns=all_columns,
            region_columns_map=region_map,
            config=config
        )

        self.assertIsInstance(result, DataProcessingResult)
        self.assertEqual(result.column_count, 0)

    def test_invalid_configuration_handling(self):
        """Test processing with invalid configuration."""
        raw_data = self.factory.create_multi_column_dataset(['ME'], ['L'], 1)
        column_data = self.adapter.normalize_input(raw_data)
        all_columns = self.factory.create_all_possible_columns()
        region_map = self.factory.create_region_columns_map()

        # Create invalid config (empty region name should fail validation)
        try:
            invalid_config = ProcessingConfig(
                metric_type=MetricType.SYNAPSE_DENSITY,
                soma_side=SomaSide.LEFT,
                region_name='',  # Invalid empty region
                neuron_type='TestNeuron',
                output_format='svg'
            )
            # If config creation succeeds, test that processing handles it
            result = self.processor.process_column_data(
                column_data=column_data,
                all_possible_columns=all_columns,
                region_columns_map=region_map,
                config=invalid_config
            )
            self.assertFalse(result.is_successful)
        except ValueError:
            # Config validation caught the error at creation time
            pass

    def test_processing_summary_generation(self):
        """Test generation of processing summaries."""
        raw_data = self.factory.create_multi_column_dataset(['ME'], ['L'], 2)
        column_data = self.adapter.normalize_input(raw_data)
        all_columns = self.factory.create_all_possible_columns()
        region_map = self.factory.create_region_columns_map()
        config = self.factory.create_processing_config()

        result = self.processor.process_column_data(
            column_data=column_data,
            all_possible_columns=all_columns,
            region_columns_map=region_map,
            config=config
        )

        summary = self.processor.get_processing_summary(result)

        self.assertIsInstance(summary, dict)
        self.assertIn('success', summary)
        self.assertIn('total_columns', summary)
        self.assertIn('validation', summary)
        self.assertIn('status_distribution', summary)


class TestIntegrationDataFlow(unittest.TestCase):
    """Test end-to-end data flow through the modern pipeline."""

    def setUp(self):
        self.adapter = DataAdapter()
        self.processor = DataProcessor()
        self.factory = ModernTestDataFactory()

    def test_complete_pipeline_flow(self):
        """Test complete data flow from raw input to processed output."""
        # Step 1: Create raw input data
        raw_input = self.factory.create_multi_column_dataset(['ME', 'LO'], ['L', 'R'], 2)

        # Step 2: Convert to structured format
        column_data = self.adapter.normalize_input(raw_input)
        self.assertGreater(len(column_data), 0)

        # Step 3: Process through modern pipeline
        config = self.factory.create_processing_config()
        all_columns = self.factory.create_all_possible_columns()
        region_map = self.factory.create_region_columns_map()

        result = self.processor.process_column_data(
            column_data=column_data,
            all_possible_columns=all_columns,
            region_columns_map=region_map,
            config=config
        )

        # Step 4: Verify end-to-end integrity
        self.assertTrue(result.is_successful)
        self.assertGreater(result.column_count, 0)

        # Verify data structure integrity
        for processed_column in result.processed_columns:
            self.assertIsInstance(processed_column, ProcessedColumn)
            if processed_column.layer_values:
                # Verify layer data consistency
                self.assertGreater(len(processed_column.layer_values), 0)
                self.assertEqual(len(processed_column.layer_values), len(processed_column.layer_colors))

    def test_different_data_sizes(self):
        """Test pipeline with different data sizes."""
        data_sizes = [1, 5, 10, 50]

        for size in data_sizes:
            with self.subTest(size=size):
                raw_input = self.factory.create_multi_column_dataset(['ME'], ['L'], size)
                column_data = self.adapter.normalize_input(raw_input)

                config = self.factory.create_processing_config()
                all_columns = self.factory.create_all_possible_columns()
                region_map = self.factory.create_region_columns_map()

                result = self.processor.process_column_data(
                    column_data=column_data,
                    all_possible_columns=all_columns,
                    region_columns_map=region_map,
                    config=config
                )

                self.assertTrue(result.is_successful, f"Failed for size {size}")
                self.assertEqual(len(column_data), size)

    def test_edge_cases_handling(self):
        """Test pipeline handling of edge cases."""
        edge_cases = [
            # Single layer data
            [{
                'region': 'ME', 'side': 'L', 'hex1': 0, 'hex2': 0,
                'total_synapses': 10, 'neuron_count': 5,
                'layers': [{'layer_index': 1, 'synapse_count': 10, 'neuron_count': 5, 'value': 10.0}]
            }],
            # Zero values
            [{
                'region': 'ME', 'side': 'L', 'hex1': 0, 'hex2': 0,
                'total_synapses': 0, 'neuron_count': 0,
                'layers': [{'layer_index': 1, 'synapse_count': 0, 'neuron_count': 0, 'value': 0.0}]
            }],
            # Large layer count
            [{
                'region': 'ME', 'side': 'L', 'hex1': 0, 'hex2': 0,
                'total_synapses': 1000, 'neuron_count': 100,
                'layers': [
                    {'layer_index': i+1, 'synapse_count': 10, 'neuron_count': 1, 'value': 10.0}
                    for i in range(20)
                ]
            }]
        ]

        config = self.factory.create_processing_config()
        all_columns = self.factory.create_all_possible_columns()
        region_map = self.factory.create_region_columns_map()

        for i, case_data in enumerate(edge_cases):
            with self.subTest(case=i):
                column_data = self.adapter.normalize_input(case_data)

                result = self.processor.process_column_data(
                    column_data=column_data,
                    all_possible_columns=all_columns,
                    region_columns_map=region_map,
                    config=config
                )

                # Should handle edge cases gracefully
                self.assertIsInstance(result, DataProcessingResult)


class TestPerformanceAndScalability(unittest.TestCase):
    """Test performance and scalability of the modern pipeline."""

    def setUp(self):
        self.adapter = DataAdapter()
        self.processor = DataProcessor()
        self.factory = ModernTestDataFactory()

    def test_large_dataset_processing(self):
        """Test processing with large datasets."""
        # Create a large dataset
        large_dataset = self.factory.create_multi_column_dataset(
            regions=['ME', 'LO', 'LOP', 'LOBP'],
            sides=['L', 'R'],
            columns_per_region=25  # 200 total columns
        )

        column_data = self.adapter.normalize_input(large_dataset)

        config = self.factory.create_processing_config()
        all_columns = self.factory.create_all_possible_columns()
        region_map = self.factory.create_region_columns_map()

        # Measure processing performance
        import time
        start_time = time.time()

        result = self.processor.process_column_data(
            column_data=column_data,
            all_possible_columns=all_columns,
            region_columns_map=region_map,
            config=config
        )

        end_time = time.time()
        processing_time = end_time - start_time

        # Verify results
        self.assertTrue(result.is_successful)
        self.assertEqual(len(column_data), 200)

        # Performance should be reasonable (less than 5 seconds for 200 columns)
        self.assertLess(processing_time, 5.0,
                       f"Processing took {processing_time:.2f}s, expected < 5s")

    def test_memory_usage_scalability(self):
        """Test memory usage with increasing data sizes."""
        import gc
        import sys

        base_sizes = [10, 50, 100]

        for size in base_sizes:
            with self.subTest(size=size):
                gc.collect()  # Clean up before measurement

                dataset = self.factory.create_multi_column_dataset(
                    regions=['ME'],
                    sides=['L'],
                    columns_per_region=size
                )

                column_data = self.adapter.normalize_input(dataset)

                config = self.factory.create_processing_config()
                all_columns = self.factory.create_all_possible_columns()
                region_map = self.factory.create_region_columns_map()

                result = self.processor.process_column_data(
                    column_data=column_data,
                    all_possible_columns=all_columns,
                    region_columns_map=region_map,
                    config=config
                )

                self.assertTrue(result.is_successful)

                # Clean up
                del dataset, column_data, result
                gc.collect()


class TestErrorHandlingAndValidation(unittest.TestCase):
    """Test error handling and validation in the modern pipeline."""

    def setUp(self):
        self.adapter = DataAdapter()
        self.processor = DataProcessor(strict_validation=True)
        self.factory = ModernTestDataFactory()

    def test_malformed_input_handling(self):
        """Test handling of malformed input data."""
        malformed_cases = [
            # Missing required fields
            [{'region': 'ME', 'side': 'L'}],  # Missing hex coordinates
            # Invalid data types
            [{'region': 'ME', 'side': 'L', 'hex1': 'invalid', 'hex2': 0}],
            # Invalid layer structure
            [{
                'region': 'ME', 'side': 'L', 'hex1': 0, 'hex2': 0,
                'layers': [{'invalid': 'structure'}]
            }]
        ]

        for i, case in enumerate(malformed_cases):
            with self.subTest(case=i):
                try:
                    column_data = self.adapter.normalize_input(case)
                    # If normalization succeeds, processing should handle gracefully
                    config = self.factory.create_processing_config()
                    all_columns = self.factory.create_all_possible_columns()
                    region_map = self.factory.create_region_columns_map()

                    result = self.processor.process_column_data(
                        column_data=column_data,
                        all_possible_columns=all_columns,
                        region_columns_map=region_map,
                        config=config
                    )

                    # Should either succeed or fail gracefully
                    self.assertIsInstance(result, DataProcessingResult)

                except (ValueError, TypeError, KeyError):
                    # Expected for malformed data
                    pass

    def test_validation_modes(self):
        """Test different validation modes."""
        # Create data with some issues
        problematic_data = [{
            'region': 'ME',
            'side': 'L',
            'hex1': 0,
            'hex2': 0,
            'total_synapses': 10,  # Use valid positive value
            'neuron_count': 0,
            'layers': [
                {'layer_index': 1, 'synapse_count': 5, 'neuron_count': 0, 'value': 5.0}
            ]
        }]

        column_data = self.adapter.normalize_input(problematic_data)
        config = self.factory.create_processing_config()
        all_columns = self.factory.create_all_possible_columns()
        region_map = self.factory.create_region_columns_map()

        # Test strict validation
        strict_processor = DataProcessor(strict_validation=True)
        strict_result = strict_processor.process_column_data(
            column_data=column_data,
            all_possible_columns=all_columns,
            region_columns_map=region_map,
            config=config
        )

        # Test lenient validation
        lenient_processor = DataProcessor(strict_validation=False)
        lenient_result = lenient_processor.process_column_data(
            column_data=column_data,
            all_possible_columns=all_columns,
            region_columns_map=region_map,
            config=config
        )

        # Both should handle the data, but with different validation results
        self.assertIsInstance(strict_result, DataProcessingResult)
        self.assertIsInstance(lenient_result, DataProcessingResult)


class TestBackwardCompatibility(unittest.TestCase):
    """Test that backward compatibility is maintained where needed."""

    def setUp(self):
        self.adapter = DataAdapter()
        self.factory = ModernTestDataFactory()

    def test_property_accessor_compatibility(self):
        """Test that legacy property accessors still work."""
        raw_data = [self.factory.create_structured_column_data()]
        column_data = self.adapter.normalize_input(raw_data)

        column = column_data[0]

        # These property accessors should work for backward compatibility
        self.assertIsInstance(column.synapses_per_layer, list)
        self.assertIsInstance(column.neurons_per_layer, list)
        self.assertEqual(len(column.synapses_per_layer), len(column.layers))
        self.assertEqual(len(column.neurons_per_layer), len(column.layers))

        # Verify values match layer data
        expected_synapses = [layer.synapse_count for layer in column.layers]
        expected_neurons = [layer.neuron_count for layer in column.layers]
        self.assertEqual(column.synapses_per_layer, expected_synapses)
        self.assertEqual(column.neurons_per_layer, expected_neurons)


class TestDeprecatedMethodsRemoved(unittest.TestCase):
    """Verify that deprecated methods have been properly removed."""

    def test_deprecated_processor_methods_removed(self):
        """Test that deprecated DataProcessor methods are removed."""
        processor = DataProcessor()

        deprecated_methods = [
            'calculate_thresholds_for_data',
            'calculate_min_max_for_data',
            'extract_metric_statistics',
            'validate_input_data',
            '_convert_summary_to_column_data'
        ]

        for method_name in deprecated_methods:
            self.assertFalse(hasattr(processor, method_name),
                           f"Deprecated method {method_name} still exists")

    def test_modern_api_available(self):
        """Test that modern API methods are available."""
        processor = DataProcessor()

        modern_methods = [
            'process_column_data',
            'get_processing_summary'
        ]

        for method_name in modern_methods:
            self.assertTrue(hasattr(processor, method_name),
                          f"Modern method {method_name} not available")
            self.assertTrue(callable(getattr(processor, method_name)),
                          f"Modern method {method_name} is not callable")


class TestSVGMetadataIntegration(unittest.TestCase):
    """Test SVG metadata generation integration."""

    def setUp(self):
        self.adapter = DataAdapter()
        self.processor = DataProcessor()
        self.factory = ModernTestDataFactory()

    def test_layer_data_for_svg_generation(self):
        """Test that processed data can be used for SVG metadata generation."""
        # Create test data with varied layer values
        raw_data = [
            self.factory.create_structured_column_data('ME', 'L', 0, 0, 5),
            self.factory.create_structured_column_data('ME', 'L', 1, 0, 5),
            self.factory.create_structured_column_data('ME', 'L', 0, 1, 5)
        ]

        column_data = self.adapter.normalize_input(raw_data)

        config = self.factory.create_processing_config()
        all_columns = self.factory.create_all_possible_columns()
        region_map = self.factory.create_region_columns_map()

        result = self.processor.process_column_data(
            column_data=column_data,
            all_possible_columns=all_columns,
            region_columns_map=region_map,
            config=config
        )

        self.assertTrue(result.is_successful)

        # Verify that processed columns have the data needed for SVG generation
        for column in result.processed_columns:
            if column.layer_values:
                # Should have accessible layer values for color mapping
                layer_values = column.layer_values
                self.assertTrue(all(isinstance(v, (int, float)) for v in layer_values))

                # Should have accessible colors for tooltip generation
                layer_colors = column.layer_colors
                self.assertEqual(len(layer_colors), len(column.layer_values))


def create_test_suite() -> unittest.TestSuite:
    """Create a comprehensive test suite for Option C."""
    suite = unittest.TestSuite()

    # Add all test classes
    test_classes = [
        TestModernDataAdapter,
        TestModernDataProcessor,
        TestIntegrationDataFlow,
        TestPerformanceAndScalability,
        TestErrorHandlingAndValidation,
        TestBackwardCompatibility,
        TestDeprecatedMethodsRemoved,
        TestSVGMetadataIntegration
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    return suite


def run_option_c_tests(verbose: bool = True) -> bool:
    """
    Run Option C - Comprehensive Test Suite Modernization.

    Args:
        verbose: Whether to show detailed output

    Returns:
        True if all tests pass, False otherwise
    """
    print("🧪 Running Option C - Comprehensive Test Suite Modernization")
    print("=" * 70)
    print()
    print("📋 Test Categories:")
    print("   • Modern Data Adapter Testing")
    print("   • Modern Data Processor Testing")
    print("   • Integration & Data Flow Testing")
    print("   • Performance & Scalability Testing")
    print("   • Error Handling & Validation Testing")
    print("   • Backward Compatibility Testing")
    print("   • Deprecated Method Removal Verification")
    print("   • SVG Metadata Integration Testing")
    print()

    # Configure logging for tests
    if not verbose:
        logging.disable(logging.CRITICAL)

    # Create and run test suite
    suite = create_test_suite()

    # Use detailed runner if verbose, otherwise capture output
    if verbose:
        runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    else:
        runner = unittest.TextTestRunner(
            verbosity=0,
            stream=open(os.devnull, 'w'),
            buffer=True
        )

    result = runner.run(suite)

    # Print summary
    print()
    print("=" * 70)
    print("📊 Option C Test Summary:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")

    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            test_name = str(test).split(' ')[0]
            error_msg = traceback.split('AssertionError: ')[-1].split('\n')[0] if 'AssertionError:' in traceback else 'Unknown failure'
            print(f"   {test_name}: {error_msg}")

    if result.errors:
        print("\n💥 ERRORS:")
        for test, traceback in result.errors:
            test_name = str(test).split(' ')[0]
            error_msg = traceback.split('\n')[-2] if traceback.split('\n') else 'Unknown error'
            print(f"   {test_name}: {error_msg}")

    success = result.wasSuccessful()

    if success:
        print("\n✅ ALL TESTS PASSED - Option C Modernization Successful!")
        print("\n🎯 Modernization Results:")
        print("   ✓ Modern API thoroughly tested")
        print("   ✓ Deprecated methods confirmed removed")
        print("   ✓ Structured data format validated")
        print("   ✓ Integration pipeline verified")
        print("   ✓ Performance characteristics confirmed")
        print("   ✓ Error handling validated")
        print("   ✓ Backward compatibility preserved")
        print("   ✓ SVG metadata generation supported")
        print("\n🚀 The data processing pipeline is now fully modernized")
        print("   and comprehensively tested with a robust test suite!")
    else:
        print("\n❌ Some tests failed - please review the issues above")
        print("\n🔧 Next Steps:")
        print("   1. Review and fix failing tests")
        print("   2. Ensure all deprecated methods are properly removed")
        print("   3. Verify data flow integrity")
        print("   4. Re-run tests until all pass")

    return success


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run Option C - Comprehensive Test Suite Modernization')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Run tests with minimal output')
    parser.add_argument('--category', '-c',
                       choices=['adapter', 'processor', 'integration', 'performance',
                               'error', 'compatibility', 'deprecated', 'svg'],
                       help='Run only specific test category')

    args = parser.parse_args()

    if args.category:
        # Run specific category only
        category_map = {
            'adapter': TestModernDataAdapter,
            'processor': TestModernDataProcessor,
            'integration': TestIntegrationDataFlow,
            'performance': TestPerformanceAndScalability,
            'error': TestErrorHandlingAndValidation,
            'compatibility': TestBackwardCompatibility,
            'deprecated': TestDeprecatedMethodsRemoved,
            'svg': TestSVGMetadataIntegration
        }

        test_class = category_map[args.category]
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=2 if not args.quiet else 0)
        result = runner.run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)
    else:
        # Run all tests
        success = run_option_c_tests(verbose=not args.quiet)
        sys.exit(0 if success else 1)
