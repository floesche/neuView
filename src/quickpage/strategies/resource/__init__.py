"""
Resource Strategy Implementations for QuickPage Phase 3

This module provides various resource loading and management strategies that implement
different approaches to resource handling, caching, and optimization. Each strategy
is optimized for different resource types and access patterns.

Resource Strategies:
- FileSystemResourceStrategy: Direct file system resource loading
- CachedResourceStrategy: Adds caching layer to any resource strategy
- RemoteResourceStrategy: Handles loading resources from URLs/remote sources
- CompositeResourceStrategy: Combines multiple strategies for different resource types
- OptimizedResourceStrategy: Adds minification and compression capabilities
"""

import os
import shutil
import hashlib
import requests
import gzip
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List, Union, Tuple
from urllib.parse import urlparse
import mimetypes
import time

from .. import (
    ResourceStrategy,
    ResourceError,
    ResourceNotFoundError,
    ResourceLoadError,
    CacheStrategy
)

logger = logging.getLogger(__name__)


class FileSystemResourceStrategy(ResourceStrategy):
    """
    File system-based resource loading strategy.

    This strategy loads resources directly from the local file system
    with support for multiple search paths and file type detection.
    """

    def __init__(self, base_paths: Union[Path, List[Path]], follow_symlinks: bool = True):
        """
        Initialize file system resource strategy.

        Args:
            base_paths: Base directory or list of directories to search for resources
            follow_symlinks: Whether to follow symbolic links
        """
        if isinstance(base_paths, (str, Path)):
            self.base_paths = [Path(base_paths)]
        else:
            self.base_paths = [Path(p) for p in base_paths]

        self.follow_symlinks = follow_symlinks
        self._resource_cache = {}

    def _find_resource_path(self, resource_path: str) -> Optional[Path]:
        """Find the actual file path for a resource."""
        for base_path in self.base_paths:
            full_path = base_path / resource_path
            if full_path.exists() and (full_path.is_file() or
                                      (full_path.is_symlink() and self.follow_symlinks)):
                return full_path
        return None

    def load_resource(self, resource_path: str) -> bytes:
        """Load a resource from the file system."""
        full_path = self._find_resource_path(resource_path)

        if full_path is None:
            raise ResourceNotFoundError(f"Resource not found: {resource_path}")

        try:
            with open(full_path, 'rb') as f:
                return f.read()
        except Exception as e:
            raise ResourceLoadError(f"Failed to load resource {resource_path}: {e}")

    def resource_exists(self, resource_path: str) -> bool:
        """Check if a resource exists in the file system."""
        return self._find_resource_path(resource_path) is not None

    def get_resource_metadata(self, resource_path: str) -> Dict[str, Any]:
        """Get metadata for a file system resource."""
        full_path = self._find_resource_path(resource_path)

        if full_path is None:
            raise ResourceNotFoundError(f"Resource not found: {resource_path}")

        try:
            stat = full_path.stat()
            mime_type, encoding = mimetypes.guess_type(str(full_path))

            return {
                'path': str(full_path),
                'size': stat.st_size,
                'modified_time': stat.st_mtime,
                'created_time': stat.st_ctime,
                'is_file': full_path.is_file(),
                'is_symlink': full_path.is_symlink(),
                'mime_type': mime_type,
                'encoding': encoding,
                'suffix': full_path.suffix,
                'name': full_path.name
            }
        except Exception as e:
            raise ResourceLoadError(f"Failed to get metadata for {resource_path}: {e}")

    def list_resources(self, resource_dir: Path, pattern: str = "*") -> List[str]:
        """List resources matching a pattern in the directory."""
        resources = []

        for base_path in self.base_paths:
            search_dir = base_path / resource_dir
            if search_dir.exists() and search_dir.is_dir():
                try:
                    for match in search_dir.rglob(pattern):
                        if match.is_file() or (match.is_symlink() and self.follow_symlinks):
                            # Get relative path from the search directory
                            rel_path = match.relative_to(base_path)
                            resources.append(str(rel_path))
                except Exception as e:
                    logger.error(f"Error listing resources in {search_dir}: {e}")

        return sorted(list(set(resources)))  # Remove duplicates and sort

    def copy_resource(self, source_path: str, dest_path: str) -> bool:
        """Copy a resource from source to destination."""
        source_full_path = self._find_resource_path(source_path)

        if source_full_path is None:
            logger.error(f"Source resource not found: {source_path}")
            return False

        try:
            dest_full_path = Path(dest_path)
            dest_full_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(source_full_path, dest_full_path)
            return True
        except Exception as e:
            logger.error(f"Failed to copy resource from {source_path} to {dest_path}: {e}")
            return False

    def get_resource_hash(self, resource_path: str) -> str:
        """Get MD5 hash of a resource for cache validation."""
        try:
            content = self.load_resource(resource_path)
            return hashlib.md5(content).hexdigest()
        except Exception as e:
            logger.error(f"Failed to get hash for {resource_path}: {e}")
            return ""


