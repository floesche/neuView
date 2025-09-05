"""
Jinja Template Strategy Implementation

This module provides a Jinja2-based template strategy with support for
custom filters, globals, template inheritance, and dependency tracking.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound, TemplateSyntaxError

from ..base import TemplateStrategy
from ..exceptions import TemplateNotFoundError, TemplateLoadError, TemplateRenderError

logger = logging.getLogger(__name__)


class JinjaTemplateStrategy(TemplateStrategy):
    """
    Jinja2 template strategy for advanced template rendering.

    This strategy provides full Jinja2 template support including:
    - Template inheritance and includes
    - Custom filters and global variables
    - Template caching and compilation
    - Dependency tracking for template hierarchies
    """

    def __init__(self, template_dirs: List[str], auto_reload: bool = True, cache_size: int = 400):
        """
        Initialize Jinja template strategy.

        Args:
            template_dirs: List of directories containing templates
            auto_reload: Whether to automatically reload changed templates
            cache_size: Maximum number of compiled templates to cache

        """

        self.template_dirs = [Path(d) for d in template_dirs]
        self.auto_reload = auto_reload
        self.cache_size = cache_size
        self._environment = None
        self._custom_filters = {}
        self._custom_globals = {}

        # Validate template directories
        for template_dir in self.template_dirs:
            if not template_dir.exists():
                logger.warning(f"Template directory does not exist: {template_dir}")

    def _ensure_environment(self) -> Environment:
        """Ensure Jinja2 environment is initialized."""
        if self._environment is None:
            loader = FileSystemLoader([str(d) for d in self.template_dirs])
            self._environment = Environment(
                loader=loader,
                auto_reload=self.auto_reload,
                cache_size=self.cache_size,
                trim_blocks=True,
                lstrip_blocks=True
            )

            # Add custom filters and globals
            self._environment.filters.update(self._custom_filters)
            self._environment.globals.update(self._custom_globals)

        return self._environment

    def load_template(self, template_path: str) -> Any:
        """
        Load a Jinja2 template.

        Args:
            template_path: Path to the template file

        Returns:
            Compiled Jinja2 template object

        Raises:
            TemplateNotFoundError: If template doesn't exist
            TemplateLoadError: If template can't be loaded or compiled
        """
        try:
            env = self._ensure_environment()
            return env.get_template(template_path)
        except TemplateNotFound:
            raise TemplateNotFoundError(f"Template not found: {template_path}")
        except TemplateSyntaxError as e:
            raise TemplateLoadError(f"Template syntax error in {template_path}: {e}")
        except Exception as e:
            raise TemplateLoadError(f"Failed to load template {template_path}: {e}")

    def render_template(self, template: Any, context: Dict[str, Any]) -> str:
        """
        Render a Jinja2 template with context.

        Args:
            template: Compiled Jinja2 template
            context: Variables to pass to the template

        Returns:
            Rendered template content as string

        Raises:
            TemplateRenderError: If rendering fails
        """
        try:
            return template.render(**context)
        except Exception as e:
            raise TemplateRenderError(f"Template rendering failed: {e}")

    def validate_template(self, template_path: str) -> bool:
        """
        Validate that a template is syntactically correct.

        Args:
            template_path: Path to the template file

        Returns:
            True if template is valid, False otherwise
        """
        try:
            self.load_template(template_path)
            return True
        except (TemplateNotFoundError, TemplateLoadError):
            return False

    def list_templates(self, template_dir: Path) -> List[str]:
        """
        List all templates in the given directory.

        Args:
            template_dir: Directory to search for templates

        Returns:
            List of template paths relative to template directories
        """
        templates = []

        for base_dir in self.template_dirs:
            search_dir = base_dir / template_dir if template_dir != Path('.') else base_dir
            if not search_dir.exists() or not search_dir.is_dir():
                continue

            try:
                for template_file in search_dir.rglob('*.html'):
                    if template_file.is_file():
                        # Get path relative to base template directory
                        relative_path = template_file.relative_to(base_dir)
                        templates.append(str(relative_path))
            except Exception as e:
                logger.warning(f"Error listing templates in {search_dir}: {e}")

        return sorted(list(set(templates)))  # Remove duplicates and sort

    def get_template_dependencies(self, template_path: str) -> List[str]:
        """
        Get dependencies (includes, extends) for a template.

        Args:
            template_path: Path to the template file

        Returns:
            List of dependency template paths
        """
        dependencies = []

        # Find template file in template directories
        template_file = None
        for template_dir in self.template_dirs:
            candidate = template_dir / template_path
            if candidate.exists():
                template_file = candidate
                break

        if template_file is None:
            return dependencies

        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse Jinja2 template syntax for dependencies
            # Look for {% extends "..." %} and {% include "..." %}
            extend_pattern = r'{%\s*extends\s+["\']([^"\']+)["\']\s*%}'
            include_pattern = r'{%\s*include\s+["\']([^"\']+)["\']\s*%}'
            import_pattern = r'{%\s*(?:from\s+["\']([^"\']+)["\']\s+)?import\s+'

            for pattern in [extend_pattern, include_pattern, import_pattern]:
                matches = re.findall(pattern, content, re.IGNORECASE)
                dependencies.extend(matches)

            # Remove duplicates and filter out empty strings
            dependencies = list(set(dep for dep in dependencies if dep))

        except Exception as e:
            logger.warning(f"Error parsing template dependencies for {template_path}: {e}")

        return dependencies

    def add_filter(self, name: str, filter_func) -> None:
        """
        Add a custom filter to the Jinja environment.

        Args:
            name: Name of the filter
            filter_func: Filter function
        """
        self._custom_filters[name] = filter_func
        if self._environment:
            self._environment.filters[name] = filter_func

    def add_global(self, name: str, value: Any) -> None:
        """
        Add a global variable to the Jinja environment.

        Args:
            name: Name of the global variable
            value: Value of the global variable
        """
        self._custom_globals[name] = value
        if self._environment:
            self._environment.globals[name] = value

    def get_environment(self) -> Any:
        """Get the Jinja2 environment for advanced usage."""
        return self._ensure_environment()

    def supports_template(self, template_path: str) -> bool:
        """
        Check if this strategy can handle the given template.

        Jinja strategy is best for templates with Jinja2 syntax and .jinja extensions.

        Args:
            template_path: Path to the template file

        Returns:
            True if this strategy should handle the template
        """
        # Find template file
        template_file = None
        for template_dir in self.template_dirs:
            candidate = template_dir / template_path
            if candidate.exists() and candidate.is_file():
                template_file = candidate
                break

        if template_file is None:
            return False

        try:
            # Check file extension - .jinja files should definitely use Jinja
            if template_path.endswith(('.jinja', '.j2', '.jinja2')):
                return True

            # For other files, do a content check
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read(1000)  # Read first 1KB

            # If it contains Jinja2 syntax, it should use JinjaTemplateStrategy
            jinja_patterns = [
                '{%', '%}',  # Jinja2 statements
                '{#', '#}',  # Jinja2 comments
                '{{', '}}',  # Variables (could be simple, but check for filters)
            ]

            # Check for Jinja2-specific features
            has_jinja_syntax = any(pattern in content for pattern in jinja_patterns)
            has_filters = '|' in content and '{{' in content
            has_blocks = '{%' in content
            has_comments = '{#' in content

            # If it has advanced Jinja2 features, definitely use Jinja
            if has_blocks or has_comments or has_filters:
                return True

            # If it just has simple variables, could go either way
            # Default to True since Jinja can handle everything static can
            return has_jinja_syntax

        except Exception:
            # If we can't read the file, assume Jinja can handle it
            return True
