#!/usr/bin/env python3
"""
Realistic bulk generation profiling that accounts for both caches being loaded.

This script provides a more accurate simulation of the bulk generation scenario
where neuron type cache files are already being read for page generation,
making the separate soma sides cache redundant.
"""

import time
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add the quickpage module to the path
sys.path.insert(0, 'src')

from quickpage.neuprint_connector import NeuPrintConnector
from quickpage.cache import NeuronTypeCacheManager, NeuronTypeCacheData
from quickpage.config import Config

# Set up logging to reduce noise
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class RealisticBulkProfiler:
    """
    Profiles the realistic bulk generation scenario where both caches are involved.
    """

    def __init__(self):
        self.config = Config.load("config.yaml")
        self.connector = NeuPrintConnector(self.config)
        self.cache_manager = NeuronTypeCacheManager("output/.cache")
        self.cache_dir = Path("output/.cache")

    def simulate_current_bulk_generation(self, neuron_types: List[str]) -> Dict[str, Any]:
        """
        Simulate current bulk generation where both caches are read separately.
        """
        print(f"🔄 Simulating CURRENT bulk generation for {len(neuron_types)} types...")

        total_start_time = time.time()

        # Phase 1: Read neuron type cache files (for page generation)
        neuron_cache_time_start = time.time()
        neuron_cache_data = {}
        neuron_cache_reads = 0

        for neuron_type in neuron_types:
            cache_file = self.cache_dir / f"{neuron_type}.json"
            if cache_file.exists():
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                    neuron_cache_data[neuron_type] = data
                    neuron_cache_reads += 1
                except Exception:
                    continue

        neuron_cache_time = time.time() - neuron_cache_time_start

        # Phase 2: Read soma sides cache files (current approach)
        self.connector._soma_sides_cache.clear()  # Force cache misses

        soma_cache_time_start = time.time()
        soma_sides_data = {}
        soma_cache_reads = 0

        for neuron_type in neuron_types:
            try:
                soma_sides = self.connector.get_soma_sides_for_type(neuron_type)
                soma_sides_data[neuron_type] = soma_sides
                soma_cache_reads += 1
            except Exception:
                continue

        soma_cache_time = time.time() - soma_cache_time_start
        total_time = time.time() - total_start_time

        return {
            'approach': 'current',
            'total_time': total_time,
            'neuron_cache_time': neuron_cache_time,
            'soma_cache_time': soma_cache_time,
            'neuron_cache_reads': neuron_cache_reads,
            'soma_cache_reads': soma_cache_reads,
            'total_cache_reads': neuron_cache_reads + soma_cache_reads,
            'neuron_cache_data': neuron_cache_data,
            'soma_sides_data': soma_sides_data
        }

    def simulate_optimized_bulk_generation(self, neuron_types: List[str]) -> Dict[str, Any]:
        """
        Simulate optimized bulk generation where soma sides are extracted from neuron cache.
        """
        print(f"⚡ Simulating OPTIMIZED bulk generation for {len(neuron_types)} types...")

        total_start_time = time.time()

        # Phase 1: Read neuron type cache files (same as current)
        neuron_cache_time_start = time.time()
        neuron_cache_data = {}
        cache_reads = 0

        for neuron_type in neuron_types:
            cache_file = self.cache_dir / f"{neuron_type}.json"
            if cache_file.exists():
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                    neuron_cache_data[neuron_type] = data
                    cache_reads += 1
                except Exception:
                    continue

        neuron_cache_time = time.time() - neuron_cache_time_start

        # Phase 2: Extract soma sides from already-loaded neuron cache data (in-memory)
        soma_extraction_start = time.time()
        soma_sides_data = {}

        for neuron_type, cache_data in neuron_cache_data.items():
            try:
                # Reconstruct NeuronTypeCacheData to access soma_sides_available
                cache_obj = NeuronTypeCacheData(**cache_data)
                soma_sides = self._convert_soma_sides_format(cache_obj.soma_sides_available)
                soma_sides_data[neuron_type] = soma_sides
            except Exception as e:
                # Fallback: extract directly from dict
                soma_sides_available = cache_data.get('soma_sides_available', [])
                soma_sides = self._convert_soma_sides_format(soma_sides_available)
                soma_sides_data[neuron_type] = soma_sides

        soma_extraction_time = time.time() - soma_extraction_start
        total_time = time.time() - total_start_time

        return {
            'approach': 'optimized',
            'total_time': total_time,
            'neuron_cache_time': neuron_cache_time,
            'soma_extraction_time': soma_extraction_time,
            'cache_reads': cache_reads,
            'total_cache_reads': cache_reads,  # No additional soma cache reads
            'neuron_cache_data': neuron_cache_data,
            'soma_sides_data': soma_sides_data
        }

    def _convert_soma_sides_format(self, soma_sides_available: List[str]) -> List[str]:
        """
        Convert from neuron cache format to soma cache format.
        ['left', 'right', 'combined'] -> ['L', 'R']
        """
        result = []
        for side in soma_sides_available or []:
            if side == 'left':
                result.append('L')
            elif side == 'right':
                result.append('R')
            elif side == 'middle':
                result.append('M')
            # Skip 'combined' as it's derived
        return result

    def analyze_io_overhead(self, neuron_types: List[str]) -> Dict[str, Any]:
        """
        Analyze the IO overhead of the current approach during bulk generation.
        """
        print(f"📊 Analyzing I/O overhead for {len(neuron_types)} neuron types...")

        # Count file operations
        neuron_cache_files = []
        soma_cache_files = []

        for neuron_type in neuron_types:
            # Neuron cache file
            neuron_cache_file = self.cache_dir / f"{neuron_type}.json"
            if neuron_cache_file.exists():
                neuron_cache_files.append(neuron_cache_file)

            # Soma cache file
            import hashlib
            cache_key = f"soma_sides_{self.config.neuprint.server}_{self.config.neuprint.dataset}_{neuron_type}"
            cache_filename = hashlib.md5(cache_key.encode()).hexdigest() + "_soma_sides.json"
            soma_cache_file = self.cache_dir / cache_filename
            if soma_cache_file.exists():
                soma_cache_files.append(soma_cache_file)

        # Calculate file sizes
        neuron_cache_size = sum(f.stat().st_size for f in neuron_cache_files)
        soma_cache_size = sum(f.stat().st_size for f in soma_cache_files)

        # Measure read times
        start_time = time.time()
        for f in neuron_cache_files:
            with open(f, 'r') as file:
                json.load(file)
        neuron_read_time = time.time() - start_time

        start_time = time.time()
        for f in soma_cache_files:
            with open(f, 'r') as file:
                json.load(file)
        soma_read_time = time.time() - start_time

        return {
            'neuron_cache_files_count': len(neuron_cache_files),
            'soma_cache_files_count': len(soma_cache_files),
            'neuron_cache_size': neuron_cache_size,
            'soma_cache_size': soma_cache_size,
            'neuron_read_time': neuron_read_time,
            'soma_read_time': soma_read_time,
            'total_files_current': len(neuron_cache_files) + len(soma_cache_files),
            'total_files_optimized': len(neuron_cache_files),
            'io_reduction': len(soma_cache_files),
            'size_reduction': soma_cache_size
        }

    def validate_data_consistency(self, current_results: Dict, optimized_results: Dict) -> Dict[str, Any]:
        """
        Validate that both approaches produce the same soma sides data.
        """
        print("🔍 Validating data consistency between approaches...")

        current_soma = current_results['soma_sides_data']
        optimized_soma = optimized_results['soma_sides_data']

        consistent_types = []
        inconsistent_types = []

        for neuron_type in current_soma:
            if neuron_type in optimized_soma:
                current_sides = set(current_soma[neuron_type])
                optimized_sides = set(optimized_soma[neuron_type])

                if current_sides == optimized_sides:
                    consistent_types.append(neuron_type)
                else:
                    inconsistent_types.append({
                        'type': neuron_type,
                        'current': list(current_sides),
                        'optimized': list(optimized_sides)
                    })

        consistency_rate = len(consistent_types) / len(current_soma) if current_soma else 0

        return {
            'total_types': len(current_soma),
            'consistent_types': len(consistent_types),
            'inconsistent_types': len(inconsistent_types),
            'consistency_rate': consistency_rate,
            'inconsistent_details': inconsistent_types[:5]  # Show first 5 for analysis
        }

    def generate_performance_report(self, current: Dict, optimized: Dict, io_analysis: Dict, consistency: Dict):
        """
        Generate a comprehensive performance report.
        """
        print("\n" + "="*80)
        print("REALISTIC BULK GENERATION PERFORMANCE REPORT")
        print("="*80)

        print(f"\n📈 PERFORMANCE COMPARISON:")
        print(f"   Current approach total time:    {current['total_time']:.4f}s")
        print(f"   Optimized approach total time:  {optimized['total_time']:.4f}s")

        if optimized['total_time'] > 0:
            speedup = current['total_time'] / optimized['total_time']
            print(f"   Performance improvement:        {speedup:.2f}x")
        else:
            print(f"   Performance improvement:        ∞x")

        print(f"\n⚡ TIME BREAKDOWN:")
        print(f"   Current - Neuron cache read:    {current['neuron_cache_time']:.4f}s")
        print(f"   Current - Soma cache read:      {current['soma_cache_time']:.4f}s")
        print(f"   Optimized - Neuron cache read:  {optimized['neuron_cache_time']:.4f}s")
        print(f"   Optimized - Soma extraction:    {optimized['soma_extraction_time']:.4f}s")

        print(f"\n💾 I/O ANALYSIS:")
        print(f"   Current approach file reads:    {current['total_cache_reads']}")
        print(f"   Optimized approach file reads:  {optimized['total_cache_reads']}")
        print(f"   I/O operations saved:           {current['total_cache_reads'] - optimized['total_cache_reads']}")
        print(f"   Storage space saved:            {io_analysis['size_reduction']/1024:.1f}KB")

        print(f"\n✅ DATA CONSISTENCY:")
        print(f"   Types analyzed:                 {consistency['total_types']}")
        print(f"   Consistent results:             {consistency['consistent_types']}")
        print(f"   Consistency rate:               {consistency['consistency_rate']*100:.1f}%")

        if consistency['inconsistent_details']:
            print(f"\n⚠️  INCONSISTENCIES FOUND:")
            for item in consistency['inconsistent_details']:
                print(f"   {item['type']}: current={item['current']}, optimized={item['optimized']}")

        # Calculate realistic savings during bulk generation
        soma_overhead = current['soma_cache_time']
        total_bulk_time = current['total_time']
        overhead_percentage = (soma_overhead / total_bulk_time * 100) if total_bulk_time > 0 else 0

        print(f"\n🎯 BULK GENERATION IMPACT:")
        print(f"   Soma cache overhead:            {soma_overhead:.4f}s ({overhead_percentage:.1f}% of total)")
        print(f"   Files eliminated:               {io_analysis['soma_cache_files_count']}")
        print(f"   Cache management simplified:     YES")

        print(f"\n💡 RECOMMENDATION:")
        if consistency['consistency_rate'] > 0.95:  # 95% consistency
            print(f"   ✅ IMPLEMENT OPTIMIZATION")
            print(f"   - High data consistency ({consistency['consistency_rate']*100:.1f}%)")
            print(f"   - Eliminates {io_analysis['io_reduction']} redundant file reads")
            print(f"   - Saves {io_analysis['size_reduction']/1024:.1f}KB storage")
            print(f"   - Simplifies cache architecture")
        else:
            print(f"   ⚠️  INVESTIGATE INCONSISTENCIES FIRST")
            print(f"   - Data consistency too low ({consistency['consistency_rate']*100:.1f}%)")
            print(f"   - Need to resolve format differences")


def main():
    """
    Main function to run realistic bulk generation profiling.
    """
    print("Realistic Bulk Generation Profiling")
    print("="*50)

    # Check cache directory
    cache_dir = Path("output/.cache")
    if not cache_dir.exists():
        print("❌ Cache directory not found. Run quickpage first.")
        return

    try:
        profiler = RealisticBulkProfiler()

        # Get list of neuron types to test with
        cached_types = profiler.cache_manager.list_cached_neuron_types()
        test_types = cached_types[:15]  # Test with 15 types for meaningful results

        if len(test_types) < 5:
            print("❌ Need at least 5 cached neuron types for meaningful analysis")
            return

        print(f"Testing with {len(test_types)} neuron types: {test_types[:5]}...")

        # Run simulations
        current_results = profiler.simulate_current_bulk_generation(test_types)
        optimized_results = profiler.simulate_optimized_bulk_generation(test_types)

        # Analyze I/O overhead
        io_analysis = profiler.analyze_io_overhead(test_types)

        # Validate consistency
        consistency = profiler.validate_data_consistency(current_results, optimized_results)

        # Generate comprehensive report
        profiler.generate_performance_report(current_results, optimized_results, io_analysis, consistency)

    except Exception as e:
        print(f"❌ Error during profiling: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
