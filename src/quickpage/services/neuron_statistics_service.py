"""
Neuron Statistics Service

Provides modern, service-oriented access to neuron statistics and metadata.
Offers a clean service interface for neuron type analysis and statistics.
"""

import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass

from ..models import NeuronTypeName, SomaSide, NeuronTypeStatistics
from ..result import Result, Ok, Err

logger = logging.getLogger(__name__)


@dataclass
class NeuronStatsQuery:
    """Query parameters for neuron statistics."""
    neuron_type: str
    soma_side: Optional[str] = None
    include_synapse_stats: bool = True
    include_roi_stats: bool = False


class NeuronStatisticsService:
    """Service for retrieving neuron statistics without legacy class dependencies."""

    def __init__(self, connector):
        """
        Initialize the neuron statistics service.

        Args:
            connector: NeuPrint connector for data access
        """
        self.connector = connector

    async def get_neuron_count(self, neuron_type: str, soma_side: Optional[str] = None) -> Result[int, str]:
        """
        Get the count of neurons for a specific type and optional soma side.

        Args:
            neuron_type: The neuron type name
            soma_side: Optional soma side filter ('left', 'right', 'middle', 'combined')

        Returns:
            Result containing the neuron count or error message
        """
        try:
            # Use combined if no specific side requested
            side = soma_side or 'combined'

            data = self.connector.get_neuron_data(neuron_type, side)
            if not data or 'neurons' not in data:
                return Ok(0)

            neurons_df = data['neurons']
            if neurons_df is None or neurons_df.empty:
                return Ok(0)

            # If requesting a specific side and we got combined data, filter
            if soma_side and soma_side != 'combined':
                if 'somaSide' in neurons_df.columns:
                    side_key = soma_side[0].upper() if soma_side in ['left', 'right', 'middle'] else soma_side
                    filtered = neurons_df[neurons_df['somaSide'] == side_key]
                    return Ok(len(filtered))

            return Ok(len(neurons_df))

        except Exception as e:
            logger.error(f"Failed to get neuron count for {neuron_type}: {e}")
            return Err(f"Failed to get neuron count: {str(e)}")

    async def get_soma_side_distribution(self, neuron_type: str) -> Result[Dict[str, int], str]:
        """
        Get the distribution of neurons across soma sides.

        Args:
            neuron_type: The neuron type name

        Returns:
            Result containing soma side counts or error message
        """
        try:
            # First try the connector's direct method if available
            if hasattr(self.connector, 'get_soma_side_distribution'):
                distribution = self.connector.get_soma_side_distribution(neuron_type)
                if distribution:
                    return Ok(distribution)

            # Fallback: get combined data and calculate distribution
            data = self.connector.get_neuron_data(neuron_type, 'combined')
            if not data or 'neurons' not in data:
                return Ok({})

            neurons_df = data['neurons']
            if neurons_df is None or neurons_df.empty or 'somaSide' not in neurons_df.columns:
                return Ok({})

            # Count by soma side
            counts = {}
            for side_code in ['L', 'R', 'M']:
                side_neurons = neurons_df[neurons_df['somaSide'] == side_code]
                side_name = {'L': 'left', 'R': 'right', 'M': 'middle'}[side_code]
                counts[side_name] = len(side_neurons)

            # Add total
            counts['total'] = len(neurons_df)

            return Ok(counts)

        except Exception as e:
            logger.error(f"Failed to get soma distribution for {neuron_type}: {e}")
            return Err(f"Failed to get soma distribution: {str(e)}")

    async def get_synapse_statistics(self, neuron_type: str, soma_side: Optional[str] = None) -> Result[Dict[str, float], str]:
        """
        Get synapse statistics for a neuron type.

        Args:
            neuron_type: The neuron type name
            soma_side: Optional soma side filter

        Returns:
            Result containing synapse statistics or error message
        """
        try:
            side = soma_side or 'combined'

            data = self.connector.get_neuron_data(neuron_type, side)
            if not data or 'neurons' not in data:
                return Ok({})

            neurons_df = data['neurons']
            if neurons_df is None or neurons_df.empty:
                return Ok({})

            # Filter by soma side if specified and we have combined data
            if soma_side and soma_side != 'combined' and 'somaSide' in neurons_df.columns:
                side_key = soma_side[0].upper() if soma_side in ['left', 'right', 'middle'] else soma_side
                neurons_df = neurons_df[neurons_df['somaSide'] == side_key]

            if neurons_df.empty:
                return Ok({})

            # Calculate synapse statistics
            stats = {}

            if 'pre' in neurons_df.columns:
                stats['avg_pre'] = float(neurons_df['pre'].mean())
                stats['total_pre'] = int(neurons_df['pre'].sum())
                stats['max_pre'] = int(neurons_df['pre'].max())
                stats['min_pre'] = int(neurons_df['pre'].min())

            if 'post' in neurons_df.columns:
                stats['avg_post'] = float(neurons_df['post'].mean())
                stats['total_post'] = int(neurons_df['post'].sum())
                stats['max_post'] = int(neurons_df['post'].max())
                stats['min_post'] = int(neurons_df['post'].min())

            # Combined average
            if 'pre' in neurons_df.columns and 'post' in neurons_df.columns:
                stats['avg_total'] = stats.get('avg_pre', 0) + stats.get('avg_post', 0)

            return Ok(stats)

        except Exception as e:
            logger.error(f"Failed to get synapse stats for {neuron_type}: {e}")
            return Err(f"Failed to get synapse statistics: {str(e)}")

    async def has_data(self, neuron_type: str, soma_side: Optional[str] = None) -> Result[bool, str]:
        """
        Check if a neuron type has available data.

        Args:
            neuron_type: The neuron type name
            soma_side: Optional soma side filter

        Returns:
            Result containing boolean indicating data availability
        """
        count_result = await self.get_neuron_count(neuron_type, soma_side)
        if count_result.is_err():
            return Err(count_result.unwrap_err())

        return Ok(count_result.unwrap() > 0)

    async def get_comprehensive_statistics(self, neuron_type: str, soma_side: SomaSide = SomaSide.COMBINED) -> Result[NeuronTypeStatistics, str]:
        """
        Get comprehensive statistics for a neuron type.

        Args:
            neuron_type: The neuron type name
            soma_side: Soma side specification

        Returns:
            Result containing comprehensive statistics or error message
        """
        try:
            type_name = NeuronTypeName(neuron_type) if not isinstance(neuron_type, NeuronTypeName) else neuron_type

            # Get total count
            total_count_result = await self.get_neuron_count(neuron_type, 'combined')
            if total_count_result.is_err():
                return Err(total_count_result.unwrap_err())

            total_count = total_count_result.unwrap()

            # Get soma side distribution
            soma_dist_result = await self.get_soma_side_distribution(neuron_type)
            if soma_dist_result.is_err():
                return Err(soma_dist_result.unwrap_err())

            soma_counts = soma_dist_result.unwrap()

            # Get synapse statistics for the requested side
            soma_side_str = soma_side.value if soma_side != SomaSide.ALL else 'combined'
            synapse_result = await self.get_synapse_statistics(neuron_type, soma_side_str)
            if synapse_result.is_err():
                return Err(synapse_result.unwrap_err())

            synapse_stats = synapse_result.unwrap()

            # Create comprehensive statistics object
            stats = NeuronTypeStatistics(
                type_name=type_name,
                total_count=total_count,
                soma_side_counts=soma_counts,
                synapse_stats=synapse_stats
            )

            return Ok(stats)

        except Exception as e:
            logger.error(f"Failed to get comprehensive statistics for {neuron_type}: {e}")
            return Err(f"Failed to get comprehensive statistics: {str(e)}")

    async def check_neuron_type_exists(self, neuron_type: str) -> Result[bool, str]:
        """
        Check if a neuron type exists in the database.

        Args:
            neuron_type: The neuron type name to check

        Returns:
            Result containing boolean indicating existence
        """
        return await self.has_data(neuron_type)

    async def get_basic_info(self, neuron_type: str) -> Result[Dict[str, Any], str]:
        """
        Get basic information about a neuron type for quick checks.

        Args:
            neuron_type: The neuron type name

        Returns:
            Result containing basic info dictionary
        """
        try:
            count_result = await self.get_neuron_count(neuron_type)
            if count_result.is_err():
                return Err(count_result.unwrap_err())

            count = count_result.unwrap()
            exists = count > 0

            info = {
                'name': neuron_type,
                'exists': exists,
                'count': count
            }

            # Add soma distribution if data exists
            if exists:
                soma_result = await self.get_soma_side_distribution(neuron_type)
                if soma_result.is_ok():
                    info['soma_sides'] = soma_result.unwrap()

            return Ok(info)

        except Exception as e:
            logger.error(f"Failed to get basic info for {neuron_type}: {e}")
            return Err(f"Failed to get basic info: {str(e)}")
