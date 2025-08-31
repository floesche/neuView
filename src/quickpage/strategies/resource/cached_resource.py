"""
Cached Resource Strategy Implementation

This module provides a caching wrapper for resource strategies that adds
transparent caching capabilities to any underlying resource strategy.
"""

import hashlib
from typing import Any, Dict, Optional, List
from pathlib import Path
import logging

from ..base import ResourceStrategy, CacheStrategy
from ..exceptions import ResourceNotFoundError, ResourceLoadError

logger = logging.getLogger(__name__)


class CachedResourceStrategy(ResourceStrategy):
    """
    Cached resource strategy that wraps another resource strategy with caching.

    This strategy adds transparent caching to any resource strategy,
    improving performance by avoiding repeated resource loading operations.
    The cache key is based on the resource path and optionally the content hash.
    """

    def __init__(self, base_strategy: ResourceStrategy, cache_strategy: CacheStrategy, cache_ttl: Optional[int] = 3600):
        """
        Initialize cached resource strategy.

        Args:
            base_strategy: Underlying resource strategy to cache
            cache_strategy: Cache strategy to use for caching
            cache_ttl: Time to live for cached resources in seconds (default: 1 hour)
        """
        self.base_strategy = base_strategy
        self.cache_strategy = cache_strategy
        self.cache_ttl = cache_ttl

    def _get_cache_key(self, resource_path: str, suffix: str = "") -> str:
        """Generate cache key for a resource."""
        key = f"resource:{resource_path}"
        if suffix:
            key += f":{suffix}"
        return hashlib.md5(key.encode()).hexdigest()

    def load_resource(self, resource_path: str) -> bytes:
        """
        Load a resource with caching.

        Args:
            resource_path: Path to the resource file

        Returns:
            Resource content as bytes

        Raises:
            ResourceNotFoundError: If resource doesn't exist
            ResourceLoadError: If resource can't be loaded
        """
        cache_key = self._get_cache_key(resource_path, "content")

        # Try to get from cache first
        cached_content = self.cache_strategy.get(cache_key)
        if cached_content is not None:
            return cached_content

        # Load from base strategy
        content = self.base_strategy.load_resource(resource_path)

        # Cache the content
        self.cache_strategy.put(cache_key, content, self.cache_ttl)

        return content

    def resource_exists(self, resource_path: str) -> bool:
        """
        Check if a resource exists with caching.

        Args:
            resource_path: Path to the resource file

        Returns:
            True if resource exists, False otherwise
        """
        cache_key = self._get_cache_key(resource_path, "exists")

        # Try to get from cache first
        cached_result = self.cache_strategy.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Check with base strategy
        exists = self.base_strategy.resource_exists(resource_path)

        # Cache the result (with shorter TTL for existence checks)
        self.cache_strategy.put(cache_key, exists, min(self.cache_ttl, 300))

        return exists

    def get_resource_metadata(self, resource_path: str) -> Dict[str, Any]:
        """
        Get metadata for a resource with caching.

        Args:
            resource_path: Path to the resource file

        Returns:
            Dictionary containing resource metadata
        """
        cache_key = self._get_cache_key(resource_path, "metadata")

        # Try to get from cache first
        cached_metadata = self.cache_strategy.get(cache_key)
        if cached_metadata is not None:
            return cached_metadata

        # Get from base strategy
        metadata = self.base_strategy.get_resource_metadata(resource_path)

        # Cache the metadata
        self.cache_strategy.put(cache_key, metadata, self.cache_ttl)

        return metadata

    def list_resources(self, resource_dir: Path, pattern: str = "*") -> List[str]:
        """
        List resources with caching.

        Args:
            resource_dir: Directory to search for resources
            pattern: Glob pattern to match (default: "*")

        Returns:
            List of resource paths
        """
        cache_key = self._get_cache_key(f"{resource_dir}:{pattern}", "list")

        # Try to get from cache first
        cached_list = self.cache_strategy.get(cache_key)
        if cached_list is not None:
            return cached_list

        # Get from base strategy
        resources = self.base_strategy.list_resources(resource_dir, pattern)

        # Cache the list (with shorter TTL for directory listings)
        self.cache_strategy.put(cache_key, resources, min(self.cache_ttl, 600))

        return resources

    def copy_resource(self, source_path: str, dest_path: str) -> bool:
        """
        Copy a resource (no caching for write operations).

        Args:
            source_path: Source resource path
            dest_path: Destination path

        Returns:
            True if copy was successful, False otherwise
        """
        return self.base_strategy.copy_resource(source_path, dest_path)

    def clear_cache(self) -> None:
        """Clear all cached resources."""
        # We can't selectively clear just our keys without knowing all keys,
        # so we'll need to clear the entire cache or implement a more sophisticated approach
        logger.info("Clearing resource cache")
        try:
            # If the cache supports selective clearing by pattern, use it
            if hasattr(self.cache_strategy, 'clear_pattern'):
                self.cache_strategy.clear_pattern("resource:*")
            else:
                # Otherwise, clear everything (not ideal but safe)
                self.cache_strategy.clear()
        except Exception as e:
            logger.warning(f"Failed to clear resource cache: {e}")

    def invalidate_resource(self, resource_path: str) -> None:
        """
        Invalidate cache entries for a specific resource.

        Args:
            resource_path: Path to the resource to invalidate
        """
        # Remove all cache entries for this resource
        cache_keys = [
            self._get_cache_key(resource_path, "content"),
            self._get_cache_key(resource_path, "exists"),
            self._get_cache_key(resource_path, "metadata")
        ]

        for cache_key in cache_keys:
            try:
                self.cache_strategy.delete(cache_key)
            except Exception as e:
                logger.warning(f"Failed to invalidate cache key {cache_key}: {e}")
