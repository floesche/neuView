"""
Resource Strategy Implementations for QuickPage

This module provides resource loading strategies for static resource management.
The modern approach uses UnifiedResourceStrategy which consolidates all functionality
into a single, high-performance strategy.

RECOMMENDED STRATEGY:
- UnifiedResourceStrategy: Modern unified strategy with built-in caching, optimization,
  and filesystem support. Replaces the need for multiple wrapper strategies.

LEGACY STRATEGIES (DEPRECATED):
- FileSystemResourceStrategy: Basic filesystem loading (use UnifiedResourceStrategy)
- CachedResourceStrategy: Caching wrapper (use UnifiedResourceStrategy with cache_strategy)
- OptimizedResourceStrategy: Optimization wrapper (use UnifiedResourceStrategy with enable_optimization=True)

SPECIALIZED STRATEGIES (STILL SUPPORTED):
- RemoteResourceStrategy: HTTP/HTTPS remote resource loading
- CompositeResourceStrategy: Multi-strategy resource loading

MIGRATION GUIDE:
  # Old pattern (deprecated)
  fs_strategy = FileSystemResourceStrategy(base_paths=[...])
  opt_strategy = OptimizedResourceStrategy(fs_strategy, enable_minification=True)
  cached_strategy = CachedResourceStrategy(opt_strategy, cache_strategy)

  # New pattern (recommended)
  unified_strategy = UnifiedResourceStrategy(
      base_paths=[...],
      cache_strategy=cache_strategy,
      enable_optimization=True,
      enable_minification=True,
      enable_compression=True
  )
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
from .unified_resource import UnifiedResourceStrategy

# Export all resource strategies and interfaces
__all__ = [
    "ResourceStrategy",
    "ResourceError",
    "ResourceNotFoundError",
    "ResourceLoadError",

    # Modern unified strategy (recommended)
    "UnifiedResourceStrategy",

    # Legacy strategies (deprecated - use UnifiedResourceStrategy instead)
    "FileSystemResourceStrategy",
    "CachedResourceStrategy",
    "OptimizedResourceStrategy",

    # Specialized strategies (still supported)
    "RemoteResourceStrategy",
    "CompositeResourceStrategy",
]
