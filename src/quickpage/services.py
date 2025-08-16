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
import yaml

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
class FillQueueCommand:
    """Command to create a queue YAML file with generate options."""
    neuron_type: Optional[NeuronTypeName] = None
    soma_side: SomaSide = SomaSide.ALL
    output_directory: Optional[str] = None
    include_connectivity: bool = True
    include_3d_view: bool = False
    min_synapse_count: int = 0
    image_format: str = 'svg'
    embed_images: bool = False
    all_types: bool = False
    max_types: int = 10
    config_file: Optional[str] = None
    requested_at: Optional[datetime] = None

    def __post_init__(self):
        if self.requested_at is None:
            self.requested_at = datetime.now()

        # Ensure neuron_type is a NeuronTypeName instance if provided
        if self.neuron_type is not None and not isinstance(self.neuron_type, NeuronTypeName):
            self.neuron_type = NeuronTypeName(str(self.neuron_type))

        # Ensure soma_side is a SomaSide instance
        if not isinstance(self.soma_side, SomaSide):
            self.soma_side = SomaSide.from_string(str(self.soma_side))


@dataclass
class PopCommand:
    """Command to pop and process a queue file."""
    output_directory: Optional[str] = None
    requested_at: Optional[datetime] = None

    def __post_init__(self):
        if self.requested_at is None:
            self.requested_at = datetime.now()


@dataclass
class CreateIndexCommand:
    """Command to create an index page listing all neuron types."""
    output_directory: Optional[str] = None
    index_filename: str = "index.html"
    include_roi_analysis: bool = True  # Default: include ROI analysis for comprehensive data (use --quick to disable)
    requested_at: Optional[datetime] = None

    def __post_init__(self):
        if self.requested_at is None:
            self.requested_at = datetime.now()


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

    def __init__(self, neuprint_connector, page_generator, config=None):
        self.connector = neuprint_connector
        self.generator = page_generator
        self.config = config

        # Initialize cache manager if config is available
        self.cache_manager = None
        if config and hasattr(config, 'output') and hasattr(config.output, 'directory'):
            from .cache import create_cache_manager
            self.cache_manager = create_cache_manager(config.output.directory)

    async def generate_page(self, command: GeneratePageCommand) -> Result[str, str]:
        """Generate an HTML page for a neuron type with optimized data sharing."""
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

            # Pre-fetch raw neuron data for single page generation (enables caching for future calls)
            neuron_type_name = command.neuron_type.value
            try:
                self.connector._get_or_fetch_raw_neuron_data(neuron_type_name)
            except Exception as e:
                return Err(f"Failed to fetch neuron data for {neuron_type_name}: {str(e)}")

            # Convert SomaSide enum to legacy format for specific sides
            if command.soma_side == SomaSide.BOTH:
                legacy_soma_side = 'both'
            elif command.soma_side == SomaSide.LEFT:
                legacy_soma_side = 'left'
            elif command.soma_side == SomaSide.RIGHT:
                legacy_soma_side = 'right'
            elif command.soma_side == SomaSide.MIDDLE:
                legacy_soma_side = 'middle'
            else:
                legacy_soma_side = 'both'

            neuron_type_obj = NeuronType(
                neuron_type_name,
                config,
                self.connector,
                soma_side=legacy_soma_side
            )

            # Check if we have data
            if not neuron_type_obj.has_data():
                # Clear cache on failure to avoid stale data
                self.connector.clear_neuron_data_cache(neuron_type_name)
                return Err(f"No neurons found for type {command.neuron_type}")

            try:
                # Generate the page using legacy generator (pass connector for primary ROI fetching)
                output_file = self.generator.generate_page_from_neuron_type(
                    neuron_type_obj,
                    self.connector,
                    image_format=command.image_format,
                    embed_images=command.embed_images
                )

                # Save to persistent cache for index generation
                await self._save_neuron_type_to_cache(neuron_type_name, neuron_type_obj, command)

                # Log cache performance for single pages too
                if command.soma_side != SomaSide.ALL:
                    self.connector.log_cache_performance()
                    self.connector.clear_neuron_data_cache(neuron_type_name)

                return Ok(output_file)
            except Exception as e:
                # Clear cache on error to avoid stale data
                self.connector.clear_neuron_data_cache(neuron_type_name)
                raise e

        except Exception as e:
            return Err(f"Failed to generate page: {str(e)}")

    async def _save_neuron_type_to_cache(self, neuron_type_name: str, neuron_type_obj, command: GeneratePageCommand):
        """Save neuron type data to persistent cache for later index generation."""
        if not self.cache_manager:
            return  # No cache manager available

        try:
            from .cache import NeuronTypeCacheData

            # Get neuron data from the neuron type object
            neurons_df = getattr(neuron_type_obj, 'neurons', None)

            # Create cache data from legacy neuron type object
            legacy_data = {
                'neurons': neurons_df,
            }

            # Extract ROI summary if available (simplified for now)
            roi_summary = []
            parent_roi = ""

            cache_data = NeuronTypeCacheData.from_legacy_data(
                neuron_type=neuron_type_name,
                legacy_data=legacy_data,
                roi_summary=roi_summary,
                parent_roi=parent_roi,
                has_connectivity=command.include_connectivity
            )

            # Save to cache
            success = self.cache_manager.save_neuron_type_cache(cache_data)
            if success:
                logger.debug(f"Saved cache data for neuron type {neuron_type_name}")
            else:
                logger.warning(f"Failed to save cache data for neuron type {neuron_type_name}")

        except Exception as e:
            logger.warning(f"Error saving cache for {neuron_type_name}: {e}")

    async def _generate_pages_with_auto_detection(self, command: GeneratePageCommand, config) -> Result[str, str]:
        """Generate multiple pages based on available soma sides with shared data optimization."""
        try:
            from .neuron_type import NeuronType

            # Pre-fetch raw neuron data to be shared across all soma sides
            neuron_type_name = command.neuron_type.value
            try:
                # This will cache the raw data in the connector
                self.connector._get_or_fetch_raw_neuron_data(neuron_type_name)
            except Exception as e:
                return Err(f"Failed to fetch neuron data for {neuron_type_name}: {str(e)}")

            # First, check what data is available with 'both'
            neuron_type_obj = NeuronType(
                neuron_type_name,
                config,
                self.connector,
                soma_side='both'
            )

            if not neuron_type_obj.has_data():
                # Clear cache on failure to avoid stale data
                self.connector.clear_neuron_data_cache(neuron_type_name)
                return Err(f"No neurons found for type {command.neuron_type}")

            # Check available soma sides
            left_count = neuron_type_obj.get_neuron_count('left')
            right_count = neuron_type_obj.get_neuron_count('right')
            middle_count = neuron_type_obj.get_neuron_count('middle')
            total_count = neuron_type_obj.get_neuron_count()

            generated_files = []

            # Count how many sides have data
            sides_with_data = 0
            if left_count > 0:
                sides_with_data += 1
            if right_count > 0:
                sides_with_data += 1
            if middle_count > 0:
                sides_with_data += 1

            try:
                # Generate general page if multiple sides have data OR if no soma side data exists but neurons are present
                if sides_with_data > 1 or (sides_with_data == 0 and total_count > 0):
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
                        neuron_type_name,
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
                        neuron_type_name,
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

                # Generate middle-specific page if there are middle-side neurons
                if middle_count > 0:
                    middle_neuron_type = NeuronType(
                        neuron_type_name,
                        config,
                        self.connector,
                        soma_side='middle'
                    )
                    middle_output = self.generator.generate_page_from_neuron_type(
                        middle_neuron_type,
                        self.connector,
                        image_format=command.image_format,
                        embed_images=command.embed_images
                    )
                    generated_files.append(middle_output)

                # Save to persistent cache for index generation (use 'both' data for comprehensive info)
                await self._save_neuron_type_to_cache(neuron_type_name, neuron_type_obj, command)

                # Log cache performance before clearing
                self.connector.log_cache_performance()

                # Clear cache after successful generation to free memory
                self.connector.clear_neuron_data_cache(neuron_type_name)

                # Return summary of all generated files
                files_summary = ", ".join(generated_files)
                return Ok(files_summary)

            except Exception as e:
                # Clear cache on error to avoid stale data
                self.connector.clear_neuron_data_cache(neuron_type_name)
                raise e

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
            elif command.soma_side == SomaSide.MIDDLE:
                legacy_soma_side = 'middle'
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
                "middle": neuron_type_obj.get_neuron_count('middle')
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


