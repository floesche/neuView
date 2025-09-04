"""
Comprehensive validation module for eyemap generation requests and data structures.

This module provides specialized validators for all aspects of eyemap generation,
including request validation, data structure validation, and configuration validation.
It builds on the base exception system to provide detailed, context-aware error messages.
"""

import logging
from typing import Any, Dict, List, Optional, Union, Set, Type, Callable
from pathlib import Path

from .exceptions import ValidationError, DataProcessingError, ConfigurationError, ErrorContext
from .data_transfer_objects import GridGenerationRequest, SingleRegionGridRequest
from .data_processing.data_structures import MetricType, SomaSide, ProcessingConfig, ColumnStatus

logger = logging.getLogger(__name__)


class EyemapRequestValidator:
    """Validator for eyemap generation requests."""

    @staticmethod
    def validate_grid_generation_request(request: GridGenerationRequest) -> None:
        """
        Validate a complete grid generation request.

        Args:
            request: The request to validate

        Raises:
            ValidationError: If request validation fails
        """
        with ErrorContext("grid_generation_request_validation"):
            if not isinstance(request, GridGenerationRequest):
                raise ValidationError(
                    "Request must be a GridGenerationRequest instance",
                    field="request",
                    value=type(request).__name__,
                    expected_type=GridGenerationRequest
                )

            # Validate required fields
            EyemapRequestValidator._validate_required_columns(request.all_possible_columns)
            EyemapRequestValidator._validate_regions(request.regions)
            EyemapRequestValidator._validate_sides(request.sides)
            EyemapRequestValidator._validate_metrics(request.metrics)

            # Validate optional fields if present
            if hasattr(request, 'data_maps') and request.data_maps is not None:
                EyemapRequestValidator._validate_data_maps(request.data_maps)

            if hasattr(request, 'save_to_files') and request.save_to_files is not None:
                EyemapRequestValidator._validate_boolean_field(request.save_to_files, "save_to_files")

            logger.debug("Grid generation request validation completed successfully")

    @staticmethod
    def validate_single_region_request(request: SingleRegionGridRequest) -> None:
        """
        Validate a single region grid request.

        Args:
            request: The request to validate

        Raises:
            ValidationError: If request validation fails
        """
        with ErrorContext("single_region_request_validation"):
            if not isinstance(request, SingleRegionGridRequest):
                raise ValidationError(
                    "Request must be a SingleRegionGridRequest instance",
                    field="request",
                    value=type(request).__name__,
                    expected_type=SingleRegionGridRequest
                )

            # Validate required fields
            EyemapRequestValidator._validate_required_columns(request.all_possible_columns)
            EyemapRequestValidator._validate_single_region(request.region_name)
            EyemapRequestValidator._validate_single_side(request.soma_side.value if request.soma_side else '')
            EyemapRequestValidator._validate_single_metric(request.metric_type)

            # Validate optional fields
            if hasattr(request, 'data_maps') and request.data_maps is not None:
                EyemapRequestValidator._validate_data_maps(request.data_maps)

            logger.debug("Single region request validation completed successfully")

    @staticmethod
    def _validate_required_columns(columns: Any) -> None:
        """Validate the all_possible_columns field."""
        if columns is None:
            raise ValidationError("all_possible_columns cannot be None", field="all_possible_columns")

        if not isinstance(columns, list):
            raise ValidationError(
                "all_possible_columns must be a list",
                field="all_possible_columns",
                value=type(columns).__name__,
                expected_type=list
            )

        if not columns:
            raise ValidationError(
                "all_possible_columns cannot be empty",
                field="all_possible_columns",
                value=len(columns)
            )

        # Validate individual columns have required structure
        for i, column in enumerate(columns):
            if not isinstance(column, dict):
                raise ValidationError(
                    f"Column at index {i} must be a dictionary",
                    field=f"all_possible_columns[{i}]",
                    value=type(column).__name__,
                    expected_type=dict
                )

            # Check for required column fields
            required_fields = ['hex1', 'hex2']
            for field in required_fields:
                if field not in column:
                    raise ValidationError(
                        f"Column at index {i} missing required field '{field}'",
                        field=f"all_possible_columns[{i}].{field}"
                    )

    @staticmethod
    def _validate_regions(regions: Any) -> None:
        """Validate the regions field."""
        if regions is None:
            raise ValidationError("regions cannot be None", field="regions")

        if not isinstance(regions, list):
            raise ValidationError(
                "regions must be a list",
                field="regions",
                value=type(regions).__name__,
                expected_type=list
            )

        if not regions:
            raise ValidationError("regions cannot be empty", field="regions", value=len(regions))

        # Validate each region is a string
        for i, region in enumerate(regions):
            if not isinstance(region, str):
                raise ValidationError(
                    f"Region at index {i} must be a string",
                    field=f"regions[{i}]",
                    value=type(region).__name__,
                    expected_type=str
                )

            if not region.strip():
                raise ValidationError(
                    f"Region at index {i} cannot be empty or whitespace",
                    field=f"regions[{i}]",
                    value=region
                )

    @staticmethod
    def _validate_single_region(region: Any) -> None:
        """Validate a single region field."""
        if region is None:
            raise ValidationError("region cannot be None", field="region")

        if not isinstance(region, str):
            raise ValidationError(
                "region must be a string",
                field="region",
                value=type(region).__name__,
                expected_type=str
            )

        if not region.strip():
            raise ValidationError("region cannot be empty or whitespace", field="region", value=region)

    @staticmethod
    def _validate_sides(sides: Any) -> None:
        """Validate the sides field."""
        if sides is None:
            raise ValidationError("sides cannot be None", field="sides")

        if not isinstance(sides, list):
            raise ValidationError(
                "sides must be a list",
                field="sides",
                value=type(sides).__name__,
                expected_type=list
            )

        if not sides:
            raise ValidationError("sides cannot be empty", field="sides", value=len(sides))

        valid_sides = {side.value for side in SomaSide}
        for i, side in enumerate(sides):
            if not isinstance(side, str):
                raise ValidationError(
                    f"Side at index {i} must be a string",
                    field=f"sides[{i}]",
                    value=type(side).__name__,
                    expected_type=str
                )

            if side not in valid_sides:
                raise ValidationError(
                    f"Invalid side '{side}' at index {i}. Valid sides: {valid_sides}",
                    field=f"sides[{i}]",
                    value=side
                )

    @staticmethod
    def _validate_single_side(side: Any) -> None:
        """Validate a single side field."""
        if side is None:
            raise ValidationError("side cannot be None", field="side")

        if not isinstance(side, str):
            raise ValidationError(
                "side must be a string",
                field="side",
                value=type(side).__name__,
                expected_type=str
            )

        valid_sides = {side_enum.value for side_enum in SomaSide}
        if side not in valid_sides:
            raise ValidationError(
                f"Invalid side '{side}'. Valid sides: {valid_sides}",
                field="side",
                value=side
            )

    @staticmethod
    def _validate_metrics(metrics: Any) -> None:
        """Validate the metrics field."""
        if metrics is None:
            raise ValidationError("metrics cannot be None", field="metrics")

        if not isinstance(metrics, list):
            raise ValidationError(
                "metrics must be a list",
                field="metrics",
                value=type(metrics).__name__,
                expected_type=list
            )

        if not metrics:
            raise ValidationError("metrics cannot be empty", field="metrics", value=len(metrics))

        valid_metrics = {metric.value for metric in MetricType}
        for i, metric in enumerate(metrics):
            if not isinstance(metric, str):
                raise ValidationError(
                    f"Metric at index {i} must be a string",
                    field=f"metrics[{i}]",
                    value=type(metric).__name__,
                    expected_type=str
                )

            if metric not in valid_metrics:
                raise ValidationError(
                    f"Invalid metric '{metric}' at index {i}. Valid metrics: {valid_metrics}",
                    field=f"metrics[{i}]",
                    value=metric
                )

    @staticmethod
    def _validate_single_metric(metric: Any) -> None:
        """Validate a single metric field."""
        if metric is None:
            raise ValidationError("metric cannot be None", field="metric")

        if not isinstance(metric, str):
            raise ValidationError(
                "metric must be a string",
                field="metric",
                value=type(metric).__name__,
                expected_type=str
            )

        valid_metrics = {metric_enum.value for metric_enum in MetricType}
        if metric not in valid_metrics:
            raise ValidationError(
                f"Invalid metric '{metric}'. Valid metrics: {valid_metrics}",
                field="metric",
                value=metric
            )

    @staticmethod
    def _validate_data_maps(data_maps: Any) -> None:
        """Validate the data_maps field."""
        if not isinstance(data_maps, dict):
            raise ValidationError(
                "data_maps must be a dictionary",
                field="data_maps",
                value=type(data_maps).__name__,
                expected_type=dict
            )

        # Validate each side's data
        valid_sides = {side.value for side in SomaSide}
        for side, side_data in data_maps.items():
            if side not in valid_sides:
                raise ValidationError(
                    f"Invalid side '{side}' in data_maps. Valid sides: {valid_sides}",
                    field=f"data_maps.{side}"
                )

            if not isinstance(side_data, dict):
                raise ValidationError(
                    f"Data for side '{side}' must be a dictionary",
                    field=f"data_maps.{side}",
                    value=type(side_data).__name__,
                    expected_type=dict
                )

    @staticmethod
    def _validate_boolean_field(value: Any, field_name: str) -> None:
        """Validate a boolean field."""
        if not isinstance(value, bool):
            raise ValidationError(
                f"{field_name} must be a boolean",
                field=field_name,
                value=type(value).__name__,
                expected_type=bool
            )


