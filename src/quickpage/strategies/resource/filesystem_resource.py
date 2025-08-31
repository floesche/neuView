"""
Filesystem Resource Strategy Implementation

This module provides a file system-based resource strategy that loads
resources from local file system directories with support for multiple
search paths and resource metadata extraction.
"""

import os
import hashlib
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, List
import logging

from ..base import ResourceStrategy
from ..exceptions import ResourceNotFoundError, ResourceLoadError

logger = logging.getLogger(__name__)


class FileSystemResourceStrategy(ResourceStrategy):
    """
    File system resource strategy for loading static resources.

    This strategy loads resources from one or more file system directories,
    supporting multiple search paths and providing resource metadata
    such as file size, modification time, and content hash.
    """

    def __init__(self, resource_dirs: List[str], enable_caching: bool = True):
        """
        Initialize filesystem resource strategy.

        Args:
            resource_dirs: List of directories to search for resources
            enable_caching: Whether to cache file metadata for performance
        """
        self.resource_dirs = [Path(dir_path) for dir_path in resource_dirs]
        self.enable_caching = enable_caching
        self._metadata_cache: Dict[str, Dict[str, Any]] = {}

        # Validate resource directories
        for resource_dir in self.resource_dirs:
            if not resource_dir.exists():
                logger.warning(f"Resource directory does not exist: {resource_dir}")

    def _find_resource_path(self, resource_path: str) -> Optional[Path]:
        """Find the actual file path for a resource."""
        for resource_dir in self.resource_dirs:
            full_path = resource_dir / resource_path
            if full_path.exists() and full_path.is_file():
                return full_path
        return None

    def load_resource(self, resource_path: str) -> bytes:
        """
        Load a resource from the file system.

        Args:
            resource_path: Path to the resource file relative to resource directories

        Returns:
            Resource content as bytes

        Raises:
            ResourceNotFoundError: If resource doesn't exist
            ResourceLoadError: If resource can't be loaded
        """
        full_path = self._find_resource_path(resource_path)
        if full_path is None:
            raise ResourceNotFoundError(f"Resource not found: {resource_path}")

        try:
            with open(full_path, 'rb') as f:
                return f.read()
        except Exception as e:
            raise ResourceLoadError(f"Failed to load resource {resource_path}: {e}")

    def resource_exists(self, resource_path: str) -> bool:
        """
        Check if a resource exists.

        Args:
            resource_path: Path to the resource file

        Returns:
            True if resource exists, False otherwise
        """
        return self._find_resource_path(resource_path) is not None

    def get_resource_metadata(self, resource_path: str) -> Dict[str, Any]:
        """
        Get metadata for a resource.

        Args:
            resource_path: Path to the resource file

        Returns:
            Dictionary containing resource metadata

        Raises:
            ResourceNotFoundError: If resource doesn't exist
        """
        if self.enable_caching and resource_path in self._metadata_cache:
            return self._metadata_cache[resource_path].copy()

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
                'stem': full_path.stem
            }

            if self.enable_caching:
                self._metadata_cache[resource_path] = metadata.copy()

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
        resources = []

        for base_dir in self.resource_dirs:
            search_dir = base_dir / resource_dir
            if not search_dir.exists() or not search_dir.is_dir():
                continue

            try:
                for file_path in search_dir.glob(pattern):
                    if file_path.is_file():
                        # Get path relative to base resource directory
                        relative_path = file_path.relative_to(base_dir)
                        resources.append(str(relative_path))
            except Exception as e:
                logger.warning(f"Error listing resources in {search_dir}: {e}")

        return sorted(list(set(resources)))  # Remove duplicates and sort

    def copy_resource(self, source_path: str, dest_path: str) -> bool:
        """
        Copy a resource from source to destination.

        Args:
            source_path: Source resource path (relative to resource directories)
            dest_path: Destination file path (absolute or relative to current directory)

        Returns:
            True if copy was successful, False otherwise
        """
        try:
            source_full_path = self._find_resource_path(source_path)
            if source_full_path is None:
                logger.error(f"Source resource not found: {source_path}")
                return False

            dest_full_path = Path(dest_path)
            dest_full_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(source_full_path, dest_full_path)
            return True

        except Exception as e:
            logger.error(f"Failed to copy resource {source_path} to {dest_path}: {e}")
            return False

    def get_resource_hash(self, resource_path: str, algorithm: str = 'md5') -> str:
        """
        Get hash of a resource for cache invalidation.

        Args:
            resource_path: Path to the resource file
            algorithm: Hash algorithm to use ('md5', 'sha1', 'sha256')

        Returns:
            Hex digest of the resource content

        Raises:
            ResourceNotFoundError: If resource doesn't exist
            ResourceLoadError: If resource can't be hashed
        """
        try:
            content = self.load_resource(resource_path)
            hash_obj = hashlib.new(algorithm)
            hash_obj.update(content)
            return hash_obj.hexdigest()
        except ResourceNotFoundError:
            raise
        except Exception as e:
            raise ResourceLoadError(f"Failed to hash resource {resource_path}: {e}")
