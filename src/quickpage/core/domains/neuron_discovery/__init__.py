"""
Neuron Discovery Bounded Context

This bounded context is responsible for discovering, cataloging, and managing
neuron types and their metadata within the connectome dataset. It handles
the business logic around neuron type identification, classification, and
basic metadata management.

Key Responsibilities:
- Discovering available neuron types
- Managing neuron type metadata and classification
- Validating neuron type existence and properties
- Providing neuron type search and filtering capabilities
"""

from .entities import (
    NeuronTypeRegistry,
    NeuronTypeEntry,
    NeuronTypeMetadata
)

from .value_objects import (
    NeuronTypeId,
    NeuronTypeClassification,
    DiscoveryTimestamp,
    TypeAvailability
)

from .services import (
    NeuronTypeDiscoveryService,
    NeuronTypeValidationService,
    NeuronTypeRegistryService
)

from .repositories import (
    NeuronTypeRegistryRepository
)

from .specifications import (
    NeuronTypeExistsSpecification,
    NeuronTypeHasDataSpecification,
    NeuronTypeIsValidSpecification
)

from .events import (
    NeuronTypeDiscovered,
    NeuronTypeRegistryUpdated,
    NeuronTypeValidated,
    NeuronTypeInvalidated
)

from .factories import (
    NeuronTypeRegistryFactory,
    NeuronTypeEntryFactory
)

__all__ = [
    # Entities
    'NeuronTypeRegistry',
    'NeuronTypeEntry',
    'NeuronTypeMetadata',

    # Value Objects
    'NeuronTypeId',
    'NeuronTypeClassification',
    'DiscoveryTimestamp',
    'TypeAvailability',

    # Domain Services
    'NeuronTypeDiscoveryService',
    'NeuronTypeValidationService',
    'NeuronTypeRegistryService',

    # Repository Interfaces
    'NeuronTypeRegistryRepository',

    # Specifications
    'NeuronTypeExistsSpecification',
    'NeuronTypeHasDataSpecification',
    'NeuronTypeIsValidSpecification',

    # Domain Events
    'NeuronTypeDiscovered',
    'NeuronTypeRegistryUpdated',
    'NeuronTypeValidated',
    'NeuronTypeInvalidated',

    # Factories
    'NeuronTypeRegistryFactory',
    'NeuronTypeEntryFactory',
]
