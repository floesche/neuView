"""
Domain ports (interfaces) for QuickPage.

Ports define the contracts that the domain layer expects from external systems.
They are implemented by adapters in the infrastructure layer.
"""

from .neuron_repository import NeuronRepository
from .connectivity_repository import ConnectivityRepository
from .cache_repository import CacheRepository
from .template_engine import TemplateEngine
from .file_storage import FileStorage

# Export all ports
__all__ = [
    'NeuronRepository',
    'ConnectivityRepository',
    'CacheRepository',
    'TemplateEngine',
    'FileStorage'
]
