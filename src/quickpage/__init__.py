"""
QuickPage - Generate HTML pages for neuron types from neuprint data.
"""

from .config import Config
from .neuprint_connector import NeuPrintConnector
from .page_generator import PageGenerator
from .neuron_type import NeuronType, NeuronSummary, ConnectivityData
from .dataset_adapters import (
    DatasetAdapter, CNSAdapter, HemibrainAdapter, OpticLobeAdapter,
    DatasetAdapterFactory, get_dataset_adapter
)

__version__ = "0.1.0"
__all__ = [
    "Config", "NeuPrintConnector", "PageGenerator", 
    "NeuronType", "NeuronSummary", "ConnectivityData",
    "DatasetAdapter", "CNSAdapter", "HemibrainAdapter", "OpticLobeAdapter",
    "DatasetAdapterFactory", "get_dataset_adapter"
]