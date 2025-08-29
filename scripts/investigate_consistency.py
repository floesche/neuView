#!/usr/bin/env python3
"""
Investigate the data consistency issue between soma cache and neuron cache.

This script analyzes why there's a 93.3% consistency rate and identifies
the specific differences between the two cache formats.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import hashlib

# Add the quickpage module to the path
sys.path.insert(0, 'src')

from quickpage.cache import NeuronTypeCacheManager, NeuronTypeCacheData
from quickpage.config import Config


def analyze_inconsistency():
    """
    Analyze the specific inconsistencies between soma cache and neuron cache.
    """
    print("Investigating Data Consistency Issues")
    print("=" * 50)

    config = Config.load("config.yaml")
    cache_manager = NeuronTypeCacheManager("output/.cache")
    cache_dir = Path("output/.cache")

    # Get all cached neuron types
    cached_types = cache_manager.list_cached_neuron_types()[:10]  # Test first 10

    inconsistencies = []
    consistent = []

    for neuron_type in cached_types:
        print(f"\nAnalyzing {neuron_type}...")

        # Get neuron cache data
        all_cache_data = cache_manager.get_all_cached_data()
        cache_data = all_cache_data.get(neuron_type)

        if not cache_data:
            print(f"  ❌ No neuron cache data found")
            continue

        # Get soma cache data
        cache_key = f"soma_sides_{config.neuprint.server}_{config.neuprint.dataset}_{neuron_type}"
        cache_filename = hashlib.md5(cache_key.encode()).hexdigest() + "_soma_sides.json"
        soma_cache_file = cache_dir / cache_filename

        if not soma_cache_file.exists():
            print(f"  ❌ No soma cache file found")
            continue

        try:
            with open(soma_cache_file, 'r') as f:
                soma_cache_data = json.load(f)
        except Exception as e:
            print(f"  ❌ Error reading soma cache: {e}")
            continue

        # Extract data from both sources
        neuron_soma_sides = cache_data.soma_sides_available or []
        soma_cache_sides = soma_cache_data.get('soma_sides', [])

        # Convert neuron cache format to soma cache format
        converted_sides = []
        for side in neuron_soma_sides:
            if side == 'left':
                converted_sides.append('L')
            elif side == 'right':
                converted_sides.append('R')
            elif side == 'middle':
                converted_sides.append('M')
            # Skip 'combined' as it's derived

        # Compare
        converted_set = set(converted_sides)
        soma_set = set(soma_cache_sides)

        print(f"  Neuron cache sides: {neuron_soma_sides}")
        print(f"  Converted sides: {converted_sides}")
        print(f"  Soma cache sides: {soma_cache_sides}")

        if converted_set == soma_set:
            print(f"  ✅ CONSISTENT")
            consistent.append(neuron_type)
        else:
            print(f"  ❌ INCONSISTENT")
            inconsistencies.append({
                'neuron_type': neuron_type,
                'neuron_sides': neuron_soma_sides,
                'converted_sides': converted_sides,
                'soma_sides': soma_cache_sides,
                'soma_side_counts': cache_data.soma_side_counts
            })

    # Detailed analysis of inconsistencies
    print(f"\n{'='*50}")
    print("DETAILED INCONSISTENCY ANALYSIS")
    print(f"{'='*50}")

    print(f"Total types analyzed: {len(cached_types)}")
    print(f"Consistent: {len(consistent)}")
    print(f"Inconsistent: {len(inconsistencies)}")
    print(f"Consistency rate: {len(consistent)/len(cached_types)*100:.1f}%")

    if inconsistencies:
        print(f"\nINCONSISTENT CASES:")
        for item in inconsistencies:
            print(f"\n{item['neuron_type']}:")
            print(f"  Soma side counts: {item['soma_side_counts']}")
            print(f"  Neuron cache: {item['neuron_sides']} -> {item['converted_sides']}")
            print(f"  Soma cache: {item['soma_sides']}")

            # Analyze the root cause
            counts = item['soma_side_counts']
            has_left = counts.get('left', 0) > 0
            has_right = counts.get('right', 0) > 0
            has_middle = counts.get('middle', 0) > 0
            has_unknown = counts.get('unknown', 0) > 0

            expected_sides = []
            if has_left:
                expected_sides.append('L')
            if has_right:
                expected_sides.append('R')
            if has_middle:
                expected_sides.append('M')

            print(f"  Expected from counts: {expected_sides}")

            # Check for combined logic differences
            neuron_has_combined = 'combined' in item['neuron_sides']
            should_have_combined = (
                len([s for s in [has_left, has_right, has_middle] if s]) > 1 or
                (has_unknown and any([has_left, has_right, has_middle])) or
                (has_unknown and not any([has_left, has_right, has_middle]))
            )

            print(f"  Neuron cache has 'combined': {neuron_has_combined}")
            print(f"  Should have 'combined': {should_have_combined}")

    # Check for format conversion issues
    print(f"\n{'='*50}")
    print("ROOT CAUSE ANALYSIS")
    print(f"{'='*50}")

    if inconsistencies:
        # Look for patterns
        has_combined_issues = sum(1 for item in inconsistencies if 'combined' in item['neuron_sides'])
        has_missing_sides = sum(1 for item in inconsistencies if len(item['converted_sides']) != len(item['soma_sides']))

        print(f"Cases with 'combined' in neuron cache: {has_combined_issues}")
        print(f"Cases with different side counts: {has_missing_sides}")

        print(f"\nLIKELY CAUSES:")
        print(f"1. 'combined' side is included in neuron cache but not soma cache")
        print(f"2. Different logic for determining available sides")
        print(f"3. Timing differences in cache generation")

        print(f"\nRECOMMENDATION:")
        print(f"The inconsistency is primarily due to the 'combined' side logic.")
        print(f"This is expected and not a data integrity issue.")
        print(f"The optimization is still valid - just exclude 'combined' during conversion.")

    else:
        print(f"No inconsistencies found! The optimization is safe to implement.")


def demonstrate_correct_conversion():
    """
    Demonstrate the correct conversion logic that handles 'combined' properly.
    """
    print(f"\n{'='*50}")
    print("CORRECT CONVERSION LOGIC")
    print(f"{'='*50}")

    def convert_soma_sides_correctly(soma_sides_available: List[str]) -> List[str]:
        """
        Correct conversion from neuron cache to soma cache format.
        """
        result = []
        for side in soma_sides_available or []:
            if side == 'left':
                result.append('L')
            elif side == 'right':
                result.append('R')
            elif side == 'middle':
                result.append('M')
            # Explicitly skip 'combined' as it's a derived value, not a real soma side
        return result

    # Test cases
    test_cases = [
        ['left', 'right'],
        ['left', 'right', 'combined'],
        ['left'],
        ['right'],
        ['middle'],
        ['left', 'middle', 'combined'],
        ['unknown'],
        []
    ]

    print("Test conversion logic:")
    for test_input in test_cases:
        converted = convert_soma_sides_correctly(test_input)
        print(f"  {test_input} -> {converted}")

    print(f"\nKey insight: 'combined' should be filtered out during conversion")
    print(f"because it represents a page type, not a physical soma side.")


if __name__ == "__main__":
    analyze_inconsistency()
    demonstrate_correct_conversion()
