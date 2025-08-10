"""
RoiName and SynapseStatistics value objects for the QuickPage domain.

This module contains value objects related to regions of interest (ROIs)
and synapse statistics in the connectome dataset.
"""

from dataclasses import dataclass
from .synapse_count import SynapseCount


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
