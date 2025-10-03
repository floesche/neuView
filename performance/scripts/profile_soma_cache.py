#!/usr/bin/env python3
"""
Profile script to measure IO overhead in _load_persistent_soma_sides_cache.

This script profiles the file IO operations when loading soma sides cache files
and compares it with the neuron type cache data structure to identify redundancy.
"""

import time
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any
import cProfile
import pstats
from io import StringIO

# Add the neuview module to the path
sys.path.insert(0, "src")

from neuview.neuprint_connector import NeuPrintConnector
from neuview.cache import NeuronTypeCacheManager, NeuronTypeCacheData
from neuview.config import Config


def profile_soma_cache_loading():
    """Profile the soma cache loading process."""

    # Load config
    config = Config.load("config.yaml")

    # Initialize connector
    connector = NeuPrintConnector(config)

    # Initialize cache manager
    cache_manager = NeuronTypeCacheManager("output/.cache")

    # Get list of soma sides cache files
    cache_dir = Path("output/.cache")
    soma_cache_files = list(cache_dir.glob("*_soma_sides.json"))

    print(f"Found {len(soma_cache_files)} soma sides cache files")

    # Profile the loading process
    pr = cProfile.Profile()

    # Test neuron type
    test_type = "Dm4"

    print(f"\n=== Profiling soma cache loading for {test_type} ===")

    # Clear in-memory cache to force file loading
    connector._soma_sides_cache.clear()

    # Time the operation
    start_time = time.time()
    pr.enable()

    # This will trigger _load_persistent_soma_sides_cache
    soma_sides = connector.get_soma_sides_for_type(test_type)

    pr.disable()
    end_time = time.time()

    print(f"Soma sides for {test_type}: {soma_sides}")
    print(f"Time taken: {end_time - start_time:.4f} seconds")

    # Print profiling results
    s = StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
    ps.print_stats()

    print("\n=== Profiling Results ===")
    print(s.getvalue())

    return soma_sides


def analyze_cache_redundancy():
    """Analyze if soma sides information is already available in neuron type cache."""

    print("\n=== Analyzing Cache Redundancy ===")

    cache_manager = NeuronTypeCacheManager("output/.cache")

    # Get list of cached neuron types
    cached_types = cache_manager.list_cached_neuron_types()

    print(f"Found {len(cached_types)} cached neuron types")

    redundant_data = []

    for neuron_type in cached_types[:5]:  # Check first 5 types
        print(f"\nAnalyzing {neuron_type}...")

        # Load neuron type cache data
        all_cache_data = cache_manager.get_all_cached_data()
        cache_data = all_cache_data.get(neuron_type)

        if cache_data:
            print(f"  Soma side counts: {cache_data.soma_side_counts}")
            print(f"  Soma sides available: {cache_data.soma_sides_available}")

            # Check if there's a corresponding soma sides cache file
            cache_dir = Path("output/.cache")
            config = Config.load("config.yaml")

            import hashlib

            cache_key = f"soma_sides_{config.neuprint.server}_{config.neuprint.dataset}_{neuron_type}"
            cache_filename = (
                hashlib.md5(cache_key.encode()).hexdigest() + "_soma_sides.json"
            )
            soma_cache_file = cache_dir / cache_filename

            if soma_cache_file.exists():
                with open(soma_cache_file, "r") as f:
                    soma_cache_data = json.load(f)

                print(f"  Soma cache file exists: {soma_cache_file.name}")
                print(f"  Soma cache data: {soma_cache_data.get('soma_sides', [])}")

                # Compare data
                neuron_cache_sides = set(cache_data.soma_sides_available or [])
                soma_cache_sides = set(soma_cache_data.get("soma_sides", []))

                if neuron_cache_sides == soma_cache_sides:
                    redundant_data.append(
                        {
                            "neuron_type": neuron_type,
                            "neuron_cache_sides": list(neuron_cache_sides),
                            "soma_cache_sides": list(soma_cache_sides),
                            "redundant": True,
                        }
                    )
                    print(f"  ✅ Data is REDUNDANT - same in both caches")
                else:
                    redundant_data.append(
                        {
                            "neuron_type": neuron_type,
                            "neuron_cache_sides": list(neuron_cache_sides),
                            "soma_cache_sides": list(soma_cache_sides),
                            "redundant": False,
                        }
                    )
                    print(f"  ❌ Data DIFFERS between caches")
            else:
                print(f"  No soma cache file found")

    # Summary
    redundant_count = sum(1 for item in redundant_data if item["redundant"])
    print(f"\n=== Redundancy Analysis Summary ===")
    print(f"Total analyzed: {len(redundant_data)}")
    print(f"Redundant data: {redundant_count}")
    print(f"Different data: {len(redundant_data) - redundant_count}")

    return redundant_data


