#!/usr/bin/env python3
"""
Generate a sample HTML page without NeuPrint connection for testing.
"""

import sys
import os
from pathlib import Path
import pandas as pd
from datetime import datetime

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent / "src"))

from quickpage.config import Config
from quickpage.page_generator import PageGenerator


def create_mock_neuron_data(neuron_type: str, soma_side: str):
    """Create mock neuron data for testing."""
    # Create mock neurons DataFrame
    neurons_data = {
        'bodyId': [123456789, 123456790, 123456791],
        'instance': [f'{neuron_type}_001', f'{neuron_type}_002', f'{neuron_type}_003'],
        'type': [neuron_type, neuron_type, neuron_type],
        'pre': [45, 52, 38],
        'post': [123, 156, 98],
        'somaLocation': ['LHS', 'RHS', 'LHS']
    }
    neurons_df = pd.DataFrame(neurons_data)
    
    # Filter by soma side if specified
    if soma_side != 'both':
        side_map = {'left': 'LHS', 'right': 'RHS'}
        if soma_side in side_map:
            neurons_df = neurons_df[neurons_df['somaLocation'] == side_map[soma_side]]
    
    # Create summary statistics
    total_count = len(neurons_df)
    left_count = len(neurons_df[neurons_df['somaLocation'] == 'LHS'])
    right_count = len(neurons_df[neurons_df['somaLocation'] == 'RHS'])
    total_pre = neurons_df['pre'].sum()
    total_post = neurons_df['post'].sum()
    
    summary = {
        'total_count': total_count,
        'left_count': left_count,
        'right_count': right_count,
        'type': neuron_type,
        'soma_side': soma_side,
        'total_pre_synapses': total_pre,
        'total_post_synapses': total_post,
        'avg_pre_synapses': round(total_pre / total_count, 2) if total_count > 0 else 0,
        'avg_post_synapses': round(total_post / total_count, 2) if total_count > 0 else 0
    }
    
    return {
        'neurons': neurons_df,
        'roi_counts': pd.DataFrame(),  # Empty for mock
        'summary': summary,
        'connectivity': {
            'upstream': ['T4', 'T5', 'Tm9'],
            'downstream': ['LPLC2', 'LC11', 'LC15'],
            'note': 'Mock connectivity data for testing'
        },
        'type': neuron_type,
        'soma_side': soma_side
    }


def main():
    """Generate sample HTML pages."""
    print("Generating sample HTML pages...")
    
    # Load configuration
    try:
        config = Config.load("config.yaml")
        print(f"✓ Configuration loaded successfully")
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        sys.exit(1)
    
    # Initialize page generator
    generator = PageGenerator(config, "output")
    print(f"✓ Page generator initialized")
    
    # Generate sample pages for different neuron types and sides
    test_cases = [
        ('LC10', 'both'),
        ('LPLC2', 'left'),
        ('T4', 'right'),
    ]
    
    for neuron_type, soma_side in test_cases:
        print(f"\\nGenerating page for {neuron_type} ({soma_side} side)...")
        
        try:
            # Create mock data
            neuron_data = create_mock_neuron_data(neuron_type, soma_side)
            
            # Generate HTML page
            output_file = generator.generate_page(neuron_type, neuron_data, soma_side)
            
            print(f"✓ Generated: {output_file}")
            
        except Exception as e:
            print(f"✗ Error generating page for {neuron_type}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\\n" + "=" * 50)
    print("✓ Sample HTML generation complete!")
    print("\\nGenerated files can be found in the 'output' directory.")
    print("Open any HTML file in a web browser to view the results.")


if __name__ == "__main__":
    main()
