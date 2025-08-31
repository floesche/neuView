"""
Base Strategy Interfaces for QuickPage

This module contains the abstract base classes that define the strategy interfaces
for template, resource, and cache strategies. These interfaces establish the
contracts that all strategy implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from pathlib import Path


class TemplateStrategy(ABC):
    """
    Abstract base class for template handling strategies.

    Template strategies define how templates are loaded, parsed, validated,
    and rendered. Different strategies can handle different template formats
    or provide different performance characteristics.
    """

    @abstractmethod
    def load_template(self, template_path: str) -> Any:
        """
        Load a template from the given path.

        Args:
            template_path: Path to the template file

        Returns:
            Template object that can be used for rendering

        Raises:
            TemplateNotFoundError: If template doesn't exist
            TemplateLoadError: If template can't be loaded
        """
        pass

    @abstractmethod
    def render_template(self, template: Any, context: Dict[str, Any]) -> str:
        """
        Render a template with the given context.

        Args:
            template: Template object (from load_template)
            context: Variables to pass to the template

        Returns:
            Rendered template content as string

        Raises:
            TemplateRenderError: If rendering fails
        """
        pass

    @abstractmethod
    def validate_template(self, template_path: str) -> bool:
        """
        Validate that a template is syntactically correct.

        Args:
            template_path: Path to the template file

        Returns:
            True if template is valid, False otherwise
        """
        pass

    @abstractmethod
    def list_templates(self, template_dir: Path) -> List[str]:
        """
        List all templates in the given directory.

        Args:
            template_dir: Directory to search for templates

        Returns:
            List of template names/paths
        """
        pass

    @abstractmethod
    def get_template_dependencies(self, template_path: str) -> List[str]:
        """
        Get dependencies (includes, extends, etc.) for a template.

        Args:
            template_path: Path to the template file

        Returns:
            List of dependency template paths
        """
        pass


class ResourceStrategy(ABC):
    """
    Abstract base class for resource loading strategies.

    Resource strategies define how static resources (CSS, JS, images, etc.)
    are loaded, cached, and served. Different strategies can provide different
    performance characteristics or support different source types.
    """

    @abstractmethod
    def load_resource(self, resource_path: str) -> bytes:
        """
        Load a resource from the given path.

        Args:
            resource_path: Path to the resource file

        Returns:
            Resource content as bytes

        Raises:
            ResourceNotFoundError: If resource doesn't exist
            ResourceLoadError: If resource can't be loaded
        """
        pass

    @abstractmethod
    def resource_exists(self, resource_path: str) -> bool:
        """
        Check if a resource exists.

        Args:
            resource_path: Path to the resource file

        Returns:
            True if resource exists, False otherwise
        """
        pass

    @abstractmethod
    def get_resource_metadata(self, resource_path: str) -> Dict[str, Any]:
        """
        Get metadata for a resource (size, modified time, etc.).

        Args:
            resource_path: Path to the resource file

        Returns:
            Dictionary containing resource metadata
        """
        pass

    @abstractmethod
    def list_resources(self, resource_dir: Path, pattern: str = "*") -> List[str]:
        """
        List resources matching a pattern in the given directory.

        Args:
            resource_dir: Directory to search for resources
            pattern: Glob pattern to match (default: "*")

        Returns:
            List of resource paths
        """
        pass

    @abstractmethod
    def copy_resource(self, source_path: str, dest_path: str) -> bool:
        """
        Copy a resource from source to destination.

        Args:
            source_path: Source resource path
            dest_path: Destination path

        Returns:
            True if copy was successful, False otherwise
        """
        pass


class CacheStrategy(ABC):
    """
    Abstract base class for caching strategies.

    Cache strategies define how data is stored, retrieved, and managed in cache.
    Different strategies can provide different performance characteristics,
    eviction policies, and storage backends.
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        pass

    @abstractmethod
    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None for no expiration)
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Remove a value from the cache.

        Args:
            key: Cache key

        Returns:
            True if key was found and deleted, False otherwise
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all cached values."""
        pass

    @abstractmethod
    def contains(self, key: str) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            key: Cache key

        Returns:
            True if key exists and is not expired, False otherwise
        """
        pass

    @abstractmethod
    def keys(self) -> List[str]:
        """
        Get all cache keys.

        Returns:
            List of all cache keys
        """
        pass

    @abstractmethod
    def size(self) -> int:
        """
        Get the number of items in the cache.

        Returns:
            Number of cached items
        """
        pass
