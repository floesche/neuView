"""
Dataset query classes for the application layer.

These queries handle operations related to retrieving dataset
information, metadata, and connection status.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class GetDatasetInfoQuery:
    """
    Query to retrieve dataset information.

    This query fetches metadata about the connected dataset
    including version, statistics, and connection status.
    """
    include_statistics: bool = True
    include_connection_details: bool = False
    requested_at: Optional[datetime] = None

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
    query_executed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.query_executed_at is None:
            object.__setattr__(self, 'query_executed_at', datetime.now())
