"""
CLI Application for QuickPage - Domain-Driven Design Implementation

This module provides a clean, DDD-based CLI application that replaces the legacy
ApplicationBootstrap. It properly integrates all the DDD components including:
- Domain services and factories
- Application services with CQRS
- Infrastructure adapters
- Domain events
- Dependency injection

The CLI application serves as the composition root where all dependencies
are wired together and the application context is established.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

import click

from ..shared.dependency_injection import Container
from ..shared.domain_events import get_event_publisher, EventPublisher
from ..application.queries.handlers import (
    QueryBus, get_query_bus, set_query_bus,
    GetNeuronTypeDetailQuery, GetNeuronTypeDetailQueryHandler,
    SearchNeuronsQuery, SearchNeuronsQueryHandler,
    GetNeuronTypeComparisonQuery, GetNeuronTypeComparisonQueryHandler
)
from ..application.commands import (
    GeneratePageCommand, GenerateBulkPagesCommand
)
from ..application.services import (
    PageGenerationService, NeuronDiscoveryService, ConnectionTestService
)
from ..core.services import NeuronAnalysisService
from ..core.factories import NeuronFactory, NeuronCollectionFactory, AggregateFactory
from ..core.value_objects import NeuronTypeName, SomaSide
from ..infrastructure.repositories import (
    NeuPrintNeuronRepository, NeuPrintConnectivityRepository
)
from ..infrastructure.adapters import (
    Jinja2TemplateEngine, LocalFileStorage, MemoryCacheRepository
)
from ...config import Config
from ...shared.result import Result


@dataclass
class ApplicationContext:
    """
    Application context containing all configured services and dependencies.

    This serves as the composition root for dependency injection and provides
    a clean interface for the CLI to access all application services.
    """
    # Configuration
    config: Config

    # Core domain services
    neuron_analysis_service: NeuronAnalysisService

    # Domain factories
    neuron_factory: NeuronFactory
    collection_factory: NeuronCollectionFactory
    aggregate_factory: AggregateFactory

    # Infrastructure repositories
    neuron_repository: NeuPrintNeuronRepository
    connectivity_repository: NeuPrintConnectivityRepository
    cache_repository: MemoryCacheRepository

    # Infrastructure adapters
    template_engine: Jinja2TemplateEngine
    file_storage: LocalFileStorage

    # Application services
    page_generation_service: PageGenerationService
    discovery_service: NeuronDiscoveryService
    connection_test_service: ConnectionTestService

    # CQRS components
    query_bus: QueryBus
    event_publisher: EventPublisher

    # Application metadata
    created_at: datetime
    version: str


class CLIApplication:
    """
    Main CLI application that handles dependency injection and service coordination.

    This class is responsible for:
    - Setting up the dependency injection container
    - Configuring all services and repositories
    - Setting up event handlers
    - Providing a clean interface for CLI commands
    - Managing application lifecycle
    """

    def __init__(self, config: Config):
        self.config = config
        self._context: Optional[ApplicationContext] = None
        self._container: Optional[Container] = None
        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> None:
        """
        Initialize the application and all its dependencies.

        This method sets up the entire application context including:
        - Domain services and factories
        - Infrastructure adapters and repositories
        - Application services
        - Event system
        - Query handlers
        """
        self.logger.info("Initializing QuickPage CLI application")

        try:
            # Create dependency injection container
            self._container = Container()

            # Initialize domain factories
            neuron_factory = NeuronFactory()
            collection_factory = NeuronCollectionFactory(neuron_factory)
            aggregate_factory = AggregateFactory(neuron_factory, collection_factory)

            # Initialize domain services
            neuron_analysis_service = NeuronAnalysisService()

            # Initialize infrastructure adapters
            template_engine = Jinja2TemplateEngine(
                template_dir=self.config.templates.directory,
                cache_templates=self.config.templates.cache_enabled
            )

            file_storage = LocalFileStorage(
                base_directory=self.config.output.directory
            )

            cache_repository = MemoryCacheRepository()

            # Initialize infrastructure repositories
            neuron_repository = NeuPrintNeuronRepository(
                server=self.config.neuprint.server,
                token=self.config.neuprint.token,
                dataset=self.config.neuprint.dataset,
                cache_repository=cache_repository
            )

            connectivity_repository = NeuPrintConnectivityRepository(
                server=self.config.neuprint.server,
                token=self.config.neuprint.token,
                dataset=self.config.neuprint.dataset,
                cache_repository=cache_repository
            )

            # Initialize application services
            page_generation_service = PageGenerationService(
                neuron_repo=neuron_repository,
                connectivity_repo=connectivity_repository,
                template_engine=template_engine,
                file_storage=file_storage,
                cache_repo=cache_repository
            )

            discovery_service = NeuronDiscoveryService(
                neuron_repository=neuron_repository,
                analysis_service=neuron_analysis_service,
                collection_factory=collection_factory
            )

            connection_test_service = ConnectionTestService(
                neuron_repository=neuron_repository,
                connectivity_repository=connectivity_repository
            )

            # Initialize CQRS components
            event_publisher = get_event_publisher()
            query_bus = get_query_bus()

            # Register query handlers
            await self._setup_query_handlers(
                query_bus=query_bus,
                neuron_repository=neuron_repository,
                connectivity_repository=connectivity_repository,
                analysis_service=neuron_analysis_service
            )

            # Setup event handlers
            await self._setup_event_handlers(event_publisher)

            # Create application context
            self._context = ApplicationContext(
                config=self.config,
                neuron_analysis_service=neuron_analysis_service,
                neuron_factory=neuron_factory,
                collection_factory=collection_factory,
                aggregate_factory=aggregate_factory,
                neuron_repository=neuron_repository,
                connectivity_repository=connectivity_repository,
                cache_repository=cache_repository,
                template_engine=template_engine,
                file_storage=file_storage,
                page_generation_service=page_generation_service,
                discovery_service=discovery_service,
                connection_test_service=connection_test_service,
                query_bus=query_bus,
                event_publisher=event_publisher,
                created_at=datetime.now(),
                version="2.0.0"
            )

            self.logger.info("QuickPage CLI application initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize CLI application: {e}", exc_info=True)
            raise

    async def shutdown(self) -> None:
        """Clean shutdown of the application."""
        self.logger.info("Shutting down QuickPage CLI application")

        if self._context:
            # Clear event subscriptions
            self._context.event_publisher.clear_subscriptions()

            # Clear query handlers
            self._context.query_bus.clear_handlers()

            # Close any connections (if repositories support it)
            # This would be implemented in the repositories

            self._context = None

        self.logger.info("QuickPage CLI application shut down")

    @property
    def context(self) -> ApplicationContext:
        """Get the application context. Raises if not initialized."""
        if self._context is None:
            raise RuntimeError("Application not initialized. Call initialize() first.")
        return self._context

    async def generate_page(
        self,
        neuron_type: str,
        soma_side: str = "all",
        output_directory: Optional[str] = None,
        include_connectivity: bool = True,
        include_3d_view: bool = False,
        min_synapse_count: int = 0,
        template_name: str = "neuron_report.html"
    ) -> Result[str, str]:
        """
        Generate a single neuron type page.

        Args:
            neuron_type: The neuron type to generate a page for
            soma_side: Soma side filter ('left', 'right', 'all')
            output_directory: Optional output directory override
            include_connectivity: Whether to include connectivity data
            include_3d_view: Whether to include 3D visualization
            min_synapse_count: Minimum synapse count filter
            template_name: Template file to use

        Returns:
            Result containing output file path or error message
        """
        try:
            command = GeneratePageCommand(
                neuron_type=NeuronTypeName(neuron_type),
                soma_side=SomaSide(soma_side),
                output_directory=output_directory or self.config.output.directory,
                include_connectivity=include_connectivity,
                include_3d_view=include_3d_view,
                min_synapse_count=min_synapse_count,
                template_name=template_name
            )

            result = await self.context.page_generation_service.generate_page(command)

            if result.is_ok():
                self.logger.info(f"Successfully generated page: {result.value}")
            else:
                self.logger.error(f"Failed to generate page: {result.error}")

            return result

        except Exception as e:
            error_msg = f"Error generating page for {neuron_type}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return Result.err(error_msg)

    async def list_neuron_types(self) -> Result[Dict[str, Any], str]:
        """
        List all available neuron types.

        Returns:
            Result containing neuron type information or error message
        """
        try:
            result = await self.context.discovery_service.discover_neuron_types()

            if result.is_ok():
                type_info = result.value
                self.logger.info(f"Found {len(type_info)} neuron types")
                return Result.ok({
                    'types': type_info,
                    'total_count': len(type_info),
                    'discovered_at': datetime.now().isoformat()
                })
            else:
                self.logger.error(f"Failed to discover neuron types: {result.error}")
                return result

        except Exception as e:
            error_msg = f"Error listing neuron types: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return Result.err(error_msg)

    async def test_connection(self) -> Result[Dict[str, Any], str]:
        """
        Test connection to NeuPrint database.

        Returns:
            Result containing connection information or error message
        """
        try:
            result = await self.context.connection_test_service.test_connection()

            if result.is_ok():
                connection_info = result.value
                self.logger.info("Connection test successful")
                return Result.ok(connection_info)
            else:
                self.logger.error(f"Connection test failed: {result.error}")
                return result

        except Exception as e:
            error_msg = f"Error testing connection: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return Result.err(error_msg)

    async def search_neurons(
        self,
        neuron_type: Optional[str] = None,
        soma_side: Optional[str] = None,
        min_synapses: Optional[int] = None,
        max_synapses: Optional[int] = None,
        required_rois: Optional[list] = None,
        high_quality_only: bool = False,
        limit: int = 100
    ) -> Result[Dict[str, Any], str]:
        """
        Search for neurons with specified criteria.

        Args:
            neuron_type: Optional neuron type filter
            soma_side: Optional soma side filter
            min_synapses: Minimum synapse count
            max_synapses: Maximum synapse count
            required_rois: List of required ROIs
            high_quality_only: Filter for high quality neurons only
            limit: Maximum number of results

        Returns:
            Result containing search results or error message
        """
        try:
            query = SearchNeuronsQuery(
                neuron_type=neuron_type,
                soma_side=soma_side,
                min_synapses=min_synapses,
                max_synapses=max_synapses,
                required_rois=required_rois or [],
                high_quality_only=high_quality_only,
                limit=limit
            )

            result = await self.context.query_bus.handle(query)

            if result.is_ok():
                search_result = result.value
                self.logger.info(f"Search found {len(search_result.neurons)} neurons")
                return Result.ok({
                    'neurons': [neuron.__dict__ for neuron in search_result.neurons],
                    'total_count': search_result.total_count,
                    'filtered_count': search_result.filtered_count,
                    'search_criteria': search_result.search_criteria,
                    'facets': search_result.facets
                })
            else:
                self.logger.error(f"Search failed: {result.error}")
                return result

        except Exception as e:
            error_msg = f"Error searching neurons: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return Result.err(error_msg)

    async def get_neuron_type_details(
        self,
        neuron_type: str,
        soma_side: Optional[str] = None,
        include_connectivity: bool = False,
        include_individual_neurons: bool = False
    ) -> Result[Dict[str, Any], str]:
        """
        Get detailed information about a specific neuron type.

        Args:
            neuron_type: The neuron type to analyze
            soma_side: Optional soma side filter
            include_connectivity: Whether to include connectivity analysis
            include_individual_neurons: Whether to include individual neuron data

        Returns:
            Result containing detailed neuron type information or error message
        """
        try:
            query = GetNeuronTypeDetailQuery(
                neuron_type=neuron_type,
                soma_side=soma_side,
                include_connectivity=include_connectivity,
                include_individual_neurons=include_individual_neurons
            )

            result = await self.context.query_bus.handle(query)

            if result.is_ok():
                detail_result = result.value
                self.logger.info(f"Retrieved details for neuron type: {neuron_type}")

                # Convert to serializable format
                return Result.ok({
                    'statistics': detail_result.statistics.__dict__,
                    'connectivity': detail_result.connectivity.__dict__ if detail_result.connectivity else None,
                    'individual_neurons': [n.__dict__ for n in detail_result.individual_neurons],
                    'quality_assessment': detail_result.quality_assessment,
                    'bilateral_analysis': detail_result.bilateral_analysis
                })
            else:
                self.logger.error(f"Failed to get neuron type details: {result.error}")
                return result

        except Exception as e:
            error_msg = f"Error getting neuron type details: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return Result.err(error_msg)

    async def _setup_query_handlers(
        self,
        query_bus: QueryBus,
        neuron_repository,
        connectivity_repository,
        analysis_service
    ) -> None:
        """Setup all CQRS query handlers."""

        # Register neuron type detail handler
        detail_handler = GetNeuronTypeDetailQueryHandler(
            neuron_repository=neuron_repository,
            connectivity_repository=connectivity_repository,
            analysis_service=analysis_service
        )
        query_bus.register_handler(GetNeuronTypeDetailQuery, detail_handler)

        # Register search handler
        search_handler = SearchNeuronsQueryHandler(
            neuron_repository=neuron_repository
        )
        query_bus.register_handler(SearchNeuronsQuery, search_handler)

        # Register comparison handler
        comparison_handler = GetNeuronTypeComparisonQueryHandler(
            neuron_repository=neuron_repository,
            analysis_service=analysis_service
        )
        query_bus.register_handler(GetNeuronTypeComparisonQuery, comparison_handler)

        self.logger.info("Query handlers registered successfully")

    async def _setup_event_handlers(self, event_publisher: EventPublisher) -> None:
        """Setup domain event handlers."""

        # Example: Log all domain events
        async def log_domain_event(event):
            self.logger.info(f"Domain event: {event.event_type} - {event.event_id}")

        # Subscribe to all domain events for logging
        from ..shared.domain_events import DomainEvent
        event_publisher.subscribe(
            handler=log_domain_event,
            event_types=DomainEvent
        )

        self.logger.info("Event handlers setup successfully")


# Global application instance
_app_instance: Optional[CLIApplication] = None


def get_application() -> CLIApplication:
    """Get the global CLI application instance."""
    global _app_instance
    if _app_instance is None:
        raise RuntimeError("Application not initialized")
    return _app_instance


def set_application(app: CLIApplication) -> None:
    """Set the global CLI application instance."""
    global _app_instance
    _app_instance = app


async def initialize_application(config: Config) -> CLIApplication:
    """
    Initialize and return a configured CLI application.

    Args:
        config: Application configuration

    Returns:
        Initialized CLI application
    """
    app = CLIApplication(config)
    await app.initialize()
    set_application(app)
    return app


# Context manager for proper application lifecycle
class ApplicationManager:
    """Context manager for CLI application lifecycle."""

    def __init__(self, config: Config):
        self.config = config
        self.app: Optional[CLIApplication] = None

    async def __aenter__(self) -> CLIApplication:
        """Initialize the application."""
        self.app = await initialize_application(self.config)
        return self.app

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Shutdown the application."""
        if self.app:
            await self.app.shutdown()
