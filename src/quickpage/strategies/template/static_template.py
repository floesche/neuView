"""
Static Template Strategy Implementation

This module provides a simple static template strategy that uses basic
string replacement for variable substitution without external dependencies.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from ..base import TemplateStrategy
from ..exceptions import TemplateNotFoundError, TemplateLoadError, TemplateRenderError

logger = logging.getLogger(__name__)


class StaticTemplateStrategy(TemplateStrategy):
    """
    Static template strategy for simple variable substitution.

    This strategy provides basic template functionality using string replacement
    for variable substitution. It supports simple variable syntax like {{variable}}
    and basic conditional blocks, but doesn't require external dependencies.
    """

    def __init__(self, template_dirs: List[str], variable_pattern: str = r'\{\{([^}]+)\}\}'):
        """
        Initialize static template strategy.

        Args:
            template_dirs: List of directories containing templates
            variable_pattern: Regex pattern for variable substitution (default: {{variable}})
        """
        self.template_dirs = [Path(d) for d in template_dirs]
        self.variable_pattern = re.compile(variable_pattern)

        # Validate template directories
        for template_dir in self.template_dirs:
            if not template_dir.exists():
                logger.warning(f"Template directory does not exist: {template_dir}")

    def load_template(self, template_path: str) -> str:
        """
        Load a static template from file.

        Args:
            template_path: Path to the template file

        Returns:
            Template content as string

        Raises:
            TemplateNotFoundError: If template doesn't exist
            TemplateLoadError: If template can't be loaded
        """
        # Find template file
        template_file = None
        for template_dir in self.template_dirs:
            candidate = template_dir / template_path
            if candidate.exists() and candidate.is_file():
                template_file = candidate
                break

        if template_file is None:
            raise TemplateNotFoundError(f"Template not found: {template_path}")

        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()

            return content

        except Exception as e:
            raise TemplateLoadError(f"Failed to load template {template_path}: {e}")

    def render_template(self, template: str, context: Dict[str, Any]) -> str:
        """
        Render a static template with context using string replacement.

        Args:
            template: Template content string
            context: Variables to substitute in the template

        Returns:
            Rendered template content as string

        Raises:
            TemplateRenderError: If rendering fails
        """
        try:
            def replace_var(match):
                var_name = match.group(1).strip()

                # Handle nested attribute access (e.g., user.name)
                if '.' in var_name:
                    parts = var_name.split('.')
                    value = context
                    for part in parts:
                        if isinstance(value, dict) and part in value:
                            value = value[part]
                        elif hasattr(value, part):
                            value = getattr(value, part)
                        else:
                            return f"{{{{ {var_name} }}}}"  # Return original if not found
                    return str(value) if value is not None else ""

                # Simple variable replacement
                value = context.get(var_name)
                if value is not None:
                    return str(value)
                else:
                    # Keep original placeholder if variable not found
                    return f"{{{{ {var_name} }}}}"

            # Perform variable substitution
            rendered = self.variable_pattern.sub(replace_var, template)
            return rendered

        except Exception as e:
            raise TemplateRenderError(f"Template rendering failed: {e}")

    def validate_template(self, template_path: str) -> bool:
        """
        Validate that a template can be loaded.

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
                # Look for common template extensions
                for pattern in ['*.html', '*.htm', '*.txt', '*.md']:
                    for template_file in search_dir.rglob(pattern):
                        if template_file.is_file():
                            # Get path relative to base template directory
                            relative_path = template_file.relative_to(base_dir)
                            templates.append(str(relative_path))
            except Exception as e:
                logger.warning(f"Error listing templates in {search_dir}: {e}")

        return sorted(list(set(templates)))  # Remove duplicates and sort

    def get_template_dependencies(self, template_path: str) -> List[str]:
        """
        Get dependencies for a static template.

        Static templates don't support includes/extends, so this returns empty list.

        Args:
            template_path: Path to the template file

        Returns:
            Empty list (static templates don't have dependencies)
        """
        return []

    def supports_template(self, template_path: str) -> bool:
        """
        Check if this strategy can handle the given template.

        Static strategy is best for simple templates without Jinja2 syntax.

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
            # Check file extension - .jinja files should use JinjaTemplateStrategy
            if template_path.endswith(('.jinja', '.j2')):
                return False

            # For other files, do a quick content check
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read(1000)  # Read first 1KB

            # If it contains Jinja2 syntax, it should use JinjaTemplateStrategy
            jinja_patterns = [
                '{%', '%}',  # Jinja2 statements
                '{#', '#}',  # Jinja2 comments
                '|',         # Jinja2 filters (in context of variables)
            ]

            # Simple heuristic: if it has {{}} variables AND Jinja2 syntax, use Jinja
            has_variables = '{{' in content and '}}' in content
            has_jinja_syntax = any(pattern in content for pattern in jinja_patterns)

            if has_variables and has_jinja_syntax:
                return False

            # Otherwise, static strategy can handle it
            return True

        except Exception:
            # If we can't read the file, let static strategy try
            return True
