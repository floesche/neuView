"""
NeuronType class for encapsulating neuron data and metadata.
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .neuprint_connector import NeuPrintConnector
from .config import NeuronTypeConfig


@dataclass
class NeuronSummary:
    """Summary statistics for a neuron type."""
    total_count: int
    left_count: int
    right_count: int
    type_name: str
    soma_side: str
    total_pre_synapses: int
    total_post_synapses: int
    avg_pre_synapses: float
    avg_post_synapses: float


@dataclass
class ConnectivityData:
    """Connectivity information for neurons."""
    upstream: List[Dict[str, Any]] = field(default_factory=list)
    downstream: List[Dict[str, Any]] = field(default_factory=list)
    note: str = ""


class NeuronType:
    """
    Represents a neuron type with its data fetched from NeuPrint.
    
    This class encapsulates all data and metadata for a specific neuron type,
    handling the fetching from NeuPrint and providing a clean interface
    for the page generator.
    """
    
    def __init__(self, name: str, config: NeuronTypeConfig, 
                 connector: NeuPrintConnector, soma_side: str = 'both'):
        """
        Initialize a NeuronType instance.
        
        Args:
            name: The neuron type name
            config: Configuration for this neuron type
            connector: NeuPrint connector for data fetching
            soma_side: Which soma side to fetch ('left', 'right', 'both')
        """
        self.name = name
        self.config = config
        self.connector = connector
        self.soma_side = soma_side
        self.fetch_time: Optional[datetime] = None
        
        # Data containers
        self._neurons_df: Optional[pd.DataFrame] = None
        self._roi_counts: Optional[pd.DataFrame] = None
        self._summary: Optional[NeuronSummary] = None
        self._connectivity: Optional[ConnectivityData] = None
        self._is_fetched = False
    
    def fetch_data(self) -> None:
        """Fetch neuron data from NeuPrint."""
        try:
            raw_data = self.connector.get_neuron_data(self.name, self.soma_side)
            
            # Store raw data
            self._neurons_df = raw_data['neurons']
            self._roi_counts = raw_data.get('roi_counts', pd.DataFrame())
            
            # Convert summary to dataclass
            summary_data = raw_data['summary']
            self._summary = NeuronSummary(
                total_count=summary_data['total_count'],
                left_count=summary_data['left_count'],
                right_count=summary_data['right_count'],
                type_name=summary_data['type'],
                soma_side=summary_data['soma_side'],
                total_pre_synapses=summary_data['total_pre_synapses'],
                total_post_synapses=summary_data['total_post_synapses'],
                avg_pre_synapses=summary_data['avg_pre_synapses'],
                avg_post_synapses=summary_data['avg_post_synapses']
            )
            
            # Convert connectivity to dataclass
            conn_data = raw_data.get('connectivity', {})
            self._connectivity = ConnectivityData(
                upstream=conn_data.get('upstream', []),
                downstream=conn_data.get('downstream', []),
                note=conn_data.get('note', '')
            )
            
            self.fetch_time = datetime.now()
            self._is_fetched = True
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch data for neuron type {self.name}: {e}")
    
    @property
    def is_fetched(self) -> bool:
        """Check if data has been fetched."""
        return self._is_fetched
    
    @property
    def neurons(self) -> pd.DataFrame:
        """Get the neurons DataFrame."""
        if not self._is_fetched:
            self.fetch_data()
        return self._neurons_df if self._neurons_df is not None else pd.DataFrame()
    
    @property
    def roi_counts(self) -> pd.DataFrame:
        """Get the ROI counts DataFrame."""
        if not self._is_fetched:
            self.fetch_data()
        return self._roi_counts if self._roi_counts is not None else pd.DataFrame()
    
    @property
    def summary(self) -> NeuronSummary:
        """Get the summary statistics."""
        if not self._is_fetched:
            self.fetch_data()
        if self._summary is None:
            raise RuntimeError("Summary data not available")
        return self._summary
    
    @property
    def connectivity(self) -> ConnectivityData:
        """Get the connectivity data."""
        if not self._is_fetched:
            self.fetch_data()
        if self._connectivity is None:
            raise RuntimeError("Connectivity data not available")
        return self._connectivity
    
    @property
    def description(self) -> str:
        """Get the neuron type description."""
        return self.config.description or f"Neuron type: {self.name}"
    
    @property
    def query_type(self) -> str:
        """Get the query type used for this neuron type."""
        return self.config.query_type or "type"
    
    def get_neuron_count(self, side: Optional[str] = None) -> int:
        """
        Get neuron count for a specific side or total.
        
        Args:
            side: 'left', 'right', or None for total
            
        Returns:
            Number of neurons
        """
        summary = self.summary  # This will trigger fetch_data if needed
        
        if side is None:
            return summary.total_count
        elif side.lower() == 'left':
            return summary.left_count
        elif side.lower() == 'right':
            return summary.right_count
        else:
            raise ValueError(f"Invalid side: {side}. Use 'left', 'right', or None")
    
    def get_synapse_stats(self) -> Dict[str, Any]:
        """Get synapse statistics."""
        summary = self.summary  # This will trigger fetch_data if needed
        
        return {
            'total_pre': summary.total_pre_synapses,
            'total_post': summary.total_post_synapses,
            'avg_pre': summary.avg_pre_synapses,
            'avg_post': summary.avg_post_synapses
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the neuron type data to a dictionary for template rendering.
        
        This method provides compatibility with the existing page generator
        by returning data in the same format as the old neuprint_connector.
        """
        summary = self.summary  # This will trigger fetch_data if needed
        connectivity = self.connectivity
        
        return {
            'neurons': self._neurons_df,
            'roi_counts': self._roi_counts,
            'summary': {
                'total_count': summary.total_count,
                'left_count': summary.left_count,
                'right_count': summary.right_count,
                'type': summary.type_name,
                'soma_side': summary.soma_side,
                'total_pre_synapses': summary.total_pre_synapses,
                'total_post_synapses': summary.total_post_synapses,
                'avg_pre_synapses': summary.avg_pre_synapses,
                'avg_post_synapses': summary.avg_post_synapses
            },
            'connectivity': {
                'upstream': connectivity.upstream,
                'downstream': connectivity.downstream,
                'note': connectivity.note
            },
            'type': self.name,
            'soma_side': self.soma_side,
            'config': {
                'description': self.description,
                'query_type': self.query_type
            },
            'fetch_time': self.fetch_time
        }
    
    def __repr__(self) -> str:
        """String representation of the neuron type."""
        status = "fetched" if self._is_fetched else "not fetched"
        count = ""
        if self._is_fetched and self._summary is not None:
            count = f" ({self._summary.total_count} neurons)"
        return f"NeuronType('{self.name}', {self.soma_side}, {status}{count})"
