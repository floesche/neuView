"""
Facade package for neuView.

This package contains facade pattern implementations that provide
simplified interfaces for complex subsystems, hiding implementation
details and providing a clean API for external users.
"""

from .neu_view_facade import NeuViewFacade

__all__ = [
    "NeuViewFacade",
]
