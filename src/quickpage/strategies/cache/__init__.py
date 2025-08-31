"""
Cache Strategy Implementations for QuickPage Phase 3

This module provides various caching strategies that can be used for template
and resource management. Each strategy implements different caching mechanisms
with various performance characteristics and eviction policies.

Cache Strategies:
- MemoryCacheStrategy: In-memory caching with LRU eviction
- FileCacheStrategy: File-based persistent caching
- LRUCacheStrategy: Memory cache with strict LRU eviction
- CompositeCacheStrategy: Multi-level caching (memory + file)
"""

# Import base strategy interface
from ..base import CacheStrategy

# Import strategy exceptions
from ..exceptions import CacheError

# Import individual cache strategy implementations
from .memory_cache import MemoryCacheStrategy
from .file_cache import FileCacheStrategy
from .lru_cache import LRUCacheStrategy
from .composite_cache import CompositeCacheStrategy

# Export all cache strategies and interfaces
__all__ = [
    "CacheStrategy",
    "CacheError",
    "MemoryCacheStrategy",
    "FileCacheStrategy",
    "LRUCacheStrategy",
    "CompositeCacheStrategy",
]
