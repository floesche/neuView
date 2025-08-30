"""
Neuron Discovery Service

Handles discovery and inspection of available neuron types in the database.
Extracted from core_services.py to improve separation of concerns.
Uses existing services for ROI analysis and neuron naming.
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

from ..models import NeuronTypeName, SomaSide, NeuronTypeStatistics
from ..result import Result, Ok, Err

logger = logging.getLogger(__name__)


@dataclass
class ListNeuronTypesCommand:
    """Command to list available neuron types."""
    max_results: int = 10
    all_results: bool = False
    sorted_results: bool = False
    show_soma_sides: bool = False
    show_statistics: bool = False
    filter_pattern: Optional[str] = None
    exclude_empty: bool = True
    with_roi_enrichment: bool = False


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


@dataclass
class NeuronTypeInfo:
    """Information about a neuron type."""
    name: str
    count: int = 0
    soma_sides: Optional[Dict[str, int]] = None
    avg_synapses: float = 0.0
    primary_roi: Optional[str] = None
    parent_roi: Optional[str] = None

    def __post_init__(self):
        if self.soma_sides is None:
            self.soma_sides = {}


class NeuronDiscoveryService:
    """Service for discovering available neuron types."""

    def __init__(self, neuprint_connector, config, roi_analysis_service=None, neuron_name_service=None):
        self.connector = neuprint_connector
        self.config = config
        self.roi_analysis_service = roi_analysis_service
        self.neuron_name_service = neuron_name_service

    async def list_neuron_types(self, command: ListNeuronTypesCommand) -> Result[List[NeuronTypeInfo], str]:
        """List available neuron types."""
        # If ROI enrichment is requested and we have the service, use the enhanced method
        if command.with_roi_enrichment and self.roi_analysis_service:
            return await self.get_neuron_types_with_roi_enrichment(command)

        try:
            # Use the discovery configuration from config, but override max_types if --all is specified
            discovery_config = self.config.discovery
            if command.all_results:
                from dataclasses import replace
                discovery_config = replace(discovery_config, max_types=999999)

            discovered_types = self.connector.discover_neuron_types(discovery_config)
            # Convert to NeuronTypeInfo objects
            type_infos = []
            for type_name in discovered_types:
                info = NeuronTypeInfo(name=type_name)

                # If statistics are requested, get them (but don't fail if we can't)
                if command.show_statistics:
                    try:
                        # Try to get basic neuron count using the legacy method
                        from ..neuron_type import NeuronType
                        from ..config import NeuronTypeConfig

                        config = NeuronTypeConfig(name=type_name, description=f"{type_name} neurons")
                        neuron_type_obj = NeuronType(type_name, config, self.connector, soma_side='combined')

                        if neuron_type_obj.has_data():
                            info.count = neuron_type_obj.get_neuron_count()
                            synapse_stats = neuron_type_obj.get_synapse_stats()
                            info.avg_synapses = synapse_stats.get('avg_pre', 0.0) + synapse_stats.get('avg_post', 0.0)
                    except Exception:
                        # If we can't get stats, skip this type when show_statistics is requested
                        continue

                # If soma sides are requested, get them
                if command.show_soma_sides:
                    try:
                        soma_data = self.connector.get_soma_side_distribution(type_name)
                        if soma_data:
                            info.soma_sides = soma_data
                    except Exception:
                        pass  # Skip if we can't get soma data

                type_infos.append(info)

            # Filter by pattern if specified
            if command.filter_pattern:
                import re
                pattern = re.compile(command.filter_pattern, re.IGNORECASE)
                type_infos = [info for info in type_infos if pattern.search(info.name)]

            # Exclude empty types if requested (only if we have count data)
            if command.exclude_empty and command.show_statistics:
                type_infos = [info for info in type_infos if info.count > 0]

            # Sort if requested
            if command.sorted_results:
                type_infos.sort(key=lambda x: x.name)

            # Limit results (unless --all is specified)
            if not command.all_results and command.max_results > 0:
                type_infos = type_infos[:command.max_results]
            return Ok(type_infos)

        except Exception as e:
            return Err(f"Failed to list neuron types: {str(e)}")

    async def inspect_neuron_type(self, command: InspectNeuronTypeCommand) -> Result[NeuronTypeStatistics, str]:
        """Inspect detailed information about a neuron type."""
        try:
            # Import legacy components
            from ..neuron_type import NeuronType
            from ..config import NeuronTypeConfig

            # Create NeuronType instance
            config = NeuronTypeConfig(
                name=command.neuron_type.value,
                description=f"{command.neuron_type.value} neurons"
            )

            # Convert SomaSide enum to legacy format
            if command.soma_side in [SomaSide.ALL, SomaSide.COMBINED]:
                legacy_soma_side = 'combined'
            elif command.soma_side == SomaSide.LEFT:
                legacy_soma_side = 'left'
            elif command.soma_side == SomaSide.RIGHT:
                legacy_soma_side = 'right'
            elif command.soma_side == SomaSide.MIDDLE:
                legacy_soma_side = 'middle'
            else:
                legacy_soma_side = 'combined'

            neuron_type_obj = NeuronType(
                command.neuron_type.value,
                config,
                self.connector,
                soma_side=legacy_soma_side
            )

            # Check if we have data
            if not neuron_type_obj.has_data():
                return Err(f"No neurons found for type {command.neuron_type}")

            # Gather statistics
            neuron_count = neuron_type_obj.get_neuron_count()
            soma_counts = {
                "left": neuron_type_obj.get_neuron_count('left'),
                "right": neuron_type_obj.get_neuron_count('right'),
                "middle": neuron_type_obj.get_neuron_count('middle')
            }
            synapse_stats = neuron_type_obj.get_synapse_stats()

            # Create statistics object
            stats = NeuronTypeStatistics(
                type_name=command.neuron_type,
                total_count=neuron_count,
                soma_side_counts=soma_counts,
                synapse_stats=synapse_stats
            )

            return Ok(stats)

        except Exception as e:
            return Err(f"Failed to inspect neuron type: {str(e)}")

    async def get_neuron_types_with_roi_enrichment(self, command: ListNeuronTypesCommand) -> Result[List[NeuronTypeInfo], str]:
        """Get neuron types enriched with ROI summary data using existing services."""
        try:
            # First get the basic neuron type list
            basic_result = await self.list_neuron_types(command)
            if basic_result.is_err():
                return basic_result

            type_infos = basic_result.unwrap()

            # If we have ROI analysis service, enrich with ROI data
            if self.roi_analysis_service:
                for info in type_infos:
                    try:
                        roi_summary, parent_roi = self.roi_analysis_service.get_roi_summary_for_neuron_type(
                            info.name, self.connector, skip_roi_analysis=False
                        )
                        # Add ROI info to the neuron type info
                        if roi_summary:
                            info.primary_roi = roi_summary[0]['name'] if roi_summary else None
                            info.parent_roi = parent_roi
                    except Exception as e:
                        logger.debug(f"Failed to get ROI data for {info.name}: {e}")
                        continue

            return Ok(type_infos)

        except Exception as e:
            return Err(f"Failed to get enriched neuron types: {str(e)}")

    def get_filename_for_neuron_type(self, neuron_type_name: str) -> str:
        """Get the filename for a neuron type using the neuron name service."""
        if self.neuron_name_service:
            return self.neuron_name_service.neuron_name_to_filename(neuron_type_name)
        else:
            # Fallback to simple conversion
            return neuron_type_name.replace('/', '_').replace(' ', '_')