class EyemapDataValidator:
    """Validator for eyemap data structures and processing configurations."""

    @staticmethod
    def validate_processing_config(config: ProcessingConfig) -> None:
        """
        Validate a processing configuration.

        Args:
            config: The configuration to validate

        Raises:
            ValidationError: If configuration validation fails
        """
        with ErrorContext("processing_config_validation"):
            if not isinstance(config, ProcessingConfig):
                raise ValidationError(
                    "Config must be a ProcessingConfig instance",
                    field="config",
                    value=type(config).__name__,
                    expected_type=ProcessingConfig
                )

            # Validate numeric fields
            if hasattr(config, 'min_x') and config.min_x is not None:
                EyemapDataValidator._validate_numeric_field(config.min_x, "min_x")

            if hasattr(config, 'max_x') and config.max_x is not None:
                EyemapDataValidator._validate_numeric_field(config.max_x, "max_x")

            if hasattr(config, 'min_y') and config.min_y is not None:
                EyemapDataValidator._validate_numeric_field(config.min_y, "min_y")

            if hasattr(config, 'max_y') and config.max_y is not None:
                EyemapDataValidator._validate_numeric_field(config.max_y, "max_y")

            # Validate coordinate ranges make sense
            if (hasattr(config, 'min_x') and hasattr(config, 'max_x') and
                config.min_x is not None and config.max_x is not None):
                if config.min_x >= config.max_x:
                    raise ValidationError(
                        f"min_x ({config.min_x}) must be less than max_x ({config.max_x})",
                        field="coordinate_range"
                    )

            if (hasattr(config, 'min_y') and hasattr(config, 'max_y') and
                config.min_y is not None and config.max_y is not None):
                if config.min_y >= config.max_y:
                    raise ValidationError(
                        f"min_y ({config.min_y}) must be less than max_y ({config.max_y})",
                        field="coordinate_range"
                    )

    @staticmethod
    def validate_column_data(columns: List[Dict[str, Any]]) -> None:
        """
        Validate column data structure.

        Args:
            columns: List of column dictionaries to validate

        Raises:
            ValidationError: If column data validation fails
        """
        with ErrorContext("column_data_validation"):
            if not isinstance(columns, list):
                raise ValidationError(
                    "Columns must be a list",
                    field="columns",
                    value=type(columns).__name__,
                    expected_type=list
                )

            seen_ids = set()
            for i, column in enumerate(columns):
                EyemapDataValidator._validate_single_column(column, i)

                # Check for duplicate column coordinates
                coord_key = (column.get('hex1'), column.get('hex2'))
                if coord_key in seen_ids:
                    raise ValidationError(
                        f"Duplicate coordinates '{coord_key}' found at index {i}",
                        field=f"columns[{i}].coordinates",
                        value=coord_key
                    )
                seen_ids.add(coord_key)

    @staticmethod
    def _validate_single_column(column: Dict[str, Any], index: int) -> None:
        """Validate a single column dictionary."""
        if not isinstance(column, dict):
            raise ValidationError(
                f"Column at index {index} must be a dictionary",
                field=f"columns[{index}]",
                value=type(column).__name__,
                expected_type=dict
            )

        # Validate required fields
        required_fields = {
            'hex1': (int,),
            'hex2': (int,)
        }

        for field_name, expected_types in required_fields.items():
            if field_name not in column:
                raise ValidationError(
                    f"Column at index {index} missing required field '{field_name}'",
                    field=f"columns[{index}].{field_name}"
                )

            value = column[field_name]
            if not isinstance(value, expected_types):
                type_names = [t.__name__ for t in (expected_types if isinstance(expected_types, tuple) else (expected_types,))]
                raise ValidationError(
                    f"Column field '{field_name}' at index {index} must be {' or '.join(type_names)}",
                    field=f"columns[{index}].{field_name}",
                    value=type(value).__name__,
                    expected_type=expected_types
                )

        # Validate hex coordinates are non-negative
        if column['hex1'] < 0:
            raise ValidationError(
                f"Column hex1 at index {index} cannot be negative",
                field=f"columns[{index}].hex1",
                value=column['hex1']
            )
        if column['hex2'] < 0:
            raise ValidationError(
                f"Column hex2 at index {index} cannot be negative",
                field=f"columns[{index}].hex2",
                value=column['hex2']
            )

    @staticmethod
    def _validate_numeric_field(value: Any, field_name: str) -> None:
        """Validate a numeric field."""
        if not isinstance(value, (int, float)):
            raise ValidationError(
                f"{field_name} must be numeric",
                field=field_name,
                value=type(value).__name__,
                expected_type=(int, float)
            )

        if not (-float('inf') < value < float('inf')):
            raise ValidationError(
                f"{field_name} must be a finite number",
                field=field_name,
                value=value
            )


