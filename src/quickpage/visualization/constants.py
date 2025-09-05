"""
Constants used throughout the eyemap visualization system.

This module centralizes all hardcoded values, magic numbers, and configuration
constants used in eyemap generation to improve maintainability and consistency.
"""

from typing import List

# Region Processing
REGION_ORDER: List[str] = ["ME", "LO", "LOP"]
"""Standard order for processing brain regions in eyemap generation."""


# Default Configuration Values
DEFAULT_HEX_SIZE: int = 6
"""Default size of individual hexagons in pixels."""

DEFAULT_SPACING_FACTOR: float = 1.1
"""Default spacing factor between hexagons."""

DEFAULT_MARGIN: int = 10
"""Default margin around eyemap visualizations in pixels."""


# Metric Types
METRIC_SYNAPSE_DENSITY: str = "synapse_density"
"""Identifier for synapse density metric."""

METRIC_CELL_COUNT: str = "cell_count"
"""Identifier for cell count metric."""


# Output Formats
OUTPUT_FORMAT_SVG: str = "svg"
"""SVG output format identifier."""

OUTPUT_FORMAT_PNG: str = "png"
"""PNG output format identifier."""

SUPPORTED_OUTPUT_FORMATS: List[str] = [OUTPUT_FORMAT_SVG, OUTPUT_FORMAT_PNG]
"""List of all supported output formats."""


# Note: Soma sides are now handled by the SomaSide enum in data_structures.py


# Tooltip Labels
TOOLTIP_SYNAPSE_LABEL: str = "Synapse count"
"""Label used in tooltips for synapse data."""

TOOLTIP_CELL_LABEL: str = "Cell count"
"""Label used in tooltips for cell count data."""

# File and Directory Names
EYEMAPS_SUBDIRECTORY: str = "eyemaps"
"""Default subdirectory name for saving eyemap files."""

# Error Messages
ERROR_NO_COLUMNS: str = "No columns provided"
"""Error message when no column data is available."""


# Note: Soma side validation is now handled by the SomaSide enum


# Validation Constants
MIN_HEX_SIZE: int = 1
"""Minimum allowed hexagon size."""

MAX_HEX_SIZE: int = 50
"""Maximum allowed hexagon size."""

MIN_SPACING_FACTOR: float = 1.0
"""Minimum allowed spacing factor."""

MAX_SPACING_FACTOR: float = 3.0
"""Maximum allowed spacing factor."""
