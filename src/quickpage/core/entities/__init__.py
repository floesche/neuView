"""
Domain entities for QuickPage.

Entities are objects that have a distinct identity that runs through time
and different representations. They are defined by their identity rather
than their attributes.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from ..value_objects import (
    BodyId, SynapseCount, NeuronTypeName, SomaSide,
    RoiName, SynapseStatistics
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

    def remove_neuron(self, body_id: BodyId) -> bool:
        """Remove a neuron by body ID. Returns True if removed."""
        for i, neuron in enumerate(self.neurons):
            if neuron.body_id == body_id:
                self.neurons.pop(i)
                return True
        return False

    def get_neuron_by_body_id(self, body_id: BodyId) -> Optional[Neuron]:
        """Find a neuron by its body ID."""
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

    def calculate_statistics(self) -> 'NeuronTypeStatistics':
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

    def get_unique_rois(self) -> List[RoiName]:
        """Get all unique ROIs present in the neurons."""
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


@dataclass(frozen=True)
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
class ConnectivityPartner:
    """Represents a connectivity partner (upstream or downstream)."""
    partner_type: NeuronTypeName
    synapse_count: SynapseCount
    connection_strength: float = 0.0

    def __post_init__(self):
        if self.connection_strength < 0.0 or self.connection_strength > 1.0:
            raise ValueError("Connection strength must be between 0.0 and 1.0")


@dataclass
class NeuronTypeConnectivity:
    """
    Entity representing connectivity information for a neuron type.

    This aggregates connectivity data and provides methods to analyze
    the synaptic connections of a neuron type.
    """
    type_name: NeuronTypeName
    upstream_partners: List[ConnectivityPartner] = field(default_factory=list)
    downstream_partners: List[ConnectivityPartner] = field(default_factory=list)
    analysis_notes: str = ""

    def add_upstream_partner(self, partner: ConnectivityPartner) -> None:
        """Add an upstream connectivity partner."""
        # Remove existing partner with same type if exists
        self.upstream_partners = [
            p for p in self.upstream_partners
            if p.partner_type != partner.partner_type
        ]
        self.upstream_partners.append(partner)

    def add_downstream_partner(self, partner: ConnectivityPartner) -> None:
        """Add a downstream connectivity partner."""
        # Remove existing partner with same type if exists
        self.downstream_partners = [
            p for p in self.downstream_partners
            if p.partner_type != partner.partner_type
        ]
        self.downstream_partners.append(partner)

    def get_top_upstream_partners(self, limit: int = 10) -> List[ConnectivityPartner]:
        """Get top upstream partners by synapse count."""
        return sorted(
            self.upstream_partners,
            key=lambda p: p.synapse_count.value,
            reverse=True
        )[:limit]

    def get_top_downstream_partners(self, limit: int = 10) -> List[ConnectivityPartner]:
        """Get top downstream partners by synapse count."""
        return sorted(
            self.downstream_partners,
            key=lambda p: p.synapse_count.value,
            reverse=True
        )[:limit]

    def total_upstream_synapses(self) -> SynapseCount:
        """Total synapses from upstream partners."""
        total = sum(partner.synapse_count.value for partner in self.upstream_partners)
        return SynapseCount(total)

    def total_downstream_synapses(self) -> SynapseCount:
        """Total synapses to downstream partners."""
        total = sum(partner.synapse_count.value for partner in self.downstream_partners)
        return SynapseCount(total)


# Export all entities
__all__ = [
    'Neuron',
    'NeuronCollection',
    'NeuronTypeStatistics',
    'ConnectivityPartner',
    'NeuronTypeConnectivity'
]
