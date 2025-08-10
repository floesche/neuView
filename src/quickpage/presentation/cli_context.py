"""
CLI context class for the presentation layer.

This module contains the CLIContext class which manages shared state
and service dependencies for the command line interface.
"""

import logging
from typing import Optional

from ..config import Config
from ..application.services import (
    PageGenerationService, NeuronDiscoveryService, ConnectionTestService
)
from ..infrastructure.repositories import (
    NeuPrintNeuronRepository, NeuPrintConnectivityRepository
)
from ..shared.container import get_container, setup_container

logger = logging.getLogger(__name__)


class CLIContext:
    """Context object to hold shared CLI state."""

    def __init__(self, config: Config, verbose: bool = False):
        self.config = config
        self.verbose = verbose
        self.container = setup_container(get_container())
        self._setup_services()

    def _setup_services(self):
        """Set up service dependencies in the container."""
        # Register repositories
        neuron_repo = NeuPrintNeuronRepository(self.config)
        connectivity_repo = NeuPrintConnectivityRepository(self.config)

        self.container.register_singleton(
            NeuPrintNeuronRepository, neuron_repo
        )
        self.container.register_singleton(
            NeuPrintConnectivityRepository, connectivity_repo
        )

        # Register application services
        self.container.register_transient(
            PageGenerationService, PageGenerationService
        )
        self.container.register_transient(
            NeuronDiscoveryService, NeuronDiscoveryService
        )
        self.container.register_transient(
            ConnectionTestService, ConnectionTestService
        )

    def get_page_generation_service(self) -> PageGenerationService:
        """Get the page generation service."""
        # For now, create manually - in full implementation would use container
        neuron_repo = self.container.resolve(NeuPrintNeuronRepository)
        connectivity_repo = self.container.resolve(NeuPrintConnectivityRepository)

        # TODO: Add template engine and file storage implementations
        return PageGenerationService(
            neuron_repo=neuron_repo,
            connectivity_repo=connectivity_repo,
            template_engine=None,  # Will be implemented in infrastructure
            file_storage=None      # Will be implemented in infrastructure
        )

    def get_discovery_service(self) -> NeuronDiscoveryService:
        """Get the neuron discovery service."""
        neuron_repo = self.container.resolve(NeuPrintNeuronRepository)
        return NeuronDiscoveryService(neuron_repo=neuron_repo)

    def get_connection_service(self) -> ConnectionTestService:
        """Get the connection test service."""
        neuron_repo = self.container.resolve(NeuPrintNeuronRepository)
        return ConnectionTestService(neuron_repo=neuron_repo)
