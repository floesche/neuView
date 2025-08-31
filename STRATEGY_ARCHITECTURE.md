# Strategy Pattern Architecture Overview

## Refactored Module Structure

The QuickPage strategies package has been completely refactored to follow best practices and provide a clean, maintainable architecture.

```
src/quickpage/strategies/
├── __init__.py                     # Main imports and exports (94 lines)
├── base.py                         # Abstract base classes (261 lines)
├── exceptions.py                   # Strategy exceptions (97 lines)
├── cache/
│   ├── __init__.py                 # Cache imports (35 lines)
│   ├── memory_cache.py             # In-memory caching (155 lines)
│   ├── file_cache.py               # Persistent file caching (235 lines)
│   ├── lru_cache.py                # LRU eviction cache (129 lines)
│   └── composite_cache.py          # Multi-level caching (192 lines)
├── resource/
│   ├── __init__.py                 # Resource imports (40 lines)
│   ├── filesystem_resource.py      # Local file resources (213 lines)
│   ├── cached_resource.py          # Resource caching wrapper (199 lines)
│   ├── remote_resource.py          # HTTP/HTTPS resources (198 lines)
│   ├── composite_resource.py       # Multi-strategy routing (163 lines)
│   └── optimized_resource.py       # Web optimization (211 lines)
└── template/
    ├── __init__.py                 # Template imports (38 lines)
    ├── jinja_template.py           # Jinja2 template engine (245 lines)
    ├── static_template.py          # Simple variable substitution (193 lines)
    ├── composite_template.py       # Multi-strategy routing (189 lines)
    └── cached_template.py          # Template caching wrapper (229 lines)
```

## Architecture Layers

### 1. Base Layer (`base.py`)
Contains abstract base classes that define the contracts for all strategies:

- **TemplateStrategy**: Template loading, rendering, validation
- **ResourceStrategy**: Resource loading, metadata, file operations
- **CacheStrategy**: Key-value storage with TTL and eviction

### 2. Exception Layer (`exceptions.py`)
Organized exception hierarchy for proper error handling:

```
StrategyError
├── TemplateError
│   ├── TemplateNotFoundError
│   ├── TemplateLoadError
│   └── TemplateRenderError
├── ResourceError
│   ├── ResourceNotFoundError
│   └── ResourceLoadError
└── CacheError
```

### 3. Implementation Layer
Individual strategy implementations organized by category:

#### Cache Strategies
- **Memory**: Fast in-memory storage with TTL
- **File**: Persistent disk-based storage
- **LRU**: Fixed-size with least-recently-used eviction
- **Composite**: Multi-level caching (memory + file)

#### Resource Strategies
- **Filesystem**: Local file system access
- **Remote**: HTTP/HTTPS resource loading
- **Cached**: Transparent caching wrapper
- **Optimized**: Minification and compression
- **Composite**: Route by pattern/type

#### Template Strategies
- **Jinja**: Full Jinja2 template engine
- **Static**: Simple variable substitution
- **Cached**: Template compilation caching
- **Composite**: Route by file type/pattern

## Design Patterns

### 1. Strategy Pattern
Each category (cache, resource, template) uses the strategy pattern:
- Abstract base class defines interface
- Concrete implementations provide different behaviors
- Strategies are interchangeable at runtime

### 2. Decorator Pattern
Wrapper strategies add capabilities:
- `CachedResourceStrategy` adds caching to any resource strategy
- `CachedTemplateStrategy` adds caching to any template strategy
- `OptimizedResourceStrategy` adds optimization to any resource strategy

### 3. Composite Pattern
Composite strategies manage multiple strategies:
- `CompositeResourceStrategy` routes to different strategies by pattern
- `CompositeTemplateStrategy` routes to different engines by file type
- `CompositeCacheStrategy` provides multi-level caching

## Dependency Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Applications  │    │    Services     │    │    Managers     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Strategy Layer                               │
├─────────────────┬─────────────────┬─────────────────────────────┤
│ Template        │ Resource        │ Cache                       │
│ Strategies      │ Strategies      │ Strategies                  │
│                 │                 │                             │
│ • Jinja         │ • Filesystem    │ • Memory                    │
│ • Static        │ • Remote        │ • File                      │
│ • Composite     │ • Cached        │ • LRU                       │
│ • Cached        │ • Optimized     │ • Composite                 │
│                 │ • Composite     │                             │
└─────────────────┴─────────────────┴─────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Base Interfaces                               │
│  TemplateStrategy │ ResourceStrategy │ CacheStrategy            │
└─────────────────────────────────────────────────────────────────┘
```

## Import Patterns

### Backward Compatible (Recommended)
```python
# Main module imports (works with existing code)
from quickpage.strategies import MemoryCacheStrategy
from quickpage.strategies import FileSystemResourceStrategy
from quickpage.strategies import JinjaTemplateStrategy

