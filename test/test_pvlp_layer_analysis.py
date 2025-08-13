#!/usr/bin/env python3
"""
Test script to verify PVLP appears in LPLC2 layer analysis after the fix.

This script tests whether PVLP (and other central brain ROIs) now appear
in the Layer-Based ROI Analysis section for LPLC2 neurons.
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


def test_pvlp_in_layer_analysis():
    """Test if PVLP now appears in LPLC2 layer analysis."""

    print("=== Testing PVLP in LPLC2 Layer Analysis ===\n")

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

    # Get LPLC2 data
    try:
        neuron_data = connector.get_neuron_data("LPLC2", soma_side='both')
        neurons_df = neuron_data['neurons']
        roi_df = neuron_data['roi_counts']

        if neurons_df.empty or roi_df.empty:
            print("❌ No LPLC2 data found")
            return False

        print(f"✅ Found LPLC2 data: {len(neurons_df)} neurons, {len(roi_df)} ROI entries")

    except Exception as e:
        print(f"❌ Failed to get LPLC2 data: {e}")
        return False

    # Check if PVLP ROI data exists
    pvlp_data = roi_df[roi_df['roi'].str.contains('PVLP', case=False, na=False)]
    if pvlp_data.empty:
        print("❌ No PVLP ROI data found for LPLC2 - cannot test layer analysis")
        return False

    print(f"✅ Found PVLP data: {len(pvlp_data)} entries")
    print(f"   PVLP ROIs: {pvlp_data['roi'].unique().tolist()}")
    print(f"   PVLP synapses: {pvlp_data['pre'].sum()} pre, {pvlp_data['post'].sum()} post")

    # Test the layer analysis directly
    try:
        print("\n=== Testing Layer Analysis Function ===")
        layer_analysis = page_generator._analyze_layer_roi_data(
            roi_df,
            neurons_df,
            'both',
            'LPLC2',
            connector
        )

        if layer_analysis is None:
            print("❌ Layer analysis returned None")
            return False

        print(f"✅ Layer analysis completed")
        print(f"   Total layers: {len(layer_analysis.get('layers', []))}")

        # Check if any PVLP entries are in the results
        layers = layer_analysis.get('layers', [])
        pvlp_entries = [layer for layer in layers if 'PVLP' in layer.get('roi', '').upper()]

        if pvlp_entries:
            print(f"✅ Found {len(pvlp_entries)} PVLP entries in layer analysis:")
            for entry in pvlp_entries:
                roi = entry.get('roi', 'Unknown')
                pre = entry.get('pre', 0)
                post = entry.get('post', 0)
                total = entry.get('total', 0)
                print(f"   - {roi}: {pre} pre, {post} post, {total} total")
        else:
            print("❌ No PVLP entries found in layer analysis")
            print("\n   Available entries:")
            for entry in layers[:10]:  # Show first 10
                roi = entry.get('roi', 'Unknown')
                region = entry.get('region', 'Unknown')
                layer = entry.get('layer', 'Unknown')
                total = entry.get('total', 0)
                print(f"   - {roi} (region: {region}, layer: {layer}, total: {total})")
            if len(layers) > 10:
                print(f"   ... and {len(layers) - 10} more")
            return False

    except Exception as e:
        print(f"❌ Layer analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test ROI strategy integration
    try:
        print("\n=== Testing ROI Strategy Integration ===")
        from quickpage.dataset_adapters import DatasetAdapterFactory

        adapter = DatasetAdapterFactory.create_adapter('optic-lobe')
        all_rois = roi_df['roi'].unique().tolist()
        central_brain_rois = adapter.query_central_brain_rois(all_rois)

        pvlp_rois = [roi for roi in all_rois if 'PVLP' in roi.upper()]
        pvlp_is_central = any(roi in central_brain_rois for roi in pvlp_rois)

        print(f"   All ROIs: {len(all_rois)}")
        print(f"   Central brain ROIs: {len(central_brain_rois)}")
        print(f"   PVLP ROIs found: {pvlp_rois}")
        print(f"   PVLP classified as central brain: {pvlp_is_central}")

        if pvlp_is_central:
            print("✅ PVLP correctly classified as central brain")
        else:
            print("❌ PVLP not classified as central brain")
            return False

    except Exception as e:
        print(f"❌ ROI strategy test failed: {e}")
        return False

    # Test full page generation
    try:
        print("\n=== Testing Full Page Generation ===")
        neuron_config = NeuronTypeConfig(
            name="LPLC2",
            description="LPLC2 test"
        )
        lplc2 = NeuronType("LPLC2", neuron_config, connector, soma_side='both')

        # This should now include PVLP in layer analysis
        output_file = page_generator.generate_page_from_neuron_type(
            lplc2,
            connector,
            image_format='svg'
        )

        print(f"✅ Generated page: {output_file}")

        # Check if the HTML contains PVLP
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                html_content = f.read()

            if 'PVLP' in html_content:
                print("✅ PVLP found in generated HTML")

                # Count PVLP occurrences in layer analysis section
                layer_section = html_content.split('Layer-Based ROI Analysis')[1].split('</section>')[0] if 'Layer-Based ROI Analysis' in html_content else ""
                pvlp_count = layer_section.count('PVLP')

                if pvlp_count > 0:
                    print(f"✅ PVLP appears {pvlp_count} times in Layer-Based ROI Analysis section")
                else:
                    print("❌ PVLP not found in Layer-Based ROI Analysis section")
                    return False
            else:
                print("❌ PVLP not found in generated HTML")
                return False
        else:
            print("❌ Generated HTML file not found")
            return False

    except Exception as e:
        print(f"❌ Page generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n=== TEST RESULTS ===")
    print("✅ All tests passed!")
    print("✅ PVLP now appears in LPLC2 Layer-Based ROI Analysis")
    print("✅ The fix successfully integrates dataset-specific ROI strategies")

    return True


def show_before_after_comparison():
    """Show what changed with the fix."""

    print("\n=== BEFORE vs AFTER Comparison ===")
    print("\nBEFORE (hardcoded approach):")
    print("  Layer analysis only included:")
    print("  - (ME|LO|LOP)_[LR]_layer_* patterns")
    print("  - AME_L, AME_R, LA_L, LA_R")
    print("  - centralBrain, centralBrain-unspecified")
    print("  → PVLP was excluded (not in hardcoded list)")

    print("\nAFTER (dataset-specific ROI strategy):")
    print("  Layer analysis now includes:")
    print("  - (ME|LO|LOP)_[LR]_layer_* patterns")
    print("  - AME_L, AME_R, LA_L, LA_R")
    print("  - ALL central brain ROIs per dataset strategy")
    print("  → PVLP included (classified as central brain)")

    print("\nDataset-specific central brain definition:")
    print("  Optic-lobe: Everything NOT in {ME, LO, LOP, AME, LA}")
    print("              and NOT matching layer/column patterns")
    print("  → PVLP qualifies as central brain")
    print("  → Now appears in Layer-Based ROI Analysis")


if __name__ == "__main__":
    success = test_pvlp_in_layer_analysis()
    show_before_after_comparison()

    if success:
        print("\n🎉 SUCCESS: PVLP connectivity issue has been resolved!")
    else:
        print("\n❌ FAILED: PVLP connectivity issue still exists.")
        sys.exit(1)
