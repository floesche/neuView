"""
Dependency injection container for QuickPage.

This module provides the main interface for dependency injection,
importing the container implementation from a separate file.
"""

from .dependency_injection import Container, ServiceInfo, get_container, setup_container

# Export public interface
__all__ = [
    'Container',
    'ServiceInfo',
    'get_container',
    'setup_container'
]
