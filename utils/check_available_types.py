#!/usr/bin/env python3
"""
Utility script to check available neuron types in the configured dataset.
Useful for updating config.yaml with valid neuron types.
"""

import sys
from pathlib import Path

# Add the src directory to the path so we can import quickpage
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from quickpage import Config, NeuPrintConnector


def check_available_types():
    """Check what neuron types are available in the current dataset."""
    
    print("=== Available Neuron Types Check ===\n")
    
    # Load configuration
    config = Config.load("config.yaml")
    print(f"Dataset: {config.neuprint.dataset}")
    print(f"Server: {config.neuprint.server}")
    print()
    
    try:
        # Create connector
        connector = NeuPrintConnector(config)
        print("✓ Connected successfully\n")
        
        # Get all available types
        available_types = connector.get_available_types()
        print(f"Total available neuron types: {len(available_types)}\n")
        
        # Show currently configured types and their availability
        print("=== Currently Configured Types ===")
        for nt_config in config.neuron_types:
            name = nt_config.name
            if name in available_types:
                print(f"✓ {name} - Available")
            else:
                print(f"✗ {name} - NOT AVAILABLE")
                # Look for similar types
                similar = [t for t in available_types if name.lower() in t.lower() or t.lower() in name.lower()]
                if similar:
                    print(f"    Similar types found: {', '.join(similar[:10])}")
        print()
        
        # Show some common categories
        categories = {
            'LC': 'Lobula Columnar',
            'LPLC': 'Lobula Plate Lobula Columnar', 
            'T4': 'T4 Motion Detection',
            'T5': 'T5 Motion Detection',
            'Mi': 'Medulla Intrinsic',
            'Tm': 'Transmedulla',
            'C': 'Centrifugal'
        }
        
        print("=== Available Types by Category ===")
        for prefix, description in categories.items():
            matching = [t for t in available_types if t.startswith(prefix)]
            if matching:
                print(f"{description} ({prefix}*): {len(matching)} types")
                print(f"  Examples: {', '.join(matching[:10])}")
                if len(matching) > 10:
                    print(f"  ... and {len(matching) - 10} more")
                print()
        
        # Show all types if requested
        show_all = input("Show all available types? (y/N): ").lower().strip()
        if show_all == 'y':
            print("\n=== All Available Types ===")
            for i, neuron_type in enumerate(available_types, 1):
                print(f"{i:4d}. {neuron_type}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_available_types()
