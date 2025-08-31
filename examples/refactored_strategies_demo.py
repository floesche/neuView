"""
Refactored Strategies Demo

This example demonstrates how to use the newly refactored strategy implementations
that follow best practices and align with the rest of the codebase structure.

The strategies have been refactored from having all implementations in __init__.py
files to having individual dedicated modules for each strategy implementation.
"""

import sys
import tempfile
from pathlib import Path

# Add the src directory to the path so we can import quickpage modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from quickpage.strategies.cache import (
    MemoryCacheStrategy,
    FileCacheStrategy,
    LRUCacheStrategy,
    CompositeCacheStrategy
)

from quickpage.strategies.resource import (
    FileSystemResourceStrategy,
    CachedResourceStrategy,
    RemoteResourceStrategy,
    CompositeResourceStrategy,
    OptimizedResourceStrategy
)

from quickpage.strategies.template import (
    StaticTemplateStrategy,
    CompositeTemplateStrategy,
    CachedTemplateStrategy
)

try:
    from quickpage.strategies.template import JinjaTemplateStrategy
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False


def demo_cache_strategies():
    """Demonstrate the refactored cache strategies."""
    print("=== Cache Strategies Demo ===\n")

    # 1. Memory Cache Strategy
    print("1. Memory Cache Strategy:")
    memory_cache = MemoryCacheStrategy(max_size=100, default_ttl=300)

    memory_cache.put("key1", "value1")
    memory_cache.put("key2", {"data": "complex_value"})

    print(f"  Retrieved key1: {memory_cache.get('key1')}")
    print(f"  Cache size: {memory_cache.size()}")
    print(f"  Contains key1: {memory_cache.contains('key1')}")
    print()

    # 2. File Cache Strategy
    print("2. File Cache Strategy:")
    with tempfile.TemporaryDirectory() as temp_dir:
        file_cache = FileCacheStrategy(temp_dir, default_ttl=600)

        file_cache.put("persistent_key", "This will survive restarts")
        print(f"  Stored in file cache: {file_cache.get('persistent_key')}")
        print(f"  Cache directory: {temp_dir}")
    print()

    # 3. LRU Cache Strategy
    print("3. LRU Cache Strategy:")
    lru_cache = LRUCacheStrategy(max_size=3)

    lru_cache.put("a", "value_a")
    lru_cache.put("b", "value_b")
    lru_cache.put("c", "value_c")
    lru_cache.put("d", "value_d")  # This should evict 'a'

    print(f"  Key 'a' (should be None): {lru_cache.get('a')}")
    print(f"  Key 'b': {lru_cache.get('b')}")
    print(f"  Cache keys: {lru_cache.keys()}")
    print()

    # 4. Composite Cache Strategy
    print("4. Composite Cache Strategy:")
    primary = MemoryCacheStrategy(max_size=50)
    secondary = LRUCacheStrategy(max_size=100)
    composite_cache = CompositeCacheStrategy(primary, secondary)

    composite_cache.put("multi_level", "cached_in_both")
    print(f"  Retrieved from composite: {composite_cache.get('multi_level')}")
    print()


