#!/usr/bin/env python3
"""
Test script to verify the soma cache optimization implementation.

This script tests that the optimization properly uses the neuron type cache
instead of reading separate soma cache files.
"""

import sys
import logging
from pathlib import Path

# Add the quickpage module to the path
sys.path.insert(0, 'src')

from quickpage.neuprint_connector import NeuPrintConnector
from quickpage.config import Config

# Set up logging to see the optimization in action
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_soma_cache_optimization():
    """
    Test that soma sides are retrieved from neuron cache instead of soma cache files.
    """
    print("Testing Soma Cache Optimization")
    print("=" * 50)

    try:
        # Load config
        config = Config.load("config.yaml")

        # Create connector
        connector = NeuPrintConnector(config)

        # Test neuron types that should have cached data
        test_types = ["Dm4", "AN07B013", "AOTU019"]

        for neuron_type in test_types:
            print(f"\nTesting {neuron_type}:")

            # Clear memory cache to force fresh lookup
            if neuron_type in connector._soma_sides_cache:
                del connector._soma_sides_cache[neuron_type]
                print(f"  Cleared memory cache for {neuron_type}")

            # This should trigger the optimization
            print(f"  Calling get_soma_sides_for_type({neuron_type})...")

            try:
                soma_sides = connector.get_soma_sides_for_type(neuron_type)
                print(f"  Result: {soma_sides}")
                print(f"  ✅ Success")
            except Exception as e:
                print(f"  ❌ Error: {e}")

        # Test cache stats
        print(f"\nCache Statistics:")
        print(f"  Soma sides hits: {connector._cache_stats['soma_sides_hits']}")
        print(f"  Soma sides misses: {connector._cache_stats['soma_sides_misses']}")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_cache_file_counts():
    """
    Check the current state of cache files.
    """
    print(f"\nCache File Analysis:")
    print("-" * 30)

    cache_dir = Path("output/.cache")
    if not cache_dir.exists():
        print("❌ Cache directory doesn't exist")
        return

    # Count different types of cache files
    soma_cache_files = list(cache_dir.glob("*_soma_sides.json"))
    neuron_cache_files = [f for f in cache_dir.glob("*.json")
                         if not f.name.endswith("_soma_sides.json")
                         and not f.name.endswith("_columns.json")
                         and f.name != "roi_hierarchy.json"]

    print(f"Soma cache files: {len(soma_cache_files)}")
    print(f"Neuron cache files: {len(neuron_cache_files)}")

    if soma_cache_files:
        total_soma_size = sum(f.stat().st_size for f in soma_cache_files)
        print(f"Total soma cache size: {total_soma_size} bytes ({total_soma_size/1024:.1f}KB)")
        print(f"With optimization, these {len(soma_cache_files)} files are redundant")

if __name__ == "__main__":
    test_cache_file_counts()
    test_soma_cache_optimization()

    print(f"\n{'='*50}")
    print("OPTIMIZATION VERIFICATION")
    print(f"{'='*50}")
    print("Look for log messages containing:")
    print("  'Extracted soma sides from neuron cache'")
    print("  'retrieved from neuron cache'")
    print("")
    print("These indicate the optimization is working correctly.")
    print("If you see 'retrieved from persistent cache (fallback)',")
    print("it means the optimization fell back to the old method.")
