"""
Page Generation Service for QuickPage.

This service orchestrates page generation workflow using the modern
PageGenerationRequest and PageGenerationOrchestrator architecture.
"""

import logging
from ..result import Result, Ok, Err
from ..commands import GeneratePageCommand
from ..models import SomaSide
from ..models.page_generation import PageGenerationRequest, PageGenerationMode
from .cache_service import CacheService
from .soma_detection_service import SomaDetectionService

logger = logging.getLogger(__name__)


class PageGenerationService:
    """Orchestrates page generation workflow using modern architecture."""

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

        # Create neuron statistics service for soma detection
        from .neuron_statistics_service import NeuronStatisticsService
        neuron_statistics_service = NeuronStatisticsService(neuprint_connector)

        self.soma_detection_service = SomaDetectionService(
            neuprint_connector, page_generator, self.cache_service, neuron_statistics_service
        )

    async def generate_page(self, command: GeneratePageCommand) -> Result[str, str]:
        """Generate an HTML page for a neuron type using the modern workflow."""
        try:
            # Handle auto-detection for SomaSide.ALL
            if command.soma_side == SomaSide.ALL:
                return await self.soma_detection_service.generate_pages_with_auto_detection(command)

            # Pre-fetch raw neuron data (enables caching for future calls)
            neuron_type_name = command.neuron_type.value
            try:
                neuron_data = self.connector.get_neuron_data(neuron_type_name, soma_side_str)
            except Exception as e:
                return Err(f"Failed to fetch neuron data for {neuron_type_name}: {str(e)}")

            # Convert SomaSide enum to string format
            soma_side_str = command.soma_side.value if command.soma_side != SomaSide.ALL else "combined"

            # Check if we have data
            try:
                neurons_df = neuron_data.get('neurons') if neuron_data else None
                if (not neuron_data or
                    neurons_df is None or
                    len(neurons_df) == 0):
                    # Clear cache on failure to avoid stale data
                    self.connector.clear_neuron_data_cache(neuron_type_name)
                    return Err(f"No neurons found for type {command.neuron_type}")
            except Exception as e:
                logger.warning(f"Error checking neuron data for {neuron_type_name}: {e}")
                self.connector.clear_neuron_data_cache(neuron_type_name)
                return Err(f"Data validation error for {neuron_type_name}: {str(e)}")

            try:
                # Create modern PageGenerationRequest
                request = PageGenerationRequest(
                    neuron_type=neuron_type_name,
                    soma_side=soma_side_str,
                    neuron_data=neuron_data,
                    connector=self.connector,
                    image_format=command.image_format,
                    embed_images=command.embed_images,
                    uncompress=command.uncompress,
                    run_roi_analysis=True,
                    run_layer_analysis=True,
                    run_column_analysis=True,
                    hex_size=command.hex_size,
                    spacing_factor=command.spacing_factor
                )

                # Validate request
                if not request.validate():
                    return Err(f"Invalid page generation request for {neuron_type_name}")

                # Generate the page using the modern unified workflow
                response = self.generator.generate_page_unified(request)

                if not response.success:
                    return Err(f"Page generation failed: {response.error_message}")

                # Save to persistent cache for index generation
                await self._save_to_cache_modern(neuron_type_name, neuron_data, command)

                # Log cache performance and cleanup
                self.connector.log_cache_performance()
                self.connector.clear_neuron_data_cache(neuron_type_name)

                return Ok(response.output_path)

            except Exception as e:
                # Clear cache on error to avoid stale data
                self.connector.clear_neuron_data_cache(neuron_type_name)
                raise e

        except Exception as e:
            return Err(f"Failed to generate page: {str(e)}")

    async def _save_to_cache_modern(self, neuron_type_name: str, neuron_data: dict,
                                  command: GeneratePageCommand):
        """Save neuron data to persistent cache using modern dictionary format."""
        try:
            if self.cache_service and self.cache_manager:
                await self.cache_service.save_neuron_data_to_cache(
                    neuron_type_name, neuron_data, command, self.connector
                )
        except Exception as e:
            logger.warning(f"Failed to save to cache for {neuron_type_name}: {e}")
            # Don't fail the whole operation for cache issues

    def generate_page_sync(self, request: PageGenerationRequest) -> Result[str, str]:
        """Synchronous version of page generation for direct use.

        This method provides a direct interface to the modern generation workflow
        without requiring async/await for simple use cases.
        """
        try:
            # Validate request
            if not request.validate():
                return Err("Invalid page generation request: missing required data")

            # Generate the page using the modern unified workflow
            response = self.generator.generate_page_unified(request)

            if not response.success:
                return Err(f"Page generation failed: {response.error_message}")

            return Ok(response.output_path)

        except Exception as e:
            return Err(f"Failed to generate page: {str(e)}")