class CachedResourceStrategy(ResourceStrategy):
    """
    Resource strategy wrapper that adds caching to any resource strategy.

    This strategy acts as a decorator around another resource strategy,
    adding resource caching for improved performance and reduced I/O.
    """

    def __init__(self, wrapped_strategy: ResourceStrategy, cache_strategy: CacheStrategy):
        """
        Initialize cached resource strategy.

        Args:
            wrapped_strategy: The resource strategy to wrap with caching
            cache_strategy: The cache strategy to use for resource storage
        """
        self.wrapped_strategy = wrapped_strategy
        self.cache_strategy = cache_strategy
        self._metadata_cache = {}

    def _get_cache_key(self, resource_path: str, operation: str) -> str:
        """Generate a cache key for a resource operation."""
        return f"resource:{operation}:{resource_path}"

    def load_resource(self, resource_path: str) -> bytes:
        """Load a resource with caching."""
        cache_key = self._get_cache_key(resource_path, "content")

        # Try to get from cache first
        cached_content = self.cache_strategy.get(cache_key)
        if cached_content is not None:
            return cached_content

        # Load from wrapped strategy
        content = self.wrapped_strategy.load_resource(resource_path)

        # Cache the content
        self.cache_strategy.put(cache_key, content)

        return content

    def resource_exists(self, resource_path: str) -> bool:
        """Check if a resource exists with caching."""
        cache_key = self._get_cache_key(resource_path, "exists")

        # Try to get from cache first
        cached_result = self.cache_strategy.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Check using wrapped strategy
        exists = self.wrapped_strategy.resource_exists(resource_path)

        # Cache the result for a short time
        self.cache_strategy.put(cache_key, exists, ttl=30)

        return exists

    def get_resource_metadata(self, resource_path: str) -> Dict[str, Any]:
        """Get resource metadata with caching."""
        if resource_path in self._metadata_cache:
            return self._metadata_cache[resource_path]

        metadata = self.wrapped_strategy.get_resource_metadata(resource_path)
        self._metadata_cache[resource_path] = metadata

        return metadata

    def list_resources(self, resource_dir: Path, pattern: str = "*") -> List[str]:
        """List resources with caching."""
        cache_key = f"resources:list:{resource_dir}:{pattern}"

        # Try to get from cache first
        cached_list = self.cache_strategy.get(cache_key)
        if cached_list is not None:
            return cached_list

        # Get from wrapped strategy
        resource_list = self.wrapped_strategy.list_resources(resource_dir, pattern)

        # Cache the list for a short time
        self.cache_strategy.put(cache_key, resource_list, ttl=60)

        return resource_list

    def copy_resource(self, source_path: str, dest_path: str) -> bool:
        """Copy a resource (delegated to wrapped strategy)."""
        return self.wrapped_strategy.copy_resource(source_path, dest_path)

    def clear_cache(self) -> None:
        """Clear all cached resources."""
        self.cache_strategy.clear()
        self._metadata_cache.clear()

    def invalidate_resource(self, resource_path: str) -> None:
        """Invalidate cache for a specific resource."""
        operations = ["content", "exists"]
        for op in operations:
            cache_key = self._get_cache_key(resource_path, op)
            self.cache_strategy.delete(cache_key)

        if resource_path in self._metadata_cache:
            del self._metadata_cache[resource_path]


