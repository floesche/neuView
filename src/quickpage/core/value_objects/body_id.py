"""
BodyId value object for the QuickPage domain.

This module contains the BodyId value object which represents
a unique identifier for a neuron in the connectome dataset.
"""

from dataclasses import dataclass


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
