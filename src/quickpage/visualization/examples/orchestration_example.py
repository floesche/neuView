"""
Example demonstrating the new orchestration architecture in Phase 5.

This example shows how to use the new orchestration services for both
simple and advanced grid generation workflows, demonstrating the improved
modularity and single responsibility design.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List

# Import orchestration services
from ..orchestration import (
    GridGenerationOrchestrator, RequestProcessor, ResultAssembler, PerformanceManager,
    ComprehensiveGridGenerationCommand, SingleRegionGridGenerationCommand,
    BatchGridGenerationCommand
)
from ..data_transfer_objects import GridGenerationRequest, SingleRegionGridRequest
from ..dependency_injection import EyemapServiceContainer, get_default_container
from ..config_manager import ConfigurationManager

logger = logging.getLogger(__name__)


def basic_orchestration_example():
    """
    Basic example using the new orchestration architecture.

    Demonstrates how the new architecture simplifies grid generation
    while providing better error handling and performance monitoring.
    """
    print("=== Basic Orchestration Example ===")

    # Get default container with orchestration services
    container = get_default_container()

    # Resolve orchestration services directly
    orchestrator = container.resolve('GridGenerationOrchestrator')
    request_processor = container.resolve('RequestProcessor')
    performance_manager = container.resolve('PerformanceManager')

    print(f"✓ Orchestration services resolved successfully")

    # Create a simple grid generation request
    sample_request = GridGenerationRequest(
        regions=['ME_R', 'LO_R'],
        sides=['right'],
        metrics=['synapse_density'],
        all_possible_columns=[
            {'hex1': 0, 'hex2': 0, 'region': 'ME_R'},
            {'hex1': 1, 'hex2': 0, 'region': 'ME_R'},
            {'hex1': 0, 'hex2': 1, 'region': 'LO_R'}
        ],
        save_to_files=False
    )

    # Use request processor for validation and preprocessing
    try:
        request_processor.validate_comprehensive_request(sample_request)
        print("✓ Request validation passed")

        preprocessing_result = request_processor.preprocess_comprehensive_request(sample_request)
        if preprocessing_result.success:
            print(f"✓ Request preprocessing completed with {len(preprocessing_result.validation_warnings)} warnings")
        else:
            print(f"✗ Request preprocessing failed: {preprocessing_result.error_message}")
            return

    except Exception as e:
        print(f"✗ Request processing failed: {e}")
        return

    # Monitor performance during operation
    with performance_manager.monitor_operation("basic_example", request_type="comprehensive") as metrics:
        try:
            # Use orchestrator directly for workflow coordination
            result = orchestrator.generate_comprehensive_grids(sample_request)

            if result.success:
                print(f"✓ Grid generation completed successfully")
                print(f"  - Generated {len(result.region_grids)} region grids")
                print(f"  - Processing time: {result.processing_time:.2f}s")
            else:
                print(f"✗ Grid generation failed: {result.error_message}")

        except Exception as e:
            print(f"✗ Grid generation error: {e}")

    # Get performance statistics
    stats = performance_manager.get_performance_statistics()
    print(f"✓ Performance stats: {stats['total_operations']} total operations")

    print("=== Basic Example Complete ===\n")


def command_pattern_example():
    """
    Advanced example using the Command pattern.

    Demonstrates how to use command objects for more complex
    workflow control, including batch operations and error recovery.
    """
    print("=== Command Pattern Example ===")

    container = get_default_container()

    # Create sample requests for batch processing
    requests = [
        SingleRegionGridRequest(
            region='ME_R',
            side='right',
            metric='synapse_density',
            all_possible_columns=[
                {'hex1': i, 'hex2': 0, 'region': 'ME_R'} for i in range(3)
            ],
            thresholds={'min': 0, 'max': 100}
        )
        for _ in range(3)
    ]

    # Create individual commands
    commands = [
        SingleRegionGridGenerationCommand(container, request)
        for request in requests
    ]

    print(f"✓ Created {len(commands)} single region commands")

    # Create batch command for parallel execution
    batch_command = BatchGridGenerationCommand(container, commands)

    try:
        # Validate all commands in batch
        batch_command.validate()
        print("✓ Batch validation passed")

        # Execute batch with performance monitoring
        batch_result = batch_command.execute()

        if batch_result.success:
            print(f"✓ Batch execution completed")
            print(f"  - Total operations: {batch_result.metadata['total_commands']}")
            print(f"  - Successful: {batch_result.metadata['successful_commands']}")
            print(f"  - Success rate: {batch_result.metadata['success_rate']:.1%}")
            print(f"  - Total time: {batch_result.processing_time:.2f}s")
        else:
            print(f"✗ Batch execution failed: {batch_result.error_message}")

    except Exception as e:
        print(f"✗ Batch command error: {e}")

    print("=== Command Pattern Example Complete ===\n")


def result_assembly_example():
    """
    Example demonstrating advanced result assembly and optimization.

    Shows how the ResultAssembler provides content optimization,
    quality validation, and metadata enrichment.
    """
    print("=== Result Assembly Example ===")

    container = get_default_container()
    result_assembler = container.resolve('ResultAssembler')

    # Simulate a grid generation result
    from ..data_transfer_objects import GridGenerationResult

    sample_result = GridGenerationResult(
        region_grids={
            'ME_R_right_synapse_density': '<svg>...</svg>',
            'LO_R_right_synapse_density': '<svg>...</svg>'
        },
        processing_time=1.23,
        success=True,
        warnings=['Sample warning for demonstration']
    )

    sample_request = GridGenerationRequest(
        regions=['ME_R', 'LO_R'],
        sides=['right'],
        metrics=['synapse_density'],
        all_possible_columns=[],
        save_to_files=False
    )

    try:
        # Assemble and optimize the result
        assembled_result = result_assembler.assemble_comprehensive_result(
            sample_result, sample_request
        )

        if assembled_result.success:
            print("✓ Result assembly completed")
            print(f"  - Original grids: {len(sample_result.region_grids)}")
            print(f"  - Assembled grids: {len(assembled_result.region_grids)}")
            print(f"  - Warnings: {len(assembled_result.warnings)}")

            # Check if metadata was attached
            if hasattr(assembled_result, '_metadata'):
                print(f"  - Metadata attached: ✓")
            else:
                print(f"  - Metadata attached: ✗")

        else:
            print(f"✗ Result assembly failed: {assembled_result.error_message}")

    except Exception as e:
        print(f"✗ Result assembly error: {e}")

    print("=== Result Assembly Example Complete ===\n")


def performance_monitoring_example():
    """
    Example demonstrating comprehensive performance monitoring.

    Shows how to use the PerformanceManager for operation monitoring,
    memory optimization, and performance analysis.
    """
    print("=== Performance Monitoring Example ===")

    container = get_default_container()
    performance_manager = container.resolve('PerformanceManager')

    # Example operations with monitoring
    operations = [
        ("data_processing", lambda: simulate_data_processing()),
        ("coordinate_conversion", lambda: simulate_coordinate_conversion()),
        ("hexagon_creation", lambda: simulate_hexagon_creation()),
    ]

    print("✓ Running monitored operations...")

    for op_name, operation in operations:
        with performance_manager.monitor_operation(op_name,
                                                  operation_type="simulation") as metrics:
            try:
                # Simulate operation
                result = operation()
                print(f"  - {op_name}: completed in {metrics.duration:.3f}s")
            except Exception as e:
                print(f"  - {op_name}: failed - {e}")

    # Get comprehensive performance statistics
    stats = performance_manager.get_performance_statistics()
    print(f"\n✓ Performance Statistics:")
    print(f"  - Total operations: {stats['total_operations']}")
    print(f"  - Success rate: {stats['success_rate']:.1%}")
    print(f"  - Average duration: {stats['average_duration']:.3f}s")

    # Generate performance report
    report = performance_manager.create_performance_report()
    print(f"\n✓ Performance Report Generated:")
    print(f"  - Recommendations: {len(report['recommendations'])}")
    for rec in report['recommendations'][:2]:  # Show first 2 recommendations
        print(f"    * {rec}")

    # Demonstrate memory optimization
    memory_result = performance_manager.optimize_memory_usage()
    print(f"\n✓ Memory Optimization:")
    print(f"  - Available: {memory_result.get('optimization_available', False)}")
    if 'memory_saved_mb' in memory_result:
        print(f"  - Memory saved: {memory_result['memory_saved_mb']:.1f} MB")

    print("=== Performance Monitoring Example Complete ===\n")


def advanced_integration_example():
    """
    Advanced example showing full integration of orchestration services.

    Demonstrates how all orchestration services work together for
    complex workflows with comprehensive monitoring and optimization.
    """
    print("=== Advanced Integration Example ===")

    # Create custom configuration
    config = ConfigurationManager.create_for_generation(
        hex_size=10,
        spacing_factor=1.2,
        output_dir=Path("./output"),
        enable_performance_optimization=True
    )

    # Create container with custom configuration
    container = EyemapServiceContainer(config)

    # Resolve all orchestration services
    orchestrator = container.resolve('GridGenerationOrchestrator')
    request_processor = container.resolve('RequestProcessor')
    result_assembler = container.resolve('ResultAssembler')
    performance_manager = container.resolve('PerformanceManager')

    print("✓ Custom container and services initialized")

    # Create complex request
    complex_request = GridGenerationRequest(
        regions=['ME_R', 'LO_R', 'LA_R'],
        sides=['right', 'left'],
        metrics=['synapse_density', 'cell_count'],
        all_possible_columns=[
            {'hex1': i, 'hex2': j, 'region': region}
            for region in ['ME_R', 'LO_R', 'LA_R']
            for i in range(2) for j in range(2)
        ],
        save_to_files=True,
        thresholds={'min': 0, 'max': 500}
    )

    print(f"✓ Complex request created: {len(complex_request.regions)} regions, "
          f"{len(complex_request.sides)} sides, {len(complex_request.metrics)} metrics")

    try:
        # Full workflow with all orchestration services
        with performance_manager.monitor_operation("advanced_workflow",
                                                  workflow_type="full_integration") as workflow_metrics:

            # Step 1: Request processing
            preprocessing_result = request_processor.preprocess_comprehensive_request(complex_request)
            if not preprocessing_result.success:
                print(f"✗ Preprocessing failed: {preprocessing_result.error_message}")
                return

            # Step 2: Grid generation via command
            command = ComprehensiveGridGenerationCommand(container, complex_request)
            generation_result = command.execute()

            if not generation_result.success:
                print(f"✗ Generation failed: {generation_result.error_message}")
                return

            # Step 3: Result assembly and optimization
            final_result = result_assembler.assemble_comprehensive_result(
                generation_result.result, complex_request
            )

            if final_result.success:
                print(f"✓ Advanced workflow completed successfully")
                print(f"  - Generated grids: {len(final_result.region_grids)}")
                print(f"  - Total workflow time: {workflow_metrics.duration:.2f}s")
                print(f"  - Command execution time: {generation_result.processing_time:.2f}s")

                # Performance analysis
                stats = performance_manager.get_performance_statistics()
                print(f"  - Operations monitored: {stats['total_operations']}")

            else:
                print(f"✗ Result assembly failed: {final_result.error_message}")

    except Exception as e:
        print(f"✗ Advanced workflow error: {e}")

    print("=== Advanced Integration Example Complete ===\n")


# Helper functions for simulation
def simulate_data_processing():
    """Simulate data processing operation."""
    import time
    time.sleep(0.1)  # Simulate processing time
    return "data_processed"

def simulate_coordinate_conversion():
    """Simulate coordinate conversion operation."""
    import time
    time.sleep(0.05)
    return "coordinates_converted"

def simulate_hexagon_creation():
    """Simulate hexagon creation operation."""
    import time
    time.sleep(0.15)
    return "hexagons_created"


def main():
    """
    Run all orchestration examples.

    This demonstrates the complete Phase 5 implementation including
    single responsibility services, command pattern, and performance
    monitoring integration.
    """
    print("Phase 5: Single Responsibility Orchestration Examples")
    print("=" * 60)

    try:
        # Run all examples
        basic_orchestration_example()
        command_pattern_example()
        result_assembly_example()
        performance_monitoring_example()
        advanced_integration_example()

        print("🎉 All orchestration examples completed successfully!")
        print("\nKey Benefits Demonstrated:")
        print("✓ Single Responsibility: Each service has one clear purpose")
        print("✓ Command Pattern: Complex operations encapsulated as commands")
        print("✓ Performance Monitoring: Comprehensive operation tracking")
        print("✓ Result Assembly: Advanced result optimization and validation")
        print("✓ Error Handling: Robust error recovery and reporting")
        print("✓ Backward Compatibility: Existing interfaces preserved")

    except Exception as e:
        print(f"❌ Example execution failed: {e}")
        logger.exception("Failed to run orchestration examples")


if __name__ == "__main__":
    # Configure logging for the example
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    main()
