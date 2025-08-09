"""
Infrastructure adapters for QuickPage.

These adapters implement the domain ports using concrete technologies
like Jinja2 for templating, local filesystem for storage, and memory
for caching.
"""

import os
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ...core.ports import TemplateEngine, FileStorage, CacheRepository

logger = logging.getLogger(__name__)


class Jinja2TemplateEngine(TemplateEngine):
    """
    Template engine adapter using Jinja2.

    This adapter implements the TemplateEngine port using Jinja2
    as the underlying template processing technology.
    """

    def __init__(self, template_dir: str):
        self.template_dir = Path(template_dir)
        self._env = None
        self._setup_environment()

    def _setup_environment(self):
        """Set up the Jinja2 environment with custom filters."""
        # Ensure template directory exists
        self.template_dir.mkdir(parents=True, exist_ok=True)

        # Create Jinja2 environment
        self._env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Add custom filters
        self._env.filters['format_number'] = self._format_number
        self._env.filters['format_percentage'] = self._format_percentage
        self._env.filters['format_datetime'] = self._format_datetime
        self._env.filters['soma_side_display'] = self._soma_side_display

    def _format_number(self, value: Any) -> str:
        """Format a number with thousands separators."""
        if isinstance(value, (int, float)):
            return f"{value:,}"
        return str(value)

    def _format_percentage(self, value: Any, decimals: int = 1) -> str:
        """Format a number as percentage."""
        if isinstance(value, (int, float)):
            return f"{value:.{decimals}f}%"
        return str(value)

    def _format_datetime(self, value: datetime, format: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format a datetime object."""
        if isinstance(value, datetime):
            return value.strftime(format)
        return str(value)

    def _soma_side_display(self, value: Any) -> str:
        """Display soma side in a user-friendly format."""
        if not value:
            return "Unknown"

        side_map = {
            'L': 'Left',
            'R': 'Right',
            'M': 'Middle',
            'left': 'Left',
            'right': 'Right',
            'middle': 'Middle',
            'all': 'All sides'
        }
        return side_map.get(str(value), str(value))

    async def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a template with the given context.

        Args:
            template_name: Name of the template to render
            context: Template context variables

        Returns:
            Rendered HTML content
        """
        try:
            # Add template name without extension if needed
            if not template_name.endswith('.html'):
                template_name += '.html'

            template = self._env.get_template(template_name)

            # Add common context variables
            enhanced_context = {
                **context,
                'generated_at': datetime.now(),
                'template_name': template_name
            }

            # Render in executor to avoid blocking
            loop = asyncio.get_event_loop()
            html_content = await loop.run_in_executor(
                None, template.render, enhanced_context
            )

            logger.debug(f"Rendered template {template_name}")
            return html_content

        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            raise

    def list_templates(self) -> List[str]:
        """
        List available templates.

        Returns:
            List of template names
        """
        try:
            templates = []
            for template_path in self.template_dir.glob("*.html"):
                templates.append(template_path.stem)
            return sorted(templates)
        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            return []


class LocalFileStorage(FileStorage):
    """
    File storage adapter using the local filesystem.

    This adapter implements the FileStorage port using the local
    filesystem for all file operations.
    """

    async def save_file(self, path: str, content: str) -> None:
        """
        Save content to a file.

        Args:
            path: File path to save to
            content: Content to save
        """
        try:
            file_path = Path(path)

            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: file_path.write_text(content, encoding='utf-8')
            )

            logger.debug(f"Saved file: {path}")

        except Exception as e:
            logger.error(f"Failed to save file {path}: {e}")
            raise

    async def read_file(self, path: str) -> str:
        """
        Read content from a file.

        Args:
            path: File path to read from

        Returns:
            File content
        """
        try:
            file_path = Path(path)

            # Read file in executor to avoid blocking
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(
                None,
                lambda: file_path.read_text(encoding='utf-8')
            )

            logger.debug(f"Read file: {path}")
            return content

        except Exception as e:
            logger.error(f"Failed to read file {path}: {e}")
            raise

    async def file_exists(self, path: str) -> bool:
        """
        Check if a file exists.

        Args:
            path: File path to check

        Returns:
            True if file exists, False otherwise
        """
        try:
            file_path = Path(path)
            return file_path.exists() and file_path.is_file()
        except Exception:
            return False

    async def create_directory(self, path: str) -> None:
        """
        Create a directory.

        Args:
            path: Directory path to create
        """
        try:
            dir_path = Path(path)
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {path}")
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {e}")
            raise

    async def list_files(self, directory: str) -> List[str]:
        """
        List files in a directory.

        Args:
            directory: Directory path to list

        Returns:
            List of file names in the directory
        """
        try:
            dir_path = Path(directory)
            if not dir_path.exists() or not dir_path.is_dir():
                return []

            files = []
            for file_path in dir_path.iterdir():
                if file_path.is_file():
                    files.append(file_path.name)

            return sorted(files)

        except Exception as e:
            logger.error(f"Failed to list files in {directory}: {e}")
            return []


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


# Export all adapters
__all__ = [
    'Jinja2TemplateEngine',
    'LocalFileStorage',
    'MemoryCacheRepository'
]