def demo_resource_strategies():
    """Demonstrate the refactored resource strategies."""
    print("=== Resource Strategies Demo ===\n")

    # Create some temporary resources for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        resource_dir = Path(temp_dir)

        # Create test files
        (resource_dir / "style.css").write_text("body { margin: 0; }")
        (resource_dir / "script.js").write_text("console.log('Hello World');")
        (resource_dir / "data.json").write_text('{"key": "value"}')

        # 1. FileSystem Resource Strategy
        print("1. FileSystem Resource Strategy:")
        fs_strategy = FileSystemResourceStrategy([str(resource_dir)])

        css_content = fs_strategy.load_resource("style.css")
        print(f"  Loaded CSS: {css_content.decode()}")

        metadata = fs_strategy.get_resource_metadata("style.css")
        print(f"  CSS file size: {metadata['size']} bytes")

        resources = fs_strategy.list_resources(Path("."), "*.js")
        print(f"  JavaScript files: {resources}")
        print()

        # 2. Cached Resource Strategy
        print("2. Cached Resource Strategy:")
        cache = MemoryCacheStrategy()
        cached_strategy = CachedResourceStrategy(fs_strategy, cache)

        # First load (from filesystem)
        content1 = cached_strategy.load_resource("script.js")
        print(f"  First load: {content1.decode()}")

        # Second load (from cache)
        content2 = cached_strategy.load_resource("script.js")
        print(f"  Second load (cached): {content2.decode()}")
        print()

        # 3. Optimized Resource Strategy
        print("3. Optimized Resource Strategy:")
        optimized_strategy = OptimizedResourceStrategy(fs_strategy, enable_compression=False)

        optimized_css = optimized_strategy.load_resource("style.css")
        print(f"  Original CSS: {css_content.decode()}")
        print(f"  Optimized CSS: {optimized_css.decode()}")
        print()

        # 4. Composite Resource Strategy
        print("4. Composite Resource Strategy:")
        composite_strategy = CompositeResourceStrategy(fs_strategy)

        # Register different strategies for different file types
        composite_strategy.register_strategy(r".*\.css$", optimized_strategy)
        composite_strategy.register_strategy(r".*\.js$", cached_strategy)

        css_via_composite = composite_strategy.load_resource("style.css")
        js_via_composite = composite_strategy.load_resource("script.js")

        print(f"  CSS via composite (optimized): {css_via_composite.decode()}")
        print(f"  JS via composite (cached): {js_via_composite.decode()}")
        print()


def demo_template_strategies():
    """Demonstrate the refactored template strategies."""
    print("=== Template Strategies Demo ===\n")

    # Create temporary templates for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        template_dir = Path(temp_dir)

        # Create test templates
        (template_dir / "basic.txt").write_text("Hello {{name}}! You have {{count}} messages.")
        (template_dir / "welcome.html").write_text("""
<!DOCTYPE html>
<html>
<head><title>Welcome {{user}}</title></head>
<body><h1>Welcome {{user}}!</h1><p>Status: {{status}}</p></body>
</html>
        """.strip())

        # 1. Static Template Strategy
        print("1. Static Template Strategy:")
        static_strategy = StaticTemplateStrategy([str(template_dir)])

        template = static_strategy.load_template("basic.txt")
        rendered = static_strategy.render_template(template, {
            "name": "Alice",
            "count": 5
        })
        print(f"  Template: {template}")
        print(f"  Rendered: {rendered}")
        print()

        # 2. Cached Template Strategy
        print("2. Cached Template Strategy:")
        cache = MemoryCacheStrategy()
        cached_strategy = CachedTemplateStrategy(static_strategy, cache)

        # First load (from filesystem)
        template1 = cached_strategy.load_template("welcome.html")
        rendered1 = cached_strategy.render_template(template1, {
            "user": "Bob",
            "status": "Active"
        })

        # Second load (from cache)
        template2 = cached_strategy.load_template("welcome.html")

        print(f"  First render: {rendered1[:50]}...")
        print(f"  Templates are same object: {template1 is template2}")
        print()

        # 3. Composite Template Strategy
        print("3. Composite Template Strategy:")
        composite_strategy = CompositeTemplateStrategy(static_strategy)

        # Register different strategies for different file types
        composite_strategy.register_strategy(r".*\.txt$", static_strategy)
        composite_strategy.register_strategy(r".*\.html$", cached_strategy)

        txt_template = composite_strategy.load_template("basic.txt")
        html_template = composite_strategy.load_template("welcome.html")

        print(f"  Loaded TXT template: {type(txt_template)}")
        print(f"  Loaded HTML template: {type(html_template)}")
        print()

        if HAS_JINJA2:
            # 4. Jinja Template Strategy (if available)
            print("4. Jinja Template Strategy:")
            (template_dir / "jinja.html").write_text("""
<h1>{{ title }}</h1>
<ul>
{% for item in items %}
    <li>{{ item.name }}: {{ item.value }}</li>
{% endfor %}
</ul>
            """.strip())

            jinja_strategy = JinjaTemplateStrategy([str(template_dir)])
            jinja_template = jinja_strategy.load_template("jinja.html")
            jinja_rendered = jinja_strategy.render_template(jinja_template, {
                "title": "My List",
                "items": [
                    {"name": "Item 1", "value": "Value 1"},
                    {"name": "Item 2", "value": "Value 2"}
                ]
            })
            print(f"  Jinja rendered: {jinja_rendered}")
        else:
            print("4. Jinja Template Strategy: (Jinja2 not available)")

        print()


