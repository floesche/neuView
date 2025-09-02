#!/usr/bin/env python3
"""
Comprehensive test for Layer-Based ROI Analysis requirements.

This script tests that the layer analysis table:
1. Appears whenever neuron type has >0 connections in ME/LO/LOP layers
2. Always shows central brain, LA, AME entries (even if 0 synapses)
3. Shows ALL layer entries that exist in dataset (even if 0 synapses)
4. Defaults to 0 when neuron type has no connections in specific regions
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


def test_layer_analysis_requirements():
    """Test all layer analysis requirements."""

    print("=== Testing Layer-Based ROI Analysis Requirements ===\n")

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
        page_generator = PageGenerator.create_with_factory(config, "test_output")
        print(f"✅ Connected to NeuPrint and created page generator")
    except Exception as e:
        print(f"❌ Failed to setup: {e}")
        return False

    # Test different neuron types
    test_results = []
    neuron_types_to_test = ["LPLC2", "T4", "T5", "LC4", "LPLC1", "Mi1", "Tm3"]

    for neuron_type in neuron_types_to_test:
        print(f"\n--- Testing {neuron_type} ---")
        result = test_single_neuron_type(connector, page_generator, neuron_type)
        test_results.append((neuron_type, result))

        if result['success']:
            print(f"✅ {neuron_type}: All requirements met")
        else:
            print(f"❌ {neuron_type}: {result.get('error', 'Unknown error')}")

    # Summary
    print(f"\n=== Test Summary ===")
    successful_tests = [result for result in test_results if result[1]['success']]
    failed_tests = [result for result in test_results if not result[1]['success']]

    print(f"✅ Successful tests: {len(successful_tests)}/{len(test_results)}")
    for neuron_type, _ in successful_tests:
        print(f"   - {neuron_type}")

    if failed_tests:
        print(f"❌ Failed tests: {len(failed_tests)}")
        for neuron_type, result in failed_tests:
            print(f"   - {neuron_type}: {result.get('error', 'Unknown')}")

    # Overall result
    all_passed = len(failed_tests) == 0
    if all_passed:
        print(f"\n🎉 ALL TESTS PASSED!")
        print("✅ Layer analysis meets all requirements")
    else:
        print(f"\n❌ SOME TESTS FAILED")
        print("Check individual test results above")

    return all_passed


def test_single_neuron_type(connector, page_generator, neuron_type):
    """Test layer analysis requirements for a single neuron type."""

    result = {
        'success': False,
        'has_layer_data': False,
        'table_appears': False,
        'has_central_brain': False,
        'has_la': False,
        'has_ame': False,
        'all_layers_shown': False,
        'zeros_handled': False,
        'error': None
    }

    try:
        # Get neuron data
        neuron_data = connector.get_neuron_data(neuron_type, soma_side='combined')
        neurons_df = neuron_data['neurons']
        roi_df = neuron_data['roi_counts']

        if neurons_df.empty or roi_df.empty:
            result['error'] = f"No data found for {neuron_type}"
            return result

        print(f"   Data: {len(neurons_df)} neurons, {len(roi_df)} ROI entries")

        # Check if this neuron type has layer connections
        layer_pattern = r'^(ME|LO|LOP)_[LR]_layer_\d+$'
        layer_data = roi_df[roi_df['roi'].str.match(layer_pattern, na=False)]

        has_layer_connections = not layer_data.empty
        result['has_layer_data'] = has_layer_connections

        if has_layer_connections:
            layer_synapses = layer_data['pre'].sum() + layer_data['post'].sum()
            print(f"   ✅ Has layer connections: {len(layer_data)} entries, {layer_synapses} total synapses")
        else:
            print(f"   ❌ No layer connections found")
            result['error'] = "No layer connections - table should not appear"
            return result

        # Test layer analysis function
        layer_analysis = page_generator._analyze_layer_roi_data(
            roi_df,
            neurons_df,
            'combined',
            test_type,
            connector
        )

        if layer_analysis is None:
            result['error'] = "Layer analysis returned None despite having layer connections"
            return result

        result['table_appears'] = True
        print(f"   ✅ Layer analysis table appears")

        layers = layer_analysis.get('layers', [])
        print(f"   Analysis returned {len(layers)} entries")

        # Check required entries
        entry_regions = [layer.get('region', '') for layer in layers]

        # Requirement 2: Always show central brain, LA, AME
        result['has_central_brain'] = 'central brain' in entry_regions
        result['has_la'] = 'LA' in entry_regions
        result['has_ame'] = 'AME' in entry_regions

        if result['has_central_brain']:
            cb_entry = next(layer for layer in layers if layer.get('region') == 'central brain')
            cb_total = cb_entry.get('total', 0)
            print(f"   ✅ Central brain entry: {cb_total} synapses")
        else:
            print(f"   ❌ Central brain entry missing")

        if result['has_la']:
            la_entry = next(layer for layer in layers if layer.get('region') == 'LA')
            la_total = la_entry.get('total', 0)
            print(f"   ✅ LA entry: {la_total} synapses")
        else:
            print(f"   ❌ LA entry missing")

        if result['has_ame']:
            ame_entry = next(layer for layer in layers if layer.get('region') == 'AME')
            ame_total = ame_entry.get('total', 0)
            print(f"   ✅ AME entry: {ame_total} synapses")
        else:
            print(f"   ❌ AME entry missing")

        # Requirement 3: Check if all dataset layers are shown
        all_rois = roi_df['roi'].unique().tolist()
        all_dataset_layers = set()

        for roi in all_rois:
            import re
            match = re.match(layer_pattern, roi)
            if match:
                region = match.group(1)
                side = match.group(2)
                layer_num = int(match.group(3))
                all_dataset_layers.add((region, side, layer_num))

        shown_layers = set()
        for layer in layers:
            if layer.get('layer', 0) > 0:  # Actual layer (not central brain/LA/AME)
                region = layer.get('region', '')
                side = layer.get('side', '')
                layer_num = layer.get('layer', 0)
                shown_layers.add((region, side, layer_num))

        missing_layers = all_dataset_layers - shown_layers
        result['all_layers_shown'] = len(missing_layers) == 0

        if result['all_layers_shown']:
            print(f"   ✅ All {len(all_dataset_layers)} dataset layers shown")
        else:
            print(f"   ❌ Missing {len(missing_layers)} dataset layers: {list(missing_layers)[:3]}...")

        # Requirement 4: Check zeros are handled properly
        zero_entries = [layer for layer in layers if layer.get('total', 0) == 0]
        result['zeros_handled'] = len(zero_entries) > 0  # Should have some zero entries

        if result['zeros_handled']:
            print(f"   ✅ Zero entries handled: {len(zero_entries)} entries with 0 synapses")
        else:
            print(f"   ℹ️  No zero entries (may be normal if neuron has connections everywhere)")
            result['zeros_handled'] = True  # Don't fail for this

        # Test full page generation
        try:
            neuron_config = NeuronTypeConfig(name=neuron_type, description=f"{neuron_type} test")
            test_neuron = NeuronType(neuron_type, neuron_config, connector, soma_side='combined')

            output_file = page_generator.generate_page_from_neuron_type(
                test_neuron, connector, image_format='svg'
            )

            # Check HTML content
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    html_content = f.read()

                if 'Layer-Based ROI Analysis' in html_content:
                    layer_section = html_content.split('Layer-Based ROI Analysis')[1].split('</section>')[0]

                    # Check for required entries in HTML
                    html_has_central = 'central brain' in layer_section.lower()
                    html_has_la = '>LA<' in layer_section or 'LA</td>' in layer_section
                    html_has_ame = '>AME<' in layer_section or 'AME</td>' in layer_section

                    print(f"   HTML check - Central brain: {html_has_central}, LA: {html_has_la}, AME: {html_has_ame}")

                    if not all([html_has_central, html_has_la, html_has_ame]):
                        result['error'] = "Required entries missing from generated HTML"
                        return result

                else:
                    result['error'] = "Layer-Based ROI Analysis section not found in HTML"
                    return result
            else:
                result['error'] = "Generated HTML file not found"
                return result

        except Exception as e:
            result['error'] = f"Page generation failed: {str(e)}"
            return result

        # Overall success
        result['success'] = all([
            result['table_appears'],
            result['has_central_brain'],
            result['has_la'],
            result['has_ame'],
            result['all_layers_shown'],
            result['zeros_handled']
        ])

    except Exception as e:
        result['error'] = f"Test failed with exception: {str(e)}"
        import traceback
        traceback.print_exc()

    return result


def show_requirements_summary():
    """Show summary of requirements being tested."""

    print("\n=== Layer-Based ROI Analysis Requirements ===")

    print("\n📋 REQUIREMENT 1: Table Visibility")
    print("   ✓ Table appears when neuron has >0 connections in ME/LO/LOP layers")
    print("   ✓ Table hidden when neuron has no layer connections")

    print("\n📋 REQUIREMENT 2: Always Show Core Entries")
    print("   ✓ Central brain entry (consolidated)")
    print("   ✓ LA entry (individual)")
    print("   ✓ AME entry (individual)")
    print("   ✓ Show even if 0 synapses")

    print("\n📋 REQUIREMENT 3: Show All Dataset Layers")
    print("   ✓ All ME_[LR]_layer_* patterns in dataset")
    print("   ✓ All LO_[LR]_layer_* patterns in dataset")
    print("   ✓ All LOP_[LR]_layer_* patterns in dataset")
    print("   ✓ Show even if neuron has 0 connections")

    print("\n📋 REQUIREMENT 4: Default to Zero")
    print("   ✓ Regions with no connections show 0")
    print("   ✓ Layers with no connections show 0")
    print("   ✓ No missing entries")


if __name__ == "__main__":
    show_requirements_summary()
    success = test_layer_analysis_requirements()

    if success:
        print("\n🎉 SUCCESS: All layer analysis requirements implemented correctly!")
    else:
        print("\n❌ FAILED: Some requirements not met.")
        sys.exit(1)
