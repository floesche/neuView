"""
Performance optimization module for eyemap visualization.

This module provides caching, memory optimization, and performance monitoring
capabilities to enhance the performance of eyemap generation operations.

Components:
- cache: Caching strategies and decorators
- memory: Memory optimization utilities
- monitoring: Performance monitoring and metrics
- optimizers: Specialized optimization classes
"""

from .cache import (
    CacheManager,
    LRUCache,
    cached_method,
    coordinate_cache,
    color_cache,
    metadata_cache
)

from .memory import (
    MemoryOptimizer,
    StreamingHexagonProcessor,
    memory_efficient_processing,
    memory_limit_context
)

from .monitoring import (
    PerformanceMonitor,
    performance_timer,
    memory_tracker,
    cache_metrics,
    BatchPerformanceAnalyzer,
    get_performance_monitor,
    configure_performance_monitoring
)

from .optimizers import (
    CoordinateOptimizer,
    ColorOptimizer,
    MetadataOptimizer,
    HexagonCollectionOptimizer,
    PerformanceOptimizerFactory
)

__all__ = [
    # Cache components
    'CacheManager',
    'LRUCache',
    'cached_method',
    'coordinate_cache',
    'color_cache',
    'metadata_cache',

    # Memory optimization
    'MemoryOptimizer',
    'StreamingHexagonProcessor',
    'memory_efficient_processing',
    'memory_limit_context',

    # Performance monitoring
    'PerformanceMonitor',
    'performance_timer',
    'memory_tracker',
    'cache_metrics',
    'BatchPerformanceAnalyzer',
    'get_performance_monitor',
    'configure_performance_monitoring',

    # Optimizers
    'CoordinateOptimizer',
    'ColorOptimizer',
    'MetadataOptimizer',
    'HexagonCollectionOptimizer',
    'PerformanceOptimizerFactory'
]
