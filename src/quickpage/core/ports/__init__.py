"""
Domain ports (interfaces) for QuickPage.

Ports define the contracts that the domain layer expects from external systems.
They are implemented by adapters in the infrastructure layer.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..entities import Neuron, NeuronCollection, NeuronTypeConnectivity
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


class CacheRepository(ABC):
    """
    Repository interface for caching data.

    This port defines how the domain layer expects to interact with
    caching systems for performance optimization.
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a cached value by key.

        Args:
            key: The cache key

        Returns:
            Cached value if found, None otherwise
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a cached value.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Time to live in seconds (optional)
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a cached value.

        Args:
            key: The cache key

        Returns:
            True if the key was deleted, False if it didn't exist
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached values."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            key: The cache key

        Returns:
            True if the key exists, False otherwise
        """
        pass


class TemplateEngine(ABC):
    """
    Port for HTML template rendering.

    This port defines how the domain layer expects templates to be
    processed for generating HTML output.
    """

    @abstractmethod
    async def render_template(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Render a template with the given context.

        Args:
            template_name: Name of the template to render
            context: Template context variables

        Returns:
            Rendered HTML content
        """
        pass

    @abstractmethod
    def list_templates(self) -> List[str]:
        """
        List available templates.

        Returns:
            List of template names
        """
        pass


class FileStorage(ABC):
    """
    Port for file storage operations.

    This port defines how the domain layer expects to interact with
    the file system for saving generated content.
    """

    @abstractmethod
    async def save_file(self, path: str, content: str) -> None:
        """
        Save content to a file.

        Args:
            path: File path to save to
            content: Content to save
        """
        pass

    @abstractmethod
    async def read_file(self, path: str) -> str:
        """
        Read content from a file.

        Args:
            path: File path to read from

        Returns:
            File content
        """
        pass

    @abstractmethod
    async def file_exists(self, path: str) -> bool:
        """
        Check if a file exists.

        Args:
            path: File path to check

        Returns:
            True if file exists, False otherwise
        """
        pass

    @abstractmethod
    async def create_directory(self, path: str) -> None:
        """
        Create a directory.

        Args:
            path: Directory path to create
        """
        pass

    @abstractmethod
    async def list_files(self, directory: str) -> List[str]:
        """
        List files in a directory.

        Args:
            directory: Directory path to list

        Returns:
            List of file names in the directory
        """
        pass


# Export all ports
__all__ = [
    'NeuronRepository',
    'ConnectivityRepository',
    'CacheRepository',
    'TemplateEngine',
    'FileStorage'
]
