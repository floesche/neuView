"""
NeuPrint connector for fetching neuron data.
"""

import pandas as pd
from typing import Dict, List, Any
from neuprint import Client, fetch_neurons, NeuronCriteria
import os
import re

from .config import Config, DiscoveryConfig
from .dataset_adapters import get_dataset_adapter


class NeuPrintConnector:
    """Handle connections and data fetching from NeuPrint."""
    
    def __init__(self, config: Config):
        """Initialize the NeuPrint connector."""
        self.config = config
        self.client = None
        self.dataset_adapter = get_dataset_adapter(config.neuprint.dataset)
        self._connect()
    
    def _connect(self):
        """Establish connection to NeuPrint server."""
        server = self.config.neuprint.server
        dataset = self.config.neuprint.dataset
        
        # Get token from config or environment
        token = self.config.neuprint.token or os.getenv('NEUPRINT_TOKEN')
        
        if not token:
            raise ValueError(
                "NeuPrint token not found. Set it in one of these ways:\n"
                "1. Create a .env file with NEUPRINT_TOKEN=your_token\n"
                "2. Set NEUPRINT_TOKEN environment variable\n"
                "3. Add token to config.yaml"
            )
        
        try:
            self.client = Client(server, dataset=dataset, token=token)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to NeuPrint: {e}")
    
    def test_connection(self) -> Dict[str, Any]:
        """Test the connection and return server information."""
        if not self.client:
            raise ConnectionError("Not connected to NeuPrint")
        
        try:
            # Try to get dataset info
            info = self.client.fetch_database()
            return {
                'dataset': self.config.neuprint.dataset,
                'version': info.get('version', 'Unknown'),
                'server': self.config.neuprint.server
            }
        except Exception as e:
            raise ConnectionError(f"Connection test failed: {e}")
    
    def get_neuron_data(self, neuron_type: str, soma_side: str = 'both') -> Dict[str, Any]:
        """
        Fetch neuron data for a specific type and soma side.
        
        Args:
            neuron_type: The type of neuron to fetch
            soma_side: 'left', 'right', or 'both'
            
        Returns:
            Dictionary containing neuron data and metadata
        """
        if not self.client:
            raise ConnectionError("Not connected to NeuPrint")
        
        try:
            # Build criteria for neuron search
            criteria = NeuronCriteria(type=neuron_type)
            
            # Fetch neuron data
            neurons_df, roi_df = fetch_neurons(criteria)
            
            # Use dataset adapter to process the data
            if not neurons_df.empty:
                # Normalize columns and extract soma side using adapter
                neurons_df = self.dataset_adapter.normalize_columns(neurons_df)
                neurons_df = self.dataset_adapter.extract_soma_side(neurons_df)
                
                # Filter by soma side using adapter
                neurons_df = self.dataset_adapter.filter_by_soma_side(neurons_df, soma_side)
            
            if neurons_df.empty:
                return {
                    'neurons': pd.DataFrame(),
                    'roi_counts': pd.DataFrame(),
                    'summary': {
                        'total_count': 0,
                        'left_count': 0,
                        'right_count': 0,
                        'type': neuron_type,
                        'soma_side': soma_side,
                        'total_pre_synapses': 0,
                        'total_post_synapses': 0,
                        'avg_pre_synapses': 0,
                        'avg_post_synapses': 0
                    },
                    'connectivity': {'upstream': [], 'downstream': [], 'note': 'No neurons found for this type'},
                    'type': neuron_type,
                    'soma_side': soma_side
                }
            
            # Calculate summary statistics
            summary = self._calculate_summary(neurons_df, neuron_type, soma_side)
            
            # Get connectivity data
            connectivity = self._get_connectivity_summary(neurons_df)
            
            return {
                'neurons': neurons_df,
                'roi_counts': roi_df,
                'summary': summary,
                'connectivity': connectivity,
                'type': neuron_type,
                'soma_side': soma_side
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch neuron data for {neuron_type}: {e}")
    
    def _calculate_summary(self, neurons_df: pd.DataFrame, 
                         neuron_type: str, soma_side: str) -> Dict[str, Any]:
        """Calculate summary statistics for the neuron data."""
        total_count = len(neurons_df)
        
        # Count by soma side if side column exists
        left_count = 0
        right_count = 0

        if 'somaSide' in neurons_df.columns:
            side_counts = neurons_df['somaSide'].value_counts()
            left_count = side_counts.get('L', 0)
            right_count = side_counts.get('R', 0)
        
        # Use dataset adapter to get synapse statistics
        pre_synapses, post_synapses = self.dataset_adapter.get_synapse_counts(neurons_df)
        
        return {
            'total_count': total_count,
            'left_count': left_count,
            'right_count': right_count,
            'type': neuron_type,
            'soma_side': soma_side,
            'total_pre_synapses': pre_synapses,
            'total_post_synapses': post_synapses,
            'avg_pre_synapses': round(pre_synapses / total_count, 2) if total_count > 0 else 0,
            'avg_post_synapses': round(post_synapses / total_count, 2) if total_count > 0 else 0
        }
    
    def _get_connectivity_summary(self, neurons_df: pd.DataFrame) -> Dict[str, Any]:
        """Get connectivity summary for the neurons."""
        if neurons_df.empty:
            return {'upstream': [], 'downstream': []}
        
        # This is a simplified version - in practice you might want to
        # fetch detailed connectivity data using neuprint queries
        return {
            'upstream': [],  # Top upstream partners
            'downstream': [],  # Top downstream partners
            'note': 'Detailed connectivity analysis requires additional queries'
        }
    
    def get_available_types(self) -> List[str]:
        """Get list of available neuron types in the dataset."""
        if not self.client:
            raise ConnectionError("Not connected to NeuPrint")
        
        try:
            # Query for distinct neuron types
            query = """
            MATCH (n:Neuron)
            WHERE n.type IS NOT NULL
            RETURN DISTINCT n.type as type
            ORDER BY n.type
            """
            result = self.client.fetch_custom(query)
            return result['type'].tolist()
        except Exception as e:
            raise RuntimeError(f"Failed to fetch available neuron types: {e}")
    
    def get_type_counts(self) -> Dict[str, int]:
        """Get neuron counts for each type in the dataset."""
        if not self.client:
            raise ConnectionError("Not connected to NeuPrint")
        
        try:
            # Query for neuron counts by type
            query = """
            MATCH (n:Neuron)
            WHERE n.type IS NOT NULL
            RETURN n.type as type, count(n) as count
            ORDER BY count DESC, n.type
            """
            result = self.client.fetch_custom(query)
            return dict(zip(result['type'], result['count']))
        except Exception as e:
            raise RuntimeError(f"Failed to fetch neuron type counts: {e}")
    
    def discover_neuron_types(self, discovery_config: DiscoveryConfig) -> List[str]:
        """
        Discover neuron types based on configuration settings.
        
        Args:
            discovery_config: DiscoveryConfig object with selection criteria
            
        Returns:
            List of selected neuron type names
        """
        # If specific types are requested, use those
        if discovery_config.include_only:
            return discovery_config.include_only[:discovery_config.max_types]
        
        # Get all types with their counts
        type_counts = self.get_type_counts()
        
        # Filter by minimum neuron count
        filtered_types = {
            type_name: count for type_name, count in type_counts.items()
            if count >= discovery_config.min_neuron_count
        }
        
        # Filter by exclude list
        if discovery_config.exclude_types:
            filtered_types = {
                type_name: count for type_name, count in filtered_types.items()
                if type_name not in discovery_config.exclude_types
            }
        
        # Filter by regex pattern if provided
        if discovery_config.type_filter:
            try:
                pattern = re.compile(discovery_config.type_filter)
                filtered_types = {
                    type_name: count for type_name, count in filtered_types.items()
                    if pattern.search(type_name)
                }
            except re.error as e:
                print(f"Warning: Invalid regex pattern '{discovery_config.type_filter}': {e}")
        
        # Sort by count (descending) and take the top N
        sorted_types = sorted(filtered_types.items(), key=lambda x: x[1], reverse=True)
        selected_types = [type_name for type_name, _ in sorted_types[:discovery_config.max_types]]
        
        return selected_types
