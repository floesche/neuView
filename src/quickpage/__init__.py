"""
QuickPage - Simplified architecture for generating HTML pages from neuron data.

This package provides a clean, simplified architecture that maintains all
functionality while reducing complexity and improving maintainability.
"""

__version__ = "0.1.0"

# Core domain models
from .models import (
    # Value objects
    BodyId,
    NeuronTypeName,
    SomaSide,
    SynapseCount,
    RoiName,

    # Entities
    Neuron,
    NeuronCollection,
    NeuronTypeStatistics,
    NeuronTypeConnectivity,
    ConnectivityPartner
)

# Application services
from .services import (
    # Commands
    GeneratePageCommand,
    ListNeuronTypesCommand,
    InspectNeuronTypeCommand,
    TestConnectionCommand,

    # Services
    PageGenerationService,
    NeuronDiscoveryService,
    ConnectionTestService,
    ServiceContainer,

    # Data transfer objects
    NeuronTypeInfo,
    DatasetInfo
)

# Result pattern for error handling
from .result import Result, Ok, Err

# CLI interface
from .cli import main

__all__ = [
    # Value objects
    'BodyId',
    'NeuronTypeName',
    'SomaSide',
    'SynapseCount',
    'RoiName',

    # Entities
    'Neuron',
    'NeuronCollection',
    'NeuronTypeStatistics',
    'NeuronTypeConnectivity',
    'ConnectivityPartner',

    # Commands
    'GeneratePageCommand',
    'ListNeuronTypesCommand',
    'InspectNeuronTypeCommand',
    'TestConnectionCommand',

    # Services
    'PageGenerationService',
    'NeuronDiscoveryService',
    'ConnectionTestService',
    'ServiceContainer',

    # Data transfer objects
    'NeuronTypeInfo',
    'DatasetInfo',

    # Result pattern
    'Result',
    'Ok',
    'Err',

    # CLI
    'main'
]
