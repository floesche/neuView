"""
Usage example demonstrating the refactored EyemapGenerator with dependency injection and error handling.

This example shows how to use the enhanced EyemapGenerator with:
- Phase 3: Type Safety & Error Handling
- Phase 4: Dependency Injection Container

The refactored system provides better error messages, validation, and service management.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any

# Import the refactored components
from ..eyemap_generator import EyemapGenerator
from ..dependency_injection import EyemapServiceContainer, get_default_container
from ..config_manager import ConfigurationManager
from ..data_transfer_objects import GridGenerationRequest, SingleRegionGridRequest
from ..exceptions import (
    EyemapError, ValidationError, DataProcessingError,
    RenderingError, ConfigurationError, DependencyError
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_basic_usage():
    """
    Example 1: Basic usage with automatic dependency injection.

    This is the simplest way to use the refactored EyemapGenerator.
    """
    print("=== Example 1: Basic Usage with Default Container ===")

    try:
        # Create generator with default configuration
        generator = EyemapGenerator.create_with_defaults()

        # The generator now has full error handling and validation
        print(f"Generator created successfully with hex_size: {generator.hex_size}")

        # Get performance statistics (if enabled)
        stats = generator.get_performance_statistics()
        print(f"Performance monitoring: {stats.get('performance_monitoring', 'enabled')}")

    except DependencyError as e:
        print(f"Dependency injection failed: {e}")
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def example_custom_configuration():
    """
    Example 2: Custom configuration with validation.

    Shows how to create a generator with custom parameters and proper error handling.
    """
    print("\n=== Example 2: Custom Configuration with Validation ===")

    try:
        # Create custom configuration
        config = ConfigurationManager.create_for_generation(
            hex_size=20,
            spacing_factor=1.2,
            output_dir=Path("./custom_output"),
            eyemaps_dir=Path("./custom_eyemaps")
        )

        # Create service container with custom config
        container = EyemapServiceContainer(config)

        # Create generator from container
        generator = EyemapGenerator.create_from_container(container)

        print(f"Custom generator created with hex_size: {generator.hex_size}")
        print(f"Output directory: {generator.output_dir}")

        # Test configuration update with validation
        try:
            generator.update_configuration(hex_size=25, spacing_factor=1.5)
            print(f"Configuration updated successfully. New hex_size: {generator.hex_size}")
        except ValidationError as e:
            print(f"Configuration validation failed: {e}")

    except ConfigurationError as e:
        print(f"Configuration error: {e}")
    except ValidationError as e:
        print(f"Validation error: {e}")


def example_comprehensive_grid_generation():
    """
    Example 3: Comprehensive grid generation with full error handling.

    Demonstrates the enhanced grid generation with proper validation and error handling.
    """
    print("\n=== Example 3: Comprehensive Grid Generation ===")

    try:
        # Create generator
        generator = EyemapGenerator.create_with_defaults(hex_size=15)

        # Create sample data (normally this would come from your data source)
        sample_columns = [
            {'column_id': 1, 'hex1': 0, 'hex2': 0, 'x': 100, 'y': 100},
            {'column_id': 2, 'hex1': 1, 'hex2': 0, 'x': 120, 'y': 100},
            {'column_id': 3, 'hex1': 0, 'hex2': 1, 'x': 100, 'y': 120},
        ]

        # Create grid generation request with validation
        request = GridGenerationRequest(
            all_possible_columns=sample_columns,
            regions=['ME_R'],
            sides=['right'],
            metrics=['synapse_density'],
            data_maps={'right': {'ME_R': {}}},
            save_to_files=False
        )

        # Generate grids with comprehensive error handling
        result = generator.generate_comprehensive_region_hexagonal_grids(request)

        if result.success:
            print(f"Grid generation successful in {result.processing_time:.2f}s")
            print(f"Generated {len(result.region_grids)} region grids")
            if result.warnings:
                print(f"Warnings: {result.warnings}")
        else:
            print(f"Grid generation failed: {result.error_message}")

    except ValidationError as e:
        print(f"Request validation failed: {e}")
        print(f"Field: {e.field}, Value: {e.value}")
    except DataProcessingError as e:
        print(f"Data processing failed: {e}")
        print(f"Operation: {e.operation}")
    except EyemapError as e:
        print(f"Eyemap error: {e}")
        if e.details:
            print(f"Details: {e.details}")


def example_single_region_generation():
    """
    Example 4: Single region generation with error recovery.

    Shows how to handle errors gracefully and recover from failures.
    """
    print("\n=== Example 4: Single Region Generation with Error Recovery ===")

    generator = EyemapGenerator.create_with_defaults()

    # Test cases with various validation scenarios
    test_cases = [
        {
            'name': 'Valid Request',
            'request': SingleRegionGridRequest(
                all_possible_columns=[{'column_id': 1, 'hex1': 0, 'hex2': 0}],
                region='ME_R',
                side='right',
                metric='synapse_density',
                region_name='Medulla Right',
                metric_type='synapse_density'
            )
        },
        {
            'name': 'Invalid Request - Empty Columns',
            'request': SingleRegionGridRequest(
                all_possible_columns=[],  # This should fail validation
                region='ME_R',
                side='right',
                metric='synapse_density'
            )
        },
        {
            'name': 'Invalid Request - Invalid Side',
            'request': SingleRegionGridRequest(
                all_possible_columns=[{'column_id': 1, 'hex1': 0, 'hex2': 0}],
                region='ME_R',
                side='invalid_side',  # This should fail validation
                metric='synapse_density'
            )
        }
    ]

    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        try:
            result = generator.generate_comprehensive_single_region_grid(test_case['request'])
            if result:
                print("✓ Generation successful")
            else:
                print("✗ Generation returned empty result")

        except ValidationError as e:
            print(f"✗ Validation failed as expected: {e.message}")
        except DataProcessingError as e:
            print(f"✗ Data processing failed: {e.message}")
        except Exception as e:
            print(f"✗ Unexpected error: {e}")


def example_performance_monitoring():
    """
    Example 5: Performance monitoring and optimization.

    Shows how to use the performance features of the refactored generator.
    """
    print("\n=== Example 5: Performance Monitoring ===")

    try:
        # Create generator with performance enabled
        generator = EyemapGenerator.create_with_defaults(enable_performance_optimization=True)

        # Check if performance monitoring is available
        stats = generator.get_performance_statistics()
        print(f"Performance monitoring status: {stats}")

        # Run some operations to generate performance data
        sample_request = SingleRegionGridRequest(
            all_possible_columns=[
                {'column_id': i, 'hex1': i % 10, 'hex2': i // 10}
                for i in range(100)
            ],
            region='ME_R',
            side='right',
            metric='synapse_density',
            region_name='Test Region'
        )

        # Generate grid multiple times to collect performance data
        for i in range(3):
            try:
                result = generator.generate_comprehensive_single_region_grid(sample_request)
                print(f"Run {i+1}: Generated result length {len(result) if result else 0}")
            except Exception as e:
                print(f"Run {i+1}: Failed with {type(e).__name__}: {e}")

        # Get updated performance statistics
        final_stats = generator.get_performance_statistics()
        if 'operation_stats' in final_stats:
            print("Performance statistics collected:")
            for op, stats in final_stats['operation_stats'].items():
                print(f"  {op}: {stats}")

        # Demonstrate memory optimization
        print("\nOptimizing memory usage...")
        optimization_result = generator.optimize_memory_usage()
        print(f"Optimization result: {optimization_result}")

    except Exception as e:
        print(f"Performance monitoring example failed: {e}")


def example_service_container_management():
    """
    Example 6: Advanced service container management.

    Shows how to work directly with the service container for advanced scenarios.
    """
    print("\n=== Example 6: Service Container Management ===")

    try:
        # Get the default container
        container = get_default_container()

        # Check what services are registered
        registration_info = container.get_registration_info()
        print("Registered services:")
        for service_name, info in registration_info.items():
            print(f"  {service_name}: {info['lifetime']} (deps: {info['dependencies']})")

        # Create multiple generators from the same container (singletons will be reused)
        generator1 = container.create_eyemap_generator()
        generator2 = container.create_eyemap_generator(hex_size=30)

        print(f"Generator 1 hex_size: {generator1.hex_size}")
        print(f"Generator 2 hex_size: {generator2.hex_size}")

        # Check if they share the same color palette (singleton)
        print(f"Same color palette instance: {generator1.color_palette is generator2.color_palette}")

    except DependencyError as e:
        print(f"Service container error: {e}")


def main():
    """Run all examples to demonstrate the refactored EyemapGenerator."""
    print("EyemapGenerator Refactoring Examples")
    print("====================================")
    print("Demonstrating Phase 3 (Type Safety & Error Handling) and")
    print("Phase 4 (Dependency Injection Container) improvements")

    examples = [
        example_basic_usage,
        example_custom_configuration,
        example_comprehensive_grid_generation,
        example_single_region_generation,
        example_performance_monitoring,
        example_service_container_management
    ]

    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\nExample {example_func.__name__} failed with unexpected error: {e}")
            logger.exception("Example failed")

        print()  # Add spacing between examples

    print("All examples completed!")


if __name__ == "__main__":
    main()
