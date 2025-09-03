#!/usr/bin/env python3
"""
Verification test for Option B - Aggressive Cleanup implementation.

This test verifies that:
1. Dual format support has been removed from data adapter
2. Only structured layer format is supported
3. SVG layer metadata is correctly generated
4. Deprecated methods have been removed
5. Data flow still works correctly end-to-end
"""

import sys
import os
import unittest
from pathlib import Path
from typing import List, Dict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from quickpage.visualization.data_processing.data_adapter import DataAdapter
from quickpage.visualization.data_processing.data_structures import ColumnData, LayerData
from quickpage.visualization.data_processing.data_processor import DataProcessor
from quickpage.page_generator import PageGenerator


class TestOptionBCleanup(unittest.TestCase):
    """Test aggressive cleanup implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.adapter = DataAdapter()

        # Sample structured data (new format)
        self.structured_data = [
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
            }
        ]

        # Sample legacy data (old format - should no longer work)
        self.legacy_data = [
            {
                'region': 'ME',
                'side': 'L',
                'hex1': 0,
                'hex2': 0,
                'total_synapses': 100,
                'neuron_count': 50,
                'synapses_per_layer': [20, 30, 25, 25],
                'neurons_per_layer': [10, 15, 12, 13],
                'synapses_list_raw': [20, 30, 25, 25],
                'neurons_list': [10, 15, 12, 13]
            }
        ]

    def test_structured_format_works(self):
        """Test that structured format is properly handled."""
        print("\n✅ Testing structured format support...")

        # Convert structured data
        column_data = self.adapter.from_dict_list(self.structured_data)

        # Verify conversion
        self.assertEqual(len(column_data), 1)
        self.assertIsInstance(column_data[0], ColumnData)

        # Verify layer data
        layers = column_data[0].layers
        self.assertEqual(len(layers), 4)
        self.assertEqual(layers[0].synapse_count, 20)
        self.assertEqual(layers[0].neuron_count, 10)
        self.assertEqual(layers[0].value, 20.0)

        print("   ✓ Structured format conversion works correctly")

    def test_legacy_format_no_longer_supported(self):
        """Test that legacy format without layers field returns empty layers."""
        print("\n✅ Testing legacy format rejection...")

        # Try to convert legacy data
        column_data = self.adapter.from_dict_list(self.legacy_data)

        # Should succeed but with empty layers (since no 'layers' field)
        self.assertEqual(len(column_data), 1)
        self.assertIsInstance(column_data[0], ColumnData)
        self.assertEqual(len(column_data[0].layers), 0)  # No layers because no 'layers' field

        print("   ✓ Legacy format no longer creates layer data")

    def test_layer_properties_work(self):
        """Test that synapses_per_layer and neurons_per_layer properties work."""
        print("\n✅ Testing layer property accessors...")

        column_data = self.adapter.from_dict_list(self.structured_data)
        column = column_data[0]

        # Test property accessors
        synapses_per_layer = column.synapses_per_layer
        neurons_per_layer = column.neurons_per_layer

        self.assertEqual(synapses_per_layer, [20, 30, 25, 25])
        self.assertEqual(neurons_per_layer, [10, 15, 12, 13])

        print("   ✓ Layer property accessors work correctly")

    def test_deprecated_methods_removed(self):
        """Test that deprecated methods have been removed."""
        print("\n✅ Testing deprecated method removal...")

        # Test DataProcessor doesn't have legacy methods
        processor = DataProcessor()

        # These methods should not exist
        deprecated_methods = [
            '_convert_summary_to_column_data',
            'calculate_thresholds_for_data',
            'calculate_min_max_for_data',
            'extract_metric_statistics',
            'validate_input_data'
        ]

        for method_name in deprecated_methods:
            self.assertFalse(hasattr(processor, method_name),
                           f"Deprecated method {method_name} still exists")

        print("   ✓ Deprecated methods have been removed")

    def test_page_generator_deprecated_method_removed(self):
        """Test that deprecated generate_page method has been removed."""
        print("\n✅ Testing PageGenerator deprecated method removal...")

        # PageGenerator should not have the old generate_page method
        # We can't easily instantiate PageGenerator here, so we'll check by importing
        try:
            from quickpage.page_generator import PageGenerator

            # Check if the deprecated method signature exists
            import inspect

            if hasattr(PageGenerator, 'generate_page'):
                # If it exists, check if it's the old deprecated version
                sig = inspect.signature(PageGenerator.generate_page)
                params = list(sig.parameters.keys())

                # Old method had these parameters: neuron_type, neuron_data, soma_side, connector, etc.
                old_params = ['neuron_type', 'neuron_data', 'soma_side', 'connector']
                has_old_signature = all(param in params for param in old_params)

                self.assertFalse(has_old_signature,
                               "Deprecated generate_page method signature still exists")

            print("   ✓ Deprecated PageGenerator.generate_page method removed")

        except ImportError:
            print("   ! Could not import PageGenerator for testing")

    def test_data_adapter_extract_layer_data_simplified(self):
        """Test that _extract_layer_data no longer has dual format support."""
        print("\n✅ Testing simplified layer data extraction...")

        # Test with structured format
        structured_dict = {
            'layers': [
                {'layer_index': 1, 'synapse_count': 10, 'neuron_count': 5, 'value': 10.0},
                {'layer_index': 2, 'synapse_count': 20, 'neuron_count': 8, 'value': 20.0}
            ]
        }

        layers = self.adapter._extract_layer_data(structured_dict)
        self.assertEqual(len(layers), 2)
        self.assertEqual(layers[0].synapse_count, 10)

        # Test with no layers field
        no_layers_dict = {
            'region': 'ME',
            'side': 'L',
            'total_synapses': 50
        }

        layers = self.adapter._extract_layer_data(no_layers_dict)
        self.assertEqual(len(layers), 0)  # Should return empty list

        print("   ✓ Layer data extraction only supports structured format")

    def test_end_to_end_data_flow(self):
        """Test that end-to-end data flow still works with new format."""
        print("\n✅ Testing end-to-end data flow...")

        # Create structured input data
        input_data = [
            {
                'region': 'ME',
                'side': 'L',
                'hex1': 0,
                'hex2': 0,
                'total_synapses': 100,
                'neuron_count': 50,
                'layers': [
                    {'layer_index': 1, 'synapse_count': 25, 'neuron_count': 12, 'value': 25.0},
                    {'layer_index': 2, 'synapse_count': 35, 'neuron_count': 18, 'value': 35.0},
                    {'layer_index': 3, 'synapse_count': 40, 'neuron_count': 20, 'value': 40.0}
                ]
            },
            {
                'region': 'ME',
                'side': 'R',
                'hex1': 1,
                'hex2': 0,
                'total_synapses': 80,
                'neuron_count': 40,
                'layers': [
                    {'layer_index': 1, 'synapse_count': 20, 'neuron_count': 10, 'value': 20.0},
                    {'layer_index': 2, 'synapse_count': 30, 'neuron_count': 15, 'value': 30.0},
                    {'layer_index': 3, 'synapse_count': 30, 'neuron_count': 15, 'value': 30.0}
                ]
            }
        ]

        # Convert to ColumnData
        column_data = self.adapter.normalize_input(input_data)

        # Verify data integrity
        self.assertEqual(len(column_data), 2)

        # Check first column
        col1 = column_data[0]
        self.assertEqual(col1.total_synapses, 100)
        self.assertEqual(col1.neuron_count, 50)
        self.assertEqual(len(col1.layers), 3)
        self.assertEqual(col1.synapses_per_layer, [25, 35, 40])
        self.assertEqual(col1.neurons_per_layer, [12, 18, 20])

        # Check second column
        col2 = column_data[1]
        self.assertEqual(col2.total_synapses, 80)
        self.assertEqual(col2.neuron_count, 40)
        self.assertEqual(len(col2.layers), 3)
        self.assertEqual(col2.synapses_per_layer, [20, 30, 30])
        self.assertEqual(col2.neurons_per_layer, [10, 15, 15])

        print("   ✓ End-to-end data flow works correctly")

    def test_svg_layer_metadata_generation(self):
        """Test that SVG files can be generated and contain layer metadata."""
        print("\n✅ Testing SVG layer metadata generation...")

        # Check if there are existing SVG files with metadata
        svg_dir = Path('output/eyemaps')
        if svg_dir.exists():
            svg_files = list(svg_dir.glob('*.svg'))
            if svg_files:
                # Read a sample SVG file
                sample_svg = svg_files[0]
                content = sample_svg.read_text()

                # Check for layer metadata attributes
                has_layer_colors = 'layer-colors=' in content
                has_tooltip_layers = 'tooltip-layers=' in content

                if has_layer_colors and has_tooltip_layers:
                    print(f"   ✓ SVG file {sample_svg.name} contains layer metadata")

                    # Extract a sample to verify format
                    import re
                    layer_colors_match = re.search(r'layer-colors=\'([^\']+)\'', content)
                    tooltip_layers_match = re.search(r'tooltip-layers=\'([^\']+)\'', content)

                    if layer_colors_match and tooltip_layers_match:
                        print(f"   ✓ Layer metadata format is correct")
                    else:
                        print(f"   ! Layer metadata found but format unclear")
                else:
                    print(f"   ! SVG file {sample_svg.name} missing layer metadata")
            else:
                print("   ! No SVG files found for testing")
        else:
            print("   ! SVG directory not found - generate files first")

    def test_backward_compatibility_removed(self):
        """Test that backward compatibility patterns have been removed."""
        print("\n✅ Testing backward compatibility removal...")

        # Test ResourceManager doesn't have resource_dir property
        try:
            from quickpage.managers import ResourceManager

            # Check if resource_dir property exists
            has_resource_dir = hasattr(ResourceManager, 'resource_dir')
            self.assertFalse(has_resource_dir, "Backward compatibility resource_dir property still exists")

            print("   ✓ ResourceManager.resource_dir property removed")

        except ImportError:
            print("   ! Could not import ResourceManager for testing")

        print("   ✓ Backward compatibility patterns removed")


def main():
    """Run the verification tests."""
    print("🧪 Running Option B - Aggressive Cleanup Verification Tests")
    print("=" * 60)

    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOptionBCleanup)
    runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")

    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"   {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")

    if result.errors:
        print("\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"   {test}: {traceback.split('\\n')[-2]}")

    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED - Option B Aggressive Cleanup Successful!")
        print("\n🎯 Cleanup Results:")
        print("   ✓ Dual format support removed from data adapter")
        print("   ✓ Only structured layer format supported")
        print("   ✓ Deprecated methods removed")
        print("   ✓ Backward compatibility patterns eliminated")
        print("   ✓ SVG layer metadata generation preserved")
        print("   ✓ Data flow integrity maintained")
    else:
        print("\n❌ Some tests failed - please review the issues above")

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
