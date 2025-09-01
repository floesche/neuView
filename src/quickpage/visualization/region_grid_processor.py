"""
Region grid processor for handling region-specific eyemap generation logic.

This module provides a service class that handles the complex logic of processing
regions and sides for eyemap generation, including mirroring, filtering, and
grid generation coordination.
"""

import logging
from typing import Dict, List, Set, Tuple

from .constants import REGION_ORDER
from .data_processing import DataProcessor
from .data_transfer_objects import (
    GridGenerationRequest, SingleRegionGridRequest,
    create_single_region_request
)

logger = logging.getLogger(__name__)


class RegionGridProcessor:
    """
    Service class for processing regions and sides in eyemap generation.

    This class encapsulates the complex logic of iterating through regions
    and sides, applying mirroring logic, filtering columns, and coordinating
    the generation of individual region grids.
    """

    def __init__(self, data_processor: DataProcessor):
        """
        Initialize the region grid processor.

        Args:
            data_processor: DataProcessor instance for handling data operations
        """
        self.data_processor = data_processor

    def process_all_regions_and_sides(self, request: GridGenerationRequest,
                                    data_maps: Dict, grid_generator_func) -> Dict:
        """
        Process all regions and sides to generate comprehensive grids.

        Args:
            request: GridGenerationRequest containing all generation parameters
            data_maps: Dictionary mapping sides to their organized data maps
            grid_generator_func: Function to call for generating individual grids

        Returns:
            Dictionary mapping region_side keys to their generated grids
        """
        region_grids = {}

        # Generate grids for each region and side
        for region in REGION_ORDER:
            for side, data_map in data_maps.items():
                logger.debug(f"Processing region {region}, side {side}")

                # Process this specific region and side combination
                region_side_grids = self._process_single_region_side(
                    request, region, side, data_map, grid_generator_func
                )

                region_side_key = f"{region}_{side}"
                region_grids[region_side_key] = region_side_grids

        return region_grids

    def _process_single_region_side(self, request: GridGenerationRequest,
                                  region: str, side: str, data_map: Dict,
                                  grid_generator_func) -> Dict:
        """
        Process a single region and side combination.

        Args:
            request: GridGenerationRequest containing all generation parameters
            region: Region name (e.g., 'ME', 'LO', 'LOP')
            side: Side identifier ('L' or 'R')
            data_map: Organized data map for this side
            grid_generator_func: Function to call for generating individual grids

        Returns:
            Dictionary with generated grid content for this region/side
        """
        # Get region-specific configuration
        region_config = self._get_region_configuration(request, region, side)

        # Generate grids for both metrics
        synapse_content, cell_content = self._generate_metric_grids(
            request, region, side, data_map, region_config, grid_generator_func
        )

        return {
            'synapse_content': synapse_content,
            'cell_content': cell_content,
            'region': region,
            'side': side
        }

    def _get_region_configuration(self, request: GridGenerationRequest,
                                region: str, side: str) -> Dict:
        """
        Get configuration specific to a region and side combination.

        Args:
            request: GridGenerationRequest containing all generation parameters
            region: Region name
            side: Side identifier

        Returns:
            Dictionary containing region-specific configuration
        """
        region_side_key = f"{region}_{side}"
        region_column_coords = request.region_columns_map.get(region_side_key, set())

        # Determine mirroring based on soma side and current side
        mirror_side = self.determine_mirror_side(request.soma_side, side)

        # Get other regions' column coordinates for the same soma side
        other_regions_coords = self.data_processor._get_other_regions_coords(
            request.region_columns_map, region, side
        )

        # Filter all_possible_columns to only include columns relevant for this soma side
        side_filtered_columns = self.data_processor._filter_columns_for_side(
            request.all_possible_columns, request.region_columns_map, region, side
        )

        return {
            'region_column_coords': region_column_coords,
            'mirror_side': mirror_side,
            'other_regions_coords': other_regions_coords,
            'side_filtered_columns': side_filtered_columns
        }

    def _generate_metric_grids(self, request: GridGenerationRequest, region: str,
                             side: str, data_map: Dict, region_config: Dict,
                             grid_generator_func) -> Tuple[str, str]:
        """
        Generate synapse and cell grids for a specific region and side.

        Args:
            request: GridGenerationRequest containing all generation parameters
            region: Region name
            side: Side identifier
            data_map: Organized data map for this side
            region_config: Region-specific configuration
            grid_generator_func: Function to call for generating individual grids

        Returns:
            Tuple of (synapse_content, cell_content)
        """
        # Create requests for single region grid generation
        synapse_request = self._create_metric_request(
            request, region, data_map, region_config, 'synapse_density'
        )

        cell_request = self._create_metric_request(
            request, region, data_map, region_config, 'cell_count'
        )

        # Generate the grids
        synapse_content = grid_generator_func(synapse_request)
        cell_content = grid_generator_func(cell_request)

        return synapse_content, cell_content

    def _create_metric_request(self, request: GridGenerationRequest, region: str,
                             data_map: Dict, region_config: Dict,
                             metric_type: str) -> SingleRegionGridRequest:
        """
        Create a SingleRegionGridRequest for a specific metric type.

        Args:
            request: Original GridGenerationRequest
            region: Region name
            data_map: Data map for the current side
            region_config: Region-specific configuration
            metric_type: Either 'synapse_density' or 'cell_count'

        Returns:
            SingleRegionGridRequest for the specified metric
        """
        # Select appropriate thresholds based on metric type
        if metric_type == 'synapse_density':
            thresholds = request.thresholds_all['total_synapses']
        else:  # cell_count
            thresholds = request.thresholds_all['neuron_count']

        return create_single_region_request(
            region_config['side_filtered_columns'],
            region_config['region_column_coords'],
            data_map,
            metric_type,
            region,
            thresholds=thresholds,
            neuron_type=request.neuron_type,
            soma_side=region_config['mirror_side'],
            output_format=request.output_format,
            other_regions_coords=region_config['other_regions_coords'],
            min_max_data=request.min_max_data
        )

    def determine_mirror_side(self, soma_side: str, current_side: str) -> str:
        """
        Determine if mirroring should be applied based on soma side and current side.

        Args:
            soma_side: The soma side from the request ('left', 'right', 'combined')
            current_side: The current processing side ('L' or 'R')

        Returns:
            Mirror side string ('left' or 'right')
        """
        # Determine if mirroring should be applied:
        # - For soma_side='left': mirror everything
        # - For soma_side='combined': mirror only L grids to match dedicated left pages
        # - For soma_side='right': don't mirror anything
        if soma_side.lower() == 'left':
            return 'left'  # Mirror everything
        elif soma_side.lower() == 'combined' and current_side == 'L':
            return 'left'  # Mirror only L grids
        else:
            return 'right'  # No mirroring

    def validate_region_side_combination(self, region: str, side: str) -> bool:
        """
        Validate that a region and side combination is valid.

        Args:
            region: Region name to validate
            side: Side identifier to validate

        Returns:
            True if the combination is valid, False otherwise
        """
        if region not in REGION_ORDER:
            logger.warning(f"Invalid region: {region}. Valid regions: {REGION_ORDER}")
            return False

        if side not in ['L', 'R']:
            logger.warning(f"Invalid side: {side}. Valid sides: ['L', 'R']")
            return False

        return True

    def get_processing_statistics(self, region_grids: Dict) -> Dict:
        """
        Get statistics about the processing results.

        Args:
            region_grids: Dictionary of processed region grids

        Returns:
            Dictionary containing processing statistics
        """
        stats = {
            'total_region_side_combinations': len(region_grids),
            'regions_processed': set(),
            'sides_processed': set(),
            'successful_generations': 0,
            'failed_generations': 0
        }

        for region_side_key, grid_data in region_grids.items():
            if '_' in region_side_key:
                region, side = region_side_key.split('_', 1)
                stats['regions_processed'].add(region)
                stats['sides_processed'].add(side)

            # Check if generation was successful (has content)
            if (grid_data.get('synapse_content') and
                grid_data.get('cell_content')):
                stats['successful_generations'] += 1
            else:
                stats['failed_generations'] += 1

        # Convert sets to lists for JSON serialization
        stats['regions_processed'] = list(stats['regions_processed'])
        stats['sides_processed'] = list(stats['sides_processed'])

        return stats


class RegionGridProcessorFactory:
    """
    Factory class for creating RegionGridProcessor instances.
    """

    @staticmethod
    def create_processor(data_processor: DataProcessor) -> RegionGridProcessor:
        """
        Create a new RegionGridProcessor instance.

        Args:
            data_processor: DataProcessor instance to use

        Returns:
            New RegionGridProcessor instance
        """
        return RegionGridProcessor(data_processor)

    @staticmethod
    def create_with_default_data_processor() -> RegionGridProcessor:
        """
        Create a RegionGridProcessor with a default DataProcessor.

        Returns:
            New RegionGridProcessor instance with default data processor
        """
        data_processor = DataProcessor()
        return RegionGridProcessor(data_processor)
