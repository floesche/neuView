"""
Result assembler for handling result post-processing and assembly.

This module provides the ResultAssembler class that handles the assembly
and post-processing of generation results. It focuses on result validation,
transformation, optimization, and final packaging for consumption.

The ResultAssembler ensures consistent result formatting and provides
extensible post-processing capabilities while maintaining separation
of concerns with the generation pipeline.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from pathlib import Path

from ..data_transfer_objects import (
    GridGenerationRequest, SingleRegionGridRequest, GridGenerationResult
)
from ..exceptions import (
    EyemapError, ValidationError, DataProcessingError, RenderingError,
    ErrorContext, safe_operation
)
from ..validation import EyemapRuntimeValidator
from ..config_manager import EyemapConfiguration
from ..dependency_injection import EyemapServiceContainer

logger = logging.getLogger(__name__)


@dataclass
class ResultMetadata:
    """Metadata associated with generation results."""
    generation_timestamp: float
    processing_statistics: Dict[str, Any]
    quality_metrics: Dict[str, Any]
    optimization_applied: List[str]
    warnings: List[str]
    validation_status: str

    def __post_init__(self):
        if not self.processing_statistics:
            self.processing_statistics = {}
        if not self.quality_metrics:
            self.quality_metrics = {}
        if not self.optimization_applied:
            self.optimization_applied = []
        if not self.warnings:
            self.warnings = []


@dataclass
class AssemblyResult:
    """Result of the assembly process."""
    success: bool
    assembled_result: Any = None
    metadata: Optional[ResultMetadata] = None
    error_message: Optional[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class ResultAssembler:
    """
    Assembles and post-processes generation results.

    This class handles the final assembly of generation results including
    validation, optimization, metadata enrichment, and packaging for
    consumption. It ensures consistent result formatting and provides
    extensible post-processing capabilities.
    """

    def __init__(self, container: EyemapServiceContainer):
        """
        Initialize result assembler with dependency injection.

        Args:
            container: Service container for dependency resolution
        """
        self.container = container
        self.config = container.resolve(EyemapConfiguration)
        self.runtime_validator = EyemapRuntimeValidator()

        # Resolve optional services
        self.performance_manager = container.try_resolve('PerformanceManager')
        self.file_manager = container.try_resolve('FileOutputManager')

        logger.debug("ResultAssembler initialized successfully")

    def assemble_comprehensive_result(self, grid_result: GridGenerationResult,
                                    request: GridGenerationRequest) -> GridGenerationResult:
        """
        Assemble comprehensive grid generation result.

        Performs final assembly including validation, optimization,
        and metadata enrichment for comprehensive grid results.

        Args:
            grid_result: Initial grid generation result
            request: Original generation request

        Returns:
            Assembled and enriched GridGenerationResult

        Raises:
            DataProcessingError: If assembly fails
        """
        with ErrorContext("comprehensive_result_assembly"):
            try:
                # Validate input result
                self._validate_comprehensive_result(grid_result, request)

                # Extract and validate region grids
                region_grids = grid_result.region_grids or {}
                warnings = list(grid_result.warnings) if grid_result.warnings else []

                # Apply post-processing optimizations
                optimized_grids = self._optimize_comprehensive_grids(region_grids, request, warnings)

                # Generate comprehensive metadata
                metadata = self._generate_comprehensive_metadata(grid_result, request, optimized_grids)

                # Perform quality validation
                quality_metrics = self._validate_result_quality(optimized_grids, request)
                metadata.quality_metrics.update(quality_metrics)

                # Apply final transformations
                final_grids = self._apply_final_transformations(optimized_grids, request, warnings)

                # Create enriched result
                assembled_result = GridGenerationResult(
                    region_grids=final_grids,
                    processing_time=grid_result.processing_time,
                    success=grid_result.success and bool(final_grids),
                    warnings=warnings,
                    error_message=grid_result.error_message
                )

                # Attach metadata if available
                if hasattr(assembled_result, '_metadata'):
                    assembled_result._metadata = metadata

                logger.debug(f"Comprehensive result assembled successfully with {len(final_grids)} region grids")
                return assembled_result

            except Exception as e:
                error_message = f"Comprehensive result assembly failed: {str(e)}"
                logger.error(error_message)

                # Return failed result with original data
                return GridGenerationResult(
                    region_grids=grid_result.region_grids or {},
                    processing_time=grid_result.processing_time,
                    success=False,
                    error_message=error_message,
                    warnings=grid_result.warnings
                )

    def assemble_single_region_result(self, grid_content: str,
                                    request: SingleRegionGridRequest) -> str:
        """
        Assemble single region grid generation result.

        Performs validation, optimization, and post-processing
        for single region grid content.

        Args:
            grid_content: Generated grid content
            request: Original single region request

        Returns:
            Assembled and optimized grid content

        Raises:
            DataProcessingError: If assembly fails
        """
        with ErrorContext("single_region_result_assembly",
                         region=request.region,
                         side=request.side,
                         metric=request.metric):
            try:
                # Validate input content
                self._validate_single_region_content(grid_content, request)

                warnings = []

                # Apply content optimizations
                optimized_content = self._optimize_single_region_content(grid_content, request, warnings)

                # Validate optimized content
                self._validate_optimized_content(optimized_content, request)

                # Apply final content transformations
                final_content = self._apply_content_transformations(optimized_content, request, warnings)

                # Log any warnings
                if warnings:
                    logger.warning(f"Single region result assembly completed with warnings: {warnings}")

                logger.debug(f"Single region result assembled successfully for {request.region}/{request.side}/{request.metric}")
                return final_content

            except Exception as e:
                error_message = f"Single region result assembly failed: {str(e)}"
                logger.error(error_message)

                # Return original content if assembly fails
                return grid_content if grid_content else ""

    def assemble_batch_results(self, results: List[Any],
                             requests: List[Any]) -> List[AssemblyResult]:
        """
        Assemble batch generation results.

        Handles assembly of multiple results with batch-specific
        optimizations and consistency checks.

        Args:
            results: List of generation results
            requests: List of corresponding requests

        Returns:
            List of assembled results

        Raises:
            DataProcessingError: If batch assembly fails
        """
        with ErrorContext("batch_result_assembly", result_count=len(results)):
            try:
                assembled_results = []
                batch_warnings = []

                for i, (result, request) in enumerate(zip(results, requests)):
                    try:
                        if isinstance(request, GridGenerationRequest):
                            assembled = self.assemble_comprehensive_result(result, request)
                        elif isinstance(request, SingleRegionGridRequest):
                            assembled = self.assemble_single_region_result(result, request)
                        else:
                            assembled = result

                        assembled_results.append(AssemblyResult(
                            success=True,
                            assembled_result=assembled
                        ))

                    except Exception as e:
                        error_msg = f"Failed to assemble result {i}: {str(e)}"
                        batch_warnings.append(error_msg)
                        assembled_results.append(AssemblyResult(
                            success=False,
                            error_message=error_msg
                        ))

                # Apply batch-level optimizations
                if self.performance_manager:
                    assembled_results = self.performance_manager.optimize_batch_results(assembled_results)

                logger.debug(f"Batch assembly completed: {len(assembled_results)} results processed")
                return assembled_results

            except Exception as e:
                error_message = f"Batch result assembly failed: {str(e)}"
                logger.error(error_message)
                raise DataProcessingError(
                    error_message,
                    operation="batch_result_assembly"
                ) from e

    def _validate_comprehensive_result(self, result: GridGenerationResult,
                                     request: GridGenerationRequest) -> None:
        """
        Validate comprehensive generation result.

        Args:
            result: Grid generation result to validate
            request: Original request

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(result, GridGenerationResult):
            raise ValidationError(
                "Invalid result type for comprehensive result validation",
                operation="comprehensive_result_validation"
            )

        if not result.success and not result.error_message:
            raise ValidationError(
                "Failed result must include error message",
                operation="comprehensive_result_validation"
            )

        if result.success and not result.region_grids:
            raise ValidationError(
                "Successful result must include region grids",
                operation="comprehensive_result_validation"
            )

        # Validate result integrity
        self.runtime_validator.validate_result_integrity(
            result.region_grids if result.region_grids else {},
            dict,
            "comprehensive_result_validation"
        )

    def _validate_single_region_content(self, content: str,
                                      request: SingleRegionGridRequest) -> None:
        """
        Validate single region content.

        Args:
            content: Grid content to validate
            request: Original request

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(content, str):
            raise ValidationError(
                "Single region content must be a string",
                operation="single_region_content_validation"
            )

        if not content.strip():
            raise ValidationError(
                "Single region content cannot be empty",
                operation="single_region_content_validation"
            )

        # Format-specific validation
        format_type = getattr(request, 'format', 'svg').lower()
        if format_type == 'svg' and '<svg' not in content:
            raise ValidationError(
                "SVG content must contain SVG elements",
                operation="single_region_content_validation"
            )

    def _optimize_comprehensive_grids(self, region_grids: Dict[str, str],
                                    request: GridGenerationRequest,
                                    warnings: List[str]) -> Dict[str, str]:
        """
        Apply optimizations to comprehensive grids.

        Args:
            region_grids: Dictionary of region grids
            request: Original request
            warnings: List to append warnings to

        Returns:
            Optimized region grids
        """
        optimized_grids = {}

        for key, content in region_grids.items():
            try:
                # Apply content-level optimizations
                optimized_content = self._optimize_grid_content(content, warnings)

                # Apply compression if enabled
                if self.config.enable_compression:
                    optimized_content = self._compress_grid_content(optimized_content)

                optimized_grids[key] = optimized_content

            except Exception as e:
                warnings.append(f"Failed to optimize grid {key}: {str(e)}")
                optimized_grids[key] = content  # Use original content

        return optimized_grids

    def _optimize_single_region_content(self, content: str,
                                      request: SingleRegionGridRequest,
                                      warnings: List[str]) -> str:
        """
        Apply optimizations to single region content.

        Args:
            content: Grid content to optimize
            request: Original request
            warnings: List to append warnings to

        Returns:
            Optimized content
        """
        try:
            # Apply content-level optimizations
            optimized_content = self._optimize_grid_content(content, warnings)

            # Apply format-specific optimizations
            format_type = getattr(request, 'format', 'svg').lower()
            if format_type == 'svg':
                optimized_content = self._optimize_svg_content(optimized_content, warnings)

            return optimized_content

        except Exception as e:
            warnings.append(f"Content optimization failed: {str(e)}")
            return content

    def _optimize_grid_content(self, content: str, warnings: List[str]) -> str:
        """
        Apply general grid content optimizations.

        Args:
            content: Content to optimize
            warnings: List to append warnings to

        Returns:
            Optimized content
        """
        if not content:
            return content

        try:
            # Remove unnecessary whitespace
            optimized = content.strip()

            # Apply compression if content is large
            if len(optimized) > 10000:  # 10KB threshold
                # Simple whitespace optimization for large content
                import re
                optimized = re.sub(r'\s+', ' ', optimized)
                optimized = re.sub(r'>\s+<', '><', optimized)

            return optimized

        except Exception as e:
            warnings.append(f"Grid content optimization failed: {str(e)}")
            return content

    def _optimize_svg_content(self, content: str, warnings: List[str]) -> str:
        """
        Apply SVG-specific optimizations.

        Args:
            content: SVG content to optimize
            warnings: List to append warnings to

        Returns:
            Optimized SVG content
        """
        try:
            # Remove unnecessary SVG attributes and whitespace
            import re

            # Remove comments
            optimized = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)

            # Optimize number precision
            optimized = re.sub(r'(\d+\.\d{3,})', lambda m: f"{float(m.group(1)):.2f}", optimized)

            return optimized

        except Exception as e:
            warnings.append(f"SVG optimization failed: {str(e)}")
            return content

    def _compress_grid_content(self, content: str) -> str:
        """
        Apply compression to grid content.

        Args:
            content: Content to compress

        Returns:
            Compressed content
        """
        try:
            import gzip
            import base64

            # Compress content
            compressed = gzip.compress(content.encode('utf-8'))

            # Encode as base64 for storage
            encoded = base64.b64encode(compressed).decode('utf-8')

            # Only use compressed version if it's actually smaller
            if len(encoded) < len(content):
                return encoded
            else:
                return content

        except Exception:
            # Return original content if compression fails
            return content

    def _generate_comprehensive_metadata(self, result: GridGenerationResult,
                                       request: GridGenerationRequest,
                                       grids: Dict[str, str]) -> ResultMetadata:
        """
        Generate metadata for comprehensive results.

        Args:
            result: Grid generation result
            request: Original request
            grids: Final grids dictionary

        Returns:
            Result metadata
        """
        import time

        processing_stats = {
            'total_grids': len(grids),
            'processing_time': result.processing_time,
            'regions_count': len(request.regions) if request.regions else 0,
            'metrics_count': len(request.metrics) if request.metrics else 0,
            'success_rate': 1.0 if result.success else 0.0
        }

        quality_metrics = {
            'content_size_total': sum(len(content) for content in grids.values()),
            'average_content_size': sum(len(content) for content in grids.values()) / len(grids) if grids else 0,
            'empty_grids_count': sum(1 for content in grids.values() if not content.strip())
        }

        return ResultMetadata(
            generation_timestamp=time.time(),
            processing_statistics=processing_stats,
            quality_metrics=quality_metrics,
            optimization_applied=[],
            warnings=result.warnings or [],
            validation_status='passed' if result.success else 'failed'
        )

    def _validate_result_quality(self, grids: Dict[str, str],
                               request: GridGenerationRequest) -> Dict[str, Any]:
        """
        Validate quality of assembled results.

        Args:
            grids: Dictionary of grid content
            request: Original request

        Returns:
            Quality metrics dictionary
        """
        quality_metrics = {}

        try:
            # Check for empty content
            empty_count = sum(1 for content in grids.values() if not content.strip())
            quality_metrics['empty_grids_ratio'] = empty_count / len(grids) if grids else 0

            # Check content size distribution
            sizes = [len(content) for content in grids.values()]
            if sizes:
                quality_metrics['min_content_size'] = min(sizes)
                quality_metrics['max_content_size'] = max(sizes)
                quality_metrics['avg_content_size'] = sum(sizes) / len(sizes)

            # Format-specific quality checks
            format_type = getattr(request, 'format', 'svg').lower()
            if format_type == 'svg':
                svg_count = sum(1 for content in grids.values() if '<svg' in content)
                quality_metrics['valid_svg_ratio'] = svg_count / len(grids) if grids else 0

        except Exception as e:
            logger.warning(f"Quality validation failed: {str(e)}")
            quality_metrics['validation_error'] = str(e)

        return quality_metrics

    def _validate_optimized_content(self, content: str,
                                  request: SingleRegionGridRequest) -> None:
        """
        Validate optimized content integrity.

        Args:
            content: Optimized content
            request: Original request

        Raises:
            ValidationError: If validation fails
        """
        if not content:
            raise ValidationError(
                "Optimized content cannot be empty",
                operation="optimized_content_validation"
            )

        # Validate content integrity based on format
        format_type = getattr(request, 'format', 'svg').lower()
        if format_type == 'svg':
            if '<svg' not in content or '</svg>' not in content:
                raise ValidationError(
                    "Optimized SVG content must contain valid SVG structure",
                    operation="optimized_content_validation"
                )

    def _apply_final_transformations(self, grids: Dict[str, str],
                                   request: GridGenerationRequest,
                                   warnings: List[str]) -> Dict[str, str]:
        """
        Apply final transformations to grid content.

        Args:
            grids: Dictionary of grid content
            request: Original request
            warnings: List to append warnings to

        Returns:
            Transformed grid content
        """
        transformed_grids = {}

        for key, content in grids.items():
            try:
                # Apply any final format-specific transformations
                transformed_content = self._apply_format_transformations(content, request)
                transformed_grids[key] = transformed_content

            except Exception as e:
                warnings.append(f"Final transformation failed for grid {key}: {str(e)}")
                transformed_grids[key] = content

        return transformed_grids

    def _apply_content_transformations(self, content: str,
                                     request: SingleRegionGridRequest,
                                     warnings: List[str]) -> str:
        """
        Apply content-specific transformations.

        Args:
            content: Content to transform
            request: Original request
            warnings: List to append warnings to

        Returns:
            Transformed content
        """
        try:
            return self._apply_format_transformations(content, request)
        except Exception as e:
            warnings.append(f"Content transformation failed: {str(e)}")
            return content

    def _apply_format_transformations(self, content: str, request: Any) -> str:
        """
        Apply format-specific transformations.

        Args:
            content: Content to transform
            request: Request object

        Returns:
            Transformed content
        """
        format_type = getattr(request, 'format', 'svg').lower()

        if format_type == 'svg':
            # Ensure proper SVG namespace and structure
            if '<svg' in content and 'xmlns=' not in content:
                content = content.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"')

        return content