class RemoteResourceStrategy(ResourceStrategy):
    """
    Strategy for loading resources from remote URLs.

    This strategy can fetch resources from HTTP/HTTPS URLs with support
    for caching, headers, and basic authentication.
    """

    def __init__(self, timeout: int = 30, max_retries: int = 3,
                 default_headers: Optional[Dict[str, str]] = None):
        """
        Initialize remote resource strategy.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            default_headers: Default headers to send with requests
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.default_headers = default_headers or {}
        self._session = requests.Session()
        self._session.headers.update(self.default_headers)

    def _is_valid_url(self, resource_path: str) -> bool:
        """Check if the resource path is a valid URL."""
        try:
            result = urlparse(resource_path)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def load_resource(self, resource_path: str) -> bytes:
        """Load a resource from a remote URL."""
        if not self._is_valid_url(resource_path):
            raise ResourceNotFoundError(f"Invalid URL: {resource_path}")

        for attempt in range(self.max_retries + 1):
            try:
                response = self._session.get(resource_path, timeout=self.timeout)
                response.raise_for_status()
                return response.content
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries:
                    raise ResourceLoadError(f"Failed to load remote resource {resource_path}: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff

    def resource_exists(self, resource_path: str) -> bool:
        """Check if a remote resource exists using HEAD request."""
        if not self._is_valid_url(resource_path):
            return False

        try:
            response = self._session.head(resource_path, timeout=self.timeout)
            return response.status_code == 200
        except Exception:
            return False

    def get_resource_metadata(self, resource_path: str) -> Dict[str, Any]:
        """Get metadata for a remote resource."""
        if not self._is_valid_url(resource_path):
            raise ResourceNotFoundError(f"Invalid URL: {resource_path}")

        try:
            response = self._session.head(resource_path, timeout=self.timeout)
            response.raise_for_status()

            parsed_url = urlparse(resource_path)

            return {
                'url': resource_path,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content_type': response.headers.get('content-type'),
                'content_length': response.headers.get('content-length'),
                'last_modified': response.headers.get('last-modified'),
                'etag': response.headers.get('etag'),
                'server': response.headers.get('server'),
                'scheme': parsed_url.scheme,
                'netloc': parsed_url.netloc,
                'path': parsed_url.path
            }
        except Exception as e:
            raise ResourceLoadError(f"Failed to get metadata for {resource_path}: {e}")

    def list_resources(self, resource_dir: Path, pattern: str = "*") -> List[str]:
        """List resources (not supported for remote strategy)."""
        logger.warning("list_resources not supported for remote resources")
        return []

    def copy_resource(self, source_path: str, dest_path: str) -> bool:
        """Copy a remote resource to local destination."""
        try:
            content = self.load_resource(source_path)
            dest_full_path = Path(dest_path)
            dest_full_path.parent.mkdir(parents=True, exist_ok=True)

            with open(dest_full_path, 'wb') as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Failed to copy remote resource {source_path} to {dest_path}: {e}")
            return False


class CompositeResourceStrategy(ResourceStrategy):
    """
    Composite resource strategy that delegates to different strategies based on resource type.

    This strategy allows using different resource loading mechanisms for different
    resource types or locations (e.g., local files, remote URLs, cached resources).
    """

    def __init__(self):
        """Initialize composite resource strategy."""
        self._strategies: List[Tuple[callable, ResourceStrategy]] = []
        self._default_strategy = None

    def register_strategy(self, condition: callable, strategy: ResourceStrategy) -> None:
        """
        Register a strategy with a condition function.

        Args:
            condition: Function that takes resource_path and returns True if strategy should be used
            strategy: Resource strategy to use when condition is met
        """
        self._strategies.append((condition, strategy))

    def set_default_strategy(self, strategy: ResourceStrategy) -> None:
        """Set the default strategy for resources that don't match any condition."""
        self._default_strategy = strategy

    def _get_strategy_for_resource(self, resource_path: str) -> ResourceStrategy:
        """Get the appropriate strategy for a resource path."""
        for condition, strategy in self._strategies:
            try:
                if condition(resource_path):
                    return strategy
            except Exception as e:
                logger.error(f"Error evaluating strategy condition for {resource_path}: {e}")

        if self._default_strategy:
            return self._default_strategy
        else:
            raise ResourceLoadError(f"No strategy available for resource: {resource_path}")

    def load_resource(self, resource_path: str) -> bytes:
        """Load a resource using the appropriate strategy."""
        strategy = self._get_strategy_for_resource(resource_path)
        return strategy.load_resource(resource_path)

    def resource_exists(self, resource_path: str) -> bool:
        """Check if a resource exists using the appropriate strategy."""
        try:
            strategy = self._get_strategy_for_resource(resource_path)
            return strategy.resource_exists(resource_path)
        except Exception:
            return False

    def get_resource_metadata(self, resource_path: str) -> Dict[str, Any]:
        """Get resource metadata using the appropriate strategy."""
        strategy = self._get_strategy_for_resource(resource_path)
        return strategy.get_resource_metadata(resource_path)

    def list_resources(self, resource_dir: Path, pattern: str = "*") -> List[str]:
        """List resources using all registered strategies."""
        all_resources = set()

        for _, strategy in self._strategies:
            try:
                resources = strategy.list_resources(resource_dir, pattern)
                all_resources.update(resources)
            except Exception as e:
                logger.error(f"Error listing resources with strategy: {e}")

        if self._default_strategy:
            try:
                resources = self._default_strategy.list_resources(resource_dir, pattern)
                all_resources.update(resources)
            except Exception as e:
                logger.error(f"Error listing resources with default strategy: {e}")

        return sorted(list(all_resources))

    def copy_resource(self, source_path: str, dest_path: str) -> bool:
        """Copy a resource using the appropriate strategy."""
        try:
            strategy = self._get_strategy_for_resource(source_path)
            return strategy.copy_resource(source_path, dest_path)
        except Exception as e:
            logger.error(f"Failed to copy resource {source_path}: {e}")
            return False


