"""
Template Strategy Implementations for QuickPage Phase 3

This module provides various template strategies that can be used for
template loading, parsing, and rendering. Each strategy implements different
template engines and capabilities.

Template Strategies:
- JinjaTemplateStrategy: Full Jinja2 template support with inheritance
- StaticTemplateStrategy: Simple variable substitution without dependencies
"""

# Import base strategy interface
from ..base import TemplateStrategy

# Import strategy exceptions
from ..exceptions import TemplateError, TemplateNotFoundError, TemplateLoadError, TemplateRenderError

# Import individual template strategy implementations
from .jinja_template import JinjaTemplateStrategy
from .static_template import StaticTemplateStrategy

# Export all template strategies and interfaces
__all__ = [
    "TemplateStrategy",
    "TemplateError",
    "TemplateNotFoundError",
    "TemplateLoadError",
    "TemplateRenderError",
    "JinjaTemplateStrategy",
    "StaticTemplateStrategy",
]
