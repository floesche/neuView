"""
Composite Cache Strategy Implementation

This module provides a multi-level caching strategy that combines different
cache backends (e.g., memory + file) for optimal performance and persistence.
"""

import threading
from typing import Any, Optional, List
import logging

from ..base import CacheStrategy

logger = logging.getLogger(__name__)


class CompositeCacheStrategy(CacheStrategy):
    """
    Multi-level cache strategy that combines multiple cache backends.

    This strategy uses multiple cache levels (e.g., fast memory cache
    backed by persistent file cache) to provide both performance and
    persistence. Items are checked in order of cache levels, and
    writes propagate to all levels.
    """

    def __init__(self, primary_cache: CacheStrategy, secondary_cache: CacheStrategy):
        """
        Initialize composite cache strategy.

        Args:
            primary_cache: Fast cache (e.g., memory cache)
            secondary_cache: Persistent cache (e.g., file cache)
        """
        self.primary_cache = primary_cache
        self.secondary_cache = secondary_cache
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.

        Checks primary cache first, then secondary cache.
        If found in secondary but not primary, promotes to primary.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            # Try primary cache first
            value = self.primary_cache.get(key)
            if value is not None:
                return value

            # Try secondary cache
            value = self.secondary_cache.get(key)
            if value is not None:
                # Promote to primary cache
                try:
                    self.primary_cache.put(key, value)
                except Exception as e:
                    logger.warning(f"Failed to promote key {key} to primary cache: {e}")
                return value

            return None

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store a value in the cache.

        Stores in both primary and secondary caches.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None for no expiration)
        """
        with self._lock:
            # Store in both caches
            try:
                self.primary_cache.put(key, value, ttl)
            except Exception as e:
                logger.warning(f"Failed to store key {key} in primary cache: {e}")

            try:
                self.secondary_cache.put(key, value, ttl)
            except Exception as e:
                logger.warning(f"Failed to store key {key} in secondary cache: {e}")

    def delete(self, key: str) -> bool:
        """
        Remove a value from the cache.

        Removes from both primary and secondary caches.

        Args:
            key: Cache key

        Returns:
            True if key was found in any cache and deleted, False otherwise
        """
        with self._lock:
            primary_deleted = False
            secondary_deleted = False

            try:
                primary_deleted = self.primary_cache.delete(key)
            except Exception as e:
                logger.warning(f"Failed to delete key {key} from primary cache: {e}")

            try:
                secondary_deleted = self.secondary_cache.delete(key)
            except Exception as e:
                logger.warning(f"Failed to delete key {key} from secondary cache: {e}")

            return primary_deleted or secondary_deleted

    def clear(self) -> None:
        """Clear all cached values from both caches."""
        with self._lock:
            try:
                self.primary_cache.clear()
            except Exception as e:
                logger.warning(f"Failed to clear primary cache: {e}")

            try:
                self.secondary_cache.clear()
            except Exception as e:
                logger.warning(f"Failed to clear secondary cache: {e}")

    def contains(self, key: str) -> bool:
        """
        Check if a key exists in any cache level.

        Args:
            key: Cache key

        Returns:
            True if key exists in any cache, False otherwise
        """
        return self.get(key) is not None

    def keys(self) -> List[str]:
        """
        Get all cache keys from both caches.

        Returns:
            List of all unique cache keys
        """
        with self._lock:
            primary_keys = set()
            secondary_keys = set()

            try:
                primary_keys = set(self.primary_cache.keys())
            except Exception as e:
                logger.warning(f"Failed to get keys from primary cache: {e}")

            try:
                secondary_keys = set(self.secondary_cache.keys())
            except Exception as e:
                logger.warning(f"Failed to get keys from secondary cache: {e}")

            return list(primary_keys | secondary_keys)

    def size(self) -> int:
        """
        Get the number of unique items across both caches.

        Returns:
            Number of unique cached items
        """
        return len(self.keys())

    def cleanup_expired(self) -> None:
        """Remove expired items from both caches."""
        with self._lock:
            try:
                if hasattr(self.primary_cache, 'cleanup_expired'):
                    self.primary_cache.cleanup_expired()
            except Exception as e:
                logger.warning(f"Failed to cleanup primary cache: {e}")

            try:
                if hasattr(self.secondary_cache, 'cleanup_expired'):
                    self.secondary_cache.cleanup_expired()
            except Exception as e:
                logger.warning(f"Failed to cleanup secondary cache: {e}")
