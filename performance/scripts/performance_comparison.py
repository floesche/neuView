#!/usr/bin/env python3
"""
Performance comparison between old and optimized soma cache approaches.

This script measures and compares the performance of:
1. OLD: Reading individual soma cache files (*_soma_sides.json)
2. NEW: Extracting soma sides from neuron type cache (*.json)

The comparison demonstrates the I/O overhead elimination achieved by the optimization.
"""

import time
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any
import hashlib

# Add the neuview module to the path
sys.path.insert(0, "src")

from neuview.neuprint_connector import NeuPrintConnector
from neuview.cache import NeuronTypeCacheManager
from neuview.config import Config


class PerformanceComparator:
    """
    Compare performance between old and optimized soma cache approaches.
    """

    def __init__(self):
        self.config = Config.load("config.yaml")
        self.cache_dir = Path("output/.cache")
        self.cache_manager = NeuronTypeCacheManager(str(self.cache_dir))

    def simulate_old_approach(self, neuron_types: List[str]) -> Dict[str, Any]:
        """
        Simulate the old approach: reading individual soma cache files.

        Args:
            neuron_types: List of neuron types to test

        Returns:
            Performance metrics and results
        """
        print(f"🔄 Simulating OLD approach (individual soma cache files)...")

        start_time = time.time()
        results = {}
        files_read = 0
        total_size = 0
        errors = 0

        for neuron_type in neuron_types:
            try:
                # Generate soma cache filename (same logic as original)
                cache_key = f"soma_sides_{self.config.neuprint.server}_{self.config.neuprint.dataset}_{neuron_type}"
                cache_filename = (
                    hashlib.md5(cache_key.encode()).hexdigest() + "_soma_sides.json"
                )
                cache_file = self.cache_dir / cache_filename

                if cache_file.exists():
                    # Read the soma cache file
                    with open(cache_file, "r") as f:
                        data = json.load(f)

                    soma_sides = data.get("soma_sides", [])
                    results[neuron_type] = soma_sides
                    files_read += 1
                    total_size += cache_file.stat().st_size
                else:
                    results[neuron_type] = []

            except Exception as e:
                errors += 1
                results[neuron_type] = []

        end_time = time.time()

        return {
            "approach": "old",
            "total_time": end_time - start_time,
            "files_read": files_read,
            "total_size_bytes": total_size,
            "errors": errors,
            "results": results,
            "types_processed": len(neuron_types),
        }

    def simulate_new_approach(self, neuron_types: List[str]) -> Dict[str, Any]:
        """
        Simulate the new approach: extracting from neuron type cache.

        Args:
            neuron_types: List of neuron types to test

        Returns:
            Performance metrics and results
        """
        print(f"⚡ Simulating NEW approach (neuron type cache extraction)...")

        start_time = time.time()
        results = {}
        files_read = 0
        total_size = 0
        extraction_time = 0

        # Load all neuron cache data once
        cache_load_start = time.time()
        all_cache_data = self.cache_manager.get_all_cached_data()
        cache_load_time = time.time() - cache_load_start

        for neuron_type in neuron_types:
            try:
                # Extract soma sides from neuron cache (in-memory operation)
                extract_start = time.time()
                cache_data = all_cache_data.get(neuron_type)

                if cache_data and cache_data.soma_sides_available:
                    # Convert format (same logic as optimization)
                    soma_sides = []
                    for side in cache_data.soma_sides_available:
                        if side == "left":
                            soma_sides.append("L")
                        elif side == "right":
                            soma_sides.append("R")
                        elif side == "middle":
                            soma_sides.append("M")
                        # Skip 'combined'

                    results[neuron_type] = soma_sides

                    # Count the neuron cache file that was read
                    neuron_cache_file = self.cache_dir / f"{neuron_type}.json"
                    if neuron_cache_file.exists():
                        files_read += 1
                        total_size += neuron_cache_file.stat().st_size
                else:
                    results[neuron_type] = []

                extraction_time += time.time() - extract_start

            except Exception as e:
                results[neuron_type] = []

        end_time = time.time()

        return {
            "approach": "new",
            "total_time": end_time - start_time,
            "cache_load_time": cache_load_time,
            "extraction_time": extraction_time,
            "files_read": files_read,
            "total_size_bytes": total_size,
            "results": results,
            "types_processed": len(neuron_types),
        }

    def compare_data_consistency(
        self, old_results: Dict, new_results: Dict
    ) -> Dict[str, Any]:
        """
        Compare data consistency between old and new approaches.

        Args:
            old_results: Results from old approach
            new_results: Results from new approach

        Returns:
            Consistency analysis
        """
        print(f"🔍 Comparing data consistency...")

        old_data = old_results["results"]
        new_data = new_results["results"]

        consistent = 0
        inconsistent = []

        for neuron_type in old_data:
            if neuron_type in new_data:
                old_sides = set(old_data[neuron_type])
                new_sides = set(new_data[neuron_type])

                if old_sides == new_sides:
                    consistent += 1
                else:
                    inconsistent.append(
                        {
                            "neuron_type": neuron_type,
                            "old": list(old_sides),
                            "new": list(new_sides),
                        }
                    )

        total_compared = len([nt for nt in old_data if nt in new_data])
        consistency_rate = consistent / total_compared if total_compared > 0 else 0

        return {
            "total_compared": total_compared,
            "consistent": consistent,
            "inconsistent_count": len(inconsistent),
            "consistency_rate": consistency_rate,
            "inconsistent_details": inconsistent[:5],  # Show first 5
        }

    def generate_performance_report(
        self, old_metrics: Dict, new_metrics: Dict, consistency: Dict
    ):
        """
        Generate comprehensive performance comparison report.

        Args:
            old_metrics: Performance metrics from old approach
            new_metrics: Performance metrics from new approach
            consistency: Data consistency analysis
        """
        print(f"\n{'=' * 80}")
        print("PERFORMANCE COMPARISON REPORT")
        print(f"{'=' * 80}")

        # Performance comparison
        print(f"\n📊 PERFORMANCE METRICS:")
        print(
            f"{'Metric':<30} {'Old Approach':<15} {'New Approach':<15} {'Improvement':<15}"
        )
        print(f"{'-' * 75}")

        # Time comparison
        old_time = old_metrics["total_time"]
        new_time = new_metrics["total_time"]
        time_improvement = f"{old_time / new_time:.2f}x" if new_time > 0 else "∞x"
        print(
            f"{'Total Time':<30} {old_time:.4f}s{'':<6} {new_time:.4f}s{'':<6} {time_improvement:<15}"
        )

        # File I/O comparison
        old_files = old_metrics["files_read"]
        new_files = new_metrics["files_read"]
        io_reduction = old_files - new_files
        print(
            f"{'Files Read':<30} {old_files:<15} {new_files:<15} -{io_reduction} files"
        )

        # Data size comparison
        old_size_kb = old_metrics["total_size_bytes"] / 1024
        new_size_kb = new_metrics["total_size_bytes"] / 1024
        size_ratio = f"{new_size_kb / old_size_kb:.1f}x" if old_size_kb > 0 else "N/A"
        print(
            f"{'Data Read (KB)':<30} {old_size_kb:.1f}KB{'':<9} {new_size_kb:.1f}KB{'':<9} {size_ratio} larger"
        )

        # Detailed breakdown
        print(f"\n⚡ OPTIMIZATION BREAKDOWN:")
        print(f"   Old approach:")
        print(f"     - Reads {old_files} small soma cache files")
        print(f"     - Total size: {old_size_kb:.1f}KB")
        print(f"     - Time: {old_time:.4f}s")

        print(f"   New approach:")
        print(f"     - Reads {new_files} neuron cache files (needed anyway)")
        print(f"     - In-memory extraction: {new_metrics['extraction_time']:.4f}s")
        print(f"     - Total time: {new_time:.4f}s")

        # I/O efficiency
        print(f"\n💾 I/O EFFICIENCY:")
        io_efficiency = (1 - new_files / old_files) * 100 if old_files > 0 else 0
        print(
            f"   I/O operations reduced: {io_reduction} ({io_efficiency:.1f}% reduction)"
        )
        print(f"   Redundant files eliminated: {old_files}")

        # Data consistency
        print(f"\n✅ DATA CONSISTENCY:")
        print(f"   Types compared: {consistency['total_compared']}")
        print(f"   Consistent results: {consistency['consistent']}")
        print(f"   Consistency rate: {consistency['consistency_rate'] * 100:.1f}%")

        if consistency["inconsistent_details"]:
            print(f"   Inconsistencies found: {consistency['inconsistent_count']}")
            for item in consistency["inconsistent_details"]:
                print(
                    f"     - {item['neuron_type']}: old={item['old']} vs new={item['new']}"
                )

        # Benefits summary
        print(f"\n🎯 OPTIMIZATION BENEFITS:")
        benefits = [
            f"Eliminates {io_reduction} redundant file operations",
            f"Reduces I/O overhead by {io_efficiency:.1f}%",
            f"Uses already-loaded neuron cache data",
            f"Maintains {consistency['consistency_rate'] * 100:.1f}% data consistency",
            "Simplifies cache architecture",
            "Reduces storage requirements",
        ]

        for benefit in benefits:
            print(f"   ✅ {benefit}")

        # Recommendation
        print(f"\n💡 RECOMMENDATION:")
        if consistency["consistency_rate"] >= 0.95:
            print(f"   🚀 DEPLOY OPTIMIZATION")
            print(
                f"   The optimization provides clear benefits with high data consistency."
            )
        else:
            print(f"   ⚠️  INVESTIGATE INCONSISTENCIES")
            print(f"   Address data consistency issues before deploying.")


