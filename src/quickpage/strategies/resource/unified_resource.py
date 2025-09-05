"""
Unified Resource Strategy Implementation

This module provides a unified resource strategy that consolidates the functionality
of filesystem resource loading, caching, and optimization into a single, configurable
strategy. This reduces complexity and eliminates the need for multiple wrapper strategies.
"""

import re
import gzip
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional, List, Union
import logging

from ..base import ResourceStrategy, CacheStrategy
from ..exceptions import ResourceNotFoundError, ResourceLoadError

logger = logging.getLogger(__name__)


class UnifiedResourceStrategy(ResourceStrategy):
    """
    Unified resource strategy with built-in caching and optimization.

    This strategy combines filesystem resource loading, caching, and optimization
    features into a single configurable class, eliminating the need for complex
    strategy wrapping patterns.
    """

    def __init__(self,
                 base_paths: List[Union[str, Path]],
                 follow_symlinks: bool = True,
                 cache_strategy: Optional[CacheStrategy] = None,
                 cache_ttl: Optional[int] = 3600,
                 enable_optimization: bool = False,
                 enable_minification: bool = True,
                 enable_compression: bool = True,
                 enable_metadata_cache: bool = True):
        """
        Initialize unified resource strategy.

        Args:
            base_paths: List of directories to search for resources
            follow_symlinks: Whether to follow symbolic links
            cache_strategy: Optional cache strategy for resource caching
            cache_ttl: Time to live for cached resources in seconds (default: 1 hour)
            enable_optimization: Whether to enable resource optimization (minification/compression)
            enable_minification: Whether to enable CSS/JS minification
            enable_compression: Whether to enable gzip compression
            enable_metadata_cache: Whether to cache file metadata for performance
        """
        if not base_paths:
            raise ValueError("base_paths parameter is required and cannot be empty")

        self.base_paths = [Path(dir_path) for dir_path in base_paths]
        self.follow_symlinks = follow_symlinks

        # Caching configuration
        self.cache_strategy = cache_strategy
        self.cache_ttl = cache_ttl
        self.enable_metadata_cache = enable_metadata_cache
        self._metadata_cache: Dict[str, Dict[str, Any]] = {}
        self._max_metadata_cache_size = 1000  # Prevent memory leaks

        # Optimization configuration
        self.enable_optimization = enable_optimization
        self.enable_minification = enable_minification and enable_optimization
        self.enable_compression = enable_compression and enable_optimization

        # Validate resource directories
        for base_path in self.base_paths:
            if not base_path.exists():
                logger.warning(f"Resource directory does not exist: {base_path}")

    def _find_resource_path(self, resource_path: str) -> Optional[Path]:
        """Find the actual file path for a resource."""
        for base_path in self.base_paths:
            full_path = base_path / resource_path
            # Check if path exists and handle symlinks based on configuration
            if full_path.exists():
                if full_path.is_symlink():
                    # Handle symlinks based on configuration
                    if self.follow_symlinks:
                        try:
                            if full_path.resolve().is_file():
                                return full_path
                        except (OSError, RuntimeError):
                            # Handle broken symlinks or circular references
                            continue
                    else:
                        # If not following symlinks, skip this path
                        continue
                elif full_path.is_file():
                    # If it's a regular file (not a symlink), return it
                    return full_path
        return None

    def _get_cache_key(self, resource_path: str, suffix: str = "") -> str:
        """Generate cache key for a resource."""
        key = f"unified_resource:{resource_path}"
        if suffix:
            key += f":{suffix}"
        return hashlib.md5(key.encode()).hexdigest()

    def _should_minify(self, resource_path: str) -> bool:
        """Check if a resource should be minified."""
        if not self.enable_minification:
            return False

        extension = Path(resource_path).suffix.lower()
        return (extension in ['.css', '.js'] and
                not resource_path.endswith('.min.css') and
                not resource_path.endswith('.min.js'))

    def _should_compress(self, resource_path: str) -> bool:
        """Check if a resource should be compressed."""
        if not self.enable_compression:
            return False

        extension = Path(resource_path).suffix.lower()
        return extension in ['.css', '.js', '.html', '.xml', '.json', '.txt']

    def _minify_css(self, content: str) -> str:
        """Basic CSS minification."""
        try:
            # Remove comments
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            # Remove unnecessary whitespace
            content = re.sub(r'\s+', ' ', content)
            # Remove whitespace around specific characters
            content = re.sub(r'\s*([{}:;,>+~])\s*', r'\1', content)
            return content.strip()
        except Exception as e:
            logger.warning(f"CSS minification failed: {e}")
            return content

    def _minify_js(self, content: str) -> str:
        """Basic JavaScript minification."""
        try:
            # Remove single-line comments (be careful with URLs)
            content = re.sub(r'(?<!:)//.*$', '', content, flags=re.MULTILINE)
            # Remove multi-line comments
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            # Remove unnecessary whitespace
            content = re.sub(r'\s+', ' ', content)
            # Remove whitespace around operators and punctuation
            content = re.sub(r'\s*([{}();,=+\-*/&|!<>])\s*', r'\1', content)
            return content.strip()
        except Exception as e:
            logger.warning(f"JavaScript minification failed: {e}")
            return content

    def _optimize_content(self, content: bytes, resource_path: str) -> bytes:
        """Apply optimizations to resource content."""
        if not self.enable_optimization:
            return content

        try:
            # Convert to string for text-based optimizations
            text_content = content.decode('utf-8')

            # Apply minification if applicable
            if self._should_minify(resource_path):
                extension = Path(resource_path).suffix.lower()
                if extension == '.css':
                    text_content = self._minify_css(text_content)
                elif extension == '.js':
                    text_content = self._minify_js(text_content)

            # Convert back to bytes
            optimized_content = text_content.encode('utf-8')

            # Apply compression if applicable
            if self._should_compress(resource_path):
                optimized_content = gzip.compress(optimized_content)

            return optimized_content

        except UnicodeDecodeError:
            # Binary content, only apply compression if applicable
            if self._should_compress(resource_path):
                return gzip.compress(content)
            return content
        except Exception as e:
            logger.warning(f"Content optimization failed for {resource_path}: {e}")
            return content

    def _manage_metadata_cache(self) -> None:
        """Manage metadata cache size to prevent memory leaks."""
        if len(self._metadata_cache) > self._max_metadata_cache_size:
            # Remove oldest 20% of entries (simple FIFO eviction)
            keys_to_remove = list(self._metadata_cache.keys())[:len(self._metadata_cache) // 5]
            for key in keys_to_remove:
                self._metadata_cache.pop(key, None)

    def load_resource(self, resource_path: str) -> bytes:
        """
        Load a resource with optional caching and optimization.

        Args:
            resource_path: Path to the resource file

        Returns:
            Resource content as bytes (potentially optimized)

        Raises:
            ResourceNotFoundError: If resource doesn't exist
            ResourceLoadError: If resource can't be loaded
        """
        # Generate cache key for both reading and writing
        cache_key = self._get_cache_key(resource_path, "content")

        # Try cache first if caching is enabled
        if self.cache_strategy:
            cached_content = self.cache_strategy.get(cache_key)
            if cached_content is not None:
                return cached_content

        # Load from filesystem
        full_path = self._find_resource_path(resource_path)
        if full_path is None:
            raise ResourceNotFoundError(f"Resource not found: {resource_path}")

        try:
            with open(full_path, 'rb') as f:
                content = f.read()
        except Exception as e:
            raise ResourceLoadError(f"Failed to load resource {resource_path}: {e}")

        # Apply optimizations if enabled
        optimized_content = self._optimize_content(content, resource_path)

        # Cache the optimized content if caching is enabled
        if self.cache_strategy:
            self.cache_strategy.put(cache_key, optimized_content, self.cache_ttl)

        return optimized_content

    def resource_exists(self, resource_path: str) -> bool:
        """
        Check if a resource exists with optional caching.

        Args:
            resource_path: Path to the resource file

        Returns:
            True if resource exists, False otherwise
        """
        # Generate cache key for both reading and writing
        cache_key = self._get_cache_key(resource_path, "exists")

        # Try cache first if caching is enabled
        if self.cache_strategy:
            cached_result = self.cache_strategy.get(cache_key)
            if cached_result is not None:
                return cached_result

        # Check filesystem
        exists = self._find_resource_path(resource_path) is not None

        # Cache the result if caching is enabled (with shorter TTL for existence checks)
        if self.cache_strategy:
            cache_ttl = min(self.cache_ttl or 3600, 300)
            self.cache_strategy.put(cache_key, exists, cache_ttl)

        return exists

    def get_resource_metadata(self, resource_path: str) -> Dict[str, Any]:
        """
        Get metadata for a resource with optional caching.

        Args:
            resource_path: Path to the resource file

        Returns:
            Dictionary containing resource metadata including optimization info

        Raises:
            ResourceNotFoundError: If resource doesn't exist
        """
        # Try cache first if caching is enabled
        if self.cache_strategy:
            cache_key = self._get_cache_key(resource_path, "metadata")
            cached_metadata = self.cache_strategy.get(cache_key)
            if cached_metadata is not None:
                return cached_metadata

        # Try local metadata cache
        if self.enable_metadata_cache and resource_path in self._metadata_cache:
            return self._metadata_cache[resource_path].copy()

        # Get metadata from filesystem
        full_path = self._find_resource_path(resource_path)
        if full_path is None:
            raise ResourceNotFoundError(f"Resource not found: {resource_path}")

        try:
            stat = full_path.stat()
            metadata = {
                'path': str(full_path),
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'created': stat.st_ctime,
                'is_file': full_path.is_file(),
                'is_directory': full_path.is_dir(),
                'extension': full_path.suffix.lower(),
                'name': full_path.name,
                'stem': full_path.stem,
                # Optimization metadata
                'optimized': self.enable_optimization,
                'minifiable': self._should_minify(resource_path),
                'compressible': self._should_compress(resource_path),
                'cached': self.cache_strategy is not None
            }

            # Cache metadata locally if enabled
            if self.enable_metadata_cache:
                self._manage_metadata_cache()
                self._metadata_cache[resource_path] = metadata.copy()

            # Cache metadata in strategy cache if enabled
            if self.cache_strategy:
                self.cache_strategy.put(
                    self._get_cache_key(resource_path, "metadata"),
                    metadata,
                    self.cache_ttl
                )

            return metadata

        except Exception as e:
            raise ResourceLoadError(f"Failed to get metadata for {resource_path}: {e}")

    def list_resources(self, resource_dir: Path, pattern: str = "*") -> List[str]:
        """
        List resources matching a pattern in the given directory.

        Args:
            resource_dir: Directory to search for resources (relative to resource dirs)
            pattern: Glob pattern to match (default: "*")

        Returns:
            List of resource paths relative to resource directories
        """
        # Try cache first if caching is enabled
        if self.cache_strategy:
            cache_key = self._get_cache_key(f"{resource_dir}:{pattern}", "list")
            cached_list = self.cache_strategy.get(cache_key)
            if cached_list is not None:
                return cached_list

        resources = []

        for base_path in self.base_paths:
            search_dir = base_path / resource_dir
            if not search_dir.exists() or not search_dir.is_dir():
                continue

            try:
                for file_path in search_dir.glob(pattern):
                    # Check if it's a file and handle symlinks properly
                    is_valid_file = False
                    if file_path.is_file():
                        if file_path.is_symlink():
                            # Only include symlinks if we're following them
                            if self.follow_symlinks:
                                try:
                                    # Verify the symlink target is actually a file
                                    if file_path.resolve().is_file():
                                        is_valid_file = True
                                except (OSError, RuntimeError):
                                    # Handle broken symlinks or circular references
                                    continue
                        else:
                            # Regular file
                            is_valid_file = True

                    if is_valid_file:
                        # Get path relative to base resource directory
                        relative_path = file_path.relative_to(base_path)
                        resources.append(str(relative_path))
            except Exception as e:
                logger.warning(f"Error listing resources in {search_dir}: {e}")

        # Remove duplicates and sort
        unique_resources = sorted(list(set(resources)))

        # Cache the list if caching is enabled (with shorter TTL for directory listings)
        if self.cache_strategy:
            cache_ttl = min(self.cache_ttl or 3600, 600)
            self.cache_strategy.put(
                self._get_cache_key(f"{resource_dir}:{pattern}", "list"),
                unique_resources,
                cache_ttl
            )

        return unique_resources

    def copy_resource(self, source_path: str, dest_path: str) -> bool:
        """
        Copy and optionally optimize a resource to destination.

        Args:
            source_path: Source resource path (relative to resource directories)
            dest_path: Destination file path (absolute or relative to current directory)

        Returns:
            True if copy was successful, False otherwise
        """
        try:
            # Load and potentially optimize content
            optimized_content = self.load_resource(source_path)

            # Write to destination
            dest_file = Path(dest_path)
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            with open(dest_file, 'wb') as f:
                f.write(optimized_content)

            return True

        except Exception as e:
            logger.error(f"Failed to copy resource {source_path} to {dest_path}: {e}")
            return False

    def clear_cache(self) -> None:
        """Clear all cached resources."""
        if self.cache_strategy:
            # We can't selectively clear just our keys without knowing all keys,
            # so we'll need to clear the entire cache or implement a more sophisticated approach
            logger.info("Clearing unified resource cache")
            try:
                # Clear all cache entries (using only standard CacheStrategy methods)
                self.cache_strategy.clear()
            except Exception as e:
                logger.warning(f"Failed to clear resource cache: {e}")

        # Clear local metadata cache
        if self.enable_metadata_cache:
            self._metadata_cache.clear()

    def invalidate_resource(self, resource_path: str) -> None:
        """
        Invalidate cache entries for a specific resource.

        Args:
            resource_path: Path to the resource to invalidate
        """
        if self.cache_strategy:
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

        # Remove from local metadata cache
        if self.enable_metadata_cache and resource_path in self._metadata_cache:
            del self._metadata_cache[resource_path]
