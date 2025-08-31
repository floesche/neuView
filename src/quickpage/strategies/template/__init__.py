"""
Template Strategy Implementations for QuickPage Phase 3

This module provides various template handling strategies that implement different
approaches to template loading, parsing, validation, and rendering. Each strategy
is optimized for different template types and use cases.

Template Strategies:
- JinjaTemplateStrategy: Full Jinja2 template support with advanced features
- StaticTemplateStrategy: Simple text/HTML templates with variable substitution
- CompositeTemplateStrategy: Combines multiple strategies for complex templates
- CachedTemplateStrategy: Adds caching layer to any template strategy
"""

import re
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List, Set
from abc import ABC

try:
    from jinja2 import Environment, FileSystemLoader, Template as JinjaTemplate
    from jinja2.exceptions import TemplateNotFound, TemplateSyntaxError, TemplateRuntimeError
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

from .. import (
    TemplateStrategy,
    TemplateError,
    TemplateNotFoundError,
    TemplateLoadError,
    TemplateRenderError,
    CacheStrategy
)

logger = logging.getLogger(__name__)


class JinjaTemplateStrategy(TemplateStrategy):
    """
    Jinja2-based template strategy with full template engine support.

    This strategy provides complete Jinja2 template functionality including
    template inheritance, includes, macros, filters, and custom extensions.
    """

    def __init__(self, template_dir: Path, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Jinja template strategy.

        Args:
            template_dir: Directory containing template files
            config: Optional Jinja2 configuration options
        """
        if not JINJA2_AVAILABLE:
            raise TemplateLoadError("Jinja2 is required for JinjaTemplateStrategy")

        self.template_dir = Path(template_dir)
        self.config = config or {}
        self._environment = None
        self._custom_filters = {}
        self._custom_globals = {}

        # Default Jinja2 configuration
        self.jinja_config = {
            'autoescape': True,
            'trim_blocks': True,
            'lstrip_blocks': True,
            'keep_trailing_newline': True,
            **self.config.get('jinja2', {})
        }

    def _ensure_environment(self):
        """Ensure Jinja2 environment is initialized."""
        if self._environment is None:
            self._environment = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                **self.jinja_config
            )

            # Add custom filters and globals
            self._environment.filters.update(self._custom_filters)
            self._environment.globals.update(self._custom_globals)

    def load_template(self, template_path: str) -> JinjaTemplate:
        """Load a Jinja2 template from the given path."""
        try:
            self._ensure_environment()
            return self._environment.get_template(template_path)
        except TemplateNotFound:
            raise TemplateNotFoundError(f"Template not found: {template_path}")
        except TemplateSyntaxError as e:
            raise TemplateLoadError(f"Template syntax error in {template_path}: {e}")
        except Exception as e:
            raise TemplateLoadError(f"Failed to load template {template_path}: {e}")

    def render_template(self, template: JinjaTemplate, context: Dict[str, Any]) -> str:
        """Render a Jinja2 template with the given context."""
        try:
            return template.render(**context)
        except TemplateRuntimeError as e:
            raise TemplateRenderError(f"Template rendering error: {e}")
        except Exception as e:
            raise TemplateRenderError(f"Failed to render template: {e}")

    def validate_template(self, template_path: str) -> bool:
        """Validate that a Jinja2 template is syntactically correct."""
        try:
            self.load_template(template_path)
            return True
        except (TemplateNotFoundError, TemplateLoadError):
            return False

    def list_templates(self, template_dir: Path) -> List[str]:
        """List all Jinja2 templates in the given directory."""
        try:
            self._ensure_environment()
            return self._environment.list_templates()
        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            return []

    def get_template_dependencies(self, template_path: str) -> List[str]:
        """Get dependencies (includes, extends, imports) for a Jinja2 template."""
        try:
            template = self.load_template(template_path)
            dependencies = set()

            # Get template source
            source, _, _ = self._environment.loader.get_source(self._environment, template_path)

            # Parse extends
            extends_matches = re.findall(r'{% extends ["\']([^"\']+)["\'] %}', source)
            dependencies.update(extends_matches)

            # Parse includes
            include_matches = re.findall(r'{% include ["\']([^"\']+)["\'] %}', source)
            dependencies.update(include_matches)

            # Parse imports
            import_matches = re.findall(r'{% import ["\']([^"\']+)["\']', source)
            dependencies.update(import_matches)

            # Parse from imports
            from_matches = re.findall(r'{% from ["\']([^"\']+)["\']', source)
            dependencies.update(from_matches)

            return list(dependencies)

        except Exception as e:
            logger.error(f"Failed to get dependencies for {template_path}: {e}")
            return []

    def add_filter(self, name: str, filter_func: callable) -> None:
        """Add a custom filter to the Jinja2 environment."""
        self._custom_filters[name] = filter_func
        if self._environment:
            self._environment.filters[name] = filter_func

    def add_global(self, name: str, value: Any) -> None:
        """Add a global variable to the Jinja2 environment."""
        self._custom_globals[name] = value
        if self._environment:
            self._environment.globals[name] = value

    def get_environment(self) -> Environment:
        """Get the Jinja2 environment instance."""
        self._ensure_environment()
        return self._environment


class StaticTemplateStrategy(TemplateStrategy):
    """
    Simple template strategy for static text/HTML with basic variable substitution.

    This strategy handles simple templates with ${variable} or {{variable}}
    placeholders. It's lightweight and doesn't require Jinja2.
    """

    def __init__(self, template_dir: Path, variable_pattern: str = r'\$\{([^}]+)\}'):
        """
        Initialize static template strategy.

        Args:
            template_dir: Directory containing template files
            variable_pattern: Regex pattern for variable substitution
        """
        self.template_dir = Path(template_dir)
        self.variable_pattern = re.compile(variable_pattern)
        self._template_cache = {}

    def load_template(self, template_path: str) -> str:
        """Load a static template from the given path."""
        full_path = self.template_dir / template_path

        if not full_path.exists():
            raise TemplateNotFoundError(f"Template not found: {template_path}")

        try:
            if template_path not in self._template_cache:
                with open(full_path, 'r', encoding='utf-8') as f:
                    self._template_cache[template_path] = f.read()
            return self._template_cache[template_path]
        except Exception as e:
            raise TemplateLoadError(f"Failed to load template {template_path}: {e}")

    def render_template(self, template: str, context: Dict[str, Any]) -> str:
        """Render a static template with the given context."""
        try:
            def replace_var(match):
                var_name = match.group(1).strip()

                # Support nested variable access (e.g., ${obj.attr})
                try:
                    value = context
                    for part in var_name.split('.'):
                        if isinstance(value, dict):
                            value = value[part]
                        else:
                            value = getattr(value, part)
                    return str(value)
                except (KeyError, AttributeError, TypeError):
                    logger.warning(f"Variable not found in context: {var_name}")
                    return match.group(0)  # Return original placeholder

            return self.variable_pattern.sub(replace_var, template)

        except Exception as e:
            raise TemplateRenderError(f"Failed to render static template: {e}")

    def validate_template(self, template_path: str) -> bool:
        """Validate that a static template exists and is readable."""
        try:
            self.load_template(template_path)
            return True
        except (TemplateNotFoundError, TemplateLoadError):
            return False

    def list_templates(self, template_dir: Path) -> List[str]:
        """List all static templates in the given directory."""
        try:
            template_dir = Path(template_dir)
            if not template_dir.exists():
                return []

            templates = []
            for ext in ['*.html', '*.htm', '*.txt', '*.md']:
                templates.extend([
                    str(p.relative_to(template_dir))
                    for p in template_dir.rglob(ext)
                ])
            return sorted(templates)

        except Exception as e:
            logger.error(f"Failed to list static templates: {e}")
            return []

    def get_template_dependencies(self, template_path: str) -> List[str]:
        """Get dependencies for a static template (none for this strategy)."""
        return []

    def clear_cache(self) -> None:
        """Clear the template cache."""
        self._template_cache.clear()


class CompositeTemplateStrategy(TemplateStrategy):
    """
    Composite template strategy that delegates to different strategies based on file type.

    This strategy allows using different template engines for different file types
    within the same application (e.g., Jinja2 for .html files, static for .txt files).
    """

    def __init__(self, template_dir: Path):
        """
        Initialize composite template strategy.

        Args:
            template_dir: Directory containing template files
        """
        self.template_dir = Path(template_dir)
        self._strategies: Dict[str, TemplateStrategy] = {}
        self._default_strategy = None

    def register_strategy(self, file_extension: str, strategy: TemplateStrategy) -> None:
        """
        Register a strategy for a specific file extension.

        Args:
            file_extension: File extension (e.g., '.html', '.txt')
            strategy: Template strategy to use for this extension
        """
        self._strategies[file_extension.lower()] = strategy

    def set_default_strategy(self, strategy: TemplateStrategy) -> None:
        """Set the default strategy for unrecognized file types."""
        self._default_strategy = strategy

    def _get_strategy_for_template(self, template_path: str) -> TemplateStrategy:
        """Get the appropriate strategy for a template path."""
        ext = Path(template_path).suffix.lower()

        if ext in self._strategies:
            return self._strategies[ext]
        elif self._default_strategy:
            return self._default_strategy
        else:
            raise TemplateLoadError(f"No strategy registered for file type: {ext}")

    def load_template(self, template_path: str) -> Any:
        """Load a template using the appropriate strategy."""
        strategy = self._get_strategy_for_template(template_path)
        return strategy.load_template(template_path)

    def render_template(self, template: Any, context: Dict[str, Any]) -> str:
        """Render a template (strategy is embedded in template object)."""
        # For composite strategy, we need to track which strategy was used
        # This is a simplified implementation - in practice, you'd want to
        # store the strategy reference with the template
        if hasattr(template, '_strategy'):
            return template._strategy.render_template(template, context)
        else:
            # Fallback: try to determine strategy from template type
            if JINJA2_AVAILABLE and isinstance(template, JinjaTemplate):
                jinja_strategy = JinjaTemplateStrategy(self.template_dir)
                return jinja_strategy.render_template(template, context)
            elif isinstance(template, str):
                static_strategy = StaticTemplateStrategy(self.template_dir)
                return static_strategy.render_template(template, context)
            else:
                raise TemplateRenderError("Cannot determine template strategy")

    def validate_template(self, template_path: str) -> bool:
        """Validate a template using the appropriate strategy."""
        try:
            strategy = self._get_strategy_for_template(template_path)
            return strategy.validate_template(template_path)
        except Exception:
            return False

    def list_templates(self, template_dir: Path) -> List[str]:
        """List all templates using all registered strategies."""
        all_templates = set()

        for strategy in self._strategies.values():
            templates = strategy.list_templates(template_dir)
            all_templates.update(templates)

        if self._default_strategy:
            templates = self._default_strategy.list_templates(template_dir)
            all_templates.update(templates)

        return sorted(list(all_templates))

    def get_template_dependencies(self, template_path: str) -> List[str]:
        """Get dependencies using the appropriate strategy."""
        try:
            strategy = self._get_strategy_for_template(template_path)
            return strategy.get_template_dependencies(template_path)
        except Exception as e:
            logger.error(f"Failed to get dependencies for {template_path}: {e}")
            return []


class CachedTemplateStrategy(TemplateStrategy):
    """
    Template strategy wrapper that adds caching to any template strategy.

    This strategy acts as a decorator around another template strategy,
    adding template caching for improved performance.
    """

    def __init__(self, wrapped_strategy: TemplateStrategy, cache_strategy: CacheStrategy):
        """
        Initialize cached template strategy.

        Args:
            wrapped_strategy: The template strategy to wrap with caching
            cache_strategy: The cache strategy to use for template storage
        """
        self.wrapped_strategy = wrapped_strategy
        self.cache_strategy = cache_strategy
        self._dependency_cache = {}

    def _get_cache_key(self, template_path: str, operation: str) -> str:
        """Generate a cache key for a template operation."""
        return f"template:{operation}:{template_path}"

    def load_template(self, template_path: str) -> Any:
        """Load a template with caching."""
        cache_key = self._get_cache_key(template_path, "load")

        # Try to get from cache first
        cached_template = self.cache_strategy.get(cache_key)
        if cached_template is not None:
            return cached_template

        # Load from wrapped strategy
        template = self.wrapped_strategy.load_template(template_path)

        # Cache the template
        self.cache_strategy.put(cache_key, template)

        return template

    def render_template(self, template: Any, context: Dict[str, Any]) -> str:
        """Render a template (delegated to wrapped strategy)."""
        # Template rendering is not cached as context varies
        return self.wrapped_strategy.render_template(template, context)

    def validate_template(self, template_path: str) -> bool:
        """Validate a template with caching."""
        cache_key = self._get_cache_key(template_path, "validate")

        # Try to get validation result from cache
        cached_result = self.cache_strategy.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Validate using wrapped strategy
        result = self.wrapped_strategy.validate_template(template_path)

        # Cache the validation result
        self.cache_strategy.put(cache_key, result, ttl=300)  # Cache for 5 minutes

        return result

    def list_templates(self, template_dir: Path) -> List[str]:
        """List templates with caching."""
        cache_key = f"templates:list:{template_dir}"

        # Try to get from cache first
        cached_list = self.cache_strategy.get(cache_key)
        if cached_list is not None:
            return cached_list

        # Get from wrapped strategy
        template_list = self.wrapped_strategy.list_templates(template_dir)

        # Cache the list
        self.cache_strategy.put(cache_key, template_list, ttl=60)  # Cache for 1 minute

        return template_list

    def get_template_dependencies(self, template_path: str) -> List[str]:
        """Get template dependencies with caching."""
        if template_path in self._dependency_cache:
            return self._dependency_cache[template_path]

        dependencies = self.wrapped_strategy.get_template_dependencies(template_path)
        self._dependency_cache[template_path] = dependencies

        return dependencies

    def clear_cache(self) -> None:
        """Clear all cached templates."""
        self.cache_strategy.clear()
        self._dependency_cache.clear()

    def invalidate_template(self, template_path: str) -> None:
        """Invalidate cache for a specific template."""
        operations = ["load", "validate"]
        for op in operations:
            cache_key = self._get_cache_key(template_path, op)
            self.cache_strategy.delete(cache_key)

        if template_path in self._dependency_cache:
            del self._dependency_cache[template_path]


# Export template strategies
__all__ = [
    "JinjaTemplateStrategy",
    "StaticTemplateStrategy",
    "CompositeTemplateStrategy",
    "CachedTemplateStrategy",
]
