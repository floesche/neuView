"""
Neuron discovery service for the application layer.

This service handles neuron type discovery, search, and metadata retrieval.
It orchestrates business logic by coordinating between domain entities
and infrastructure services.
"""

from typing import List, Optional, Dict, Any
import asyncio
import logging

from ..commands import DiscoverNeuronTypesCommand
from ..queries import (
    GetNeuronTypeQuery, GetNeuronTypeQueryResult,
    ListNeuronTypesQuery, ListNeuronTypesQueryResult,
    NeuronTypeInfo
)
from ...core.ports import NeuronRepository, CacheRepository
from ...core.entities import NeuronCollection, NeuronTypeStatistics
from ...core.value_objects import NeuronTypeName, SomaSide
from ...shared.result import Result, Ok, Err


logger = logging.getLogger(__name__)


class NeuronDiscoveryService:
    """
    Application service for discovering and querying neuron data.

    This service handles neuron type discovery, search, and metadata retrieval.
    """

    def __init__(
        self,
        neuron_repo: NeuronRepository,
        cache_repo: Optional[CacheRepository] = None
    ):
        self.neuron_repo = neuron_repo
        self.cache_repo = cache_repo

    async def discover_neuron_types(
        self,
        command: DiscoverNeuronTypesCommand
    ) -> Result[List[NeuronTypeName], str]:
        """
        Discover available neuron types from the dataset.

        Args:
            command: The discovery command

        Returns:
            Result containing list of discovered neuron types or error message
        """
        try:
            # Validate command
            validation_errors = command.validate()
            if validation_errors:
                return Err(f"Invalid command: {', '.join(validation_errors)}")

            logger.info("Discovering neuron types")

            # Check cache first if available
            cache_key = self._build_discovery_cache_key(command)
            if self.cache_repo:
                cached_result = await self.cache_repo.get(cache_key)
                if cached_result:
                    logger.info("Retrieved neuron types from cache")
                    return Ok(cached_result)

            # Get all available types from repository
            all_types = await self.neuron_repo.get_available_types()

            # Apply filters
            filtered_types = self._apply_discovery_filters(all_types, command)

            # Apply sorting and limiting
            final_types = self._apply_discovery_sorting_and_limiting(filtered_types, command)

            # Cache the result if cache is available
            if self.cache_repo:
                await self.cache_repo.set(cache_key, final_types, ttl=3600)  # 1 hour TTL

            logger.info(f"Discovered {len(final_types)} neuron types")
            return Ok(final_types)

        except Exception as e:
            error_msg = f"Failed to discover neuron types: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Err(error_msg)

    async def get_neuron_type_details(
        self,
        query: GetNeuronTypeQuery
    ) -> Result[GetNeuronTypeQueryResult, str]:
        """
        Get detailed information about a specific neuron type.

        Args:
            query: The neuron type query

        Returns:
            Result containing neuron type details or error message
        """
        try:
            # Validate query
            validation_errors = query.validate()
            if validation_errors:
                return Err(f"Invalid query: {', '.join(validation_errors)}")

            logger.info(f"Getting details for neuron type {query.neuron_type}")

            # Get neuron collection
            if query.soma_side and query.soma_side.value != 'all':
                neuron_collection = await self.neuron_repo.find_by_type_and_side(
                    query.neuron_type, query.soma_side
                )
            else:
                neuron_collection = await self.neuron_repo.find_by_type(query.neuron_type)

            # Filter by minimum synapse count if specified
            if query.min_synapse_count > 0:
                filtered_neurons = [
                    neuron for neuron in neuron_collection.neurons
                    if neuron.get_total_synapses().value >= query.min_synapse_count
                ]
                neuron_collection.neurons = filtered_neurons

            # Calculate statistics
            statistics = neuron_collection.calculate_statistics()

            result = GetNeuronTypeQueryResult(
                neuron_collection=neuron_collection,
                statistics=statistics
            )

            return Ok(result)

        except Exception as e:
            error_msg = f"Failed to get neuron type details: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Err(error_msg)

    async def list_neuron_types(
        self,
        query: ListNeuronTypesQuery
    ) -> Result[ListNeuronTypesQueryResult, str]:
        """
        List available neuron types with metadata.

        Args:
            query: The list query

        Returns:
            Result containing list of neuron types with metadata or error message
        """
        try:
            # Validate query
            validation_errors = query.validate()
            if validation_errors:
                return Err(f"Invalid query: {', '.join(validation_errors)}")

            logger.info("Listing neuron types")

            # Get all available types
            all_types = await self.neuron_repo.get_available_types()

            # Get soma sides if requested
            types_with_sides = {}
            if query.include_soma_sides:
                types_with_sides = await self.neuron_repo.get_types_with_soma_sides()

            # Build neuron type info list
            neuron_type_infos = []
            for neuron_type in all_types:
                # Apply filter if specified
                if query.filter_pattern:
                    if query.filter_pattern.lower() not in str(neuron_type).lower():
                        continue

                # Check exclusion list
                if str(neuron_type) in query.exclude_types:
                    continue

                # Get available soma sides
                available_sides = types_with_sides.get(neuron_type, [])

                # Get statistics if requested
                statistics = None
                if query.include_statistics:
                    collection = await self.neuron_repo.find_by_type(neuron_type)
                    statistics = collection.calculate_statistics()

                info = NeuronTypeInfo(
                    name=neuron_type,
                    available_soma_sides=available_sides,
                    total_count=statistics.total_count if statistics else 0,
                    statistics=statistics
                )
                neuron_type_infos.append(info)

            # Apply sorting
            if query.sort_by == "name":
                neuron_type_infos.sort(key=lambda x: str(x.name))
            elif query.sort_by == "count":
                neuron_type_infos.sort(key=lambda x: x.total_count, reverse=True)
            elif query.sort_by == "random":
                import random
                random.shuffle(neuron_type_infos)

            # Apply limit
            neuron_type_infos = neuron_type_infos[:query.max_results]

            result = ListNeuronTypesQueryResult(
                neuron_types=neuron_type_infos,
                total_available=len(all_types)
            )

            return Ok(result)

        except Exception as e:
            error_msg = f"Failed to list neuron types: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Err(error_msg)

    def _apply_discovery_filters(
        self,
        types: List[NeuronTypeName],
        command: DiscoverNeuronTypesCommand
    ) -> List[NeuronTypeName]:
        """Apply filtering logic to neuron types."""
        filtered_types = types.copy()

        # Apply pattern filter
        if command.type_filter_pattern:
            filtered_types = [
                t for t in filtered_types
                if command.type_filter_pattern.lower() in str(t).lower()
            ]

        # Apply include_only filter
        if command.include_only:
            filtered_types = [
                t for t in filtered_types
                if str(t) in command.include_only
            ]

        # Apply exclude filter
        if command.exclude_types:
            filtered_types = [
                t for t in filtered_types
                if str(t) not in command.exclude_types
            ]

        return filtered_types

    def _apply_discovery_sorting_and_limiting(
        self,
        types: List[NeuronTypeName],
        command: DiscoverNeuronTypesCommand
    ) -> List[NeuronTypeName]:
        """Apply sorting and limiting logic."""
        if command.randomize:
            import random
            random.shuffle(types)
        else:
            types.sort(key=str)

        return types[:command.max_types]

    def _build_discovery_cache_key(self, command: DiscoverNeuronTypesCommand) -> str:
        """Build a cache key for the discovery command."""
        key_parts = [
            "discovery",
            str(command.max_types),
            command.type_filter_pattern or "no-filter",
            ",".join(sorted(command.exclude_types)),
            ",".join(sorted(command.include_only)),
            str(command.randomize),
            str(command.min_neuron_count)
        ]
        return ":".join(key_parts)
