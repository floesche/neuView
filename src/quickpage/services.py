"""
Simplified services for QuickPage application layer.

This module consolidates the application services into manageable classes
that orchestrate business logic without excessive abstraction.
"""

import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
import logging

from .models import (
    NeuronTypeName, SomaSide, NeuronCollection,
    NeuronTypeStatistics, NeuronTypeConnectivity
)
from .result import Result, Ok, Err

logger = logging.getLogger(__name__)


@dataclass
class GeneratePageCommand:
    """Command to generate an HTML page for a neuron type."""
    neuron_type: NeuronTypeName
    soma_side: SomaSide = SomaSide.ALL
    output_directory: Optional[str] = None
    include_connectivity: bool = True
    include_3d_view: bool = False
    min_synapse_count: int = 0
    image_format: str = 'svg'
    embed_images: bool = False
    requested_at: Optional[datetime] = None

    def __post_init__(self):
        if self.requested_at is None:
            self.requested_at = datetime.now()

        # Ensure neuron_type is a NeuronTypeName instance
        if not isinstance(self.neuron_type, NeuronTypeName):
            self.neuron_type = NeuronTypeName(str(self.neuron_type))

        # Ensure soma_side is a SomaSide instance
        if not isinstance(self.soma_side, SomaSide):
            self.soma_side = SomaSide.from_string(str(self.soma_side))


@dataclass
class ListNeuronTypesCommand:
    """Command to list available neuron types."""
    max_results: int = 10
    all_results: bool = False
    sorted_results: bool = False
    show_soma_sides: bool = False
    show_statistics: bool = False
    filter_pattern: Optional[str] = None
    exclude_empty: bool = True


@dataclass
class InspectNeuronTypeCommand:
    """Command to inspect detailed neuron type information."""
    neuron_type: NeuronTypeName
    soma_side: SomaSide = SomaSide.BOTH
    min_synapse_count: int = 0
    include_connectivity: bool = True

    def __post_init__(self):
        if not isinstance(self.neuron_type, NeuronTypeName):
            self.neuron_type = NeuronTypeName(str(self.neuron_type))
        if not isinstance(self.soma_side, SomaSide):
            self.soma_side = SomaSide.from_string(str(self.soma_side))


@dataclass
class TestConnectionCommand:
    """Command to test NeuPrint connection."""
    detailed: bool = False
    timeout: int = 30


@dataclass
class NeuronTypeInfo:
    """Information about a neuron type."""
    name: str
    count: int = 0
    soma_sides: Optional[Dict[str, int]] = None
    avg_synapses: float = 0.0

    def __post_init__(self):
        if self.soma_sides is None:
            self.soma_sides = {}


@dataclass
class DatasetInfo:
    """Information about the dataset."""
    name: str
    version: str = "Unknown"
    server_url: str = "Unknown"
    connection_status: str = "Unknown"


