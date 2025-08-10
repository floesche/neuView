"""
Cache repository port for the core domain layer.

This port defines the contract that the domain layer expects from
external caching systems for performance optimization.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any


class CacheRepository(ABC):
    """
    Repository interface for caching data.

    This port defines how the domain layer expects to interact with
    caching systems for performance optimization.
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a cached value by key.

        Args:
            key: The cache key

        Returns:
            Cached value if found, None otherwise
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a cached value.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Time to live in seconds (optional)
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a cached value.

        Args:
            key: The cache key

        Returns:
            True if the key was deleted, False if it didn't exist
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached values."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            key: The cache key

        Returns:
            True if the key exists, False otherwise
        """
        pass
