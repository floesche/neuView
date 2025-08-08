"""
NeuPrint connector for fetching neuron data.
"""

import pandas as pd
from typing import Dict, List, Any
from neuprint import Client, fetch_neurons, NeuronCriteria
import os
import re
import random

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
        
        try:
            # Get body IDs from the neuron DataFrame
            if 'bodyId' in neurons_df.columns:
                body_ids = neurons_df['bodyId'].tolist()
            else:
                # Fallback to index if bodyId column doesn't exist
                body_ids = neurons_df.index.tolist()
            
            if not body_ids:
                return {'upstream': [], 'downstream': []}
            
            # Query for upstream connections (neurons that connect TO these neurons)
            upstream_query = f"""
            MATCH (upstream:Neuron)-[c:ConnectsTo]->(target:Neuron) 
            WHERE target.bodyId IN {body_ids}
            RETURN upstream.type as partner_type, 
                    COALESCE(
                        upstream.somaSide, 
                        apoc.coll.flatten(apoc.text.regexGroups(upstream.instance, '_([LR])$'))[1],
                        ''
                    ) as soma_side,
                   COALESCE(upstream.consensusNt, 'Unknown') as neurotransmitter,
                   SUM(c.weight) as total_weight,
                   COUNT(c) as connection_count
            ORDER BY total_weight DESC
            """
            
            upstream_result = self.client.fetch_custom(upstream_query)
            upstream_partners = []
            total_upstream_weight = 0
            
            if hasattr(upstream_result, 'iterrows'):
                # First pass: calculate total weight for percentage calculation
                for _, record in upstream_result.iterrows():
                    if record['partner_type']:  # Skip null types
                        total_upstream_weight += int(record['total_weight'])
                
                # Second pass: build the partner list with percentages
                for _, record in upstream_result.iterrows():
                    if record['partner_type']:  # Skip null types
                        weight = int(record['total_weight'])
                        percentage = (weight / total_upstream_weight * 100) if total_upstream_weight > 0 else 0
                        connections_per_neuron = round(int(record['total_weight']) / len(body_ids), 1)
                        upstream_partners.append({
                            'type': record['partner_type'],
                            'soma_side': record['soma_side'],
                            'neurotransmitter': record['neurotransmitter'] if pd.notna(record['neurotransmitter']) else 'Unknown',
                            'weight': weight,
                            'connections_per_neuron': connections_per_neuron,
                            'percentage': round(percentage, 1)
                        })
            
            # Query for downstream connections (neurons that these neurons connect TO)
            downstream_query = f"""
            MATCH (source:Neuron)-[c:ConnectsTo]->(downstream:Neuron) 
            WHERE source.bodyId IN {body_ids}
            RETURN downstream.type as partner_type,
                    COALESCE(
                        downstream.somaSide, 
                        apoc.coll.flatten(apoc.text.regexGroups(downstream.instance, '_([LR])$'))[1],
                        ''
                    ) as soma_side,
                    COALESCE(downstream.consensusNt, 'Unknown') as neurotransmitter,
                    SUM(c.weight) as total_weight,
                    COUNT(c) as connection_count
            ORDER BY total_weight DESC
            """
            
            downstream_result = self.client.fetch_custom(downstream_query)
            downstream_partners = []
            total_downstream_weight = 0
            
            if hasattr(downstream_result, 'iterrows'):
                # First pass: calculate total weight for percentage calculation
                for _, record in downstream_result.iterrows():
                    if record['partner_type']:  # Skip null types
                        total_downstream_weight += int(record['total_weight'])
                
                # Second pass: build the partner list with percentages
                for _, record in downstream_result.iterrows():
                    if record['partner_type']:  # Skip null types
                        weight = int(record['total_weight'])
                        percentage = (weight / total_downstream_weight * 100) if total_downstream_weight > 0 else 0
                        connections_per_neuron = round(int(record['total_weight']) / len(body_ids), 1)
                        downstream_partners.append({
                            'type': record['partner_type'],
                            'soma_side': record['soma_side'],
                            'neurotransmitter': record['neurotransmitter'] if pd.notna(record['neurotransmitter']) else 'Unknown',
                            'weight': weight,
                            'connections_per_neuron': connections_per_neuron,
                            'percentage': round(percentage, 1)
                        })
            
            return {
                'upstream': upstream_partners,
                'downstream': downstream_partners,
                'note': f'Connections with weight >= 5 for {len(body_ids)} neurons'
            }
            
        except Exception as e:
            return {
                'upstream': [],
                'downstream': [],
                'note': f'Error fetching connectivity: {str(e)}'
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
    
    def get_types_with_soma_sides(self) -> Dict[str, List[str]]:
        """Get neuron types with their available soma sides."""
        if not self.client:
            raise ConnectionError("Not connected to NeuPrint")
        
        try:
            # Query for neuron types with instances to extract soma sides
            query = """
            MATCH (n:Neuron)
            WHERE n.type IS NOT NULL AND n.instance IS NOT NULL
            RETURN DISTINCT n.type as type, collect(DISTINCT n.instance) as instances
            ORDER BY n.type
            """
            result = self.client.fetch_custom(query)
            
            types_with_sides = {}
            for _, row in result.iterrows():
                neuron_type = row['type']
                instances = row['instances']
                
                # Create a mini DataFrame to use dataset adapter
                mini_df = pd.DataFrame({
                    'type': [neuron_type] * len(instances),
                    'instance': instances
                })
                
                # Extract soma sides using dataset adapter
                mini_df = self.dataset_adapter.extract_soma_side(mini_df)
                
                # Get unique soma sides for this type
                if 'somaSide' in mini_df.columns:
                    soma_sides = mini_df['somaSide'].dropna().unique().tolist()
                    # Filter out 'U' (unknown) and normalize values
                    normalized_sides = []
                    for side in soma_sides:
                        if side and side != 'U':  # Keep all non-empty, non-unknown values
                            # Normalize common variations
                            side_str = str(side).strip().upper()
                            if side_str in ['L', 'LEFT']:
                                normalized_sides.append('L')
                            elif side_str in ['R', 'RIGHT']:
                                normalized_sides.append('R')
                            elif side_str in ['M', 'MIDDLE', 'MID']:
                                normalized_sides.append('M')
                            else:
                                # Keep other values as-is but uppercased
                                normalized_sides.append(side_str)
                    soma_sides = sorted(list(set(normalized_sides)))  # Remove duplicates and sort
                else:
                    soma_sides = []
                
                types_with_sides[neuron_type] = soma_sides
            
            return types_with_sides
        except Exception as e:
            raise RuntimeError(f"Failed to fetch neuron types with soma sides: {e}")
    
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
        
        # Get all available types
        available_types = self.get_available_types()
        
        # Filter by exclude list
        if discovery_config.exclude_types:
            available_types = [
                type_name for type_name in available_types
                if type_name not in discovery_config.exclude_types
            ]
        
        # Filter by regex pattern if provided
        if discovery_config.type_filter:
            try:
                pattern = re.compile(discovery_config.type_filter)
                available_types = [
                    type_name for type_name in available_types
                    if pattern.search(type_name)
                ]
            except re.error as e:
                print(f"Warning: Invalid regex pattern '{discovery_config.type_filter}': {e}")
        
        # Randomize or keep alphabetical order
        if discovery_config.randomize:
            # Create a copy to avoid modifying the original list
            available_types = available_types.copy()
            random.shuffle(available_types)
        # If not randomizing, the list is already sorted alphabetically from the query
        
        # Return the first N types
        return available_types[:discovery_config.max_types]
