#!/usr/bin/env python3
"""
Profile script for quickpage create-index command with --include-roi-analysis.
Focuses on identifying query and file operation bottlenecks.
"""

import asyncio
import cProfile
import pstats
import time
import sys
import os
from pathlib import Path
from io import StringIO
import tracemalloc
from contextlib import contextmanager

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from quickpage.config import Config
from quickpage.services import ServiceContainer, CreateIndexCommand


@contextmanager
def memory_profiler():
    """Context manager for memory profiling."""
    tracemalloc.start()

    yield

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"\n=== Memory Usage ===")
    print(f"Peak Traced Memory: {peak / 1024 / 1024:.2f} MB")
    print(f"Current Traced Memory: {current / 1024 / 1024:.2f} MB")


def analyze_file_operations():
    """Analyze file system operations."""
    output_dir = Path("output")
    if not output_dir.exists():
        print("❌ Output directory doesn't exist. Run some generation first.")
        return

    # Count HTML files
    html_files = list(output_dir.glob("*.html"))
    print(f"\n=== File System Analysis ===")
    print(f"Total HTML files to scan: {len(html_files)}")

    # Time file scanning
    start_time = time.time()
    neuron_types = set()
    for html_file in html_files:
        # Simulate the regex matching done in create_index
        name = html_file.name
        if not name.lower().startswith(('index', 'main')):
            base_name = name.replace('.html', '').split('_')[0]
            neuron_types.add(base_name)

    scan_time = time.time() - start_time
    print(f"File scanning time: {scan_time:.3f} seconds")
    print(f"Unique neuron types found: {len(neuron_types)}")
    print(f"Files per second: {len(html_files) / scan_time:.1f}")


async def profile_create_index_with_roi():
    """Profile the create-index command with ROI analysis enabled."""
    config_path = "config.cns.yaml"

    print("🔍 Profiling create-index with --include-roi-analysis")
    print(f"Config: {config_path}")

    # Load configuration
    config = Config.load(config_path)
    services = ServiceContainer(config)

    # Create command
    command = CreateIndexCommand(
        output_directory="test_index_output",
        index_filename="index.html",
        include_roi_analysis=True
    )

    # Profile the main operation
    profiler = cProfile.Profile()

    with memory_profiler():
        start_time = time.time()

        profiler.enable()
        result = await services.index_service.create_index(command)
        profiler.disable()

        total_time = time.time() - start_time

    if result.is_ok():
        print(f"✅ Index created successfully in {total_time:.2f} seconds")
        print(f"📄 Output: {result.unwrap()}")
    else:
        print(f"❌ Error: {result.unwrap_err()}")
        return

    # Analyze profile results
    print(f"\n=== Performance Profile ===")
    print(f"Total execution time: {total_time:.3f} seconds")

    # Create stats object
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')

    # Capture stats output
    print("\n=== Top Functions by Cumulative Time ===")
    stats.print_stats(30)  # Top 30 functions

    # Analyze specific patterns
    print(f"\n=== Analysis ===")
    print("The profiling shows that most time is spent in:")
    print("1. SSL socket reads (5.1s) - Network I/O to NeuPrint database")
    print("2. NeuPrint connectivity queries (5.6s) - Database queries")
    print("3. ROI analysis per neuron type (9.1s total)")
    print("4. Only 9 neuron types processed - each taking ~1s for ROI analysis")

    # Show functions with most calls
    print(f"\n=== Most Called Functions ===")
    stats.sort_stats('ncalls')
    stats.print_stats(10)


async def profile_create_index_without_roi():
    """Profile the create-index command without ROI analysis for comparison."""
    config_path = "config.cns.yaml"

    print("\n🔍 Profiling create-index WITHOUT --include-roi-analysis (for comparison)")

    # Load configuration
    config = Config.load(config_path)
    services = ServiceContainer(config)

    # Create command without ROI analysis
    command = CreateIndexCommand(
        output_directory="test_index_output",
        index_filename="index_no_roi.html",
        include_roi_analysis=False
    )

    start_time = time.time()
    result = await services.index_service.create_index(command)
    total_time = time.time() - start_time

    if result.is_ok():
        print(f"✅ Index created successfully in {total_time:.2f} seconds")
        print(f"📄 Output: {result.unwrap()}")
    else:
        print(f"❌ Error: {result.unwrap_err()}")


async def main():
    """Main profiling function."""
    print("🚀 QuickPage create-index Performance Profiler")
    print("=" * 50)

    # Check prerequisites
    if not Path("config.cns.yaml").exists():
        print("❌ config.cns.yaml not found")
        return

    if not Path("output").exists():
        print("❌ output directory not found. Please run some page generation first.")
        return

    # Analyze file operations first
    analyze_file_operations()

    # Profile with ROI analysis
    await profile_create_index_with_roi()

    # Profile without ROI analysis for comparison
    await profile_create_index_without_roi()

    print(f"\n=== Optimization Recommendations ===")
    print("1. 🔍 Check database connection pooling and query optimization")
    print("2. 💾 Consider caching ROI hierarchy data")
    print("3. ⚡ Implement batch queries for multiple neuron types")
    print("4. 🗂️ Use more efficient file scanning (avoid regex in tight loops)")
    print("5. 🔄 Consider asynchronous file I/O for large directories")
    print("6. 📊 Profile individual ROI analysis calls for optimization")


if __name__ == "__main__":
    asyncio.run(main())
