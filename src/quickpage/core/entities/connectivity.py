"""
Connectivity entities for the QuickPage domain.

This module contains entities related to synaptic connectivity between
neuron types, including connectivity partners and aggregate connectivity data.
"""

from dataclasses import dataclass, field
from typing import List
from ..value_objects import NeuronTypeName, SynapseCount


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
