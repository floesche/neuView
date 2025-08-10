"""
Connectivity query classes for the application layer.

These queries handle operations related to retrieving synaptic
connectivity information for neuron types and individual neurons.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from ...core.value_objects import NeuronTypeName
from ...core.entities import NeuronTypeConnectivity


@dataclass(frozen=True)
class GetConnectivityQuery:
    """
    Query to retrieve connectivity information for a neuron type.

    This query fetches synaptic connectivity data including
    upstream and downstream partners.
    """
    neuron_type: NeuronTypeName
    include_partner_details: bool = True
    max_partners: int = 50
    min_synapse_threshold: int = 1
    requested_at: Optional[datetime] = None

    def __post_init__(self):
        if self.requested_at is None:
            object.__setattr__(self, 'requested_at', datetime.now())

    def validate(self) -> list[str]:
        """
        Validate the query parameters.

        Returns:
            List of validation errors, empty if valid
        """
        errors = []

        if not str(self.neuron_type).strip():
            errors.append("Neuron type cannot be empty")

        if self.max_partners <= 0:
            errors.append("Max partners must be positive")

        if self.min_synapse_threshold < 0:
            errors.append("Minimum synapse threshold cannot be negative")

        return errors

    def is_valid(self) -> bool:
        """Check if the query is valid."""
        return len(self.validate()) == 0


@dataclass(frozen=True)
class GetConnectivityQueryResult:
    """Result of a GetConnectivityQuery."""
    connectivity: NeuronTypeConnectivity
    query_executed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.query_executed_at is None:
            object.__setattr__(self, 'query_executed_at', datetime.now())