class QueueService:
    """Service for managing queue files."""

    def __init__(self, config):
        self.config = config
        # Load queued neuron types once during initialization
        self._queued_types: List[str] = self._load_queued_neuron_types()

    async def fill_queue(self, command: FillQueueCommand) -> Result[str, str]:
        """Create a YAML queue file with generate command options."""
        try:
            if command.neuron_type is not None:
                # Single neuron type mode
                return await self._create_single_queue_file(command)
            else:
                # Batch mode - discover neuron types
                return await self._create_batch_queue_files(command)

        except Exception as e:
            return Err(f"Failed to create queue file: {str(e)}")

    async def _create_single_queue_file(self, command: FillQueueCommand) -> Result[str, str]:
        """Create a single queue file for a specific neuron type."""
        if command.neuron_type is None:
            return Err("Neuron type is required for single queue file creation")

        # Import PageGenerator to use filename generation logic
        from .page_generator import PageGenerator

        # Create a temporary page generator to get the filename logic
        temp_generator = PageGenerator(self.config, self.config.output.directory, None)

        # Convert soma_side enum to string for filename generation
        soma_side_str = command.soma_side.value
        if command.soma_side == SomaSide.BOTH:
            soma_side_str = 'both'
        elif command.soma_side == SomaSide.ALL:
            soma_side_str = 'all'

        # Generate the HTML filename that would be created
        html_filename = temp_generator._generate_filename(
            command.neuron_type.value,
            soma_side_str
        )

        # Create YAML filename by replacing .html with .yaml
        yaml_filename = html_filename.replace('.html', '.yaml')

        # Create the queue directory if it doesn't exist
        queue_dir = Path(self.config.output.directory) / '.queue'
        queue_dir.mkdir(parents=True, exist_ok=True)

        # Full path to the YAML file
        yaml_path = queue_dir / yaml_filename

        # Prepare the generate command options
        queue_data = {
            'command': 'generate',
            'config_file': command.config_file,
            'options': {
                'neuron-type': command.neuron_type.value,
                'soma-side': command.soma_side.value,
                'output-dir': command.output_directory,
                'image-format': command.image_format,
                'embed': command.embed_images,
                'min-synapses': command.min_synapse_count,
                'no-connectivity': not command.include_connectivity,
                'include-3d-view': command.include_3d_view,
            },
            'created_at': (command.requested_at or datetime.now()).isoformat()
        }

        # Remove None values to keep the YAML clean
        queue_data['options'] = {
            k: v for k, v in queue_data['options'].items()
            if v is not None
        }

        # Remove config_file if None
        if queue_data['config_file'] is None:
            del queue_data['config_file']

        # Write the YAML file
        with open(yaml_path, 'w') as f:
            yaml.dump(queue_data, f, default_flow_style=False, indent=2)

        # Update the central queue.yaml file (only in single mode)
        await self._update_queue_manifest([command.neuron_type.value])

        return Ok(str(yaml_path))

    async def _create_batch_queue_files(self, command: FillQueueCommand) -> Result[str, str]:
        """Create queue files for multiple neuron types."""
        from .neuprint_connector import NeuPrintConnector

        # Create connector for type discovery (optimized)
        connector = NeuPrintConnector(self.config)

        try:
            if command.all_types:
                # Optimized path: directly get all types without discovery service overhead
                type_names = connector.get_available_types()
                types = [NeuronTypeInfo(name=name) for name in type_names]
            else:
                # Use discovery service for filtered results
                discovery_service = NeuronDiscoveryService(connector, self.config)
                max_results = command.max_types

                list_command = ListNeuronTypesCommand(
                    max_results=max_results,
                    exclude_empty=False,  # Skip expensive empty filtering for queue creation
                    all_results=False,
                    show_statistics=False,  # No need for stats when creating queue files
                    sorted_results=False   # No need to sort for queue creation
                )

                list_result = await discovery_service.list_neuron_types(list_command)
                if list_result.is_err():
                    return Err(f"Failed to discover neuron types: {list_result.unwrap_err()}")
                types = list_result.unwrap()

            if not types:
                return Err("No neuron types found")
        except Exception as e:
            return Err(f"Failed to get neuron types: {str(e)}")

        # Create queue files for each type (optimized concurrent batch processing)
        created_files = []

        # Create queue directory once
        queue_dir = Path(self.config.output.directory) / '.queue'
        queue_dir.mkdir(parents=True, exist_ok=True)

        # Create all commands for concurrent processing
        batch_commands = []
        for type_info in types:
            # Create a command for this specific type
            single_command = FillQueueCommand(
                neuron_type=NeuronTypeName(type_info.name),
                soma_side=command.soma_side,
                output_directory=command.output_directory,
                include_connectivity=command.include_connectivity,
                include_3d_view=command.include_3d_view,
                min_synapse_count=command.min_synapse_count,
                image_format=command.image_format,
                embed_images=command.embed_images,
                config_file=command.config_file,
                requested_at=command.requested_at
            )
            batch_commands.append(single_command)

        # Process all commands concurrently with limited concurrency
        semaphore = asyncio.Semaphore(100)  # Limit concurrent file operations

        async def process_single_command(cmd):
            async with semaphore:
                return await self._create_single_queue_file_batch(cmd, queue_dir)

        results = await asyncio.gather(
            *[process_single_command(cmd) for cmd in batch_commands],
            return_exceptions=True
        )

        # Collect successful results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Failed to create queue file for {batch_commands[i].neuron_type}: {result}")
            elif result.is_ok():
                created_files.append(batch_commands[i].neuron_type.value)

        if created_files:
            # Update the central queue.yaml file ONCE at the end
            await self._update_queue_manifest(created_files)
            return Ok(f"Created {len(created_files)} queue files")
        else:
            return Err("Failed to create any queue files")

    async def _create_single_queue_file_batch(self, command: FillQueueCommand, queue_dir: Path) -> Result[str, str]:
        """Create a single queue file for batch processing (no manifest update)."""
        if command.neuron_type is None:
            return Err("Neuron type is required for single queue file creation")

        # Import PageGenerator to use filename generation logic
        from .page_generator import PageGenerator

        # Create a temporary page generator to get the filename logic
        temp_generator = PageGenerator(self.config, self.config.output.directory, None)

        # Convert soma_side enum to string for filename generation
        soma_side_str = command.soma_side.value
        if command.soma_side == SomaSide.BOTH:
            soma_side_str = 'both'
        elif command.soma_side == SomaSide.ALL:
            soma_side_str = 'all'

        # Generate the HTML filename that would be created
        html_filename = temp_generator._generate_filename(
            command.neuron_type.value,
            soma_side_str
        )

        # Create YAML filename by replacing .html with .yaml
        yaml_filename = html_filename.replace('.html', '.yaml')

        # Full path to the YAML file (use pre-created queue_dir)
        yaml_path = queue_dir / yaml_filename

        # Prepare the generate command options
        queue_data = {
            'command': 'generate',
            'config_file': command.config_file,
            'options': {
                'neuron-type': command.neuron_type.value,
                'soma-side': command.soma_side.value,
                'output-dir': command.output_directory,
                'image-format': command.image_format,
                'embed': command.embed_images,
                'min-synapses': command.min_synapse_count,
                'no-connectivity': not command.include_connectivity,
                'include-3d-view': command.include_3d_view,
            },
            'created_at': (command.requested_at or datetime.now()).isoformat()
        }

        # Remove None values to keep the YAML clean
        queue_data['options'] = {
            k: v for k, v in queue_data['options'].items()
            if v is not None
        }

        # Remove config_file if None
        if queue_data['config_file'] is None:
            del queue_data['config_file']

        # Write the YAML file synchronously (no manifest update in batch mode)
        try:
            with open(yaml_path, 'w') as f:
                yaml.dump(queue_data, f, default_flow_style=False, indent=2)
        except Exception as e:
            return Err(f"Failed to write queue file {yaml_path}: {str(e)}")

        return Ok(str(yaml_path))

    async def _update_queue_manifest(self, neuron_types: List[str]):
        """Update the central queue.yaml file with neuron types."""
        queue_dir = Path(self.config.output.directory) / '.queue'
        queue_manifest_path = queue_dir / 'queue.yaml'

        # Load existing manifest or create new one
        if queue_manifest_path.exists():
            with open(queue_manifest_path, 'r') as f:
                manifest_data = yaml.safe_load(f) or {}
        else:
            manifest_data = {}

        # Get existing neuron types or initialize empty list
        existing_types = set(manifest_data.get('neuron_types', []))

        # Add new neuron types (batch update)
        existing_types.update(neuron_types)

        # Update manifest data
        manifest_data.update({
            'neuron_types': sorted(list(existing_types)),
            'updated_at': datetime.now().isoformat(),
            'count': len(existing_types)
        })

        # Create created_at if it doesn't exist
        if 'created_at' not in manifest_data:
            manifest_data['created_at'] = datetime.now().isoformat()

        # Write updated manifest
        with open(queue_manifest_path, 'w') as f:
            yaml.dump(manifest_data, f, default_flow_style=False, indent=2)

        # Reload queued types since we just updated the manifest
        self._queued_types = self._load_queued_neuron_types()

    def _load_queued_neuron_types(self) -> List[str]:
        """Load queued neuron types from the queue manifest file."""
        queue_dir = Path(self.config.output.directory) / '.queue'
        queue_manifest_path = queue_dir / 'queue.yaml'

        if not queue_manifest_path.exists():
            logger.debug("Queue manifest file does not exist")
            return []

        try:
            logger.debug(f"Loading queued types from {queue_manifest_path}")
            with open(queue_manifest_path, 'r') as f:
                manifest_data = yaml.safe_load(f) or {}

            neuron_types = manifest_data.get('neuron_types', [])
            logger.debug(f"Loaded {len(neuron_types)} queued neuron types")
            return neuron_types

        except Exception as e:
            logger.warning(f"Failed to load queued types: {e}")
            return []

    def get_queued_neuron_types(self) -> List[str]:
        """Get list of neuron types in the queue manifest."""
        return self._queued_types

    async def pop_queue(self, command: PopCommand) -> Result[str, str]:
        """Pop and process a queue file."""
        try:
            # Get the queue directory
            queue_dir = Path(self.config.output.directory) / '.queue'

            # Check if queue directory exists
            if not queue_dir.exists():
                return Err("Queue directory does not exist")

            # Try to claim a file - keep trying until we succeed or run out of files
            while True:
                # Find all .yaml files in queue directory (refresh the list each time)
                # Exclude queue.yaml as it's a summary file, not a processable queue file
                yaml_files = [f for f in queue_dir.glob('*.yaml') if f.name != 'queue.yaml']

                if not yaml_files:
                    return Ok("No queue files to process")

                # Try to claim the first yaml file
                yaml_file = yaml_files[0]
                lock_file = yaml_file.with_suffix('.lock')

                try:
                    # Attempt to rename to .lock to claim it
                    yaml_file.rename(lock_file)
                    # Success! We claimed this file, break out of the loop
                    break
                except FileNotFoundError:
                    # File was deleted/renamed by another process, try next file
                    continue

            try:
                # Read the YAML content
                with open(lock_file, 'r') as f:
                    queue_data = yaml.safe_load(f)

                if not queue_data or 'options' not in queue_data:
                    raise ValueError("Invalid queue file format")

                options = queue_data['options']
                stored_config_file = queue_data.get('config_file')

                # Convert YAML options back to GeneratePageCommand
                generate_command = GeneratePageCommand(
                    neuron_type=NeuronTypeName(options['neuron-type']),
                    soma_side=SomaSide.from_string(options['soma-side']),
                    output_directory=command.output_directory or options.get('output-dir'),
                    include_connectivity=not options.get('no-connectivity', False),
                    min_synapse_count=options.get('min-synapses', 0),
                    image_format=options.get('image-format', 'svg'),
                    embed_images=options.get('embed', True),
                    include_3d_view=options.get('include-3d-view', False)
                )

                # Get page service from container (we need access to it)
                from .page_generator import PageGenerator
                from .neuprint_connector import NeuPrintConnector
                from .config import Config

                # Use the stored config file if available, otherwise use current config
                if stored_config_file:
                    config = Config.load(stored_config_file)
                else:
                    config = self.config

                # Create services with the appropriate config
                connector = NeuPrintConnector(config)

                # Create queue service to check for queued neuron types
                queue_service = QueueService(config)
                generator = PageGenerator(config, config.output.directory, queue_service)
                page_service = PageGenerationService(connector, generator)

                # Generate the page
                result = await page_service.generate_page(generate_command)

                if result.is_ok():
                    # Success - delete the lock file
                    lock_file.unlink()
                    return Ok(f"Generated {result.unwrap()} from queue file {yaml_file.name}")
                else:
                    # Failure - rename back to .yaml
                    lock_file.rename(yaml_file)
                    return Err(f"Generation failed: {result.unwrap_err()}")

            except Exception as e:
                # Any error during processing - rename back to .yaml
                if lock_file.exists():
                    lock_file.rename(yaml_file)
                raise e

        except Exception as e:
            return Err(f"Failed to pop queue: {str(e)}")


