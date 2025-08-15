#!/usr/bin/env python3
"""
Benchmark script to compare optimized vs original create-index performance.
Tests both with and without ROI analysis to measure optimization impact.
"""

import asyncio
import time
import sys
from pathlib import Path
from typing import Dict, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from quickpage.config import Config
from quickpage.services import ServiceContainer, CreateIndexCommand
from quickpage.optimized_index_service import OptimizedIndexService


class PerformanceBenchmark:
    """Performance benchmark for create-index optimization."""

    def __init__(self, config_path: str = "config.cns.yaml"):
        self.config_path = config_path
        self.config = Config.load(config_path)
        self.results = {}

    async def benchmark_original_with_roi(self) -> Dict[str, float]:
        """Benchmark original implementation with ROI analysis."""
        print("🔍 Benchmarking ORIGINAL implementation WITH ROI analysis...")

        services = ServiceContainer(self.config)
        command = CreateIndexCommand(
            output_directory="benchmark_output",
            index_filename="index_original_roi.html",
            include_roi_analysis=True
        )

        start_time = time.time()
        result = await services.index_service.create_index(command)
        total_time = time.time() - start_time

        success = result.is_ok()
        if success:
            print(f"✅ Original with ROI: {total_time:.2f}s")
        else:
            print(f"❌ Original with ROI failed: {result.unwrap_err()}")

        return {
            'time': total_time,
            'success': success,
            'error': None if success else result.unwrap_err()
        }

    async def benchmark_original_without_roi(self) -> Dict[str, float]:
        """Benchmark original implementation without ROI analysis."""
        print("🔍 Benchmarking ORIGINAL implementation WITHOUT ROI analysis...")

        services = ServiceContainer(self.config)
        command = CreateIndexCommand(
            output_directory="benchmark_output",
            index_filename="index_original_no_roi.html",
            include_roi_analysis=False
        )

        start_time = time.time()
        result = await services.index_service.create_index(command)
        total_time = time.time() - start_time

        success = result.is_ok()
        if success:
            print(f"✅ Original without ROI: {total_time:.2f}s")
        else:
            print(f"❌ Original without ROI failed: {result.unwrap_err()}")

        return {
            'time': total_time,
            'success': success,
            'error': None if success else result.unwrap_err()
        }

    async def benchmark_optimized_with_roi(self) -> Dict[str, float]:
        """Benchmark optimized implementation with ROI analysis."""
        print("🚀 Benchmarking OPTIMIZED implementation WITH ROI analysis...")

        services = ServiceContainer(self.config)
        optimized_service = OptimizedIndexService(self.config, services.page_generator)

        command = CreateIndexCommand(
            output_directory="benchmark_output",
            index_filename="index_optimized_roi.html",
            include_roi_analysis=True
        )

        start_time = time.time()
        result = await optimized_service.create_index_optimized(command)
        total_time = time.time() - start_time

        success = result.is_ok()
        if success:
            print(f"✅ Optimized with ROI: {total_time:.2f}s")
            # Print cache stats
            cache_stats = optimized_service.get_cache_stats()
            print(f"   Cache stats: {cache_stats}")
        else:
            print(f"❌ Optimized with ROI failed: {result.unwrap_err()}")

        return {
            'time': total_time,
            'success': success,
            'error': None if success else result.unwrap_err(),
            'cache_stats': optimized_service.get_cache_stats() if success else None
        }

    async def benchmark_optimized_without_roi(self) -> Dict[str, float]:
        """Benchmark optimized implementation without ROI analysis."""
        print("🚀 Benchmarking OPTIMIZED implementation WITHOUT ROI analysis...")

        services = ServiceContainer(self.config)
        optimized_service = OptimizedIndexService(self.config, services.page_generator)

        command = CreateIndexCommand(
            output_directory="benchmark_output",
            index_filename="index_optimized_no_roi.html",
            include_roi_analysis=False
        )

        start_time = time.time()
        result = await optimized_service.create_index_optimized(command)
        total_time = time.time() - start_time

        success = result.is_ok()
        if success:
            print(f"✅ Optimized without ROI: {total_time:.2f}s")
        else:
            print(f"❌ Optimized without ROI failed: {result.unwrap_err()}")

        return {
            'time': total_time,
            'success': success,
            'error': None if success else result.unwrap_err()
        }

    def analyze_file_operations(self):
        """Analyze file system operations for context."""
        output_dir = Path("output")
        if not output_dir.exists():
            print("❌ Output directory doesn't exist")
            return

        html_files = list(output_dir.glob("*.html"))
        neuron_types = set()

        start_time = time.time()
        for html_file in html_files:
            name = html_file.name
            if not name.lower().startswith(('index', 'main')):
                base_name = name.replace('.html', '').split('_')[0]
                neuron_types.add(base_name)
        scan_time = time.time() - start_time

        print(f"\n📊 File System Analysis:")
        print(f"   Total HTML files: {len(html_files):,}")
        print(f"   Unique neuron types: {len(neuron_types):,}")
        print(f"   File scan time: {scan_time:.3f}s")
        print(f"   Files per second: {len(html_files)/scan_time:,.0f}")

    async def run_full_benchmark(self) -> Dict[str, Dict]:
        """Run complete benchmark suite."""
        print("🏁 Starting Performance Benchmark")
        print("=" * 60)

        # Analyze file operations first
        self.analyze_file_operations()

        # Create benchmark output directory
        Path("benchmark_output").mkdir(exist_ok=True)

        # Run all benchmarks
        results = {}

        try:
            # Original implementations
            results['original_with_roi'] = await self.benchmark_original_with_roi()
            print()

            results['original_without_roi'] = await self.benchmark_original_without_roi()
            print()

            # Optimized implementations
            results['optimized_with_roi'] = await self.benchmark_optimized_with_roi()
            print()

            results['optimized_without_roi'] = await self.benchmark_optimized_without_roi()
            print()

        except Exception as e:
            print(f"❌ Benchmark failed: {e}")
            return results

        # Calculate improvements
        self.print_performance_analysis(results)

        return results

    def print_performance_analysis(self, results: Dict[str, Dict]):
        """Print detailed performance analysis."""
        print("📈 Performance Analysis")
        print("=" * 60)

        # Check if we have valid results
        orig_roi = results.get('original_with_roi', {})
        orig_no_roi = results.get('original_without_roi', {})
        opt_roi = results.get('optimized_with_roi', {})
        opt_no_roi = results.get('optimized_without_roi', {})

        print(f"{'Scenario':<30} {'Time (s)':<12} {'Status':<10}")
        print("-" * 60)

        # Original results
        if orig_roi.get('success'):
            print(f"{'Original WITH ROI':<30} {orig_roi['time']:<12.2f} {'✅ Success':<10}")
        else:
            print(f"{'Original WITH ROI':<30} {'N/A':<12} {'❌ Failed':<10}")

        if orig_no_roi.get('success'):
            print(f"{'Original WITHOUT ROI':<30} {orig_no_roi['time']:<12.2f} {'✅ Success':<10}")
        else:
            print(f"{'Original WITHOUT ROI':<30} {'N/A':<12} {'❌ Failed':<10}")

        # Optimized results
        if opt_roi.get('success'):
            print(f"{'Optimized WITH ROI':<30} {opt_roi['time']:<12.2f} {'✅ Success':<10}")
        else:
            print(f"{'Optimized WITH ROI':<30} {'N/A':<12} {'❌ Failed':<10}")

        if opt_no_roi.get('success'):
            print(f"{'Optimized WITHOUT ROI':<30} {opt_no_roi['time']:<12.2f} {'✅ Success':<10}")
        else:
            print(f"{'Optimized WITHOUT ROI':<30} {'N/A':<12} {'❌ Failed':<10}")

        print()

        # Calculate improvements
        print("🎯 Performance Improvements")
        print("-" * 40)

        if orig_roi.get('success') and opt_roi.get('success'):
            improvement = ((orig_roi['time'] - opt_roi['time']) / orig_roi['time']) * 100
            speedup = orig_roi['time'] / opt_roi['time']
            print(f"WITH ROI Analysis:")
            print(f"  Original: {orig_roi['time']:.2f}s → Optimized: {opt_roi['time']:.2f}s")
            print(f"  Improvement: {improvement:.1f}% faster ({speedup:.1f}x speedup)")
            print()

        if orig_no_roi.get('success') and opt_no_roi.get('success'):
            improvement = ((orig_no_roi['time'] - opt_no_roi['time']) / orig_no_roi['time']) * 100
            speedup = orig_no_roi['time'] / opt_no_roi['time']
            print(f"WITHOUT ROI Analysis:")
            print(f"  Original: {orig_no_roi['time']:.2f}s → Optimized: {opt_no_roi['time']:.2f}s")
            print(f"  Improvement: {improvement:.1f}% faster ({speedup:.1f}x speedup)")
            print()

        # ROI impact analysis
        if orig_roi.get('success') and orig_no_roi.get('success'):
            roi_overhead_orig = orig_roi['time'] / orig_no_roi['time']
            print(f"ROI Analysis Impact (Original): {roi_overhead_orig:.1f}x slower")

        if opt_roi.get('success') and opt_no_roi.get('success'):
            roi_overhead_opt = opt_roi['time'] / opt_no_roi['time']
            print(f"ROI Analysis Impact (Optimized): {roi_overhead_opt:.1f}x slower")

        print()
        print("💡 Key Insights:")
        print("   • Network I/O to NeuPrint database is the main bottleneck")
        print("   • ROI analysis adds significant overhead due to database queries")
        print("   • Batch queries and enhanced caching should reduce round trips")
        print("   • File scanning is already very fast and not a bottleneck")

    async def stress_test(self, iterations: int = 3):
        """Run stress test with multiple iterations."""
        print(f"🏋️ Stress Test - {iterations} iterations")
        print("=" * 50)

        original_times = []
        optimized_times = []

        for i in range(iterations):
            print(f"\nIteration {i+1}/{iterations}")
            print("-" * 30)

            # Test original
            result_orig = await self.benchmark_original_with_roi()
            if result_orig['success']:
                original_times.append(result_orig['time'])

            # Test optimized
            result_opt = await self.benchmark_optimized_with_roi()
            if result_opt['success']:
                optimized_times.append(result_opt['time'])

        # Calculate statistics
        if original_times and optimized_times:
            orig_avg = sum(original_times) / len(original_times)
            opt_avg = sum(optimized_times) / len(optimized_times)

            print(f"\n📊 Stress Test Results:")
            print(f"Original average: {orig_avg:.2f}s (runs: {len(original_times)})")
            print(f"Optimized average: {opt_avg:.2f}s (runs: {len(optimized_times)})")

            if orig_avg > 0:
                improvement = ((orig_avg - opt_avg) / orig_avg) * 100
                print(f"Average improvement: {improvement:.1f}%")


async def main():
    """Main benchmark function."""
    if not Path("config.cns.yaml").exists():
        print("❌ config.cns.yaml not found")
        return

    if not Path("output").exists():
        print("❌ output directory not found. Please run some page generation first.")
        return

    benchmark = PerformanceBenchmark()

    # Run full benchmark
    results = await benchmark.run_full_benchmark()

    # Optionally run stress test
    print("\n" + "="*60)
    stress_choice = input("Run stress test? (y/N): ").lower().strip()
    if stress_choice in ['y', 'yes']:
        await benchmark.stress_test(3)


if __name__ == "__main__":
    asyncio.run(main())
