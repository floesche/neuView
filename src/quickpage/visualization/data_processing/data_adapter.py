"""
Data Adapter for Data Processing Module

This module provides centralized data conversion functionality between external
data formats (dictionaries) and internal structured data types (dataclasses).
It serves as the single entry point for external data, ensuring consistent
validation and conversion throughout the data processing pipeline.
"""

import logging
from typing import List, Dict, Optional, Any, Union
from .data_structures import (
    ColumnData, ColumnCoordinate, LayerData, ColumnStatus, MetricType, SomaSide
)

logger = logging.getLogger(__name__)


class DataAdapter:
    """
    Handles conversion between external data formats and internal structures.

    This class provides centralized data conversion functionality, eliminating
    the need for backward compatibility patterns scattered throughout the codebase.
    It validates input data and converts it to strongly-typed dataclass objects.
    """

    @staticmethod
    def from_dict_list(column_summary: List[Dict]) -> List[ColumnData]:
        """
        Convert a list of dictionary objects to ColumnData objects.

        Args:
            column_summary: List of column data dictionaries from external sources

        Returns:
            List of validated ColumnData objects

        Raises:
            ValueError: If required fields are missing or invalid
            TypeError: If input data types are incorrect
        """
        if not column_summary:
            logger.warning("Empty column summary provided to data adapter")
            return []

        if not isinstance(column_summary, list):
            raise TypeError("column_summary must be a list of dictionaries")

        converted_columns = []

        for i, col_dict in enumerate(column_summary):
            try:
                column_data = DataAdapter._dict_to_column_data(col_dict)
                converted_columns.append(column_data)
            except Exception as e:
                logger.error(f"Failed to convert column {i}: {e}")
                raise ValueError(f"Invalid column data at index {i}: {e}") from e

        logger.debug(f"Successfully converted {len(converted_columns)} columns from dictionaries")
        return converted_columns

    @staticmethod
    def _dict_to_column_data(col_dict: Dict) -> ColumnData:
        """
        Convert a single dictionary to a ColumnData object with full validation.

        Args:
            col_dict: Dictionary containing column data

        Returns:
            Validated ColumnData object

        Raises:
            KeyError: If required fields are missing
            ValueError: If field values are invalid
        """
        # Validate required fields
        required_fields = ['hex1', 'hex2', 'region', 'side']
        for field in required_fields:
            if field not in col_dict:
                raise KeyError(f"Required field '{field}' missing from column data")

        # Extract and validate coordinate data
        try:
            hex1 = int(col_dict['hex1'])
            hex2 = int(col_dict['hex2'])
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid coordinate values: hex1={col_dict.get('hex1')}, hex2={col_dict.get('hex2')}") from e

        coordinate = ColumnCoordinate(hex1=hex1, hex2=hex2, region=col_dict['region'])

        # Validate and normalize side
        side = DataAdapter._normalize_side(col_dict['side'])

        # Extract numeric data with defaults
        total_synapses = DataAdapter._extract_int_field(col_dict, 'total_synapses', 0)
        neuron_count = DataAdapter._extract_int_field(col_dict, 'neuron_count', 0)

        # Extract layer data if present
        layers = DataAdapter._extract_layer_data(col_dict)

        # Determine column status
        status = DataAdapter._determine_status(col_dict, total_synapses, neuron_count, layers)

        # Extract metadata
        metadata = DataAdapter._extract_metadata(col_dict)

        return ColumnData(
            coordinate=coordinate,
            region=col_dict['region'],
            side=side,
            total_synapses=total_synapses,
            neuron_count=neuron_count,
            layers=layers,
            status=status,
            metadata=metadata
        )

    @staticmethod
    def _normalize_side(side_value: Any) -> str:
        """
        Normalize and validate side specification.

        Args:
            side_value: Side specification from input data

        Returns:
            Normalized side string ('L' or 'R')

        Raises:
            ValueError: If side specification is invalid
        """
        if not isinstance(side_value, str):
            raise ValueError(f"Side must be a string, got {type(side_value)}")

        side_lower = side_value.lower()

        if side_lower in ['l', 'left']:
            return 'L'
        elif side_lower in ['r', 'right']:
            return 'R'
        elif side_value in ['L', 'R']:
            return side_value
        else:
            raise ValueError(f"Invalid side specification: {side_value}. Must be 'L', 'R', 'left', or 'right'")

    @staticmethod
    def _extract_int_field(col_dict: Dict, field_name: str, default: int = 0) -> int:
        """
        Extract and validate an integer field from dictionary.

        Args:
            col_dict: Source dictionary
            field_name: Name of the field to extract
            default: Default value if field is missing

        Returns:
            Validated integer value

        Raises:
            ValueError: If field value cannot be converted to int or is negative
        """
        if field_name not in col_dict:
            return default

        try:
            value = int(col_dict[field_name])
            if value < 0:
                raise ValueError(f"{field_name} cannot be negative: {value}")
            return value
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid {field_name} value: {col_dict[field_name]}") from e

    @staticmethod
    def _extract_layer_data(col_dict: Dict) -> List[LayerData]:
        """
        Extract layer data from dictionary if present.

        Args:
            col_dict: Source dictionary

        Returns:
            List of LayerData objects
        """
        layers = []

        # Check for various layer data formats
        if 'layers' in col_dict and isinstance(col_dict['layers'], list):
            for i, layer_dict in enumerate(col_dict['layers']):
                try:
                    layer_data = DataAdapter._dict_to_layer_data(layer_dict, i)
                    layers.append(layer_data)
                except Exception as e:
                    logger.warning(f"Skipping invalid layer {i}: {e}")

        elif 'layer_data' in col_dict:
            # Alternative layer data format
            layer_data_dict = col_dict['layer_data']
            if isinstance(layer_data_dict, dict):
                for layer_index, layer_info in layer_data_dict.items():
                    try:
                        layer_index_int = int(layer_index)
                        layer_data = DataAdapter._dict_to_layer_data(layer_info, layer_index_int)
                        layers.append(layer_data)
                    except Exception as e:
                        logger.warning(f"Skipping invalid layer {layer_index}: {e}")

        # Handle legacy column summary format with separate lists
        elif ('synapses_per_layer' in col_dict or 'neurons_per_layer' in col_dict or
              'synapses_list_raw' in col_dict or 'neurons_list' in col_dict):
            # Extract layer data from separate lists
            synapses_list = (col_dict.get('synapses_per_layer') or
                           col_dict.get('synapses_list_raw') or [])
            neurons_list = (col_dict.get('neurons_per_layer') or
                          col_dict.get('neurons_list') or [])

            if isinstance(synapses_list, list) or isinstance(neurons_list, list):
                # Ensure both lists exist and have the same length
                max_len = max(len(synapses_list) if isinstance(synapses_list, list) else 0,
                            len(neurons_list) if isinstance(neurons_list, list) else 0)

                for layer_index in range(max_len):
                    try:
                        synapse_count = (synapses_list[layer_index] if
                                       isinstance(synapses_list, list) and layer_index < len(synapses_list)
                                       else 0)
                        neuron_count = (neurons_list[layer_index] if
                                      isinstance(neurons_list, list) and layer_index < len(neurons_list)
                                      else 0)

                        # Convert to int and validate
                        synapse_count = int(synapse_count) if synapse_count is not None else 0
                        neuron_count = int(neuron_count) if neuron_count is not None else 0

                        if synapse_count < 0:
                            synapse_count = 0
                        if neuron_count < 0:
                            neuron_count = 0

                        layer_data = LayerData(
                            layer_index=layer_index,
                            synapse_count=synapse_count,
                            neuron_count=neuron_count,
                            value=float(synapse_count)  # Default value to synapse count
                        )
                        layers.append(layer_data)

                    except Exception as e:
                        logger.warning(f"Skipping invalid layer {layer_index} in legacy format: {e}")

        return sorted(layers, key=lambda x: x.layer_index)

    @staticmethod
    def _dict_to_layer_data(layer_dict: Dict, layer_index: int) -> LayerData:
        """
        Convert dictionary to LayerData object.

        Args:
            layer_dict: Dictionary containing layer information
            layer_index: Index of the layer

        Returns:
            LayerData object

        Raises:
            ValueError: If layer data is invalid
        """
        if not isinstance(layer_dict, dict):
            raise ValueError(f"Layer data must be a dictionary, got {type(layer_dict)}")

        # Use provided layer_index or extract from dict
        if 'layer_index' in layer_dict:
            try:
                layer_index = int(layer_dict['layer_index'])
            except (ValueError, TypeError):
                pass  # Use the provided layer_index parameter

        synapse_count = DataAdapter._extract_int_field(layer_dict, 'synapse_count', 0)
        neuron_count = DataAdapter._extract_int_field(layer_dict, 'neuron_count', 0)

        # Extract value with multiple possible field names
        value = 0.0
        for value_field in ['value', 'density', 'synapse_density', 'metric_value']:
            if value_field in layer_dict:
                try:
                    value = float(layer_dict[value_field])
                    break
                except (ValueError, TypeError):
                    continue

        color = layer_dict.get('color')

        return LayerData(
            layer_index=layer_index,
            synapse_count=synapse_count,
            neuron_count=neuron_count,
            value=value,
            color=color
        )

    @staticmethod
    def _determine_status(col_dict: Dict, total_synapses: int, neuron_count: int, layers: List[LayerData]) -> ColumnStatus:
        """
        Determine the status of a column based on its data.

        Args:
            col_dict: Source dictionary (may contain explicit status)
            total_synapses: Total synapse count
            neuron_count: Total neuron count
            layers: List of layer data

        Returns:
            ColumnStatus enum value
        """
        # Check for explicit status in input
        if 'status' in col_dict:
            status_str = col_dict['status']
            try:
                return ColumnStatus(status_str)
            except ValueError:
                logger.warning(f"Invalid status value: {status_str}, determining from data")

        # Determine status from data
        has_synapse_data = total_synapses > 0 or any(layer.synapse_count > 0 for layer in layers)
        has_neuron_data = neuron_count > 0 or any(layer.neuron_count > 0 for layer in layers)
        has_value_data = any(layer.value > 0 for layer in layers)

        if has_synapse_data or has_neuron_data or has_value_data:
            return ColumnStatus.HAS_DATA
        else:
            return ColumnStatus.NO_DATA

    @staticmethod
    def _extract_metadata(col_dict: Dict) -> Dict[str, Any]:
        """
        Extract metadata from dictionary, excluding known data fields.

        Args:
            col_dict: Source dictionary

        Returns:
            Dictionary containing metadata
        """
        # Fields that are part of the main data structure
        excluded_fields = {
            'hex1', 'hex2', 'region', 'side', 'total_synapses', 'neuron_count',
            'layers', 'layer_data', 'status'
        }

        metadata = {}
        for key, value in col_dict.items():
            if key not in excluded_fields:
                metadata[key] = value

        return metadata

    @staticmethod
    def validate_structured_input(column_data: List[ColumnData]) -> None:
        """
        Validate that structured input data is properly formatted.

        Args:
            column_data: List of ColumnData objects to validate

        Raises:
            TypeError: If input is not properly structured
            ValueError: If data validation fails
        """
        if not isinstance(column_data, list):
            raise TypeError("column_data must be a list")

        for i, column in enumerate(column_data):
            if not isinstance(column, ColumnData):
                raise TypeError(f"Item {i} must be a ColumnData object, got {type(column)}")

        logger.debug(f"Validated {len(column_data)} structured column objects")

    @staticmethod
    def normalize_input(column_input: Union[List[Dict], List[ColumnData]]) -> List[ColumnData]:
        """
        Normalize input data to ColumnData objects regardless of input format.

        This is the main entry point for data conversion, handling both
        dictionary and structured input formats.

        Args:
            column_input: Either list of dictionaries or list of ColumnData objects

        Returns:
            List of ColumnData objects

        Raises:
            TypeError: If input format is not supported
            ValueError: If data validation fails
        """
        if not column_input:
            return []

        # Determine input format by checking first item
        first_item = column_input[0]

        if isinstance(first_item, dict):
            logger.debug("Converting dictionary input to structured format")
            # Type assertion to help type checker understand this is List[Dict]
            dict_input: List[Dict] = column_input  # type: ignore
            return DataAdapter.from_dict_list(dict_input)
        elif isinstance(first_item, ColumnData):
            logger.debug("Input already in structured format, validating")
            # Type assertion to help type checker understand this is List[ColumnData]
            structured_input: List[ColumnData] = column_input  # type: ignore
            DataAdapter.validate_structured_input(structured_input)
            return structured_input
        else:
            raise TypeError(f"Unsupported input format: expected dict or ColumnData, got {type(first_item)}")
