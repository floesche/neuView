"""
Performance manager for managing optimization and monitoring.

This module provides the PerformanceManager class that handles all aspects
of performance optimization and monitoring for grid generation operations.
It coordinates with performance optimization services and provides
centralized performance management capabilities.

The PerformanceManager follows the single responsibility principle by
focusing solely on performance-related concerns while integrating
with the broader orchestration framework.
"""

import logging
import time
import threading
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager

from ..exceptions import (
    EyemapError, DataProcessingError, ErrorContext
)
from ..config_manager import EyemapConfiguration
from ..dependency_injection import EyemapServiceContainer

# Try to import performance modules
try:
    from ..performance import (
        PerformanceOptimizerFactory,
        get_performance_monitor,
        MemoryOptimizer
    )
    PERFORMANCE_AVAILABLE = True
except ImportError:
    PERFORMANCE_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations."""
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    memory_usage_start: Optional[float] = None
    memory_usage_end: Optional[float] = None
    cpu_usage: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> float:
        """Get operation duration in seconds."""
        if self.end_time is None:
            return 0.0
        return self.end_time - self.start_time

    @property
    def memory_delta(self) -> Optional[float]:
        """Get memory usage change."""
        if self.memory_usage_start is None or self.memory_usage_end is None:
            return None
        return self.memory_usage_end - self.memory_usage_start


@dataclass
class BatchPerformanceResult:
    """Result of batch performance optimization."""
    total_operations: int
    successful_operations: int
    total_duration: float
    average_duration: float
    memory_efficiency: Optional[float] = None
    optimization_applied: List[str] = field(default_factory=list)
    performance_metrics: List[PerformanceMetrics] = field(default_factory=list)


class PerformanceManager:
    """
    Manages performance optimization and monitoring.

    This class provides centralized performance management including
    operation monitoring, batch optimization, memory management,
    and performance analytics for grid generation workflows.
    """

    def __init__(self, container: EyemapServiceContainer, enable_optimization: bool = True):
        """
        Initialize performance manager with dependency injection.

        Args:
            container: Service container for dependency resolution
            enable_optimization: Whether to enable performance optimizations
        """
        self.container = container
        self.config = container.resolve(EyemapConfiguration)
        self.enable_optimization = enable_optimization and PERFORMANCE_AVAILABLE

        # Initialize performance tracking
        self._metrics_history: List[PerformanceMetrics] = []
        self._metrics_lock = threading.Lock()
        self._active_operations: Dict[str, PerformanceMetrics] = {}

        # Initialize performance services if available
        if self.enable_optimization:
            try:
                self.memory_optimizer = container.try_resolve(MemoryOptimizer)
                self.performance_monitor = container.try_resolve(type(get_performance_monitor()))

                optimizer_factory = container.try_resolve(PerformanceOptimizerFactory)
                self.optimizers = optimizer_factory.create_full_optimizer_suite() if optimizer_factory else None

                logger.debug("Performance manager initialized with optimization enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize performance services: {e}")
                self.enable_optimization = False
                self._initialize_dummy_services()
        else:
            self._initialize_dummy_services()

        logger.debug(f"PerformanceManager initialized (optimization: {self.enable_optimization})")

    def _initialize_dummy_services(self):
        """Initialize dummy services when performance features are not available."""
        self.memory_optimizer = None
        self.performance_monitor = None
        self.optimizers = None

    @contextmanager
    def monitor_operation(self, operation_name: str, **metadata):
        """
        Context manager for monitoring operation performance.

        Args:
            operation_name: Name of the operation to monitor
            **metadata: Additional metadata to track

        Yields:
            PerformanceMetrics object for the operation
        """
        metrics = PerformanceMetrics(
            operation_name=operation_name,
            start_time=time.time(),
            metadata=metadata
        )

        # Record memory usage if available
        if self.memory_optimizer:
            try:
                metrics.memory_usage_start = self.memory_optimizer.get_current_memory_usage()
            except Exception:
                pass

        # Track active operation
        operation_id = f"{operation_name}_{metrics.start_time}"
        self._active_operations[operation_id] = metrics

        try:
            yield metrics
            metrics.success = True
        except Exception as e:
            metrics.success = False
            metrics.error_message = str(e)
            raise
        finally:
            # Complete metrics
            metrics.end_time = time.time()

            if self.memory_optimizer:
                try:
                    metrics.memory_usage_end = self.memory_optimizer.get_current_memory_usage()
                except Exception:
                    pass

            # Remove from active operations and add to history
            self._active_operations.pop(operation_id, None)
            self._add_metrics_to_history(metrics)

    def execute_batch_operations(self, operations: List[Any], max_workers: Optional[int] = None) -> List[Any]:
        """
        Execute operations in batch with performance optimization.

        Args:
            operations: List of operations (commands) to execute
            max_workers: Maximum number of worker threads

        Returns:
            List of operation results

        Raises:
            DataProcessingError: If batch execution fails
        """
        if not operations:
            return []

        with ErrorContext("batch_operation_execution", operation_count=len(operations)):
            try:
                # Determine optimal worker count
                if max_workers is None:
                    max_workers = self._calculate_optimal_workers(len(operations))

                results = []

                if max_workers == 1 or not self.enable_optimization:
                    # Sequential execution
                    for operation in operations:
                        with self.monitor_operation(f"batch_operation_{len(results)}",
                                                  operation_type=type(operation).__name__):
                            result = operation.execute()
                            results.append(result)
                else:
                    # Parallel execution
                    results = self._execute_parallel_operations(operations, max_workers)

                logger.debug(f"Batch execution completed: {len(results)} operations")
                return results

            except Exception as e:
                error_message = f"Batch operation execution failed: {str(e)}"
                logger.error(error_message)
                raise DataProcessingError(
                    error_message,
                    operation="batch_operation_execution"
                ) from e

    def optimize_batch_results(self, results: List[Any]) -> List[Any]:
        """
        Apply batch-level optimizations to results.

        Args:
            results: List of assembly results to optimize

        Returns:
            Optimized results
        """
        if not results or not self.enable_optimization:
            return results

        try:
            with self.monitor_operation("batch_result_optimization", result_count=len(results)):
                optimized_results = []

                for result in results:
                    try:
                        # Apply memory optimization if available
                        if self.memory_optimizer and hasattr(result, 'assembled_result'):
                            optimized_content = self.memory_optimizer.optimize_content(
                                result.assembled_result
                            )
                            if optimized_content != result.assembled_result:
                                result.assembled_result = optimized_content
                                if hasattr(result, 'metadata') and result.metadata:
                                    result.metadata.optimization_applied.append('memory_optimization')

                        optimized_results.append(result)

                    except Exception as e:
                        logger.warning(f"Failed to optimize result: {e}")
                        optimized_results.append(result)

                logger.debug(f"Batch result optimization completed for {len(optimized_results)} results")
                return optimized_results

        except Exception as e:
            logger.warning(f"Batch result optimization failed: {e}")
            return results

    def get_performance_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive performance statistics.

        Returns:
            Dictionary of performance statistics
        """
        with self._metrics_lock:
            if not self._metrics_history:
                return {
                    'total_operations': 0,
                    'optimization_enabled': self.enable_optimization
                }

            successful_operations = [m for m in self._metrics_history if m.success]
            failed_operations = [m for m in self._metrics_history if not m.success]

            total_duration = sum(m.duration for m in self._metrics_history)
            avg_duration = total_duration / len(self._metrics_history)

            # Memory statistics
            memory_metrics = [m for m in self._metrics_history if m.memory_delta is not None]
            avg_memory_delta = sum(m.memory_delta for m in memory_metrics) / len(memory_metrics) if memory_metrics else None

            # Operation type statistics
            operation_types = {}
            for metrics in self._metrics_history:
                op_type = metrics.operation_name
                if op_type not in operation_types:
                    operation_types[op_type] = {'count': 0, 'total_duration': 0, 'success_count': 0}

                operation_types[op_type]['count'] += 1
                operation_types[op_type]['total_duration'] += metrics.duration
                if metrics.success:
                    operation_types[op_type]['success_count'] += 1

            # Calculate average durations by operation type
            for op_type, stats in operation_types.items():
                stats['avg_duration'] = stats['total_duration'] / stats['count']
                stats['success_rate'] = stats['success_count'] / stats['count']

            return {
                'total_operations': len(self._metrics_history),
                'successful_operations': len(successful_operations),
                'failed_operations': len(failed_operations),
                'success_rate': len(successful_operations) / len(self._metrics_history),
                'total_duration': total_duration,
                'average_duration': avg_duration,
                'average_memory_delta': avg_memory_delta,
                'optimization_enabled': self.enable_optimization,
                'active_operations': len(self._active_operations),
                'operation_types': operation_types
            }

    def clear_performance_history(self) -> None:
        """Clear performance metrics history."""
        with self._metrics_lock:
            self._metrics_history.clear()
            logger.debug("Performance history cleared")

    def optimize_memory_usage(self) -> Dict[str, Any]:
        """
        Perform memory optimization.

        Returns:
            Dictionary with optimization results
        """
        if not self.enable_optimization or not self.memory_optimizer:
            return {'optimization_available': False}

        try:
            with self.monitor_operation("memory_optimization"):
                initial_memory = self.memory_optimizer.get_current_memory_usage()

                # Perform memory optimization
                optimization_result = self.memory_optimizer.optimize_memory()

                final_memory = self.memory_optimizer.get_current_memory_usage()
                memory_saved = initial_memory - final_memory if initial_memory and final_memory else 0

                return {
                    'optimization_available': True,
                    'initial_memory_mb': initial_memory,
                    'final_memory_mb': final_memory,
                    'memory_saved_mb': memory_saved,
                    'optimization_details': optimization_result
                }

        except Exception as e:
            logger.warning(f"Memory optimization failed: {e}")
            return {
                'optimization_available': True,
                'error': str(e)
            }

    def _execute_parallel_operations(self, operations: List[Any], max_workers: int) -> List[Any]:
        """
        Execute operations in parallel using thread pool.

        Args:
            operations: List of operations to execute
            max_workers: Maximum number of worker threads

        Returns:
            List of operation results
        """
        results = [None] * len(operations)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all operations
            future_to_index = {}
            for i, operation in enumerate(operations):
                future = executor.submit(self._execute_monitored_operation, operation, i)
                future_to_index[future] = i

            # Collect results
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    result = future.result()
                    results[index] = result
                except Exception as e:
                    logger.error(f"Operation {index} failed: {e}")
                    # Create error result
                    from .commands import CommandResult
                    results[index] = CommandResult(
                        success=False,
                        error_message=f"Parallel execution failed: {str(e)}"
                    )

        return results

    def _execute_monitored_operation(self, operation: Any, operation_index: int) -> Any:
        """
        Execute a single operation with monitoring.

        Args:
            operation: Operation to execute
            operation_index: Index of the operation in the batch

        Returns:
            Operation result
        """
        operation_name = f"parallel_operation_{operation_index}"
        with self.monitor_operation(operation_name,
                                  operation_type=type(operation).__name__,
                                  operation_index=operation_index):
            return operation.execute()

    def _calculate_optimal_workers(self, operation_count: int) -> int:
        """
        Calculate optimal number of worker threads.

        Args:
            operation_count: Number of operations to execute

        Returns:
            Optimal number of workers
        """
        import os

        # Base on CPU count and operation count
        cpu_count = os.cpu_count() or 1

        # Conservative approach: use at most half the CPU cores
        max_workers = max(1, cpu_count // 2)

        # Don't create more workers than operations
        optimal_workers = min(max_workers, operation_count)

        # For small batches, use sequential execution
        if operation_count <= 2:
            optimal_workers = 1

        logger.debug(f"Calculated optimal workers: {optimal_workers} for {operation_count} operations")
        return optimal_workers

    def _add_metrics_to_history(self, metrics: PerformanceMetrics) -> None:
        """
        Add metrics to history with thread safety.

        Args:
            metrics: Performance metrics to add
        """
        with self._metrics_lock:
            self._metrics_history.append(metrics)

            # Limit history size to prevent memory growth
            max_history_size = 1000
            if len(self._metrics_history) > max_history_size:
                self._metrics_history = self._metrics_history[-max_history_size:]

    def create_performance_report(self) -> Dict[str, Any]:
        """
        Create comprehensive performance report.

        Returns:
            Detailed performance report
        """
        stats = self.get_performance_statistics()

        report = {
            'summary': stats,
            'recommendations': self._generate_performance_recommendations(stats),
            'recent_operations': self._get_recent_operation_summary(),
            'memory_usage': self._get_memory_usage_summary(),
            'optimization_status': {
                'enabled': self.enable_optimization,
                'available_optimizers': self._get_available_optimizers(),
                'active_operations': len(self._active_operations)
            }
        }

        return report

    def _generate_performance_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """
        Generate performance recommendations based on statistics.

        Args:
            stats: Performance statistics

        Returns:
            List of performance recommendations
        """
        recommendations = []

        if stats['total_operations'] == 0:
            return ["No operations recorded yet"]

        # Success rate recommendations
        if stats['success_rate'] < 0.9:
            recommendations.append("Success rate is below 90%. Consider investigating frequent failures.")

        # Duration recommendations
        if stats['average_duration'] > 5.0:
            recommendations.append("Average operation duration is high. Consider enabling optimization.")

        # Memory recommendations
        if stats.get('average_memory_delta') and stats['average_memory_delta'] > 100:
            recommendations.append("High memory usage detected. Consider memory optimization.")

        # Optimization recommendations
        if not self.enable_optimization:
            recommendations.append("Performance optimization is disabled. Enable for better performance.")

        if not recommendations:
            recommendations.append("Performance is within acceptable parameters.")

        return recommendations

    def _get_recent_operation_summary(self) -> List[Dict[str, Any]]:
        """Get summary of recent operations."""
        with self._metrics_lock:
            recent_ops = self._metrics_history[-10:] if self._metrics_history else []
            return [
                {
                    'operation': op.operation_name,
                    'duration': round(op.duration, 3),
                    'success': op.success,
                    'memory_delta': round(op.memory_delta, 2) if op.memory_delta else None
                }
                for op in recent_ops
            ]

    def _get_memory_usage_summary(self) -> Dict[str, Any]:
        """Get memory usage summary."""
        if not self.memory_optimizer:
            return {'available': False}

        try:
            current_usage = self.memory_optimizer.get_current_memory_usage()
            return {
                'available': True,
                'current_usage_mb': current_usage,
                'optimization_available': True
            }
        except Exception as e:
            return {
                'available': True,
                'error': str(e)
            }

    def _get_available_optimizers(self) -> List[str]:
        """Get list of available optimizers."""
        optimizers = []

        if self.memory_optimizer:
            optimizers.append('memory_optimizer')

        if self.performance_monitor:
            optimizers.append('performance_monitor')

        if self.optimizers:
            optimizers.append('optimization_suite')

        return optimizers
