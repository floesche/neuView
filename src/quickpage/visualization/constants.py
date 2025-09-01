"""
Constants used throughout the eyemap visualization system.

This module centralizes all hardcoded values, magic numbers, and configuration
constants used in eyemap generation to improve maintainability and consistency.
"""

from typing import List, Dict, Any

# Region Processing
REGION_ORDER: List[str] = ['ME', 'LO', 'LOP']
"""Standard order for processing brain regions in eyemap generation."""

REGION_NAMES: Dict[str, str] = {
    'ME': 'Medulla',
    'LO': 'Lobula',
    'LOP': 'Lobula Plate'
}
"""Full names for brain regions."""

# Default Configuration Values
DEFAULT_HEX_SIZE: int = 6
"""Default size of individual hexagons in pixels."""

DEFAULT_SPACING_FACTOR: float = 1.1
"""Default spacing factor between hexagons."""

DEFAULT_MARGIN: int = 10
"""Default margin around eyemap visualizations in pixels."""

# Coordinate System
COORDINATE_PRECISION: int = 6
"""Decimal precision for coordinate calculations."""

# Visualization Constants
MIN_NORMALIZED_VALUE: float = 0.0
"""Minimum value for normalized data ranges."""

MAX_NORMALIZED_VALUE: float = 1.0
"""Maximum value for normalized data ranges."""

# Metric Types
METRIC_SYNAPSE_DENSITY: str = 'synapse_density'
"""Identifier for synapse density metric."""

METRIC_CELL_COUNT: str = 'cell_count'
"""Identifier for cell count metric."""

SUPPORTED_METRICS: List[str] = [METRIC_SYNAPSE_DENSITY, METRIC_CELL_COUNT]
"""List of all supported metric types."""

# Output Formats
OUTPUT_FORMAT_SVG: str = 'svg'
"""SVG output format identifier."""

OUTPUT_FORMAT_PNG: str = 'png'
"""PNG output format identifier."""

SUPPORTED_OUTPUT_FORMATS: List[str] = [OUTPUT_FORMAT_SVG, OUTPUT_FORMAT_PNG]
"""List of all supported output formats."""

# Soma Sides
SOMA_SIDE_LEFT: str = 'left'
"""Left hemisphere identifier."""

SOMA_SIDE_RIGHT: str = 'right'
"""Right hemisphere identifier."""

SOMA_SIDE_COMBINED: str = 'combined'
"""Combined hemisphere identifier."""

SUPPORTED_SOMA_SIDES: List[str] = [SOMA_SIDE_LEFT, SOMA_SIDE_RIGHT, SOMA_SIDE_COMBINED]
"""List of all supported soma sides."""

# Column Status
STATUS_HAS_DATA: str = 'has_data'
"""Status for columns with available data."""

STATUS_NO_DATA: str = 'no_data'
"""Status for columns with no data available."""

STATUS_NOT_IN_REGION: str = 'not_in_region'
"""Status for columns not present in the specified region."""

# Tooltip Labels
TOOLTIP_SYNAPSE_LABEL: str = "Synapse count"
"""Label used in tooltips for synapse data."""

TOOLTIP_CELL_LABEL: str = "Cell count"
"""Label used in tooltips for cell count data."""

# File and Directory Names
EYEMAPS_SUBDIRECTORY: str = 'eyemaps'
"""Default subdirectory name for saving eyemap files."""

# Error Messages
ERROR_NO_COLUMNS: str = "No columns provided"
"""Error message when no column data is available."""

ERROR_INVALID_METRIC: str = "Invalid metric type: {metric}. Supported types: {supported}"
"""Template for invalid metric type error messages."""

ERROR_INVALID_OUTPUT_FORMAT: str = "Invalid output format: {format}. Supported formats: {supported}"
"""Template for invalid output format error messages."""

ERROR_INVALID_SOMA_SIDE: str = "Invalid soma side: {side}. Supported sides: {supported}"
"""Template for invalid soma side error messages."""

# Performance Constants
DEFAULT_PROCESSING_TIMEOUT: int = 300
"""Default timeout for processing operations in seconds."""

MAX_CONCURRENT_RENDERS: int = 4
"""Maximum number of concurrent rendering operations."""

# Layer Processing
MAX_LAYER_INDEX: int = 10
"""Maximum expected layer index for layer-based processing."""

LAYER_INDEX_BASE: int = 1
"""Base index for layer numbering (1-based)."""

# Color Configuration
COLOR_STEPS: int = 5
"""Number of distinct color steps in color mapping."""

# Template Names
TEMPLATE_EYEMAP_SVG: str = 'eyemap.svg.jinja'
"""Template filename for SVG eyemap generation."""

# Validation Constants
MIN_HEX_SIZE: int = 1
"""Minimum allowed hexagon size."""

MAX_HEX_SIZE: int = 50
"""Maximum allowed hexagon size."""

MIN_SPACING_FACTOR: float = 1.0
"""Minimum allowed spacing factor."""

MAX_SPACING_FACTOR: float = 3.0
"""Maximum allowed spacing factor."""

# Cache Configuration
DEFAULT_CACHE_SIZE: int = 100
"""Default size for internal caches."""

CACHE_TTL_SECONDS: int = 3600
"""Default time-to-live for cached items in seconds."""
