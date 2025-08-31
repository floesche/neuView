"""
Strategy Pattern Implementations for QuickPage Phase 3

This package contains strategy pattern implementations for template and resource management.
The strategy pattern allows for flexible, pluggable implementations of core functionality
with improved testability and maintainability.

Strategy Categories:
- Template Strategies: Different approaches to template loading, parsing, and rendering
- Resource Strategies: Different approaches to resource loading, caching, and management
- Cache Strategies: Different caching mechanisms for templates and resources

These strategies work together to provide a flexible and optimized template and resource
management system that can adapt to different use cases and performance requirements.
"""

# Import base strategy interfaces
from .base import TemplateStrategy, ResourceStrategy, CacheStrategy

# Import strategy exceptions
from .exceptions import (
    StrategyError,
    TemplateError,
    TemplateNotFoundError,
    TemplateLoadError,
    TemplateRenderError,
    ResourceError,
    ResourceNotFoundError,
    ResourceLoadError,
    CacheError,
)

# Import cache strategy implementations
from .cache import (
    MemoryCacheStrategy,
    FileCacheStrategy,
    LRUCacheStrategy,
    CompositeCacheStrategy,
)

# Import resource strategy implementations
from .resource import (
    FileSystemResourceStrategy,
    CachedResourceStrategy,
    RemoteResourceStrategy,
    CompositeResourceStrategy,
    OptimizedResourceStrategy,
)

# Import template strategy implementations
from .template import (
    JinjaTemplateStrategy,
    StaticTemplateStrategy,
    CompositeTemplateStrategy,
    CachedTemplateStrategy,
)

# Export all strategy interfaces, exceptions, and implementations
__all__ = [
    # Base strategy interfaces
    "TemplateStrategy",
    "ResourceStrategy",
    "CacheStrategy",

    # Strategy exceptions
    "StrategyError",
    "TemplateError",
    "TemplateNotFoundError",
    "TemplateLoadError",
    "TemplateRenderError",
    "ResourceError",
    "ResourceNotFoundError",
    "ResourceLoadError",
    "CacheError",

    # Cache strategy implementations
    "MemoryCacheStrategy",
    "FileCacheStrategy",
    "LRUCacheStrategy",
    "CompositeCacheStrategy",

    # Resource strategy implementations
    "FileSystemResourceStrategy",
    "CachedResourceStrategy",
    "RemoteResourceStrategy",
    "CompositeResourceStrategy",
    "OptimizedResourceStrategy",

    # Template strategy implementations
    "JinjaTemplateStrategy",
    "StaticTemplateStrategy",
    "CompositeTemplateStrategy",
    "CachedTemplateStrategy",
]
