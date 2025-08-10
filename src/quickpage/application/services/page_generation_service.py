"""
PageGenerationService for the QuickPage application layer.

This module contains the application service responsible for orchestrating
the process of generating HTML pages for neuron types. It coordinates between
domain entities and infrastructure services to implement the page generation
use case.
"""

from typing import List, Optional
import asyncio
import logging

from ..commands import GeneratePageCommand, GenerateBulkPagesCommand
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
    ) -> dict:
        """Build the template context for rendering."""
        from datetime import datetime

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
