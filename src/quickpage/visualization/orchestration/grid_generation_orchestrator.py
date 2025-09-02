"""
Grid generation orchestrator for coordinating complex workflows.

This module provides the GridGenerationOrchestrator class that coordinates
high-level grid generation workflows. It serves as the central coordinator
between request processing, data processing, rendering, and result assembly.

The orchestrator focuses on workflow coordination and delegation while
maintaining clear separation of concerns with other system components.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

from ..data_transfer_objects import (
    GridGenerationRequest, SingleRegionGridRequest, GridGenerationResult
)
from ..exceptions import (
    EyemapError, ValidationError, DataProcessingError, RenderingError,
    ErrorContext, safe_operation
)
from ..dependency_injection import EyemapServiceContainer
from ..config_manager import EyemapConfiguration

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStep:
    """Represents a step in the generation workflow."""
    name: str
    operation: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None

    @property
    def duration(self) -> float:
        """Get step duration in seconds."""
        if self.start_time is None or self.end_time is None:
            return 0.0
        return self.end_time - self.start_time


@dataclass
class WorkflowResult:
    """Result of a complete workflow execution."""
    success: bool
    result: Any = None
    steps: List[WorkflowStep] = None
    total_duration: float = 0.0
    error_message: Optional[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.steps is None:
            self.steps = []
        if self.warnings is None:
            self.warnings = []


class GridGenerationOrchestrator:
    """
    Orchestrates grid generation workflows.

    This class coordinates complex multi-step grid generation processes,
    managing the flow between validation, data processing, rendering,
    and result assembly while providing comprehensive error handling
    and performance monitoring.
    """

    def __init__(self, container: EyemapServiceContainer):
        """
        Initialize orchestrator with dependency injection.

        Args:
            container: Service container for dependency resolution
        """
        self.container = container
        self.config = container.resolve(EyemapConfiguration)

        # Resolve core services
        self.color_palette = container.resolve('ColorPalette')
        self.color_mapper = container.resolve('ColorMapper')
        self.coordinate_system = container.resolve('EyemapCoordinateSystem')
        self.data_processor = container.resolve('DataProcessor')
        self.rendering_manager = container.resolve('RenderingManager')

        # Resolve factory services
        region_factory = container.resolve('RegionGridProcessorFactory')
        self.region_processor = region_factory.create_processor(self.data_processor)

        file_factory = container.resolve('FileOutputManagerFactory')
        self.file_manager = file_factory.create_from_config(self.config)

        # Resolve performance services if available
        self.performance_manager = container.try_resolve('PerformanceManager')

        logger.debug("GridGenerationOrchestrator initialized successfully")

    def generate_comprehensive_grids(self, request: GridGenerationRequest) -> GridGenerationResult:
        """
        Orchestrate comprehensive grid generation workflow.

        Coordinates the complete workflow for generating grids across
        multiple regions, sides, and metrics with proper error handling
        and performance optimization.

        Args:
            request: Grid generation request parameters

        Returns:
            GridGenerationResult with generation results and metadata

        Raises:
            DataProcessingError: If workflow execution fails
        """
        workflow = self._create_comprehensive_workflow()
        start_time = time.time()

        with ErrorContext("comprehensive_grid_orchestration",
                         regions=len(request.regions) if request.regions else 0):
            try:
                # Step 1: Configure environment
                step = self._start_workflow_step(workflow, "configure_environment", "environment_setup")
                try:
                    self._configure_generation_environment(request)
                    self._complete_workflow_step(step, success=True)
                except Exception as e:
                    self._complete_workflow_step(step, success=False, error=str(e))
                    raise

                # Step 2: Organize data by side
                step = self._start_workflow_step(workflow, "organize_data", "data_organization")
                try:
                    data_maps = safe_operation(
                        "organize_data_by_side",
                        self._organize_data_by_side,
                        request
                    )
                    self._complete_workflow_step(step, success=True)
                except Exception as e:
                    self._complete_workflow_step(step, success=False, error=str(e))
                    raise

                # Step 3: Process all regions and sides
                step = self._start_workflow_step(workflow, "process_regions", "region_processing")
                try:
                    processed_grids = safe_operation(
                        "process_all_regions_and_sides",
                        self.region_processor.process_all_regions_and_sides,
                        request, data_maps, self.generate_single_region_grid
                    )
                    self._complete_workflow_step(step, success=True)
                except Exception as e:
                    self._complete_workflow_step(step, success=False, error=str(e))
                    raise

                # Step 4: Handle output generation
                step = self._start_workflow_step(workflow, "handle_outputs", "output_generation")
                try:
                    region_grids = safe_operation(
                        "handle_all_grid_outputs",
                        self._handle_all_grid_outputs,
                        request, processed_grids
                    )
                    self._complete_workflow_step(step, success=True)
                except Exception as e:
                    self._complete_workflow_step(step, success=False, error=str(e))
                    raise

                # Create successful result
                total_time = time.time() - start_time
                workflow_result = WorkflowResult(
                    success=True,
                    result=region_grids,
                    steps=workflow,
                    total_duration=total_time
                )

                logger.info(f"Comprehensive grid generation completed successfully in {total_time:.2f}s")

                return GridGenerationResult(
                    region_grids=region_grids,
                    processing_time=total_time,
                    success=True,
                    warnings=workflow_result.warnings
                )

            except Exception as e:
                total_time = time.time() - start_time
                error_message = f"Comprehensive grid generation failed: {str(e)}"
                logger.error(error_message)

                workflow_result = WorkflowResult(
                    success=False,
                    steps=workflow,
                    total_duration=total_time,
                    error_message=error_message
                )

                return GridGenerationResult(
                    region_grids={},
                    processing_time=total_time,
                    success=False,
                    error_message=error_message
                )

    def generate_single_region_grid(self, request: SingleRegionGridRequest) -> str:
        """
        Orchestrate single region grid generation workflow.

        Coordinates the workflow for generating a grid for a specific
        region, side, and metric combination with optimized processing.

        Args:
            request: Single region grid request parameters

        Returns:
            Generated visualization content as string

        Raises:
            DataProcessingError: If workflow execution fails
        """
        workflow = self._create_single_region_workflow()

        with ErrorContext("single_region_grid_orchestration",
                         region=request.region,
                         side=request.side,
                         metric=request.metric):
            try:
                # Step 1: Calculate coordinate and value ranges
                step = self._start_workflow_step(workflow, "calculate_ranges", "range_calculation")
                try:
                    coordinate_ranges = safe_operation(
                        "calculate_coordinate_ranges",
                        self._calculate_coordinate_ranges,
                        request.all_possible_columns
                    )

                    value_range = safe_operation(
                        "determine_value_range",
                        self._determine_value_range,
                        request.thresholds
                    )
                    self._complete_workflow_step(step, success=True)
                except Exception as e:
                    self._complete_workflow_step(step, success=False, error=str(e))
                    raise

                # Step 2: Setup grid metadata
                step = self._start_workflow_step(workflow, "setup_metadata", "metadata_setup")
                try:
                    grid_metadata = safe_operation(
                        "setup_grid_metadata",
                        self._setup_grid_metadata,
                        request, value_range
                    )
                    self._complete_workflow_step(step, success=True)
                except Exception as e:
                    self._complete_workflow_step(step, success=False, error=str(e))
                    raise

                # Step 3: Create processing configuration
                step = self._start_workflow_step(workflow, "create_config", "config_creation")
                try:
                    processing_config = safe_operation(
                        "create_processing_configuration",
                        self._create_processing_configuration,
                        request
                    )
                    self._complete_workflow_step(step, success=True)
                except Exception as e:
                    self._complete_workflow_step(step, success=False, error=str(e))
                    raise

                # Step 4: Process region data
                step = self._start_workflow_step(workflow, "process_data", "data_processing")
                try:
                    processing_result = safe_operation(
                        "process_single_region_data",
                        self._process_single_region_data,
                        request, processing_config
                    )

                    if not processing_result.is_successful:
                        error_details = getattr(processing_result, 'validation_result', {}).get('errors', "Unknown processing error")
                        raise DataProcessingError(
                            f"Data processing failed: {error_details}",
                            operation="process_single_region_data"
                        )
                    self._complete_workflow_step(step, success=True)
                except Exception as e:
                    self._complete_workflow_step(step, success=False, error=str(e))
                    raise

                # Step 5: Convert coordinates and create hexagons
                step = self._start_workflow_step(workflow, "create_hexagons", "hexagon_creation")
                try:
                    coord_to_pixel = safe_operation(
                        "convert_coordinates_to_pixels",
                        self._convert_coordinates_to_pixels,
                        request.all_possible_columns, request.soma_side
                    )

                    hexagons = safe_operation(
                        "create_hexagon_data_collection",
                        self._create_hexagon_data_collection,
                        processing_result, coord_to_pixel, request, value_range
                    )
                    self._complete_workflow_step(step, success=True)
                except Exception as e:
                    self._complete_workflow_step(step, success=False, error=str(e))
                    raise

                # Step 6: Finalize visualization
                step = self._start_workflow_step(workflow, "finalize_visualization", "visualization_finalization")
                try:
                    result = safe_operation(
                        "finalize_single_region_visualization",
                        self._finalize_single_region_visualization,
                        hexagons, request, grid_metadata, value_range
                    )
                    self._complete_workflow_step(step, success=True)
                except Exception as e:
                    self._complete_workflow_step(step, success=False, error=str(e))
                    raise

                logger.debug(f"Single region grid generation completed for {request.region}/{request.side}/{request.metric}")
                return result

            except Exception as e:
                error_message = f"Single region grid generation failed: {str(e)}"
                logger.error(error_message)
                raise DataProcessingError(
                    error_message,
                    operation="single_region_grid_orchestration"
                ) from e

    def _create_comprehensive_workflow(self) -> List[WorkflowStep]:
        """Create workflow steps for comprehensive grid generation."""
        return []

    def _create_single_region_workflow(self) -> List[WorkflowStep]:
        """Create workflow steps for single region grid generation."""
        return []

    def _start_workflow_step(self, workflow: List[WorkflowStep], name: str, operation: str) -> WorkflowStep:
        """
        Start a new workflow step.

        Args:
            workflow: List of workflow steps
            name: Step name
            operation: Operation name

        Returns:
            Created workflow step
        """
        step = WorkflowStep(name=name, operation=operation, start_time=time.time())
        workflow.append(step)
        logger.debug(f"Started workflow step: {name}")
        return step

    def _complete_workflow_step(self, step: WorkflowStep, success: bool, error: Optional[str] = None) -> None:
        """
        Complete a workflow step.

        Args:
            step: Workflow step to complete
            success: Whether the step succeeded
            error: Error message if step failed
        """
        step.end_time = time.time()
        step.success = success
        step.error_message = error

        status = "completed" if success else "failed"
        logger.debug(f"Workflow step {step.name} {status} in {step.duration:.3f}s")

    def _configure_generation_environment(self, request: GridGenerationRequest) -> None:
        """
        Configure environment for grid generation.

        Args:
            request: Grid generation request

        Raises:
            DataProcessingError: If configuration fails
        """
        try:
            # Set embed mode based on save_to_files parameter
            embed_mode = not request.save_to_files
            self.config.update(embed_mode=embed_mode, save_to_files=request.save_to_files)

            logger.debug(f"Environment configured: embed_mode={embed_mode}, save_to_files={request.save_to_files}")
        except Exception as e:
            raise DataProcessingError(
                f"Failed to configure generation environment: {str(e)}",
                operation="environment_configuration"
            ) from e

    def _organize_data_by_side(self, request: GridGenerationRequest) -> Dict[str, Any]:
        """
        Organize data by anatomical side.

        Args:
            request: Grid generation request

        Returns:
            Dictionary of organized data maps

        Raises:
            DataProcessingError: If data organization fails
        """
        try:
            # Delegate to the data processor for side organization
            return self.data_processor.organize_data_by_side(request)
        except Exception as e:
            raise DataProcessingError(
                f"Failed to organize data by side: {str(e)}",
                operation="data_organization"
            ) from e

    def _handle_all_grid_outputs(self, request: GridGenerationRequest, processed_grids: Dict[str, str]) -> Dict[str, str]:
        """
        Handle output generation for all processed grids.

        Args:
            request: Grid generation request
            processed_grids: Dictionary of processed grid content

        Returns:
            Dictionary of final grid outputs

        Raises:
            DataProcessingError: If output handling fails
        """
        try:
            # Use file manager for output handling
            if request.save_to_files:
                return self.file_manager.save_all_grids(processed_grids, request)
            else:
                return processed_grids
        except Exception as e:
            raise DataProcessingError(
                f"Failed to handle grid outputs: {str(e)}",
                operation="output_handling"
            ) from e

    def _calculate_coordinate_ranges(self, all_possible_columns: List[Any]) -> Tuple[Any, Any]:
        """
        Calculate coordinate ranges from column data.

        Args:
            all_possible_columns: List of all possible columns

        Returns:
            Tuple of coordinate ranges

        Raises:
            DataProcessingError: If calculation fails
        """
        try:
            return self.coordinate_system.calculate_coordinate_ranges(all_possible_columns)
        except Exception as e:
            raise DataProcessingError(
                f"Failed to calculate coordinate ranges: {str(e)}",
                operation="coordinate_range_calculation"
            ) from e

    def _determine_value_range(self, thresholds: Optional[Dict[str, Any]]) -> Tuple[float, float]:
        """
        Determine value range for visualization.

        Args:
            thresholds: Optional threshold data

        Returns:
            Tuple of (min_value, max_value)

        Raises:
            DataProcessingError: If determination fails
        """
        try:
            return self.color_mapper.determine_value_range(thresholds)
        except Exception as e:
            raise DataProcessingError(
                f"Failed to determine value range: {str(e)}",
                operation="value_range_determination"
            ) from e

    def _setup_grid_metadata(self, request: SingleRegionGridRequest, value_range: Tuple[float, float]) -> Dict[str, Any]:
        """
        Setup grid metadata for visualization.

        Args:
            request: Single region grid request
            value_range: Value range tuple

        Returns:
            Grid metadata dictionary

        Raises:
            DataProcessingError: If setup fails
        """
        try:
            return {
                'region': request.region,
                'side': request.side,
                'metric': request.metric,
                'value_range': value_range,
                'format': getattr(request, 'format', 'svg'),
                'hex_size': self.config.hex_size,
                'spacing_factor': self.config.spacing_factor
            }
        except Exception as e:
            raise DataProcessingError(
                f"Failed to setup grid metadata: {str(e)}",
                operation="grid_metadata_setup"
            ) from e

    def _create_processing_configuration(self, request: SingleRegionGridRequest) -> Any:
        """
        Create processing configuration from request.

        Args:
            request: Single region grid request

        Returns:
            Processing configuration object

        Raises:
            DataProcessingError: If configuration creation fails
        """
        try:
            return self.data_processor.create_processing_config(request)
        except Exception as e:
            raise DataProcessingError(
                f"Failed to create processing configuration: {str(e)}",
                operation="processing_config_creation"
            ) from e

    def _process_single_region_data(self, request: SingleRegionGridRequest, config: Any) -> Any:
        """
        Process single region data using the data processor.

        Args:
            request: Single region grid request
            config: Processing configuration

        Returns:
            Processing result

        Raises:
            DataProcessingError: If processing fails
        """
        try:
            return self.data_processor.process_single_region_data(request, config)
        except Exception as e:
            raise DataProcessingError(
                f"Failed to process single region data: {str(e)}",
                operation="single_region_data_processing"
            ) from e

    def _convert_coordinates_to_pixels(self, all_possible_columns: List[Any], soma_side: str) -> Dict[str, Any]:
        """
        Convert coordinates to pixel positions.

        Args:
            all_possible_columns: List of all possible columns
            soma_side: Soma side identifier

        Returns:
            Coordinate to pixel mapping

        Raises:
            DataProcessingError: If conversion fails
        """
        try:
            return self.coordinate_system.convert_coordinates_to_pixels(all_possible_columns, soma_side)
        except Exception as e:
            raise DataProcessingError(
                f"Failed to convert coordinates to pixels: {str(e)}",
                operation="coordinate_to_pixel_conversion"
            ) from e

    def _create_hexagon_data_collection(self, processing_result: Any, coord_to_pixel: Dict[str, Any],
                                      request: SingleRegionGridRequest, value_range: Tuple[float, float]) -> List[Any]:
        """
        Create hexagon data collection for rendering.

        Args:
            processing_result: Result from data processing
            coord_to_pixel: Coordinate to pixel mapping
            request: Single region grid request
            value_range: Value range tuple

        Returns:
            List of hexagon data objects

        Raises:
            DataProcessingError: If creation fails
        """
        try:
            return self.rendering_manager.create_hexagon_data_collection(
                processing_result, coord_to_pixel, request, value_range
            )
        except Exception as e:
            raise DataProcessingError(
                f"Failed to create hexagon data collection: {str(e)}",
                operation="hexagon_data_collection_creation"
            ) from e

    def _finalize_single_region_visualization(self, hexagons: List[Any], request: SingleRegionGridRequest,
                                            grid_metadata: Dict[str, Any], value_range: Tuple[float, float]) -> str:
        """
        Finalize single region visualization.

        Args:
            hexagons: List of hexagon data objects
            request: Single region grid request
            grid_metadata: Grid metadata
            value_range: Value range tuple

        Returns:
            Final visualization content

        Raises:
            RenderingError: If finalization fails
        """
        try:
            return self.rendering_manager.finalize_single_region_visualization(
                hexagons, request, grid_metadata, value_range
            )
        except Exception as e:
            raise RenderingError(
                f"Failed to finalize single region visualization: {str(e)}",
                operation="single_region_visualization_finalization"
            ) from e
