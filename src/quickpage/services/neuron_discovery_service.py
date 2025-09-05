"""
Neuron Discovery Service

Handles discovery and inspection of available neuron types in the database.
Extracted from core_services.py to improve separation of concerns.
Uses existing services for ROI analysis and neuron naming.
"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass

from ..models import NeuronTypeName, SomaSide, NeuronTypeStatistics
from ..result import Result, Ok, Err

logger = logging.getLogger(__name__)


@dataclass
class InspectNeuronTypeCommand:
    """Command to inspect detailed neuron type information."""
    neuron_type: NeuronTypeName
    soma_side: SomaSide = SomaSide.COMBINED

    def __post_init__(self):
        if not isinstance(self.neuron_type, NeuronTypeName):
            self.neuron_type = NeuronTypeName(str(self.neuron_type))
        if not isinstance(self.soma_side, SomaSide):
            self.soma_side = SomaSide.from_string(str(self.soma_side))


class NeuronDiscoveryService:
    """Service for discovering available neuron types."""

    def __init__(self, neuprint_connector, config, neuron_statistics_service, roi_analysis_service=None, neuron_name_service=None):
        self.connector = neuprint_connector
        self.config = config
        if not neuron_statistics_service:
            raise ValueError("Neuron statistics service is required")
        self.neuron_statistics_service = neuron_statistics_service
        self.roi_analysis_service = roi_analysis_service
        self.neuron_name_service = neuron_name_service

    async def inspect_neuron_type(self, command: InspectNeuronTypeCommand) -> Result[NeuronTypeStatistics, str]:
        """Inspect detailed information about a neuron type."""
        try:
            # Use modern statistics service
            return await self.neuron_statistics_service.get_comprehensive_statistics(
                command.neuron_type.value,
                command.soma_side
            )

        except Exception as e:
            return Err(f"Failed to inspect neuron type: {str(e)}")

    def get_filename_for_neuron_type(self, neuron_type_name: str) -> str:
        """Get the filename for a neuron type using the neuron name service."""
        if self.neuron_name_service:
            return self.neuron_name_service.neuron_name_to_filename(neuron_type_name)
        else:
            # Fallback to simple conversion
            return neuron_type_name.replace('/', '_').replace(' ', '_')