# Category-specific imports
from quickpage.strategies.cache import LRUCacheStrategy
from quickpage.strategies.resource import OptimizedResourceStrategy
from quickpage.strategies.template import StaticTemplateStrategy
```

### Direct Module Imports (New)
```python
# Direct imports from individual files
from quickpage.strategies.cache.memory_cache import MemoryCacheStrategy
from quickpage.strategies.resource.filesystem_resource import FileSystemResourceStrategy
from quickpage.strategies.template.jinja_template import JinjaTemplateStrategy

# Base interfaces and exceptions
from quickpage.strategies.base import TemplateStrategy, CacheStrategy
from quickpage.strategies.exceptions import TemplateError, ResourceError
```

## Usage Examples

### Basic Strategy Usage
```python
from quickpage.strategies import MemoryCacheStrategy, FileSystemResourceStrategy

# Create strategies
cache = MemoryCacheStrategy(max_size=100, default_ttl=300)
resources = FileSystemResourceStrategy(['/path/to/resources'])

# Use strategies
cache.put('key', 'value')
content = resources.load_resource('style.css')
```

### Composite Strategy Pattern
```python
from quickpage.strategies import (
    CompositeResourceStrategy, 
    FileSystemResourceStrategy,
    RemoteResourceStrategy
)

# Create composite strategy
composite = CompositeResourceStrategy()

# Register strategies for different patterns
composite.register_strategy(r'^https?://', RemoteResourceStrategy())
composite.register_strategy(r'.*', FileSystemResourceStrategy(['/local/path']))

# Use unified interface
content = composite.load_resource('http://example.com/remote.css')
local_content = composite.load_resource('local.css')
```

### Decorator Strategy Pattern
```python
from quickpage.strategies import (
    FileSystemResourceStrategy,
    CachedResourceStrategy,
    OptimizedResourceStrategy,
    MemoryCacheStrategy
)

# Layer strategies for enhanced functionality
base = FileSystemResourceStrategy(['/path/to/resources'])
optimized = OptimizedResourceStrategy(base, enable_minification=True)
cached = CachedResourceStrategy(optimized, MemoryCacheStrategy())

# Get optimized and cached resource
content = cached.load_resource('app.css')  # Minified and cached
```

## Benefits of Refactored Architecture

### Code Organization
- ✅ **Single Responsibility**: Each file has one clear purpose
- ✅ **Separation of Concerns**: Interfaces, exceptions, implementations separated
- ✅ **Logical Grouping**: Related strategies grouped by category
- ✅ **Clean Imports**: No more monolithic __init__.py files

### Maintainability
- ✅ **Easy Navigation**: Find specific strategies quickly
- ✅ **Isolated Changes**: Modify one strategy without affecting others
- ✅ **Clear Dependencies**: Explicit imports show relationships
- ✅ **Better Git History**: Changes tracked per individual file

### Extensibility
- ✅ **Add New Strategies**: Drop in new files without modifying existing code
- ✅ **Strategy Composition**: Easy to combine strategies
- ✅ **Custom Implementations**: Inherit from base classes
- ✅ **Plugin Architecture**: Support for external strategy modules

### Testing
- ✅ **Unit Testing**: Test each strategy in isolation
- ✅ **Mock Dependencies**: Easy to mock individual strategies
- ✅ **Integration Testing**: Test strategy combinations
- ✅ **Performance Testing**: Benchmark individual strategies

### Developer Experience
- ✅ **IDE Support**: Better autocomplete and navigation
- ✅ **Code Search**: Easy to find specific implementations
- ✅ **Documentation**: Each module can have detailed docs
- ✅ **Learning Curve**: Easier to understand individual strategies

## Performance Impact

The refactoring has **zero negative performance impact**:

- **Import Time**: Python's import caching means no overhead
- **Runtime Performance**: Identical execution paths
- **Memory Usage**: Same memory footprint
- **Strategy Selection**: No additional overhead in strategy dispatch

## Migration Path

### Phase 1: Use Existing Imports (No Changes Required)
Existing code continues to work without modification:
```python
from quickpage.strategies import MemoryCacheStrategy  # Still works
```

### Phase 2: Adopt Category Imports (Optional)
More explicit imports for better organization:
```python
from quickpage.strategies.cache import MemoryCacheStrategy
```

### Phase 3: Direct Module Imports (Advanced)
Most explicit imports for maximum clarity:
```python
from quickpage.strategies.cache.memory_cache import MemoryCacheStrategy
```

## Future Enhancements

The new architecture enables:

1. **Plugin System**: External strategy packages
2. **Dynamic Loading**: Runtime strategy discovery
3. **Configuration-Driven**: YAML/JSON strategy configuration
4. **Monitoring Integration**: Per-strategy metrics and logging
5. **A/B Testing**: Easy strategy swapping for experiments

This refactored architecture provides a solid foundation for the QuickPage strategy pattern while maintaining full backward compatibility and enabling future enhancements.