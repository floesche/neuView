"""
Data Structures for Data Processing Module

This module defines the core data structures used throughout the data processing
system for hexagon grid generation. These structures provide type safety and
clear interfaces for data flow between components.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set, Tuple
from enum import Enum


class ColumnStatus(Enum):
    """Status of a column in the visualization."""
    HAS_DATA = "has_data"
    NO_DATA = "no_data"
    NOT_IN_REGION = "not_in_region"
    EXCLUDED = "excluded"


class MetricType(Enum):
    """Type of metric being processed."""
    SYNAPSE_DENSITY = "synapse_density"
    CELL_COUNT = "cell_count"


class SomaSide(Enum):
    """Side of the soma being processed."""
    LEFT = "left"
    RIGHT = "right"
    COMBINED = "combined"
    L = "L"
    R = "R"


@dataclass
class ColumnCoordinate:
    """Basic column coordinate information."""
    hex1: int
    hex2: int
    region: Optional[str] = None

    def __hash__(self) -> int:
        return hash((self.hex1, self.hex2))

    def __eq__(self, other) -> bool:
        if not isinstance(other, ColumnCoordinate):
            return False
        return self.hex1 == other.hex1 and self.hex2 == other.hex2

    def to_tuple(self) -> Tuple[int, int]:
        """Convert to tuple for use as dictionary key."""
        return (self.hex1, self.hex2)


@dataclass
class LayerData:
    """Data for a single layer within a column."""
    layer_index: int
    synapse_count: int = 0
    neuron_count: int = 0
    value: float = 0.0
    color: Optional[str] = None

    def __post_init__(self):
        """Validate layer data after initialization."""
        if self.layer_index < 0:
            raise ValueError("Layer index cannot be negative")
        if self.synapse_count < 0:
            raise ValueError("Synapse count cannot be negative")
        if self.neuron_count < 0:
            raise ValueError("Neuron count cannot be negative")


@dataclass
class ColumnData:
    """Complete data for a single column."""
    coordinate: ColumnCoordinate
    region: str
    side: str
    total_synapses: int = 0
    neuron_count: int = 0
    layers: List[LayerData] = field(default_factory=list)
    status: ColumnStatus = ColumnStatus.HAS_DATA
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate column data after initialization."""
        if not self.region:
            raise ValueError("Region cannot be empty")
        if self.side not in ['L', 'R']:
            raise ValueError(f"Invalid side: {self.side}. Must be 'L' or 'R'")
        if self.total_synapses < 0:
            raise ValueError("Total synapses cannot be negative")
        if self.neuron_count < 0:
            raise ValueError("Neuron count cannot be negative")

    @property
    def synapses_per_layer(self) -> List[int]:
        """Get synapse counts per layer."""
        return [layer.synapse_count for layer in self.layers]

    @property
    def neurons_per_layer(self) -> List[int]:
        """Get neuron counts per layer."""
        return [layer.neuron_count for layer in self.layers]

    @property
    def key(self) -> Tuple[str, str, int, int]:
        """Get unique key for this column."""
        return (self.region, self.side, self.coordinate.hex1, self.coordinate.hex2)


@dataclass
class ProcessedColumn:
    """Column data after processing for visualization."""
    coordinate: ColumnCoordinate
    x: float
    y: float
    value: float
    color: str
    status: ColumnStatus
    region: str
    side: str
    metric_type: MetricType
    layer_values: List[float] = field(default_factory=list)
    layer_colors: List[str] = field(default_factory=list)
    tooltip: str = ""
    tooltip_layers: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def hex1(self) -> int:
        """Convenience property for hex1 coordinate."""
        return self.coordinate.hex1

    @property
    def hex2(self) -> int:
        """Convenience property for hex2 coordinate."""
        return self.coordinate.hex2


@dataclass
class ThresholdData:
    """Threshold configuration for value-to-color mapping."""
    all_layers: List[float] = field(default_factory=list)
    layers: Dict[int, List[float]] = field(default_factory=dict)
    min_value: float = 0.0
    max_value: float = 1.0

    def __post_init__(self):
        """Validate threshold data after initialization."""
        if self.min_value >= self.max_value:
            raise ValueError("min_value must be less than max_value")
        if self.all_layers and len(self.all_layers) == 0:
            raise ValueError("all_layers cannot be empty if provided")


@dataclass
class MinMaxData:
    """Min/Max values for normalization across regions and metrics."""
    min_syn_region: Dict[str, float] = field(default_factory=dict)
    max_syn_region: Dict[str, float] = field(default_factory=dict)
    min_cells_region: Dict[str, float] = field(default_factory=dict)
    max_cells_region: Dict[str, float] = field(default_factory=dict)
    global_min_syn: float = 0.0
    global_max_syn: float = 1.0
    global_min_cells: float = 0.0
    global_max_cells: float = 1.0

    def get_min_for_metric(self, metric_type: MetricType, region: str) -> float:
        """Get minimum value for specific metric and region."""
        if metric_type == MetricType.SYNAPSE_DENSITY:
            return self.min_syn_region.get(region, self.global_min_syn)
        else:
            return self.min_cells_region.get(region, self.global_min_cells)

    def get_max_for_metric(self, metric_type: MetricType, region: str) -> float:
        """Get maximum value for specific metric and region."""
        if metric_type == MetricType.SYNAPSE_DENSITY:
            return self.max_syn_region.get(region, self.global_max_syn)
        else:
            return self.max_cells_region.get(region, self.global_max_cells)


@dataclass
class ProcessingConfig:
    """Configuration for data processing operations."""
    metric_type: MetricType
    soma_side: SomaSide
    region_name: str
    neuron_type: Optional[str] = None
    mirror_side: Optional[str] = None
    output_format: str = 'svg'
    include_tooltips: bool = True
    validate_data: bool = True
    precision: int = 2

    def __post_init__(self):
        """Validate processing configuration."""
        if not self.region_name:
            raise ValueError("Region name cannot be empty")
        if self.output_format not in ['svg', 'png']:
            raise ValueError(f"Unsupported output format: {self.output_format}")
        if self.precision < 0:
            raise ValueError("Precision cannot be negative")


@dataclass
class ValidationResult:
    """Result of data validation operations."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validated_count: int = 0
    rejected_count: int = 0

    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0

    @property
    def summary(self) -> str:
        """Get a summary of validation results."""
        return (f"Validation {'passed' if self.is_valid else 'failed'}: "
                f"{self.validated_count} valid, {self.rejected_count} rejected, "
                f"{len(self.errors)} errors, {len(self.warnings)} warnings")


@dataclass
class DataProcessingResult:
    """Result of data processing operations."""
    processed_columns: List[ProcessedColumn]
    validation_result: ValidationResult
    threshold_data: Optional[ThresholdData] = None
    min_max_data: Optional[MinMaxData] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_successful(self) -> bool:
        """Check if processing was successful."""
        return self.validation_result.is_valid and len(self.processed_columns) > 0

    @property
    def column_count(self) -> int:
        """Get number of processed columns."""
        return len(self.processed_columns)

    def get_columns_by_status(self, status: ColumnStatus) -> List[ProcessedColumn]:
        """Get columns filtered by status."""
        return [col for col in self.processed_columns if col.status == status]

    def get_data_columns(self) -> List[ProcessedColumn]:
        """Get columns that have data."""
        return self.get_columns_by_status(ColumnStatus.HAS_DATA)


# Type aliases for common data structures
ColumnDataMap = Dict[Tuple[str, int, int], ColumnData]
RegionColumnsMap = Dict[str, Set[Tuple[int, int]]]
ThresholdMap = Dict[str, ThresholdData]
