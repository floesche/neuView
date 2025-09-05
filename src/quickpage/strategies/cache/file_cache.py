"""
File Cache Strategy Implementation

This module provides a file-based persistent cache strategy that stores
cached items on disk with metadata for TTL and expiration handling.
"""

import time
import pickle
import hashlib
import threading
import json
from pathlib import Path
from typing import Any, Optional, List
import logging

from ..base import CacheStrategy
from ..exceptions import CacheError

logger = logging.getLogger(__name__)


class FileCacheStrategy(CacheStrategy):
    """
    File-based persistent cache strategy.

    This strategy stores cached items as files on disk, allowing
    persistence across application restarts. Each cached item has
    an associated metadata file for expiration tracking.
    """

    def __init__(self, cache_dir: str, default_ttl: Optional[int] = None):
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
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.cache"

    def _get_metadata_file_path(self, key: str) -> Path:
        """Get the metadata file path for a cache key."""
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.meta"

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            cache_file = self._get_cache_file_path(key)
            meta_file = self._get_metadata_file_path(key)

            if not cache_file.exists() or not meta_file.exists():
                return None

            try:
                # Check expiration
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                    expiry = metadata.get('expiry', 0)

                if expiry > 0 and time.time() > expiry:
                    # Remove expired files
                    cache_file.unlink(missing_ok=True)
                    meta_file.unlink(missing_ok=True)
                    return None

                # Load cached value
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)

            except Exception as e:
                logger.warning(f"Error loading cache file {cache_file}: {e}")
                # Clean up corrupted files
                cache_file.unlink(missing_ok=True)
                meta_file.unlink(missing_ok=True)
                return None

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None for no expiration)
        """
        with self._lock:
            cache_file = self._get_cache_file_path(key)
            meta_file = self._get_metadata_file_path(key)

            try:
                # Calculate expiry time
                if ttl is not None:
                    expiry = time.time() + ttl
                elif self.default_ttl is not None:
                    expiry = time.time() + self.default_ttl
                else:
                    expiry = 0  # No expiration

                # Write cache file
                with open(cache_file, 'wb') as f:
                    pickle.dump(value, f)

                # Write metadata file
                metadata = {
                    'key': key,
                    'expiry': expiry,
                    'created': time.time()
                }
                with open(meta_file, 'w') as f:
                    json.dump(metadata, f)

            except Exception as e:
                logger.error(f"Error writing cache file {cache_file}: {e}")
                # Clean up partial files
                cache_file.unlink(missing_ok=True)
                meta_file.unlink(missing_ok=True)
                raise CacheError(f"Failed to cache key {key}: {e}")

    def delete(self, key: str) -> bool:
        """
        Remove a value from the cache.

        Args:
            key: Cache key

        Returns:
            True if key was found and deleted, False otherwise
        """
        with self._lock:
            cache_file = self._get_cache_file_path(key)
            meta_file = self._get_metadata_file_path(key)

            existed = cache_file.exists() or meta_file.exists()

            cache_file.unlink(missing_ok=True)
            meta_file.unlink(missing_ok=True)

            return existed

    def clear(self) -> None:
        """Clear all cached values."""
        with self._lock:
            for file_path in self.cache_dir.glob("*.cache"):
                file_path.unlink(missing_ok=True)
            for file_path in self.cache_dir.glob("*.meta"):
                file_path.unlink(missing_ok=True)

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
            keys = []
            for meta_file in self.cache_dir.glob("*.meta"):
                try:
                    with open(meta_file, 'r') as f:
                        metadata = json.load(f)
                        expiry = metadata.get('expiry', 0)

                        # Check if expired
                        if expiry > 0 and time.time() > expiry:
                            # Remove expired files
                            cache_file = self._get_cache_file_path(metadata['key'])
                            cache_file.unlink(missing_ok=True)
                            meta_file.unlink(missing_ok=True)
                        else:
                            keys.append(metadata['key'])
                except Exception as e:
                    logger.warning(f"Error reading metadata file {meta_file}: {e}")
                    # Clean up corrupted metadata file
                    meta_file.unlink(missing_ok=True)

            return keys

    def size(self) -> int:
        """
        Get the number of items in the cache.

        Returns:
            Number of cached items
        """
        return len(self.keys())

    def cleanup_expired(self) -> None:
        """Remove expired items from cache."""
        with self._lock:
            current_time = time.time()
            for meta_file in self.cache_dir.glob("*.meta"):
                try:
                    with open(meta_file, 'r') as f:
                        metadata = json.load(f)
                        expiry = metadata.get('expiry', 0)

                        if expiry > 0 and current_time > expiry:
                            # Remove expired files
                            cache_file = self._get_cache_file_path(metadata['key'])
                            cache_file.unlink(missing_ok=True)
                            meta_file.unlink(missing_ok=True)
                except Exception as e:
                    logger.warning(f"Error processing metadata file {meta_file}: {e}")
                    # Clean up corrupted metadata file
                    meta_file.unlink(missing_ok=True)
