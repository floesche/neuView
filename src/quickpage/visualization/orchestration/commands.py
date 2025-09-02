"""
Command pattern implementation for grid generation operations.

This module provides command objects that encapsulate grid generation operations,
following the Command pattern to promote loose coupling and enable features like
operation queuing, logging, and undo functionality.

The commands handle the coordination of complex multi-step operations while
delegating actual work to specialized service objects.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..data_transfer_objects import (
    GridGenerationRequest, SingleRegionGridRequest, GridGenerationResult
)
from ..exceptions import (
    EyemapError, ValidationError, DataProcessingError, RenderingError,
    ErrorContext, safe_operation
)
from ..dependency_injection import EyemapServiceContainer

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """Result of executing a command."""
    success: bool
    result: Any = None
    error_message: Optional[str] = None
    processing_time: float = 0.0
    warnings: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}


class GridGenerationCommand(ABC):
    """
    Abstract base class for grid generation commands.

    Implements the Command pattern to encapsulate grid generation operations
    and provide a consistent interface for execution, validation, and error handling.
    """

    def __init__(self, container: EyemapServiceContainer):
        """
        Initialize command with service container.

        Args:
            container: Service container for dependency resolution
        """
        self.container = container
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    @abstractmethod
    def validate(self) -> None:
        """
        Validate command parameters and preconditions.

        Raises:
            ValidationError: If validation fails
        """
        pass

    @abstractmethod
    def execute(self) -> CommandResult:
        """
        Execute the command operation.

        Returns:
            CommandResult with operation results
        """
        pass

    def get_execution_time(self) -> float:
        """Get execution time in seconds."""
        if self.start_time is None or self.end_time is None:
            return 0.0
        return self.end_time - self.start_time

    def _start_timing(self) -> None:
        """Start timing the operation."""
        self.start_time = time.time()

    def _end_timing(self) -> None:
        """End timing the operation."""
        self.end_time = time.time()

    def _create_error_result(self, error: Exception, operation_name: str) -> CommandResult:
        """
        Create a standardized error result.

        Args:
            error: The exception that occurred
            operation_name: Name of the operation that failed

        Returns:
            CommandResult with error information
        """
        self._end_timing()
        error_message = f"{operation_name} failed: {str(error)}"
        logger.error(error_message)

        return CommandResult(
            success=False,
            error_message=error_message,
            processing_time=self.get_execution_time(),
            metadata={"operation": operation_name, "error_type": type(error).__name__}
        )


class ComprehensiveGridGenerationCommand(GridGenerationCommand):
    """
    Command for generating comprehensive region hexagonal grids.

    Encapsulates the complex workflow of generating grids for multiple regions,
    sides, and metrics with proper error handling and validation.
    """

    def __init__(self, container: EyemapServiceContainer, request: GridGenerationRequest):
        """
        Initialize comprehensive grid generation command.

        Args:
            container: Service container for dependency resolution
            request: Grid generation request parameters
        """
        super().__init__(container)
        self.request = request

        # Resolve required services
        self.orchestrator = container.resolve('GridGenerationOrchestrator')
        self.request_processor = container.resolve('RequestProcessor')
        self.result_assembler = container.resolve('ResultAssembler')

    def validate(self) -> None:
        """
        Validate comprehensive grid generation request.

        Raises:
            ValidationError: If request validation fails
        """
        with ErrorContext("comprehensive_grid_validation"):
            # Use request processor for validation
            self.request_processor.validate_comprehensive_request(self.request)

    def execute(self) -> CommandResult:
        """
        Execute comprehensive grid generation workflow.

        Returns:
            CommandResult with grid generation results
        """
        self._start_timing()

        with ErrorContext("comprehensive_grid_generation",
                         regions=len(self.request.regions) if self.request.regions else 0):
            try:
                # Validate request
                self.validate()

                # Process request through orchestrator
                grid_result = self.orchestrator.generate_comprehensive_grids(self.request)

                # Assemble final result
                final_result = self.result_assembler.assemble_comprehensive_result(
                    grid_result, self.request
                )

                self._end_timing()

                return CommandResult(
                    success=final_result.success,
                    result=final_result,
                    processing_time=self.get_execution_time(),
                    warnings=final_result.warnings,
                    metadata={
                        "operation": "comprehensive_grid_generation",
                        "region_count": len(self.request.regions) if self.request.regions else 0,
                        "metric_count": len(self.request.metrics) if self.request.metrics else 0
                    }
                )

            except ValidationError as e:
                return self._create_error_result(e, "comprehensive_grid_validation")
            except DataProcessingError as e:
                return self._create_error_result(e, "comprehensive_grid_processing")
            except RenderingError as e:
                return self._create_error_result(e, "comprehensive_grid_rendering")
            except Exception as e:
                return self._create_error_result(e, "comprehensive_grid_generation")


class SingleRegionGridGenerationCommand(GridGenerationCommand):
    """
    Command for generating a single region hexagonal grid.

    Encapsulates the workflow for generating a grid for a specific region,
    side, and metric combination with optimized processing.
    """

    def __init__(self, container: EyemapServiceContainer, request: SingleRegionGridRequest):
        """
        Initialize single region grid generation command.

        Args:
            container: Service container for dependency resolution
            request: Single region grid request parameters
        """
        super().__init__(container)
        self.request = request

        # Resolve required services
        self.orchestrator = container.resolve('GridGenerationOrchestrator')
        self.request_processor = container.resolve('RequestProcessor')
        self.result_assembler = container.resolve('ResultAssembler')

    def validate(self) -> None:
        """
        Validate single region grid generation request.

        Raises:
            ValidationError: If request validation fails
        """
        with ErrorContext("single_region_grid_validation"):
            # Use request processor for validation
            self.request_processor.validate_single_region_request(self.request)

    def execute(self) -> CommandResult:
        """
        Execute single region grid generation workflow.

        Returns:
            CommandResult with grid content
        """
        self._start_timing()

        with ErrorContext("single_region_grid_generation",
                         region=self.request.region,
                         side=self.request.side,
                         metric=self.request.metric):
            try:
                # Validate request
                self.validate()

                # Process request through orchestrator
                grid_content = self.orchestrator.generate_single_region_grid(self.request)

                # Validate and assemble result
                final_result = self.result_assembler.assemble_single_region_result(
                    grid_content, self.request
                )

                self._end_timing()

                return CommandResult(
                    success=bool(final_result),
                    result=final_result,
                    processing_time=self.get_execution_time(),
                    metadata={
                        "operation": "single_region_grid_generation",
                        "region": self.request.region,
                        "side": self.request.side,
                        "metric": self.request.metric,
                        "format": getattr(self.request, 'format', 'svg')
                    }
                )

            except ValidationError as e:
                return self._create_error_result(e, "single_region_grid_validation")
            except DataProcessingError as e:
                return self._create_error_result(e, "single_region_grid_processing")
            except RenderingError as e:
                return self._create_error_result(e, "single_region_grid_rendering")
            except Exception as e:
                return self._create_error_result(e, "single_region_grid_generation")


class BatchGridGenerationCommand(GridGenerationCommand):
    """
    Command for executing multiple grid generation operations in batch.

    Provides efficient batch processing with parallel execution capabilities
    and consolidated error handling.
    """

    def __init__(self, container: EyemapServiceContainer, commands: List[GridGenerationCommand]):
        """
        Initialize batch grid generation command.

        Args:
            container: Service container for dependency resolution
            commands: List of commands to execute in batch
        """
        super().__init__(container)
        self.commands = commands
        self.performance_manager = container.try_resolve('PerformanceManager')

    def validate(self) -> None:
        """
        Validate all commands in the batch.

        Raises:
            ValidationError: If any command validation fails
        """
        with ErrorContext("batch_grid_validation"):
            validation_errors = []

            for i, command in enumerate(self.commands):
                try:
                    command.validate()
                except ValidationError as e:
                    validation_errors.append(f"Command {i}: {str(e)}")

            if validation_errors:
                raise ValidationError(
                    f"Batch validation failed: {'; '.join(validation_errors)}",
                    operation="batch_grid_validation"
                )

    def execute(self) -> CommandResult:
        """
        Execute all commands in the batch.

        Returns:
            CommandResult with batch execution results
        """
        self._start_timing()

        with ErrorContext("batch_grid_generation", command_count=len(self.commands)):
            try:
                # Validate all commands
                self.validate()

                results = []
                errors = []
                total_warnings = []

                # Execute commands with optional performance optimization
                if self.performance_manager and len(self.commands) > 1:
                    # Use performance manager for batch optimization
                    results = self.performance_manager.execute_batch_operations(self.commands)
                else:
                    # Execute sequentially
                    for command in self.commands:
                        try:
                            result = command.execute()
                            results.append(result)
                            if result.warnings:
                                total_warnings.extend(result.warnings)
                        except Exception as e:
                            error_result = command._create_error_result(e, "batch_command_execution")
                            results.append(error_result)
                            errors.append(str(e))

                self._end_timing()

                # Calculate success rate
                successful_count = sum(1 for r in results if r.success)
                success_rate = successful_count / len(results) if results else 0

                return CommandResult(
                    success=success_rate > 0.5,  # Consider successful if > 50% succeed
                    result=results,
                    processing_time=self.get_execution_time(),
                    warnings=total_warnings,
                    metadata={
                        "operation": "batch_grid_generation",
                        "total_commands": len(self.commands),
                        "successful_commands": successful_count,
                        "success_rate": success_rate,
                        "errors": errors
                    }
                )

            except ValidationError as e:
                return self._create_error_result(e, "batch_grid_validation")
            except Exception as e:
                return self._create_error_result(e, "batch_grid_generation")
