"""
Memory cache repository adapter for the infrastructure layer.

This adapter implements the CacheRepository port using a simple
in-memory dictionary with TTL support.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from ...core.ports import CacheRepository

logger = logging.getLogger(__name__)


class MemoryCacheRepository(CacheRepository):
    """
    Cache repository adapter using in-memory storage.

    This adapter implements the CacheRepository port using a simple
    in-memory dictionary with TTL support.
    """

    def __init__(self, default_ttl: int = 3600):
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _is_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if a cache entry is expired."""
        if 'expires_at' not in cache_entry:
            return False
        return datetime.now() > cache_entry['expires_at']

    def _cleanup_expired(self):
        """Remove expired entries from cache."""
        expired_keys = [
            key for key, entry in self._cache.items()
            if self._is_expired(entry)
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    async def get(self, key: str) -> Optional[Any]:
        """
        Get a cached value by key.

        Args:
            key: The cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        try:
            # Periodic cleanup
            if len(self._cache) % 100 == 0:
                self._cleanup_expired()

            if key not in self._cache:
                return None

            entry = self._cache[key]

            # Check expiration
            if self._is_expired(entry):
                del self._cache[key]
                return None

            logger.debug(f"Cache hit: {key}")
            return entry['value']

        except Exception as e:
            logger.error(f"Failed to get cache key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a cached value.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Time to live in seconds (optional)
        """
        try:
            expires_at = None
            if ttl is not None:
                expires_at = datetime.now() + timedelta(seconds=ttl)
            elif self.default_ttl > 0:
                expires_at = datetime.now() + timedelta(seconds=self.default_ttl)

            self._cache[key] = {
                'value': value,
                'created_at': datetime.now(),
                'expires_at': expires_at
            }

            logger.debug(f"Cache set: {key} (TTL: {ttl or self.default_ttl}s)")

        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")

    async def delete(self, key: str) -> bool:
        """
        Delete a cached value.

        Args:
            key: The cache key

        Returns:
            True if the key was deleted, False if it didn't exist
        """
        try:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache delete: {key}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {e}")
            return False

    async def clear(self) -> None:
        """Clear all cached values."""
        try:
            count = len(self._cache)
            self._cache.clear()
            logger.debug(f"Cache cleared: {count} entries")

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            key: The cache key

        Returns:
            True if the key exists and is not expired, False otherwise
        """
        try:
            if key not in self._cache:
                return False

            entry = self._cache[key]
            if self._is_expired(entry):
                del self._cache[key]
                return False

            return True

        except Exception as e:
            logger.error(f"Failed to check cache key existence {key}: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            # Clean up first
            self._cleanup_expired()

            total_entries = len(self._cache)
            total_size = sum(
                len(str(entry['value'])) for entry in self._cache.values()
            )

            return {
                'total_entries': total_entries,
                'total_size_bytes': total_size,
                'default_ttl': self.default_ttl
            }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {'error': str(e)}
