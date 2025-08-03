#!/usr/bin/env python3
"""
Example script demonstrating dataset adapter usage for different NeuPrint datasets.

This shows how the system automatically adapts to different dataset structures
and handles soma side extraction differently for each dataset type.
"""

import sys
from pathlib import Path

# Add the src directory to the path so we can import quickpage
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from quickpage import (
    Config, NeuPrintConnector, NeuronType, 
    DatasetAdapterFactory, get_dataset_adapter
)
from quickpage.config import NeuronTypeConfig


def demonstrate_dataset_adapters():
    """Demonstrate how different dataset adapters work."""
    
    print("=== Dataset Adapter Demonstration ===\n")
    
    # Show supported datasets
    supported = DatasetAdapterFactory.get_supported_datasets()
    print(f"Supported datasets: {', '.join(supported)}\n")
    
    # Demonstrate adapter creation for different datasets
    datasets_to_test = ['cns', 'hemibrain', 'optic-lobe', 'optic-lobe:v1.1']
    
    for dataset_name in datasets_to_test:
        print(f"Dataset: {dataset_name}")
        adapter = get_dataset_adapter(dataset_name)
        print(f"  Adapter type: {type(adapter).__name__}")
        print(f"  Dataset info: {adapter.dataset_info.name}")
        if adapter.dataset_info.soma_side_column:
            print(f"  Soma side column: {adapter.dataset_info.soma_side_column}")
        if adapter.dataset_info.soma_side_extraction:
            print(f"  Soma side regex: {adapter.dataset_info.soma_side_extraction}")
        print()


def test_current_dataset():
    """Test the current dataset configuration."""
    
    print("=== Testing Current Dataset ===\n")
    
    # Load configuration
    config = Config.load("config.yaml")
    print(f"Current dataset: {config.neuprint.dataset}")
    
    # Get the appropriate adapter
    adapter = get_dataset_adapter(config.neuprint.dataset)
    print(f"Using adapter: {type(adapter).__name__}")
    
    try:
        # Create connector (this will use the dataset adapter internally)
        connector = NeuPrintConnector(config)
        print("✓ Connected to neuprint successfully")
        
        # Test with a neuron type
        lc4_config = NeuronTypeConfig(
            name="LC4",
            description="Lobula Columnar Type 4 neurons"
        )
        
        # Create neuron type instances for different soma sides
        print("\nTesting soma side filtering:")
        
        for side in ['both', 'left', 'right']:
            try:
                lc4 = NeuronType("LC4", lc4_config, connector, soma_side=side)
                count = lc4.get_neuron_count()
                print(f"  {side.capitalize()}: {count} neurons")
            except Exception as e:
                print(f"  {side.capitalize()}: Error - {e}")
        
        # Test soma side extraction on a small sample
        print("\nTesting soma side extraction:")
        lc4_both = NeuronType("LC4", lc4_config, connector, soma_side='both')
        neurons_df = lc4_both.neurons
        
        if 'somaSide' in neurons_df.columns:
            side_counts = neurons_df['somaSide'].value_counts()
            print(f"  Soma sides found: {dict(side_counts)}")
        else:
            print("  No somaSide column found")
        
        if 'instance' in neurons_df.columns:
            print(f"  Sample instance names: {neurons_df['instance'].head().tolist()}")
        
    except Exception as e:
        print(f"✗ Error: {e}")


def simulate_optic_lobe_dataset():
    """Simulate how the optic-lobe adapter would work."""
    
    print("\n=== Simulating Optic-Lobe Dataset ===\n")
    
    import pandas as pd
    
    # Create sample data that mimics optic-lobe structure
    sample_data = pd.DataFrame({
        'bodyId': [1, 2, 3, 4, 5, 6],
        'instance': ['LC4_L', 'LC4_R', 'LPLC2_L_001', 'LPLC2_R_002', 'T4_L_medulla', 'T4_R_medulla'],
        'type': ['LC4', 'LC4', 'LPLC2', 'LPLC2', 'T4', 'T4'],
        'pre': [400, 450, 300, 350, 200, 250],
        'post': [2500, 2600, 1800, 1900, 1200, 1300]
    })
    
    print("Sample optic-lobe data:")
    print(sample_data)
    print()
    
    # Get optic-lobe adapter
    adapter = get_dataset_adapter('optic-lobe')
    
    # Test soma side extraction
    processed_data = adapter.extract_soma_side(sample_data)
    print("After soma side extraction:")
    print(processed_data[['instance', 'somaSide']])
    print()
    
    # Test filtering
    left_data = adapter.filter_by_soma_side(processed_data, 'left')
    print(f"Left-side neurons: {len(left_data)}")
    print(left_data[['instance', 'somaSide']])
    print()
    
    # Test synapse counting
    pre_total, post_total = adapter.get_synapse_counts(processed_data)
    print(f"Total synapses - Pre: {pre_total}, Post: {post_total}")


def main():
    """Main function."""
    
    try:
        demonstrate_dataset_adapters()
        test_current_dataset()
        simulate_optic_lobe_dataset()
        
        print("\n=== Summary ===")
        print("The dataset adapter system provides:")
        print("1. Automatic detection of dataset type")
        print("2. Dataset-specific soma side extraction")
        print("3. Consistent interface across all datasets")
        print("4. Easy extensibility for new datasets")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
