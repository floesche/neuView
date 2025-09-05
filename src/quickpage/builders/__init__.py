"""
Builders package for QuickPage.

This package contains builder pattern implementations for creating
configured instances of complex objects like PageGenerator.
"""

from .page_generator_builder import PageGeneratorBuilder

__all__ = [
    "PageGeneratorBuilder",
]