class EyemapConfigurationValidator:
    """Validator for eyemap configuration objects."""

    @staticmethod
    def validate_configuration(config) -> None:
        """
        Validate an eyemap configuration object.

        Args:
            config: Configuration object to validate

        Raises:
            ConfigurationError: If configuration validation fails
        """
        with ErrorContext("configuration_validation"):
            # Validate hex_size
            if hasattr(config, 'hex_size') and config.hex_size is not None:
                if not isinstance(config.hex_size, (int, float)):
                    raise ConfigurationError(
                        f"hex_size must be numeric, got {type(config.hex_size).__name__}"
                    )
                if config.hex_size <= 0:
                    raise ConfigurationError(f"hex_size must be positive, got {config.hex_size}")

            # Validate spacing_factor
            if hasattr(config, 'spacing_factor') and config.spacing_factor is not None:
                if not isinstance(config.spacing_factor, (int, float)):
                    raise ConfigurationError(
                        f"spacing_factor must be numeric, got {type(config.spacing_factor).__name__}"
                    )
                if config.spacing_factor <= 0:
                    raise ConfigurationError(f"spacing_factor must be positive, got {config.spacing_factor}")

            # Validate paths
            path_fields = ['output_dir', 'eyemaps_dir']
            for field in path_fields:
                if hasattr(config, field):
                    path_value = getattr(config, field)
                    if path_value is not None:
                        EyemapConfigurationValidator._validate_path_field(path_value, field)

            # Validate boolean fields
            boolean_fields = ['embed_mode', 'save_to_files']
            for field in boolean_fields:
                if hasattr(config, field):
                    bool_value = getattr(config, field)
                    if bool_value is not None and not isinstance(bool_value, bool):
                        raise ConfigurationError(
                            f"{field} must be boolean, got {type(bool_value).__name__}"
                        )

    @staticmethod
    def _validate_path_field(path_value: Any, field_name: str) -> None:
        """Validate a path field in configuration."""
        if not isinstance(path_value, (str, Path)):
            raise ConfigurationError(
                f"{field_name} must be string or Path, got {type(path_value).__name__}"
            )

        try:
            Path(path_value)
        except (TypeError, ValueError) as e:
            raise ConfigurationError(f"{field_name} is not a valid path: {e}")


