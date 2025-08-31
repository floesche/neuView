"""
Resource Strategy Implementations for QuickPage Phase 3

This module provides various resource loading strategies that can be used for
static resource management. Each strategy implements different resource loading
mechanisms with various capabilities and optimizations.

Resource Strategies:
- FileSystemResourceStrategy: Local file system resource loading
- CachedResourceStrategy: Adds caching to any resource strategy
- RemoteResourceStrategy: HTTP/HTTPS remote resource loading
- CompositeResourceStrategy: Multi-strategy resource loading
- OptimizedResourceStrategy: Resource optimization (minification, compression)
"""

# Import base strategy interface
from ..base import ResourceStrategy

# Import strategy exceptions
from ..exceptions import ResourceError, ResourceNotFoundError, ResourceLoadError

# Import individual resource strategy implementations
from .filesystem_resource import FileSystemResourceStrategy
from .cached_resource import CachedResourceStrategy
from .remote_resource import RemoteResourceStrategy
from .composite_resource import CompositeResourceStrategy
from .optimized_resource import OptimizedResourceStrategy

# Export all resource strategies and interfaces
__all__ = [
    "ResourceStrategy",
    "ResourceError",
    "ResourceNotFoundError",
    "ResourceLoadError",
    "FileSystemResourceStrategy",
    "CachedResourceStrategy",
    "RemoteResourceStrategy",
    "CompositeResourceStrategy",
    "OptimizedResourceStrategy",
]
