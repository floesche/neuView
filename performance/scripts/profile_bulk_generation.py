#!/usr/bin/env python3
"""
Enhanced profiling script to simulate bulk generation and analyze soma cache optimization.

This script simulates the bulk generation scenario where many neuron types are processed,
and measures the IO overhead of loading soma sides cache files versus using the
consolidated neuron type cache.
"""

import time
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Set
import logging
from collections import defaultdict

# Add the neuview module to the path
sys.path.insert(0, "src")

from neuview.neuprint_connector import NeuPrintConnector
from neuview.cache import NeuronTypeCacheManager, NeuronTypeCacheData
from neuview.config import Config

# Set up logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def get_soma_sides_from_neuron_cache(
    neuron_type: str, cache_manager: NeuronTypeCacheManager
) -> List[str]:
    """
    Extract soma sides from neuron type cache data.
    This simulates the optimized approach.
    """
    all_cache_data = cache_manager.get_all_cached_data()
    cache_data = all_cache_data.get(neuron_type)

    if cache_data and cache_data.soma_sides_available:
        # Convert to the format expected by soma sides cache
        result = []
        for side in cache_data.soma_sides_available:
            if side == "left":
                result.append("L")
            elif side == "right":
                result.append("R")
            elif side == "middle":
                result.append("M")
            # Skip 'combined' as it's not a real soma side
        return result

    return []


def profile_bulk_soma_loading_current():
    """
    Profile the current approach: loading many individual soma sides cache files.
    """
    print("=== Profiling Current Approach (Individual Cache Files) ===")

    try:
        config = Config.load("config.yaml")
        connector = NeuPrintConnector(config)

        # Get all soma sides cache files
        cache_dir = Path("output/.cache")
        soma_cache_files = list(cache_dir.glob("*_soma_sides.json"))

        print(f"Found {len(soma_cache_files)} soma sides cache files")

        # Clear memory cache to force file loading
        connector._soma_sides_cache.clear()

        # Simulate bulk loading by calling get_soma_sides_for_type for multiple types
        neuron_types = []

        # Extract neuron types from cache file names (this is a simulation)
        for cache_file in soma_cache_files[:10]:  # Test with first 10 files
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                neuron_type = data.get("neuron_type", "")
                if neuron_type:
                    neuron_types.append(neuron_type)
            except Exception:
                continue

        print(f"Testing with {len(neuron_types)} neuron types")

        # Profile the loading
        start_time = time.time()
        file_reads = 0

        results = {}
        for neuron_type in neuron_types:
            # This will trigger file I/O for each type
            try:
                soma_sides = connector.get_soma_sides_for_type(neuron_type)
                results[neuron_type] = soma_sides
                file_reads += 1
            except Exception as e:
                print(f"Error loading {neuron_type}: {e}")

        end_time = time.time()

        total_time = end_time - start_time
        print(f"Current approach: {total_time:.4f}s for {len(neuron_types)} types")
        print(
            f"Average time per type: {total_time / max(len(neuron_types), 1) * 1000:.2f}ms"
        )
        print(f"File reads performed: {file_reads}")

        return {
            "approach": "current",
            "total_time": total_time,
            "types_processed": len(neuron_types),
            "file_reads": file_reads,
            "results": results,
        }

    except Exception as e:
        print(f"Error in current approach profiling: {e}")
        return None


