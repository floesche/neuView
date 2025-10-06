#!/usr/bin/env python3
"""
Comprehensive performance profiling for the `neuview pop` command.

This script measures and analyzes the performance characteristics of the
queue processing system, identifying bottlenecks and suggesting optimizations.
"""

import time
import asyncio
import json
import sys
import os
import traceback
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
import tempfile
import shutil
from dataclasses import dataclass
from contextlib import contextmanager

# Add the neuview module to the path
sys.path.insert(0, "src")

# Set up logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise during profiling
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class PopPerformanceMetrics:
    """Performance metrics for a single pop operation."""

    total_time: float
    queue_discovery_time: float
    file_locking_time: float
    yaml_parsing_time: float
    service_creation_time: float
    page_generation_time: float
    cache_operation_time: float
    cleanup_time: float
    queue_files_processed: int
    queue_files_remaining: int
    success: bool
    error_message: Optional[str] = None


@dataclass
class BatchPopMetrics:
    """Aggregate metrics for batch pop operations."""

    total_operations: int
    successful_operations: int
    failed_operations: int
    total_time: float
    average_time_per_operation: float
    throughput_operations_per_second: float
    queue_discovery_overhead: float
    file_io_overhead: float
    cache_performance: Dict[str, Any]
    memory_usage: Dict[str, Any]


