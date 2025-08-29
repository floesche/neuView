#!/usr/bin/env python3
"""
Focused test to verify the soma cache optimization is working.

This script forces fresh cache lookups to demonstrate the optimization
that uses neuron type cache instead of soma cache files.
"""

import sys
import logging
import os
from pathlib import Path

# Add the quickpage module to the path
sys.path.insert(0, 'src')

from quickpage.neuprint_connector import NeuPrintConnector
from quickpage.config import Config

def test_optimization_fresh():
    """
    Test optimization with fresh connector instance and cleared caches.
    """
    print("Verifying Soma Cache Optimization")
    print("=" * 50)

    # Set up detailed logging to capture optimization messages
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Only show our connector logs to reduce noise
    logging.getLogger('quickpage.neuprint_connector').setLevel(logging.DEBUG)
    logging.getLogger('quickpage.cache').setLevel(logging.WARNING)
    logging.getLogger('neuprint').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    try:
        # Load config
        config = Config.load("config.yaml")

        # Create fresh connector
        print("\n1. Creating fresh NeuPrintConnector...")
        connector = NeuPrintConnector(config)

        # Test with neuron types that should have neuron cache data
        test_types = ["Dm4", "AN07B013", "AOTU019"]

        for i, neuron_type in enumerate(test_types, 1):
            print(f"\n{i+1}. Testing {neuron_type} (fresh lookup):")

            # Ensure memory cache is clear for this type
            connector._soma_sides_cache.pop(neuron_type, None)

            # Call get_soma_sides_for_type - this should trigger the optimization
            print(f"   Calling get_soma_sides_for_type('{neuron_type}')...")

            try:
                soma_sides = connector.get_soma_sides_for_type(neuron_type)
                print(f"   ✅ Got soma sides: {soma_sides}")
            except Exception as e:
                print(f"   ❌ Error: {e}")

        print(f"\n4. Cache Statistics:")
        print(f"   Soma sides hits: {connector._cache_stats['soma_sides_hits']}")
        print(f"   Soma sides misses: {connector._cache_stats['soma_sides_misses']}")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def analyze_cache_state():
    """
    Analyze current cache file state.
    """
    print(f"\n5. Cache File State Analysis:")
    print("-" * 40)

    cache_dir = Path("output/.cache")
    if not cache_dir.exists():
        print("❌ Cache directory doesn't exist")
        return

    # Count cache files
    soma_cache_files = list(cache_dir.glob("*_soma_sides.json"))
    neuron_cache_files = [f for f in cache_dir.glob("*.json")
                         if not f.name.endswith("_soma_sides.json")
                         and not f.name.endswith("_columns.json")
                         and f.name != "roi_hierarchy.json"]

    print(f"   Soma cache files (redundant): {len(soma_cache_files)}")
    print(f"   Neuron cache files (primary): {len(neuron_cache_files)}")

    if soma_cache_files:
        total_soma_size = sum(f.stat().st_size for f in soma_cache_files)
        print(f"   Redundant storage: {total_soma_size} bytes ({total_soma_size/1024:.1f}KB)")

        # Show first few soma cache files as examples
        print(f"   Example soma cache files:")
        for f in soma_cache_files[:3]:
            print(f"     - {f.name} ({f.stat().st_size} bytes)")

def show_expected_messages():
    """
    Show what messages indicate successful optimization.
    """
    print(f"\n6. Success Indicators:")
    print("-" * 30)
    print("✅ Look for these log messages:")
    print("   'Extracted soma sides from neuron cache for [TYPE]: [...]'")
    print("   'get_soma_sides_for_type([TYPE]): retrieved from neuron cache'")
    print("")
    print("❌ These messages indicate fallback to old method:")
    print("   'retrieved from persistent cache (fallback)'")
    print("   'Failed to extract soma sides from neuron cache'")
    print("")
    print("📊 Benefits of optimization:")
    print("   - Eliminates redundant file I/O operations")
    print("   - Uses already-loaded neuron cache data")
    print("   - Maintains 100% data consistency")
    print("   - Simplifies cache architecture")

if __name__ == "__main__":
    analyze_cache_state()
    test_optimization_fresh()
    show_expected_messages()
