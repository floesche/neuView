"""
Simplified core services for QuickPage application layer.

This module contains simplified orchestration services after refactoring
complex logic into specialized services in the services/ package.
"""

import logging
from typing import List

from .result import Result, Err
from .commands import FillQueueCommand, PopCommand

logger = logging.getLogger(__name__)


class QueueService:
    """Service for managing queue files with simplified logic."""

    def __init__(self, config):
        self.config = config
        # Load cached neuron types once during initialization
        self._cached_types: List[str] = self._load_cached_neuron_types()

    async def fill_queue(self, command: FillQueueCommand) -> Result[str, str]:
        """Create a YAML queue file with generate command options."""
        try:
            from .services.queue_file_manager import QueueFileManager

            queue_manager = QueueFileManager(self.config)

            if command.neuron_type is not None:
                # Single neuron type mode
                result = await queue_manager.create_single_queue_file(command)
                if result.is_ok():
                    # Update the central manifest.json file (only in single mode)
                    await queue_manager.update_cache_manifest(
                        [command.neuron_type.value]
                    )
                return result
            else:
                # Batch mode - discover neuron types
                return await self._create_batch_queue_files(command, queue_manager)

        except Exception as e:
            return Err(f"Failed to create queue file: {str(e)}")

    async def _create_batch_queue_files(
        self, command: FillQueueCommand, queue_manager
    ) -> Result[str, str]:
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
                # Use connector directly for filtered results
                discovered_types = connector.discover_neuron_types(
                    self.config.discovery
                )
                types = list(discovered_types)

                # Apply max_results limit if specified
                if command.max_types > 0:
                    types = types[: command.max_types]

            if not types:
                return Err("No neuron types found")
        except Exception as e:
            return Err(f"Failed to get neuron types: {str(e)}")

        # Create queue files for each type
        result = await queue_manager.create_batch_queue_files(command, types)
        if result.is_ok():
            # Update the central manifest.json file ONCE at the end
            await queue_manager.update_cache_manifest(types)
            # Reload cached types since we just updated the manifest
            self._cached_types = self._load_cached_neuron_types()

        return result

    async def pop_queue(self, command: PopCommand) -> Result[str, str]:
        """Pop and process a queue file."""
        from .services.queue_processor import QueueProcessor

        processor = QueueProcessor(self.config)
        return await processor.pop_and_process_queue(command)

    def _load_cached_neuron_types(self) -> List[str]:
        """Load cached neuron types from the cache manifest file."""
        from .services.queue_file_manager import QueueFileManager

        queue_manager = QueueFileManager(self.config)
        return queue_manager.load_cached_neuron_types()

    def get_cached_neuron_types(self) -> List[str]:
        """Get list of neuron types in the cache manifest."""
        return self._cached_types