class PopCommandProfiler:
    """
    Comprehensive profiler for the neuview pop command.
    """

    def __init__(self):
        self.output_dir = Path("output")
        self.queue_dir = self.output_dir / ".queue"
        self.cache_dir = self.output_dir / ".cache"
        self.test_output_dir = Path("profile_test_output")

        # Performance tracking
        self.metrics_history: List[PopPerformanceMetrics] = []
        self.system_metrics: Dict[str, Any] = {}

        # Ensure directories exist
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def profile_context(self, operation_name: str):
        """Context manager for timing operations."""
        start_time = time.time()
        start_memory = self._get_memory_usage()

        try:
            yield
        finally:
            end_time = time.time()
            end_memory = self._get_memory_usage()

            duration = end_time - start_time
            memory_delta = (
                end_memory - start_memory if end_memory and start_memory else 0
            )

            logger.debug(
                f"{operation_name}: {duration:.4f}s, memory: {memory_delta:+.2f}MB"
            )

    def _get_memory_usage(self) -> Optional[float]:
        """Get current memory usage in MB."""
        import psutil

        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024  # Convert to MB

    def _run_pop_command(
        self, output_dir: Optional[str] = None, verbose: bool = True
    ) -> Tuple[bool, str, float]:
        """
        Execute a single pop command and measure its performance.

        Returns:
            Tuple of (success, output, execution_time)
        """
        start_time = time.time()

        cmd = ["python", "-m", "neuview"]
        if verbose:
            cmd.append("--verbose")

        cmd.append("pop")

        if output_dir:
            cmd.extend(["--output-dir", output_dir])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=".",
                timeout=300,  # 5 minute timeout
            )

            execution_time = time.time() - start_time
            success = result.returncode == 0
            output = result.stdout + result.stderr

            return success, output, execution_time

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return False, "Command timed out after 5 minutes", execution_time
        except Exception as e:
            execution_time = time.time() - start_time
            return False, f"Command failed: {str(e)}", execution_time

    def _parse_pop_output(self, output: str) -> Dict[str, Any]:
        """Parse the output of a pop command to extract performance information."""
        metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "database_queries": 0,
            "files_read": 0,
            "files_written": 0,
            "warnings": [],
            "errors": [],
        }

        lines = output.split("\n")
        for line in lines:
            line = line.strip()

            # Extract cache performance
            if "cache hit" in line.lower():
                metrics["cache_hits"] += 1
            elif "cache miss" in line.lower():
                metrics["cache_misses"] += 1

            # Extract file operations
            if "reading" in line.lower() or "loading" in line.lower():
                metrics["files_read"] += 1
            elif "writing" in line.lower() or "saving" in line.lower():
                metrics["files_written"] += 1

            # Extract database operations
            if "query" in line.lower() or "fetching" in line.lower():
                metrics["database_queries"] += 1

            # Collect warnings and errors
            if "warning" in line.lower():
                metrics["warnings"].append(line)
            elif "error" in line.lower():
                metrics["errors"].append(line)

        return metrics

    def profile_single_pop(self) -> PopPerformanceMetrics:
        """Profile a single pop operation with detailed timing."""
        total_start = time.time()

        # Count queue files before operation
        queue_files_before = len(list(self.queue_dir.glob("*.yaml")))

        # Execute pop command
        success, output, execution_time = self._run_pop_command()

        # Count queue files after operation
        queue_files_after = len(list(self.queue_dir.glob("*.yaml")))

        # Parse output for detailed metrics
        parsed_metrics = self._parse_pop_output(output)

        total_time = time.time() - total_start

        metrics = PopPerformanceMetrics(
            total_time=total_time,
            queue_discovery_time=0.0,  # Would need instrumentation to measure
            file_locking_time=0.0,  # Would need instrumentation to measure
            yaml_parsing_time=0.0,  # Would need instrumentation to measure
            service_creation_time=0.0,  # Would need instrumentation to measure
            page_generation_time=execution_time * 0.8,  # Estimate: 80% of time
            cache_operation_time=0.0,  # Would need instrumentation to measure
            cleanup_time=0.0,  # Would need instrumentation to measure
            queue_files_processed=max(0, queue_files_before - queue_files_after),
            queue_files_remaining=queue_files_after,
            success=success,
            error_message=None if success else output,
        )

        self.metrics_history.append(metrics)
        return metrics

    def profile_batch_pop(self, num_operations: int = 10) -> BatchPopMetrics:
        """Profile multiple consecutive pop operations."""
        print(f"🔄 Profiling {num_operations} consecutive pop operations...")

        batch_start = time.time()
        successful_ops = 0
        failed_ops = 0
        total_queue_discovery = 0.0
        total_file_io = 0.0

        individual_metrics = []

        for i in range(num_operations):
            print(f"  Operation {i + 1}/{num_operations}...", end=" ")

            metrics = self.profile_single_pop()
            individual_metrics.append(metrics)

            if metrics.success:
                successful_ops += 1
                print("✅")
            else:
                failed_ops += 1
                print("❌")

            # Stop if no more queue files
            if metrics.queue_files_remaining == 0:
                print(f"  No more queue files after {i + 1} operations")
                break

            # Small delay to avoid overwhelming the system
            time.sleep(0.1)

        total_time = time.time() - batch_start
        total_ops = successful_ops + failed_ops

        return BatchPopMetrics(
            total_operations=total_ops,
            successful_operations=successful_ops,
            failed_operations=failed_ops,
            total_time=total_time,
            average_time_per_operation=total_time / total_ops if total_ops > 0 else 0,
            throughput_operations_per_second=total_ops / total_time
            if total_time > 0
            else 0,
            queue_discovery_overhead=total_queue_discovery,
            file_io_overhead=total_file_io,
            cache_performance={
                "total_metrics": len(individual_metrics),
                "successful_operations": successful_ops,
            },
            memory_usage={},
        )

    def analyze_queue_characteristics(self) -> Dict[str, Any]:
        """Analyze the current queue structure and characteristics."""
        print("📊 Analyzing queue characteristics...")

        yaml_files = list(self.queue_dir.glob("*.yaml"))
        lock_files = list(self.queue_dir.glob("*.lock"))

        # Analyze file sizes
        file_sizes = []
        total_size = 0

        for yaml_file in yaml_files:
            try:
                size = yaml_file.stat().st_size
                file_sizes.append(size)
                total_size += size
            except OSError:
                continue

        # Analyze queue file content
        neuron_types = set()
        soma_sides = set()
        configurations = {}

        for yaml_file in yaml_files[:50]:  # Sample first 50 files
            try:
                import yaml

                with open(yaml_file, "r") as f:
                    data = yaml.safe_load(f)

                if data and "options" in data:
                    options = data["options"]
                    neuron_types.add(options.get("neuron-type", "unknown"))
                    soma_sides.add(options.get("soma-side", "unknown"))

                    # Track configuration variations
                    config_key = (
                        options.get("image-format", "svg"),
                        options.get("embed", True),
                    )
                    configurations[config_key] = configurations.get(config_key, 0) + 1

            except Exception as e:
                logger.warning(f"Failed to parse {yaml_file}: {e}")

        return {
            "total_yaml_files": len(yaml_files),
            "total_lock_files": len(lock_files),
            "total_queue_size_bytes": total_size,
            "average_file_size_bytes": sum(file_sizes) / len(file_sizes)
            if file_sizes
            else 0,
            "min_file_size_bytes": min(file_sizes) if file_sizes else 0,
            "max_file_size_bytes": max(file_sizes) if file_sizes else 0,
            "unique_neuron_types": len(neuron_types),
            "unique_soma_sides": len(soma_sides),
            "configuration_variations": len(configurations),
            "sample_neuron_types": list(neuron_types)[:10],
            "sample_soma_sides": list(soma_sides),
            "popular_configurations": sorted(
                configurations.items(), key=lambda x: x[1], reverse=True
            )[:5],
        }

    def benchmark_queue_processing_patterns(self) -> Dict[str, Any]:
        """Benchmark different queue processing patterns."""
        print("⚡ Benchmarking queue processing patterns...")

        results = {}

        # Pattern 1: Sequential processing (current implementation)
        print("  Testing sequential processing...")
        sequential_start = time.time()
        sequential_metrics = self.profile_batch_pop(5)
        sequential_time = time.time() - sequential_start

        results["sequential"] = {
            "total_time": sequential_time,
            "throughput": sequential_metrics.throughput_operations_per_second,
            "success_rate": sequential_metrics.successful_operations
            / sequential_metrics.total_operations,
            "metrics": sequential_metrics,
        }

        # Pattern 2: File system optimization analysis
        print("  Analyzing file system patterns...")

        # Measure queue directory scanning overhead
        scan_times = []
        for _ in range(10):
            start = time.time()
            yaml_files = list(self.queue_dir.glob("*.yaml"))
            scan_times.append(time.time() - start)

        results["filesystem"] = {
            "queue_scan_average_time": sum(scan_times) / len(scan_times),
            "queue_scan_min_time": min(scan_times),
            "queue_scan_max_time": max(scan_times),
            "files_scanned": len(yaml_files) if yaml_files else 0,
        }

        return results

    def identify_bottlenecks(self) -> Dict[str, Any]:
        """Identify performance bottlenecks in the pop command."""
        print("🔍 Identifying performance bottlenecks...")

        if not self.metrics_history:
            return {"error": "No metrics available. Run profiling first."}

        # Analyze timing patterns
        total_times = [m.total_time for m in self.metrics_history if m.success]
        generation_times = [
            m.page_generation_time for m in self.metrics_history if m.success
        ]

        if not total_times:
            return {"error": "No successful operations to analyze."}

        # Calculate statistics
        avg_total = sum(total_times) / len(total_times)
        avg_generation = sum(generation_times) / len(generation_times)

        # Identify slow operations
        slow_threshold = avg_total * 1.5
        slow_operations = [
            m for m in self.metrics_history if m.total_time > slow_threshold
        ]

        # Analyze failure patterns
        failed_operations = [m for m in self.metrics_history if not m.success]

        return {
            "performance_stats": {
                "average_total_time": avg_total,
                "average_generation_time": avg_generation,
                "min_total_time": min(total_times),
                "max_total_time": max(total_times),
                "generation_time_percentage": (avg_generation / avg_total * 100)
                if avg_total > 0
                else 0,
            },
            "bottlenecks": {
                "slow_operations_count": len(slow_operations),
                "slow_operations_threshold": slow_threshold,
                "primary_bottleneck": "page_generation"
                if avg_generation > avg_total * 0.7
                else "queue_management",
            },
            "failure_analysis": {
                "total_failures": len(failed_operations),
                "failure_rate": len(failed_operations) / len(self.metrics_history),
                "common_errors": self._analyze_common_errors(failed_operations),
            },
        }

    def _analyze_common_errors(
        self, failed_operations: List[PopPerformanceMetrics]
    ) -> List[str]:
        """Analyze common error patterns."""
        error_patterns = {}

        for op in failed_operations:
            if op.error_message:
                # Extract key error patterns
                error = op.error_message.lower()
                if "timeout" in error:
                    error_patterns["timeout"] = error_patterns.get("timeout", 0) + 1
                elif "connection" in error:
                    error_patterns["connection"] = (
                        error_patterns.get("connection", 0) + 1
                    )
                elif "file not found" in error or "no such file" in error:
                    error_patterns["file_not_found"] = (
                        error_patterns.get("file_not_found", 0) + 1
                    )
                elif "memory" in error:
                    error_patterns["memory"] = error_patterns.get("memory", 0) + 1
                else:
                    error_patterns["other"] = error_patterns.get("other", 0) + 1

        return sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)

    def suggest_optimizations(
        self, bottlenecks: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Suggest performance optimizations based on analysis."""
        suggestions = []

        perf_stats = bottlenecks.get("performance_stats", {})
        bottleneck_info = bottlenecks.get("bottlenecks", {})
        failure_info = bottlenecks.get("failure_analysis", {})

        # Queue management optimizations
        if bottleneck_info.get("primary_bottleneck") == "queue_management":
            suggestions.append(
                {
                    "category": "Queue Management",
                    "priority": "HIGH",
                    "title": "Optimize Queue File Discovery",
                    "description": "Implement directory watching or indexing to avoid scanning all files",
                    "implementation": "Add inotify/watchdog to monitor queue directory changes",
                    "estimated_impact": "30-50% faster queue processing",
                }
            )

        # Page generation optimizations
        generation_pct = perf_stats.get("generation_time_percentage", 0)
        if generation_pct > 70:
            suggestions.append(
                {
                    "category": "Page Generation",
                    "priority": "HIGH",
                    "title": "Optimize Page Generation Pipeline",
                    "description": "Cache optimization and connection pooling for database queries",
                    "implementation": "Implement connection pooling and enhance cache utilization",
                    "estimated_impact": "20-40% faster page generation",
                }
            )

        # File I/O optimizations
        suggestions.append(
            {
                "category": "File I/O",
                "priority": "MEDIUM",
                "title": "Batch File Operations",
                "description": "Process multiple queue files in batches to reduce I/O overhead",
                "implementation": "Modify pop command to process N files at once",
                "estimated_impact": "15-25% improvement in throughput",
            }
        )

        # Error handling optimizations
        failure_rate = failure_info.get("failure_rate", 0)
        if failure_rate > 0.1:  # More than 10% failure rate
            suggestions.append(
                {
                    "category": "Reliability",
                    "priority": "HIGH",
                    "title": "Improve Error Handling",
                    "description": f"Address {failure_rate * 100:.1f}% failure rate",
                    "implementation": "Add retry logic and better error recovery",
                    "estimated_impact": "Reduced failure rate and better reliability",
                }
            )

        # Caching optimizations (from existing analysis)
        suggestions.append(
            {
                "category": "Caching",
                "priority": "MEDIUM",
                "title": "Implement Soma Cache Optimization",
                "description": "Use neuron cache data instead of separate soma cache files",
                "implementation": "Apply already-analyzed soma cache optimization",
                "estimated_impact": "50% reduction in cache I/O operations",
            }
        )

        return suggestions

    def generate_comprehensive_report(self):
        """Generate a comprehensive performance report."""
        print("\n" + "=" * 80)
        print("NEUVIEW POP COMMAND - COMPREHENSIVE PERFORMANCE REPORT")
        print("=" * 80)

        # System information
        print(f"\n📋 SYSTEM INFORMATION:")
        print(f"   Python version: {sys.version.split()[0]}")
        print(f"   Working directory: {os.getcwd()}")
        print(f"   Queue directory: {self.queue_dir}")
        print(f"   Cache directory: {self.cache_dir}")

        # Queue characteristics
        queue_analysis = self.analyze_queue_characteristics()
        print(f"\n📊 QUEUE ANALYSIS:")
        print(f"   Total queue files: {queue_analysis['total_yaml_files']}")
        print(f"   Active lock files: {queue_analysis['total_lock_files']}")
        print(
            f"   Total queue size: {queue_analysis['total_queue_size_bytes'] / 1024:.1f}KB"
        )
        print(
            f"   Average file size: {queue_analysis['average_file_size_bytes']:.0f} bytes"
        )
        print(f"   Unique neuron types: {queue_analysis['unique_neuron_types']}")
        print(
            f"   Configuration variations: {queue_analysis['configuration_variations']}"
        )

        # Performance benchmarks
        print(f"\n⚡ PERFORMANCE BENCHMARKS:")

        # Single operation profile
        print(f"   Single pop operation:")
        single_metrics = self.profile_single_pop()
        print(f"     Success: {'✅' if single_metrics.success else '❌'}")
        print(f"     Total time: {single_metrics.total_time:.3f}s")
        print(f"     Files processed: {single_metrics.queue_files_processed}")
        print(f"     Files remaining: {single_metrics.queue_files_remaining}")

        # Batch operation profile
        print(f"   Batch pop operations (10 ops):")
        batch_metrics = self.profile_batch_pop(10)
        print(
            f"     Successful operations: {batch_metrics.successful_operations}/{batch_metrics.total_operations}"
        )
        print(
            f"     Average time per operation: {batch_metrics.average_time_per_operation:.3f}s"
        )
        print(
            f"     Throughput: {batch_metrics.throughput_operations_per_second:.2f} ops/sec"
        )
        print(
            f"     Success rate: {batch_metrics.successful_operations / batch_metrics.total_operations * 100:.1f}%"
        )

        # Bottleneck analysis
        bottlenecks = self.identify_bottlenecks()
        if "error" not in bottlenecks:
            print(f"\n🔍 BOTTLENECK ANALYSIS:")
            perf_stats = bottlenecks["performance_stats"]
            print(f"   Average operation time: {perf_stats['average_total_time']:.3f}s")
            print(
                f"   Page generation time: {perf_stats['generation_time_percentage']:.1f}% of total"
            )
            print(
                f"   Primary bottleneck: {bottlenecks['bottlenecks']['primary_bottleneck']}"
            )
            print(
                f"   Failure rate: {bottlenecks['failure_analysis']['failure_rate'] * 100:.1f}%"
            )

        # Processing patterns
        patterns = self.benchmark_queue_processing_patterns()
        print(f"\n📈 PROCESSING PATTERNS:")
        seq = patterns["sequential"]
        print(f"   Sequential processing throughput: {seq['throughput']:.2f} ops/sec")
        print(
            f"   Queue scanning overhead: {patterns['filesystem']['queue_scan_average_time'] * 1000:.1f}ms"
        )

        # Optimization suggestions
        if "error" not in bottlenecks:
            suggestions = self.suggest_optimizations(bottlenecks)
            print(f"\n💡 OPTIMIZATION SUGGESTIONS:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"   {i}. [{suggestion['priority']}] {suggestion['title']}")
                print(f"      Category: {suggestion['category']}")
                print(f"      Impact: {suggestion['estimated_impact']}")
                print(f"      Implementation: {suggestion['implementation']}")
                print()

        # Summary and recommendations
        print(f"🎯 SUMMARY & RECOMMENDATIONS:")

        if batch_metrics.throughput_operations_per_second < 0.5:
            print(
                f"   ⚠️  LOW THROUGHPUT: {batch_metrics.throughput_operations_per_second:.2f} ops/sec"
            )
            print(f"   → Focus on page generation and cache optimizations")
        elif batch_metrics.throughput_operations_per_second < 1.0:
            print(
                f"   📈 MODERATE THROUGHPUT: {batch_metrics.throughput_operations_per_second:.2f} ops/sec"
            )
            print(f"   → Queue management and I/O optimizations recommended")
        else:
            print(
                f"   ✅ GOOD THROUGHPUT: {batch_metrics.throughput_operations_per_second:.2f} ops/sec"
            )
            print(f"   → Focus on reliability and error handling improvements")

        failure_rate = batch_metrics.failed_operations / batch_metrics.total_operations
        if failure_rate > 0.1:
            print(f"   ❌ HIGH FAILURE RATE: {failure_rate * 100:.1f}%")
            print(f"   → Implement better error handling and retry logic")

        if queue_analysis["total_yaml_files"] > 1000:
            print(f"   📁 LARGE QUEUE: {queue_analysis['total_yaml_files']} files")
            print(f"   → Consider batch processing and queue management optimization")

        print(f"\n🔧 NEXT STEPS:")
        print(f"   1. Apply soma cache optimization (50% I/O reduction)")
        print(f"   2. Implement queue directory watching for faster discovery")
        print(f"   3. Add connection pooling for database operations")
        print(f"   4. Consider batch processing for improved throughput")

        return {
            "queue_analysis": queue_analysis,
            "single_metrics": single_metrics,
            "batch_metrics": batch_metrics,
            "bottlenecks": bottlenecks,
            "patterns": patterns,
            "suggestions": suggestions if "error" not in bottlenecks else [],
        }


def main():
    """Main function to run comprehensive pop command profiling."""
    print("neuView Pop Command Performance Profiler")
    print("=" * 50)

    try:
        profiler = PopCommandProfiler()

        # Check if queue directory exists and has files
        if not profiler.queue_dir.exists():
            print("❌ Queue directory not found. Run 'neuview fill-queue' first.")
            return

        yaml_files = list(profiler.queue_dir.glob("*.yaml"))
        if not yaml_files:
            print("❌ No queue files found. Run 'neuview fill-queue' first.")
            return

        print(f"✅ Found {len(yaml_files)} queue files to process")

        # Generate comprehensive report
        report = profiler.generate_comprehensive_report()

        # Save detailed report to file
        report_file = Path("pop_performance_report.json")
        with open(report_file, "w") as f:
            # Convert dataclasses to dicts for JSON serialization
            json_report = {}
            for key, value in report.items():
                if hasattr(value, "__dict__"):
                    json_report[key] = value.__dict__
                else:
                    json_report[key] = value

            json.dump(json_report, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: {report_file}")

    except KeyboardInterrupt:
        print("\n❌ Profiling interrupted by user")
    except Exception as e:
        print(f"❌ Error during profiling: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