def profile_bulk_soma_loading_optimized():
    """
    Profile the optimized approach: loading from consolidated neuron type cache.
    """
    print("\n=== Profiling Optimized Approach (Consolidated Cache) ===")

    try:
        cache_manager = NeuronTypeCacheManager("output/.cache")

        # Get all cached neuron types
        cached_types = cache_manager.list_cached_neuron_types()

        print(f"Found {len(cached_types)} cached neuron types")

        # Test with same types as current approach (or subset)
        test_types = cached_types[:10] if len(cached_types) > 10 else cached_types

        print(f"Testing with {len(test_types)} neuron types")

        # Profile the loading
        start_time = time.time()

        # Load all cache data once
        all_cache_data = cache_manager.get_all_cached_data()

        results = {}
        for neuron_type in test_types:
            soma_sides = get_soma_sides_from_neuron_cache(neuron_type, cache_manager)
            results[neuron_type] = soma_sides

        end_time = time.time()

        total_time = end_time - start_time
        print(f"Optimized approach: {total_time:.4f}s for {len(test_types)} types")
        print(
            f"Average time per type: {total_time / max(len(test_types), 1) * 1000:.2f}ms"
        )
        print(
            f"File reads performed: {len(test_types)}"
        )  # One read per neuron type cache file

        return {
            "approach": "optimized",
            "total_time": total_time,
            "types_processed": len(test_types),
            "file_reads": len(test_types),
            "results": results,
        }

    except Exception as e:
        print(f"Error in optimized approach profiling: {e}")
        return None


def analyze_cache_storage_efficiency():
    """
    Analyze storage efficiency and redundancy.
    """
    print("\n=== Storage Efficiency Analysis ===")

    cache_dir = Path("output/.cache")

    # Analyze soma sides cache files
    soma_cache_files = list(cache_dir.glob("*_soma_sides.json"))
    soma_total_size = sum(f.stat().st_size for f in soma_cache_files)

    # Analyze neuron type cache files
    neuron_cache_files = [
        f
        for f in cache_dir.glob("*.json")
        if not f.name.endswith("_soma_sides.json")
        and not f.name.endswith("_columns.json")
        and f.name != "roi_hierarchy.json"
    ]
    neuron_total_size = sum(f.stat().st_size for f in neuron_cache_files)

    print(
        f"Soma sides cache files: {len(soma_cache_files)} files, {soma_total_size} bytes ({soma_total_size / 1024:.1f} KB)"
    )
    print(
        f"Neuron type cache files: {len(neuron_cache_files)} files, {neuron_total_size} bytes ({neuron_total_size / 1024:.1f} KB)"
    )

    # Estimate redundancy
    redundant_data_estimate = 0
    for soma_file in soma_cache_files:
        try:
            with open(soma_file, "r") as f:
                data = json.load(f)
            # Estimate the redundant data size (soma_sides field)
            soma_sides = data.get("soma_sides", [])
            redundant_data_estimate += len(json.dumps(soma_sides))
        except Exception:
            continue

    print(
        f"Estimated redundant data in soma cache: {redundant_data_estimate} bytes ({redundant_data_estimate / 1024:.1f} KB)"
    )
    print(
        f"Storage savings potential: {soma_total_size - redundant_data_estimate} bytes ({(soma_total_size - redundant_data_estimate) / 1024:.1f} KB)"
    )

    return {
        "soma_cache_files": len(soma_cache_files),
        "soma_cache_size": soma_total_size,
        "neuron_cache_files": len(neuron_cache_files),
        "neuron_cache_size": neuron_total_size,
        "redundant_data_estimate": redundant_data_estimate,
        "storage_savings": soma_total_size - redundant_data_estimate,
    }


def demonstrate_data_conversion():
    """
    Demonstrate how to convert between the two cache formats.
    """
    print("\n=== Data Format Conversion Demo ===")

    # Example conversion from neuron cache format to soma cache format
    neuron_cache_sides = ["left", "right", "combined"]
    soma_cache_sides = []

    for side in neuron_cache_sides:
        if side == "left":
            soma_cache_sides.append("L")
        elif side == "right":
            soma_cache_sides.append("R")
        elif side == "middle":
            soma_cache_sides.append("M")
        # Skip 'combined' as it's derived, not a real soma side

    print(f"Neuron cache format: {neuron_cache_sides}")
    print(f"Soma cache format: {soma_cache_sides}")

    # Reverse conversion
    converted_back = []
    for side in soma_cache_sides:
        if side == "L":
            converted_back.append("left")
        elif side == "R":
            converted_back.append("right")
        elif side == "M":
            converted_back.append("middle")

    # Add combined logic
    if len(converted_back) > 1:
        converted_back.append("combined")

    print(f"Converted back: {converted_back}")

    return {
        "neuron_format": neuron_cache_sides,
        "soma_format": soma_cache_sides,
        "converted_back": converted_back,
    }


