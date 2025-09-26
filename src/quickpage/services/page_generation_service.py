"""
Page Generation Service for QuickPage.

This service orchestrates page generation workflow using the modern
PageGenerationOrchestrator architecture.
"""

import logging
from ..result import Result, Ok, Err
from ..commands import GeneratePageCommand


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