class OptimizedResourceStrategy(ResourceStrategy):
    """
    Resource strategy wrapper that adds optimization capabilities.

    This strategy can minify CSS/JS resources, compress content,
    and optimize images for better performance.
    """

    def __init__(self, wrapped_strategy: ResourceStrategy,
                 enable_minification: bool = True, enable_compression: bool = True):
        """
        Initialize optimized resource strategy.

        Args:
            wrapped_strategy: The resource strategy to wrap with optimization
            enable_minification: Whether to minify CSS/JS resources
            enable_compression: Whether to compress resources
        """
        self.wrapped_strategy = wrapped_strategy
        self.enable_minification = enable_minification
        self.enable_compression = enable_compression

    def _should_minify(self, resource_path: str) -> bool:
        """Check if a resource should be minified."""
        if not self.enable_minification:
            return False

        ext = Path(resource_path).suffix.lower()
        return ext in ['.css', '.js']

    def _should_compress(self, resource_path: str) -> bool:
        """Check if a resource should be compressed."""
        if not self.enable_compression:
            return False

        ext = Path(resource_path).suffix.lower()
        return ext in ['.html', '.css', '.js', '.json', '.xml', '.txt']

    def _minify_css(self, content: str) -> str:
        """Simple CSS minification."""
        import re
        # Remove comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        # Remove whitespace around certain characters
        content = re.sub(r'\s*([{}:;,>+~])\s*', r'\1', content)
        return content.strip()

    def _minify_js(self, content: str) -> str:
        """Simple JavaScript minification."""
        import re
        # Remove single-line comments
        content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
        # Remove multi-line comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        return content.strip()

    def _optimize_content(self, content: bytes, resource_path: str) -> bytes:
        """Optimize resource content based on type."""
        try:
            if self._should_minify(resource_path):
                text_content = content.decode('utf-8')
                ext = Path(resource_path).suffix.lower()

                if ext == '.css':
                    text_content = self._minify_css(text_content)
                elif ext == '.js':
                    text_content = self._minify_js(text_content)

                content = text_content.encode('utf-8')

            if self._should_compress(resource_path):
                content = gzip.compress(content)

        except Exception as e:
            logger.error(f"Failed to optimize resource {resource_path}: {e}")
            # Return original content if optimization fails

        return content

    def load_resource(self, resource_path: str) -> bytes:
        """Load and optimize a resource."""
        content = self.wrapped_strategy.load_resource(resource_path)
        return self._optimize_content(content, resource_path)

    def resource_exists(self, resource_path: str) -> bool:
        """Check if a resource exists (delegated to wrapped strategy)."""
        return self.wrapped_strategy.resource_exists(resource_path)

    def get_resource_metadata(self, resource_path: str) -> Dict[str, Any]:
        """Get resource metadata with optimization info."""
        metadata = self.wrapped_strategy.get_resource_metadata(resource_path)

        # Add optimization flags
        metadata['optimized'] = True
        metadata['minified'] = self._should_minify(resource_path)
        metadata['compressed'] = self._should_compress(resource_path)

        return metadata

    def list_resources(self, resource_dir: Path, pattern: str = "*") -> List[str]:
        """List resources (delegated to wrapped strategy)."""
        return self.wrapped_strategy.list_resources(resource_dir, pattern)

    def copy_resource(self, source_path: str, dest_path: str) -> bool:
        """Copy and optimize a resource."""
        try:
            # Load optimized content
            content = self.load_resource(source_path)

            # Write to destination
            dest_full_path = Path(dest_path)
            dest_full_path.parent.mkdir(parents=True, exist_ok=True)

            with open(dest_full_path, 'wb') as f:
                f.write(content)

            return True
        except Exception as e:
            logger.error(f"Failed to copy optimized resource {source_path} to {dest_path}: {e}")
            return False


# Export resource strategies
__all__ = [
    "FileSystemResourceStrategy",
    "CachedResourceStrategy",
    "RemoteResourceStrategy",
    "CompositeResourceStrategy",
    "OptimizedResourceStrategy",
]
