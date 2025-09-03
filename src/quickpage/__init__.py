"""
QuickPage - Simplified architecture for generating HTML pages from neuron data.

This package provides a clean, simplified architecture that maintains all
functionality while reducing complexity and improving maintainability.
"""

__version__ = "0.1.0"

# Page generation models
from .models import (
    PageGenerationRequest,
    PageGenerationResponse,
    AnalysisResults,
    URLCollection,
    PageGenerationMode
)

# Application services from core services module
from .commands import (
    # Commands
    GeneratePageCommand,
    TestConnectionCommand,
    FillQueueCommand,
    PopCommand,
    CreateListCommand,
    DatasetInfo
)

# Legacy services moved to internal imports only
# from .core_services import QueueService, ServiceContainer

from .services import (
    # New refactored services
    PageGenerationService,
    ConnectionTestService,
    CacheService,
    ROIProcessingService,
    SomaDetectionService,
    QueueFileManager,
    QueueProcessor
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
    # Page generation models
    'PageGenerationRequest',
    'PageGenerationResponse',
    'AnalysisResults',
    'URLCollection',
    'PageGenerationMode',

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
    'IndexService',

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