class PageGenerationService:
    """Service for generating HTML pages."""

    def __init__(self, neuprint_connector, page_generator):
        self.connector = neuprint_connector
        self.generator = page_generator

    async def generate_page(self, command: GeneratePageCommand) -> Result[str, str]:
        """Generate an HTML page for a neuron type."""
        try:
            # Import the legacy NeuronType class
            from .neuron_type import NeuronType
            from .config import NeuronTypeConfig

            # Create NeuronType instance
            config = NeuronTypeConfig(
                name=command.neuron_type.value,
                description=f"{command.neuron_type.value} neurons"
            )

            # Handle auto-detection for SomaSide.ALL
            if command.soma_side == SomaSide.ALL:
                return await self._generate_pages_with_auto_detection(command, config)

            # Convert SomaSide enum to legacy format for specific sides
            if command.soma_side == SomaSide.BOTH:
                legacy_soma_side = 'both'
            elif command.soma_side == SomaSide.LEFT:
                legacy_soma_side = 'left'
            elif command.soma_side == SomaSide.RIGHT:
                legacy_soma_side = 'right'
            else:
                legacy_soma_side = 'both'

            neuron_type_obj = NeuronType(
                command.neuron_type.value,
                config,
                self.connector,
                soma_side=legacy_soma_side
            )

            # Check if we have data
            if not neuron_type_obj.has_data():
                return Err(f"No neurons found for type {command.neuron_type}")

            # Generate the page using legacy generator (pass connector for primary ROI fetching)
            output_file = self.generator.generate_page_from_neuron_type(
                neuron_type_obj,
                self.connector,
                image_format=command.image_format,
                embed_images=command.embed_images
            )
            return Ok(output_file)

        except Exception as e:
            return Err(f"Failed to generate page: {str(e)}")

    async def _generate_pages_with_auto_detection(self, command: GeneratePageCommand, config) -> Result[str, str]:
        """Generate multiple pages based on available soma sides."""
        try:
            from .neuron_type import NeuronType

            # First, check what data is available with 'both'
            neuron_type_obj = NeuronType(
                command.neuron_type.value,
                config,
                self.connector,
                soma_side='both'
            )

            if not neuron_type_obj.has_data():
                return Err(f"No neurons found for type {command.neuron_type}")

            # Check available soma sides
            left_count = neuron_type_obj.get_neuron_count('left')
            right_count = neuron_type_obj.get_neuron_count('right')
            total_count = neuron_type_obj.get_neuron_count()

            generated_files = []

            # Count how many sides have data
            sides_with_data = 0
            if left_count > 0:
                sides_with_data += 1
            if right_count > 0:
                sides_with_data += 1

            # Only generate general page if multiple sides have data
            if sides_with_data > 1:
                general_output = self.generator.generate_page_from_neuron_type(
                    neuron_type_obj,
                    self.connector,
                    image_format=command.image_format,
                    embed_images=command.embed_images
                )
                generated_files.append(general_output)

            # Generate left-specific page if there are left-side neurons
            if left_count > 0:
                left_neuron_type = NeuronType(
                    command.neuron_type.value,
                    config,
                    self.connector,
                    soma_side='left'
                )
                left_output = self.generator.generate_page_from_neuron_type(
                    left_neuron_type,
                    self.connector,
                    image_format=command.image_format,
                    embed_images=command.embed_images
                )
                generated_files.append(left_output)

            # Generate right-specific page if there are right-side neurons
            if right_count > 0:
                right_neuron_type = NeuronType(
                    command.neuron_type.value,
                    config,
                    self.connector,
                    soma_side='right'
                )
                right_output = self.generator.generate_page_from_neuron_type(
                    right_neuron_type,
                    self.connector,
                    image_format=command.image_format,
                    embed_images=command.embed_images
                )
                generated_files.append(right_output)

            # Return summary of all generated files
            files_summary = ", ".join(generated_files)
            return Ok(files_summary)

        except Exception as e:
            return Err(f"Failed to generate pages with auto-detection: {str(e)}")


