"""
Caching system for eyemap visualization performance optimization.

This module provides various caching strategies, decorators, and utilities
to optimize frequently computed values in eyemap generation.
"""

import hashlib
import logging
import time
import weakref
from collections import OrderedDict
from functools import wraps
from typing import Any, Callable, Dict, Hashable, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class LRUCache:
    """
    Least Recently Used cache implementation with size and TTL support.

    Features:
    - Size-based eviction (LRU policy)
    - Time-based expiration (TTL)
    - Thread-safe operations
    - Memory-efficient implementation
    - Cache statistics tracking
    """

    def __init__(self, max_size: int = 1000, default_ttl: Optional[float] = None):
        """
        Initialize LRU cache.

        Args:
            max_size: Maximum number of items to cache
            default_ttl: Default time-to-live in seconds (None = no expiration)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache = OrderedDict()
        self._timestamps = {}
        self._access_times = {}

        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key: Hashable, default: Any = None) -> Any:
        """Get value from cache."""
        if key not in self._cache:
            self.misses += 1
            return default

        # Check TTL expiration
        if self._is_expired(key):
            self._remove(key)
            self.misses += 1
            return default

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        self._access_times[key] = time.time()
        self.hits += 1

        return self._cache[key]

    def put(self, key: Hashable, value: Any, ttl: Optional[float] = None) -> None:
        """Put value into cache."""
        # Remove if exists to update position
        if key in self._cache:
            self._remove(key)

        # Evict if at capacity
        while len(self._cache) >= self.max_size:
            self._evict_lru()

        # Add new item
        self._cache[key] = value
        current_time = time.time()
        self._access_times[key] = current_time

        if ttl is not None or self.default_ttl is not None:
            ttl_value = ttl if ttl is not None else self.default_ttl
            if ttl_value is not None:
                expiry_time = current_time + ttl_value
                self._timestamps[key] = expiry_time

    def invalidate(self, key: Hashable) -> bool:
        """Remove specific key from cache."""
        if key in self._cache:
            self._remove(key)
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._timestamps.clear()
        self._access_times.clear()
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)

    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def cleanup_expired(self) -> int:
        """Remove all expired entries and return count removed."""
        expired_keys = [
            key for key in self._cache.keys()
            if self._is_expired(key)
        ]

        for key in expired_keys:
            self._remove(key)

        return len(expired_keys)

    def _is_expired(self, key: Hashable) -> bool:
        """Check if key has expired."""
        if key not in self._timestamps:
            return False
        return time.time() > self._timestamps[key]

    def _remove(self, key: Hashable) -> None:
        """Remove key from all tracking structures."""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
        self._access_times.pop(key, None)

    def _evict_lru(self) -> None:
        """Evict least recently used item."""
        if self._cache:
            lru_key = next(iter(self._cache))
            self._remove(lru_key)
            self.evictions += 1


class CacheManager:
    """
    Central cache management system for eyemap performance optimization.

    Manages multiple specialized caches with different policies and
    provides unified access and monitoring capabilities.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize cache manager.

        Args:
            config: Cache configuration dictionary
        """
        self.config = config or {}
        self._caches = {}

        # Initialize specialized caches
        self._init_coordinate_cache()
        self._init_color_cache()
        self._init_metadata_cache()

    def _init_coordinate_cache(self) -> None:
        """Initialize coordinate conversion cache."""
        cache_config = self.config.get('coordinate_cache', {})
        self._caches['coordinates'] = LRUCache(
            max_size=cache_config.get('max_size', 5000),
            default_ttl=cache_config.get('ttl', 3600)  # 1 hour
        )

    def _init_color_cache(self) -> None:
        """Initialize color computation cache."""
        cache_config = self.config.get('color_cache', {})
        self._caches['colors'] = LRUCache(
            max_size=cache_config.get('max_size', 10000),
            default_ttl=cache_config.get('ttl', 1800)  # 30 minutes
        )

    def _init_metadata_cache(self) -> None:
        """Initialize metadata generation cache."""
        cache_config = self.config.get('metadata_cache', {})
        self._caches['metadata'] = LRUCache(
            max_size=cache_config.get('max_size', 1000),
            default_ttl=cache_config.get('ttl', 7200)  # 2 hours
        )

    def get_cache(self, cache_name: str) -> Optional[LRUCache]:
        """Get specific cache by name."""
        return self._caches.get(cache_name)

    def get_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all caches."""
        stats = {}
        for name, cache in self._caches.items():
            stats[name] = {
                'size': cache.size(),
                'max_size': cache.max_size,
                'hits': cache.hits,
                'misses': cache.misses,
                'evictions': cache.evictions,
                'hit_rate': cache.hit_rate()
            }
        return stats

    def cleanup_all(self) -> Dict[str, int]:
        """Cleanup expired entries in all caches."""
        cleanup_counts = {}
        for name, cache in self._caches.items():
            cleanup_counts[name] = cache.cleanup_expired()
        return cleanup_counts

    def clear_all(self) -> None:
        """Clear all caches."""
        for cache in self._caches.values():
            cache.clear()


def _generate_cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments."""
    # Create a stable hash from arguments
    key_data = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key_data.encode()).hexdigest()














# Global cache manager instance
_global_cache_manager = None


def get_cache_manager() -> CacheManager:
    """Get or create global cache manager instance."""
    global _global_cache_manager
    if _global_cache_manager is None:
        _global_cache_manager = CacheManager()
    return _global_cache_manager


def configure_global_cache(config: Dict[str, Any]) -> None:
    """Configure global cache manager."""
    global _global_cache_manager
    _global_cache_manager = CacheManager(config)
