"""
Simplified core services for QuickPage application layer.

This module contains simplified orchestration services after refactoring
complex logic into specialized services in the services/ package.
"""

import asyncio
import logging
from typing import List
from pathlib import Path
from datetime import datetime
import yaml

from .models import NeuronTypeName, SomaSide
from .result import Result, Ok, Err
from .commands import (
    GeneratePageCommand, TestConnectionCommand, FillQueueCommand,
    PopCommand, CreateListCommand, DatasetInfo
)

logger = logging.getLogger(__name__)


class QueueService:
    """Service for managing queue files with simplified logic."""

    def __init__(self, config):
        self.config = config
        # Load queued neuron types once during initialization
        self._queued_types: List[str] = self._load_queued_neuron_types()

    async def fill_queue(self, command: FillQueueCommand) -> Result[str, str]:
        """Create a YAML queue file with generate command options."""
        try:
            from .services.queue_file_manager import QueueFileManager
            queue_manager = QueueFileManager(self.config)

            if command.neuron_type is not None:
                # Single neuron type mode
                result = await queue_manager.create_single_queue_file(command)
                if result.is_ok():
                    # Update the central queue.yaml file (only in single mode)
                    await queue_manager.update_queue_manifest([command.neuron_type.value])
                return result
            else:
                # Batch mode - discover neuron types
                return await self._create_batch_queue_files(command, queue_manager)

        except Exception as e:
            return Err(f"Failed to create queue file: {str(e)}")

    async def _create_batch_queue_files(self, command: FillQueueCommand, queue_manager) -> Result[str, str]:
        """Create queue files for multiple neuron types."""
        from .neuprint_connector import NeuPrintConnector

        # Create connector for type discovery (optimized)
        connector = NeuPrintConnector(self.config)

        try:
            if command.all_types:
                # Optimized path: directly get all types without discovery service overhead
                type_names = connector.get_available_types()
                types = [type_name for type_name in type_names]
            else:
                # Use discovery service for filtered results
                from .services.neuron_discovery_service import NeuronDiscoveryService, ListNeuronTypesCommand
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
                type_infos = list_result.unwrap()
                types = [type_info.name for type_info in type_infos]

            if not types:
                return Err("No neuron types found")
        except Exception as e:
            return Err(f"Failed to get neuron types: {str(e)}")

        # Create queue files for each type
        result = await queue_manager.create_batch_queue_files(command, types)
        if result.is_ok():
            # Update the central queue.yaml file ONCE at the end
            await queue_manager.update_queue_manifest(types)
            # Reload queued types since we just updated the manifest
            self._queued_types = self._load_queued_neuron_types()

        return result

    async def pop_queue(self, command: PopCommand) -> Result[str, str]:
        """Pop and process a queue file."""
        from .services.queue_processor import QueueProcessor
        processor = QueueProcessor(self.config)
        return await processor.pop_and_process_queue(command)

    def _load_queued_neuron_types(self) -> List[str]:
        """Load queued neuron types from the queue manifest file."""
        from .services.queue_file_manager import QueueFileManager
        queue_manager = QueueFileManager(self.config)
        return queue_manager.load_queued_neuron_types()

    def get_queued_neuron_types(self) -> List[str]:
        """Get list of neuron types in the queue manifest."""
        return self._queued_types


class ServiceContainer:
    """Simple service container for dependency management."""

    def __init__(self, config):
        self.config = config
        self._services = {}

    def _get_or_create_service(self, service_name: str, factory_func):
        """Generic method to get or create a service."""
        if service_name not in self._services:
            self._services[service_name] = factory_func()
        return self._services[service_name]

    @property
    def neuprint_connector(self):
        """Get or create NeuPrint connector."""
        def create():
            from .neuprint_connector import NeuPrintConnector
            return NeuPrintConnector(self.config)
        return self._get_or_create_service('neuprint_connector', create)

    @property
    def page_generator(self):
        """Get or create page generator."""
        def create():
            from .page_generator import PageGenerator
            return PageGenerator(
                self.config,
                self.config.output.directory,
                self.queue_service,
                self.cache_manager
            )
        return self._get_or_create_service('page_generator', create)

    @property
    def cache_manager(self):
        """Get or create cache manager."""
        def create():
            from .cache import create_cache_manager
            return create_cache_manager(self.config.output.directory)
        return self._get_or_create_service('cache_manager', create)

    @property
    def page_service(self):
        """Get or create page generation service."""
        def create():
            from .services.page_generation_service import PageGenerationService
            return PageGenerationService(
                self.neuprint_connector,
                self.page_generator,
                self.config
            )
        return self._get_or_create_service('page_service', create)

    @property
    def discovery_service(self):
        """Get or create neuron discovery service."""
        def create():
            from .services import NeuronDiscoveryService, ROIAnalysisService, NeuronNameService

            # Create ROI analysis service for enriched discovery
            roi_analysis_service = ROIAnalysisService(
                self.page_generator,
                self.roi_hierarchy_service
            )

            # Create neuron name service for filename conversion
            neuron_name_service = NeuronNameService(self.cache_manager)

            return NeuronDiscoveryService(
                self.neuprint_connector,
                self.config,
                roi_analysis_service=roi_analysis_service,
                neuron_name_service=neuron_name_service
            )
        return self._get_or_create_service('discovery_service', create)

    @property
    def connection_service(self):
        """Get or create connection test service."""
        def create():
            from .services.connection_test_service import ConnectionTestService
            return ConnectionTestService(self.neuprint_connector)
        return self._get_or_create_service('connection_service', create)

    @property
    def queue_service(self):
        """Get or create queue service."""
        def create():
            return QueueService(self.config)
        return self._get_or_create_service('queue_service', create)

    @property
    def roi_hierarchy_service(self):
        """Get or create ROI hierarchy service."""
        def create():
            from .services import ROIHierarchyService
            return ROIHierarchyService(self.config, self.cache_manager)
        return self._get_or_create_service('roi_hierarchy_service', create)

    @property
    def index_service(self):
        """Get or create index service."""
        def create():
            from .services import IndexService
            return IndexService(self.config, self.page_generator)
        return self._get_or_create_service('index_service', create)

    def cleanup(self):
        """Clean up services and resources."""
        # Close any connections or clean up resources
        if 'neuprint_connector' in self._services:
            # Add any cleanup logic for the connector if needed
            pass

        # Clear all service references
        self._services.clear()