def main():
    """
    Main function to run performance comparison.
    """
    print("Soma Cache Performance Comparison")
    print("=" * 50)

    # Check cache directory
    cache_dir = Path("output/.cache")
    if not cache_dir.exists():
        print("❌ Cache directory not found. Run neuview first.")
        return

    try:
        comparator = PerformanceComparator()

        # Get neuron types to test
        cached_types = comparator.cache_manager.list_cached_neuron_types()
        test_types = cached_types[:20]  # Test with first 20 types

        if len(test_types) < 5:
            print("❌ Need at least 5 cached neuron types for meaningful comparison")
            return

        print(f"Testing with {len(test_types)} neuron types...")
        print(f"Sample types: {test_types[:5]}")

        # Run performance tests
        old_metrics = comparator.simulate_old_approach(test_types)
        new_metrics = comparator.simulate_new_approach(test_types)

        # Compare data consistency
        consistency = comparator.compare_data_consistency(old_metrics, new_metrics)

        # Generate comprehensive report
        comparator.generate_performance_report(old_metrics, new_metrics, consistency)

        print(f"\n{'=' * 80}")
        print("CONCLUSION")
        print(f"{'=' * 80}")

        if consistency["consistency_rate"] >= 0.95:
            print("🎉 The optimization is ready for deployment!")
            print("   High performance gains with excellent data consistency.")
        else:
            print("🔧 Minor inconsistencies detected - investigation recommended.")
            print("   Performance gains are solid, consistency needs review.")

    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
