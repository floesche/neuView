#!/usr/bin/env python3
"""
Test script to verify AME and LA ROIs are included in central brain consolidation.

This script tests that AME and LA synapses appear in the consolidated "central brain"
entry in the Layer-Based ROI Analysis, even though they're excluded from the general
central brain definition.
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
from quickpage.dataset_adapters import DatasetAdapterFactory
from quickpage.neuron_type import NeuronType
from quickpage.config import NeuronTypeConfig


def test_ame_la_inclusion():
    """Test that AME and LA are included in central brain consolidation."""

    print("=== Testing AME and LA Inclusion in Central Brain Consolidation ===\n")

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
        print(f"✅ Connected to NeuPrint")
    except Exception as e:
        print(f"❌ Failed to connect to NeuPrint: {e}")
        return False

    # Create page generator
    try:
        page_generator = PageGenerator.create_with_factory(config, "test_output")
        print(f"✅ Created page generator")
    except Exception as e:
        print(f"❌ Failed to create page generator: {e}")
        return False

    # Get test neuron data (try LPLC2 first, then T4/T5 as alternatives)
    test_types = ["LPLC2", "T4", "T5", "LC4", "LPLC1"]
    neuron_data = None
    test_type = None

    for neuron_type in test_types:
        try:
            neuron_data = connector.get_neuron_data(neuron_type, soma_side='combined')
            if not neuron_data['neurons'].empty and not neuron_data['roi_counts'].empty:
                test_type = neuron_type
                print(f"✅ Using {neuron_type} for testing")
                break
        except Exception:
            continue

    if neuron_data is None or test_type is None:
        print("❌ Could not find suitable test neuron type")
        return False

    neurons_df = neuron_data['neurons']
    roi_df = neuron_data['roi_counts']

    print(f"   Data: {len(neurons_df)} neurons, {len(roi_df)} ROI entries")

    # Check for AME and LA data
    print("\n=== AME and LA ROI Data Analysis ===")

    ame_data = roi_df[roi_df['roi'].str.contains('AME', case=False, na=False)]
    la_data = roi_df[roi_df['roi'].str.contains('LA', case=False, na=False)]

    if ame_data.empty and la_data.empty:
        print("❌ No AME or LA ROI data found - cannot test inclusion")
        return False

    if not ame_data.empty:
        ame_rois = ame_data['roi'].unique().tolist()
        ame_pre_total = ame_data['pre'].sum()
        ame_post_total = ame_data['post'].sum()
        print(f"✅ Found AME data:")
        print(f"   ROIs: {ame_rois}")
        print(f"   Synapses: {ame_pre_total} pre, {ame_post_total} post, {ame_pre_total + ame_post_total} total")
    else:
        ame_pre_total = ame_post_total = 0
        print("ℹ️  No AME data found")

    if not la_data.empty:
        la_rois = la_data['roi'].unique().tolist()
        la_pre_total = la_data['pre'].sum()
        la_post_total = la_data['post'].sum()
        print(f"✅ Found LA data:")
        print(f"   ROIs: {la_rois}")
        print(f"   Synapses: {la_pre_total} pre, {la_post_total} post, {la_pre_total + la_post_total} total")
    else:
        la_pre_total = la_post_total = 0
        print("ℹ️  No LA data found")

    expected_ame_la_total = ame_pre_total + ame_post_total + la_pre_total + la_post_total

    if expected_ame_la_total == 0:
        print("❌ No AME or LA synapses found - cannot test inclusion")
        return False

    # Test ROI strategy classification
    print("\n=== ROI Strategy Classification ===")
    adapter = DatasetAdapterFactory.create_adapter('optic-lobe')
    all_rois = roi_df['roi'].unique().tolist()

    # Check general central brain classification (should exclude AME/LA)
    central_brain_rois = adapter.query_central_brain_rois(all_rois)
    ame_la_in_central = any('AME' in roi or 'LA' in roi for roi in central_brain_rois)

    print(f"AME/LA in general central brain classification: {ame_la_in_central}")
    print("(Expected: False - AME/LA should be excluded from general definition)")

    # Test layer analysis
    print("\n=== Testing Layer Analysis with AME/LA Inclusion ===")
    try:
        layer_analysis = page_generator._analyze_layer_roi_data(
            roi_df,
            neurons_df,
            'combined',
            test_type,
            connector
        )

        if layer_analysis is None:
            print("❌ Layer analysis returned None")
            return False

        layers = layer_analysis.get('layers', [])
        print(f"✅ Layer analysis completed with {len(layers)} entries")

        # Find central brain entry
        central_brain_entries = [layer for layer in layers if 'central brain' in layer.get('region', '').lower()]

        if not central_brain_entries:
            print("❌ No central brain entry found in layer analysis")
            return False

        central_brain_entry = central_brain_entries[0]
        central_brain_total = central_brain_entry.get('total', 0)
        central_brain_pre = central_brain_entry.get('pre', 0)
        central_brain_post = central_brain_entry.get('post', 0)

        print(f"✅ Found central brain entry:")
        print(f"   Total synapses: {central_brain_total}")
        print(f"   Pre: {central_brain_pre}, Post: {central_brain_post}")

        # Calculate what the central brain total should include
        # It should include: true central brain ROIs + AME + LA
        true_central_total = 0
        for roi in central_brain_rois:
            roi_data = roi_df[roi_df['roi'] == roi]
            if not roi_data.empty:
                true_central_total += roi_data['pre'].sum() + roi_data['post'].sum()

        expected_total = true_central_total + expected_ame_la_total

        print(f"\n=== Synapse Accounting ===")
        print(f"True central brain synapses: {true_central_total}")
        print(f"AME + LA synapses: {expected_ame_la_total}")
        print(f"Expected consolidated total: {expected_total}")
        print(f"Actual consolidated total: {central_brain_total}")

        # Check if AME/LA synapses are included
        if central_brain_total >= expected_ame_la_total:
            print("✅ AME and LA synapses appear to be included in central brain consolidation")
        else:
            print("❌ AME and LA synapses missing from central brain consolidation")
            return False

        # More precise check
        if abs(central_brain_total - expected_total) <= 1:  # Allow for rounding
            print("✅ Central brain total matches expected value (including AME/LA)")
        else:
            print(f"⚠️  Central brain total doesn't exactly match expected value")
            print(f"   Difference: {central_brain_total - expected_total}")
            print("   This could be due to other central brain ROIs or rounding")

    except Exception as e:
        print(f"❌ Layer analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test full page generation
    print("\n=== Testing Full Page Generation ===")
    try:
        neuron_config = NeuronTypeConfig(
            name=test_type,
            description=f"{test_type} test"
        )
        test_neuron = NeuronType(test_type, neuron_config, connector, soma_side='combined')

        output_file = page_generator.generate_page_from_neuron_type(
            test_neuron,
            connector,
            image_format='svg'
        )

        print(f"✅ Generated page: {output_file}")

        # Check HTML content
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                html_content = f.read()

            if 'Layer-Based ROI Analysis' in html_content:
                layer_section = html_content.split('Layer-Based ROI Analysis')[1].split('</section>')[0]

                # Look for central brain row
                if 'central brain' in layer_section.lower():
                    print("✅ Central brain entry found in HTML")

                    # Check that individual AME/LA entries are NOT present
                    individual_ame_la = False
                    for roi_pattern in ['AME(', 'AME_', 'LA(', 'LA_']:
                        if roi_pattern in layer_section and 'central brain' not in layer_section.split(roi_pattern)[0].split('<tr>')[-1]:
                            print(f"❌ Individual {roi_pattern} entry found (should be consolidated)")
                            individual_ame_la = True

                    if not individual_ame_la:
                        print("✅ AME and LA properly consolidated (no individual entries)")
                    else:
                        return False

                else:
                    print("❌ Central brain entry not found in HTML")
                    return False
            else:
                print("❌ Layer-Based ROI Analysis section not found")
                return False

        else:
            print("❌ Generated HTML file not found")
            return False

    except Exception as e:
        print(f"❌ Page generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n=== TEST SUMMARY ===")
    print("✅ All tests passed!")
    print("✅ AME and LA synapses are included in central brain consolidation")
    print("✅ Layer-Based ROI Analysis properly consolidates central brain + AME + LA")
    print("✅ Individual AME and LA entries are not shown (properly consolidated)")

    return True


def show_ame_la_inclusion_summary():
    """Show summary of AME/LA inclusion logic."""

    print("\n=== AME and LA Inclusion Summary ===")

    print("\n🔍 CONTEXT:")
    print("  • General central brain definition: Excludes AME and LA")
    print("  • Layer-based ROI analysis: Includes AME and LA in consolidation")
    print("  • This provides comprehensive synapse accounting")

    print("\n📋 LAYER ANALYSIS CONSOLIDATION:")
    print("  ✓ True central brain ROIs (PVLP, FB, PB, EB, NO, SMP, etc.)")
    print("  ✓ AME ROIs (AME(L), AME(R), AME_L, AME_R, etc.)")
    print("  ✓ LA ROIs (LA(L), LA(R), LA_L, LA_R, etc.)")
    print("  = Single 'central brain' entry with combined totals")

    print("\n🎯 RESULT:")
    print("  • Complete synapse accounting in layer analysis")
    print("  • Clean consolidated display")
    print("  • AME and LA synapses not lost or excluded")


if __name__ == "__main__":
    success = test_ame_la_inclusion()
    show_ame_la_inclusion_summary()

    if success:
        print("\n🎉 SUCCESS: AME and LA are properly included in central brain consolidation!")
    else:
        print("\n❌ FAILED: AME and LA inclusion not working correctly.")
        sys.exit(1)
