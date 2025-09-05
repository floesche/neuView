"""
Column Data Manager for Data Processing Module

This module provides functionality for organizing, filtering, and managing
column data used in hexagon grid visualizations. It handles data organization
by sides, regions, and coordinates, as well as data validation and merging.
"""

import logging
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict
from .data_structures import (
    ColumnData,
    ColumnCoordinate,
    ColumnStatus,
    MetricType,
    SomaSide,
    RegionColumnsMap,
    ColumnDataMap,
)
from .validation_manager import ValidationManager

logger = logging.getLogger(__name__)


class ColumnDataManager:
    """
    Manages organization and transformation of column data for visualization.

    This class provides methods for organizing column data by region and side,
    filtering data based on various criteria, and transforming raw column data
    into formats suitable for visualization processing.
    """

    def __init__(self, validation_manager: Optional[ValidationManager] = None):
        """
        Initialize the column data manager.

        Args:
            validation_manager: Optional validation manager for data validation
        """
        self.validation_manager = validation_manager or ValidationManager()
        self.logger = logging.getLogger(__name__)

    def organize_structured_data_by_side(
        self, column_data: List[ColumnData], soma_side: SomaSide
    ) -> Dict[str, Dict[Tuple, ColumnData]]:
        """
        Organize ColumnData objects by side using modern structured approach.

        Args:
            column_data: List of ColumnData objects
            soma_side: Side specification as SomaSide enum

        Returns:
            Dictionary mapping sides to data maps with ColumnData objects

        Raises:
            ValueError: If invalid soma_side or no data for specified side
            TypeError: If soma_side is not a SomaSide enum
        """
        # Enforce enum validation
        if not isinstance(soma_side, SomaSide):
            raise TypeError(f"soma_side must be a SomaSide enum, got {type(soma_side)}")

        if not column_data:
            self.logger.debug("No column data provided for organization")
            return {}

        data_maps = {}

        if soma_side == SomaSide.COMBINED:
            # For combined sides, create separate data maps for L and R
            data_maps["L"] = {}
            data_maps["R"] = {}

            for col in column_data:
                if col.side in ["L", "R"]:
                    key = (col.region, col.coordinate.hex1, col.coordinate.hex2)
                    data_maps[col.side][key] = col
        else:
            # Determine target side from soma_side specification
            if soma_side in [SomaSide.LEFT, SomaSide.L]:
                target_side = "L"
            elif soma_side in [SomaSide.RIGHT, SomaSide.R]:
                target_side = "R"
            else:
                raise ValueError(f"Invalid soma_side specification: {soma_side}")

            data_maps[target_side] = {}
            matching_columns = [col for col in column_data if col.side == target_side]

            if not matching_columns:
                self.logger.debug(
                    f"No columns found for side {target_side} (may be normal for this neuron type)"
                )

            for col in matching_columns:
                key = (col.region, col.coordinate.hex1, col.coordinate.hex2)
                data_maps[target_side][key] = col

        self.logger.debug(
            f"Organized {len(column_data)} columns into {len(data_maps)} side maps"
        )
        return data_maps

    def filter_columns_by_region(
        self, columns: List[ColumnData], region: str
    ) -> List[ColumnData]:
        """
        Filter columns by region.

        Args:
            columns: List of ColumnData to filter
            region: Target region name

        Returns:
            List of columns matching the region
        """
        return [col for col in columns if col.region == region]

    def filter_columns_by_side(
        self, columns: List[ColumnData], side: str
    ) -> List[ColumnData]:
        """
        Filter columns by side.

        Args:
            columns: List of ColumnData to filter
            side: Target side ('L', 'R', 'left', 'right')

        Returns:
            List of columns matching the side
        """
        # Filter by exact side match
        if side not in ["L", "R"]:
            raise ValueError(f"Invalid side: {side}. Must be 'L' or 'R'")

        return [col for col in columns if col.side == side]

    def filter_columns_by_coordinates(
        self, columns: List[ColumnData], coordinate_set: Set[Tuple[int, int]]
    ) -> List[ColumnData]:
        """
        Filter columns by coordinate set.

        Args:
            columns: List of ColumnData to filter
            coordinate_set: Set of (hex1, hex2) coordinate tuples

        Returns:
            List of columns with coordinates in the set
        """
        return [col for col in columns if col.coordinate.to_tuple() in coordinate_set]

    def create_region_columns_map(self, columns: List[ColumnData]) -> RegionColumnsMap:
        """
        Create a mapping of region_side to coordinate sets.

        Args:
            columns: List of ColumnData to analyze

        Returns:
            Dictionary mapping region_side strings to coordinate sets
        """
        region_map = defaultdict(set)

        for column in columns:
            region_side = f"{column.region}_{column.side}"
            coordinate_tuple = column.coordinate.to_tuple()
            region_map[region_side].add(coordinate_tuple)

        return dict(region_map)

    def get_all_possible_columns(self, columns: List[ColumnData]) -> List[Dict]:
        """
        Extract all possible column coordinates from column data.

        Args:
            columns: List of ColumnData to extract coordinates from

        Returns:
            List of dictionaries with coordinate information
        """
        seen_coordinates = set()
        all_columns = []

        for column in columns:
            coord_tuple = column.coordinate.to_tuple()
            if coord_tuple not in seen_coordinates:
                seen_coordinates.add(coord_tuple)
                all_columns.append(
                    {
                        "hex1": column.coordinate.hex1,
                        "hex2": column.coordinate.hex2,
                        "region": column.region,
                    }
                )

        return all_columns

    def determine_column_status(
        self,
        coordinate: ColumnCoordinate,
        region: str,
        region_column_coords: Set[Tuple[int, int]],
        data_map: ColumnDataMap,
        other_regions_coords: Optional[Set[Tuple[int, int]]] = None,
    ) -> ColumnStatus:
        """
        Determine the status of a column based on data availability.

        Args:
            coordinate: Column coordinate to check
            region: Target region name
            region_column_coords: Set of coordinates in the current region
            data_map: Dictionary mapping keys to column data
            other_regions_coords: Optional set of coordinates in other regions

        Returns:
            ColumnStatus indicating the column's status
        """
        coord_tuple = coordinate.to_tuple()
        data_key = (region, coordinate.hex1, coordinate.hex2)

        # Check if column exists in current region
        if coord_tuple in region_column_coords:
            if data_key in data_map:
                return ColumnStatus.HAS_DATA
            else:
                return ColumnStatus.NO_DATA
        elif other_regions_coords and coord_tuple in other_regions_coords:
            return ColumnStatus.NOT_IN_REGION
        else:
            return ColumnStatus.EXCLUDED

    def extract_metric_data(
        self, columns: List[ColumnData], metric_type: MetricType
    ) -> Dict[str, Any]:
        """
        Extract metric-specific data from columns.

        Args:
            columns: List of ColumnData to extract from
            metric_type: Type of metric to extract

        Returns:
            Dictionary containing extracted metric data
        """
        metric_data = {
            "values": [],
            "layer_values": [],
            "statistics": {},
            "distribution": {},
        }

        for column in columns:
            if metric_type == MetricType.SYNAPSE_DENSITY:
                value = column.total_synapses
                layer_vals = column.synapses_per_layer
            elif metric_type == MetricType.CELL_COUNT:
                value = column.neuron_count
                layer_vals = column.neurons_per_layer
            else:
                continue

            metric_data["values"].append(value)
            metric_data["layer_values"].extend(layer_vals)

        # Calculate basic statistics
        if metric_data["values"]:
            import numpy as np

            values = np.array(metric_data["values"])
            metric_data["statistics"] = {
                "count": len(values),
                "mean": float(np.mean(values)),
                "median": float(np.median(values)),
                "std": float(np.std(values)),
                "min": float(np.min(values)),
                "max": float(np.max(values)),
            }

        return metric_data

    def group_columns_by_region(
        self, columns: List[ColumnData]
    ) -> Dict[str, List[ColumnData]]:
        """
        Group columns by region.

        Args:
            columns: List of ColumnData to group

        Returns:
            Dictionary mapping region names to column lists
        """
        grouped = defaultdict(list)
        for column in columns:
            grouped[column.region].append(column)
        return dict(grouped)

    def group_columns_by_side(
        self, columns: List[ColumnData]
    ) -> Dict[str, List[ColumnData]]:
        """
        Group columns by side.

        Args:
            columns: List of ColumnData to group

        Returns:
            Dictionary mapping side names to column lists
        """
        grouped = defaultdict(list)
        for column in columns:
            grouped[column.side].append(column)
        return dict(grouped)

    def find_overlapping_coordinates(
        self, columns1: List[ColumnData], columns2: List[ColumnData]
    ) -> Set[Tuple[int, int]]:
        """
        Find coordinates that appear in both column lists.

        Args:
            columns1: First list of columns
            columns2: Second list of columns

        Returns:
            Set of overlapping coordinate tuples
        """
        coords1 = {col.coordinate.to_tuple() for col in columns1}
        coords2 = {col.coordinate.to_tuple() for col in columns2}
        return coords1.intersection(coords2)

    def merge_column_data(
        self,
        primary_columns: List[ColumnData],
        secondary_columns: List[ColumnData],
        merge_strategy: str = "primary_priority",
    ) -> List[ColumnData]:
        """
        Merge two lists of column data.

        Args:
            primary_columns: Primary column data list
            secondary_columns: Secondary column data list
            merge_strategy: Strategy for merging ('primary_priority', 'sum', 'average')

        Returns:
            List of merged column data
        """
        merged = {}

        # Add primary columns
        for column in primary_columns:
            merged[column.key] = column

        # Process secondary columns based on strategy
        for column in secondary_columns:
            key = column.key

            if key not in merged:
                merged[key] = column
            else:
                if merge_strategy == "primary_priority":
                    # Keep primary, ignore secondary
                    continue
                elif merge_strategy == "sum":
                    # Sum numeric values
                    existing = merged[key]
                    merged[key] = self._sum_columns(existing, column)
                elif merge_strategy == "average":
                    # Average numeric values
                    existing = merged[key]
                    merged[key] = self._average_columns(existing, column)

        return list(merged.values())

    def validate_data_consistency(self, columns: List[ColumnData]) -> Dict[str, Any]:
        """
        Validate consistency of column data.

        Args:
            columns: List of ColumnData to validate

        Returns:
            Dictionary containing validation results
        """
        validation_results = {
            "is_consistent": True,
            "issues": [],
            "warnings": [],
            "statistics": {},
        }

        # Check for duplicate coordinates
        seen_coords = set()
        duplicates = set()

        for column in columns:
            coord = column.coordinate.to_tuple()
            if coord in seen_coords:
                duplicates.add(coord)
                validation_results["is_consistent"] = False
            seen_coords.add(coord)

        if duplicates:
            validation_results["issues"].append(
                f"Duplicate coordinates found: {duplicates}"
            )

        # Check for missing layer data
        columns_with_layers = sum(1 for col in columns if col.layers)
        columns_without_layers = len(columns) - columns_with_layers

        if columns_without_layers > 0:
            validation_results["warnings"].append(
                f"{columns_without_layers} columns have no layer data"
            )

        # Check for data consistency within columns
        for column in columns:
            layer_syn_total = sum(layer.synapse_count for layer in column.layers)
            layer_neu_total = sum(layer.neuron_count for layer in column.layers)

            if layer_syn_total != column.total_synapses and column.layers:
                validation_results["warnings"].append(
                    f"Column {column.key}: layer synapse total mismatch"
                )

            if layer_neu_total != column.neuron_count and column.layers:
                validation_results["warnings"].append(
                    f"Column {column.key}: layer neuron total mismatch"
                )

        # Calculate statistics
        validation_results["statistics"] = {
            "total_columns": len(columns),
            "columns_with_layers": columns_with_layers,
            "columns_without_layers": columns_without_layers,
            "duplicate_count": len(duplicates),
            "regions": len(set(col.region for col in columns)),
            "sides": len(set(col.side for col in columns)),
        }

        return validation_results

    def _sum_columns(self, col1: ColumnData, col2: ColumnData) -> ColumnData:
        """
        Sum two columns' numeric values.

        Args:
            col1: First column
            col2: Second column

        Returns:
            ColumnData with summed values
        """
        from .data_structures import LayerData

        # Sum totals
        total_synapses = col1.total_synapses + col2.total_synapses
        neuron_count = col1.neuron_count + col2.neuron_count

        # Sum layers
        merged_layers = []
        max_layers = max(len(col1.layers), len(col2.layers))

        for i in range(max_layers):
            syn1 = col1.layers[i].synapse_count if i < len(col1.layers) else 0
            syn2 = col2.layers[i].synapse_count if i < len(col2.layers) else 0
            neu1 = col1.layers[i].neuron_count if i < len(col1.layers) else 0
            neu2 = col2.layers[i].neuron_count if i < len(col2.layers) else 0

            layer = LayerData(
                layer_index=i, synapse_count=syn1 + syn2, neuron_count=neu1 + neu2
            )
            merged_layers.append(layer)

        return ColumnData(
            coordinate=col1.coordinate,
            region=col1.region,
            side=col1.side,
            total_synapses=total_synapses,
            neuron_count=neuron_count,
            layers=merged_layers,
        )

    def _average_columns(self, col1: ColumnData, col2: ColumnData) -> ColumnData:
        """
        Average two columns' numeric values.

        Args:
            col1: First column
            col2: Second column

        Returns:
            ColumnData with averaged values
        """
        from .data_structures import LayerData

        # Average totals
        total_synapses = (col1.total_synapses + col2.total_synapses) // 2
        neuron_count = (col1.neuron_count + col2.neuron_count) // 2

        # Average layers
        merged_layers = []
        max_layers = max(len(col1.layers), len(col2.layers))

        for i in range(max_layers):
            syn1 = col1.layers[i].synapse_count if i < len(col1.layers) else 0
            syn2 = col2.layers[i].synapse_count if i < len(col2.layers) else 0
            neu1 = col1.layers[i].neuron_count if i < len(col1.layers) else 0
            neu2 = col2.layers[i].neuron_count if i < len(col2.layers) else 0

            layer = LayerData(
                layer_index=i,
                synapse_count=(syn1 + syn2) // 2,
                neuron_count=(neu1 + neu2) // 2,
            )
            merged_layers.append(layer)

        return ColumnData(
            coordinate=col1.coordinate,
            region=col1.region,
            side=col1.side,
            total_synapses=total_synapses,
            neuron_count=neuron_count,
            layers=merged_layers,
        )
