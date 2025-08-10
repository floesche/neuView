"""
NeuronTypeName value object for the QuickPage domain.

This module contains the NeuronTypeName value object which represents
a validated neuron type identifier in the connectome dataset.
"""

import re
from dataclasses import dataclass


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
