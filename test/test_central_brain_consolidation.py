#!/usr/bin/env python3
"""
Test script to verify central brain ROI consolidation in layer analysis.

This script tests that all central brain ROIs (everything not in optic lobe
regions or layer/column patterns) are consolidated under a single
"central brain" entry in the Layer-Based ROI Analysis.
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


def test_central_brain_consolidation():
    """Test that central brain ROIs are properly consolidated."""

    print("=== Testing Central Brain Consolidation in Layer Analysis ===\n")

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
        page_generator = PageGenerator(config, "test_output")
        print(f"✅ Created page generator")
    except Exception as e:
        print(f"❌ Failed to create page generator: {e}")
        return False

    # Test with LPLC2 (should have central brain connections)
    try:
        neuron_data = connector.get_neuron_data("LPLC2", soma_side='combined')
        neurons_df = neuron_data['neurons']
        roi_df = neuron_data['roi_counts']

        if neurons_df.empty or roi_df.empty:
            print("❌ No LPLC2 data found")
            return False

        print(f"✅ Found LPLC2 data: {len(neurons_df)} neurons, {len(roi_df)} ROI entries")

    except Exception as e:
        print(f"❌ Failed to get LPLC2 data: {e}")
        return False

    # Analyze what ROIs should be excluded vs included
    print("\n=== ROI Classification Analysis ===")

    adapter = DatasetAdapterFactory.create_adapter('optic-lobe')
    all_rois = roi_df['roi'].unique().tolist()

    # Get ROI categories
    roi_categories = adapter.categorize_rois(all_rois)
    central_brain_rois = roi_categories.get('central_brain', [])
    optic_rois = roi_categories.get('optic_regions', [])
    layer_rois = roi_categories.get('layers', [])
    column_rois = roi_categories.get('columns', [])

    print(f"Total ROIs: {len(all_rois)}")
    print(f"Central brain ROIs: {len(central_brain_rois)}")
    print(f"Optic region ROIs: {len(optic_rois)}")
    print(f"Layer ROIs: {len(layer_rois)}")
    print(f"Column ROIs: {len(column_rois)}")

    # Show samples of each category
    print(f"\nSample optic region ROIs: {optic_rois[:5]}")
    print(f"Sample layer ROIs: {layer_rois[:5]}")
    print(f"Sample column ROIs: {column_rois[:5]}")
    print(f"Sample central brain ROIs: {central_brain_rois[:10]}")

    # Check for specific ROIs mentioned in requirements
    key_rois_to_check = ['PVLP', 'FB', 'PB', 'EB', 'NO', 'SMP', 'CRE']
    for roi_name in key_rois_to_check:
        matching_rois = [roi for roi in all_rois if roi_name in roi.upper()]
        if matching_rois:
            is_central = any(roi in central_brain_rois for roi in matching_rois)
            print(f"  {roi_name} ROIs: {matching_rois} → Central brain: {is_central}")

    # Test the layer analysis with consolidation
    print("\n=== Testing Layer Analysis with Consolidation ===")
    try:
        layer_analysis = page_generator._analyze_layer_roi_data(
            roi_df,
            neurons_df,
            'combined',
            'LPLC2',
            connector
        )

        if layer_analysis is None:
            print("❌ Layer analysis returned None")
            return False

        layers = layer_analysis.get('layers', [])
        print(f"✅ Layer analysis completed with {len(layers)} entries")

        # Check for consolidated central brain entry
        central_brain_entries = [layer for layer in layers if 'central brain' in layer.get('region', '').lower()]

        if central_brain_entries:
            print(f"✅ Found {len(central_brain_entries)} consolidated central brain entry:")
            for entry in central_brain_entries:
                roi = entry.get('roi', 'Unknown')
                region = entry.get('region', 'Unknown')
                pre = entry.get('pre', 0)
                post = entry.get('post', 0)
                total = entry.get('total', 0)
                print(f"   - {region}: {pre} pre, {post} post, {total} total synapses")
        else:
            print("❌ No consolidated central brain entry found")
            return False

        # Check that individual central brain ROIs are NOT listed separately
        individual_central_entries = [
            layer for layer in layers
            if layer.get('roi', '') in central_brain_rois and 'central brain' not in layer.get('region', '').lower()
        ]

        if individual_central_entries:
            print(f"❌ Found {len(individual_central_entries)} individual central brain ROIs (should be consolidated):")
            for entry in individual_central_entries[:5]:
                print(f"   - {entry.get('roi', 'Unknown')}")
            return False
        else:
            print("✅ No individual central brain ROIs found - properly consolidated")

        # Show what entries ARE in the layer analysis
        print(f"\nFinal layer analysis entries ({len(layers)} total):")
        for entry in layers:
            roi = entry.get('roi', 'Unknown')
            region = entry.get('region', 'Unknown')
            layer_num = entry.get('layer', 0)
            total = entry.get('total', 0)
            if layer_num > 0:
                print(f"   - {roi} (layer {layer_num}): {total} synapses")
            else:
                print(f"   - {region}: {total} synapses")

    except Exception as e:
        print(f"❌ Layer analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test full page generation
    print("\n=== Testing Full Page Generation ===")
    try:
        neuron_config = NeuronTypeConfig(
            name="LPLC2",
            description="LPLC2 test"
        )
        lplc2 = NeuronType("LPLC2", neuron_config, connector, soma_side='combined')

        output_file = page_generator.generate_page_from_neuron_type(
            lplc2,
            connector,
            image_format='svg'
        )

        print(f"✅ Generated page: {output_file}")

        # Check the HTML content
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                html_content = f.read()

            # Check for "central brain" in layer analysis section
            if 'Layer-Based ROI Analysis' in html_content:
                layer_section = html_content.split('Layer-Based ROI Analysis')[1].split('</section>')[0]

                central_brain_count = layer_section.lower().count('central brain')
                if central_brain_count > 0:
                    print(f"✅ 'central brain' appears {central_brain_count} times in Layer-Based ROI Analysis")
                else:
                    print("❌ 'central brain' not found in Layer-Based ROI Analysis section")
                    return False

                # Check that individual central brain ROIs are not listed
                problem_rois = ['PVLP', 'FB(', 'PB', 'EB', 'NO(', 'SMP(', 'CRE(']
                individual_roi_found = False
                for roi in problem_rois:
                    if roi in layer_section and 'central brain' not in layer_section.split(roi)[0].split('<tr>')[-1]:
                        print(f"❌ Individual ROI '{roi}' found in layer analysis (should be consolidated)")
                        individual_roi_found = True
                        break

                if not individual_roi_found:
                    print("✅ Individual central brain ROIs properly consolidated")
                else:
                    return False

            else:
                print("❌ Layer-Based ROI Analysis section not found in HTML")
                return False
        else:
            print("❌ Generated HTML file not found")
            return False

    except Exception as e:
        print(f"❌ Page generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def show_consolidation_summary():
    """Show summary of what the consolidation does."""

    print("\n=== Central Brain Consolidation Summary ===")
    print("\nOPTIC LOBE DATASET - Layer-Based ROI Analysis:")

    print("\n📋 INCLUDED AS INDIVIDUAL ENTRIES:")
    print("  ✓ Layer patterns: (ME|LO|LOP)_[RL]_layer_*")
    print("  ✓ Column patterns: (ME|LO|LOP)_[RL]_col_*")

    print("\n📦 CONSOLIDATED UNDER 'central brain':")
    print("  ✓ All ROIs NOT matching:")
    print("    - LA, LO, LOP, ME, AME")
    print("    - Layer patterns: *_[RL]_layer_*")
    print("    - Column patterns: *_[RL]_col_*")
    print("  ✓ Examples: PVLP, FB(L), FB(R), PB, EB, NO(L), NO(R), SMP(L), etc.")

    print("\n🎯 RESULT:")
    print("  • Layer analysis shows individual layers/columns")
    print("  • Plus ONE consolidated 'central brain' entry")
    print("  • Central brain entry sums ALL non-optic synapses")
    print("  • Clean, organized display per dataset requirements")


if __name__ == "__main__":
    success = test_central_brain_consolidation()
    show_consolidation_summary()

    if success:
        print("\n🎉 SUCCESS: Central brain consolidation working correctly!")
        print("   PVLP and other central brain ROIs are now consolidated under 'central brain'")
    else:
        print("\n❌ FAILED: Central brain consolidation not working properly.")
        sys.exit(1)
