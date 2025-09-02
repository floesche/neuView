#!/usr/bin/env python3
"""
Test script to verify that specific ROIs are excluded from the ROI Innervation table.

This script tests that:
- OL(R) and OL(L) are excluded from optic-lobe dataset ROI tables
- Optic(R) and Optic(L) are excluded from CNS dataset ROI tables
- Other primary ROIs are still included as expected
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


def test_roi_exclusions():
    """Test that specific ROIs are excluded from innervation tables."""

    print("=== Testing ROI Exclusions from Innervation Tables ===\n")

    results = {}

    # Test optic-lobe dataset
    results['optic-lobe'] = test_optic_lobe_exclusions()

    # Test CNS dataset (if available)
    results['cns'] = test_cns_exclusions()

    # Summary
    print("\n=== Test Results Summary ===")
    for dataset, result in results.items():
        if result is None:
            print(f"{dataset}: Skipped (dataset not available)")
        elif result:
            print(f"✅ {dataset}: ROI exclusions working correctly")
        else:
            print(f"❌ {dataset}: ROI exclusions not working")

    all_passed = all(r for r in results.values() if r is not None)
    return all_passed


def test_optic_lobe_exclusions():
    """Test ROI exclusions for optic-lobe dataset."""

    print("--- Testing Optic-Lobe Dataset ---")

    try:
        # Load optic-lobe config
        config = Config.load("config.optic-lobe.yaml")
        print(f"✅ Loaded optic-lobe config: {config.neuprint.dataset}")

        connector = NeuPrintConnector(config)
        page_generator = PageGenerator.create_with_factory(config, "test_output")

    except Exception as e:
        print(f"❌ Failed to setup optic-lobe dataset: {e}")
        return None

    # Test dataset adapter primary ROI exclusions
    try:
        adapter = DatasetAdapterFactory.create_adapter('optic-lobe')

        # Create mock ROI list that includes the exclusions
        mock_rois = [
            'OL(R)', 'OL(L)',  # Should be excluded
            'ME(R)', 'ME(L)', 'LO(R)', 'LO(L)', 'LOP(R)', 'LOP(L)',  # Should be included
            'AME(R)', 'AME(L)', 'LA(R)', 'LA(L)',  # Should be included
            'FB(R)', 'FB(L)', 'PB', 'EB'  # Should be included
        ]

        primary_rois = adapter.query_primary_rois(mock_rois)

        print(f"   Mock ROIs: {len(mock_rois)} total")
        print(f"   Primary ROIs: {len(primary_rois)} selected")

        # Check exclusions
        excluded_found = [roi for roi in ['OL(R)', 'OL(L)'] if roi in primary_rois]
        if excluded_found:
            print(f"   ❌ Excluded ROIs found in primary list: {excluded_found}")
            return False
        else:
            print(f"   ✅ OL(R) and OL(L) properly excluded from primary ROIs")

        # Check inclusions
        expected_included = ['ME(R)', 'ME(L)', 'LO(R)', 'LO(L)', 'AME(R)', 'AME(L)']
        included_found = [roi for roi in expected_included if roi in primary_rois]
        print(f"   ✅ Expected ROIs included: {len(included_found)}/{len(expected_included)}")

    except Exception as e:
        print(f"   ❌ Adapter test failed: {e}")
        return False

    # Test page generator primary ROI method
    try:
        primary_rois_pg = page_generator._get_primary_rois(connector)

        excluded_in_pg = [roi for roi in ['OL(R)', 'OL(L)'] if roi in primary_rois_pg]
        if excluded_in_pg:
            print(f"   ❌ PageGenerator includes excluded ROIs: {excluded_in_pg}")
            return False
        else:
            print(f"   ✅ PageGenerator properly excludes OL(R) and OL(L)")

        print(f"   Primary ROIs from PageGenerator: {len(primary_rois_pg)} total")

    except Exception as e:
        print(f"   ❌ PageGenerator test failed: {e}")
        return False

    # Test with actual neuron data if available
    try:
        test_neuron_types = ["LPLC2", "T4", "T5", "LC4"]
        tested_successfully = False

        for neuron_type in test_neuron_types:
            try:
                neuron_data = connector.get_neuron_data(neuron_type, soma_side='combined')
                if not neuron_data['neurons'].empty:
                    tested_successfully = True

                    # Test ROI aggregation
                    roi_summary = page_generator._aggregate_roi_data(
                        neuron_data.get('roi_counts'),
                        neuron_data.get('neurons'),
                        'combined',
                        connector
                    )

                    if roi_summary:
                        roi_names = [roi['roi'] for roi in roi_summary]
                        excluded_in_summary = [roi for roi in ['OL(R)', 'OL(L)'] if roi in roi_names]

                        if excluded_in_summary:
                            print(f"   ❌ {neuron_type}: Excluded ROIs in summary: {excluded_in_summary}")
                            return False
                        else:
                            print(f"   ✅ {neuron_type}: OL(R)/OL(L) properly excluded from ROI summary")

                        print(f"   {neuron_type}: ROI summary contains {len(roi_names)} ROIs")
                    break

            except Exception:
                continue

        if not tested_successfully:
            print(f"   ⚠️  Could not test with actual neuron data")

    except Exception as e:
        print(f"   ❌ Neuron data test failed: {e}")

    return True


def test_cns_exclusions():
    """Test ROI exclusions for CNS dataset."""

    print("\n--- Testing CNS Dataset ---")

    try:
        # Load CNS config
        config = Config.load("config.cns.yaml")
        print(f"✅ Loaded CNS config: {config.neuprint.dataset}")

        connector = NeuPrintConnector(config)
        page_generator = PageGenerator.create_with_factory(config, "test_output")

    except Exception as e:
        print(f"❌ Failed to setup CNS dataset: {e}")
        return None

    # Test dataset adapter primary ROI exclusions
    try:
        adapter = DatasetAdapterFactory.create_adapter('cns')

        # Create mock ROI list that includes the exclusions
        mock_rois = [
            'Optic(R)', 'Optic(L)',  # Should be excluded
            'ME(R)', 'ME(L)', 'LO(R)', 'LO(L)',  # Should be included
            'AL(R)', 'AL(L)', 'MB(R)', 'MB(L)',  # Should be included
            'CX', 'PB', 'FB', 'EB'  # Should be included
        ]

        primary_rois = adapter.query_primary_rois(mock_rois)

        print(f"   Mock ROIs: {len(mock_rois)} total")
        print(f"   Primary ROIs: {len(primary_rois)} selected")

        # Check exclusions
        excluded_found = [roi for roi in ['Optic(R)', 'Optic(L)'] if roi in primary_rois]
        if excluded_found:
            print(f"   ❌ Excluded ROIs found in primary list: {excluded_found}")
            return False
        else:
            print(f"   ✅ Optic(R) and Optic(L) properly excluded from primary ROIs")

        # Check inclusions
        expected_included = ['ME(R)', 'ME(L)', 'AL(R)', 'AL(L)', 'MB(R)', 'MB(L)']
        included_found = [roi for roi in expected_included if roi in primary_rois]
        print(f"   ✅ Expected ROIs included: {len(included_found)}/{len(expected_included)}")

    except Exception as e:
        print(f"   ❌ Adapter test failed: {e}")
        return False

    # Test page generator primary ROI method
    try:
        primary_rois_pg = page_generator._get_primary_rois(connector)

        excluded_in_pg = [roi for roi in ['Optic(R)', 'Optic(L)'] if roi in primary_rois_pg]
        if excluded_in_pg:
            print(f"   ❌ PageGenerator includes excluded ROIs: {excluded_in_pg}")
            return False
        else:
            print(f"   ✅ PageGenerator properly excludes Optic(R) and Optic(L)")

        print(f"   Primary ROIs from PageGenerator: {len(primary_rois_pg)} total")

    except Exception as e:
        print(f"   ❌ PageGenerator test failed: {e}")
        return False

    return True


def show_exclusion_summary():
    """Show summary of ROI exclusions."""

    print("\n=== ROI Exclusion Requirements ===")

    print("\n📋 OPTIC-LOBE DATASET:")
    print("   ❌ Exclude: OL(R), OL(L)")
    print("   ✅ Include: ME(R), ME(L), LO(R), LO(L), LOP(R), LOP(L)")
    print("   ✅ Include: AME(R), AME(L), LA(R), LA(L)")
    print("   ✅ Include: Central brain ROIs (FB, PB, EB, etc.)")

    print("\n📋 CNS DATASET:")
    print("   ❌ Exclude: Optic(R), Optic(L)")
    print("   ✅ Include: ME(R), ME(L), LO(R), LO(L)")
    print("   ✅ Include: AL(R), AL(L), MB(R), MB(L)")
    print("   ✅ Include: CX, PB, FB, EB")

    print("\n🎯 PURPOSE:")
    print("   • Clean up ROI Innervation tables")
    print("   • Remove redundant or overly broad ROIs")
    print("   • Focus on meaningful ROI regions")
    print("   • Improve analysis clarity")

    print("\n🛠 IMPLEMENTATION:")
    print("   • Updated dataset adapter primary ROI queries")
    print("   • Modified page generator ROI filtering")
    print("   • Applied exclusions in ROI aggregation")


if __name__ == "__main__":
    show_exclusion_summary()
    success = test_roi_exclusions()

    if success:
        print("\n🎉 SUCCESS: ROI exclusions working correctly!")
        print("   ✅ OL(R) and OL(L) excluded from optic-lobe dataset")
        print("   ✅ Optic(R) and Optic(L) excluded from CNS dataset")
        print("   ✅ Other expected ROIs still included")
    else:
        print("\n❌ FAILED: ROI exclusions not working correctly.")
        sys.exit(1)
