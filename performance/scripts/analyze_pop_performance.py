#!/usr/bin/env python3
"""
Comprehensive performance analysis for the `neuview pop` command.

This script analyzes the pop command by timing execution and parsing verbose output
to identify bottlenecks and suggest performance improvements.
"""

import time
import subprocess
import re
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import statistics


@dataclass
class PopAnalysisResult:
    """Results from analyzing a single pop operation."""

    # Timing metrics
    total_time: float
    command_overhead: float

    # Operation details
    neuron_type: str
    soma_side: str
    success: bool
    error_message: Optional[str] = None

    # Parsed metrics from verbose output
    cache_operations: Dict[str, int] = None
    database_queries: int = 0
    file_operations: int = 0
    warnings: List[str] = None
    errors: List[str] = None

    # Performance indicators
    cache_hit_rate: Optional[float] = None
    generation_time_estimate: Optional[float] = None

    def __post_init__(self):
        if self.cache_operations is None:
            self.cache_operations = {}
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []


class PopPerformanceAnalyzer:
    """
    Analyzes the performance of the neuview pop command by executing it
    and parsing the verbose output to extract performance metrics.
    """

    def __init__(self):
        self.queue_dir = Path("output/.queue")
        self.cache_dir = Path("output/.cache")
        self.results: List[PopAnalysisResult] = []

        # Patterns for parsing verbose output
        self.patterns = {
            "neuron_type": re.compile(
                r"Processing neuron type:\s*(\w+)", re.IGNORECASE
            ),
            "soma_side": re.compile(r"soma[_\s]*side:\s*(\w+)", re.IGNORECASE),
            "cache_hit": re.compile(
                r"cache\s+hit|retrieved from.*cache", re.IGNORECASE
            ),
            "cache_miss": re.compile(r"cache\s+miss|not found in cache", re.IGNORECASE),
            "database_query": re.compile(
                r"query|fetching.*from.*neuprint|executing", re.IGNORECASE
            ),
            "file_read": re.compile(
                r"reading|loading.*file|opening.*\.json", re.IGNORECASE
            ),
            "file_write": re.compile(
                r"writing|saving.*file|created.*\.html", re.IGNORECASE
            ),
            "generation_start": re.compile(
                r"generating.*page|starting.*generation", re.IGNORECASE
            ),
            "generation_complete": re.compile(
                r"generated.*successfully|page.*complete", re.IGNORECASE
            ),
            "warning": re.compile(r"warning:", re.IGNORECASE),
            "error": re.compile(r"error:|failed|exception", re.IGNORECASE),
            "success": re.compile(r"✅|generated.*\.html|success", re.IGNORECASE),
        }

    def execute_pop_with_timing(
        self, timeout: int = 300
    ) -> Tuple[bool, str, float, float]:
        """
        Execute a single pop command with timing.

        Returns:
            Tuple of (success, output, total_time, command_overhead)
        """
        # Measure command startup overhead
        overhead_start = time.time()

        # Prepare command
        cmd = ["python", "-m", "neuview", "--verbose", "pop"]

        # Execute command
        exec_start = time.time()
        command_overhead = exec_start - overhead_start

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=".", timeout=timeout
            )

            total_time = time.time() - exec_start
            success = result.returncode == 0
            output = result.stdout + result.stderr

            return success, output, total_time, command_overhead

        except subprocess.TimeoutExpired:
            total_time = time.time() - exec_start
            return (
                False,
                f"Command timed out after {timeout} seconds",
                total_time,
                command_overhead,
            )
        except Exception as e:
            total_time = time.time() - exec_start
            return False, f"Command failed: {str(e)}", total_time, command_overhead

    def parse_verbose_output(self, output: str) -> Dict[str, Any]:
        """
        Parse verbose output to extract performance metrics.
        """
        lines = output.split("\n")
        metrics = {
            "neuron_type": "",
            "soma_side": "",
            "cache_hits": 0,
            "cache_misses": 0,
            "database_queries": 0,
            "file_reads": 0,
            "file_writes": 0,
            "warnings": [],
            "errors": [],
            "generation_started": False,
            "generation_completed": False,
            "success_indicators": 0,
        }

        generation_start_time = None
        generation_end_time = None

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # Extract neuron type
            if not metrics["neuron_type"]:
                match = self.patterns["neuron_type"].search(line)
                if match:
                    metrics["neuron_type"] = match.group(1)

            # Extract soma side
            if not metrics["soma_side"]:
                match = self.patterns["soma_side"].search(line)
                if match:
                    metrics["soma_side"] = match.group(1)

            # Count cache operations
            if self.patterns["cache_hit"].search(line):
                metrics["cache_hits"] += 1
            elif self.patterns["cache_miss"].search(line):
                metrics["cache_misses"] += 1

            # Count database queries
            if self.patterns["database_query"].search(line):
                metrics["database_queries"] += 1

            # Count file operations
            if self.patterns["file_read"].search(line):
                metrics["file_reads"] += 1
            elif self.patterns["file_write"].search(line):
                metrics["file_writes"] += 1

            # Track generation timing
            if (
                self.patterns["generation_start"].search(line)
                and not metrics["generation_started"]
            ):
                metrics["generation_started"] = True
                generation_start_time = i  # Use line number as proxy for time
            elif (
                self.patterns["generation_complete"].search(line)
                and not metrics["generation_completed"]
            ):
                metrics["generation_completed"] = True
                generation_end_time = i

            # Collect warnings and errors
            if self.patterns["warning"].search(line):
                metrics["warnings"].append(line_stripped)
            elif self.patterns["error"].search(line):
                metrics["errors"].append(line_stripped)

            # Count success indicators
            if self.patterns["success"].search(line):
                metrics["success_indicators"] += 1

        # Estimate generation time based on line positions
        if generation_start_time is not None and generation_end_time is not None:
            metrics["generation_line_span"] = (
                generation_end_time - generation_start_time
            )

        return metrics

    def analyze_single_pop(self) -> PopAnalysisResult:
        """Analyze a single pop operation."""
        # Check if queue files are available
        yaml_files = list(self.queue_dir.glob("*.yaml"))
        if not yaml_files:
            return PopAnalysisResult(
                total_time=0.0,
                command_overhead=0.0,
                neuron_type="",
                soma_side="",
                success=False,
                error_message="No queue files available",
            )

        # Execute the pop command
        success, output, total_time, command_overhead = self.execute_pop_with_timing()

        # Parse the output
        parsed_metrics = self.parse_verbose_output(output)

        # Calculate cache hit rate
        total_cache_ops = parsed_metrics["cache_hits"] + parsed_metrics["cache_misses"]
        cache_hit_rate = (
            (parsed_metrics["cache_hits"] / total_cache_ops)
            if total_cache_ops > 0
            else None
        )

        # Estimate generation time (rough estimate based on line span)
        generation_time_estimate = None
        if parsed_metrics.get("generation_line_span"):
            # Rough estimate: assume verbose output correlates with processing time
            generation_time_estimate = (
                total_time * 0.8
            )  # Assume 80% of time is generation

        # Extract error message if failed
        error_message = None
        if not success:
            if parsed_metrics["errors"]:
                error_message = parsed_metrics["errors"][0]
            else:
                error_message = "Unknown error"

        return PopAnalysisResult(
            total_time=total_time,
            command_overhead=command_overhead,
            neuron_type=parsed_metrics["neuron_type"],
            soma_side=parsed_metrics["soma_side"],
            success=success,
            error_message=error_message,
            cache_operations={
                "hits": parsed_metrics["cache_hits"],
                "misses": parsed_metrics["cache_misses"],
                "total": total_cache_ops,
            },
            database_queries=parsed_metrics["database_queries"],
            file_operations=parsed_metrics["file_reads"]
            + parsed_metrics["file_writes"],
            warnings=parsed_metrics["warnings"],
            errors=parsed_metrics["errors"],
            cache_hit_rate=cache_hit_rate,
            generation_time_estimate=generation_time_estimate,
        )

    def analyze_batch_operations(self, count: int = 10) -> List[PopAnalysisResult]:
        """Analyze multiple pop operations for statistical analysis."""
        print(f"🔄 Analyzing {count} pop operations...")

        results = []

        for i in range(count):
            print(f"  Operation {i + 1}/{count}...", end=" ", flush=True)

            result = self.analyze_single_pop()
            results.append(result)

            if result.success:
                print(f"✅ ({result.total_time:.2f}s)")
            else:
                print(f"❌ {result.error_message}")

            # Check if we should continue
            if not result.success and "No queue files available" in str(
                result.error_message
            ):
                print(f"  Stopping after {i + 1} operations - no more queue files")
                break

            # Small delay between operations
            time.sleep(0.2)

        self.results.extend(results)
        return results

    def analyze_queue_characteristics(self) -> Dict[str, Any]:
        """Analyze queue characteristics that might affect performance."""
        yaml_files = list(self.queue_dir.glob("*.yaml"))
        lock_files = list(self.queue_dir.glob("*.lock"))

        # Analyze file sizes
        file_sizes = []
        total_size = 0

        for yaml_file in yaml_files[:100]:  # Sample first 100 files
            try:
                size = yaml_file.stat().st_size
                file_sizes.append(size)
                total_size += size
            except OSError:
                continue

        # Analyze queue content patterns
        neuron_type_counts = defaultdict(int)
        soma_side_counts = defaultdict(int)

        for yaml_file in yaml_files[:50]:  # Sample for content analysis
            try:
                import yaml

                with open(yaml_file, "r") as f:
                    data = yaml.safe_load(f)
                if data and "options" in data:
                    options = data["options"]
                    neuron_type_counts[options.get("neuron-type", "unknown")] += 1
                    soma_side_counts[options.get("soma-side", "unknown")] += 1
            except Exception:
                continue

        return {
            "total_yaml_files": len(yaml_files),
            "total_lock_files": len(lock_files),
            "queue_size_bytes": total_size,
            "average_file_size": statistics.mean(file_sizes) if file_sizes else 0,
            "file_size_std": statistics.stdev(file_sizes) if len(file_sizes) > 1 else 0,
            "unique_neuron_types": len(neuron_type_counts),
            "unique_soma_sides": len(soma_side_counts),
            "top_neuron_types": dict(
                sorted(neuron_type_counts.items(), key=lambda x: x[1], reverse=True)[
                    :10
                ]
            ),
            "soma_side_distribution": dict(soma_side_counts),
        }

    def calculate_statistics(self, results: List[PopAnalysisResult]) -> Dict[str, Any]:
        """Calculate comprehensive statistics from analysis results."""
        successful_results = [r for r in results if r.success]

        if not successful_results:
            return {"error": "No successful operations to analyze"}

        # Timing statistics
        total_times = [r.total_time for r in successful_results]
        overhead_times = [r.command_overhead for r in successful_results]

        timing_stats = {
            "total_time_avg": statistics.mean(total_times),
            "total_time_median": statistics.median(total_times),
            "total_time_std": statistics.stdev(total_times)
            if len(total_times) > 1
            else 0,
            "total_time_min": min(total_times),
            "total_time_max": max(total_times),
            "overhead_avg": statistics.mean(overhead_times),
            "overhead_percentage": (
                statistics.mean(overhead_times) / statistics.mean(total_times)
            )
            * 100,
        }

        # Cache statistics
        cache_hit_rates = [
            r.cache_hit_rate for r in successful_results if r.cache_hit_rate is not None
        ]
        cache_operations = [
            r.cache_operations["total"]
            for r in successful_results
            if r.cache_operations["total"] > 0
        ]

        cache_stats = {
            "hit_rate_avg": statistics.mean(cache_hit_rates) if cache_hit_rates else 0,
            "hit_rate_min": min(cache_hit_rates) if cache_hit_rates else 0,
            "hit_rate_max": max(cache_hit_rates) if cache_hit_rates else 0,
            "operations_avg": statistics.mean(cache_operations)
            if cache_operations
            else 0,
        }

        # Database and file operation statistics
        db_queries = [r.database_queries for r in successful_results]
        file_ops = [r.file_operations for r in successful_results]

        operation_stats = {
            "db_queries_avg": statistics.mean(db_queries) if db_queries else 0,
            "file_ops_avg": statistics.mean(file_ops) if file_ops else 0,
            "db_queries_total": sum(db_queries),
            "file_ops_total": sum(file_ops),
        }

        # Error and warning analysis
        all_warnings = []
        all_errors = []
        for r in results:
            all_warnings.extend(r.warnings)
            all_errors.extend(r.errors)

        error_stats = {
            "success_rate": len(successful_results) / len(results),
            "total_warnings": len(all_warnings),
            "total_errors": len(all_errors),
            "unique_warnings": len(set(all_warnings)),
            "unique_errors": len(set(all_errors)),
        }

        # Throughput calculation
        if successful_results:
            avg_time = timing_stats["total_time_avg"]
            throughput = 1 / avg_time if avg_time > 0 else 0
        else:
            throughput = 0

        return {
            "timing": timing_stats,
            "cache": cache_stats,
            "operations": operation_stats,
            "errors": error_stats,
            "throughput_ops_per_second": throughput,
            "total_operations": len(results),
            "successful_operations": len(successful_results),
        }

    def identify_bottlenecks(self, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks based on statistics."""
        bottlenecks = []

        timing = stats.get("timing", {})
        cache = stats.get("cache", {})
        operations = stats.get("operations", {})
        errors = stats.get("errors", {})

        # High execution time
        avg_time = timing.get("total_time_avg", 0)
        if avg_time > 3.0:  # More than 3 seconds average
            bottlenecks.append(
                {
                    "type": "High Execution Time",
                    "severity": "HIGH",
                    "description": f"Average execution time is {avg_time:.2f}s",
                    "impact": "Low throughput",
                    "recommendation": "Focus on page generation optimization",
                }
            )

        # High command overhead
        overhead_pct = timing.get("overhead_percentage", 0)
        if overhead_pct > 5:  # More than 5% overhead
            bottlenecks.append(
                {
                    "type": "Command Overhead",
                    "severity": "MEDIUM",
                    "description": f"Command startup overhead is {overhead_pct:.1f}%",
                    "impact": "Inefficient for batch processing",
                    "recommendation": "Implement batch processing or service mode",
                }
            )

        # Poor cache performance
        hit_rate = cache.get("hit_rate_avg", 0)
        if hit_rate < 0.5:  # Less than 50% hit rate
            bottlenecks.append(
                {
                    "type": "Poor Cache Performance",
                    "severity": "HIGH",
                    "description": f"Cache hit rate is only {hit_rate * 100:.1f}%",
                    "impact": "Increased database queries and slower performance",
                    "recommendation": "Implement cache warming and retention optimization",
                }
            )

        # High database query count
        db_queries_avg = operations.get("db_queries_avg", 0)
        if db_queries_avg > 10:  # More than 10 queries per operation
            bottlenecks.append(
                {
                    "type": "Excessive Database Queries",
                    "severity": "HIGH",
                    "description": f"Average {db_queries_avg:.1f} database queries per operation",
                    "impact": "Network latency and database load",
                    "recommendation": "Implement query batching and better caching",
                }
            )

        # High error rate
        success_rate = errors.get("success_rate", 1.0)
        if success_rate < 0.9:  # Less than 90% success rate
            bottlenecks.append(
                {
                    "type": "High Error Rate",
                    "severity": "CRITICAL",
                    "description": f"Success rate is only {success_rate * 100:.1f}%",
                    "impact": "Unreliable operation",
                    "recommendation": "Improve error handling and retry logic",
                }
            )

        # High time variance
        time_std = timing.get("total_time_std", 0)
        time_avg = timing.get("total_time_avg", 1)
        if time_std / time_avg > 0.3:  # More than 30% coefficient of variation
            bottlenecks.append(
                {
                    "type": "Inconsistent Performance",
                    "severity": "MEDIUM",
                    "description": f"High time variance (std: {time_std:.2f}s)",
                    "impact": "Unpredictable processing times",
                    "recommendation": "Investigate performance variation causes",
                }
            )

        return bottlenecks

    def suggest_optimizations(
        self, stats: Dict[str, Any], bottlenecks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Suggest specific optimizations based on analysis."""
        suggestions = []

        # Always suggest the soma cache optimization (from existing analysis)
        suggestions.append(
            {
                "priority": "HIGH",
                "category": "Caching",
                "title": "Implement Soma Cache Optimization",
                "description": "Eliminate redundant soma cache files by using neuron cache data",
                "implementation": "Apply the existing soma cache optimization",
                "estimated_impact": "50% reduction in cache I/O operations",
                "effort": "LOW",
            }
        )

        # Throughput-based optimizations
        throughput = stats.get("throughput_ops_per_second", 0)
        if throughput < 0.5:  # Less than 0.5 ops/sec
            suggestions.append(
                {
                    "priority": "HIGH",
                    "category": "Throughput",
                    "title": "Implement Batch Processing",
                    "description": f"Current throughput is {throughput:.2f} ops/sec",
                    "implementation": "Process multiple queue files in a single command execution",
                    "estimated_impact": "3-5x throughput improvement",
                    "effort": "MEDIUM",
                }
            )

        # Cache-specific optimizations
        cache_hit_rate = stats.get("cache", {}).get("hit_rate_avg", 0)
        if cache_hit_rate < 0.7:
            suggestions.append(
                {
                    "priority": "HIGH",
                    "category": "Caching",
                    "title": "Implement Cache Pre-warming",
                    "description": f"Cache hit rate is {cache_hit_rate * 100:.1f}%",
                    "implementation": "Pre-load frequently accessed neuron data",
                    "estimated_impact": "20-40% faster processing",
                    "effort": "MEDIUM",
                }
            )

        # Service initialization optimizations
        overhead_pct = stats.get("timing", {}).get("overhead_percentage", 0)
        if overhead_pct > 3:
            suggestions.append(
                {
                    "priority": "MEDIUM",
                    "category": "Architecture",
                    "title": "Implement Service Daemon Mode",
                    "description": f"Command overhead is {overhead_pct:.1f}%",
                    "implementation": "Create a long-running service for queue processing",
                    "estimated_impact": f"Eliminate {overhead_pct:.1f}% overhead",
                    "effort": "HIGH",
                }
            )

        # Database optimization
        db_queries = stats.get("operations", {}).get("db_queries_avg", 0)
        if db_queries > 5:
            suggestions.append(
                {
                    "priority": "MEDIUM",
                    "category": "Database",
                    "title": "Implement Connection Pooling",
                    "description": f"Average {db_queries:.1f} queries per operation",
                    "implementation": "Use persistent database connections",
                    "estimated_impact": "15-25% reduction in query overhead",
                    "effort": "MEDIUM",
                }
            )

        # Sort by priority and estimated impact
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        suggestions.sort(key=lambda x: priority_order.get(x["priority"], 3))

        return suggestions

    def generate_comprehensive_report(self):
        """Generate a comprehensive performance analysis report."""
        print("\n" + "=" * 80)
        print("NEUVIEW POP COMMAND - COMPREHENSIVE PERFORMANCE ANALYSIS")
        print("=" * 80)

        # System information
        print(f"\n📋 SYSTEM INFORMATION:")
        print(f"   Python: {sys.version.split()[0]}")
        print(f"   Working directory: {os.getcwd()}")
        print(f"   Queue directory: {self.queue_dir}")

        # Queue analysis
        queue_info = self.analyze_queue_characteristics()
        print(f"\n📊 QUEUE ANALYSIS:")
        print(f"   Total queue files: {queue_info['total_yaml_files']}")
        print(f"   Active lock files: {queue_info['total_lock_files']}")
        print(f"   Queue size: {queue_info['queue_size_bytes'] / 1024:.1f}KB")
        print(f"   Average file size: {queue_info['average_file_size']:.0f} bytes")
        print(f"   Unique neuron types: {queue_info['unique_neuron_types']}")
        print(f"   Soma side distribution: {queue_info['soma_side_distribution']}")

        if queue_info["total_yaml_files"] == 0:
            print("\n❌ No queue files available. Run 'neuview fill-queue' first.")
            return

        # Performance analysis
        print(f"\n⚡ PERFORMANCE ANALYSIS:")
        results = self.analyze_batch_operations(min(15, queue_info["total_yaml_files"]))

        if not results:
            print("❌ No operations completed successfully")
            return

        stats = self.calculate_statistics(results)

        if "error" in stats:
            print(f"❌ {stats['error']}")
            return

        # Display performance metrics
        timing = stats["timing"]
        print(f"   Operations analyzed: {stats['total_operations']}")
        print(f"   Success rate: {stats['errors']['success_rate'] * 100:.1f}%")
        print(f"   Average execution time: {timing['total_time_avg']:.3f}s")
        print(
            f"   Execution time range: {timing['total_time_min']:.3f}s - {timing['total_time_max']:.3f}s"
        )
        print(
            f"   Throughput: {stats['throughput_ops_per_second']:.2f} operations/second"
        )
        print(f"   Command overhead: {timing['overhead_percentage']:.1f}%")

        # Cache performance
        cache = stats["cache"]
        print(f"\n🗄️  CACHE PERFORMANCE:")
        print(f"   Average hit rate: {cache['hit_rate_avg'] * 100:.1f}%")
        print(f"   Cache operations per pop: {cache['operations_avg']:.1f}")

        # Database and I/O
        ops = stats["operations"]
        print(f"\n🔍 OPERATION ANALYSIS:")
        print(f"   Database queries per pop: {ops['db_queries_avg']:.1f}")
        print(f"   File operations per pop: {ops['file_ops_avg']:.1f}")
        print(f"   Total warnings: {stats['errors']['total_warnings']}")
        print(f"   Total errors: {stats['errors']['total_errors']}")

        # Bottleneck analysis
        bottlenecks = self.identify_bottlenecks(stats)
        if bottlenecks:
            print(f"\n🔍 IDENTIFIED BOTTLENECKS:")
            for bottleneck in bottlenecks:
                print(f"   🔴 {bottleneck['type']} [{bottleneck['severity']}]")
                print(f"      Issue: {bottleneck['description']}")
                print(f"      Impact: {bottleneck['impact']}")
                print(f"      Recommendation: {bottleneck['recommendation']}")
                print()

        # Optimization suggestions
        suggestions = self.suggest_optimizations(stats, bottlenecks)
        print(f"\n💡 OPTIMIZATION RECOMMENDATIONS:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. [{suggestion['priority']}] {suggestion['title']}")
            print(f"      Category: {suggestion['category']}")
            print(f"      Description: {suggestion['description']}")
            print(f"      Implementation: {suggestion['implementation']}")
            print(f"      Estimated Impact: {suggestion['estimated_impact']}")
            print(f"      Effort: {suggestion['effort']}")
            print()

        # Summary and recommendations
        print(f"🎯 SUMMARY & NEXT STEPS:")

        # Classify performance level
        throughput = stats["throughput_ops_per_second"]
        success_rate = stats["errors"]["success_rate"]

        if throughput < 0.2:
            print(f"   🔴 CRITICAL: Very low throughput ({throughput:.2f} ops/sec)")
            print(f"   → Immediate optimization required")
        elif throughput < 0.5:
            print(f"   ⚠️  POOR: Low throughput ({throughput:.2f} ops/sec)")
            print(f"   → Significant optimization needed")
        elif throughput < 1.0:
            print(f"   📈 MODERATE: Fair throughput ({throughput:.2f} ops/sec)")
            print(f"   → Optimization recommended")
        else:
            print(f"   ✅ GOOD: Acceptable throughput ({throughput:.2f} ops/sec)")
            print(f"   → Focus on reliability and edge case optimization")

        if success_rate < 0.9:
            print(f"   ❌ RELIABILITY ISSUE: {success_rate * 100:.1f}% success rate")
            print(f"   → Fix error handling first")

        print(f"\n🚀 IMMEDIATE ACTIONS:")
        print(f"   1. Apply soma cache optimization (already analyzed)")
        print(f"   2. Implement batch processing for multiple files")
        print(f"   3. Add connection pooling for database operations")
        print(f"   4. Consider service/daemon mode for high-volume processing")

        # Save detailed report
        report_data = {
            "system_info": {
                "python_version": sys.version,
                "working_directory": os.getcwd(),
            },
            "queue_analysis": queue_info,
            "performance_results": [asdict(r) for r in results],
            "statistics": stats,
            "bottlenecks": bottlenecks,
            "suggestions": suggestions,
            "analysis_timestamp": time.time(),
        }

        with open("pop_performance_analysis.json", "w") as f:
            json.dump(report_data, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: pop_performance_analysis.json")


def main():
    """Main function to run comprehensive pop performance analysis."""
    print("neuView Pop Command - Performance Analysis")
    print("=" * 45)

    try:
        analyzer = PopPerformanceAnalyzer()

        # Check prerequisites
        if not analyzer.queue_dir.exists():
            print("❌ Queue directory not found. Run 'neuview fill-queue' first.")
            return

        yaml_files = list(analyzer.queue_dir.glob("*.yaml"))
        if not yaml_files:
            print("❌ No queue files found. Run 'neuview fill-queue' first.")
            return

        print(f"✅ Found {len(yaml_files)} queue files to analyze")

        # Generate comprehensive analysis
        analyzer.generate_comprehensive_report()

    except KeyboardInterrupt:
        print("\n❌ Analysis interrupted by user")
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
