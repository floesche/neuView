"""
Test Package for Data Processing Module

This package contains comprehensive unit tests for the data processing module
of the hexagon grid generator. It tests all components including validation,
threshold calculation, metric calculation, and data organization.

Test Structure:
    test_data_structures.py: Tests for data structure classes
    test_validation_manager.py: Tests for validation functionality
    test_threshold_calculator.py: Tests for threshold calculations
    test_metric_calculator.py: Tests for metric calculations
    test_column_data_manager.py: Tests for data organization
    test_data_processor.py: Tests for main data processor
    test_integration.py: Integration tests for complete workflows

Usage:
    Run all data processing tests:
        python -m pytest test/visualization/data_processing/

    Run specific test module:
        python -m pytest test/visualization/data_processing/test_data_processor.py

    Run with coverage:
        python -m pytest test/visualization/data_processing/ --cov=quickpage.visualization.data_processing
"""

import unittest
import sys
from pathlib import Path

# Add the source directory to the path for testing
test_dir = Path(__file__).parent
project_root = test_dir.parent.parent.parent
src_dir = project_root / "src"
sys.path.insert(0, str(src_dir))

__all__ = [
    "TestDataStructures",
    "TestValidationManager",
    "TestThresholdCalculator",
    "TestMetricCalculator",
    "TestColumnDataManager",
    "TestDataProcessor",
    "TestIntegration",
]


def run_all_tests():
    """Run all data processing tests."""
    import test_data_structures
    import test_validation_manager
    import test_threshold_calculator
    import test_metric_calculator
    import test_column_data_manager
    import test_data_processor
    import test_integration

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test modules
    test_modules = [
        test_data_structures,
        test_validation_manager,
        test_threshold_calculator,
        test_metric_calculator,
        test_column_data_manager,
        test_data_processor,
        test_integration,
    ]

    for module in test_modules:
        suite.addTests(loader.loadTestsFromModule(module))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
