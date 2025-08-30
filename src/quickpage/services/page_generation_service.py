"""
Page Generation Service for QuickPage.

This service orchestrates page generation workflow, delegating specific
responsibilities to specialized services while maintaining the main
generation logic.
"""

import logging
from ..result import Result, Ok, Err
from ..commands import GeneratePageCommand
from ..models import SomaSide
from .cache_service import CacheService
from .soma_detection_service import SomaDetectionService

logger = logging.getLogger(__name__)


class PageGenerationService:
    """Orchestrates page generation workflow."""

    def __init__(self, neuprint_connector, page_generator, config=None):
        """Initialize page generation service.

        Args:
            neuprint_connector: NeuPrint connector instance
            page_generator: Page generator instance
            config: Optional configuration object
        """
        self.connector = neuprint_connector
        self.generator = page_generator
        self.config = config

        # Initialize cache manager if config is available
        self.cache_manager = None
        if config and hasattr(config, 'output') and hasattr(config.output, 'directory'):
            from ..cache import create_cache_manager
            self.cache_manager = create_cache_manager(config.output.directory)

        # Initialize specialized services
        self.cache_service = CacheService(self.cache_manager, page_generator)
        self.soma_detection_service = SomaDetectionService(
            neuprint_connector, page_generator, self.cache_service
        )

    async def generate_page(self, command: GeneratePageCommand) -> Result[str, str]:
        """Generate an HTML page for a neuron type with optimized data sharing."""
        try:
            # Import the legacy NeuronType class
            from ..neuron_type import NeuronType
            from ..config import NeuronTypeConfig

            # Create NeuronType instance
            config = NeuronTypeConfig(
                name=command.neuron_type.value,
                description=f"{command.neuron_type.value} neurons"
            )

            # Handle auto-detection for SomaSide.ALL
            if command.soma_side == SomaSide.ALL:
                return await self.soma_detection_service.generate_pages_with_auto_detection(command, config)

            # Pre-fetch raw neuron data for single page generation (enables caching for future calls)
            neuron_type_name = command.neuron_type.value
            try:
                self.connector._get_or_fetch_raw_neuron_data(neuron_type_name)
            except Exception as e:
                return Err(f"Failed to fetch neuron data for {neuron_type_name}: {str(e)}")

            # Convert SomaSide enum to legacy format for specific sides
            legacy_soma_side = self._convert_soma_side_to_legacy(command.soma_side)

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
                    embed_images=command.embed_images,
                    uncompress=command.uncompress
                )

                # Save to persistent cache for index generation
                await self.cache_service.save_neuron_type_to_cache(neuron_type_name, neuron_type_obj, command, self.connector)

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

    def _convert_soma_side_to_legacy(self, soma_side: SomaSide) -> str:
        """Convert SomaSide enum to legacy format."""
        if soma_side == SomaSide.COMBINED:
            return 'combined'
        elif soma_side == SomaSide.LEFT:
            return 'left'
        elif soma_side == SomaSide.RIGHT:
            return 'right'
        elif soma_side == SomaSide.MIDDLE:
            return 'middle'
        else:
            return 'combined'
