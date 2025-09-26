#!/usr/bin/env python3
"""
Detailed page generation profiling for the `quickpage pop` command.

This script instruments the page generation process to identify specific
bottlenecks within the pop command execution pipeline.
"""

import time
import asyncio
import sys
import os
import json
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import subprocess

# Add the quickpage module to the path
sys.path.insert(0, "src")

# Import quickpage modules for direct instrumentation
try:
    from quickpage.config import Config
    from quickpage.services import QueueService, PageGenerationService
    from quickpage.neuprint_connector import NeuPrintConnector
    from quickpage.page_generator import PageGenerator
    from quickpage.services import PopCommand
    import yaml
except ImportError as e:
    print(f"❌ Failed to import quickpage modules: {e}")
    print("Make sure you're running from the quickpage directory")
    sys.exit(1)

# Configure logging to capture internal operations
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pop_detailed_profile.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class DetailedPopMetrics:
    """Detailed timing metrics for pop operation components."""

    # High-level timing
    total_time: float

    # Queue management timing
    queue_discovery_time: float
    file_lock_time: float
    yaml_parse_time: float

    # Service initialization timing
    config_load_time: float
    connector_init_time: float
    service_init_time: float

    # Data fetching timing
    neuron_data_fetch_time: float
    roi_data_fetch_time: float
    connectivity_fetch_time: float

    # Cache operation timing
    cache_read_time: float
    cache_write_time: float
    cache_hit_rate: float

    # Page generation timing
    template_load_time: float
    data_processing_time: float
    html_generation_time: float
    file_write_time: float

    # Database operation timing
    database_query_count: int
    database_query_time: float

    # Memory usage
    memory_peak_mb: float
    memory_delta_mb: float

    # Operation details
    neuron_type: str
    soma_side: str
    success: bool
    error_message: Optional[str] = None


