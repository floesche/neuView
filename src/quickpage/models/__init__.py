"""
Models for QuickPage application.

This module contains data models and request/response objects used throughout
the QuickPage application for type safety and clear interfaces.
"""

# Import existing models from domain_models.py
from .domain_models import (
    # Value objects
    BodyId,
    NeuronTypeName,
    SomaSide,
    SynapseCount,
    RoiName,

    # Entities
    Neuron,
    NeuronCollection,
    NeuronTypeStatistics,
    NeuronTypeConnectivity,
    ConnectivityPartner
)

# Import our new page generation models
from .page_generation import (
    PageGenerationRequest,
    PageGenerationResponse,
    AnalysisResults,
    URLCollection,
    PageGenerationMode
)

__all__ = [
    # Existing models
    'BodyId',
    'NeuronTypeName',
    'SomaSide',
    'SynapseCount',
    'RoiName',
    'Neuron',
    'NeuronCollection',
    'NeuronTypeStatistics',
    'NeuronTypeConnectivity',
    'ConnectivityPartner',

    # New page generation models
    'PageGenerationRequest',
    'PageGenerationResponse',
    'AnalysisResults',
    'URLCollection',
    'PageGenerationMode'
]
