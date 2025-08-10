"""
Domain entities for QuickPage.

Entities are objects that have a distinct identity that runs through time
and different representations. They are defined by their identity rather
than their attributes.
"""

from .neuron import Neuron
from .neuron_collection import NeuronCollection, NeuronTypeStatistics
from .connectivity import ConnectivityPartner, NeuronTypeConnectivity

# Export all entities
__all__ = [
    'Neuron',
    'NeuronCollection',
    'NeuronTypeStatistics',
    'ConnectivityPartner',
    'NeuronTypeConnectivity'
]
