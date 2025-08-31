"""
LRU Cache Strategy Implementation

This module provides a memory cache strategy with strict LRU (Least Recently Used)
eviction policy. Items are evicted when the cache reaches its maximum size.
"""

import threading
from typing import Any, Optional, List
from collections import OrderedDict
import logging

from ..base import CacheStrategy

logger = logging.getLogger(__name__)


class LRUCacheStrategy(CacheStrategy):
    """
    Memory cache strategy with strict LRU eviction.

    This strategy maintains a fixed-size cache where the least recently
    used items are evicted when the cache reaches its maximum capacity.
    No TTL support - items only expire when evicted due to size limits.
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize LRU cache strategy.

        Args:
            max_size: Maximum number of items to cache
        """
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._lock = threading.RLock()
        self.max_size = max_size

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        with self._lock:
            if key not in self._cache:
                return None

            # Move to end (most recently used)
            value = self._cache[key]
            self._cache.move_to_end(key)
            return value

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Ignored (LRU cache doesn't support TTL)
        """
        with self._lock:
            if key in self._cache:
                # Update existing key
                self._cache[key] = value
                self._cache.move_to_end(key)
            else:
                # Add new key
                self._cache[key] = value

                # Enforce size limit
                if len(self._cache) > self.max_size:
                    # Remove least recently used item
                    self._cache.popitem(last=False)

    def delete(self, key: str) -> bool:
        """
        Remove a value from the cache.

        Args:
            key: Cache key

        Returns:
            True if key was found and deleted, False otherwise
        """
        with self._lock:
            return self._cache.pop(key, None) is not None

    def clear(self) -> None:
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()

    def contains(self, key: str) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        with self._lock:
            return key in self._cache

    def keys(self) -> List[str]:
        """
        Get all cache keys.

        Returns:
            List of all cache keys
        """
        with self._lock:
            return list(self._cache.keys())

    def size(self) -> int:
        """
        Get the number of items in the cache.

        Returns:
            Number of cached items
        """
        with self._lock:
            return len(self._cache)