def demo_integration():
    """Demonstrate how the refactored strategies work together."""
    print("=== Integration Demo ===\n")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup directories
        resource_dir = Path(temp_dir) / "resources"
        template_dir = Path(temp_dir) / "templates"
        cache_dir = Path(temp_dir) / "cache"

        resource_dir.mkdir()
        template_dir.mkdir()
        cache_dir.mkdir()

        # Create test files
        (resource_dir / "app.css").write_text("""
        body {
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
        }
        .header { background: #f0f0f0; }
        """)

        (template_dir / "page.html").write_text("""
<!DOCTYPE html>
<html>
<head>
    <title>{{title}}</title>
    <style>{{css_content}}</style>
</head>
<body>
    <div class="header">
        <h1>{{heading}}</h1>
    </div>
    <p>Generated at: {{timestamp}}</p>
</body>
</html>
        """.strip())

        # Setup integrated system
        print("Setting up integrated template and resource system...")

        # Cache strategies
        memory_cache = MemoryCacheStrategy(max_size=100)
        file_cache = FileCacheStrategy(str(cache_dir))
        composite_cache = CompositeCacheStrategy(memory_cache, file_cache)

        # Resource strategies
        fs_resource = FileSystemResourceStrategy([str(resource_dir)])
        optimized_resource = OptimizedResourceStrategy(fs_resource, enable_compression=False)
        cached_resource = CachedResourceStrategy(optimized_resource, composite_cache)

        # Template strategies
        static_template = StaticTemplateStrategy([str(template_dir)])
        cached_template = CachedTemplateStrategy(static_template, composite_cache)

        # Use the integrated system
        print("Loading and processing resources...")
        css_content = cached_resource.load_resource("app.css").decode()

        print("Loading and rendering template...")
        template = cached_template.load_template("page.html")
        rendered_page = cached_template.render_template(template, {
            "title": "Demo Page",
            "heading": "Refactored Strategies Demo",
            "css_content": css_content,
            "timestamp": "2024-01-01 12:00:00"
        })

        print("Generated page:")
        print("-" * 50)
        print(rendered_page)
        print("-" * 50)

        print(f"\nCache statistics:")
        print(f"  Memory cache size: {memory_cache.size()}")
        print(f"  File cache size: {file_cache.size()}")
        print(f"  Composite cache size: {composite_cache.size()}")


def main():
    """Run all demos to showcase the refactored strategies."""
    print("Refactored Strategies Demo")
    print("=" * 50)
    print("This demo showcases the newly refactored strategy implementations")
    print("that follow best practices and align with the codebase structure.\n")

    try:
        demo_cache_strategies()
        demo_resource_strategies()
        demo_template_strategies()
        demo_integration()

        print("=" * 50)
        print("Refactoring Benefits:")
        print("✓ Each strategy is in its own dedicated file")
        print("✓ __init__.py files only handle imports/exports")
        print("✓ Better separation of concerns")
        print("✓ Easier to test individual strategies")
        print("✓ Consistent with the rest of the codebase")
        print("✓ More maintainable and readable")

    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
