"""
Facade package for QuickPage.

This package contains facade pattern implementations that provide
simplified interfaces for complex subsystems, hiding implementation
details and providing a clean API for external users.
"""

from .quickpage_facade import QuickPageFacade

__all__ = [
    'QuickPageFacade',
]
