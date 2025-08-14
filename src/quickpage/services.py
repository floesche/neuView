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


class QueueService:
    """Service for managing queue files."""

    def __init__(self, config):
        self.config = config

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

        # Update the central queue.yaml file
        await self._update_queue_manifest([command.neuron_type.value])

        return Ok(str(yaml_path))

    async def _create_batch_queue_files(self, command: FillQueueCommand) -> Result[str, str]:
        """Create queue files for multiple neuron types."""
        from .neuprint_connector import NeuPrintConnector

        # Create services for discovery
        connector = NeuPrintConnector(self.config)
        discovery_service = NeuronDiscoveryService(connector, self.config)

        # Determine max results
        max_results = 0 if command.all_types else command.max_types

        # Discover neuron types
        list_command = ListNeuronTypesCommand(
            max_results=max_results,
            exclude_empty=True,
            all_results=command.all_types
        )

        list_result = await discovery_service.list_neuron_types(list_command)

        if list_result.is_err():
            return Err(f"Failed to discover neuron types: {list_result.unwrap_err()}")

        types = list_result.unwrap()
        if not types:
            return Err("No neuron types found")

        # Create queue files for each type
        created_files = []

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

            result = await self._create_single_queue_file(single_command)
            if result.is_ok():
                created_files.append(type_info.name)

        if created_files:
            # Update the central queue.yaml file
            await self._update_queue_manifest(created_files)
            return Ok(f"Created {len(created_files)} queue files")
        else:
            return Err("Failed to create any queue files")

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

        # Add new neuron types
        for neuron_type in neuron_types:
            existing_types.add(neuron_type)

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

    def get_queued_neuron_types(self) -> List[str]:
        """Get list of neuron types in the queue manifest."""
        queue_dir = Path(self.config.output.directory) / '.queue'
        queue_manifest_path = queue_dir / 'queue.yaml'

        if not queue_manifest_path.exists():
            return []

        try:
            with open(queue_manifest_path, 'r') as f:
                manifest_data = yaml.safe_load(f) or {}
            return manifest_data.get('neuron_types', [])
        except Exception:
            return []

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
                yaml_files = list(queue_dir.glob('*.yaml'))

                if not yaml_files:
                    return Err("No queue files found")

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

    async def create_index(self, command: CreateIndexCommand) -> Result[str, str]:
        """Create an index page listing all neuron types found in the output directory."""
        try:
            from pathlib import Path
            import re
            from collections import defaultdict

            # Determine output directory
            output_dir = Path(command.output_directory or self.config.output.directory)
            if not output_dir.exists():
                return Err(f"Output directory does not exist: {output_dir}")

            # Scan for HTML files and extract neuron types with soma sides
            neuron_types = defaultdict(set)
            html_pattern = re.compile(r'^([A-Za-z0-9_-]+?)(?:_([LRM]))?\.html$')

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

            if not neuron_types:
                return Err("No neuron type HTML files found in output directory")

            # Prepare data for template
            index_data = []
            for neuron_type in sorted(neuron_types.keys()):
                sides = neuron_types[neuron_type]

                # Determine what files exist
                has_both = 'both' in sides
                has_left = 'L' in sides
                has_right = 'R' in sides
                has_middle = 'M' in sides

                # Create entry for this neuron type
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
                }

                index_data.append(entry)

            # Generate the index page using Jinja2
            template_data = {
                'config': self.config,
                'neuron_types': index_data,
                'total_types': len(index_data),
                'generation_time': command.requested_at
            }

            # Use the page generator's Jinja environment
            template = self.page_generator.env.get_template('index_page.html')
            html_content = template.render(template_data)

            # Write the index file
            index_path = output_dir / command.index_filename
            index_path.write_text(html_content, encoding='utf-8')

            return Ok(str(index_path))

        except Exception as e:
            return Err(f"Failed to create index: {str(e)}")


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
