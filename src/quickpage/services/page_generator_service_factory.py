"""
PageGenerator Service Factory - Phase 1 Refactoring

This factory encapsulates the complex service initialization logic that was
previously in PageGenerator.__init__, following the Factory pattern to
improve maintainability and testability.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
from jinja2 import Environment, FileSystemLoader

from ..config import Config
from ..visualization import HexagonGridGenerator
from ..utils import (
    NumberFormatter, PercentageFormatter, SynapseFormatter, NeurotransmitterFormatter,
    HTMLUtils, ColorUtils, TextUtils
)

logger = logging.getLogger(__name__)


class PageGeneratorServiceFactory:
    """Factory for creating and configuring PageGenerator service dependencies."""

    def __init__(self, config: Config, output_dir: str, queue_service=None, cache_manager=None):
        """
        Initialize the service factory.

        Args:
            config: Configuration object with template and output settings
            output_dir: Directory path for generated HTML files
            queue_service: Optional QueueService for checking queued neuron types
            cache_manager: Optional cache manager for accessing cached neuron data
        """
        self.config = config
        self.output_dir = Path(output_dir)
        self.template_dir = Path(config.output.template_dir)
        self.queue_service = queue_service
        self.cache_manager = cache_manager

        # Create empty services container
        self.services = {}

    def create_all_services(self) -> Dict[str, Any]:
        """
        Create and configure all services required by PageGenerator.

        Returns:
            Dictionary containing all configured services
        """
        logger.info("Creating PageGenerator services...")

        # Phase 1: Core infrastructure services
        self._create_resource_services()

        # Phase 2: Data loading services
        self._create_data_services()

        # Phase 3: Utility classes
        self._create_utility_services()

        # Phase 4: Analysis services
        self._create_analysis_services()

        # Phase 5: Template environment
        self._create_template_environment()

        # Phase 6: Processing services
        self._create_processing_services()

        # Phase 7: Final orchestration services
        self._create_orchestration_services()

        logger.info(f"Created {len(self.services)} services for PageGenerator")
        return self.services

    def _create_resource_services(self):
        """Create resource management and file system services."""
        from .resource_manager_service import ResourceManagerService

        # Initialize resource manager service
        self.services['resource_manager'] = ResourceManagerService(self.config, self.output_dir)

        # Set up output directories using resource manager
        directories = self.services['resource_manager'].setup_output_directories()
        self.services['types_dir'] = directories['types']
        self.services['eyemaps_dir'] = directories['eyemaps']

        # Initialize hexagon grid generator with eyemaps directory
        self.services['hexagon_generator'] = HexagonGridGenerator(
            output_dir=self.output_dir,
            eyemaps_dir=self.services['eyemaps_dir']
        )

    def _create_data_services(self):
        """Create data loading and external resource services."""
        # Load brain regions data for the abbr filter
        self.services['brain_regions'] = self._load_brain_regions()

        # Load citations data for synonyms links
        self.services['citations'] = self._load_citations()

    def _create_utility_services(self):
        """Create utility classes and formatters."""
        # Initialize utility classes (must be done before Jinja setup)
        self.services['color_utils'] = ColorUtils(self.services['hexagon_generator'])
        self.services['html_utils'] = HTMLUtils()
        self.services['text_utils'] = TextUtils()
        self.services['number_formatter'] = NumberFormatter()
        self.services['percentage_formatter'] = PercentageFormatter()
        self.services['synapse_formatter'] = SynapseFormatter()
        self.services['neurotransmitter_formatter'] = NeurotransmitterFormatter()

    def _create_analysis_services(self):
        """Create analysis and computation services."""
        from .layer_analysis_service import LayerAnalysisService
        from .neuron_selection_service import NeuronSelectionService
        from .file_service import FileService
        from .threshold_service import ThresholdService
        from .youtube_service import YouTubeService

        # Initialize service dependencies
        self.services['layer_analysis_service'] = LayerAnalysisService(self.config)
        self.services['neuron_selection_service'] = NeuronSelectionService(self.config)
        self.services['file_service'] = FileService()
        self.services['threshold_service'] = ThresholdService()
        self.services['youtube_service'] = YouTubeService()

    def _create_template_environment(self):
        """Create and configure Jinja2 template environment."""
        # Create template directory if it doesn't exist
        self.template_dir.mkdir(parents=True, exist_ok=True)

        # Set up Jinja2 environment
        env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Register custom filters and globals
        self._setup_jinja_filters_and_globals(env)

        self.services['template_env'] = env

    def _create_processing_services(self):
        """Create data processing and database services."""
        from .template_context_service import TemplateContextService
        from .data_processing_service import DataProcessingService
        from .database_query_service import DatabaseQueryService
        from .cache_service import CacheService
        from .roi_analysis_service import ROIAnalysisService

        # Note: These services need the PageGenerator instance, so we'll create placeholders
        # that will be properly initialized after PageGenerator creation
        self.services['template_context_service_config'] = {
            'class': TemplateContextService,
            'args': [],  # Will be set to [page_generator] after creation
        }

        self.services['data_processing_service_config'] = {
            'class': DataProcessingService,
            'args': [],  # Will be set to [page_generator] after creation
        }

        self.services['database_query_service'] = DatabaseQueryService(
            self.config,
            self.cache_manager,
            None  # data_processing_service will be set later
        )

        self.services['cache_service_config'] = {
            'class': CacheService,
            'args': [self.cache_manager],  # Will add page_generator after creation
        }

        self.services['roi_analysis_service_config'] = {
            'class': ROIAnalysisService,
            'args': [],  # Will be set to [page_generator] after creation
        }

    def _create_orchestration_services(self):
        """Create orchestration and coordination services."""
        from .column_analysis_service import ColumnAnalysisService
        from .url_generation_service import URLGenerationService
        from .page_generation_orchestrator import PageGenerationOrchestrator

        # These also need PageGenerator instance, so create configs
        self.services['column_analysis_service_config'] = {
            'class': ColumnAnalysisService,
            'args': [],  # Will be set to [page_generator, config] after creation
        }

        self.services['url_generation_service_config'] = {
            'class': URLGenerationService,
            'args': [
                self.config,
                None,  # env - will be set after creation
                None,  # page_generator - will be set after creation
                None,  # neuron_selection_service - will be set after creation
                None,  # database_query_service - will be set after creation
            ]
        }

        self.services['orchestrator_config'] = {
            'class': PageGenerationOrchestrator,
            'args': [],  # Will be set to [page_generator] after creation
        }

        # Initialize caches for expensive operations
        self.services['all_columns_cache'] = None
        self.services['column_analysis_cache'] = {}

    def finalize_services_with_page_generator(self, page_generator):
        """
        Complete service initialization that requires PageGenerator instance.

        Args:
            page_generator: The PageGenerator instance to inject into services
        """
        logger.info("Finalizing services with PageGenerator instance...")

        # Create services that depend on PageGenerator
        template_context_config = self.services['template_context_service_config']
        self.services['template_context_service'] = template_context_config['class'](page_generator)

        data_processing_config = self.services['data_processing_service_config']
        self.services['data_processing_service'] = data_processing_config['class'](page_generator)

        # Update database_query_service with data_processing_service
        self.services['database_query_service'].data_processing_service = self.services['data_processing_service']

        cache_service_config = self.services['cache_service_config']
        self.services['cache_service'] = cache_service_config['class'](
            cache_service_config['args'][0], page_generator
        )

        roi_analysis_config = self.services['roi_analysis_service_config']
        self.services['roi_analysis_service'] = roi_analysis_config['class'](page_generator)

        column_analysis_config = self.services['column_analysis_service_config']
        self.services['column_analysis_service'] = column_analysis_config['class'](
            page_generator, self.config
        )

        # Create URL generation service with all dependencies
        from .url_generation_service import URLGenerationService
        self.services['url_generation_service'] = URLGenerationService(
            self.config,
            self.services['template_env'],
            page_generator,
            self.services['neuron_selection_service'],
            self.services['database_query_service']
        )

        # Create orchestrator
        orchestrator_config = self.services['orchestrator_config']
        self.services['orchestrator'] = orchestrator_config['class'](page_generator)

        # Clean up config objects
        config_keys = [k for k in self.services.keys() if k.endswith('_config')]
        for key in config_keys:
            del self.services[key]

        logger.info("Service finalization complete")

    def _load_brain_regions(self) -> Dict[str, str]:
        """Load brain regions data from CSV for the abbr filter."""
        try:
            # Get the project root directory
            project_root = Path(__file__).parent.parent.parent.parent
            brain_regions_file = project_root / 'input' / 'brainregions.csv'

            if brain_regions_file.exists():
                # Load CSV manually to handle commas in brain region names
                # Split only on the first comma to separate abbreviation from full name
                brain_regions_dict = {}
                with open(brain_regions_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and ',' in line:
                            # Split on first comma only
                            parts = line.split(',', 1)
                            if len(parts) == 2:
                                abbr = parts[0].strip()
                                full_name = parts[1].strip()
                                brain_regions_dict[abbr] = full_name
                logger.info(f"Loaded {len(brain_regions_dict)} brain regions from {brain_regions_file}")
                return brain_regions_dict
            else:
                logger.warning(f"Brain regions file not found: {brain_regions_file}")
                return {}
        except Exception as e:
            logger.error(f"Error loading brain regions data: {e}")
            return {}

    def _load_citations(self) -> Dict[str, tuple]:
        """Load citations data from CSV for synonyms links."""
        try:
            # Get the project root directory
            project_root = Path(__file__).parent.parent.parent.parent
            citations_file = project_root / 'input' / 'citations.csv'

            if citations_file.exists():
                # Load CSV manually to handle potential commas in citations
                citations_dict = {}
                with open(citations_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and ',' in line:
                            # Split on commas, but handle quoted titles
                            import csv
                            import io
                            reader = csv.reader(io.StringIO(line))
                            row = next(reader)

                            if len(row) >= 2:
                                citation = row[0].strip()
                                url = row[1].strip()
                                title = row[2].strip().strip('"') if len(row) >= 3 else ""

                                # Convert DOI to full URL if it starts with "10."
                                if url.startswith("10."):
                                    url = f"https://doi.org/{url}"

                                # Store as tuple: (url, title)
                                citations_dict[citation] = (url, title)

                logger.info(f"Loaded {len(citations_dict)} citations from {citations_file}")
                return citations_dict
            else:
                logger.warning(f"Citations file not found: {citations_file}")
                return {}
        except Exception as e:
            logger.error(f"Error loading citations data: {e}")
            return {}

    def _setup_jinja_filters_and_globals(self, env: Environment):
        """Set up Jinja2 filters and global variables."""
        # Add utility classes as globals
        env.globals.update({
            'color_utils': self.services['color_utils'],
            'html_utils': self.services['html_utils'],
            'text_utils': self.services['text_utils'],
            'number_formatter': self.services['number_formatter'],
            'percentage_formatter': self.services['percentage_formatter'],
            'synapse_formatter': self.services['synapse_formatter'],
            'neurotransmitter_formatter': self.services['neurotransmitter_formatter'],
        })

        # Add all custom filters
        env.filters['format_number'] = self.services['number_formatter'].format_number
        env.filters['format_percentage'] = self.services['percentage_formatter'].format_percentage
        env.filters['format_percentage_5'] = self.services['percentage_formatter'].format_percentage_5
        env.filters['format_synapse_count'] = self.services['synapse_formatter'].format_synapse_count
        env.filters['format_conn_count'] = self.services['synapse_formatter'].format_conn_count
        env.filters['abbreviate_neurotransmitter'] = self.services['neurotransmitter_formatter'].abbreviate_neurotransmitter
        env.filters['is_png_data'] = self.services['html_utils'].is_png_data
        env.filters['neuron_link'] = lambda neuron_type, soma_side: self.services['html_utils'].create_neuron_link(neuron_type, soma_side, self.queue_service)
        env.filters['truncate_neuron_name'] = self.services['text_utils'].truncate_neuron_name
        env.filters['roi_abbr'] = self._roi_abbr_filter
        # Note: get_partner_body_ids filter will be added after PageGenerator creation
        env.filters['synapses_to_colors'] = self.services['color_utils'].synapses_to_colors
        env.filters['neurons_to_colors'] = self.services['color_utils'].neurons_to_colors

    def _roi_abbr_filter(self, roi_name: str) -> str:
        """
        Jinja2 filter to convert full ROI names to abbreviations.

        Args:
            roi_name: Full ROI name

        Returns:
            Abbreviated ROI name if found, original name otherwise
        """
        if not roi_name or not isinstance(roi_name, str):
            return roi_name

        brain_regions = self.services.get('brain_regions', {})

        # Check if the roi_name is already an abbreviation
        if roi_name in brain_regions:
            return roi_name

        # Look for the roi_name in the full names and return the abbreviation
        for abbr, full_name in brain_regions.items():
            if full_name.lower() == roi_name.lower():
                return abbr

        # If no match found, return original name
        return roi_name

    @classmethod
    def create_page_generator(cls, config: Config, output_dir: str,
                            queue_service=None, cache_manager=None):
        """
        Factory method to create a fully configured PageGenerator.

        Args:
            config: Configuration object with template and output settings
            output_dir: Directory path for generated HTML files
            queue_service: Optional QueueService for checking queued neuron types
            cache_manager: Optional cache manager for accessing cached neuron data

        Returns:
            Configured PageGenerator instance
        """
        logger.info(f"Creating PageGenerator for output directory: {output_dir}")

        # Create factory instance
        factory = cls(config, output_dir, queue_service, cache_manager)

        # Create all services
        services = factory.create_all_services()

        # Import PageGenerator here to avoid circular imports
        from ..page_generator import PageGenerator

        # Create PageGenerator with services
        page_generator = PageGenerator(
            config=config,
            output_dir=output_dir,
            queue_service=queue_service,
            cache_manager=cache_manager,
            services=services
        )

        # Finalize services that need PageGenerator reference
        factory.finalize_services_with_page_generator(page_generator)

        # Assign finalized services to PageGenerator
        page_generator.template_context_service = services['template_context_service']
        page_generator.data_processing_service = services['data_processing_service']
        page_generator.cache_service = services['cache_service']
        page_generator.roi_analysis_service = services['roi_analysis_service']
        page_generator.column_analysis_service = services['column_analysis_service']
        page_generator.url_generation_service = services['url_generation_service']
        page_generator.orchestrator = services['orchestrator']

        # Add PageGenerator-dependent filters to Jinja environment
        page_generator.env.filters['get_partner_body_ids'] = page_generator._get_partner_body_ids

        # Copy static files to output directory
        services['resource_manager'].copy_static_files()

        logger.info("PageGenerator creation complete")
        return page_generator