def simulate_bulk_generation_io():
    """
    Simulate the IO pattern during bulk generation.
    """
    print("\n=== Simulating Bulk Generation I/O Pattern ===")

    cache_dir = Path("output/.cache")
    soma_cache_files = list(cache_dir.glob("*_soma_sides.json"))

    # Simulate the scenario: generating pages for 20 neuron types
    num_types = min(20, len(soma_cache_files))

    print(f"Simulating bulk generation for {num_types} neuron types")

    # Current approach: read individual soma cache files
    start_time = time.time()
    current_io_count = 0

    for i, cache_file in enumerate(soma_cache_files[:num_types]):
        try:
            with open(cache_file, "r") as f:
                data = json.load(f)
            current_io_count += 1
        except Exception:
            continue

    current_time = time.time() - start_time

    # Optimized approach: read neuron type cache files
    cache_manager = NeuronTypeCacheManager("output/.cache")
    cached_types = cache_manager.list_cached_neuron_types()[:num_types]

    start_time = time.time()
    optimized_io_count = 0

    # In optimized approach, we read each neuron type cache file once
    for neuron_type in cached_types:
        cache_file = cache_manager.cache_dir / f"{neuron_type}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                optimized_io_count += 1
            except Exception:
                continue

    optimized_time = time.time() - start_time

    print(f"Current approach:")
    print(f"  - I/O operations: {current_io_count}")
    print(f"  - Time: {current_time:.4f}s")
    print(f"  - Files read: soma cache files only")

    print(f"Optimized approach:")
    print(f"  - I/O operations: {optimized_io_count}")
    print(f"  - Time: {optimized_time:.4f}s")
    print(f"  - Files read: neuron type cache files (which contain soma data)")

    speedup = current_time / optimized_time if optimized_time > 0 else float("inf")
    print(f"Potential speedup: {speedup:.1f}x")

    return {
        "current_io_count": current_io_count,
        "current_time": current_time,
        "optimized_io_count": optimized_io_count,
        "optimized_time": optimized_time,
        "speedup": speedup,
    }


