"""
Application services for QuickPage.

Application services orchestrate business logic by coordinating between
domain entities and infrastructure services. They implement use cases
and handle the application's business workflows.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import logging

from ..commands import (
    GeneratePageCommand, GenerateBulkPagesCommand, DiscoverNeuronTypesCommand,
    TestConnectionCommand, ClearCacheCommand
)
from ..queries import (
    GetNeuronTypeQuery, GetNeuronTypeQueryResult,
    ListNeuronTypesQuery, ListNeuronTypesQueryResult,
    GetConnectivityQuery, GetConnectivityQueryResult,
    GetDatasetInfoQuery, GetDatasetInfoQueryResult,
    NeuronTypeInfo, DatasetInfo
)
from ...core.ports import (
    NeuronRepository, ConnectivityRepository, CacheRepository,
    TemplateEngine, FileStorage
)
from ...core.entities import NeuronCollection, NeuronTypeStatistics
from ...core.value_objects import NeuronTypeName, SomaSide
from ...shared.result import Result, Ok, Err


logger = logging.getLogger(__name__)


class PageGenerationService:
    """
    Application service for generating HTML pages.

    This service orchestrates the process of fetching neuron data,
    processing it, and generating HTML output files.
    """

    def __init__(
        self,
        neuron_repo: NeuronRepository,
        connectivity_repo: ConnectivityRepository,
        template_engine: TemplateEngine,
        file_storage: FileStorage,
        cache_repo: Optional[CacheRepository] = None
    ):
        self.neuron_repo = neuron_repo
        self.connectivity_repo = connectivity_repo
        self.template_engine = template_engine
        self.file_storage = file_storage
        self.cache_repo = cache_repo

    async def generate_page(self, command: GeneratePageCommand) -> Result[str, str]:
        """
        Generate a single HTML page for a neuron type.

        Args:
            command: The page generation command

        Returns:
            Result containing the output file path or error message
        """
        try:
            # Validate command
            validation_errors = command.validate()
            if validation_errors:
                return Err(f"Invalid command: {', '.join(validation_errors)}")

            logger.info(f"Generating page for {command.neuron_type}")

            # Fetch neuron data
            neuron_collection = await self.neuron_repo.find_by_type_and_side(
                command.neuron_type, command.soma_side
            )

            if neuron_collection.is_empty():
                return Err(f"No neurons found for type {command.neuron_type}")

            # Filter by minimum synapse count if specified
            if command.min_synapse_count > 0:
                filtered_neurons = [
                    neuron for neuron in neuron_collection.neurons
                    if neuron.get_total_synapses().value >= command.min_synapse_count
                ]
                neuron_collection.neurons = filtered_neurons

            # Calculate statistics
            statistics = neuron_collection.calculate_statistics()

            # Get connectivity data if requested
            connectivity = None
            if command.include_connectivity:
                connectivity_result = await self.connectivity_repo.get_connectivity_for_type(
                    command.neuron_type
                )
                connectivity = connectivity_result

            # Prepare template context
            context = self._build_template_context(
                neuron_collection, statistics, connectivity, command
            )

            # Render template
            html_content = await self.template_engine.render_template(
                command.template_name, context
            )

            # Generate output file path
            output_path = self._generate_output_path(
                command.neuron_type, command.soma_side, command.output_directory
            )

            # Ensure output directory exists
            await self._ensure_output_directory(output_path)

            # Save the generated HTML
            await self.file_storage.save_file(output_path, html_content)

            logger.info(f"Successfully generated page: {output_path}")
            return Ok(output_path)

        except Exception as e:
            error_msg = f"Failed to generate page for {command.neuron_type}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Err(error_msg)

    async def generate_bulk_pages(
        self,
        command: GenerateBulkPagesCommand
    ) -> Result[List[str], str]:
        """
        Generate multiple HTML pages concurrently.

        Args:
            command: The bulk generation command

        Returns:
            Result containing list of generated file paths or error message
        """
        try:
            # Validate command
            validation_errors = command.validate()
            if validation_errors:
                return Err(f"Invalid command: {', '.join(validation_errors)}")

            logger.info(f"Generating {len(command.neuron_types)} pages")

            # Convert to individual commands
            individual_commands = command.to_individual_commands()

            # Create semaphore for concurrency control
            semaphore = asyncio.Semaphore(command.max_concurrent)

            async def generate_single_with_semaphore(cmd: GeneratePageCommand):
                async with semaphore:
                    return await self.generate_page(cmd)

            # Execute all commands concurrently
            tasks = [
                generate_single_with_semaphore(cmd)
                for cmd in individual_commands
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            successful_paths = []
            errors = []

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    errors.append(f"Error generating {individual_commands[i].neuron_type}: {result}")
                elif result.is_err():
                    errors.append(result.error)
                else:
                    successful_paths.append(result.value)

            if errors and not successful_paths:
                return Err(f"All generations failed: {'; '.join(errors)}")
            elif errors:
                logger.warning(f"Some generations failed: {'; '.join(errors)}")

            logger.info(f"Successfully generated {len(successful_paths)} pages")
            return Ok(successful_paths)

        except Exception as e:
            error_msg = f"Failed to generate bulk pages: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Err(error_msg)

    def _build_template_context(
        self,
        neuron_collection: NeuronCollection,
        statistics: NeuronTypeStatistics,
        connectivity,
        command: GeneratePageCommand
    ) -> Dict[str, Any]:
        """Build the template context for rendering."""
        return {
            'neuron_collection': neuron_collection,
            'statistics': statistics,
            'connectivity': connectivity,
            'neuron_type': command.neuron_type,
            'soma_side': command.soma_side,
            'generated_at': datetime.now(),
            'include_3d_view': command.include_3d_view,
            'include_connectivity': command.include_connectivity,
            'min_synapse_count': command.min_synapse_count
        }

    def _generate_output_path(
        self,
        neuron_type: NeuronTypeName,
        soma_side: SomaSide,
        output_directory: Optional[str]
    ) -> str:
        """Generate the output file path."""
        base_dir = output_directory or "output"

        # Create filename based on neuron type and soma side
        filename_parts = [str(neuron_type)]

        if soma_side.value and soma_side.value != 'all':
            filename_parts.append(soma_side.normalize())

        filename = "_".join(filename_parts) + "_neuron_report.html"

        return f"{base_dir}/{filename}"

    async def _ensure_output_directory(self, output_path: str):
        """Ensure the output directory exists."""
        directory = "/".join(output_path.split("/")[:-1])
        if directory:
            await self.file_storage.create_directory(directory)


class NeuronDiscoveryService:
    """
    Application service for discovering and querying neuron data.

    This service handles neuron type discovery, search, and metadata retrieval.
    """

    def __init__(
        self,
        neuron_repo: NeuronRepository,
        cache_repo: Optional[CacheRepository] = None
    ):
        self.neuron_repo = neuron_repo
        self.cache_repo = cache_repo

    async def discover_neuron_types(
        self,
        command: DiscoverNeuronTypesCommand
    ) -> Result[List[NeuronTypeName], str]:
        """
        Discover available neuron types from the dataset.

        Args:
            command: The discovery command

        Returns:
            Result containing list of discovered neuron types or error message
        """
        try:
            # Validate command
            validation_errors = command.validate()
            if validation_errors:
                return Err(f"Invalid command: {', '.join(validation_errors)}")

            logger.info("Discovering neuron types")

            # Check cache first if available
            cache_key = self._build_discovery_cache_key(command)
            if self.cache_repo:
                cached_result = await self.cache_repo.get(cache_key)
                if cached_result:
                    logger.info("Retrieved neuron types from cache")
                    return Ok(cached_result)

            # Get all available types from repository
            all_types = await self.neuron_repo.get_available_types()

            # Apply filters
            filtered_types = self._apply_discovery_filters(all_types, command)

            # Apply sorting and limiting
            final_types = self._apply_discovery_sorting_and_limiting(filtered_types, command)

            # Cache the result if cache is available
            if self.cache_repo:
                await self.cache_repo.set(cache_key, final_types, ttl=3600)  # 1 hour TTL

            logger.info(f"Discovered {len(final_types)} neuron types")
            return Ok(final_types)

        except Exception as e:
            error_msg = f"Failed to discover neuron types: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Err(error_msg)

    async def get_neuron_type_details(
        self,
        query: GetNeuronTypeQuery
    ) -> Result[GetNeuronTypeQueryResult, str]:
        """
        Get detailed information about a specific neuron type.

        Args:
            query: The neuron type query

        Returns:
            Result containing neuron type details or error message
        """
        try:
            # Validate query
            validation_errors = query.validate()
            if validation_errors:
                return Err(f"Invalid query: {', '.join(validation_errors)}")

            logger.info(f"Getting details for neuron type {query.neuron_type}")

            # Get neuron collection
            if query.soma_side and query.soma_side.value != 'all':
                neuron_collection = await self.neuron_repo.find_by_type_and_side(
                    query.neuron_type, query.soma_side
                )
            else:
                neuron_collection = await self.neuron_repo.find_by_type(query.neuron_type)

            # Filter by minimum synapse count if specified
            if query.min_synapse_count > 0:
                filtered_neurons = [
                    neuron for neuron in neuron_collection.neurons
                    if neuron.get_total_synapses().value >= query.min_synapse_count
                ]
                neuron_collection.neurons = filtered_neurons

            # Calculate statistics
            statistics = neuron_collection.calculate_statistics()

            result = GetNeuronTypeQueryResult(
                neuron_collection=neuron_collection,
                statistics=statistics
            )

            return Ok(result)

        except Exception as e:
            error_msg = f"Failed to get neuron type details: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Err(error_msg)

    async def list_neuron_types(
        self,
        query: ListNeuronTypesQuery
    ) -> Result[ListNeuronTypesQueryResult, str]:
        """
        List available neuron types with metadata.

        Args:
            query: The list query

        Returns:
            Result containing list of neuron types with metadata or error message
        """
        try:
            # Validate query
            validation_errors = query.validate()
            if validation_errors:
                return Err(f"Invalid query: {', '.join(validation_errors)}")

            logger.info("Listing neuron types")

            # Get all available types
            all_types = await self.neuron_repo.get_available_types()

            # Get soma sides if requested
            types_with_sides = {}
            if query.include_soma_sides:
                types_with_sides = await self.neuron_repo.get_types_with_soma_sides()

            # Build neuron type info list
            neuron_type_infos = []
            for neuron_type in all_types:
                # Apply filter if specified
                if query.filter_pattern:
                    if query.filter_pattern.lower() not in str(neuron_type).lower():
                        continue

                # Check exclusion list
                if str(neuron_type) in query.exclude_types:
                    continue

                # Get available soma sides
                available_sides = types_with_sides.get(neuron_type, [])

                # Get statistics if requested
                statistics = None
                if query.include_statistics:
                    collection = await self.neuron_repo.find_by_type(neuron_type)
                    statistics = collection.calculate_statistics()

                info = NeuronTypeInfo(
                    name=neuron_type,
                    available_soma_sides=available_sides,
                    total_count=statistics.total_count if statistics else 0,
                    statistics=statistics
                )
                neuron_type_infos.append(info)

            # Apply sorting
            if query.sort_by == "name":
                neuron_type_infos.sort(key=lambda x: str(x.name))
            elif query.sort_by == "count":
                neuron_type_infos.sort(key=lambda x: x.total_count, reverse=True)
            elif query.sort_by == "random":
                import random
                random.shuffle(neuron_type_infos)

            # Apply limit
            neuron_type_infos = neuron_type_infos[:query.max_results]

            result = ListNeuronTypesQueryResult(
                neuron_types=neuron_type_infos,
                total_available=len(all_types)
            )

            return Ok(result)

        except Exception as e:
            error_msg = f"Failed to list neuron types: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Err(error_msg)

    def _apply_discovery_filters(
        self,
        types: List[NeuronTypeName],
        command: DiscoverNeuronTypesCommand
    ) -> List[NeuronTypeName]:
        """Apply filtering logic to neuron types."""
        filtered_types = types.copy()

        # Apply pattern filter
        if command.type_filter_pattern:
            filtered_types = [
                t for t in filtered_types
                if command.type_filter_pattern.lower() in str(t).lower()
            ]

        # Apply include_only filter
        if command.include_only:
            filtered_types = [
                t for t in filtered_types
                if str(t) in command.include_only
            ]

        # Apply exclude filter
        if command.exclude_types:
            filtered_types = [
                t for t in filtered_types
                if str(t) not in command.exclude_types
            ]

        return filtered_types

    def _apply_discovery_sorting_and_limiting(
        self,
        types: List[NeuronTypeName],
        command: DiscoverNeuronTypesCommand
    ) -> List[NeuronTypeName]:
        """Apply sorting and limiting logic."""
        if command.randomize:
            import random
            random.shuffle(types)
        else:
            types.sort(key=str)

        return types[:command.max_types]

    def _build_discovery_cache_key(self, command: DiscoverNeuronTypesCommand) -> str:
        """Build a cache key for the discovery command."""
        key_parts = [
            "discovery",
            str(command.max_types),
            command.type_filter_pattern or "no-filter",
            ",".join(sorted(command.exclude_types)),
            ",".join(sorted(command.include_only)),
            str(command.randomize),
            str(command.min_neuron_count)
        ]
        return ":".join(key_parts)


class ConnectionTestService:
    """
    Application service for testing data source connections.
    """

    def __init__(self, neuron_repo: NeuronRepository):
        self.neuron_repo = neuron_repo

    async def test_connection(
        self,
        command: TestConnectionCommand
    ) -> Result[GetDatasetInfoQueryResult, str]:
        """
        Test connection to the data source.

        Args:
            command: The connection test command

        Returns:
            Result containing dataset info or error message
        """
        try:
            # Validate command
            validation_errors = command.validate()
            if validation_errors:
                return Err(f"Invalid command: {', '.join(validation_errors)}")

            logger.info("Testing connection to data source")

            # Test connection with timeout
            connection_info = await asyncio.wait_for(
                self.neuron_repo.test_connection(),
                timeout=command.timeout_seconds
            )

            # Build dataset info
            dataset_info = DatasetInfo(
                name=connection_info.get('dataset', 'Unknown'),
                version=connection_info.get('version', 'Unknown'),
                server_url=connection_info.get('server', 'Unknown'),
                connection_status="Connected"
            )

            # Add additional info if requested
            if command.include_dataset_info:
                try:
                    # Get basic statistics
                    all_types = await self.neuron_repo.get_available_types()
                    dataset_info.available_neuron_types = len(all_types)
                except Exception as e:
                    logger.warning(f"Could not get dataset statistics: {e}")

            result = GetDatasetInfoQueryResult(dataset_info=dataset_info)

            logger.info("Connection test successful")
            return Ok(result)

        except asyncio.TimeoutError:
            error_msg = f"Connection test timed out after {command.timeout_seconds} seconds"
            logger.error(error_msg)
            return Err(error_msg)
        except Exception as e:
            error_msg = f"Connection test failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Err(error_msg)


# Export all services
__all__ = [
    'PageGenerationService',
    'NeuronDiscoveryService',
    'ConnectionTestService'
]
