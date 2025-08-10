"""
Specification Pattern Implementation for QuickPage Domain

The Specification pattern allows us to encapsulate business rules in a composable,
testable way. Specifications can be combined using logical operators and provide
a clean way to express complex domain rules and queries.

Key Benefits:
- Encapsulates business rules in reusable objects
- Supports composition through logical operators (AND, OR, NOT)
- Makes complex domain logic testable and maintainable
- Separates query logic from entity implementation
- Enables dynamic query building
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Union

# Generic type for entities that specifications operate on
T = TypeVar('T')


class Specification(ABC, Generic[T]):
    """
    Abstract base class for all specifications.

    A specification encapsulates a business rule that can be evaluated
    against an entity to determine if it satisfies certain criteria.
    """

    @abstractmethod
    def is_satisfied_by(self, entity: T) -> bool:
        """
        Check if the given entity satisfies this specification.

        Args:
            entity: The entity to evaluate

        Returns:
            True if the entity satisfies the specification, False otherwise
        """
        pass

    def and_(self, other: 'Specification[T]') -> 'AndSpecification[T]':
        """Combine this specification with another using AND logic."""
        return AndSpecification(self, other)

    def or_(self, other: 'Specification[T]') -> 'OrSpecification[T]':
        """Combine this specification with another using OR logic."""
        return OrSpecification(self, other)

    def not_(self) -> 'NotSpecification[T]':
        """Negate this specification."""
        return NotSpecification(self)

    def __and__(self, other: 'Specification[T]') -> 'AndSpecification[T]':
        """Enable & operator for AND combinations."""
        return self.and_(other)

    def __or__(self, other: 'Specification[T]') -> 'OrSpecification[T]':
        """Enable | operator for OR combinations."""
        return self.or_(other)

    def __invert__(self) -> 'NotSpecification[T]':
        """Enable ~ operator for NOT operations."""
        return self.not_()


class CompositeSpecification(Specification[T]):
    """Base class for composite specifications that combine multiple specifications."""
    pass


class AndSpecification(CompositeSpecification[T]):
    """Specification that combines two specifications with AND logic."""

    def __init__(self, left: Specification[T], right: Specification[T]):
        self.left = left
        self.right = right

    def is_satisfied_by(self, entity: T) -> bool:
        """Entity must satisfy both specifications."""
        return self.left.is_satisfied_by(entity) and self.right.is_satisfied_by(entity)


class OrSpecification(CompositeSpecification[T]):
    """Specification that combines two specifications with OR logic."""

    def __init__(self, left: Specification[T], right: Specification[T]):
        self.left = left
        self.right = right

    def is_satisfied_by(self, entity: T) -> bool:
        """Entity must satisfy at least one specification."""
        return self.left.is_satisfied_by(entity) or self.right.is_satisfied_by(entity)


class NotSpecification(CompositeSpecification[T]):
    """Specification that negates another specification."""

    def __init__(self, specification: Specification[T]):
        self.specification = specification

    def is_satisfied_by(self, entity: T) -> bool:
        """Entity must NOT satisfy the wrapped specification."""
        return not self.specification.is_satisfied_by(entity)


# Concrete Specifications for Neuron Domain

from ..entities import Neuron, NeuronCollection
from ..value_objects import SynapseCount, SomaSide, RoiName


class HighQualityNeuronSpecification(Specification[Neuron]):
    """Specification for neurons that meet high quality criteria."""

    def __init__(self, min_synapses: int = 100, min_rois: int = 3):
        self.min_synapses = min_synapses
        self.min_rois = min_rois

    def is_satisfied_by(self, neuron: Neuron) -> bool:
        """Check if neuron meets high quality criteria."""
        return (
            neuron.get_total_synapses().value >= self.min_synapses and
            len(neuron.roi_counts) >= self.min_rois and
            neuron.is_valid()
        )


class BilateralNeuronSpecification(Specification[Neuron]):
    """Specification for neurons with bilateral soma sides."""

    def is_satisfied_by(self, neuron: Neuron) -> bool:
        """Check if neuron has left or right soma side."""
        return neuron.soma_side.is_left() or neuron.soma_side.is_right()


class SomaSideSpecification(Specification[Neuron]):
    """Specification for neurons with a specific soma side."""

    def __init__(self, soma_side: SomaSide):
        self.soma_side = soma_side

    def is_satisfied_by(self, neuron: Neuron) -> bool:
        """Check if neuron has the specified soma side."""
        return neuron.soma_side == self.soma_side


class HasRoiSpecification(Specification[Neuron]):
    """Specification for neurons that have synapses in a specific ROI."""

    def __init__(self, roi: RoiName, min_synapses: int = 1):
        self.roi = roi
        self.min_synapses = min_synapses

    def is_satisfied_by(self, neuron: Neuron) -> bool:
        """Check if neuron has minimum synapses in the specified ROI."""
        return neuron.get_roi_synapse_count(self.roi).value >= self.min_synapses


class SynapseCountRangeSpecification(Specification[Neuron]):
    """Specification for neurons within a synapse count range."""

    def __init__(self, min_count: int = 0, max_count: int = float('inf')):
        self.min_count = min_count
        self.max_count = max_count

    def is_satisfied_by(self, neuron: Neuron) -> bool:
        """Check if neuron's synapse count is within the specified range."""
        synapse_count = neuron.get_total_synapses().value
        return self.min_count <= synapse_count <= self.max_count