class NeuronDiscoveryService:
    """Service for discovering available neuron types."""

    def __init__(self, neuprint_connector, config):
        self.connector = neuprint_connector
        self.config = config

    async def list_neuron_types(self, command: ListNeuronTypesCommand) -> Result[List[NeuronTypeInfo], str]:
        """List available neuron types."""
        try:
            # Use the discovery configuration from config, but override max_types if --all is specified
            discovery_config = self.config.discovery
            if command.all_results:
                from dataclasses import replace
                discovery_config = replace(discovery_config, max_types=999999)

            discovered_types = self.connector.discover_neuron_types(discovery_config)
            # Convert to NeuronTypeInfo objects
            type_infos = []
            for type_name in discovered_types:
                info = NeuronTypeInfo(name=type_name)

                # If statistics are requested, get them (but don't fail if we can't)
                if command.show_statistics:
                    try:
                        # Try to get basic neuron count using the legacy method
                        from .neuron_type import NeuronType
                        from .config import NeuronTypeConfig

                        config = NeuronTypeConfig(name=type_name, description=f"{type_name} neurons")
                        neuron_type_obj = NeuronType(type_name, config, self.connector, soma_side='both')

                        if neuron_type_obj.has_data():
                            info.count = neuron_type_obj.get_neuron_count()
                            synapse_stats = neuron_type_obj.get_synapse_stats()
                            info.avg_synapses = synapse_stats.get('avg_pre', 0.0) + synapse_stats.get('avg_post', 0.0)
                    except Exception:
                        # If we can't get stats, skip this type when show_statistics is requested
                        continue

                # If soma sides are requested, get them
                if command.show_soma_sides:
                    try:
                        soma_data = self.connector.get_soma_side_distribution(type_name)
                        if soma_data:
                            info.soma_sides = soma_data
                    except Exception:
                        pass  # Skip if we can't get soma data

                type_infos.append(info)

            # Filter by pattern if specified
            if command.filter_pattern:
                import re
                pattern = re.compile(command.filter_pattern, re.IGNORECASE)
                type_infos = [info for info in type_infos if pattern.search(info.name)]

            # Exclude empty types if requested (only if we have count data)
            if command.exclude_empty and command.show_statistics:
                type_infos = [info for info in type_infos if info.count > 0]

            # Sort if requested
            if command.sorted_results:
                type_infos.sort(key=lambda x: x.name)

            # Limit results (unless --all is specified)
            if not command.all_results and command.max_results > 0:
                type_infos = type_infos[:command.max_results]
            return Ok(type_infos)

        except Exception as e:
            return Err(f"Failed to list neuron types: {str(e)}")

    async def inspect_neuron_type(self, command: InspectNeuronTypeCommand) -> Result[NeuronTypeStatistics, str]:
        """Inspect detailed information about a neuron type."""
        try:
            # Import legacy components
            from .neuron_type import NeuronType
            from .config import NeuronTypeConfig

            # Create NeuronType instance
            config = NeuronTypeConfig(
                name=command.neuron_type.value,
                description=f"{command.neuron_type.value} neurons"
            )

            # Convert SomaSide enum to legacy format
            if command.soma_side in [SomaSide.ALL, SomaSide.BOTH]:
                legacy_soma_side = 'both'
            elif command.soma_side == SomaSide.LEFT:
                legacy_soma_side = 'left'
            elif command.soma_side == SomaSide.RIGHT:
                legacy_soma_side = 'right'
            else:
                legacy_soma_side = 'both'

            neuron_type_obj = NeuronType(
                command.neuron_type.value,
                config,
                self.connector,
                soma_side=legacy_soma_side
            )

            # Check if we have data
            if not neuron_type_obj.has_data():
                return Err(f"No neurons found for type {command.neuron_type}")

            # Gather statistics
            neuron_count = neuron_type_obj.get_neuron_count()
            soma_counts = {
                "left": neuron_type_obj.get_neuron_count('left'),
                "right": neuron_type_obj.get_neuron_count('right'),
                "middle": 0  # Legacy NeuronType doesn't support middle
            }
            synapse_stats = neuron_type_obj.get_synapse_stats()

            # Create statistics object
            stats = NeuronTypeStatistics(
                type_name=command.neuron_type,
                total_count=neuron_count,
                soma_side_counts=soma_counts,
                synapse_stats=synapse_stats
            )

            return Ok(stats)

        except Exception as e:
            return Err(f"Failed to inspect neuron type: {str(e)}")


class ConnectionTestService:
    """Service for testing NeuPrint connection."""

    def __init__(self, neuprint_connector):
        self.connector = neuprint_connector

    async def test_connection(self, command: TestConnectionCommand) -> Result[DatasetInfo, str]:
        """Test connection to NeuPrint server."""
        try:
            info = self.connector.test_connection()

            dataset_info = DatasetInfo(
                name=info.get('dataset', 'Unknown'),
                version=info.get('version', 'Unknown'),
                server_url=info.get('server', 'Unknown'),
                connection_status='Connected'
            )

            return Ok(dataset_info)

        except Exception as e:
            return Err(f"Connection test failed: {str(e)}")


class ServiceContainer:
    """Simple service container for dependency management."""

    def __init__(self, config):
        self.config = config
        self._neuprint_connector = None
        self._page_generator = None
        self._page_service = None
        self._discovery_service = None
        self._connection_service = None

    @property
    def neuprint_connector(self):
        """Get or create NeuPrint connector."""
        if self._neuprint_connector is None:
            from .neuprint_connector import NeuPrintConnector
            self._neuprint_connector = NeuPrintConnector(self.config)
        return self._neuprint_connector

    @property
    def page_generator(self):
        """Get or create page generator."""
        if self._page_generator is None:
            from .page_generator import PageGenerator
            self._page_generator = PageGenerator(
                self.config,
                self.config.output.directory
            )
        return self._page_generator

    @property
    def page_service(self) -> PageGenerationService:
        """Get or create page generation service."""
        if self._page_service is None:
            self._page_service = PageGenerationService(
                self.neuprint_connector,
                self.page_generator
            )
        return self._page_service

    @property
    def discovery_service(self) -> NeuronDiscoveryService:
        """Get or create neuron discovery service."""
        if self._discovery_service is None:
            self._discovery_service = NeuronDiscoveryService(
                self.neuprint_connector,
                self.config
            )
        return self._discovery_service

    @property
    def connection_service(self) -> ConnectionTestService:
        """Get or create connection test service."""
        if self._connection_service is None:
            self._connection_service = ConnectionTestService(
                self.neuprint_connector
            )
        return self._connection_service
