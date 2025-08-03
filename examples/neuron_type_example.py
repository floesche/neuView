#!/usr/bin/env python3
"""
Example script demonstrating how to use the NeuronType class directly.

This shows how to programmatically work with neuron data using the new
NeuronType class, which encapsulates data fetching and provides a clean API.
"""

import sys
from pathlib import Path

# Add the src directory to Python path so we can import quickpage
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from quickpage import Config, NeuPrintConnector, NeuronType
from quickpage.config import NeuronTypeConfig


def main():
    """Demonstrate NeuronType class usage."""
    
    # Load configuration
    config_path = project_root / "config.yaml"
    config = Config.load(str(config_path))
    
    # Create neuprint connector
    connector = NeuPrintConnector(config)
    
    # Test connection
    print("Testing neuprint connection...")
    try:
        info = connector.test_connection()
        print(f"✓ Connected to {info['dataset']} dataset")
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return
    
    # Create a neuron type configuration
    lc4_config = NeuronTypeConfig(
        name="LC4",
        description="Lobula Columnar Type 4 neurons - motion detection",
        query_type="type"
    )
    
    # Create NeuronType instance for LC4 neurons
    print("\nCreating NeuronType instance for LC4...")
    lc4_neurons = NeuronType("LC4", lc4_config, connector, soma_side='both')
    
    # Print info before fetching data
    print(f"Before fetch: {lc4_neurons}")
    print(f"Data fetched: {lc4_neurons.is_fetched}")
    
    # Accessing properties will automatically fetch data
    print(f"\nNeuron counts:")
    print(f"  Total: {lc4_neurons.get_neuron_count()}")
    print(f"  Left: {lc4_neurons.get_neuron_count('left')}")
    print(f"  Right: {lc4_neurons.get_neuron_count('right')}")
    
    # Print info after fetching data
    print(f"\nAfter fetch: {lc4_neurons}")
    print(f"Data fetched: {lc4_neurons.is_fetched}")
    
    # Get synapse statistics
    synapse_stats = lc4_neurons.get_synapse_stats()
    print(f"\nSynapse statistics:")
    print(f"  Total presynapses: {synapse_stats['total_pre']:,}")
    print(f"  Total postsynapses: {synapse_stats['total_post']:,}")
    print(f"  Average presynapses per neuron: {synapse_stats['avg_pre']:.1f}")
    print(f"  Average postsynapses per neuron: {synapse_stats['avg_post']:.1f}")
    
    # Access detailed summary
    summary = lc4_neurons.summary
    print(f"\nDetailed summary:")
    print(f"  Type: {summary.type_name}")
    print(f"  Soma side filter: {summary.soma_side}")
    print(f"  Fetch time: {lc4_neurons.fetch_time}")
    
    # Show neuron DataFrame info
    neurons_df = lc4_neurons.neurons
    print(f"\nNeurons DataFrame:")
    print(f"  Shape: {neurons_df.shape}")
    print(f"  Columns: {list(neurons_df.columns)}")
    
    if not neurons_df.empty:
        print(f"\nFirst few neurons:")
        print(neurons_df[['type', 'instance', 'somaSide', 'pre', 'post']].head())
    
    # Example: Create NeuronType for different soma side
    print(f"\n" + "="*60)
    print("Creating NeuronType for left LC4 neurons only...")
    
    lc4_left = NeuronType("LC4", lc4_config, connector, soma_side='left')
    print(f"Left LC4 count: {lc4_left.get_neuron_count()}")
    
    # Compare with right side
    lc4_right = NeuronType("LC4", lc4_config, connector, soma_side='right')
    print(f"Right LC4 count: {lc4_right.get_neuron_count()}")
    
    print(f"\nBoth instances use the same connector and configuration")
    print(f"but fetch different subsets of the data based on soma_side parameter")


if __name__ == "__main__":
    main()