class PrePostRatioSpecification(Specification[Neuron]):
    """Specification for neurons with specific pre/post synapse ratios."""

    def __init__(self, min_ratio: float = 0.0, max_ratio: float = float('inf')):
        self.min_ratio = min_ratio
        self.max_ratio = max_ratio

    def is_satisfied_by(self, neuron: Neuron) -> bool:
        """Check if neuron's pre/post ratio is within the specified range."""
        if neuron.synapse_stats.post_synapses.value == 0:
            return self.max_ratio == float('inf')

        ratio = neuron.synapse_stats.pre_synapses.value / neuron.synapse_stats.post_synapses.value
        return self.min_ratio <= ratio <= self.max_ratio


class ValidNeuronSpecification(Specification[Neuron]):
    """Specification for valid neurons."""

    def is_satisfied_by(self, neuron: Neuron) -> bool:
        """Check if neuron is valid."""
        return neuron.is_valid()


# Collection Specifications

class MinimumSizeCollectionSpecification(Specification[NeuronCollection]):
    """Specification for collections with minimum size."""

    def __init__(self, min_size: int):
        self.min_size = min_size

    def is_satisfied_by(self, collection: NeuronCollection) -> bool:
        """Check if collection has minimum number of neurons."""
        return len(collection.neurons) >= self.min_size


class BilateralCollectionSpecification(Specification[NeuronCollection]):
    """Specification for collections with bilateral representation."""

    def is_satisfied_by(self, collection: NeuronCollection) -> bool:
        """Check if collection has bilateral neurons."""
        return collection.has_bilateral_neurons()


class HighQualityCollectionSpecification(Specification[NeuronCollection]):
    """Specification for high-quality neuron collections."""

    def __init__(self, min_neurons: int = 10, min_quality_ratio: float = 0.8):
        self.min_neurons = min_neurons
        self.min_quality_ratio = min_quality_ratio
        self.high_quality_spec = HighQualityNeuronSpecification()

    def is_satisfied_by(self, collection: NeuronCollection) -> bool:
        """Check if collection meets high quality standards."""
        if len(collection.neurons) < self.min_neurons:
            return False

        high_quality_count = sum(
            1 for neuron in collection.neurons
            if self.high_quality_spec.is_satisfied_by(neuron)
        )

        quality_ratio = high_quality_count / len(collection.neurons)
        return quality_ratio >= self.min_quality_ratio


# Utility Functions

def filter_neurons(neurons: List[Neuron], specification: Specification[Neuron]) -> List[Neuron]:
    """Filter a list of neurons using a specification."""
    return [neuron for neuron in neurons if specification.is_satisfied_by(neuron)]


def any_neuron_satisfies(neurons: List[Neuron], specification: Specification[Neuron]) -> bool:
    """Check if any neuron in the list satisfies the specification."""
    return any(specification.is_satisfied_by(neuron) for neuron in neurons)


def all_neurons_satisfy(neurons: List[Neuron], specification: Specification[Neuron]) -> bool:
    """Check if all neurons in the list satisfy the specification."""
    return all(specification.is_satisfied_by(neuron) for neuron in neurons)


def count_satisfying_neurons(neurons: List[Neuron], specification: Specification[Neuron]) -> int:
    """Count how many neurons satisfy the specification."""
    return sum(1 for neuron in neurons if specification.is_satisfied_by(neuron))


# Export all specifications
__all__ = [
    # Base classes
    'Specification',
    'CompositeSpecification',
    'AndSpecification',
    'OrSpecification',
    'NotSpecification',

    # Neuron specifications
    'HighQualityNeuronSpecification',
    'BilateralNeuronSpecification',
    'SomaSideSpecification',
    'HasRoiSpecification',
    'SynapseCountRangeSpecification',
    'PrePostRatioSpecification',
    'ValidNeuronSpecification',

    # Collection specifications
    'MinimumSizeCollectionSpecification',
    'BilateralCollectionSpecification',
    'HighQualityCollectionSpecification',

    # Utility functions
    'filter_neurons',
    'any_neuron_satisfies',
    'all_neurons_satisfy',
    'count_satisfying_neurons',
]
