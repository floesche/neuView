"""
Infrastructure adapters for QuickPage.

These adapters implement the domain ports using concrete technologies
like Jinja2 for templating, local filesystem for storage, and memory
for caching.

This module imports all adapter classes from their separate files and exports
them for use throughout the application.
"""

from .jinja2_template_engine import Jinja2TemplateEngine
from .local_file_storage import LocalFileStorage
from .memory_cache_repository import MemoryCacheRepository

# Export all adapters
__all__ = [
    'Jinja2TemplateEngine',
    'LocalFileStorage',
    'MemoryCacheRepository'
]
