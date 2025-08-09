"""
Domain value objects for QuickPage.

Value objects are immutable objects that are defined by their attributes
rather than their identity. They represent concepts in the domain that
are characterized by their values.
"""

from dataclasses import dataclass
from typing import Optional, Union
import re


@dataclass(frozen=True)
class BodyId:
    """Represents a neuron body ID."""
    value: int

    def __post_init__(self):
        if self.value < 0:
            raise ValueError(f"Body ID must be non-negative, got {self.value}")

    def __str__(self) -> str:
        return str(self.value)

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True)
class SynapseCount:
    """Represents a synapse count value."""
    value: int

    def __post_init__(self):
        if self.value < 0:
            raise ValueError(f"Synapse count must be non-negative, got {self.value}")

    def __str__(self) -> str:
        return str(self.value)

    def __int__(self) -> int:
        return self.value

    def __add__(self, other: 'SynapseCount') -> 'SynapseCount':
        return SynapseCount(self.value + other.value)


@dataclass(frozen=True)
class NeuronTypeName:
    """Represents a neuron type name with validation."""
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Neuron type name cannot be empty")

        # Basic validation - neuron type names should be alphanumeric with some special chars
        if not re.match(r'^[A-Za-z0-9_\-\.]+$', self.value.strip()):
            raise ValueError(f"Invalid neuron type name format: {self.value}")

    def __str__(self) -> str:
        return self.value.strip()


@dataclass(frozen=True)
class SomaSide:
    """Represents the soma side of a neuron."""
    value: Optional[str]

    VALID_SIDES = {'L', 'R', 'M', 'left', 'right', 'middle', None}

    def __post_init__(self):
        if self.value is not None:
            normalized = self.value.strip() if isinstance(self.value, str) else str(self.value)
            if normalized not in self.VALID_SIDES:
                raise ValueError(f"Invalid soma side: {self.value}. Must be one of {self.VALID_SIDES}")

    def __str__(self) -> str:
        return self.value if self.value is not None else "unknown"

    def normalize(self) -> str:
        """Return normalized soma side representation."""
        if self.value is None:
            return "unknown"

        side_map = {
            'L': 'left',
            'R': 'right',
            'M': 'middle',
            'left': 'left',
            'right': 'right',
            'middle': 'middle'
        }
        return side_map.get(self.value, self.value)

    def is_left(self) -> bool:
        return self.value in ('L', 'left')

    def is_right(self) -> bool:
        return self.value in ('R', 'right')

    def is_middle(self) -> bool:
        return self.value in ('M', 'middle')


@dataclass(frozen=True)
class RoiName:
    """Represents a Region of Interest (ROI) name."""
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("ROI name cannot be empty")

    def __str__(self) -> str:
        return self.value.strip()


@dataclass(frozen=True)
class SynapseStatistics:
    """Represents synapse statistics for a neuron or group of neurons."""
    pre_synapses: SynapseCount
    post_synapses: SynapseCount

    @property
    def total(self) -> SynapseCount:
        """Total synapse count."""
        return self.pre_synapses + self.post_synapses

    def pre_post_ratio(self) -> float:
        """Ratio of pre to post synapses."""
        if self.post_synapses.value == 0:
            return float('inf') if self.pre_synapses.value > 0 else 0.0
        return self.pre_synapses.value / self.post_synapses.value


# Export all value objects
__all__ = [
    'BodyId',
    'SynapseCount',
    'NeuronTypeName',
    'SomaSide',
    'RoiName',
    'SynapseStatistics'
]