def measure_file_io_overhead():
    """Measure the file I/O overhead of reading many small cache files."""

    print("\n=== Measuring File I/O Overhead ===")

    cache_dir = Path("output/.cache")
    soma_cache_files = list(cache_dir.glob("*_soma_sides.json"))

    print(f"Found {len(soma_cache_files)} soma sides cache files")

    # Measure time to read all files
    start_time = time.time()
    total_size = 0
    successful_reads = 0
    failed_reads = 0

    for cache_file in soma_cache_files:
        try:
            with open(cache_file, "r") as f:
                data = json.load(f)

            total_size += cache_file.stat().st_size
            successful_reads += 1

        except Exception as e:
            failed_reads += 1
            print(f"  Failed to read {cache_file.name}: {e}")

    end_time = time.time()

    print(f"Time to read all files: {end_time - start_time:.4f} seconds")
    print(f"Total file size: {total_size} bytes ({total_size / 1024:.2f} KB)")
    print(f"Successful reads: {successful_reads}")
    print(f"Failed reads: {failed_reads}")
    print(f"Average file size: {total_size / max(successful_reads, 1):.2f} bytes")
    print(
        f"Time per file: {(end_time - start_time) / max(len(soma_cache_files), 1) * 1000:.2f} ms"
    )

    return {
        "total_time": end_time - start_time,
        "total_files": len(soma_cache_files),
        "total_size": total_size,
        "successful_reads": successful_reads,
        "failed_reads": failed_reads,
    }


def demonstrate_optimized_approach():
    """Demonstrate how soma sides could be retrieved from neuron type cache."""

    print("\n=== Demonstrating Optimized Approach ===")

    cache_manager = NeuronTypeCacheManager("output/.cache")
    test_type = "Dm4"

    print(f"Getting soma sides for {test_type} from neuron type cache...")

    start_time = time.time()
    all_cache_data = cache_manager.get_all_cached_data()
    cache_data = all_cache_data.get(test_type)
    end_time = time.time()

    if cache_data:
        soma_sides = cache_data.soma_sides_available or []
        print(f"Soma sides from neuron cache: {soma_sides}")
        print(f"Time taken: {end_time - start_time:.4f} seconds")

        # Compare with current approach
        print(f"\nComparing with current approach...")
        config = Config.load("config.yaml")
        connector = NeuPrintConnector(config)
        connector._soma_sides_cache.clear()  # Clear memory cache

        start_time = time.time()
        current_soma_sides = connector.get_soma_sides_for_type(test_type)
        end_time = time.time()

        print(f"Soma sides from current approach: {current_soma_sides}")
        print(f"Time taken: {end_time - start_time:.4f} seconds")

        return soma_sides == current_soma_sides
    else:
        print(f"No cache data found for {test_type}")
        return False


def main():
    """Main profiling function."""

    print("Soma Cache IO Overhead Profiling")
    print("=" * 50)

    # Check if cache directory exists
    cache_dir = Path("output/.cache")
    if not cache_dir.exists():
        print("Cache directory does not exist. Please run neuview first.")
        return

    # 1. Profile soma cache loading
    try:
        soma_sides = profile_soma_cache_loading()
    except Exception as e:
        print(f"Error during profiling: {e}")
        soma_sides = None

    # 2. Analyze cache redundancy
    redundancy_data = analyze_cache_redundancy()

    # 3. Measure file I/O overhead
    io_stats = measure_file_io_overhead()

    # 4. Demonstrate optimized approach
    optimization_works = demonstrate_optimized_approach()

    # Final summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    if io_stats:
        print(f"• Found {io_stats['total_files']} soma sides cache files")
        print(f"• Total I/O overhead: {io_stats['total_time']:.4f} seconds")
        print(f"• Failed reads: {io_stats['failed_reads']}")

    if redundancy_data:
        redundant_count = sum(1 for item in redundancy_data if item["redundant"])
        print(
            f"• Cache redundancy: {redundant_count}/{len(redundancy_data)} analyzed types have redundant data"
        )

    if optimization_works:
        print("• ✅ Soma sides can be retrieved from neuron type cache")
    else:
        print("• ❌ Soma sides data differs between caches")

    print("\nRECOMMENDATION:")
    if redundancy_data and sum(1 for item in redundancy_data if item["redundant"]) > 0:
        print("The soma sides cache appears to be redundant with neuron type cache.")
        print(
            "Consider modifying get_soma_sides_for_type() to use neuron type cache first."
        )
    else:
        print(
            "More analysis needed to determine if soma sides cache can be eliminated."
        )


if __name__ == "__main__":
    main()
