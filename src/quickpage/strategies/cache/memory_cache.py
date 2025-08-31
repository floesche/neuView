"""
Memory Cache Strategy Implementation

This module provides an in-memory cache strategy with optional TTL and size limits.
The strategy stores cached items in memory for fast access with LRU eviction support.
"""

import time
import threading
from typing import Any, Dict, Optional, List, Tuple
from collections import OrderedDict
import logging

from .. import CacheStrategy, CacheError

logger = logging.getLogger(__name__)


class MemoryCacheStrategy(CacheStrategy):
    """
    In-memory cache strategy with optional TTL and size limits.

    This strategy stores cached items in memory for fast access.
    Items can have TTL (time-to-live) expiration and the cache
    can have a maximum size with LRU eviction.
    """

    def __init__(self, max_size: Optional[int] = None, default_ttl: Optional[int] = None):
        """
        Initialize memory cache strategy.

        Args:
            max_size: Maximum number of items to cache (None for unlimited)
            default_ttl: Default TTL in seconds (None for no expiration)
        """
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._lock = threading.RLock()
        self.max_size = max_size
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                return None

            value, expiry = self._cache[key]

            # Check if expired
            if expiry > 0 and time.time() > expiry:
                del self._cache[key]
                return None

            # Move to end (LRU)
            self._cache.move_to_end(key)
            return value

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None for no expiration)
        """
        with self._lock:
            # Calculate expiry time
            if ttl is not None:
                expiry = time.time() + ttl
            elif self.default_ttl is not None:
                expiry = time.time() + self.default_ttl
            else:
                expiry = 0  # No expiration

            self._cache[key] = (value, expiry)
            self._cache.move_to_end(key)

            # Enforce size limit
            if self.max_size is not None:
                while len(self._cache) > self.max_size:
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
            True if key exists and is not expired, False otherwise
        """
        return self.get(key) is not None

    def keys(self) -> List[str]:
        """
        Get all cache keys.

        Returns:
            List of all cache keys
        """
        with self._lock:
            # Clean up expired items first
            self.cleanup_expired()
            return list(self._cache.keys())

    def size(self) -> int:
        """
        Get the number of items in the cache.

        Returns:
            Number of cached items
        """
        with self._lock:
            self.cleanup_expired()
            return len(self._cache)

    def cleanup_expired(self) -> None:
        """Remove expired items from cache."""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, (_, expiry) in self._cache.items()
                if expiry > 0 and current_time > expiry
            ]
            for key in expired_keys:
                del self._cache[key]
