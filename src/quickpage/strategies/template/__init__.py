"""
Template Strategy Implementations for QuickPage Phase 3

This module provides various template strategies that can be used for
template loading, parsing, and rendering. Each strategy implements different
template engines and capabilities.

Template Strategies:
- JinjaTemplateStrategy: Full Jinja2 template support with inheritance
- StaticTemplateStrategy: Simple variable substitution without dependencies
- CompositeTemplateStrategy: Multi-strategy template handling
- CachedTemplateStrategy: Adds caching to any template strategy
"""

# Import individual template strategy implementations
from .jinja_template import JinjaTemplateStrategy
from .static_template import StaticTemplateStrategy
from .composite_template import CompositeTemplateStrategy
from .cached_template import CachedTemplateStrategy

# Export all template strategies
__all__ = [
    "JinjaTemplateStrategy",
    "StaticTemplateStrategy",
    "CompositeTemplateStrategy",
    "CachedTemplateStrategy",
]
