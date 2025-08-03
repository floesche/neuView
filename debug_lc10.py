#!/usr/bin/env python3
"""
Debug script to investigate LC10 fetching issues with optic-lobe dataset.
"""

import sys
from pathlib import Path
import pandas as pd

# Add the src directory to the path so we can import quickpage
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from quickpage import Config, NeuPrintConnector, get_dataset_adapter
from neuprint import fetch_neurons, NeuronCriteria


def debug_lc10_fetch():
    """Debug LC10 data fetching."""
    
    print("=== Debugging LC10 Fetch with Optic-Lobe Dataset ===\n")
    
    # Load configuration
    config = Config.load("config.yaml")
    print(f"Dataset: {config.neuprint.dataset}")
    print(f"Server: {config.neuprint.server}")
    
    # Get dataset adapter
    adapter = get_dataset_adapter(config.neuprint.dataset)
    print(f"Using adapter: {type(adapter).__name__}")
    print()
    
    try:
        # Create connector
        connector = NeuPrintConnector(config)
        print("✓ Connected successfully")
        
        # Try to fetch LC10 data manually using neuprint directly
        print("\n--- Testing direct neuprint fetch ---")
        criteria = NeuronCriteria(type="LC10")
        neurons_df, roi_df = fetch_neurons(criteria)
        
        print(f"Raw fetch results:")
        print(f"  Neurons DataFrame shape: {neurons_df.shape}")
        print(f"  Neurons DataFrame empty: {neurons_df.empty}")
        
        if not neurons_df.empty:
            print(f"  Available columns: {list(neurons_df.columns)}")
            print(f"  First few rows:")
            print(neurons_df.head())
            
            # Test adapter processing
            print("\n--- Testing adapter processing ---")
            processed_df = adapter.normalize_columns(neurons_df)
            print(f"After normalize_columns: {processed_df.shape}")
            
            processed_df = adapter.extract_soma_side(processed_df)
            print(f"After extract_soma_side: {processed_df.shape}")
            
            if 'somaSide' in processed_df.columns:
                print(f"Soma side values: {processed_df['somaSide'].value_counts().to_dict()}")
            
            # Test synapse counting
            pre_total, post_total = adapter.get_synapse_counts(processed_df)
            print(f"Synapse counts - Pre: {pre_total}, Post: {post_total}")
            
            # Test summary calculation
            print("\n--- Testing summary calculation ---")
            summary = connector._calculate_summary(processed_df, "LC10", "both")
            print(f"Summary keys: {list(summary.keys())}")
            print(f"Summary: {summary}")
            
        else:
            print("  No LC10 neurons found in optic-lobe dataset!")
            
            # Try to see what neuron types are available
            print("\n--- Checking available neuron types ---")
            available_types = connector.get_available_types()
            print(f"Available types (first 20): {available_types[:20]}")
            
            # Check if any LC* types exist
            lc_types = [t for t in available_types if t.startswith('LC')]
            print(f"LC* types available: {lc_types}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def test_working_neuron_type():
    """Test with a neuron type that should work in optic-lobe."""
    
    print("\n=== Testing Known Working Neuron Type ===\n")
    
    config = Config.load("config.yaml")
    
    try:
        connector = NeuPrintConnector(config)
        
        # Get available types
        available_types = connector.get_available_types()
        print(f"Total available types: {len(available_types)}")
        
        # Try with a common optic-lobe type
        test_types = ['LC4', 'LPLC2', 'T4', 'T5']
        
        for neuron_type in test_types:
            if neuron_type in available_types:
                print(f"\nTesting {neuron_type}:")
                try:
                    data = connector.get_neuron_data(neuron_type, 'both')
                    summary = data['summary']
                    print(f"  ✓ Success: {summary['total_count']} neurons")
                    print(f"  Summary keys: {list(summary.keys())}")
                    break
                except Exception as e:
                    print(f"  ✗ Failed: {e}")
            else:
                print(f"  - {neuron_type} not available")
                
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    debug_lc10_fetch()
    test_working_neuron_type()
