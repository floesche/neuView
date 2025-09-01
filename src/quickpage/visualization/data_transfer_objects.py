"""
Data transfer objects for hexagon grid generation.

This module provides structured data objects to encapsulate related parameters
and reduce method signature complexity in the hexagon grid generator.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Set
from pathlib import Path


@dataclass
class GridGenerationRequest:
    """
    Encapsulates all parameters needed for comprehensive grid generation.

    This replaces the complex parameter list in generate_comprehensive_region_hexagonal_grids.
    """
    column_summary: List[Dict]
    thresholds_all: Dict
    all_possible_columns: List[Dict]
    region_columns_map: Dict[str, Set]
    neuron_type: str
    soma_side: str
    output_format: str = 'svg'
    save_to_files: bool = False
    min_max_data: Optional[Dict] = None

    def __post_init__(self):
        """Validate the request parameters."""
        if not self.neuron_type:
            raise ValueError("neuron_type cannot be empty")

        if self.soma_side not in ['left', 'right', 'combined']:
            raise ValueError(f"Invalid soma_side: {self.soma_side}")

        if self.output_format not in ['svg', 'png']:
            raise ValueError(f"Invalid output_format: {self.output_format}")


@dataclass
class SingleRegionGridRequest:
    """
    Encapsulates parameters for single region grid generation.

    This replaces the complex parameter list in generate_comprehensive_single_region_grid.
    """
    all_possible_columns: List[Dict]
    region_column_coords: Set
    data_map: Dict
    metric_type: str
    region_name: str
    thresholds: Optional[Dict] = None
    neuron_type: Optional[str] = None
    soma_side: Optional[str] = None
    output_format: str = 'svg'
    other_regions_coords: Optional[Set] = None
    min_max_data: Optional[Dict] = None

    def __post_init__(self):
        """Validate the request parameters."""
        if self.metric_type not in ['synapse_density', 'cell_count']:
            raise ValueError(f"Invalid metric_type: {self.metric_type}")

        if not self.region_name:
            raise ValueError("region_name cannot be empty")


@dataclass
class RenderingRequest:
    """
    Encapsulates parameters for rendering operations.

    This simplifies rendering method calls and makes them more maintainable.
    """
    hexagons: List[Dict]
    min_val: float
    max_val: float
    thresholds: Dict
    title: str
    subtitle: str
    metric_type: str
    soma_side: str
    output_format: str = 'svg'
    save_to_file: bool = False
    filename: Optional[str] = None

    def __post_init__(self):
        """Validate the rendering request."""
        if not self.hexagons:
            raise ValueError("hexagons list cannot be empty")

        if self.min_val >= self.max_val:
            raise ValueError("min_val must be less than max_val")


@dataclass
class GeneratorConfiguration:
    """
    Encapsulates configuration parameters for the hexagon grid generator.

    This provides a structured way to manage generator settings.
    """
    hex_size: int = 6
    spacing_factor: float = 1.1
    output_dir: Optional[Path] = None
    eyemaps_dir: Optional[Path] = None
    embed_mode: bool = False

    def __post_init__(self):
        """Validate and process configuration."""
        if self.hex_size <= 0:
            raise ValueError("hex_size must be positive")

        if self.spacing_factor <= 0:
            raise ValueError("spacing_factor must be positive")

        # Set eyemaps_dir default if not provided
        if self.eyemaps_dir is None and self.output_dir is not None:
            self.eyemaps_dir = self.output_dir / 'eyemaps'


@dataclass
class TooltipGenerationRequest:
    """
    Encapsulates parameters for tooltip generation.

    This simplifies the tooltip generation method signature.
    """
    hexagons: List[Dict]
    soma_side: str
    metric_type: str

    def __post_init__(self):
        """Validate tooltip generation parameters."""
        if self.metric_type not in ['synapse_density', 'cell_count']:
            raise ValueError(f"Invalid metric_type: {self.metric_type}")


@dataclass
class GridGenerationResult:
    """
    Encapsulates the results of grid generation operations.

    This provides a structured way to return generation results with metadata.
    """
    region_grids: Dict[str, Dict[str, str]]
    processing_time: float
    success: bool
    error_message: Optional[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.warnings is None:
            self.warnings = []


@dataclass
class ColorMappingRequest:
    """
    Encapsulates parameters for color mapping operations.

    This simplifies color mapping method calls.
    """
    values: List[float]
    min_value: float
    max_value: float
    thresholds: Optional[Dict] = None
    metric_type: str = 'synapse_density'

    def __post_init__(self):
        """Validate color mapping parameters."""
        if not self.values:
            raise ValueError("values list cannot be empty")

        if self.min_value >= self.max_value:
            raise ValueError("min_value must be less than max_value")


@dataclass
class FileOperationRequest:
    """
    Encapsulates parameters for file operations.

    This simplifies file saving and loading operations.
    """
    content: str
    filename: str
    output_format: str
    output_dir: Optional[Path] = None

    def __post_init__(self):
        """Validate file operation parameters."""
        if not self.content:
            raise ValueError("content cannot be empty")

        if not self.filename:
            raise ValueError("filename cannot be empty")

        if self.output_format not in ['svg', 'png']:
            raise ValueError(f"Invalid output_format: {self.output_format}")


# Factory functions for creating commonly used data transfer objects

def create_grid_generation_request(
    column_summary: List[Dict],
    thresholds_all: Dict,
    all_possible_columns: List[Dict],
    region_columns_map: Dict[str, Set],
    neuron_type: str,
    soma_side: str,
    **kwargs
) -> GridGenerationRequest:
    """
    Factory function to create a GridGenerationRequest with defaults.

    Args:
        column_summary: List of column data dictionaries
        thresholds_all: Threshold values dictionary
        all_possible_columns: List of all possible columns
        region_columns_map: Region to columns mapping
        neuron_type: Type of neuron
        soma_side: Side of soma
        **kwargs: Additional optional parameters

    Returns:
        GridGenerationRequest object
    """
    return GridGenerationRequest(
        column_summary=column_summary,
        thresholds_all=thresholds_all,
        all_possible_columns=all_possible_columns,
        region_columns_map=region_columns_map,
        neuron_type=neuron_type,
        soma_side=soma_side,
        **kwargs
    )


def create_rendering_request(
    hexagons: List[Dict],
    min_val: float,
    max_val: float,
    thresholds: Dict,
    title: str,
    subtitle: str,
    metric_type: str,
    soma_side: str,
    **kwargs
) -> RenderingRequest:
    """
    Factory function to create a RenderingRequest with defaults.

    Args:
        hexagons: List of hexagon data
        min_val: Minimum value
        max_val: Maximum value
        thresholds: Threshold values
        title: Chart title
        subtitle: Chart subtitle
        metric_type: Type of metric
        soma_side: Side of soma
        **kwargs: Additional optional parameters

    Returns:
        RenderingRequest object
    """
    return RenderingRequest(
        hexagons=hexagons,
        min_val=min_val,
        max_val=max_val,
        thresholds=thresholds,
        title=title,
        subtitle=subtitle,
        metric_type=metric_type,
        soma_side=soma_side,
        **kwargs
    )


def create_single_region_request(
    all_possible_columns: List[Dict],
    region_column_coords: Set,
    data_map: Dict,
    metric_type: str,
    region_name: str,
    **kwargs
) -> SingleRegionGridRequest:
    """
    Factory function to create a SingleRegionGridRequest with defaults.

    Args:
        all_possible_columns: List of all possible columns
        region_column_coords: Region column coordinates
        data_map: Data mapping dictionary
        metric_type: Type of metric
        region_name: Name of the region
        **kwargs: Additional optional parameters

    Returns:
        SingleRegionGridRequest object
    """
    return SingleRegionGridRequest(
        all_possible_columns=all_possible_columns,
        region_column_coords=region_column_coords,
        data_map=data_map,
        metric_type=metric_type,
        region_name=region_name,
        **kwargs
    )