class InstrumentedPopProfiler:
    """
    Profiler that instruments the pop command execution to measure
    detailed performance metrics at each stage.
    """

    def __init__(self):
        self.config_path = "config.yaml"
        self.output_dir = Path("output")
        self.queue_dir = self.output_dir / ".queue"
        self.cache_dir = self.output_dir / ".cache"

        # Performance tracking
        self.current_metrics = None
        self.timing_stack = []
        self.operation_start_time = None
        self.memory_tracker = []

        # Instrumentation hooks
        self.database_queries = []
        self.cache_operations = []
        self.file_operations = []

    @contextmanager
    def time_operation(self, operation_name: str):
        """Context manager for timing individual operations."""
        start_time = time.time()
        start_memory = self._get_memory_usage()

        self.timing_stack.append(
            {
                "operation": operation_name,
                "start_time": start_time,
                "start_memory": start_memory,
            }
        )

        try:
            yield
        finally:
            end_time = time.time()
            end_memory = self._get_memory_usage()

            operation_info = self.timing_stack.pop()
            duration = end_time - start_time
            memory_delta = (
                (end_memory - start_memory) if end_memory and start_memory else 0
            )

            logger.debug(
                f"{operation_name}: {duration:.4f}s, memory: {memory_delta:+.2f}MB"
            )

            # Store timing for later analysis
            if hasattr(self, "current_metrics") and self.current_metrics:
                self._record_timing(operation_name, duration, memory_delta)

    def _get_memory_usage(self) -> Optional[float]:
        """Get current memory usage in MB."""
        try:
            import psutil

            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_tracker.append(memory_mb)
            return memory_mb
        except ImportError:
            return None

    def _record_timing(self, operation_name: str, duration: float, memory_delta: float):
        """Record timing information in current metrics."""
        if operation_name == "queue_discovery":
            self.current_metrics.queue_discovery_time = duration
        elif operation_name == "file_lock":
            self.current_metrics.file_lock_time = duration
        elif operation_name == "yaml_parse":
            self.current_metrics.yaml_parse_time = duration
        elif operation_name == "config_load":
            self.current_metrics.config_load_time = duration
        elif operation_name == "connector_init":
            self.current_metrics.connector_init_time = duration
        elif operation_name == "service_init":
            self.current_metrics.service_init_time = duration
        elif operation_name == "neuron_data_fetch":
            self.current_metrics.neuron_data_fetch_time = duration
        elif operation_name == "roi_data_fetch":
            self.current_metrics.roi_data_fetch_time = duration
        elif operation_name == "connectivity_fetch":
            self.current_metrics.connectivity_fetch_time = duration
        elif operation_name == "cache_read":
            self.current_metrics.cache_read_time += duration
        elif operation_name == "cache_write":
            self.current_metrics.cache_write_time += duration
        elif operation_name == "template_load":
            self.current_metrics.template_load_time = duration
        elif operation_name == "data_processing":
            self.current_metrics.data_processing_time = duration
        elif operation_name == "html_generation":
            self.current_metrics.html_generation_time = duration
        elif operation_name == "file_write":
            self.current_metrics.file_write_time = duration

    async def profile_instrumented_pop(self) -> DetailedPopMetrics:
        """
        Execute a single pop operation with detailed instrumentation.
        """
        operation_start = time.time()
        start_memory = self._get_memory_usage()

        # Initialize metrics
        self.current_metrics = DetailedPopMetrics(
            total_time=0.0,
            queue_discovery_time=0.0,
            file_lock_time=0.0,
            yaml_parse_time=0.0,
            config_load_time=0.0,
            connector_init_time=0.0,
            service_init_time=0.0,
            neuron_data_fetch_time=0.0,
            roi_data_fetch_time=0.0,
            connectivity_fetch_time=0.0,
            cache_read_time=0.0,
            cache_write_time=0.0,
            cache_hit_rate=0.0,
            template_load_time=0.0,
            data_processing_time=0.0,
            html_generation_time=0.0,
            file_write_time=0.0,
            database_query_count=0,
            database_query_time=0.0,
            memory_peak_mb=0.0,
            memory_delta_mb=0.0,
            neuron_type="",
            soma_side="",
            success=False,
        )

        try:
            # Phase 1: Queue Discovery and File Locking
            with self.time_operation("queue_discovery"):
                yaml_files = list(self.queue_dir.glob("*.yaml"))
                if not yaml_files:
                    self.current_metrics.error_message = "No queue files available"
                    return self.current_metrics

                yaml_file = yaml_files[0]
                lock_file = yaml_file.with_suffix(".lock")

            with self.time_operation("file_lock"):
                try:
                    yaml_file.rename(lock_file)
                except FileNotFoundError:
                    self.current_metrics.error_message = (
                        "File was claimed by another process"
                    )
                    return self.current_metrics

            # Phase 2: YAML Parsing
            with self.time_operation("yaml_parse"):
                with open(lock_file, "r") as f:
                    queue_data = yaml.safe_load(f)

                if not queue_data or "options" not in queue_data:
                    self.current_metrics.error_message = "Invalid queue file format"
                    return self.current_metrics

                options = queue_data["options"]
                self.current_metrics.neuron_type = options["neuron-type"]
                self.current_metrics.soma_side = options["soma-side"]

            # Phase 3: Service Initialization
            with self.time_operation("config_load"):
                config = Config.load(self.config_path)

            with self.time_operation("connector_init"):
                connector = NeuPrintConnector(config)

            with self.time_operation("service_init"):
                queue_service = QueueService(config)
                generator = PageGenerator.create_with_factory(
                    config, config.output.directory, queue_service
                )
                page_service = PageGenerationService(connector, generator, config)

            # Phase 4: Data Fetching (instrument the connector)
            original_fetch = connector._get_or_fetch_raw_neuron_data

            def instrumented_fetch(neuron_type):
                with self.time_operation("neuron_data_fetch"):
                    return original_fetch(neuron_type)

            connector._get_or_fetch_raw_neuron_data = instrumented_fetch

            # Phase 5: Create and execute generate command
            from quickpage.services import GeneratePageCommand
            from quickpage.models import NeuronTypeName

            generate_command = GeneratePageCommand(
                neuron_type=NeuronTypeName(options["neuron-type"]),
                output_directory=options.get("output-dir"),
                image_format=options.get("image-format", "svg"),
                embed_images=options.get("embed", True),
                minify=True,
            )

            # Execute page generation with instrumentation
            result = await page_service.generate_page(generate_command)

            if result.is_ok():
                self.current_metrics.success = True
                # Clean up lock file
                lock_file.unlink()
            else:
                self.current_metrics.error_message = result.unwrap_err()
                # Rename back to .yaml
                lock_file.rename(yaml_file)

        except Exception as e:
            self.current_metrics.error_message = str(e)
            logger.error(f"Error during instrumented pop: {e}")
            traceback.print_exc()

            # Cleanup on error
            if "lock_file" in locals() and lock_file.exists():
                try:
                    lock_file.rename(yaml_file)
                except:
                    pass

        # Finalize metrics
        self.current_metrics.total_time = time.time() - operation_start

        if self.memory_tracker:
            self.current_metrics.memory_peak_mb = max(self.memory_tracker)
            self.current_metrics.memory_delta_mb = (
                self.memory_tracker[-1] - self.memory_tracker[0]
            )

        # Calculate database metrics (would need more instrumentation)
        self.current_metrics.database_query_count = len(self.database_queries)
        self.current_metrics.database_query_time = sum(
            q.get("duration", 0) for q in self.database_queries
        )

        # Calculate cache hit rate (would need cache instrumentation)
        cache_hits = len(
            [op for op in self.cache_operations if op.get("type") == "hit"]
        )
        cache_total = len(self.cache_operations)
        self.current_metrics.cache_hit_rate = (
            cache_hits / cache_total if cache_total > 0 else 0.0
        )

        return self.current_metrics

    def profile_multiple_pops(self, count: int = 5) -> List[DetailedPopMetrics]:
        """Profile multiple pop operations for statistical analysis."""
        print(f"🔄 Profiling {count} detailed pop operations...")

        metrics_list = []

        for i in range(count):
            print(f"  Operation {i + 1}/{count}...", end=" ")

            try:
                metrics = asyncio.run(self.profile_instrumented_pop())
                metrics_list.append(metrics)

                if metrics.success:
                    print(f"✅ ({metrics.total_time:.2f}s)")
                else:
                    print(f"❌ {metrics.error_message}")

            except Exception as e:
                print(f"❌ Exception: {e}")
                continue

            # Small delay between operations
            time.sleep(0.5)

        return metrics_list

    def analyze_detailed_metrics(
        self, metrics_list: List[DetailedPopMetrics]
    ) -> Dict[str, Any]:
        """Analyze detailed metrics to identify bottlenecks."""
        if not metrics_list:
            return {"error": "No metrics to analyze"}

        successful_metrics = [m for m in metrics_list if m.success]

        if not successful_metrics:
            return {"error": "No successful operations to analyze"}

        # Calculate averages
        def avg(attr_name):
            values = [getattr(m, attr_name) for m in successful_metrics]
            return sum(values) / len(values)

        # Timing breakdown
        timing_analysis = {
            "queue_discovery_avg": avg("queue_discovery_time"),
            "file_lock_avg": avg("file_lock_time"),
            "yaml_parse_avg": avg("yaml_parse_time"),
            "config_load_avg": avg("config_load_time"),
            "connector_init_avg": avg("connector_init_time"),
            "service_init_avg": avg("service_init_time"),
            "neuron_data_fetch_avg": avg("neuron_data_fetch_time"),
            "roi_data_fetch_avg": avg("roi_data_fetch_time"),
            "connectivity_fetch_avg": avg("connectivity_fetch_time"),
            "cache_read_avg": avg("cache_read_time"),
            "cache_write_avg": avg("cache_write_time"),
            "template_load_avg": avg("template_load_time"),
            "data_processing_avg": avg("data_processing_time"),
            "html_generation_avg": avg("html_generation_time"),
            "file_write_avg": avg("file_write_time"),
            "total_avg": avg("total_time"),
        }

        # Identify top time consumers
        overhead_operations = [
            ("queue_discovery", timing_analysis["queue_discovery_avg"]),
            ("file_lock", timing_analysis["file_lock_avg"]),
            ("yaml_parse", timing_analysis["yaml_parse_avg"]),
            ("config_load", timing_analysis["config_load_avg"]),
            ("connector_init", timing_analysis["connector_init_avg"]),
            ("service_init", timing_analysis["service_init_avg"]),
        ]

        generation_operations = [
            ("neuron_data_fetch", timing_analysis["neuron_data_fetch_avg"]),
            ("roi_data_fetch", timing_analysis["roi_data_fetch_avg"]),
            ("connectivity_fetch", timing_analysis["connectivity_fetch_avg"]),
            ("data_processing", timing_analysis["data_processing_avg"]),
            ("html_generation", timing_analysis["html_generation_avg"]),
            ("file_write", timing_analysis["file_write_avg"]),
        ]

        cache_operations = [
            ("cache_read", timing_analysis["cache_read_avg"]),
            ("cache_write", timing_analysis["cache_write_avg"]),
        ]

        # Sort by time consumption
        overhead_sorted = sorted(overhead_operations, key=lambda x: x[1], reverse=True)
        generation_sorted = sorted(
            generation_operations, key=lambda x: x[1], reverse=True
        )
        cache_sorted = sorted(cache_operations, key=lambda x: x[1], reverse=True)

        # Calculate percentages
        total_avg = timing_analysis["total_avg"]

        for operations in [overhead_sorted, generation_sorted, cache_sorted]:
            for i, (name, time_val) in enumerate(operations):
                percentage = (time_val / total_avg * 100) if total_avg > 0 else 0
                operations[i] = (name, time_val, percentage)

        # Memory analysis
        memory_analysis = {
            "peak_memory_avg": avg("memory_peak_mb"),
            "memory_delta_avg": avg("memory_delta_mb"),
            "peak_memory_max": max(m.memory_peak_mb for m in successful_metrics),
            "memory_delta_max": max(m.memory_delta_mb for m in successful_metrics),
        }

        # Cache performance
        cache_analysis = {
            "cache_hit_rate_avg": avg("cache_hit_rate"),
            "cache_read_time_total": sum(m.cache_read_time for m in successful_metrics),
            "cache_write_time_total": sum(
                m.cache_write_time for m in successful_metrics
            ),
        }

        # Database performance
        database_analysis = {
            "query_count_avg": avg("database_query_count"),
            "query_time_avg": avg("database_query_time"),
            "query_count_total": sum(
                m.database_query_count for m in successful_metrics
            ),
        }

        return {
            "timing_analysis": timing_analysis,
            "top_overhead_operations": overhead_sorted,
            "top_generation_operations": generation_sorted,
            "top_cache_operations": cache_sorted,
            "memory_analysis": memory_analysis,
            "cache_analysis": cache_analysis,
            "database_analysis": database_analysis,
            "success_rate": len(successful_metrics) / len(metrics_list),
            "total_operations": len(metrics_list),
            "successful_operations": len(successful_metrics),
        }

    def suggest_specific_optimizations(
        self, analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Suggest specific optimizations based on detailed analysis."""
        suggestions = []

        timing = analysis["timing_analysis"]
        overhead_ops = analysis["top_overhead_operations"]
        generation_ops = analysis["top_generation_operations"]
        cache_analysis = analysis["cache_analysis"]
        memory_analysis = analysis["memory_analysis"]

        # Service initialization overhead
        init_time = (
            timing["config_load_avg"]
            + timing["connector_init_avg"]
            + timing["service_init_avg"]
        )
        init_percentage = (
            (init_time / timing["total_avg"] * 100) if timing["total_avg"] > 0 else 0
        )

        if init_percentage > 10:
            suggestions.append(
                {
                    "category": "Service Initialization",
                    "priority": "HIGH",
                    "title": "Implement Service Connection Pooling",
                    "description": f"Service initialization takes {init_percentage:.1f}% of total time",
                    "implementation": "Create persistent service instances and connection pools",
                    "estimated_impact": f"Reduce initialization overhead by {init_percentage:.1f}%",
                }
            )

        # Queue management overhead
        queue_time = (
            timing["queue_discovery_avg"]
            + timing["file_lock_avg"]
            + timing["yaml_parse_avg"]
        )
        queue_percentage = (
            (queue_time / timing["total_avg"] * 100) if timing["total_avg"] > 0 else 0
        )

        if queue_percentage > 5:
            suggestions.append(
                {
                    "category": "Queue Management",
                    "priority": "MEDIUM",
                    "title": "Optimize Queue File Processing",
                    "description": f"Queue operations take {queue_percentage:.1f}% of total time",
                    "implementation": "Implement queue indexing and faster file discovery",
                    "estimated_impact": f"Reduce queue overhead by {queue_percentage:.1f}%",
                }
            )

        # Data fetching bottlenecks
        fetch_time = (
            timing["neuron_data_fetch_avg"]
            + timing["roi_data_fetch_avg"]
            + timing["connectivity_fetch_avg"]
        )
        fetch_percentage = (
            (fetch_time / timing["total_avg"] * 100) if timing["total_avg"] > 0 else 0
        )

        if fetch_percentage > 30:
            suggestions.append(
                {
                    "category": "Data Fetching",
                    "priority": "HIGH",
                    "title": "Implement Aggressive Data Caching",
                    "description": f"Data fetching takes {fetch_percentage:.1f}% of total time",
                    "implementation": "Enhanced caching and pre-fetching strategies",
                    "estimated_impact": f"Reduce data fetching time by 20-40%",
                }
            )

        # Cache performance
        if cache_analysis["cache_hit_rate_avg"] < 0.7:
            suggestions.append(
                {
                    "category": "Caching",
                    "priority": "HIGH",
                    "title": "Improve Cache Hit Rate",
                    "description": f"Cache hit rate is only {cache_analysis['cache_hit_rate_avg'] * 100:.1f}%",
                    "implementation": "Optimize cache key generation and retention policies",
                    "estimated_impact": "Increase cache hit rate to 80%+",
                }
            )

        # Memory usage
        if memory_analysis["memory_delta_avg"] > 100:  # More than 100MB per operation
            suggestions.append(
                {
                    "category": "Memory Management",
                    "priority": "MEDIUM",
                    "title": "Optimize Memory Usage",
                    "description": f"Average memory increase: {memory_analysis['memory_delta_avg']:.1f}MB per operation",
                    "implementation": "Implement data streaming and memory cleanup",
                    "estimated_impact": "Reduce memory footprint by 30-50%",
                }
            )

        # HTML generation optimization
        html_percentage = (
            (timing["html_generation_avg"] / timing["total_avg"] * 100)
            if timing["total_avg"] > 0
            else 0
        )

        if html_percentage > 15:
            suggestions.append(
                {
                    "category": "Template Processing",
                    "priority": "MEDIUM",
                    "title": "Optimize Template Generation",
                    "description": f"HTML generation takes {html_percentage:.1f}% of total time",
                    "implementation": "Template caching and generation optimization",
                    "estimated_impact": f"Reduce template processing time by 20-30%",
                }
            )

        return suggestions

    def generate_detailed_report(self):
        """Generate a comprehensive detailed performance report."""
        print("\n" + "=" * 80)
        print("QUICKPAGE POP COMMAND - DETAILED PERFORMANCE ANALYSIS")
        print("=" * 80)

        # Profile multiple operations
        metrics_list = self.profile_multiple_pops(10)

        if not metrics_list:
            print("❌ No metrics collected")
            return

        # Analyze the metrics
        analysis = self.analyze_detailed_metrics(metrics_list)

        if "error" in analysis:
            print(f"❌ Analysis failed: {analysis['error']}")
            return

        # Display results
        print(f"\n📊 OPERATION SUMMARY:")
        print(f"   Total operations: {analysis['total_operations']}")
        print(f"   Successful operations: {analysis['successful_operations']}")
        print(f"   Success rate: {analysis['success_rate'] * 100:.1f}%")
        print(f"   Average total time: {analysis['timing_analysis']['total_avg']:.3f}s")

        print(f"\n⏱️  TIMING BREAKDOWN (Top Operations by Time):")

        print(f"   Service Overhead:")
        for name, time_val, percentage in analysis["top_overhead_operations"][:3]:
            print(f"     {name}: {time_val:.3f}s ({percentage:.1f}%)")

        print(f"   Page Generation:")
        for name, time_val, percentage in analysis["top_generation_operations"][:3]:
            print(f"     {name}: {time_val:.3f}s ({percentage:.1f}%)")

        print(f"   Cache Operations:")
        for name, time_val, percentage in analysis["top_cache_operations"]:
            print(f"     {name}: {time_val:.3f}s ({percentage:.1f}%)")

        print(f"\n💾 MEMORY ANALYSIS:")
        mem = analysis["memory_analysis"]
        print(f"   Average peak memory: {mem['peak_memory_avg']:.1f}MB")
        print(f"   Average memory delta: {mem['memory_delta_avg']:.1f}MB")
        print(f"   Maximum peak memory: {mem['peak_memory_max']:.1f}MB")

        print(f"\n🗄️  CACHE PERFORMANCE:")
        cache = analysis["cache_analysis"]
        print(f"   Average hit rate: {cache['cache_hit_rate_avg'] * 100:.1f}%")
        print(f"   Total read time: {cache['cache_read_time_total']:.3f}s")
        print(f"   Total write time: {cache['cache_write_time_total']:.3f}s")

        print(f"\n🔍 DATABASE PERFORMANCE:")
        db = analysis["database_analysis"]
        print(f"   Average queries per operation: {db['query_count_avg']:.1f}")
        print(f"   Average query time: {db['query_time_avg']:.3f}s")
        print(f"   Total queries executed: {db['query_count_total']}")

        # Generate specific optimization suggestions
        suggestions = self.suggest_specific_optimizations(analysis)

        print(f"\n💡 SPECIFIC OPTIMIZATION RECOMMENDATIONS:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. [{suggestion['priority']}] {suggestion['title']}")
            print(f"      Category: {suggestion['category']}")
            print(f"      Issue: {suggestion['description']}")
            print(f"      Solution: {suggestion['implementation']}")
            print(f"      Impact: {suggestion['estimated_impact']}")
            print()

        print(f"🎯 KEY INSIGHTS:")

        # Identify the biggest bottleneck
        top_overhead = (
            analysis["top_overhead_operations"][0]
            if analysis["top_overhead_operations"]
            else None
        )
        top_generation = (
            analysis["top_generation_operations"][0]
            if analysis["top_generation_operations"]
            else None
        )

        if top_overhead and top_generation:
            if top_overhead[2] > top_generation[2]:  # Compare percentages
                print(
                    f"   🔴 PRIMARY BOTTLENECK: Service overhead ({top_overhead[0]}: {top_overhead[2]:.1f}%)"
                )
                print(f"   → Focus on service initialization and connection pooling")
            else:
                print(
                    f"   🔴 PRIMARY BOTTLENECK: Page generation ({top_generation[0]}: {top_generation[2]:.1f}%)"
                )
                print(f"   → Focus on data fetching and caching optimization")

        # Cache efficiency insights
        if cache["cache_hit_rate_avg"] < 0.5:
            print(
                f"   ⚠️  POOR CACHE EFFICIENCY: {cache['cache_hit_rate_avg'] * 100:.1f}% hit rate"
            )
            print(f"   → Implement cache warming and better retention policies")

        # Memory usage insights
        if mem["memory_delta_avg"] > 200:
            print(
                f"   📈 HIGH MEMORY USAGE: {mem['memory_delta_avg']:.1f}MB per operation"
            )
            print(f"   → Implement memory streaming and cleanup optimizations")

        # Success rate insights
        if analysis["success_rate"] < 0.9:
            print(
                f"   ❌ RELIABILITY ISSUE: {analysis['success_rate'] * 100:.1f}% success rate"
            )
            print(f"   → Improve error handling and retry mechanisms")

        print(f"\n🚀 IMPLEMENTATION PRIORITY:")
        print(f"   1. Apply existing soma cache optimization")
        print(f"   2. Implement service connection pooling")
        print(f"   3. Enhance data caching strategies")
        print(f"   4. Optimize template processing")

        # Save detailed report
        report_data = {
            "metrics": [asdict(m) for m in metrics_list],
            "analysis": analysis,
            "suggestions": suggestions,
        }

        with open("detailed_pop_performance_report.json", "w") as f:
            json.dump(report_data, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: detailed_pop_performance_report.json")


def main():
    """Main function to run detailed pop command profiling."""
    print("QuickPage Pop Command - Detailed Performance Analysis")
    print("=" * 55)

    try:
        profiler = InstrumentedPopProfiler()

        # Check prerequisites
        if not profiler.queue_dir.exists() or not list(
            profiler.queue_dir.glob("*.yaml")
        ):
            print("❌ No queue files found. Run 'quickpage fill-queue' first.")
            return

        print(
            f"✅ Queue directory found with {len(list(profiler.queue_dir.glob('*.yaml')))} files"
        )

        # Generate detailed report
        profiler.generate_detailed_report()

    except KeyboardInterrupt:
        print("\n❌ Analysis interrupted by user")
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
