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

import time
import pickle
import hashlib
import threading
from pathlib import Path
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
        """Get a value from the cache."""
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
        """Store a value in the cache."""
        with self._lock:
            # Calculate expiry time
            if ttl is not None:
                expiry = time.time() + ttl
            elif self.default_ttl is not None:
                expiry = time.time() + self.default_ttl
            else:
                expiry = 0  # No expiration

            # Store value
            self._cache[key] = (value, expiry)
            self._cache.move_to_end(key)

            # Evict oldest if over size limit
            if self.max_size and len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    def delete(self, key: str) -> bool:
        """Remove a value from the cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()

    def contains(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        return self.get(key) is not None

    def keys(self) -> List[str]:
        """Get all cache keys."""
        with self._lock:
            # Clean up expired items first
            current_time = time.time()
            expired_keys = [
                k for k, (_, expiry) in self._cache.items()
                if expiry > 0 and current_time > expiry
            ]
            for k in expired_keys:
                del self._cache[k]

            return list(self._cache.keys())

    def size(self) -> int:
        """Get the number of items in the cache."""
        with self._lock:
            return len(self._cache)

    def cleanup_expired(self) -> int:
        """Remove expired items and return count of removed items."""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                k for k, (_, expiry) in self._cache.items()
                if expiry > 0 and current_time > expiry
            ]
            for k in expired_keys:
                del self._cache[k]
            return len(expired_keys)


class FileCacheStrategy(CacheStrategy):
    """
    File-based persistent cache strategy.

    This strategy stores cached items as files on disk for persistence
    across application restarts. Items are serialized using pickle.
    """

    def __init__(self, cache_dir: Path, default_ttl: Optional[int] = None):
        """
        Initialize file cache strategy.

        Args:
            cache_dir: Directory to store cache files
            default_ttl: Default TTL in seconds (None for no expiration)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl
        self._lock = threading.RLock()

    def _get_cache_file_path(self, key: str) -> Path:
        """Get the file path for a cache key."""
        # Hash the key to create a safe filename
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"

    def _get_metadata_file_path(self, key: str) -> Path:
        """Get the metadata file path for a cache key."""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.meta"

    def get(self, key: str) -> Optional[Any]:
        """Get a value from the file cache."""
        try:
            with self._lock:
                cache_file = self._get_cache_file_path(key)
                meta_file = self._get_metadata_file_path(key)

                if not cache_file.exists() or not meta_file.exists():
                    return None

                # Read metadata
                with open(meta_file, 'r') as f:
                    metadata = eval(f.read())  # Simple metadata format

                # Check if expired
                if metadata.get('expiry', 0) > 0 and time.time() > metadata['expiry']:
                    cache_file.unlink(missing_ok=True)
                    meta_file.unlink(missing_ok=True)
                    return None

                # Read cached value
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)

        except Exception as e:
            logger.error(f"Failed to get cached value for key {key}: {e}")
            return None

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store a value in the file cache."""
        try:
            with self._lock:
                cache_file = self._get_cache_file_path(key)
                meta_file = self._get_metadata_file_path(key)

                # Calculate expiry time
                if ttl is not None:
                    expiry = time.time() + ttl
                elif self.default_ttl is not None:
                    expiry = time.time() + self.default_ttl
                else:
                    expiry = 0  # No expiration

                # Write metadata
                metadata = {
                    'key': key,
                    'expiry': expiry,
                    'created': time.time()
                }
                with open(meta_file, 'w') as f:
                    f.write(str(metadata))

                # Write cached value
                with open(cache_file, 'wb') as f:
                    pickle.dump(value, f)

        except Exception as e:
            logger.error(f"Failed to cache value for key {key}: {e}")
            raise CacheError(f"Failed to cache value: {e}")

    def delete(self, key: str) -> bool:
        """Remove a value from the file cache."""
        try:
            with self._lock:
                cache_file = self._get_cache_file_path(key)
                meta_file = self._get_metadata_file_path(key)

                deleted = False
                if cache_file.exists():
                    cache_file.unlink()
                    deleted = True
                if meta_file.exists():
                    meta_file.unlink()
                    deleted = True

                return deleted

        except Exception as e:
            logger.error(f"Failed to delete cached value for key {key}: {e}")
            return False

    def clear(self) -> None:
        """Clear all cached values."""
        try:
            with self._lock:
                for file_path in self.cache_dir.glob("*.cache"):
                    file_path.unlink(missing_ok=True)
                for file_path in self.cache_dir.glob("*.meta"):
                    file_path.unlink(missing_ok=True)
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")

    def contains(self, key: str) -> bool:
        """Check if a key exists in the file cache."""
        return self.get(key) is not None

    def keys(self) -> List[str]:
        """Get all cache keys."""
        try:
            with self._lock:
                keys = []
                for meta_file in self.cache_dir.glob("*.meta"):
                    try:
                        with open(meta_file, 'r') as f:
                            metadata = eval(f.read())

                        # Check if expired
                        if metadata.get('expiry', 0) > 0 and time.time() > metadata['expiry']:
                            # Clean up expired entry
                            cache_file = self._get_cache_file_path(metadata['key'])
                            cache_file.unlink(missing_ok=True)
                            meta_file.unlink(missing_ok=True)
                        else:
                            keys.append(metadata['key'])
                    except Exception:
                        continue

                return keys

        except Exception as e:
            logger.error(f"Failed to get cache keys: {e}")
            return []

    def size(self) -> int:
        """Get the number of items in the file cache."""
        return len(self.keys())

    def cleanup_expired(self) -> int:
        """Remove expired cache files and return count of removed items."""
        count = 0
        try:
            with self._lock:
                current_time = time.time()
                for meta_file in self.cache_dir.glob("*.meta"):
                    try:
                        with open(meta_file, 'r') as f:
                            metadata = eval(f.read())

                        if metadata.get('expiry', 0) > 0 and current_time > metadata['expiry']:
                            cache_file = self._get_cache_file_path(metadata['key'])
                            cache_file.unlink(missing_ok=True)
                            meta_file.unlink(missing_ok=True)
                            count += 1
                    except Exception:
                        continue
        except Exception as e:
            logger.error(f"Failed to cleanup expired cache files: {e}")

        return count


class LRUCacheStrategy(CacheStrategy):
    """
    Strict LRU (Least Recently Used) cache strategy.

    This strategy maintains a fixed-size cache with strict LRU eviction.
    When the cache is full, the least recently used item is evicted.
    """

    def __init__(self, max_size: int = 128):
        """
        Initialize LRU cache strategy.

        Args:
            max_size: Maximum number of items to cache
        """
        self.max_size = max_size
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """Get a value from the LRU cache."""
        with self._lock:
            if key not in self._cache:
                return None

            # Move to end (most recently used)
            value = self._cache[key]
            self._cache.move_to_end(key)
            return value

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store a value in the LRU cache (TTL is ignored)."""
        with self._lock:
            if key in self._cache:
                # Update existing key
                self._cache[key] = value
                self._cache.move_to_end(key)
            else:
                # Add new key
                self._cache[key] = value

                # Evict least recently used if over capacity
                if len(self._cache) > self.max_size:
                    self._cache.popitem(last=False)

    def delete(self, key: str) -> bool:
        """Remove a value from the LRU cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()

    def contains(self, key: str) -> bool:
        """Check if a key exists in the LRU cache."""
        with self._lock:
            return key in self._cache

    def keys(self) -> List[str]:
        """Get all cache keys."""
        with self._lock:
            return list(self._cache.keys())

    def size(self) -> int:
        """Get the number of items in the LRU cache."""
        with self._lock:
            return len(self._cache)


class CompositeCacheStrategy(CacheStrategy):
    """
    Multi-level composite cache strategy.

    This strategy combines multiple cache strategies in a hierarchy
    (e.g., memory cache as L1, file cache as L2). Items are checked
    and stored in order of cache levels.
    """

    def __init__(self, primary_cache: CacheStrategy, secondary_cache: CacheStrategy):
        """
        Initialize composite cache strategy.

        Args:
            primary_cache: Fast cache (e.g., memory cache)
            secondary_cache: Slower but persistent cache (e.g., file cache)
        """
        self.primary_cache = primary_cache
        self.secondary_cache = secondary_cache
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """Get a value from the composite cache."""
        with self._lock:
            # Try primary cache first
            value = self.primary_cache.get(key)
            if value is not None:
                return value

            # Try secondary cache
            value = self.secondary_cache.get(key)
            if value is not None:
                # Promote to primary cache
                self.primary_cache.put(key, value)
                return value

            return None

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store a value in both cache levels."""
        with self._lock:
            # Store in both caches
            self.primary_cache.put(key, value, ttl)
            self.secondary_cache.put(key, value, ttl)

    def delete(self, key: str) -> bool:
        """Remove a value from both cache levels."""
        with self._lock:
            deleted_primary = self.primary_cache.delete(key)
            deleted_secondary = self.secondary_cache.delete(key)
            return deleted_primary or deleted_secondary

    def clear(self) -> None:
        """Clear both cache levels."""
        with self._lock:
            self.primary_cache.clear()
            self.secondary_cache.clear()

    def contains(self, key: str) -> bool:
        """Check if a key exists in either cache level."""
        return self.get(key) is not None

    def keys(self) -> List[str]:
        """Get all cache keys from both levels."""
        with self._lock:
            primary_keys = set(self.primary_cache.keys())
            secondary_keys = set(self.secondary_cache.keys())
            return list(primary_keys | secondary_keys)

    def size(self) -> int:
        """Get the total number of unique items across cache levels."""
        return len(self.keys())

    def cleanup_expired(self) -> int:
        """Cleanup expired items in both cache levels."""
        count = 0

        # Cleanup primary cache if it supports it
        if hasattr(self.primary_cache, 'cleanup_expired'):
            count += self.primary_cache.cleanup_expired()

        # Cleanup secondary cache if it supports it
        if hasattr(self.secondary_cache, 'cleanup_expired'):
            count += self.secondary_cache.cleanup_expired()

        return count


# Export cache strategies
__all__ = [
    "MemoryCacheStrategy",
    "FileCacheStrategy",
    "LRUCacheStrategy",
    "CompositeCacheStrategy",
]
