"""
SynapseCount value object for the QuickPage domain.

This module contains the SynapseCount value object which represents
the number of synapses for a neuron or connection.
"""

from dataclasses import dataclass


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
