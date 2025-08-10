"""
Neuron repository port for the core domain layer.

This port defines the contract that the domain layer expects from
external neuron data sources (like NeuPrint).
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from ..entities import Neuron, NeuronCollection
from ..value_objects import NeuronTypeName, SomaSide, BodyId


class NeuronRepository(ABC):
    """
    Repository interface for neuron data access.

    This port defines how the domain layer expects to interact with
    neuron data sources (like NeuPrint).
    """

    @abstractmethod
    async def find_by_type(self, neuron_type: NeuronTypeName) -> NeuronCollection:
        """
        Find all neurons of a specific type.

        Args:
            neuron_type: The type of neurons to find

        Returns:
            Collection of neurons of the specified type
        """
        pass

    @abstractmethod
    async def find_by_type_and_side(
        self,
        neuron_type: NeuronTypeName,
        soma_side: SomaSide
    ) -> NeuronCollection:
        """
        Find neurons of a specific type and soma side.

        Args:
            neuron_type: The type of neurons to find
            soma_side: The soma side to filter by

        Returns:
            Collection of neurons matching the criteria
        """
        pass

    @abstractmethod
    async def find_by_body_id(self, body_id: BodyId) -> Optional[Neuron]:
        """
        Find a neuron by its body ID.

        Args:
            body_id: The unique body identifier

        Returns:
            Neuron if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_available_types(self) -> List[NeuronTypeName]:
        """
        Get all available neuron types in the dataset.

        Returns:
            List of neuron type names available in the dataset
        """
        pass

    @abstractmethod
    async def get_types_with_soma_sides(self) -> Dict[NeuronTypeName, List[str]]:
        """
        Get neuron types with their available soma sides.

        Returns:
            Dictionary mapping neuron types to their available soma sides
        """
        pass

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to the data source.

        Returns:
            Connection information and status
        """
        pass
