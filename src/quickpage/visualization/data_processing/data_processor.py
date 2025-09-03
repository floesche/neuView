"""
Data Processor for Data Processing Module

This module provides the main data processing interface that orchestrates all
data processing operations for hexagon grid visualizations. It coordinates
validation, threshold calculation, metric calculation, and data organization.
"""

import logging
from typing import List, Dict, Set, Tuple, Optional, Any
from .data_structures import (
    ColumnData, ProcessedColumn, ColumnCoordinate, ColumnStatus, MetricType,
    SomaSide, ProcessingConfig, ValidationResult, DataProcessingResult,
    ThresholdData, MinMaxData
)
from .validation_manager import ValidationManager
from .threshold_calculator import ThresholdCalculator
from .metric_calculator import MetricCalculator
from .column_data_manager import ColumnDataManager


logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Main data processor for hexagon grid generation.

    This class provides the primary interface for processing column data
    for visualization. It orchestrates validation, threshold calculation,
    metric calculation, and data organization operations.
    """

    def __init__(self, strict_validation: bool = False):
        """
        Initialize the data processor.

        Args:
            strict_validation: Whether to use strict validation mode
        """
        self.validation_manager = ValidationManager(strict_mode=strict_validation)
        self.threshold_calculator = ThresholdCalculator(self.validation_manager)
        self.metric_calculator = MetricCalculator(self.validation_manager)
        self.column_data_manager = ColumnDataManager(self.validation_manager)
        self.logger = logging.getLogger(__name__)

    def process_column_data(self,
                           column_data: List[ColumnData],
                           all_possible_columns: List[Dict],
                           region_columns_map: Dict[str, Set[Tuple[int, int]]],
                           config: ProcessingConfig,
                           thresholds: Optional[Dict] = None,
                           min_max_data: Optional[Dict] = None) -> DataProcessingResult:
        """
        Process column data for visualization with modernized data flow.

        Args:
            column_data: List of ColumnData objects (use DataAdapter.normalize_input() for conversion)
            all_possible_columns: List of all possible column coordinates
            region_columns_map: Map of region_side to coordinate sets
            config: Processing configuration
            thresholds: Optional threshold configuration
            min_max_data: Optional min/max data for normalization

        Returns:
            DataProcessingResult containing processed data and validation results
        """
        try:
            # Validate configuration
            config_validation = self.validation_manager.validate_processing_config(config)
            if not config_validation.is_valid:
                return DataProcessingResult(
                    processed_columns=[],
                    validation_result=config_validation
                )

            # Validate that input is already in structured format
            if not column_data:
                self.logger.debug("Empty column data provided")
            else:
                self.logger.debug(f"Processing {len(column_data)} structured columns")

            # Validate column data
            data_validation = self.validation_manager.validate_column_data(column_data)
            if not data_validation.is_valid and config.validate_data:
                return DataProcessingResult(
                    processed_columns=[],
                    validation_result=data_validation
                )

            # Organize data by side
            data_maps = self.column_data_manager.organize_structured_data_by_side(
                column_data, config.soma_side
            )

            # Process each side
            all_processed_columns = []
            overall_validation = ValidationResult(is_valid=True)

            for side, data_map in data_maps.items():
                # Determine mirroring
                mirror_side = self._determine_mirror_side(config.soma_side, side)

                # Filter relevant columns
                side_filtered_columns = self._filter_columns_for_side(
                    all_possible_columns, region_columns_map, config.region_name, side
                )

                # Get region column coordinates
                region_side_key = f"{config.region_name}_{side}"
                region_column_coords = region_columns_map.get(region_side_key, set())

                # Get other regions coordinates
                other_regions_coords = self._get_other_regions_coords(
                    region_columns_map, config.region_name, side
                )

                # Process columns for this side
                side_processed = self._process_side_data(
                    side_filtered_columns,
                    region_column_coords,
                    data_map,
                    config,
                    other_regions_coords,
                    thresholds,
                    min_max_data,
                    mirror_side
                )

                all_processed_columns.extend(side_processed.processed_columns)

                # Merge validation results
                overall_validation.errors.extend(side_processed.validation_result.errors)
                overall_validation.warnings.extend(side_processed.validation_result.warnings)
                if not side_processed.validation_result.is_valid:
                    overall_validation.is_valid = False

            # Calculate processing statistics
            overall_validation.validated_count = len(all_processed_columns)

            # Calculate thresholds if not provided
            calculated_thresholds = None
            if not thresholds:
                try:
                    calculated_thresholds = self.threshold_calculator.calculate_thresholds(
                        column_data, config.metric_type
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to calculate thresholds: {e}")

            # Calculate min/max data if not provided
            calculated_min_max = None
            if not min_max_data:
                try:
                    calculated_min_max = self.threshold_calculator.calculate_min_max_data(column_data)
                except Exception as e:
                    self.logger.warning(f"Failed to calculate min/max data: {e}")

            return DataProcessingResult(
                processed_columns=all_processed_columns,
                validation_result=overall_validation,
                threshold_data=calculated_thresholds,
                min_max_data=calculated_min_max,
                metadata={
                    'config': config,
                    'total_input_columns': len(column_data),
                    'processed_sides': list(data_maps.keys())
                }
            )

        except Exception as e:
            self.logger.error(f"Error processing column data: {e}")
            error_validation = ValidationResult(is_valid=False)
            error_validation.add_error(f"Processing failed: {str(e)}")

            return DataProcessingResult(
                processed_columns=[],
                validation_result=error_validation
            )











    def _determine_mirror_side(self, soma_side: SomaSide, current_side: str) -> str:
        """
        Determine if mirroring should be applied.

        Args:
            soma_side: Soma side configuration
            current_side: Current processing side

        Returns:
            Mirror side string
        """
        if soma_side in [SomaSide.LEFT, SomaSide.L]:
            return 'left'  # Mirror everything
        elif soma_side == SomaSide.COMBINED and current_side == 'L':
            return 'left'  # Mirror only L grids
        else:
            return 'right'  # No mirroring

    def _filter_columns_for_side(self, all_possible_columns: List[Dict],
                                region_columns_map: Dict[str, Set[Tuple[int, int]]],
                                region_name: str,
                                side: str) -> List[Dict]:
        """
        Filter columns relevant for a specific side.

        Args:
            all_possible_columns: List of all possible column coordinates
            region_columns_map: Map of region_side to coordinate sets
            region_name: Target region name
            side: Target side

        Returns:
            List of filtered column dictionaries
        """
        # Get coordinates for current region and side
        region_side_key = f"{region_name}_{side}"
        region_coords = region_columns_map.get(region_side_key, set())

        # Get coordinates for other regions with same side
        other_regions_coords = set()
        other_regions = ['ME', 'LO', 'LOP']  # Known regions
        for other_region in other_regions:
            if other_region != region_name:
                other_region_key = f"{other_region}_{side}"
                if other_region_key in region_columns_map:
                    other_regions_coords.update(region_columns_map[other_region_key])

        # Filter columns to relevant coordinates
        relevant_coords = region_coords | other_regions_coords
        filtered_columns = [
            col for col in all_possible_columns
            if (col['hex1'], col['hex2']) in relevant_coords
        ]

        return filtered_columns

    def _get_other_regions_coords(self, region_columns_map: Dict[str, Set[Tuple[int, int]]],
                                 current_region: str,
                                 side: str) -> Set[Tuple[int, int]]:
        """
        Get coordinates for other regions with the same side.

        Args:
            region_columns_map: Map of region_side to coordinate sets
            current_region: Current region name
            side: Target side

        Returns:
            Set of coordinates from other regions
        """
        other_coords = set()
        other_regions = ['ME', 'LO', 'LOP']

        for region in other_regions:
            if region != current_region:
                region_key = f"{region}_{side}"
                if region_key in region_columns_map:
                    other_coords.update(region_columns_map[region_key])

        return other_coords

    def _process_side_data(self, side_filtered_columns: List[Dict],
                          region_column_coords: Set[Tuple[int, int]],
                          data_map: Dict[Tuple, ColumnData],
                          config: ProcessingConfig,
                          other_regions_coords: Set[Tuple[int, int]],
                          thresholds: Optional[Dict],
                          min_max_data: Optional[Dict],
                          mirror_side: str) -> DataProcessingResult:
        """
        Process data for a specific side using structured ColumnData objects.

        Args:
            side_filtered_columns: Filtered columns for this side
            region_column_coords: Coordinates in the current region
            data_map: Data mapping for this side (ColumnData objects)
            config: Processing configuration
            other_regions_coords: Coordinates in other regions
            thresholds: Optional threshold data
            min_max_data: Optional min/max data
            mirror_side: Mirror side specification

        Returns:
            DataProcessingResult for this side
        """
        processed_columns = []
        validation_result = ValidationResult(is_valid=True)

        # Extract threshold values
        if thresholds and 'all' in thresholds and thresholds['all']:
            global_min = thresholds['all'][0]
            global_max = thresholds['all'][-1]
        else:
            global_min = 0
            global_max = 1

        try:
            # Process each column
            for col_dict in side_filtered_columns:
                coordinate = ColumnCoordinate(col_dict['hex1'], col_dict['hex2'])

                # Determine column status
                status = self.column_data_manager.determine_column_status(
                    coordinate, config.region_name, region_column_coords,
                    data_map, other_regions_coords
                )

                # Skip excluded columns
                if status == ColumnStatus.EXCLUDED:
                    continue

                # Get column data from structured data map
                data_key = (config.region_name, coordinate.hex1, coordinate.hex2)
                column_data = data_map.get(data_key)

                # Debug logging for missing data
                if column_data is None and status == ColumnStatus.HAS_DATA:
                    self.logger.debug(f"No column data found for key {data_key}, available keys: {list(data_map.keys())[:5]}...")

                # Calculate values based on status and metric type
                if status == ColumnStatus.HAS_DATA and column_data:
                    # Ensure we have a ColumnData object, not a dictionary
                    if isinstance(column_data, dict):
                        self.logger.error(f"Received dict instead of ColumnData object at key {data_key}")
                        # Convert dict to ColumnData as fallback
                        from .data_adapter import DataAdapter
                        try:
                            column_data = DataAdapter._dict_to_column_data(column_data)
                        except Exception as e:
                            self.logger.error(f"Failed to convert dict to ColumnData: {e}")
                            value = 0.0
                            layer_values = []
                            layer_colors = []
                        else:
                            value = self.metric_calculator.calculate_metric_value(column_data, config.metric_type)
                            layer_values = self.metric_calculator.calculate_layer_values(column_data, config.metric_type)

                            # Extract layer data for color mapping
                            if config.metric_type == MetricType.SYNAPSE_DENSITY:
                                layer_colors = column_data.synapses_per_layer
                            else:
                                layer_colors = column_data.neurons_per_layer
                    else:
                        value = self.metric_calculator.calculate_metric_value(column_data, config.metric_type)
                        layer_values = self.metric_calculator.calculate_layer_values(column_data, config.metric_type)

                        # Extract layer data for color mapping
                        if config.metric_type == MetricType.SYNAPSE_DENSITY:
                            layer_colors = column_data.synapses_per_layer
                        else:
                            layer_colors = column_data.neurons_per_layer
                else:
                    value = 0.0
                    layer_values = []
                    layer_colors = []

                # Create processed column
                processed_column = ProcessedColumn(
                    coordinate=coordinate,
                    x=0.0,  # Will be set by coordinate system
                    y=0.0,  # Will be set by coordinate system
                    value=value,
                    color="",  # Will be set by color mapper
                    status=status,
                    region=config.region_name,
                    side='combined',  # Since we're showing all possible columns
                    metric_type=config.metric_type,
                    layer_values=layer_values,
                    layer_colors=[str(c) for c in layer_colors],  # Convert to strings
                    metadata={
                        'neuron_count': value if config.metric_type == MetricType.CELL_COUNT else 0,
                        'synapse_value': value if config.metric_type == MetricType.SYNAPSE_DENSITY else 0,
                        'column_name': f"{config.region_name}_col_{coordinate.hex1}_{coordinate.hex2}",
                        'mirror_side': mirror_side,
                        'original_data': column_data.metadata if column_data else {}
                    }
                )

                processed_columns.append(processed_column)

        except Exception as e:
            validation_result.add_error(f"Error processing side data: {str(e)}")

        return DataProcessingResult(
            processed_columns=processed_columns,
            validation_result=validation_result
        )

    def get_processing_summary(self, result: DataProcessingResult) -> Dict[str, Any]:
        """
        Get a summary of processing results.

        Args:
            result: DataProcessingResult to summarize

        Returns:
            Dictionary containing processing summary
        """
        summary = {
            'success': result.is_successful,
            'total_columns': result.column_count,
            'validation': {
                'is_valid': result.validation_result.is_valid,
                'error_count': len(result.validation_result.errors),
                'warning_count': len(result.validation_result.warnings),
                'validated_count': result.validation_result.validated_count,
                'rejected_count': result.validation_result.rejected_count
            },
            'status_distribution': {},
            'metadata': result.metadata
        }

        # Calculate status distribution
        for status in [ColumnStatus.HAS_DATA, ColumnStatus.NO_DATA,
                      ColumnStatus.NOT_IN_REGION, ColumnStatus.EXCLUDED]:
            count = len(result.get_columns_by_status(status))
            summary['status_distribution'][status.value] = count

        # Add threshold and min/max data info
        if result.threshold_data:
            summary['thresholds'] = {
                'min_value': result.threshold_data.min_value,
                'max_value': result.threshold_data.max_value,
                'num_all_thresholds': len(result.threshold_data.all_layers),
                'num_layer_thresholds': len(result.threshold_data.layers)
            }

        if result.min_max_data:
            summary['min_max_data'] = {
                'global_syn_range': (result.min_max_data.global_min_syn,
                                    result.min_max_data.global_max_syn),
                'global_cells_range': (result.min_max_data.global_min_cells,
                                     result.min_max_data.global_max_cells),
                'num_syn_regions': len(result.min_max_data.min_syn_region),
                'num_cells_regions': len(result.min_max_data.min_cells_region)
            }

        return summary
