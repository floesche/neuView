"""
Connectivity repository port for the core domain layer.

This port defines the contract that the domain layer expects from
external synaptic connectivity data sources.
"""

from abc import ABC, abstractmethod
from typing import Optional

from ..entities import NeuronTypeConnectivity
from ..value_objects import NeuronTypeName


class ConnectivityRepository(ABC):
    """
    Repository interface for connectivity data access.

    This port defines how the domain layer expects to interact with
    synaptic connectivity data.
    """

    @abstractmethod
    async def get_connectivity_for_type(
        self,
        neuron_type: NeuronTypeName
    ) -> NeuronTypeConnectivity:
        """
        Get connectivity information for a neuron type.

        Args:
            neuron_type: The type to get connectivity for

        Returns:
            Connectivity information including upstream and downstream partners
        """
        pass

    @abstractmethod
    async def get_connectivity_between_types(
        self,
        source_type: NeuronTypeName,
        target_type: NeuronTypeName
    ) -> Optional[int]:
        """
        Get synapse count between two neuron types.

        Args:
            source_type: The source neuron type
            target_type: The target neuron type

        Returns:
            Number of synapses between the types, None if no connection
        """
        pass
