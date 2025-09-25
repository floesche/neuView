"""
Page Generation Service for QuickPage.

This service orchestrates page generation workflow using the modern
PageGenerationRequest and PageGenerationOrchestrator architecture.
"""

import logging
from ..result import Result, Ok, Err
from ..commands import GeneratePageCommand

from ..models.page_generation import PageGenerationRequest
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
        if config and hasattr(config, "output") and hasattr(config.output, "directory"):
            from ..cache import create_cache_manager

            self.cache_manager = create_cache_manager(config.output.directory)

        # Initialize specialized services
        self.cache_service = CacheService(
            self.cache_manager, page_generator, None, config
        )

        # Create neuron statistics service for soma detection
        from .neuron_statistics_service import NeuronStatisticsService

        neuron_statistics_service = NeuronStatisticsService(neuprint_connector)

        self.soma_detection_service = SomaDetectionService(
            neuprint_connector,
            page_generator,
            self.cache_service,
            neuron_statistics_service,
        )

    async def generate_page(self, command: GeneratePageCommand) -> Result[str, str]:
        """Generate HTML pages for a neuron type, creating all available pages."""
        try:
            # Always use auto-detection to generate all available pages
            return await self.soma_detection_service.generate_pages_with_auto_detection(
                command
            )

        except Exception as e:
            return Err(f"Failed to generate pages: {str(e)}")

    async def _save_to_cache_modern(
        self, neuron_type_name: str, neuron_data: dict, command: GeneratePageCommand
    ):
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
