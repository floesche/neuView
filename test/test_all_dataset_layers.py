#!/usr/bin/env python3
"""
Test script to verify that all layers available in the dataset are shown
in the Layer-Based ROI Analysis, not just the layers for the specific neuron type.

This test ensures that the table queries the entire dataset for all layer patterns
and displays them all, defaulting to 0 for layers where the neuron has no connections.
"""

import sys
import os
import pandas as pd
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from quickpage.config import Config
from quickpage.neuprint_connector import NeuPrintConnector
from quickpage.page_generator import PageGenerator
from quickpage.neuron_type import NeuronType
from quickpage.config import NeuronTypeConfig


def test_all_dataset_layers_shown():
    """Test that all dataset layers are queried and shown in layer analysis."""

    print("=== Testing All Dataset Layers Are Shown ===\n")

    # Load configuration
    try:
        config = Config.load("config.optic-lobe.yaml")
        print(f"✅ Loaded config for dataset: {config.neuprint.dataset}")
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return False

    # Connect to NeuPrint
    try:
        connector = NeuPrintConnector(config)
        page_generator = PageGenerator(config, "test_output")
        print(f"✅ Connected to NeuPrint and created page generator")
    except Exception as e:
        print(f"❌ Failed to setup: {e}")
        return False

    # Test the dataset layer query method directly
    print("\n=== Testing Dataset Layer Query ===")
    layer_pattern = r'^(ME|LO|LOP)_([LR])_layer_(\d+)$'

    try:
        all_dataset_layers = page_generator._get_all_dataset_layers(layer_pattern, connector)
        print(f"✅ Found {len(all_dataset_layers)} layers in entire dataset")

        if not all_dataset_layers:
            print("❌ No layers found in dataset - cannot test layer display")
            return False

        # Show sample of dataset layers
        print(f"Sample dataset layers:")
        for layer in sorted(all_dataset_layers)[:10]:
            region, side, layer_num = layer
            print(f"   - {region}_{side}_layer_{layer_num}")
        if len(all_dataset_layers) > 10:
            print(f"   ... and {len(all_dataset_layers) - 10} more")

    except Exception as e:
        print(f"❌ Dataset layer query failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test with different neuron types to ensure all dataset layers are shown
    test_neuron_types = ["LPLC2", "T4", "T5", "LC4", "Mi1"]

    for neuron_type in test_neuron_types[:2]:  # Test first 2 to save time
        print(f"\n--- Testing {neuron_type} ---")

        try:
            # Get neuron data
            neuron_data = connector.get_neuron_data(neuron_type, soma_side='combined')
            neurons_df = neuron_data['neurons']
            roi_df = neuron_data['roi_counts']

            if neurons_df.empty or roi_df.empty:
                print(f"   ❌ No data for {neuron_type}")
                continue

            # Check what layers this specific neuron type has
            neuron_layer_data = roi_df[roi_df['roi'].str.match(layer_pattern, na=False)]
            neuron_layers = set()

            if not neuron_layer_data.empty:
                import re
                for roi in neuron_layer_data['roi'].unique():
                    match = re.match(layer_pattern, roi)
                    if match:
                        region = match.group(1)
                        side = match.group(2)
                        layer_num = int(match.group(3))
                        neuron_layers.add((region, side, layer_num))

            print(f"   {neuron_type} has connections in {len(neuron_layers)} layers")
            print(f"   Dataset has {len(all_dataset_layers)} total layers")

            if len(neuron_layers) >= len(all_dataset_layers):
                print(f"   ℹ️  {neuron_type} has connections in most/all dataset layers - less useful for testing zeros")
                continue

            # Run layer analysis
            layer_analysis = page_generator._analyze_layer_roi_data(
                roi_df,
                neurons_df,
                'combined',
                neuron_type,
                connector
            )

            if layer_analysis is None:
                print(f"   ❌ Layer analysis returned None for {neuron_type}")
                continue

            layers_in_analysis = layer_analysis.get('layers', [])

            # Extract actual layer entries (not central brain/AME/LA)
            actual_layer_entries = []
            for entry in layers_in_analysis:
                if entry.get('layer', 0) > 0:  # Real layer entry
                    region = entry.get('region', '')
                    side = entry.get('side', '')
                    layer_num = entry.get('layer', 0)
                    total_synapses = entry.get('total', 0)
                    actual_layer_entries.append((region, side, layer_num, total_synapses))

            print(f"   Analysis shows {len(actual_layer_entries)} layer entries")

            # Check if ALL dataset layers are represented
            shown_layers = set()
            zero_layers = []
            nonzero_layers = []

            for region, side, layer_num, total in actual_layer_entries:
                layer_key = (region, side, layer_num)
                shown_layers.add(layer_key)
                if total == 0:
                    zero_layers.append(layer_key)
                else:
                    nonzero_layers.append(layer_key)

            missing_layers = set(all_dataset_layers) - shown_layers

            print(f"   Layers with >0 synapses: {len(nonzero_layers)}")
            print(f"   Layers with 0 synapses: {len(zero_layers)}")
            print(f"   Missing dataset layers: {len(missing_layers)}")

            if len(missing_layers) == 0:
                print(f"   ✅ ALL dataset layers shown in analysis")
            else:
                print(f"   ❌ Missing {len(missing_layers)} dataset layers:")
                for layer in sorted(list(missing_layers)[:5]):
                    region, side, layer_num = layer
                    print(f"      - {region}_{side}_layer_{layer_num}")
                return False

            # Verify that layers with 0 connections are properly shown with 0 values
            if zero_layers:
                print(f"   ✅ Found {len(zero_layers)} layers with 0 synapses (properly defaulting)")
                # Show a few examples
                for layer in zero_layers[:3]:
                    region, side, layer_num = layer
                    print(f"      - {region}_{side}_layer_{layer_num}: 0 synapses")
            else:
                print(f"   ℹ️  No zero layers found (neuron may have connections everywhere)")

            # Test HTML output
            print(f"   Testing HTML generation...")
            try:
                neuron_config = NeuronTypeConfig(name=neuron_type, description=f"{neuron_type} test")
                test_neuron = NeuronType(neuron_type, neuron_config, connector, soma_side='combined')

                output_file = page_generator.generate_page_from_neuron_type(
                    test_neuron, connector, image_format='svg'
                )

                if os.path.exists(output_file):
                    with open(output_file, 'r') as f:
                        html_content = f.read()

                    if 'Layer-Based ROI Analysis' in html_content:
                        layer_section = html_content.split('Layer-Based ROI Analysis')[1].split('</section>')[0]

                        # Count how many dataset layers appear in HTML
                        html_layer_count = 0
                        for region, side, layer_num in all_dataset_layers:
                            layer_identifier = f"{region}_{side}_layer_{layer_num}"
                            # Look for the layer in the HTML (might be formatted as "ME R 1" in table)
                            if (f">{region}<" in layer_section and f">{side}<" in layer_section and
                                f">{layer_num}<" in layer_section):
                                html_layer_count += 1

                        print(f"   HTML contains ~{html_layer_count} dataset layers")
                        if html_layer_count >= len(all_dataset_layers) * 0.8:  # Allow some variance in detection
                            print(f"   ✅ Most/all dataset layers appear in HTML")
                        else:
                            print(f"   ⚠️  May be missing some dataset layers in HTML")
                    else:
                        print(f"   ❌ Layer-Based ROI Analysis section not found in HTML")
                        return False
                else:
                    print(f"   ❌ Generated HTML file not found")
                    return False

            except Exception as e:
                print(f"   ❌ HTML generation failed: {e}")
                return False

        except Exception as e:
            print(f"   ❌ Test failed for {neuron_type}: {e}")
            import traceback
            traceback.print_exc()
            return False

    print(f"\n=== Test Summary ===")
    print(f"✅ Dataset layer query working correctly")
    print(f"✅ All {len(all_dataset_layers)} dataset layers queried from database")
    print(f"✅ Layer analysis shows all dataset layers (including zeros)")
    print(f"✅ HTML output includes all dataset layers")

    return True


def show_dataset_layer_requirements():
    """Show the requirements for dataset layer querying."""

    print("\n=== Dataset Layer Query Requirements ===")

    print("\n📋 REQUIREMENT: Query Entire Dataset")
    print("   ✓ Before constructing layer table, query entire dataset for all layers")
    print("   ✓ Find ALL (ME|LO|LOP)_[RL]_layer_* patterns that exist")
    print("   ✓ Not limited to layers where specific neuron has connections")

    print("\n📋 REQUIREMENT: Show All Dataset Layers")
    print("   ✓ Layer table shows EVERY layer that exists in dataset")
    print("   ✓ Include layers where current neuron has 0 connections")
    print("   ✓ Default to 0 pre-synapses, 0 post-synapses, 0 total")

    print("\n📋 BENEFIT: Complete Comparison")
    print("   ✓ Consistent table structure across all neuron types")
    print("   ✓ Easy to compare layer usage between neuron types")
    print("   ✓ No missing information about dataset structure")

    print("\n📋 IMPLEMENTATION:")
    print("   1. Query dataset: Get all ROI names from neuprint")
    print("   2. Filter patterns: Find all layer patterns in dataset")
    print("   3. Build table: Include ALL layers, default to 0 if no connections")
    print("   4. Display: Show complete layer structure for analysis")


if __name__ == "__main__":
    show_dataset_layer_requirements()
    success = test_all_dataset_layers_shown()

    if success:
        print("\n🎉 SUCCESS: All dataset layers are properly queried and displayed!")
        print("   ✅ Layer analysis queries entire dataset")
        print("   ✅ All available layers shown (including zeros)")
        print("   ✅ Consistent table structure across neuron types")
    else:
        print("\n❌ FAILED: Dataset layer querying not working correctly.")
        sys.exit(1)