class IndexService:
    """Service for creating index pages that list all available neuron types."""

    def __init__(self, config, page_generator):
        self.config = config
        self.page_generator = page_generator
        self._roi_hierarchy_cache = None
        self._roi_parent_cache = {}
        self._batch_neuron_cache = {}
        self._persistent_roi_cache_path = None  # Will be set dynamically based on output directory

        # Initialize cache manager for neuron type data
        self.cache_manager = None
        if config and hasattr(config, 'output') and hasattr(config.output, 'directory'):
            from .cache import create_cache_manager
            self.cache_manager = create_cache_manager(config.output.directory)

    def _clean_roi_name(self, roi_name: str) -> str:
        """Remove (R) and (L) suffixes from ROI names."""
        import re
        # Remove (R), (L), or (M) suffixes from ROI names
        cleaned = re.sub(r'\s*\([RLM]\)$', '', roi_name)
        return cleaned.strip()

    def _find_roi_parent_recursive(self, target_roi: str, current_dict: dict, parent_name: str = "") -> str:
        """Recursively search for ROI in hierarchy and return its parent."""
        for key, value in current_dict.items():
            cleaned_key = self._clean_roi_name(key.rstrip('*'))  # Remove stars too

            # If we found our target ROI, return the parent
            if cleaned_key == target_roi:
                return parent_name

            # If this is a dictionary, search recursively
            if isinstance(value, dict):
                result = self._find_roi_parent_recursive(target_roi, value, cleaned_key)
                if result:
                    return result

        return ""

    def _get_roi_hierarchy_cached(self, connector, output_dir=None):
        """Get ROI hierarchy with persistent caching to avoid repeated expensive fetches."""
        if self._roi_hierarchy_cache is None:
            # Set cache path based on output directory
            if output_dir and not self._persistent_roi_cache_path:
                cache_dir = Path(output_dir) / ".cache"
                cache_dir.mkdir(exist_ok=True)
                self._persistent_roi_cache_path = cache_dir / "roi_hierarchy.json"
            elif not self._persistent_roi_cache_path:
                # Fallback to default output directory
                cache_dir = Path(self.config.output.directory) / ".cache"
                cache_dir.mkdir(exist_ok=True)
                self._persistent_roi_cache_path = cache_dir / "roi_hierarchy.json"

            # Try to load from persistent cache first
            self._roi_hierarchy_cache = self._load_persistent_roi_cache()

            if not self._roi_hierarchy_cache:
                # Cache miss - fetch from database
                try:
                    from neuprint.queries import fetch_roi_hierarchy
                    import neuprint

                    original_client = neuprint.default_client
                    neuprint.default_client = connector.client
                    self._roi_hierarchy_cache = fetch_roi_hierarchy()
                    neuprint.default_client = original_client

                    # Save to persistent cache
                    self._save_persistent_roi_cache(self._roi_hierarchy_cache)

                except Exception:
                    self._roi_hierarchy_cache = {}

        return self._roi_hierarchy_cache

    def _get_roi_hierarchy_parent(self, roi_name: str, connector) -> str:
        """Get the parent ROI of the given ROI from the hierarchy."""
        # Check cache first
        if roi_name in self._roi_parent_cache:
            return self._roi_parent_cache[roi_name]

        try:
            hierarchy = self._get_roi_hierarchy_cached(connector)
            if not hierarchy:
                self._roi_parent_cache[roi_name] = ""
                return ""

            # Clean the ROI name first (remove (R), (L), (M) suffixes)
            cleaned_roi = self._clean_roi_name(roi_name)

            # Search recursively for the ROI and its parent
            parent = self._find_roi_parent_recursive(cleaned_roi, hierarchy)
            result = parent if parent else ""

            # Cache the result
            self._roi_parent_cache[roi_name] = result
            return result
        except Exception:
            # If any error occurs, cache empty result and return
            self._roi_parent_cache[roi_name] = ""
            return ""

    def _get_roi_summary_for_neuron_type(self, neuron_type: str, connector, skip_roi_analysis=False) -> tuple:
        """Get ROI summary for a specific neuron type."""
        # Skip expensive ROI analysis if requested for faster indexing
        if skip_roi_analysis:
            return [], ""

        try:
            # Get neuron data for both sides
            neuron_data = connector.get_neuron_data(neuron_type, soma_side='both')

            roi_counts = neuron_data.get('roi_counts')
            neurons = neuron_data.get('neurons')

            if (not neuron_data or
                roi_counts is None or roi_counts.empty or
                neurons is None or neurons.empty):
                return [], ""

            # Use the page generator's ROI aggregation method
            roi_summary = self.page_generator._aggregate_roi_data(
                neuron_data.get('roi_counts'),
                neuron_data.get('neurons'),
                'both',
                connector
            )

            # Filter ROIs by threshold and clean names
            # Only show ROIs with ≥1.5% of either input (post) or output (pre) connections
            # This ensures only significant innervation targets are displayed
            threshold = 1.5  # Percentage threshold for ROI significance
            cleaned_roi_summary = []
            seen_names = set()

            for roi in roi_summary:
                # Only include ROIs that pass the 1.5% threshold for input OR output
                if roi['pre_percentage'] >= threshold or roi['post_percentage'] >= threshold:
                    cleaned_name = self._clean_roi_name(roi['name'])
                    if cleaned_name and cleaned_name not in seen_names:
                        cleaned_roi_summary.append({
                            'name': cleaned_name,
                            'total': roi['total'],
                            'pre_percentage': roi['pre_percentage'],
                            'post_percentage': roi['post_percentage']
                        })
                        seen_names.add(cleaned_name)

                        if len(cleaned_roi_summary) >= 5:  # Limit to top 5
                            break

            # Get parent ROI for the highest ranking (first) ROI
            parent_roi = ""
            if cleaned_roi_summary:
                highest_roi = cleaned_roi_summary[0]['name']
                parent_roi = self._get_roi_hierarchy_parent(highest_roi, connector)

            return cleaned_roi_summary, parent_roi

        except Exception as e:
            # If there's any error fetching ROI data, return empty list and parent
            logger.warning(f"Failed to get ROI summary for {neuron_type}: {e}")
            return [], ""

    async def create_index(self, command: CreateIndexCommand) -> Result[str, str]:
        """Create an index page listing all neuron types found in the output directory."""
        try:
            from pathlib import Path
            import re
            from collections import defaultdict
            import time

            logger.info("Starting optimized index creation with batch processing")
            start_time = time.time()

            # Determine output directory
            output_dir = Path(command.output_directory or self.config.output.directory)
            if not output_dir.exists():
                return Err(f"Output directory does not exist: {output_dir}")

            # First try to use cached data, then fall back to scanning
            cached_data = {}
            if self.cache_manager:
                cached_data = self.cache_manager.get_all_cached_data()
                if cached_data:
                    logger.info(f"Found cached data for {len(cached_data)} neuron types")

            if cached_data and not command.include_roi_analysis:
                # Use cached data for fast index generation
                logger.info(f"Using cached data for {len(cached_data)} neuron types (fast mode)")
                neuron_types = defaultdict(set)

                for neuron_type, cache_data in cached_data.items():
                    for side in cache_data.soma_sides_available:
                        if side == "both":
                            neuron_types[neuron_type].add('both')
                        elif side == "left":
                            neuron_types[neuron_type].add('L')
                        elif side == "right":
                            neuron_types[neuron_type].add('R')
                        elif side == "middle":
                            neuron_types[neuron_type].add('M')

                scan_time = 0.0
            else:
                # Scan for HTML files and extract neuron types with soma sides
                scan_start = time.time()
                neuron_types = defaultdict(set)
                html_pattern = re.compile(r'^([A-Za-z0-9_+\-\.,&()\']+?)(?:_([LRM]))?\.html$')

                for html_file in output_dir.glob('*.html'):
                    match = html_pattern.match(html_file.name)
                    if match:
                        base_name = match.group(1)
                        soma_side = match.group(2)  # L, R, M, or None for both

                        # Skip if this looks like an index file
                        if base_name.lower() in ['index', 'main']:
                            continue

                        # For files like "NeuronType_L.html", extract just "NeuronType"
                        if soma_side:
                            neuron_types[base_name].add(soma_side)
                        else:
                            neuron_types[base_name].add('both')

                scan_time = time.time() - scan_start
                logger.info(f"File scanning completed in {scan_time:.3f}s, found {len(neuron_types)} neuron types")

            if not neuron_types:
                return Err("No neuron type HTML files found in output directory")

            # Create a single connector instance to reuse across all neuron types
            from .neuprint_connector import NeuPrintConnector
            connector = None
            try:
                init_start = time.time()
                connector = NeuPrintConnector(self.config)
                # Pre-load ROI hierarchy cache with persistent caching
                self._get_roi_hierarchy_cached(connector, output_dir)
                init_time = time.time() - init_start
                logger.info(f"Database connector initialized in {init_time:.3f}s")
            except Exception as e:
                logger.warning(f"Failed to initialize connector: {e}")

            # OPTIMIZATION: Use batch processing for neuron data
            neuron_type_list = list(neuron_types.keys())

            if connector and command.include_roi_analysis:
                batch_start = time.time()
                index_data = await self._process_neuron_types_batch(
                    neuron_types, connector, command.include_roi_analysis
                )
                batch_time = time.time() - batch_start
                logger.info(f"Batch processing completed in {batch_time:.3f}s")
            else:
                # Try to use cached data first, then fall back to minimal processing
                index_data = []

                for neuron_type, sides in neuron_types.items():
                    # Check if we have cached data for this neuron type
                    cache_data = cached_data.get(neuron_type) if cached_data else None

                    has_both = 'both' in sides
                    has_left = 'L' in sides
                    has_right = 'R' in sides
                    has_middle = 'M' in sides

                    entry = {
                        'name': neuron_type,
                        'has_both': has_both,
                        'has_left': has_left,
                        'has_right': has_right,
                        'has_middle': has_middle,
                        'both_url': f'{neuron_type}.html' if has_both else None,
                        'left_url': f'{neuron_type}_L.html' if has_left else None,
                        'right_url': f'{neuron_type}_R.html' if has_right else None,
                        'middle_url': f'{neuron_type}_M.html' if has_middle else None,
                        'roi_summary': [],
                        'parent_roi': '',
                    }

                    # Use cached data if available
                    if cache_data:
                        entry['roi_summary'] = cache_data.roi_summary
                        entry['parent_roi'] = cache_data.parent_roi
                        logger.debug(f"Used cached data for {neuron_type}")

                    index_data.append(entry)

            # Sort results
            index_data.sort(key=lambda x: x['name'])

            # Group neuron types by parent ROI
            grouped_data = {}
            for entry in index_data:
                parent_roi = entry['parent_roi'] if entry['parent_roi'] else 'Other'
                if parent_roi not in grouped_data:
                    grouped_data[parent_roi] = []
                grouped_data[parent_roi].append(entry)

            # Sort groups by parent ROI name, but put 'Other' last
            sorted_groups = []
            for parent_roi in sorted(grouped_data.keys()):
                if parent_roi != 'Other':
                    sorted_groups.append({
                        'parent_roi': parent_roi,
                        'neuron_types': sorted(grouped_data[parent_roi], key=lambda x: x['name'])
                    })

            # Add 'Other' group last if it exists
            if 'Other' in grouped_data:
                sorted_groups.append({
                    'parent_roi': 'Other',
                    'neuron_types': sorted(grouped_data['Other'], key=lambda x: x['name'])
                })

            # Generate the index page using Jinja2
            render_start = time.time()
            template_data = {
                'config': self.config,
                'neuron_types': index_data,  # Keep for JavaScript filtering
                'grouped_neuron_types': sorted_groups,
                'total_types': len(index_data),
                'generation_time': command.requested_at
            }

            # Use the page generator's Jinja environment
            template = self.page_generator.env.get_template('index_page.html')
            html_content = template.render(template_data)

            # Write the index file
            index_path = output_dir / command.index_filename
            index_path.write_text(html_content, encoding='utf-8')

            # Generate neuron-search.js file with discovered neuron types
            await self._generate_neuron_search_js(output_dir, index_data, command.requested_at)

            render_time = time.time() - render_start
            total_time = time.time() - start_time

            logger.info(f"Template rendering completed in {render_time:.3f}s")
            logger.info(f"Total optimized index creation: {total_time:.3f}s")

            return Ok(str(index_path))

        except Exception as e:
            logger.error(f"Failed to create optimized index: {e}")
            return Err(f"Failed to create index: {str(e)}")

    async def _generate_neuron_search_js(self, output_dir: Path, neuron_data: list, generation_time) -> None:
        """Generate the neuron-search.js file with embedded neuron types data."""
        import json
        from datetime import datetime

        # Prepare neuron types data for JavaScript
        neuron_types_for_js = []

        for neuron in neuron_data:
            # Create an entry with the neuron name and available URLs
            neuron_entry = {
                'name': neuron['name'],
                'urls': {}
            }

            # Add available URLs for this neuron type
            if neuron['both_url']:
                neuron_entry['urls']['both'] = neuron['both_url']
            if neuron['left_url']:
                neuron_entry['urls']['left'] = neuron['left_url']
            if neuron['right_url']:
                neuron_entry['urls']['right'] = neuron['right_url']
            if neuron['middle_url']:
                neuron_entry['urls']['middle'] = neuron['middle_url']

            # Set primary URL (prefer 'both' if available, otherwise first available)
            if neuron['both_url']:
                neuron_entry['primary_url'] = neuron['both_url']
            elif neuron['left_url']:
                neuron_entry['primary_url'] = neuron['left_url']
            elif neuron['right_url']:
                neuron_entry['primary_url'] = neuron['right_url']
            elif neuron['middle_url']:
                neuron_entry['primary_url'] = neuron['middle_url']
            else:
                neuron_entry['primary_url'] = f"{neuron['name']}.html"  # fallback

            neuron_types_for_js.append(neuron_entry)

        # Sort neuron types alphabetically
        neuron_types_for_js.sort(key=lambda x: x['name'])

        # Extract just the names for the simple search functionality
        neuron_names = [neuron['name'] for neuron in neuron_types_for_js]

        # Prepare template data
        js_template_data = {
            'neuron_types_json': json.dumps(neuron_names, indent=2),
            'neuron_types_data_json': json.dumps(neuron_types_for_js, indent=2),
            'generation_timestamp': generation_time.strftime("%Y-%m-%d %H:%M:%S") if generation_time else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'neuron_types': neuron_types_for_js
        }

        # Load and render the neuron-search.js template
        js_template = self.page_generator.env.get_template('static/js/neuron-search.js.template')
        js_content = js_template.render(js_template_data)

        # Ensure static/js directory exists
        js_dir = output_dir / 'static' / 'js'
        js_dir.mkdir(parents=True, exist_ok=True)

        # Write the neuron-search.js file
        js_path = js_dir / 'neuron-search.js'
        js_path.write_text(js_content, encoding='utf-8')


    async def _process_neuron_types_batch(self, neuron_types_dict, connector, include_roi_analysis):
        """Process neuron types using batch queries for optimal performance."""
        import asyncio
        import time

        neuron_type_list = list(neuron_types_dict.keys())

        # OPTIMIZATION: Use batch queries to reduce database round trips
        logger.info(f"Starting batch processing for {len(neuron_type_list)} neuron types")

        # Batch fetch neuron data (replaces N individual queries with 1 batch query)
        batch_start = time.time()
        try:
            batch_neuron_data = connector.get_batch_neuron_data(neuron_type_list, soma_side='both')
            batch_fetch_time = time.time() - batch_start
            logger.info(f"Batch neuron data fetch: {batch_fetch_time:.3f}s ({len(neuron_type_list)/batch_fetch_time:.1f} types/sec)")
        except Exception as e:
            logger.warning(f"Batch query failed, falling back to individual queries: {e}")
            batch_neuron_data = {}

        # Process each neuron type with the batch-fetched data
        async def process_single_type(neuron_type: str, sides: set):
            has_both = 'both' in sides
            has_left = 'L' in sides
            has_right = 'R' in sides
            has_middle = 'M' in sides

            # Get ROI information using batch-fetched data
            roi_summary = []
            parent_roi = ""

            if include_roi_analysis and neuron_type in batch_neuron_data:
                try:
                    neuron_data = batch_neuron_data[neuron_type]
                    roi_summary, parent_roi = self._get_roi_summary_from_batch_data(
                        neuron_type, neuron_data, connector
                    )
                except Exception as e:
                    logger.debug(f"ROI analysis failed for {neuron_type}: {e}")

            return {
                'name': neuron_type,
                'has_both': has_both,
                'has_left': has_left,
                'has_right': has_right,
                'has_middle': has_middle,
                'both_url': f'{neuron_type}.html' if has_both else None,
                'left_url': f'{neuron_type}_L.html' if has_left else None,
                'right_url': f'{neuron_type}_R.html' if has_right else None,
                'middle_url': f'{neuron_type}_M.html' if has_middle else None,
                'roi_summary': roi_summary,
                'parent_roi': parent_roi,
            }

        # Process all types concurrently with higher concurrency
        # OPTIMIZATION: Increased from 50 to 200 since network I/O is the bottleneck
        semaphore = asyncio.Semaphore(200)

        async def process_with_semaphore(neuron_type: str, sides: set):
            async with semaphore:
                return await process_single_type(neuron_type, sides)

        tasks = [
            process_with_semaphore(neuron_type, sides)
            for neuron_type, sides in neuron_types_dict.items()
        ]

        process_start = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        process_time = time.time() - process_start

        # Filter out exceptions
        successful_results = [
            result for result in results
            if not isinstance(result, Exception)
        ]

        logger.info(f"Individual processing completed in {process_time:.3f}s")
        logger.info(f"Successfully processed {len(successful_results)}/{len(neuron_type_list)} neuron types")

        return successful_results

    def _get_roi_summary_from_batch_data(self, neuron_type: str, neuron_data, connector):
        """Get ROI summary from batch-fetched neuron data."""
        try:
            roi_counts = neuron_data.get('roi_counts')
            neurons = neuron_data.get('neurons')

            if (not neuron_data or
                roi_counts is None or roi_counts.empty or
                neurons is None or neurons.empty):
                return [], ""

            # Use the page generator's ROI aggregation method
            roi_summary = self.page_generator._aggregate_roi_data(
                roi_counts, neurons, 'both', connector
            )

            # Filter ROIs by threshold and clean names
            threshold = 1.5
            cleaned_roi_summary = []
            seen_names = set()

            for roi in roi_summary:
                if roi['pre_percentage'] >= threshold or roi['post_percentage'] >= threshold:
                    cleaned_name = self._clean_roi_name(roi['name'])
                    if cleaned_name and cleaned_name not in seen_names:
                        cleaned_roi_summary.append({
                            'name': cleaned_name,
                            'total': roi['total'],
                            'pre_percentage': roi['pre_percentage'],
                            'post_percentage': roi['post_percentage']
                        })
                        seen_names.add(cleaned_name)

                        if len(cleaned_roi_summary) >= 5:
                            break

            # Get parent ROI for the highest ranking (first) ROI
            parent_roi = ""
            if cleaned_roi_summary:
                highest_roi = cleaned_roi_summary[0]['name']
                parent_roi = self._get_roi_hierarchy_parent(highest_roi, connector)

            return cleaned_roi_summary, parent_roi

        except Exception as e:
            logger.warning(f"Failed to get ROI summary for {neuron_type}: {e}")
            return [], ""

    def _load_persistent_roi_cache(self):
        """Load ROI hierarchy from persistent cache file."""
        try:
            import json
            from pathlib import Path

            if not self._persistent_roi_cache_path:
                return {}

            cache_path = Path(self._persistent_roi_cache_path)
            if cache_path.exists():
                with open(cache_path, 'r') as f:
                    cache_data = json.load(f)

                # Check if cache is still valid (e.g., less than 24 hours old)
                import time
                cache_age = time.time() - cache_data.get('timestamp', 0)
                if cache_age < 24 * 3600:  # 24 hours
                    logger.info("Loaded ROI hierarchy from persistent cache")
                    return cache_data.get('hierarchy', {})
                else:
                    logger.info("Persistent ROI cache expired")

        except Exception as e:
            logger.debug(f"Failed to load persistent ROI cache: {e}")

        return {}

    def _save_persistent_roi_cache(self, hierarchy):
        """Save ROI hierarchy to persistent cache file."""
        try:
            import json
            import time
            from pathlib import Path

            if not self._persistent_roi_cache_path:
                return

            cache_path = Path(self._persistent_roi_cache_path)
            cache_path.parent.mkdir(parents=True, exist_ok=True)

            cache_data = {
                'hierarchy': hierarchy,
                'timestamp': time.time()
            }

            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)

            logger.info(f"Saved ROI hierarchy to persistent cache: {cache_path}")

        except Exception as e:
            logger.warning(f"Failed to save persistent ROI cache: {e}")

class ServiceContainer:
    """Simple service container for dependency management."""

    def __init__(self, config):
        self.config = config
        self._neuprint_connector = None
        self._page_generator = None
        self._page_service = None
        self._discovery_service = None
        self._connection_service = None
        self._queue_service = None
        self._index_service = None

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
                self.config.output.directory,
                self.queue_service
            )
        return self._page_generator

    @property
    def page_service(self) -> PageGenerationService:
        """Get or create page generation service."""
        if self._page_service is None:
            self._page_service = PageGenerationService(
                self.neuprint_connector,
                self.page_generator,
                self.config
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

    @property
    def queue_service(self) -> QueueService:
        """Get or create queue service."""
        if self._queue_service is None:
            self._queue_service = QueueService(self.config)
        return self._queue_service

    @property
    def index_service(self) -> IndexService:
        """Get or create index service."""
        if self._index_service is None:
            self._index_service = IndexService(self.config, self.page_generator)
        return self._index_service
