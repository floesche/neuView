"""
NeuPrint connector for fetching neuron data.

This module provides the core functionality for connecting to and fetching
data from NeuPrint servers, including neuron data, connectivity information,
and summary statistics.
"""

import pandas as pd
import re
import json
from typing import Dict, List, Any
from neuprint import Client, fetch_neurons, NeuronCriteria
import os
import re
import random
import time
import logging

from .config import Config, DiscoveryConfig
from .dataset_adapters import get_dataset_adapter

# Set up logger for performance monitoring
logger = logging.getLogger(__name__)


class NeuPrintConnector:
    """
    Handle connections and data fetching from NeuPrint.

    This class provides a comprehensive interface for fetching neuron data,
    connectivity information, and summary statistics from NeuPrint servers.
    """

    def __init__(self, config: Config):
        """
        Initialize the NeuPrint connector.

        Args:
            config: Configuration object containing server, dataset, and auth info
        """
        self.config = config
        self.client = None
        self.dataset_adapter = get_dataset_adapter(config.neuprint.dataset)
        # Cache for expensive queries to avoid repeated database hits
        self._soma_sides_cache = None
        # Connection reuse optimization
        self._connection_pool = None
        # Cache for raw neuron data to avoid redundant queries across soma sides
        self._raw_neuron_data_cache = {}
        # Cache for connectivity data to avoid redundant queries
        self._connectivity_cache = {}
        # Cache statistics for monitoring performance
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'total_queries_saved': 0,
            'connectivity_hits': 0,
            'connectivity_misses': 0,
            'connectivity_queries_saved': 0
        }
        self._connect()

    def _escape_regex_chars(self, text: str) -> str:
        """
        Escape special characters in neuron type names for Cypher queries.

        Try backslash escaping for single quotes instead of doubling them,
        as the Neo4j version might not support doubled quotes.

        Args:
            text: The neuron type name that may contain special characters

        Returns:
            The escaped text safe for use in Cypher string literals
        """
        # Try backslash escaping for single quotes
        return text.replace("'", "\\'")

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
            # Configure connection pooling for better performance
            if hasattr(self.client, 'session'):
                # Keep connections alive and reuse them
                self.client.session.headers.update({'Connection': 'keep-alive'})
        except Exception as e:
            raise ConnectionError(f"Failed to connect to NeuPrint: {e}")

    def test_connection(self) -> Dict[str, Any]:
        """Test the connection and return server information."""
        if not self.client:
            raise ConnectionError("Not connected to NeuPrint")

        try:
            # Try to get dataset info
            datasets = self.client.fetch_datasets()
            uuid = 'Unknown'
            if dataset := datasets.get(self.config.neuprint.dataset):
                uuid = dataset.get('uuid', 'no UUID')
            return {
                'server': self.config.neuprint.server,
                'dataset': self.config.neuprint.dataset,
                'version': uuid
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
            # Get cached raw data or fetch it
            raw_neurons_df, raw_roi_df = self._get_or_fetch_raw_neuron_data(neuron_type)

            # Filter by soma side using adapter
            if not raw_neurons_df.empty:
                neurons_df = self.dataset_adapter.filter_by_soma_side(raw_neurons_df, soma_side)
            else:
                neurons_df = pd.DataFrame()

            if neurons_df.empty:
                return {
                    'neurons': pd.DataFrame(),
                    'roi_counts': pd.DataFrame(),
                    'summary': {
                        'total_count': 0,
                        'left_count': 0,
                        'right_count': 0,
                        'middle_count': 0,
                        'type': neuron_type,
                        'soma_side': soma_side,
                        'total_pre_synapses': 0,
                        'total_post_synapses': 0,
                        'avg_pre_synapses': 0,
                        'avg_post_synapses': 0
                    },
                    'connectivity': {'upstream': [], 'downstream': [], 'regional_connections': {}, 'note': 'No neurons found for this type'},
                    'type': neuron_type,
                    'soma_side': soma_side
                }

            # Filter ROI data to match the filtered neurons
            if not raw_roi_df.empty and not neurons_df.empty:
                body_ids = neurons_df['bodyId'].tolist() if 'bodyId' in neurons_df.columns else []
                roi_df = raw_roi_df[raw_roi_df['bodyId'].isin(body_ids)] if body_ids else pd.DataFrame()
            else:
                roi_df = pd.DataFrame()

            # Calculate summary statistics
            summary = self._calculate_summary(neurons_df, neuron_type, soma_side)

            # Get connectivity data with caching
            body_ids = neurons_df['bodyId'].tolist() if 'bodyId' in neurons_df.columns else []
            connectivity = self._get_cached_connectivity_summary(body_ids, roi_df, neuron_type, soma_side)

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

    def _get_or_fetch_raw_neuron_data(self, neuron_type: str) -> tuple:
        """
        Get raw neuron data from cache or fetch it from database.

        Args:
            neuron_type: The type of neuron to fetch

        Returns:
            Tuple of (neurons_df, roi_df) - the raw unfiltered data
        """
        # Check cache first
        if neuron_type in self._raw_neuron_data_cache:
            cached_data = self._raw_neuron_data_cache[neuron_type]
            self._cache_stats['hits'] += 1
            self._cache_stats['total_queries_saved'] += 1
            return cached_data['neurons_df'], cached_data['roi_df']

        # Cache miss - fetch from database
        self._cache_stats['misses'] += 1
        # Escape special characters for Cypher and use exact matching
        escaped_type = self._escape_regex_chars(neuron_type)
        criteria = NeuronCriteria(type=escaped_type, regex=False)
        neurons_df, roi_df = fetch_neurons(criteria)

        # Add neurotransmitter fields via separate query if neurons were found
        if not neurons_df.empty:
            body_ids = neurons_df['bodyId'].tolist()
            body_ids_str = "[" + ", ".join(str(bid) for bid in body_ids) + "]"

            # Query for neurotransmitter fields
            nt_query = f"""
            UNWIND {body_ids_str} as target_body_id
            MATCH (n:Neuron {{bodyId: target_body_id}})
            RETURN
                target_body_id as bodyId,
                n.consensusNt as consensusNt,
                n.celltypePredictedNt as celltypePredictedNt,
                n.celltypePredictedNtConfidence as celltypePredictedNtConfidence,
                n.celltypeTotalNtPredictions as celltypeTotalNtPredictions
            """

            try:
                nt_df = self.client.fetch_custom(nt_query)
                if not nt_df.empty:
                    # Merge neurotransmitter data with neurons_df
                    neurons_df = neurons_df.merge(nt_df, on='bodyId', how='left')
                    logger.info(f"Added neurotransmitter data for {neuron_type}")
            except Exception as e:
                logger.warning(f"Failed to fetch neurotransmitter data for {neuron_type}: {e}")

        # Use dataset adapter to process the raw data
        if not neurons_df.empty:
            # Normalize columns and extract soma side using adapter
            neurons_df = self.dataset_adapter.normalize_columns(neurons_df)
            neurons_df = self.dataset_adapter.extract_soma_side(neurons_df)

        # Cache the raw data
        self._raw_neuron_data_cache[neuron_type] = {
            'neurons_df': neurons_df,
            'roi_df': roi_df,
            'fetched_at': time.time()
        }

        return neurons_df, roi_df

    def clear_neuron_data_cache(self, neuron_type: str = None):
        """
        Clear cached neuron data.

        Args:
            neuron_type: Specific type to clear, or None to clear all
        """
        if neuron_type:
            self._raw_neuron_data_cache.pop(neuron_type, None)
            # Also clear connectivity cache for this neuron type
            keys_to_remove = [k for k in self._connectivity_cache.keys() if k.startswith(f"{neuron_type}_")]
            for key in keys_to_remove:
                self._connectivity_cache.pop(key, None)
        else:
            self._raw_neuron_data_cache.clear()
            self._connectivity_cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.

        Returns:
            Dictionary with cache hit/miss ratios and query savings
        """
        total_requests = self._cache_stats['hits'] + self._cache_stats['misses']
        hit_rate = (self._cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            'cache_hits': self._cache_stats['hits'],
            'cache_misses': self._cache_stats['misses'],
            'total_requests': total_requests,
            'hit_rate_percent': round(hit_rate, 2),
            'database_queries_saved': self._cache_stats['total_queries_saved'],
            'cached_neuron_types': len(self._raw_neuron_data_cache),
            'connectivity_hits': self._cache_stats['connectivity_hits'],
            'connectivity_misses': self._cache_stats['connectivity_misses'],
            'connectivity_queries_saved': self._cache_stats['connectivity_queries_saved'],
            'cached_connectivity_entries': len(self._connectivity_cache)
        }

    def log_cache_performance(self):
        """Log cache performance statistics for monitoring."""
        stats = self.get_cache_stats()
        if stats['total_requests'] > 0:
            total_conn_requests = stats['connectivity_hits'] + stats['connectivity_misses']
            conn_hit_rate = (stats['connectivity_hits'] / total_conn_requests * 100) if total_conn_requests > 0 else 0
            logger.info(f"NeuPrint cache performance: {stats['hit_rate_percent']}% neuron hit rate, "
                       f"{round(conn_hit_rate, 2)}% connectivity hit rate, "
                       f"{stats['database_queries_saved'] + stats['connectivity_queries_saved']} total queries saved, "
                       f"{stats['cached_neuron_types']} neuron types cached, "
                       f"{stats['cached_connectivity_entries']} connectivity entries cached")

    def _calculate_summary(self, neurons_df: pd.DataFrame,
                         neuron_type: str, soma_side: str) -> Dict[str, Any]:
        """Calculate summary statistics for the neuron data."""
        total_count = len(neurons_df)

        # Count by soma side if side column exists
        left_count = 0
        right_count = 0
        middle_count = 0

        if 'somaSide' in neurons_df.columns:
            side_counts = neurons_df['somaSide'].value_counts()
            left_count = side_counts.get('L', 0)
            right_count = side_counts.get('R', 0)
            middle_count = side_counts.get('M', 0)

        # Use dataset adapter to get synapse statistics
        pre_synapses, post_synapses = self.dataset_adapter.get_synapse_counts(neurons_df)

        # Extract neurotransmitter data from first row (should be consistent across type)
        consensus_nt = None
        celltype_predicted_nt = None
        celltype_predicted_nt_confidence = None
        celltype_total_nt_predictions = None

        if total_count > 0:
            first_row = neurons_df.iloc[0]

            # Try _y suffixed columns first (from merged custom query), then fallback to original columns
            consensus_nt = None
            if 'consensusNt_y' in neurons_df.columns:
                consensus_nt = first_row.get('consensusNt_y')
            elif 'consensusNt' in neurons_df.columns:
                consensus_nt = first_row.get('consensusNt')

            celltype_predicted_nt = None
            if 'celltypePredictedNt_y' in neurons_df.columns:
                celltype_predicted_nt = first_row.get('celltypePredictedNt_y')
            elif 'celltypePredictedNt' in neurons_df.columns:
                celltype_predicted_nt = first_row.get('celltypePredictedNt')

            celltype_predicted_nt_confidence = None
            if 'celltypePredictedNtConfidence_y' in neurons_df.columns:
                celltype_predicted_nt_confidence = first_row.get('celltypePredictedNtConfidence_y')
            elif 'celltypePredictedNtConfidence' in neurons_df.columns:
                celltype_predicted_nt_confidence = first_row.get('celltypePredictedNtConfidence')

            celltype_total_nt_predictions = None
            if 'celltypeTotalNtPredictions_y' in neurons_df.columns:
                celltype_total_nt_predictions = first_row.get('celltypeTotalNtPredictions_y')
            elif 'celltypeTotalNtPredictions' in neurons_df.columns:
                celltype_total_nt_predictions = first_row.get('celltypeTotalNtPredictions')

            # Clean up None values and NaN
            import pandas as pd
            if pd.isna(consensus_nt):
                consensus_nt = None
            if pd.isna(celltype_predicted_nt):
                celltype_predicted_nt = None
            if pd.isna(celltype_predicted_nt_confidence):
                celltype_predicted_nt_confidence = None
            if pd.isna(celltype_total_nt_predictions):
                celltype_total_nt_predictions = None

        return {
            'total_count': total_count,
            'left_count': left_count,
            'right_count': right_count,
            'middle_count': middle_count,
            'type_name': neuron_type,
            'soma_side': soma_side,
            'total_pre_synapses': pre_synapses,
            'total_post_synapses': post_synapses,
            'avg_pre_synapses': round(pre_synapses / total_count, 2) if total_count > 0 else 0,
            'avg_post_synapses': round(post_synapses / total_count, 2) if total_count > 0 else 0,
            'consensus_nt': consensus_nt,
            'celltype_predicted_nt': celltype_predicted_nt,
            'celltype_predicted_nt_confidence': celltype_predicted_nt_confidence,
            'celltype_total_nt_predictions': celltype_total_nt_predictions
        }

    def _get_cached_connectivity_summary(self, body_ids: List[int], roi_df: pd.DataFrame, neuron_type: str, soma_side: str) -> Dict[str, Any]:
        """Get connectivity summary with caching to avoid redundant queries."""
        # Create cache key based on sorted body IDs to ensure consistent caching
        body_ids_key = tuple(sorted(body_ids))
        cache_key = f"{neuron_type}_{soma_side}_{hash(body_ids_key)}"

        # Check cache first
        if cache_key in self._connectivity_cache:
            self._cache_stats['connectivity_hits'] += 1
            self._cache_stats['connectivity_queries_saved'] += 1
            return self._connectivity_cache[cache_key]

        # Cache miss - compute connectivity
        self._cache_stats['connectivity_misses'] += 1

        # Create temporary DataFrame for compatibility with existing method
        if body_ids:
            temp_neurons_df = pd.DataFrame({'bodyId': body_ids})
            connectivity = self._get_connectivity_summary(temp_neurons_df, roi_df)
        else:
            connectivity = {'upstream': [], 'downstream': [], 'regional_connections': {}}

        # Cache the result
        self._connectivity_cache[cache_key] = connectivity

        return connectivity

    def _get_connectivity_summary(self, neurons_df: pd.DataFrame, roi_df: pd.DataFrame = None) -> Dict[str, Any]:
        """Get connectivity summary for the neurons."""
        if neurons_df.empty:
            return {'upstream': [], 'downstream': [], 'regional_connections': {}}

        try:
            # Get body IDs from the neuron DataFrame
            if 'bodyId' in neurons_df.columns:
                body_ids = neurons_df['bodyId'].tolist()
            else:
                # Fallback to index if bodyId column doesn't exist
                body_ids = neurons_df.index.tolist()

            if not body_ids:
                return {'upstream': [], 'downstream': [], 'regional_connections': {}}

            # Check if this neuron type innervates layer regions (only if roi_df is available)
            innervates_layers = False
            if roi_df is not None and not roi_df.empty:
                innervates_layers = self._check_layer_innervation(body_ids, roi_df)
            regional_connections = {}

            if innervates_layers:
                # Add enhanced connectivity info for layer-innervating neurons
                regional_connections = self._get_regional_connections(body_ids)

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
                            'percentage': percentage
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
                            'percentage': percentage
                        })

            return {
                'upstream': upstream_partners,
                'downstream': downstream_partners,
                'regional_connections': regional_connections,
                'note': f'Connections for {len(body_ids)} neurons'
            }

        except Exception as e:
            return {
                'upstream': [],
                'downstream': [],
                'regional_connections': {},
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
        """
        Get neuron types with their available soma sides.

        This method is cached to avoid expensive repeated queries during
        a single session. The cache is cleared when a new connector is created.
        """
        start_time = time.time()

        # Return cached result if available
        if self._soma_sides_cache is not None:
            logger.debug(f"get_types_with_soma_sides: returned cached result in {time.time() - start_time:.3f}s")
            return self._soma_sides_cache

        if not self.client:
            raise ConnectionError("Not connected to NeuPrint")

        try:
            # First, try to get soma sides directly from the database if available
            direct_query = """
            MATCH (n:Neuron)
            WHERE n.type IS NOT NULL AND n.somaSide IS NOT NULL
            RETURN DISTINCT n.type as type, collect(DISTINCT n.somaSide) as soma_sides
            ORDER BY n.type
            """

            try:
                direct_result = self.client.fetch_custom(direct_query)
                if not direct_result.empty:
                    # Database has soma side information directly - use vectorized operations
                    types_with_sides = {}

                    # Process all types at once using vectorized operations
                    for neuron_type, raw_sides in zip(direct_result['type'], direct_result['soma_sides']):
                        # Normalize and filter soma sides using list comprehension
                        normalized_sides = []
                        for side in raw_sides:
                            if side and str(side).strip():
                                side_str = str(side).strip().upper()
                                if side_str in ['L', 'LEFT']:
                                    normalized_sides.append('L')
                                elif side_str in ['R', 'RIGHT']:
                                    normalized_sides.append('R')
                                elif side_str in ['M', 'MIDDLE', 'MID']:
                                    normalized_sides.append('M')
                                elif side_str in ['L', 'R', 'M']:  # Already normalized
                                    normalized_sides.append(side_str)

                        soma_sides = sorted(list(set(normalized_sides)))  # Remove duplicates and sort
                        types_with_sides[neuron_type] = soma_sides

                    # Cache the result
                    self._soma_sides_cache = types_with_sides
                    logger.info(f"get_types_with_soma_sides: direct query completed in {time.time() - start_time:.3f}s, found {len(types_with_sides)} types")
                    return types_with_sides
            except Exception:
                # Fallback to instance-based extraction if direct query fails
                pass

            # Fallback: Extract from instance names using dataset adapter
            query = """
            MATCH (n:Neuron)
            WHERE n.type IS NOT NULL AND n.instance IS NOT NULL
            RETURN DISTINCT n.type as type, collect(DISTINCT n.instance) as instances
            ORDER BY n.type
            """
            result = self.client.fetch_custom(query)

            types_with_sides = {}
            # Use vectorized operations instead of iterrows()
            for neuron_type, instances in zip(result['type'], result['instances']):
                # Create a mini DataFrame to use dataset adapter
                mini_df = pd.DataFrame({
                    'type': [neuron_type] * len(instances),
                    'instance': instances
                })

                # Extract soma sides using dataset adapter
                mini_df = self.dataset_adapter.extract_soma_side(mini_df)

                # Get unique soma sides for this type using vectorized operations
                if 'somaSide' in mini_df.columns:
                    soma_sides = mini_df['somaSide'].dropna().unique().tolist()
                    # Filter out 'U' (unknown) and normalize values using list comprehension
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

            # Cache the result
            self._soma_sides_cache = types_with_sides
            logger.info(f"get_types_with_soma_sides: fallback query completed in {time.time() - start_time:.3f}s, found {len(types_with_sides)} types")
            return types_with_sides
        except Exception as e:
            logger.error(f"get_types_with_soma_sides: failed after {time.time() - start_time:.3f}s: {e}")
            raise RuntimeError(f"Failed to fetch neuron types with soma sides: {e}")

    def get_soma_sides_for_type(self, neuron_type: str) -> List[str]:
        """
        Get soma sides for a specific neuron type only (optimized version).

        This method queries only the requested neuron type instead of all types,
        providing significant performance improvement for single-type queries.

        Args:
            neuron_type: The specific neuron type to query

        Returns:
            List of soma side codes for the specified type
        """
        start_time = time.time()

        if not self.client:
            raise ConnectionError("Not connected to NeuPrint")

        try:
            # Optimized query for single neuron type
            escaped_type = self._escape_regex_chars(neuron_type)
            direct_query = f"""
            MATCH (n:Neuron)
            WHERE n.type = '{escaped_type}' AND n.somaSide IS NOT NULL
            RETURN DISTINCT n.somaSide as soma_side
            ORDER BY n.somaSide
            """

            try:
                direct_result = self.client.fetch_custom(direct_query)
                if not direct_result.empty:
                    # Database has soma side information directly
                    raw_sides = direct_result['soma_side'].tolist()

                    # Normalize and filter soma sides
                    normalized_sides = []
                    for side in raw_sides:
                        if side and str(side).strip():
                            side_str = str(side).strip().upper()
                            if side_str in ['L', 'LEFT']:
                                normalized_sides.append('L')
                            elif side_str in ['R', 'RIGHT']:
                                normalized_sides.append('R')
                            elif side_str in ['M', 'MIDDLE', 'MID']:
                                normalized_sides.append('M')
                            elif side_str in ['L', 'R', 'M']:  # Already normalized
                                normalized_sides.append(side_str)

                    result = sorted(list(set(normalized_sides)))
                    logger.info(f"get_soma_sides_for_type({neuron_type}): direct query completed in {time.time() - start_time:.3f}s, found sides: {result}")
                    return result
            except Exception:
                # Fallback to instance-based extraction if direct query fails
                pass

            # Fallback: Extract from instance names for this specific type
            escaped_type = self._escape_regex_chars(neuron_type)
            fallback_query = f"""
            MATCH (n:Neuron)
            WHERE n.type = '{escaped_type}' AND n.instance IS NOT NULL
            RETURN DISTINCT n.instance as instance
            """
            result = self.client.fetch_custom(fallback_query)

            if result.empty:
                logger.info(f"get_soma_sides_for_type({neuron_type}): no neurons found in {time.time() - start_time:.3f}s")
                return []

            instances = result['instance'].tolist()

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
                result = sorted(list(set(normalized_sides)))
                logger.info(f"get_soma_sides_for_type({neuron_type}): fallback query completed in {time.time() - start_time:.3f}s, found sides: {result}")
                return result
            else:
                logger.info(f"get_soma_sides_for_type({neuron_type}): no soma sides found in {time.time() - start_time:.3f}s")
                return []

        except Exception as e:
            logger.error(f"get_soma_sides_for_type({neuron_type}): failed after {time.time() - start_time:.3f}s: {e}")
            raise RuntimeError(f"Failed to fetch soma sides for type {neuron_type}: {e}")

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

    def _check_layer_innervation(self, body_ids: List[int], roi_df: pd.DataFrame) -> bool:
        """
        Check if neurons innervate layer regions using ROI data.

        Args:
            body_ids: List of neuron body IDs to check
            roi_df: DataFrame containing ROI data with columns like 'bodyId', 'roi', 'pre', 'post'

        Returns:
            True if any neuron has synapses in layer regions, False otherwise
        """
        if not body_ids or roi_df.empty:
            return False

        try:
            # Filter ROI data for our neurons
            neuron_roi_data = roi_df[roi_df['bodyId'].isin(body_ids)]

            if neuron_roi_data.empty:
                return False

            # Check for layer regions: (ME|LO|LOP)_[LR]_layer_<number>
            layer_pattern = r'^(ME|LO|LOP)_[LR]_layer_\d+$'
            layer_rois = neuron_roi_data[
                neuron_roi_data['roi'].str.match(layer_pattern, na=False)
            ]

            # Return True if we have any synapses in layer regions
            if not layer_rois.empty:
                total_synapses = layer_rois['pre'].fillna(0).sum() + layer_rois['post'].fillna(0).sum()
                return total_synapses > 0

            return False

        except Exception as e:
            # If we can't determine layer innervation, return False
            print(f"Warning: Could not check layer innervation: {e}")
            return False

    def _get_regional_connections(self, body_ids: List[int]) -> Dict[str, Any]:
        """
        Get enhanced connectivity info for neurons that innervate layers.
        Since layer innervation is detected, we provide additional context.

        Args:
            body_ids: List of neuron body IDs

        Returns:
            Dictionary containing enhanced connection metadata
        """
        return {
            'enhanced_info': {
                'innervates_layers': True,
                'note': 'This neuron type innervates layer regions (ME/LO/LOP layers). '
                       'The connections shown above may include synapses within '
                       'LA, AME, and central brain regions.',
                'layer_pattern': r'^(ME|LO|LOP)_[LR]_layer_\d+$',
                'enhanced_regions': ['LA', 'AME', 'central brain']
            }
        }

    def get_batch_neuron_data(self, neuron_types: List[str], soma_side: str = 'both') -> Dict[str, Dict[str, Any]]:
        """
        Fetch neuron data for multiple types in a single optimized query.

        This replaces N individual queries with 1 batch query, providing
        significant performance improvement for large numbers of neuron types.

        Args:
            neuron_types: List of neuron type names to fetch
            soma_side: 'left', 'right', or 'both'

        Returns:
            Dictionary mapping neuron type to its data (same format as get_neuron_data)
        """
        if not self.client:
            raise ConnectionError("Not connected to NeuPrint")

        if not neuron_types:
            return {}

        try:
            # Get batch raw data
            batch_raw_data = self._get_or_fetch_batch_raw_neuron_data(neuron_types)

            results = {}
            for neuron_type in neuron_types:
                raw_neurons_df, raw_roi_df = batch_raw_data.get(neuron_type, (pd.DataFrame(), pd.DataFrame()))

                # Filter by soma side using adapter
                if not raw_neurons_df.empty:
                    neurons_df = self.dataset_adapter.filter_by_soma_side(raw_neurons_df, soma_side)
                else:
                    neurons_df = pd.DataFrame()

                if neurons_df.empty:
                    results[neuron_type] = {
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
                        'connectivity': {'upstream': [], 'downstream': [], 'regional_connections': {}, 'note': 'No neurons found for this type'},
                        'type': neuron_type,
                        'soma_side': soma_side
                    }
                    continue

                # Filter ROI data to match the filtered neurons
                if not raw_roi_df.empty and not neurons_df.empty:
                    body_ids = neurons_df['bodyId'].tolist() if 'bodyId' in neurons_df.columns else []
                    roi_df = raw_roi_df[raw_roi_df['bodyId'].isin(body_ids)] if body_ids else pd.DataFrame()
                else:
                    roi_df = pd.DataFrame()

                # Calculate summary statistics
                summary = self._calculate_summary(neurons_df, neuron_type, soma_side)

                # Get connectivity data with caching
                body_ids = neurons_df['bodyId'].tolist() if 'bodyId' in neurons_df.columns else []
                connectivity = self._get_cached_connectivity_summary(body_ids, roi_df, neuron_type, soma_side)

                results[neuron_type] = {
                    'neurons': neurons_df,
                    'roi_counts': roi_df,
                    'summary': summary,
                    'connectivity': connectivity,
                    'type': neuron_type,
                    'soma_side': soma_side
                }

            return results

        except Exception as e:
            raise RuntimeError(f"Failed to fetch batch neuron data: {e}")

    def _get_or_fetch_batch_raw_neuron_data(self, neuron_types: List[str]) -> Dict[str, tuple]:
        """
        Get raw neuron data from cache or fetch it from database using batch query.

        Args:
            neuron_types: List of neuron type names

        Returns:
            Dictionary mapping neuron type to (neurons_df, roi_df) tuple
        """
        results = {}
        uncached_types = []

        # Check cache for each type
        for neuron_type in neuron_types:
            if neuron_type in self._raw_neuron_data_cache:
                cached_data = self._raw_neuron_data_cache[neuron_type]
                results[neuron_type] = (cached_data['neurons_df'], cached_data['roi_df'])
                self._cache_stats['hits'] += 1
                self._cache_stats['total_queries_saved'] += 1
            else:
                uncached_types.append(neuron_type)
                self._cache_stats['misses'] += 1

        # Batch fetch uncached types
        if uncached_types:
            batch_data = self._fetch_batch_raw_neuron_data(uncached_types)

            # Cache and add to results
            for neuron_type, (neurons_df, roi_df) in batch_data.items():
                # Use dataset adapter to process the raw data
                if not neurons_df.empty:
                    neurons_df = self.dataset_adapter.normalize_columns(neurons_df)
                    neurons_df = self.dataset_adapter.extract_soma_side(neurons_df)

                # Cache the raw data
                self._raw_neuron_data_cache[neuron_type] = {
                    'neurons_df': neurons_df,
                    'roi_df': roi_df,
                    'fetched_at': time.time()
                }

                results[neuron_type] = (neurons_df, roi_df)

        return results

    def _fetch_batch_raw_neuron_data(self, neuron_types: List[str]) -> Dict[str, tuple]:
        """
        Fetch raw neuron data for multiple types using a single batch query.

        This is the core optimization that replaces N individual database queries
        with 1 batch query, dramatically reducing network round trips.

        Args:
            neuron_types: List of neuron type names

        Returns:
            Dictionary mapping neuron type to (neurons_df, roi_df) tuple
        """
        if not neuron_types:
            return {}

        # Escape neuron type names for Cypher
        escaped_types = [self._escape_regex_chars(nt) for nt in neuron_types]
        types_list = "[" + ", ".join(f"'{t}'" for t in escaped_types) + "]"

        # Batch query for neuron data
        neuron_query = f"""
        UNWIND {types_list} as target_type
        MATCH (n:Neuron)
        WHERE n.type = target_type
        RETURN
            target_type,
            n.bodyId as bodyId,
            n.type as type,
            n.status as status,
            n.cropped as cropped,
            n.instance as instance,
            n.notes as notes,
            n.somaLocation as somaLocation,
            n.somaRadius as somaRadius,
            n.size as size,
            n.pre as pre,
            n.post as post
        ORDER BY target_type, n.bodyId
        """

        # Execute neuron query
        neurons_df = self.client.fetch_custom(neuron_query)

        # Get all body IDs for ROI query
        all_body_ids = neurons_df['bodyId'].tolist() if not neurons_df.empty else []

        # Batch query for ROI data - parse roiInfo property for CNS dataset compatibility
        roi_df = pd.DataFrame()
        if all_body_ids:
            body_ids_str = "[" + ", ".join(str(bid) for bid in all_body_ids) + "]"

            # First try the SynapseSet approach (for hemibrain/optic lobe datasets)
            roi_query = f"""
            UNWIND {body_ids_str} as target_body_id
            MATCH (n:Neuron {{bodyId: target_body_id}})-[:Contains]->(ss:SynapseSet)-[:ConnectsTo]->(roi:Region)
            RETURN
                target_body_id as bodyId,
                roi.name as roi,
                ss.pre as pre,
                ss.post as post
            ORDER BY target_body_id, ss.pre + ss.post DESC
            """

            roi_df = self.client.fetch_custom(roi_query)

            # If SynapseSet approach returns no data, try roiInfo property approach (for CNS dataset)
            if roi_df.empty:
                logger.debug(f"SynapseSet query returned empty, trying roiInfo approach for {len(all_body_ids)} neurons")
                roi_info_query = f"""
                UNWIND {body_ids_str} as target_body_id
                MATCH (n:Neuron {{bodyId: target_body_id}})
                WHERE n.roiInfo IS NOT NULL
                RETURN target_body_id as bodyId, n.roiInfo as roiInfo
                """

                roi_info_df = self.client.fetch_custom(roi_info_query)
                logger.debug(f"roiInfo query returned {len(roi_info_df)} rows")

                # Parse roiInfo JSON into individual ROI records
                if not roi_info_df.empty:
                    roi_records = []
                    for _, row in roi_info_df.iterrows():
                        body_id = row['bodyId']
                        roi_info = row['roiInfo']

                        # Parse JSON string if needed
                        if isinstance(roi_info, str):
                            try:
                                roi_info = json.loads(roi_info)
                            except (json.JSONDecodeError, TypeError):
                                logger.warning(f"Failed to parse roiInfo JSON for bodyId {body_id}")
                                continue

                        if roi_info and isinstance(roi_info, dict):
                            for roi_name, roi_data in roi_info.items():
                                if isinstance(roi_data, dict):
                                    roi_records.append({
                                        'bodyId': body_id,
                                        'roi': roi_name,
                                        'pre': roi_data.get('pre', 0),
                                        'post': roi_data.get('post', 0),
                                        'downstream': roi_data.get('downstream', 0),
                                        'upstream': roi_data.get('upstream', 0)
                                    })

                    if roi_records:
                        roi_df = pd.DataFrame(roi_records)
                        logger.debug(f"Parsed {len(roi_records)} ROI records from roiInfo")
                        # Sort by total synapses (pre + post) descending
                        roi_df['total_synapses'] = roi_df['pre'] + roi_df['post']
                        roi_df = roi_df.sort_values(['bodyId', 'total_synapses'], ascending=[True, False])
                        roi_df = roi_df.drop('total_synapses', axis=1)
                    else:
                        logger.debug("No ROI records parsed from roiInfo")

        # Group results by neuron type
        results = {}
        for neuron_type in neuron_types:
            # Filter neurons for this type
            type_neurons = neurons_df[neurons_df['target_type'] == neuron_type].copy() if not neurons_df.empty else pd.DataFrame()
            if not type_neurons.empty:
                type_neurons = type_neurons.drop('target_type', axis=1)

            # Filter ROI data for this type's neurons
            type_roi = pd.DataFrame()
            if not type_neurons.empty and not roi_df.empty:
                type_body_ids = type_neurons['bodyId'].tolist()
                type_roi = roi_df[roi_df['bodyId'].isin(type_body_ids)].copy()

            results[neuron_type] = (type_neurons, type_roi)

        return results
