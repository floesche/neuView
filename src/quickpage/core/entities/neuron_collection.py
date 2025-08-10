"""
NeuronCollection entity for the QuickPage domain.

This module contains the NeuronCollection aggregate root and related entities
for managing collections of neurons of the same type.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from .neuron import Neuron
from ..value_objects import (
    NeuronTypeName, SomaSide, SynapseCount
)


@dataclass
class NeuronTypeStatistics:
    """
    Value object containing statistical summary of a neuron type collection.

    This is computed from a NeuronCollection and represents
    aggregate statistics at a point in time.
    """
    type_name: NeuronTypeName
    total_count: int
    left_count: int
    right_count: int
    middle_count: int
    total_pre_synapses: SynapseCount
    total_post_synapses: SynapseCount
    avg_pre_synapses: float
    avg_post_synapses: float

    @property
    def total_synapses(self) -> SynapseCount:
        """Total synapse count across all neurons."""
        return self.total_pre_synapses + self.total_post_synapses

    def pre_post_ratio(self) -> float:
        """Average pre/post synapse ratio."""
        if self.total_post_synapses.value == 0:
            return float('inf') if self.total_pre_synapses.value > 0 else 0.0
        return self.total_pre_synapses.value / self.total_post_synapses.value

    def left_right_ratio(self) -> float:
        """Ratio of left to right neurons."""
        if self.right_count == 0:
            return float('inf') if self.left_count > 0 else 0.0
        return self.left_count / self.right_count

    def is_bilateral(self) -> bool:
        """Check if type has neurons on both sides."""
        return self.left_count > 0 and self.right_count > 0


@dataclass
class NeuronCollection:
    """
    Aggregate root representing a collection of neurons of the same type.

    This aggregate manages the consistency and business rules for
    groups of neurons that belong to the same neuron type.
    """
    type_name: NeuronTypeName
    neurons: List[Neuron] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    fetched_from: Optional[str] = None

    def add_neuron(self, neuron: Neuron) -> None:
        """Add a neuron to the collection."""
        if neuron.neuron_type != self.type_name:
            raise ValueError(
                f"Cannot add neuron of type {neuron.neuron_type} "
                f"to collection of type {self.type_name}"
            )

        # Prevent duplicates (same body ID)
        if neuron not in self.neurons:
            self.neurons.append(neuron)

    def remove_neuron(self, body_id) -> bool:
        """Remove a neuron by body ID. Returns True if removed."""
        from ..value_objects import BodyId
        if not isinstance(body_id, BodyId):
            body_id = BodyId(body_id)

        for i, neuron in enumerate(self.neurons):
            if neuron.body_id == body_id:
                self.neurons.pop(i)
                return True
        return False

    def get_neuron_by_body_id(self, body_id) -> Optional[Neuron]:
        """Find a neuron by its body ID."""
        from ..value_objects import BodyId
        if not isinstance(body_id, BodyId):
            body_id = BodyId(body_id)

        for neuron in self.neurons:
            if neuron.body_id == body_id:
                return neuron
        return None

    def filter_by_soma_side(self, soma_side: SomaSide) -> 'NeuronCollection':
        """Create a new collection filtered by soma side."""
        filtered_neurons = [
            neuron for neuron in self.neurons
            if neuron.soma_side == soma_side or soma_side.value == 'all'
        ]

        return NeuronCollection(
            type_name=self.type_name,
            neurons=filtered_neurons,
            created_at=self.created_at,
            fetched_from=self.fetched_from
        )

    def get_neurons_by_side(self, side: str) -> List[Neuron]:
        """Get neurons for a specific soma side."""
        soma_side = SomaSide(side)
        if side == 'all':
            return self.neurons.copy()

        return [
            neuron for neuron in self.neurons
            if neuron.soma_side.normalize() == soma_side.normalize()
        ]

    def count_total(self) -> int:
        """Get total neuron count."""
        return len(self.neurons)

    def count_by_side(self, side: str) -> int:
        """Get neuron count for a specific side."""
        return len(self.get_neurons_by_side(side))

    def calculate_statistics(self) -> NeuronTypeStatistics:
        """Calculate aggregate statistics for this collection."""
        if not self.neurons:
            return NeuronTypeStatistics(
                type_name=self.type_name,
                total_count=0,
                left_count=0,
                right_count=0,
                middle_count=0,
                total_pre_synapses=SynapseCount(0),
                total_post_synapses=SynapseCount(0),
                avg_pre_synapses=0.0,
                avg_post_synapses=0.0
            )

        total_pre = sum(neuron.synapse_stats.pre_synapses.value for neuron in self.neurons)
        total_post = sum(neuron.synapse_stats.post_synapses.value for neuron in self.neurons)

        return NeuronTypeStatistics(
            type_name=self.type_name,
            total_count=len(self.neurons),
            left_count=self.count_by_side('left'),
            right_count=self.count_by_side('right'),
            middle_count=self.count_by_side('middle'),
            total_pre_synapses=SynapseCount(total_pre),
            total_post_synapses=SynapseCount(total_post),
            avg_pre_synapses=total_pre / len(self.neurons),
            avg_post_synapses=total_post / len(self.neurons)
        )

    def is_empty(self) -> bool:
        """Check if collection has no neurons."""
        return len(self.neurons) == 0

    def has_bilateral_neurons(self) -> bool:
        """Check if collection has neurons on both sides."""
        has_left = any(neuron.soma_side.is_left() for neuron in self.neurons)
        has_right = any(neuron.soma_side.is_right() for neuron in self.neurons)
        return has_left and has_right

    def get_unique_rois(self) -> List:
        """Get all unique ROIs present in the neurons."""
        from ..value_objects import RoiName
        all_rois = set()
        for neuron in self.neurons:
            all_rois.update(neuron.roi_counts.keys())
        return sorted(list(all_rois), key=lambda roi: roi.value)

    def __len__(self) -> int:
        return len(self.neurons)

    def __iter__(self):
        return iter(self.neurons)

    def __str__(self) -> str:
        return f"NeuronCollection({self.type_name}, {len(self.neurons)} neurons)"