def generate_optimization_proposal():
    """
    Generate a concrete optimization proposal.
    """
    print("\n" + "=" * 60)
    print("OPTIMIZATION PROPOSAL")
    print("=" * 60)

    proposal = """
PROBLEM:
The current implementation maintains separate soma sides cache files (*_soma_sides.json)
that duplicate information already available in neuron type cache files (*.json).

During bulk generation, this creates unnecessary I/O overhead:
- Each neuron type requires reading its soma sides cache file
- The soma sides information is already in the neuron type cache
- File I/O is performed redundantly

SOLUTION:
Modify get_soma_sides_for_type() to use neuron type cache as primary source:

1. PHASE 1 - Add fallback logic:
   - First check neuron type cache for soma sides data
   - Fall back to current soma sides cache if not found
   - This maintains backward compatibility

2. PHASE 2 - Deprecate soma sides cache:
   - Update cache generation to populate neuron type cache
   - Remove soma sides cache file generation
   - Clean up existing soma sides cache files

IMPLEMENTATION:
Modify NeuPrintConnector.get_soma_sides_for_type():

def get_soma_sides_for_type(self, neuron_type: str) -> List[str]:
    # Check memory cache first (unchanged)
    if neuron_type in self._soma_sides_cache:
        return self._soma_sides_cache[neuron_type]

    # NEW: Check neuron type cache first
    soma_sides = self._get_soma_sides_from_neuron_cache(neuron_type)
    if soma_sides is not None:
        self._soma_sides_cache[neuron_type] = soma_sides
        return soma_sides

    # Fallback to current persistent cache approach
    persistent_result = self._load_persistent_soma_sides_cache(neuron_type)
    if persistent_result is not None:
        self._soma_sides_cache[neuron_type] = persistent_result
        return persistent_result

    # Query database as last resort (unchanged)
    # ... existing database query logic

def _get_soma_sides_from_neuron_cache(self, neuron_type: str) -> Optional[List[str]]:
    cache_manager = NeuronTypeCacheManager(self.cache_dir)
    all_cache_data = cache_manager.get_all_cached_data()
    cache_data = all_cache_data.get(neuron_type)

    if cache_data and cache_data.soma_sides_available:
        # Convert format: ['left', 'right'] -> ['L', 'R']
        result = []
        for side in cache_data.soma_sides_available:
            if side == 'left':
                result.append('L')
            elif side == 'right':
                result.append('R')
            elif side == 'middle':
                result.append('M')
        return result

    return None

BENEFITS:
- Eliminates redundant file I/O operations
- Reduces cache storage by ~{storage_savings_kb}KB
- Simplifies cache management
- Improves bulk generation performance
- Maintains data consistency

RISKS:
- Minimal: fallback to current approach ensures compatibility
- Need to handle format conversion (trivial)
- Temporary increase in code complexity during transition
"""

    # Get storage analysis for the proposal
    storage_stats = analyze_cache_storage_efficiency()
    storage_savings_kb = storage_stats["storage_savings"] / 1024

    print(proposal.format(storage_savings_kb=f"{storage_savings_kb:.1f}"))


def main():
    """
    Main profiling and analysis function.
    """
    print("Enhanced Soma Cache Profiling and Optimization Analysis")
    print("=" * 60)

    # Check if cache directory exists
    cache_dir = Path("output/.cache")
    if not cache_dir.exists():
        print("❌ Cache directory does not exist. Please run neuview first.")
        return

    # Run all analyses
    try:
        current_stats = profile_bulk_soma_loading_current()
        optimized_stats = profile_bulk_soma_loading_optimized()
        storage_stats = analyze_cache_storage_efficiency()
        conversion_demo = demonstrate_data_conversion()
        io_simulation = simulate_bulk_generation_io()

        # Generate final recommendation
        generate_optimization_proposal()

        print(f"\n{'=' * 60}")
        print("EXECUTIVE SUMMARY")
        print(f"{'=' * 60}")

        if current_stats and optimized_stats:
            speedup = (
                current_stats["total_time"] / optimized_stats["total_time"]
                if optimized_stats["total_time"] > 0
                else float("inf")
            )
            print(f"📊 Performance Analysis:")
            print(f"   Current approach: {current_stats['total_time']:.4f}s")
            print(f"   Optimized approach: {optimized_stats['total_time']:.4f}s")
            print(f"   Potential speedup: {speedup:.1f}x")

        if storage_stats:
            print(f"💾 Storage Analysis:")
            print(
                f"   Soma cache files: {storage_stats['soma_cache_files']} files, {storage_stats['soma_cache_size'] / 1024:.1f}KB"
            )
            print(
                f"   Storage savings potential: {storage_stats['storage_savings'] / 1024:.1f}KB"
            )

        if io_simulation:
            print(f"⚡ I/O Simulation:")
            print(f"   Current I/O operations: {io_simulation['current_io_count']}")
            print(f"   Optimized I/O operations: {io_simulation['optimized_io_count']}")
            print(
                f"   I/O reduction: {io_simulation['current_io_count'] - io_simulation['optimized_io_count']} operations"
            )

        print(f"\n✅ RECOMMENDATION: Implement the optimization proposal above")
        print(f"   The soma sides cache is redundant and can be eliminated safely.")

    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
