"""
Application queries for QuickPage.

Queries represent read operations in the application.
They are part of the Command Query Responsibility Segregation (CQRS) pattern.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
from ...core.value_objects import NeuronTypeName, SomaSide
from ...core.entities import NeuronCollection, NeuronTypeStatistics, NeuronTypeConnectivity


@dataclass(frozen=True)
class GetNeuronTypeQuery:
    """
    Query to retrieve neurons of a specific type.

    This query fetches all neurons matching the specified type
    and optional filtering criteria.
    """
    neuron_type: NeuronTypeName
    soma_side: SomaSide = None
    min_synapse_count: int = 0
    include_roi_data: bool = True
    requested_at: datetime = None

    def __post_init__(self):
        if self.requested_at is None:
            object.__setattr__(self, 'requested_at', datetime.now())
        if self.soma_side is None:
            object.__setattr__(self, 'soma_side', SomaSide('all'))

    def validate(self) -> List[str]:
        """
        Validate the query parameters.

        Returns:
            List of validation errors, empty if valid
        """
        errors = []

        if not str(self.neuron_type).strip():
            errors.append("Neuron type cannot be empty")

        if self.min_synapse_count < 0:
            errors.append("Minimum synapse count cannot be negative")

        return errors

    def is_valid(self) -> bool:
        """Check if the query is valid."""
        return len(self.validate()) == 0


@dataclass(frozen=True)
class GetNeuronTypeQueryResult:
    """Result of a GetNeuronTypeQuery."""
    neuron_collection: NeuronCollection
    statistics: NeuronTypeStatistics
    query_executed_at: datetime = None

    def __post_init__(self):
        if self.query_executed_at is None:
            object.__setattr__(self, 'query_executed_at', datetime.now())


@dataclass(frozen=True)
class ListNeuronTypesQuery:
    """
    Query to list available neuron types.

    This query retrieves a list of neuron types with optional filtering
    and metadata.
    """
    include_soma_sides: bool = False
    include_statistics: bool = False
    filter_pattern: Optional[str] = None
    exclude_types: List[str] = None
    max_results: int = 100
    sort_by: str = "name"  # "name", "count", "random"
    requested_at: datetime = None

    def __post_init__(self):
        if self.requested_at is None:
            object.__setattr__(self, 'requested_at', datetime.now())
        if self.exclude_types is None:
            object.__setattr__(self, 'exclude_types', [])

    def validate(self) -> List[str]:
        """
        Validate the query parameters.

        Returns:
            List of validation errors, empty if valid
        """
        errors = []

        if self.max_results <= 0:
            errors.append("Max results must be positive")

        valid_sort_options = {"name", "count", "random"}
        if self.sort_by not in valid_sort_options:
            errors.append(f"Sort by must be one of {valid_sort_options}")

        return errors

    def is_valid(self) -> bool:
        """Check if the query is valid."""
        return len(self.validate()) == 0


@dataclass(frozen=True)
class NeuronTypeInfo:
    """Information about a neuron type."""
    name: NeuronTypeName
    available_soma_sides: List[str]
    total_count: int
    statistics: Optional[NeuronTypeStatistics] = None


@dataclass(frozen=True)
class ListNeuronTypesQueryResult:
    """Result of a ListNeuronTypesQuery."""
    neuron_types: List[NeuronTypeInfo]
    total_available: int
    query_executed_at: datetime = None

    def __post_init__(self):
        if self.query_executed_at is None:
            object.__setattr__(self, 'query_executed_at', datetime.now())


@dataclass(frozen=True)
class GetConnectivityQuery:
    """
    Query to retrieve connectivity information for a neuron type.

    This query fetches synaptic connectivity data including
    upstream and downstream partners.
    """
    neuron_type: NeuronTypeName
    include_partner_details: bool = True
    max_partners: int = 50
    min_synapse_threshold: int = 1
    requested_at: datetime = None

    def __post_init__(self):
        if self.requested_at is None:
            object.__setattr__(self, 'requested_at', datetime.now())

    def validate(self) -> List[str]:
        """
        Validate the query parameters.

        Returns:
            List of validation errors, empty if valid
        """
        errors = []

        if not str(self.neuron_type).strip():
            errors.append("Neuron type cannot be empty")

        if self.max_partners <= 0:
            errors.append("Max partners must be positive")

        if self.min_synapse_threshold < 0:
            errors.append("Minimum synapse threshold cannot be negative")

        return errors

    def is_valid(self) -> bool:
        """Check if the query is valid."""
        return len(self.validate()) == 0


@dataclass(frozen=True)
class GetConnectivityQueryResult:
    """Result of a GetConnectivityQuery."""
    connectivity: NeuronTypeConnectivity
    query_executed_at: datetime = None

    def __post_init__(self):
        if self.query_executed_at is None:
            object.__setattr__(self, 'query_executed_at', datetime.now())


@dataclass(frozen=True)
class GetDatasetInfoQuery:
    """
    Query to retrieve dataset information.

    This query fetches metadata about the connected dataset
    including version, statistics, and connection status.
    """
    include_statistics: bool = True
    include_connection_details: bool = False
    requested_at: datetime = None

    def __post_init__(self):
        if self.requested_at is None:
            object.__setattr__(self, 'requested_at', datetime.now())


@dataclass(frozen=True)
class DatasetInfo:
    """Information about the dataset."""
    name: str
    version: str
    server_url: str
    connection_status: str
    total_neurons: Optional[int] = None
    total_synapses: Optional[int] = None
    available_neuron_types: Optional[int] = None


@dataclass(frozen=True)
class GetDatasetInfoQueryResult:
    """Result of a GetDatasetInfoQuery."""
    dataset_info: DatasetInfo
    query_executed_at: datetime = None

    def __post_init__(self):
        if self.query_executed_at is None:
            object.__setattr__(self, 'query_executed_at', datetime.now())


@dataclass(frozen=True)
class SearchNeuronsQuery:
    """
    Query to search for neurons with flexible criteria.

    This query allows searching for neurons using various criteria
    beyond just neuron type.
    """
    neuron_type: Optional[NeuronTypeName] = None
    soma_side: Optional[SomaSide] = None
    min_pre_synapses: Optional[int] = None
    max_pre_synapses: Optional[int] = None
    min_post_synapses: Optional[int] = None
    max_post_synapses: Optional[int] = None
    required_rois: List[str] = None
    excluded_rois: List[str] = None
    limit: int = 1000
    requested_at: datetime = None

    def __post_init__(self):
        if self.requested_at is None:
            object.__setattr__(self, 'requested_at', datetime.now())
        if self.required_rois is None:
            object.__setattr__(self, 'required_rois', [])
        if self.excluded_rois is None:
            object.__setattr__(self, 'excluded_rois', [])

    def validate(self) -> List[str]:
        """
        Validate the query parameters.

        Returns:
            List of validation errors, empty if valid
        """
        errors = []

        if self.limit <= 0:
            errors.append("Limit must be positive")

        if self.min_pre_synapses is not None and self.min_pre_synapses < 0:
            errors.append("Minimum pre-synapses cannot be negative")

        if self.max_pre_synapses is not None and self.max_pre_synapses < 0:
            errors.append("Maximum pre-synapses cannot be negative")

        if self.min_post_synapses is not None and self.min_post_synapses < 0:
            errors.append("Minimum post-synapses cannot be negative")

        if self.max_post_synapses is not None and self.max_post_synapses < 0:
            errors.append("Maximum post-synapses cannot be negative")

        if (self.min_pre_synapses is not None and
            self.max_pre_synapses is not None and
            self.min_pre_synapses > self.max_pre_synapses):
            errors.append("Minimum pre-synapses cannot be greater than maximum")

        if (self.min_post_synapses is not None and
            self.max_post_synapses is not None and
            self.min_post_synapses > self.max_post_synapses):
            errors.append("Minimum post-synapses cannot be greater than maximum")

        # Check for conflicts between required and excluded ROIs
        if self.required_rois and self.excluded_rois:
            conflicts = set(self.required_rois) & set(self.excluded_rois)
            if conflicts:
                errors.append(f"ROIs cannot be both required and excluded: {conflicts}")

        return errors

    def is_valid(self) -> bool:
        """Check if the query is valid."""
        return len(self.validate()) == 0


@dataclass(frozen=True)
class SearchNeuronsQueryResult:
    """Result of a SearchNeuronsQuery."""
    neuron_collection: NeuronCollection
    total_matches: int
    query_executed_at: datetime = None

    def __post_init__(self):
        if self.query_executed_at is None:
            object.__setattr__(self, 'query_executed_at', datetime.now())


# Export all queries and results
__all__ = [
    # Queries
    'GetNeuronTypeQuery',
    'ListNeuronTypesQuery',
    'GetConnectivityQuery',
    'GetDatasetInfoQuery',
    'SearchNeuronsQuery',

    # Results
    'GetNeuronTypeQueryResult',
    'ListNeuronTypesQueryResult',
    'GetConnectivityQueryResult',
    'GetDatasetInfoQueryResult',
    'SearchNeuronsQueryResult',

    # Supporting types
    'NeuronTypeInfo',
    'DatasetInfo'
]
