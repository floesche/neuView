"""
Data Processing Module for Hexagon Grid Generator

This module provides classes for processing, organizing, and calculating metrics
from column data used in hexagon grid visualizations. It extracts data processing
logic from the main generator class to improve modularity and testability.

Classes:
    DataProcessor: Main data processing interface
    ColumnDataManager: Column data organization and management
    ThresholdCalculator: Threshold calculation for color mapping
    MetricCalculator: Value and metric calculations
    ValidationManager: Data validation and error handling

Example:
    from .data_processor import DataProcessor
    from .column_data_manager import ColumnDataManager
    from .threshold_calculator import ThresholdCalculator
    from .metric_calculator import MetricCalculator
    from .validation_manager import ValidationManager

    # Initialize data processing components
    data_processor = DataProcessor()
    threshold_calc = ThresholdCalculator()
    metric_calc = MetricCalculator()
"""

from .data_processor import DataProcessor
from .column_data_manager import ColumnDataManager
from .threshold_calculator import ThresholdCalculator
from .metric_calculator import MetricCalculator
from .validation_manager import ValidationManager

__all__ = [
    'DataProcessor',
    'ColumnDataManager',
    'ThresholdCalculator',
    'MetricCalculator',
    'ValidationManager'
]

__version__ = '1.0.0'
