"""
QuickPage - Generate HTML pages for neuron types from neuprint data.

This package implements a Domain-Driven Design (DDD) architecture with:
- Core domain entities and value objects
- Application services orchestrating business logic
- Infrastructure adapters for external systems
- Clean separation of concerns and explicit error handling
"""

__version__ = "0.1.0"

# Export domain types for convenience
from .core.entities import Neuron, NeuronCollection, NeuronTypeStatistics
from .core.value_objects import BodyId, NeuronTypeName, SomaSide, SynapseCount
from .application.commands import GeneratePageCommand, DiscoverNeuronTypesCommand
from .application.services import PageGenerationService, NeuronDiscoveryService
from .shared.result import Result, Ok, Err

# Legacy imports for backward compatibility
from .config import Config
from .neuprint_connector import NeuPrintConnector
from .page_generator import PageGenerator
from .neuron_type import NeuronType, NeuronSummary, ConnectivityData
from .dataset_adapters import (
    DatasetAdapter, CNSAdapter, HemibrainAdapter, OpticLobeAdapter,
    DatasetAdapterFactory, get_dataset_adapter
)

__all__ = [
    # Domain entities
    'Neuron',
    'NeuronCollection',
    'NeuronTypeStatistics',

    # Value objects
    'BodyId',
    'NeuronTypeName',
    'SomaSide',
    'SynapseCount',

    # Application layer
    'GeneratePageCommand',
    'DiscoverNeuronTypesCommand',
    'PageGenerationService',
    'NeuronDiscoveryService',

    # Result pattern
    'Result',
    'Ok',
    'Err',

    # Legacy components (for backward compatibility)
    "Config",
    "NeuPrintConnector",
    "PageGenerator",
    "NeuronType",
    "NeuronSummary",
    "ConnectivityData",
    "DatasetAdapter",
    "CNSAdapter",
    "HemibrainAdapter",
    "OpticLobeAdapter",
    "DatasetAdapterFactory",
    "get_dataset_adapter"
]
