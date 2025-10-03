"""
Resource Strategy Implementations for neuView

This module provides resource loading strategies for static resource management.
The modern approach uses UnifiedResourceStrategy which consolidates all functionality
into a single, high-performance strategy.

RECOMMENDED STRATEGY:
- UnifiedResourceStrategy: Modern unified strategy with built-in caching, optimization,
  and filesystem support. Consolidates all resource management needs.


SPECIALIZED STRATEGIES:
- RemoteResourceStrategy: HTTP/HTTPS remote resource loading
- CompositeResourceStrategy: Multi-strategy resource loading for complex scenarios
"""

# Import base strategy interface
from ..base import ResourceStrategy

# Import strategy exceptions
from ..exceptions import ResourceError, ResourceNotFoundError, ResourceLoadError

# Import individual resource strategy implementations
from .remote_resource import RemoteResourceStrategy
from .composite_resource import CompositeResourceStrategy
from .unified_resource import UnifiedResourceStrategy

# Export all resource strategies and interfaces
__all__ = [
    "ResourceStrategy",
    "ResourceError",
    "ResourceNotFoundError",
    "ResourceLoadError",
    # Modern unified strategy (recommended)
    "UnifiedResourceStrategy",
    # Specialized strategies
    "RemoteResourceStrategy",
    "CompositeResourceStrategy",
]
