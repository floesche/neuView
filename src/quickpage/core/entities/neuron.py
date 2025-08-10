"""
Neuron entity for the QuickPage domain.

This module contains the Neuron entity which represents a single neuron
in the connectome dataset. It is a core domain entity with business logic
and behavior related to individual neurons.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from ..value_objects import (
    BodyId, NeuronTypeName, SomaSide, SynapseStatistics, RoiName, SynapseCount
)


@dataclass
class Neuron:
    """
    Core domain entity representing a single neuron.

    A neuron is uniquely identified by its body_id and represents
    a single cell in the connectome dataset.
    """
    body_id: BodyId
    neuron_type: NeuronTypeName
    soma_side: SomaSide
    synapse_stats: SynapseStatistics
    roi_counts: Dict[RoiName, SynapseCount] = field(default_factory=dict)

    def __post_init__(self):
        """Validate entity after creation."""
        if self.body_id.value <= 0:
            raise ValueError("Neuron must have a valid body ID")

    def get_total_synapses(self) -> SynapseCount:
        """Get total synapse count for this neuron."""
        return self.synapse_stats.total

    def get_roi_synapse_count(self, roi: RoiName) -> SynapseCount:
        """Get synapse count for a specific ROI."""
        return self.roi_counts.get(roi, SynapseCount(0))

    def has_roi(self, roi: RoiName) -> bool:
        """Check if neuron has synapses in the given ROI."""
        return roi in self.roi_counts and self.roi_counts[roi].value > 0

    def is_valid(self) -> bool:
        """Check if neuron has valid data."""
        return (
            self.body_id.value > 0 and
            self.get_total_synapses().value > 0
        )

    def __eq__(self, other) -> bool:
        """Neurons are equal if they have the same body ID."""
        if not isinstance(other, Neuron):
            return False
        return self.body_id == other.body_id

    def __hash__(self) -> int:
        """Hash based on body ID (identity)."""
        return hash(self.body_id)

    def __str__(self) -> str:
        return f"Neuron({self.body_id}, {self.neuron_type}, {self.soma_side})"
