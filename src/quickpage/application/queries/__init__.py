"""
Application queries for QuickPage.

Queries represent read operations in the application.
They are part of the Command Query Responsibility Segregation (CQRS) pattern.
"""

from .neuron_type_queries import (
    GetNeuronTypeQuery,
    GetNeuronTypeQueryResult,
    ListNeuronTypesQuery,
    ListNeuronTypesQueryResult,
    NeuronTypeInfo,
    SearchNeuronsQuery,
    SearchNeuronsQueryResult
)

from .connectivity_queries import (
    GetConnectivityQuery,
    GetConnectivityQueryResult
)

from .dataset_queries import (
    GetDatasetInfoQuery,
    GetDatasetInfoQueryResult,
    DatasetInfo
)

# Export all queries and results
__all__ = [
    # Neuron type queries
    'GetNeuronTypeQuery',
    'GetNeuronTypeQueryResult',
    'ListNeuronTypesQuery',
    'ListNeuronTypesQueryResult',
    'SearchNeuronsQuery',
    'SearchNeuronsQueryResult',

    # Connectivity queries
    'GetConnectivityQuery',
    'GetConnectivityQueryResult',

    # Dataset queries
    'GetDatasetInfoQuery',
    'GetDatasetInfoQueryResult',

    # Supporting types
    'NeuronTypeInfo',
    'DatasetInfo'
]
