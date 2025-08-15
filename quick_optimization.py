#!/usr/bin/env python3
"""
Quick optimization script for immediate performance improvements.
Implements the quick wins identified in the performance analysis.
"""

import asyncio
import time
import logging
import sys
import re
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from collections import defaultdict

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from quickpage.config import Config
from quickpage.services import ServiceContainer, CreateIndexCommand
from quickpage.result import Result, Ok, Err

logger = logging.getLogger(__name__)


class QuickOptimizedIndexService:
    """
    Quick optimization implementation with immediate performance improvements.
    Focuses on the most impactful changes with minimal code changes.
    """

    def __init__(self, config, page_generator):
        self.config = config
        self.page_generator = page_generator

        # Quick optimization caches
        self._roi_hierarchy_cache = None
        self._batch_cache = {}
        self._timing_stats = {}

    def _log_timing(self, operation: str, duration: float):
        """Log timing information for performance monitoring."""
        logger.info(f"⏱️  {operation}: {duration:.3f}s")
        self._timing_stats[operation] = duration

    async def create_index_quick_optimized(self, command: CreateIndexCommand) -> Result[str, str]:
        """
        Quick optimized version focusing on immediate wins:
        1. Increased concurrency (50 → 200)
        2. Basic caching for ROI hierarchy
        3. Optimized file scanning
        4. Better error handling and progress logging
        """
        total_start = time.time()

        try:
            logger.info("🚀 Starting quick-optimized index creation")

            # Determine output directory
            output_dir = Path(command.output_directory or self.config.output.directory)
            if not output_dir.exists():
                return Err(f"Output directory does not exist: {output_dir}")

            # OPTIMIZATION 1: Faster file scanning with pre-compiled regex
            scan_start = time.time()
            neuron_types = self._scan_files_optimized(output_dir)
            self._log_timing("File scanning", time.time() - scan_start)

            if not neuron_types:
                return Err("No neuron type HTML files found in output directory")

            logger.info(f"📊 Found {len(neuron_types)} unique neuron types from {sum(len(sides) for sides in neuron_types.values())} files")

            # OPTIMIZATION 2: Initialize connector with caching
            connector = None
            if command.include_roi_analysis:
                init_start = time.time()
                connector = self._initialize_connector_with_cache()
                self._log_timing("Connector initialization", time.time() - init_start)

            # OPTIMIZATION 3: Process with higher concurrency and batching
            process_start = time.time()
            index_data = await self._process_neuron_types_optimized(
                neuron_types, connector, command.include_roi_analysis
            )
            self._log_timing("Neuron processing", time.time() - process_start)

            # Sort and group results
            index_data.sort(key=lambda x: x['name'])
            grouped_data = self._group_by_parent_roi(index_data)

            # Generate template data and render
            render_start = time.time()
            template_data = {
                'config': self.config,
                'neuron_types': index_data,
                'grouped_neuron_types': grouped_data,
                'total_types': len(index_data),
                'generation_time': command.requested_at
            }

            template = self.page_generator.env.get_template('index_page.html')
            html_content = template.render(template_data)

            # Write files
            index_path = output_dir / command.index_filename
            index_path.write_text(html_content, encoding='utf-8')

            # Generate search JS
            await self._generate_search_js(output_dir, index_data, command.requested_at)
            self._log_timing("Template rendering & file writing", time.time() - render_start)

            total_time = time.time() - total_start
            logger.info(f"✅ Quick-optimized index creation completed in {total_time:.2f}s")

            # Log performance summary
            self._log_performance_summary()

            return Ok(str(index_path))

        except Exception as e:
            logger.error(f"❌ Quick-optimized index creation failed: {e}")
            return Err(f"Failed to create index: {str(e)}")

    def _scan_files_optimized(self, output_dir: Path) -> Dict[str, Set[str]]:
        """
        OPTIMIZATION 1: Optimized file scanning with pre-compiled regex.
        From profiling: File scanning is fast but can be improved.
        """
        neuron_types = defaultdict(set)

        # Pre-compile regex for better performance
        html_pattern = re.compile(r'^([A-Za-z0-9_+\-\.,&()\']+?)(?:_([LRM]))?\.html$')
        skip_patterns = {'index', 'main'}

        # Use iterator for memory efficiency with large directories
        for html_file in output_dir.glob('*.html'):
            match = html_pattern.match(html_file.name)
            if match:
                base_name = match.group(1)
                soma_side = match.group(2)

                # Quick skip check
                if base_name.lower() in skip_patterns:
                    continue

                if soma_side:
                    neuron_types[base_name].add(soma_side)
                else:
                    neuron_types[base_name].add('both')

        return neuron_types

    def _initialize_connector_with_cache(self):
        """
        OPTIMIZATION 2: Initialize connector and pre-load ROI hierarchy cache.
        """
        try:
            from quickpage.neuprint_connector import NeuPrintConnector
            connector = NeuPrintConnector(self.config)

            # Pre-load ROI hierarchy to cache
            if not self._roi_hierarchy_cache:
                cache_start = time.time()
                # Use existing method but cache result
                from quickpage.services import IndexService
                temp_service = IndexService(self.config, self.page_generator)
                self._roi_hierarchy_cache = temp_service._get_roi_hierarchy_cached(connector)
                cache_time = time.time() - cache_start
                logger.info(f"🗃️  ROI hierarchy cached in {cache_time:.3f}s")

            return connector
        except Exception as e:
            logger.warning(f"⚠️  Failed to initialize connector: {e}")
            return None

    async def _process_neuron_types_optimized(self, neuron_types: Dict[str, Set[str]],
                                            connector, include_roi_analysis: bool) -> List[Dict]:
        """
        OPTIMIZATION 3: Process neuron types with higher concurrency and better batching.
        Key changes:
        - Increased semaphore from 50 to 200
        - Better error handling
        - Progress logging
        - Batch size optimization
        """
        logger.info(f"🔄 Processing {len(neuron_types)} neuron types with optimized concurrency")

        # OPTIMIZATION: Higher concurrency for I/O-bound operations
        # From profiling: Network I/O is the bottleneck, so more concurrency helps
        semaphore = asyncio.Semaphore(200)  # Increased from default 50

        async def process_single_with_semaphore(neuron_type: str, sides: Set[str]):
            async with semaphore:
                return await self._process_single_neuron_type_quick(
                    neuron_type, sides, connector, include_roi_analysis
                )

        # Create tasks for all neuron types
        tasks = [
            process_single_with_semaphore(neuron_type, sides)
            for neuron_type, sides in neuron_types.items()
        ]

        # Process in batches with progress logging
        batch_size = 500  # Process in smaller batches for progress updates
        results = []

        for i in range(0, len(tasks), batch_size):
            batch_start = time.time()
            batch_tasks = tasks[i:i + batch_size]

            logger.info(f"📈 Processing batch {i//batch_size + 1}/{(len(tasks) + batch_size - 1)//batch_size} "
                       f"({len(batch_tasks)} types)")

            # Execute batch with exception handling
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # Filter successful results and log errors
            successful_results = []
            error_count = 0

            for result in batch_results:
                if isinstance(result, Exception):
                    error_count += 1
                    logger.warning(f"⚠️  Error processing neuron type: {result}")
                else:
                    successful_results.append(result)

            results.extend(successful_results)

            batch_time = time.time() - batch_start
            logger.info(f"✅ Batch completed in {batch_time:.2f}s "
                       f"(success: {len(successful_results)}, errors: {error_count})")

        logger.info(f"🎯 Successfully processed {len(results)} neuron types")
        return results

    async def _process_single_neuron_type_quick(self, neuron_type: str, sides: Set[str],
                                              connector, include_roi_analysis: bool) -> Dict:
        """
        OPTIMIZATION 4: Optimized single neuron type processing with better caching.
        """
        # Determine file availability quickly
        has_both = 'both' in sides
        has_left = 'L' in sides
        has_right = 'R' in sides
        has_middle = 'M' in sides

        # Get ROI information with optimized caching
        roi_summary = []
        parent_roi = ""

        if connector and include_roi_analysis:
            # Use cached data when possible
            cache_key = f"roi_summary_{neuron_type}"
            if cache_key in self._batch_cache:
                roi_summary, parent_roi = self._batch_cache[cache_key]
            else:
                try:
                    roi_summary, parent_roi = self._get_roi_summary_cached(
                        neuron_type, connector
                    )
                    # Cache for future use
                    self._batch_cache[cache_key] = (roi_summary, parent_roi)
                except Exception as e:
                    logger.debug(f"⚠️  ROI analysis failed for {neuron_type}: {e}")
                    roi_summary, parent_roi = [], ""

        return {
            'name': neuron_type,
            'has_both': has_both,
            'has_left': has_left,
            'has_right': has_right,
            'has_middle': has_middle,
            'both_url': f'{neuron_type}.html' if has_both else None,
            'left_url': f'{neuron_type}_L.html' if has_left else None,
            'right_url': f'{neuron_type}_R.html' if has_right else None,
            'middle_url': f'{neuron_type}_M.html' if has_middle else None,
            'roi_summary': roi_summary,
            'parent_roi': parent_roi,
        }

    def _get_roi_summary_cached(self, neuron_type: str, connector) -> tuple:
        """
        OPTIMIZATION 5: ROI summary with better caching and early termination.
        """
        try:
            # Use existing method but with optimizations
            from quickpage.services import IndexService
            temp_service = IndexService(self.config, self.page_generator)

            # Skip expensive analysis if configured
            skip_roi = False  # Could be made configurable

            roi_summary, parent_roi = temp_service._get_roi_summary_for_neuron_type(
                neuron_type, connector, skip_roi_analysis=skip_roi
            )

            return roi_summary, parent_roi

        except Exception as e:
            logger.debug(f"ROI summary failed for {neuron_type}: {e}")
            return [], ""

    def _group_by_parent_roi(self, index_data: List[Dict]) -> List[Dict]:
        """Group neuron types by parent ROI efficiently."""
        grouped_data = defaultdict(list)

        for entry in index_data:
            parent_roi = entry['parent_roi'] if entry['parent_roi'] else 'Other'
            grouped_data[parent_roi].append(entry)

        # Sort groups
        sorted_groups = []
        for parent_roi in sorted(grouped_data.keys()):
            if parent_roi != 'Other':
                sorted_groups.append({
                    'parent_roi': parent_roi,
                    'neuron_types': sorted(grouped_data[parent_roi], key=lambda x: x['name'])
                })

        # Add 'Other' group last
        if 'Other' in grouped_data:
            sorted_groups.append({
                'parent_roi': 'Other',
                'neuron_types': sorted(grouped_data['Other'], key=lambda x: x['name'])
            })

        return sorted_groups

    async def _generate_search_js(self, output_dir: Path, index_data: List[Dict], generation_time):
        """Generate search JS file efficiently."""
        try:
            from quickpage.services import IndexService
            temp_service = IndexService(self.config, self.page_generator)
            await temp_service._generate_neuron_search_js(output_dir, index_data, generation_time)
        except Exception as e:
            logger.warning(f"⚠️  Failed to generate search JS: {e}")

    def _log_performance_summary(self):
        """Log performance summary for analysis."""
        logger.info("📊 Performance Summary:")
        total_time = sum(self._timing_stats.values())

        for operation, duration in self._timing_stats.items():
            percentage = (duration / total_time) * 100 if total_time > 0 else 0
            logger.info(f"   {operation}: {duration:.3f}s ({percentage:.1f}%)")

        logger.info(f"   Cache entries: {len(self._batch_cache)}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'batch_cache_size': len(self._batch_cache),
            'roi_hierarchy_cached': self._roi_hierarchy_cache is not None,
            'timing_stats': self._timing_stats.copy()
        }