class EyemapRuntimeValidator:
    """Runtime validation utilities for eyemap operations."""

    @staticmethod
    def validate_operation_preconditions(operation_name: str, **conditions) -> None:
        """
        Validate runtime preconditions for an operation.

        Args:
            operation_name: Name of the operation for error context
            **conditions: Key-value pairs of condition names and their values

        Raises:
            DataProcessingError: If preconditions are not met
        """
        with ErrorContext(f"{operation_name}_preconditions"):
            failed_conditions = []

            for condition_name, condition_value in conditions.items():
                if not condition_value:
                    failed_conditions.append(condition_name)

            if failed_conditions:
                raise DataProcessingError(
                    f"Preconditions failed for operation '{operation_name}': {', '.join(failed_conditions)}",
                    operation=operation_name,
                    data_context={'failed_conditions': failed_conditions}
                )

    @staticmethod
    def validate_data_consistency(data_dict: Dict[str, Any], required_keys: Set[str],
                                operation_name: str) -> None:
        """
        Validate data consistency for an operation.

        Args:
            data_dict: Dictionary of data to validate
            required_keys: Set of keys that must be present
            operation_name: Name of the operation for error context

        Raises:
            DataProcessingError: If data is inconsistent
        """
        with ErrorContext(f"{operation_name}_data_consistency"):
            missing_keys = required_keys - set(data_dict.keys())
            if missing_keys:
                raise DataProcessingError(
                    f"Missing required data keys for operation '{operation_name}': {missing_keys}",
                    operation=operation_name,
                    data_context={'missing_keys': list(missing_keys), 'available_keys': list(data_dict.keys())}
                )

            # Check for None values in required fields
            none_fields = [key for key in required_keys if data_dict.get(key) is None]
            if none_fields:
                raise DataProcessingError(
                    f"Required fields contain None values for operation '{operation_name}': {none_fields}",
                    operation=operation_name,
                    data_context={'none_fields': none_fields}
                )

    @staticmethod
    def validate_result_integrity(result: Any, expected_type: Type, operation_name: str,
                                additional_checks: Optional[Dict[str, Callable[[Any], bool]]] = None) -> None:
        """
        Validate the integrity of an operation result.

        Args:
            result: The result to validate
            expected_type: Expected type of the result
            operation_name: Name of the operation for error context
            additional_checks: Optional dictionary of check names to validation functions

        Raises:
            DataProcessingError: If result validation fails
        """
        with ErrorContext(f"{operation_name}_result_validation"):
            # Type check
            if not isinstance(result, expected_type):
                raise DataProcessingError(
                    f"Operation '{operation_name}' returned unexpected type: expected {expected_type.__name__}, got {type(result).__name__}",
                    operation=operation_name,
                    data_context={'expected_type': expected_type.__name__, 'actual_type': type(result).__name__}
                )

            # Additional checks
            if additional_checks:
                failed_checks = []
                for check_name, check_func in additional_checks.items():
                    try:
                        if not check_func(result):
                            failed_checks.append(check_name)
                    except Exception as e:
                        failed_checks.append(f"{check_name} (error: {e})")

                if failed_checks:
                    raise DataProcessingError(
                        f"Result validation failed for operation '{operation_name}': {', '.join(failed_checks)}",
                        operation=operation_name,
                        data_context={'failed_checks': failed_checks}
                    )
