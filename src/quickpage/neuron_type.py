"""
NeuronType class for encapsulating neuron data and metadata.

This module provides a comprehensive object-oriented interface for working
with neuron data from NeuPrint, including lazy loading, statistics calculation,
and integration with the page generation system.
"""

import math
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
    middle_count: int
    type_name: str
    soma_side: str
    total_pre_synapses: int
    total_post_synapses: int
    avg_pre_synapses: float
    avg_post_synapses: float
    consensus_nt: Optional[str] = None
    celltype_predicted_nt: Optional[str] = None
    celltype_predicted_nt_confidence: Optional[float] = None
    celltype_total_nt_predictions: Optional[int] = None
    cell_class: Optional[str] = None
    cell_subclass: Optional[str] = None
    cell_superclass: Optional[str] = None


@dataclass
class ConnectivityData:
    """
    Connectivity information for neurons.

    This dataclass encapsulates upstream and downstream connectivity
    data for neuron types, including partner information and weights.
    """
    upstream: List[Dict[str, Any]] = field(default_factory=list)
    downstream: List[Dict[str, Any]] = field(default_factory=list)
    regional_connections: Dict[str, Any] = field(default_factory=dict)
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
        self._complete_summary: Optional[NeuronSummary] = None
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
                middle_count=summary_data['middle_count'],
                type_name=summary_data['type_name'],
                soma_side=summary_data['soma_side'],
                total_pre_synapses=summary_data['total_pre_synapses'],
                total_post_synapses=summary_data['total_post_synapses'],
                avg_pre_synapses=summary_data['avg_pre_synapses'],
                avg_post_synapses=summary_data['avg_post_synapses'],
                consensus_nt=summary_data.get('consensus_nt'),
                celltype_predicted_nt=summary_data.get('celltype_predicted_nt'),
                celltype_predicted_nt_confidence=summary_data.get('celltype_predicted_nt_confidence'),
                celltype_total_nt_predictions=summary_data.get('celltype_total_nt_predictions'),
                cell_class=summary_data.get('cell_class'),
                cell_subclass=summary_data.get('cell_subclass'),
                cell_superclass=summary_data.get('cell_superclass')
            )

            # Convert complete summary to dataclass if available
            complete_summary_data = raw_data.get('complete_summary')
            if complete_summary_data:
                self._complete_summary = NeuronSummary(
                    total_count=complete_summary_data['total_count'],
                    left_count=complete_summary_data['left_count'],
                    right_count=complete_summary_data['right_count'],
                    middle_count=complete_summary_data['middle_count'],
                    type_name=complete_summary_data['type_name'],
                    soma_side=complete_summary_data['soma_side'],
                    total_pre_synapses=complete_summary_data['total_pre_synapses'],
                    total_post_synapses=complete_summary_data['total_post_synapses'],
                    avg_pre_synapses=complete_summary_data['avg_pre_synapses'],
                    avg_post_synapses=complete_summary_data['avg_post_synapses'],
                    consensus_nt=complete_summary_data.get('consensus_nt'),
                    celltype_predicted_nt=complete_summary_data.get('celltype_predicted_nt'),
                    celltype_predicted_nt_confidence=complete_summary_data.get('celltype_predicted_nt_confidence'),
                    celltype_total_nt_predictions=complete_summary_data.get('celltype_total_nt_predictions'),
                    cell_class=complete_summary_data.get('cell_class'),
                    cell_subclass=complete_summary_data.get('cell_subclass'),
                    cell_superclass=complete_summary_data.get('cell_superclass')
                )

            # Convert connectivity to dataclass
            conn_data = raw_data.get('connectivity', {})
            self._connectivity = ConnectivityData(
                upstream=conn_data.get('upstream', []),
                downstream=conn_data.get('downstream', []),
                regional_connections=conn_data.get('regional_connections', {}),
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
    def complete_summary(self) -> Optional[NeuronSummary]:
        """Get the complete summary statistics for the entire neuron type."""
        if not self._is_fetched:
            self.fetch_data()
        return self._complete_summary

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
            side: 'left', 'right', 'middle', or None for total

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
        elif side.lower() == 'middle':
            return summary.middle_count
        else:
            raise ValueError(f"Invalid side: {side}. Use 'left', 'right', 'middle', or None")

    def get_synapse_stats(self) -> Dict[str, Any]:
        """Get synapse statistics."""
        summary = self.summary  # This will trigger fetch_data if needed

        return {
            'total_pre': summary.total_pre_synapses,
            'total_post': summary.total_post_synapses,
            'avg_pre': summary.avg_pre_synapses,
            'avg_post': summary.avg_post_synapses
        }

    def has_data(self) -> bool:
        """
        Check if this neuron type has any data in the dataset.

        Returns:
            True if neurons were found, False if no neurons exist for this type
        """
        if not self._is_fetched:
            self.fetch_data()
        return self._summary is not None and self._summary.total_count > 0

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the neuron type data to a dictionary for template rendering.

        This method provides compatibility with the existing page generator
        by returning data in the same format as the old neuprint_connector.
        """
        summary = self.summary  # This will trigger fetch_data if needed
        connectivity = self.connectivity
        complete_summary = self.complete_summary

        result = {
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
                'avg_post_synapses': summary.avg_post_synapses,
                'consensus_nt': summary.consensus_nt,
                'celltype_predicted_nt': summary.celltype_predicted_nt,
                'celltype_predicted_nt_confidence': summary.celltype_predicted_nt_confidence,
                'celltype_total_nt_predictions': summary.celltype_total_nt_predictions,
                'cell_class': summary.cell_class,
                'cell_subclass': summary.cell_subclass,
                'cell_superclass': summary.cell_superclass
            },
            'connectivity': {
                'upstream': connectivity.upstream,
                'downstream': connectivity.downstream,
                'regional_connections': connectivity.regional_connections,
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

        # Add complete_summary if available
        if complete_summary:
            result['complete_summary'] = {
                'total_count': complete_summary.total_count,
                'left_count': complete_summary.left_count,
                'right_count': complete_summary.right_count,
                'cell_log_ratio': self._log_ratio(complete_summary.left_count, complete_summary.right_count),
                'type': complete_summary.type_name,
                'soma_side': complete_summary.soma_side,
                'total_pre_synapses': complete_summary.total_pre_synapses,
                'total_post_synapses': complete_summary.total_post_synapses,
                'synapse_log_ratio': self._log_ratio(complete_summary.total_pre_synapses, complete_summary.total_post_synapses),
                'avg_pre_synapses': complete_summary.avg_pre_synapses,
                'avg_post_synapses': complete_summary.avg_post_synapses,
                'consensus_nt': complete_summary.consensus_nt,
                'celltype_predicted_nt': complete_summary.celltype_predicted_nt,
                'celltype_predicted_nt_confidence': complete_summary.celltype_predicted_nt_confidence,
                'celltype_total_nt_predictions': complete_summary.celltype_total_nt_predictions,
                'cell_class': complete_summary.cell_class,
                'cell_subclass': complete_summary.cell_subclass,
                'cell_superclass': complete_summary.cell_superclass
            }

        return result

    def _log_ratio(self, a, b):
        """Calculate the log ratio of two numbers."""
        if a is None:
            a = 0
        if b is None:
            b = 0
        if a==0 and b==0:
            log_ratio = 0.0
        elif a==0:
            log_ratio = -math.inf
        elif b==0:
            log_ratio = math.inf
        else:
            log_ratio = math.log(a / b)
        return log_ratio

    def __repr__(self) -> str:
        """String representation of the neuron type."""
        status = "fetched" if self._is_fetched else "not fetched"
        count = ""
        if self._is_fetched and self._summary is not None:
            count = f" ({self._summary.total_count} neurons)"
        return f"NeuronType('{self.name}', {self.soma_side}, {status}{count})"
