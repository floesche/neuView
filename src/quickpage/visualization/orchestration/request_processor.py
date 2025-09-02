"""
Request processor for centralized request validation and preprocessing.

This module provides the RequestProcessor class that centralizes all request
validation, preprocessing, and transformation logic. It serves as the entry
point for all incoming requests, ensuring they are properly validated and
formatted before being passed to the processing pipeline.

The RequestProcessor follows the single responsibility principle by focusing
solely on request handling and validation coordination.
"""

import logging
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass

from ..data_transfer_objects import (
    GridGenerationRequest, SingleRegionGridRequest
)
from ..exceptions import (
    ValidationError, DataProcessingError, ErrorContext, safe_operation
)
from ..validation import EyemapRequestValidator, EyemapRuntimeValidator
from ..config_manager import EyemapConfiguration
from ..dependency_injection import EyemapServiceContainer

logger = logging.getLogger(__name__)


@dataclass
class RequestPreprocessingResult:
    """Result of request preprocessing operations."""
    success: bool
    preprocessed_request: Any = None
    validation_warnings: List[str] = None
    metadata: Dict[str, Any] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.validation_warnings is None:
            self.validation_warnings = []
        if self.metadata is None:
            self.metadata = {}


class RequestProcessor:
    """
    Centralized request processor for validation and preprocessing.

    This class handles all aspects of request processing including validation,
    preprocessing, transformation, and preparation for the processing pipeline.
    It coordinates between different validation layers and ensures consistent
    request handling across the system.
    """

    def __init__(self, container: EyemapServiceContainer):
        """
        Initialize request processor with dependency injection.

        Args:
            container: Service container for dependency resolution
        """
        self.container = container
        self.config = container.resolve(EyemapConfiguration)

        # Initialize validators
        self.request_validator = EyemapRequestValidator()
        self.runtime_validator = EyemapRuntimeValidator()

        logger.debug("RequestProcessor initialized successfully")

    def validate_comprehensive_request(self, request: GridGenerationRequest) -> None:
        """
        Validate comprehensive grid generation request.

        Performs multi-layered validation including request structure,
        data consistency, and runtime preconditions.

        Args:
            request: Grid generation request to validate

        Raises:
            ValidationError: If validation fails at any level
        """
        with ErrorContext("comprehensive_request_validation"):
            # Layer 1: Request structure validation
            try:
                self.request_validator.validate_grid_generation_request(request)
                logger.debug("Request structure validation passed")
            except ValidationError as e:
                logger.error(f"Request structure validation failed: {e}")
                raise ValidationError(
                    f"Request structure validation failed: {e.message}",
                    operation="comprehensive_request_validation"
                ) from e

            # Layer 2: Runtime preconditions validation
            try:
                self.runtime_validator.validate_operation_preconditions(
                    "comprehensive_grid_generation",
                    has_columns=bool(request.all_possible_columns),
                    has_regions=bool(request.regions),
                    has_sides=bool(request.sides),
                    has_metrics=bool(request.metrics)
                )
                logger.debug("Runtime preconditions validation passed")
            except DataProcessingError as e:
                logger.error(f"Runtime preconditions validation failed: {e}")
                raise ValidationError(
                    f"Runtime preconditions validation failed: {e.message}",
                    operation="comprehensive_request_validation"
                ) from e

            # Layer 3: Data consistency validation
            self._validate_data_consistency(request)

            # Layer 4: Configuration compatibility validation
            self._validate_configuration_compatibility(request)

    def validate_single_region_request(self, request: SingleRegionGridRequest) -> None:
        """
        Validate single region grid generation request.

        Performs validation specific to single region operations including
        region-specific data validation and processing requirements.

        Args:
            request: Single region grid request to validate

        Raises:
            ValidationError: If validation fails
        """
        with ErrorContext("single_region_request_validation"):
            # Layer 1: Request structure validation
            try:
                self.request_validator.validate_single_region_request(request)
                logger.debug("Single region request structure validation passed")
            except ValidationError as e:
                logger.error(f"Single region request validation failed: {e}")
                raise ValidationError(
                    f"Single region request validation failed: {e.message}",
                    operation="single_region_request_validation"
                ) from e

            # Layer 2: Runtime preconditions validation
            try:
                self.runtime_validator.validate_operation_preconditions(
                    "single_region_grid_generation",
                    has_columns=bool(request.all_possible_columns),
                    has_region=bool(request.region),
                    has_side=bool(request.side),
                    has_metric=bool(request.metric)
                )
                logger.debug("Single region runtime preconditions validation passed")
            except DataProcessingError as e:
                logger.error(f"Single region runtime preconditions validation failed: {e}")
                raise ValidationError(
                    f"Single region runtime preconditions validation failed: {e.message}",
                    operation="single_region_request_validation"
                ) from e

            # Layer 3: Region-specific data validation
            self._validate_single_region_data_consistency(request)

    def preprocess_comprehensive_request(self, request: GridGenerationRequest) -> RequestPreprocessingResult:
        """
        Preprocess comprehensive grid generation request.

        Performs request preprocessing including normalization, enrichment,
        and optimization preparation.

        Args:
            request: Grid generation request to preprocess

        Returns:
            RequestPreprocessingResult with preprocessed request and metadata
        """
        with ErrorContext("comprehensive_request_preprocessing"):
            try:
                # Validate first
                self.validate_comprehensive_request(request)

                warnings = []
                metadata = {}

                # Normalize request parameters
                normalized_request = self._normalize_comprehensive_request(request)
                metadata['normalization_applied'] = True

                # Enrich request with derived data
                enriched_request = self._enrich_comprehensive_request(normalized_request, warnings)
                metadata['enrichment_applied'] = True

                # Optimize request for processing
                optimized_request = self._optimize_comprehensive_request(enriched_request, warnings)
                metadata['optimization_applied'] = True

                logger.debug(f"Comprehensive request preprocessing completed with {len(warnings)} warnings")

                return RequestPreprocessingResult(
                    success=True,
                    preprocessed_request=optimized_request,
                    validation_warnings=warnings,
                    metadata=metadata
                )

            except ValidationError as e:
                logger.error(f"Comprehensive request preprocessing failed: {e}")
                return RequestPreprocessingResult(
                    success=False,
                    error_message=f"Preprocessing validation failed: {e.message}"
                )
            except Exception as e:
                logger.error(f"Unexpected error in comprehensive request preprocessing: {e}")
                return RequestPreprocessingResult(
                    success=False,
                    error_message=f"Preprocessing failed: {str(e)}"
                )

    def preprocess_single_region_request(self, request: SingleRegionGridRequest) -> RequestPreprocessingResult:
        """
        Preprocess single region grid generation request.

        Performs specialized preprocessing for single region operations
        including region-specific optimizations.

        Args:
            request: Single region grid request to preprocess

        Returns:
            RequestPreprocessingResult with preprocessed request and metadata
        """
        with ErrorContext("single_region_request_preprocessing"):
            try:
                # Validate first
                self.validate_single_region_request(request)

                warnings = []
                metadata = {}

                # Normalize request parameters
                normalized_request = self._normalize_single_region_request(request)
                metadata['normalization_applied'] = True

                # Enrich request with region-specific data
                enriched_request = self._enrich_single_region_request(normalized_request, warnings)
                metadata['enrichment_applied'] = True

                # Apply region-specific optimizations
                optimized_request = self._optimize_single_region_request(enriched_request, warnings)
                metadata['optimization_applied'] = True

                logger.debug(f"Single region request preprocessing completed with {len(warnings)} warnings")

                return RequestPreprocessingResult(
                    success=True,
                    preprocessed_request=optimized_request,
                    validation_warnings=warnings,
                    metadata=metadata
                )

            except ValidationError as e:
                logger.error(f"Single region request preprocessing failed: {e}")
                return RequestPreprocessingResult(
                    success=False,
                    error_message=f"Preprocessing validation failed: {e.message}"
                )
            except Exception as e:
                logger.error(f"Unexpected error in single region request preprocessing: {e}")
                return RequestPreprocessingResult(
                    success=False,
                    error_message=f"Preprocessing failed: {str(e)}"
                )

    def _validate_data_consistency(self, request: GridGenerationRequest) -> None:
        """
        Validate data consistency for comprehensive requests.

        Args:
            request: Grid generation request to validate

        Raises:
            ValidationError: If data consistency checks fail
        """
        try:
            required_data = {
                'all_possible_columns': request.all_possible_columns,
                'regions': request.regions,
                'sides': request.sides,
                'metrics': request.metrics
            }

            required_keys = {'all_possible_columns', 'regions', 'sides', 'metrics'}

            self.runtime_validator.validate_data_consistency(
                required_data,
                required_keys,
                "comprehensive_grid_generation"
            )

            # Additional consistency checks
            if hasattr(request, 'region_maps') and request.region_maps:
                self._validate_region_maps_consistency(request.regions, request.region_maps)

            logger.debug("Data consistency validation passed")

        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(
                f"Data consistency validation failed: {str(e)}",
                operation="comprehensive_request_validation"
            ) from e

    def _validate_single_region_data_consistency(self, request: SingleRegionGridRequest) -> None:
        """
        Validate data consistency for single region requests.

        Args:
            request: Single region grid request to validate

        Raises:
            ValidationError: If data consistency checks fail
        """
        try:
            required_data = {
                'all_possible_columns': request.all_possible_columns,
                'region': request.region,
                'side': request.side,
                'metric': request.metric
            }

            required_keys = {'all_possible_columns', 'region', 'side', 'metric'}

            self.runtime_validator.validate_data_consistency(
                required_data,
                required_keys,
                "single_region_grid_generation"
            )

            # Validate region-specific data if present
            if hasattr(request, 'region_column_coords') and request.region_column_coords:
                self._validate_region_column_coords(request.region, request.region_column_coords)

            logger.debug("Single region data consistency validation passed")

        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(
                f"Single region data consistency validation failed: {str(e)}",
                operation="single_region_request_validation"
            ) from e

    def _validate_configuration_compatibility(self, request: GridGenerationRequest) -> None:
        """
        Validate configuration compatibility for the request.

        Args:
            request: Grid generation request to validate

        Raises:
            ValidationError: If configuration is incompatible
        """
        # Check if output configuration is compatible
        if hasattr(request, 'save_to_files') and request.save_to_files:
            if not self.config.output_dir or not self.config.output_dir.exists():
                raise ValidationError(
                    "Output directory not configured or does not exist for file saving",
                    operation="configuration_compatibility_validation"
                )

        # Check format compatibility
        if hasattr(request, 'format') and request.format:
            supported_formats = {'svg', 'png'}
            if request.format.lower() not in supported_formats:
                raise ValidationError(
                    f"Unsupported format '{request.format}'. Supported: {supported_formats}",
                    operation="configuration_compatibility_validation"
                )

        logger.debug("Configuration compatibility validation passed")

    def _validate_region_maps_consistency(self, regions: List[str], region_maps: Dict[str, Any]) -> None:
        """
        Validate consistency between regions and region maps.

        Args:
            regions: List of regions
            region_maps: Dictionary of region mappings

        Raises:
            ValidationError: If consistency check fails
        """
        if not regions or not region_maps:
            return

        missing_regions = set(regions) - set(region_maps.keys())
        if missing_regions:
            raise ValidationError(
                f"Missing region maps for regions: {missing_regions}",
                operation="region_maps_consistency_validation"
            )

    def _validate_region_column_coords(self, region: str, region_column_coords: Dict[str, Any]) -> None:
        """
        Validate region column coordinates.

        Args:
            region: Region name
            region_column_coords: Region column coordinates

        Raises:
            ValidationError: If validation fails
        """
        if not region_column_coords:
            raise ValidationError(
                f"Empty region column coordinates for region '{region}'",
                operation="region_column_coords_validation"
            )

        # Additional coordinate validation can be added here
        logger.debug(f"Region column coordinates validation passed for region '{region}'")

    def _normalize_comprehensive_request(self, request: GridGenerationRequest) -> GridGenerationRequest:
        """
        Normalize comprehensive request parameters.

        Args:
            request: Request to normalize

        Returns:
            Normalized request
        """
        # Create a copy and apply normalizations
        # This would typically involve standardizing formats, defaults, etc.
        # For now, return the original request (placeholder for future enhancements)
        return request

    def _normalize_single_region_request(self, request: SingleRegionGridRequest) -> SingleRegionGridRequest:
        """
        Normalize single region request parameters.

        Args:
            request: Request to normalize

        Returns:
            Normalized request
        """
        # Create a copy and apply normalizations
        # This would typically involve standardizing formats, defaults, etc.
        # For now, return the original request (placeholder for future enhancements)
        return request

    def _enrich_comprehensive_request(self, request: GridGenerationRequest, warnings: List[str]) -> GridGenerationRequest:
        """
        Enrich comprehensive request with derived data.

        Args:
            request: Request to enrich
            warnings: List to append warnings to

        Returns:
            Enriched request
        """
        # Add derived data, computed values, etc.
        # This is a placeholder for future enrichment logic
        return request

    def _enrich_single_region_request(self, request: SingleRegionGridRequest, warnings: List[str]) -> SingleRegionGridRequest:
        """
        Enrich single region request with derived data.

        Args:
            request: Request to enrich
            warnings: List to append warnings to

        Returns:
            Enriched request
        """
        # Add derived data, computed values, etc.
        # This is a placeholder for future enrichment logic
        return request

    def _optimize_comprehensive_request(self, request: GridGenerationRequest, warnings: List[str]) -> GridGenerationRequest:
        """
        Optimize comprehensive request for processing.

        Args:
            request: Request to optimize
            warnings: List to append warnings to

        Returns:
            Optimized request
        """
        # Apply processing optimizations
        # This is a placeholder for future optimization logic
        return request

    def _optimize_single_region_request(self, request: SingleRegionGridRequest, warnings: List[str]) -> SingleRegionGridRequest:
        """
        Optimize single region request for processing.

        Args:
            request: Request to optimize
            warnings: List to append warnings to

        Returns:
            Optimized request
        """
        # Apply processing optimizations
        # This is a placeholder for future optimization logic
        return request