async def run_quick_optimization_test():
    """Test the quick optimization implementation."""
    print("🚀 Testing Quick Optimization Implementation")
    print("=" * 60)

    if not Path("config.cns.yaml").exists():
        print("❌ config.cns.yaml not found")
        return

    if not Path("output").exists():
        print("❌ output directory not found")
        return

    # Load configuration
    config = Config.load("config.cns.yaml")
    services = ServiceContainer(config)

    # Create quick optimized service
    quick_service = QuickOptimizedIndexService(config, services.page_generator)

    # Test with ROI analysis
    command = CreateIndexCommand(
        output_directory="quick_opt_test_output",
        index_filename="index_quick_optimized.html",
        include_roi_analysis=True
    )

    # Create output directory
    Path("quick_opt_test_output").mkdir(exist_ok=True)

    # Copy some test files
    import shutil
    output_dir = Path("output")
    test_output_dir = Path("quick_opt_test_output")

    # Copy first 100 HTML files for testing
    html_files = list(output_dir.glob("*.html"))[:100]
    for html_file in html_files:
        shutil.copy2(html_file, test_output_dir)

    print(f"📋 Test setup: {len(html_files)} HTML files copied")

    # Run optimization
    start_time = time.time()
    result = await quick_service.create_index_quick_optimized(command)
    total_time = time.time() - start_time

    if result.is_ok():
        print(f"✅ Quick optimization test completed in {total_time:.2f}s")
        print(f"📄 Output: {result.unwrap()}")

        # Show cache stats
        cache_stats = quick_service.get_cache_stats()
        print(f"📊 Cache stats: {cache_stats}")
    else:
        print(f"❌ Quick optimization test failed: {result.unwrap_err()}")


def main():
    """Main function for testing and demonstration."""
    import argparse

    parser = argparse.ArgumentParser(description="Quick optimization for QuickPage create-index")
    parser.add_argument("--test", action="store_true", help="Run optimization test")
    parser.add_argument("--benchmark", action="store_true", help="Run performance benchmark")

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    if args.test:
        asyncio.run(run_quick_optimization_test())
    else:
        print("Quick Optimization Script")
        print("=" * 40)
        print("Available commands:")
        print("  --test      Run optimization test")
        print("  --benchmark Run performance benchmark")
        print("\nExample usage:")
        print("  python quick_optimization.py --test")


if __name__ == "__main__":
    main()
