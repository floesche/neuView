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

# Application services from core services module
from .core_services import (
    # Commands
    GeneratePageCommand,
    TestConnectionCommand,
    FillQueueCommand,
    PopCommand,
    CreateListCommand,

    # Services
    PageGenerationService,
    ConnectionTestService,
    QueueService,
    ServiceContainer,

    # Data transfer objects
    DatasetInfo
)

# Commands and services from services package
from .services.neuron_discovery_service import (
    ListNeuronTypesCommand,
    InspectNeuronTypeCommand,
    NeuronDiscoveryService,
    NeuronTypeInfo
)

# Specialized services from services package
from .services import IndexService

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
    'FillQueueCommand',
    'PopCommand',
    'CreateListCommand',

    # Services
    'PageGenerationService',
    'NeuronDiscoveryService',
    'ConnectionTestService',
    'QueueService',
    'IndexService',
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
