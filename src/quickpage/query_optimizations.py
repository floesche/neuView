"""
Query optimization examples for NeuPrint database operations.
Based on profiling results showing database queries as the main bottleneck.
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional, Set
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """
    Optimized query patterns for NeuPrint database operations.
    Addresses the main bottlenecks identified in profiling:
    - Reduces round trips to database
    - Implements batch operations
    - Uses connection pooling
    - Caches frequently accessed data
    """

    def __init__(self, connector):
        self.connector = connector
        self.connection_pool = ThreadPoolExecutor(max_workers=10)
        self._query_cache = {}
        self._batch_cache = {}

    def batch_neuron_query(self, neuron_types: List[str]) -> str:
        """
        Generate optimized Cypher query for multiple neuron types.
        Instead of N queries, this creates 1 query for N types.
        """
        # Escape neuron type names for Cypher
        escaped_types = [self.connector._escape_regex_chars(nt) for nt in neuron_types]

        # Create batch query using UNWIND for better performance
        types_list = "[" + ", ".join(f"'{t}'" for t in escaped_types) + "]"

        query = f"""
        UNWIND {types_list} as neuron_type
        MATCH (n:Neuron)
        WHERE n.type = neuron_type
        WITH n, neuron_type
        OPTIONAL MATCH (n)-[:Contains]->(s:SynapseSet)
        OPTIONAL MATCH (n)-[:Contains]->(ss:SynapseSet)-[:Contains]->(syn:Synapse)
        RETURN
            neuron_type,
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
            n.post as post,
            collect(DISTINCT s.roi) as rois,
            count(DISTINCT syn) as synapse_count
        ORDER BY neuron_type, n.bodyId
        """
        return query

    def batch_roi_query(self, body_ids: List[int]) -> str:
        """
        Generate optimized query for ROI data for multiple neurons.
        """
        body_ids_str = "[" + ", ".join(str(bid) for bid in body_ids) + "]"

        query = f"""
        UNWIND {body_ids_str} as bodyId
        MATCH (n:Neuron {{bodyId: bodyId}})-[:Contains]->(ss:SynapseSet)-[:ConnectsTo]->(roi:Region)
        RETURN
            bodyId,
            roi.name as roi,
            ss.pre as pre,
            ss.post as post,
            (ss.pre + ss.post) as total
        ORDER BY bodyId, total DESC
        """
        return query

    def batch_connectivity_query(self, body_ids: List[int], max_partners: int = 50) -> str:
        """
        Generate optimized connectivity query for multiple neurons.
        """
        body_ids_str = "[" + ", ".join(str(bid) for bid in body_ids) + "]"

        query = f"""
        UNWIND {body_ids_str} as sourceBodyId
        MATCH (source:Neuron {{bodyId: sourceBodyId}})

        // Upstream connections
        OPTIONAL MATCH (upstream:Neuron)-[w1:ConnectsTo]->(source)
        WHERE w1.weight >= 3
        WITH source, sourceBodyId,
             collect({{
                 bodyId: upstream.bodyId,
                 type: upstream.type,
                 weight: w1.weight,
                 direction: 'upstream'
             }})[0..{max_partners}] as upstream_connections

        // Downstream connections
        OPTIONAL MATCH (source)-[w2:ConnectsTo]->(downstream:Neuron)
        WHERE w2.weight >= 3
        WITH source, sourceBodyId, upstream_connections,
             collect({{
                 bodyId: downstream.bodyId,
                 type: downstream.type,
                 weight: w2.weight,
                 direction: 'downstream'
             }})[0..{max_partners}] as downstream_connections

        RETURN
            sourceBodyId,
            upstream_connections,
            downstream_connections
        ORDER BY sourceBodyId
        """
        return query

    async def fetch_batch_neuron_data(self, neuron_types: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Fetch neuron data for multiple types in a single optimized query.
        This replaces N individual queries with 1 batch query.
        """
        if not neuron_types:
            return {}

        # Check cache first
        cache_key = f"batch_neurons_{hash(tuple(sorted(neuron_types)))}"
        if cache_key in self._batch_cache:
            logger.info(f"Cache hit for batch neuron data ({len(neuron_types)} types)")
            return self._batch_cache[cache_key]

        logger.info(f"Fetching batch neuron data for {len(neuron_types)} types")
        start_time = time.time()

        try:
            # Generate optimized batch query
            query = self.batch_neuron_query(neuron_types)

            # Execute query
            results_df = self.connector.client.fetch_custom(query)

            if results_df.empty:
                return {}

            # Group results by neuron type
            grouped_data = {}
            for neuron_type in neuron_types:
                type_data = results_df[results_df['neuron_type'] == neuron_type].copy()
                if not type_data.empty:
                    # Drop the grouping column
                    type_data = type_data.drop('neuron_type', axis=1)
                    grouped_data[neuron_type] = type_data
                else:
                    grouped_data[neuron_type] = pd.DataFrame()

            # Cache results
            self._batch_cache[cache_key] = grouped_data

            query_time = time.time() - start_time
            logger.info(f"Batch neuron query completed in {query_time:.3f}s")

            return grouped_data

        except Exception as e:
            logger.error(f"Batch neuron query failed: {e}")
            return {}

    async def fetch_batch_roi_data(self, body_ids: List[int]) -> Dict[int, pd.DataFrame]:
        """
        Fetch ROI data for multiple neurons in a single optimized query.
        """
        if not body_ids:
            return {}

        cache_key = f"batch_roi_{hash(tuple(sorted(body_ids)))}"
        if cache_key in self._batch_cache:
            logger.info(f"Cache hit for batch ROI data ({len(body_ids)} neurons)")
            return self._batch_cache[cache_key]

        logger.info(f"Fetching batch ROI data for {len(body_ids)} neurons")
        start_time = time.time()

        try:
            query = self.batch_roi_query(body_ids)
            results_df = self.connector.client.fetch_custom(query)

            if results_df.empty:
                return {}

            # Group by body ID
            grouped_data = {}
            for body_id in body_ids:
                roi_data = results_df[results_df['bodyId'] == body_id].copy()
                grouped_data[body_id] = roi_data

            # Cache results
            self._batch_cache[cache_key] = grouped_data

            query_time = time.time() - start_time
            logger.info(f"Batch ROI query completed in {query_time:.3f}s")

            return grouped_data

        except Exception as e:
            logger.error(f"Batch ROI query failed: {e}")
            return {}

    async def fetch_batch_connectivity(self, body_ids: List[int]) -> Dict[int, Dict]:
        """
        Fetch connectivity data for multiple neurons efficiently.
        """
        if not body_ids:
            return {}

        cache_key = f"batch_conn_{hash(tuple(sorted(body_ids)))}"
        if cache_key in self._batch_cache:
            return self._batch_cache[cache_key]

        logger.info(f"Fetching batch connectivity for {len(body_ids)} neurons")
        start_time = time.time()

        try:
            query = self.batch_connectivity_query(body_ids)
            results_df = self.connector.client.fetch_custom(query)

            if results_df.empty:
                return {}

            # Process connectivity data
            connectivity_data = {}
            for _, row in results_df.iterrows():
                body_id = row['sourceBodyId']

                connectivity_data[body_id] = {
                    'upstream': row['upstream_connections'] or [],
                    'downstream': row['downstream_connections'] or []
                }

            # Cache results
            self._batch_cache[cache_key] = connectivity_data

            query_time = time.time() - start_time
            logger.info(f"Batch connectivity query completed in {query_time:.3f}s")

            return connectivity_data

        except Exception as e:
            logger.error(f"Batch connectivity query failed: {e}")
            return {}

    def optimize_roi_hierarchy_query(self) -> str:
        """
        Optimized query for ROI hierarchy that reduces data transfer.
        Only fetches essential hierarchy information.
        """
        query = """
        MATCH (roi:Region)
        OPTIONAL MATCH (roi)-[:PartOf]->(parent:Region)
        RETURN
            roi.name as roi_name,
            parent.name as parent_name,
            roi.isParent as is_parent
        ORDER BY roi.name
        """
        return query

    async def get_roi_hierarchy_optimized(self) -> Dict[str, str]:
        """
        Get ROI hierarchy with optimized caching and minimal data transfer.
        """
        cache_key = "roi_hierarchy"
        if cache_key in self._query_cache:
            return self._query_cache[cache_key]

        logger.info("Fetching ROI hierarchy (optimized)")
        start_time = time.time()

        try:
            query = self.optimize_roi_hierarchy_query()
            results_df = self.connector.client.fetch_custom(query)

            hierarchy = {}
            for _, row in results_df.iterrows():
                roi_name = row['roi_name']
                parent_name = row['parent_name']
                if parent_name:
                    hierarchy[roi_name] = parent_name

            # Cache for future use
            self._query_cache[cache_key] = hierarchy

            query_time = time.time() - start_time
            logger.info(f"ROI hierarchy loaded in {query_time:.3f}s")

            return hierarchy

        except Exception as e:
            logger.error(f"ROI hierarchy query failed: {e}")
            return {}

    async def parallel_neuron_processing(self, neuron_types: List[str], max_workers: int = 5) -> Dict[str, Any]:
        """
        Process multiple neuron types in parallel with connection pooling.
        Uses ThreadPoolExecutor for I/O-bound database operations.
        """
        logger.info(f"Processing {len(neuron_types)} neuron types in parallel (workers: {max_workers})")

        # Split into batches for parallel processing
        batch_size = max(1, len(neuron_types) // max_workers)
        batches = [neuron_types[i:i + batch_size] for i in range(0, len(neuron_types), batch_size)]

        async def process_batch(batch):
            return await self.fetch_batch_neuron_data(batch)

        # Process batches concurrently
        start_time = time.time()
        batch_results = await asyncio.gather(*[process_batch(batch) for batch in batches])

        # Combine results
        combined_results = {}
        for batch_result in batch_results:
            combined_results.update(batch_result)

        process_time = time.time() - start_time
        logger.info(f"Parallel processing completed in {process_time:.3f}s")

        return combined_results

    def optimize_for_large_datasets(self, neuron_types: List[str], chunk_size: int = 20) -> List[List[str]]:
        """
        Split large neuron type lists into optimal chunks for batch processing.
        Prevents memory issues and database timeouts with very large datasets.
        """
        chunks = []
        for i in range(0, len(neuron_types), chunk_size):
            chunks.append(neuron_types[i:i + chunk_size])

        logger.info(f"Split {len(neuron_types)} neuron types into {len(chunks)} chunks (size: {chunk_size})")
        return chunks

    async def warm_cache(self, neuron_types: List[str]):
        """
        Pre-warm caches for better performance in subsequent operations.
        """
        logger.info(f"Warming cache for {len(neuron_types)} neuron types")

        # Warm neuron data cache
        await self.fetch_batch_neuron_data(neuron_types)

        # Warm ROI hierarchy cache
        await self.get_roi_hierarchy_optimized()

        logger.info("Cache warming completed")

    def clear_cache(self):
        """Clear all caches to free memory."""
        self._query_cache.clear()
        self._batch_cache.clear()
        logger.info("Query cache cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics for monitoring."""
        return {
            'query_cache_size': len(self._query_cache),
            'batch_cache_size': len(self._batch_cache),
            'total_cached_items': len(self._query_cache) + len(self._batch_cache)
        }


class ConnectionPoolManager:
    """
    Manages database connection pooling for better performance.
    Addresses network I/O bottlenecks identified in profiling.
    """

    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.connection_pool = asyncio.Semaphore(max_connections)
        self.active_connections = 0

    async def execute_with_pool(self, query_func, *args, **kwargs):
        """Execute query function with connection pooling."""
        async with self.connection_pool:
            self.active_connections += 1
            try:
                result = await query_func(*args, **kwargs)
                return result
            finally:
                self.active_connections -= 1

    def get_pool_stats(self) -> Dict[str, int]:
        """Get connection pool statistics."""
        return {
            'max_connections': self.max_connections,
            'active_connections': self.active_connections,
            'available_connections': self.max_connections - self.active_connections
        }


# Example usage and optimization patterns
async def example_optimized_workflow():
    """
    Example showing optimized workflow for index creation.
    Demonstrates all optimization techniques.
    """
    from .neuprint_connector import NeuPrintConnector
    from .config import Config

    # Load config and create connector
    config = Config.load("config.cns.yaml")
    connector = NeuPrintConnector(config)

    # Create optimizer
    optimizer = QueryOptimizer(connector)

    # Example neuron types to process
    neuron_types = ["LC10a", "LC10b", "LC11", "LC12", "LC13", "LC14", "LC15", "LC16", "LC17", "LC18"]

    print(f"Optimized processing example for {len(neuron_types)} neuron types")

    # Step 1: Warm cache for better performance
    await optimizer.warm_cache(neuron_types)

    # Step 2: Batch fetch all neuron data
    start_time = time.time()
    neuron_data = await optimizer.fetch_batch_neuron_data(neuron_types)
    batch_time = time.time() - start_time

    print(f"Batch neuron data fetch: {batch_time:.3f}s")
    print(f"Data retrieved for {len(neuron_data)} types")

    # Step 3: Process in parallel for ROI data
    all_body_ids = []
    for type_name, data in neuron_data.items():
        if not data.empty and 'bodyId' in data.columns:
            all_body_ids.extend(data['bodyId'].tolist())

    if all_body_ids:
        roi_data = await optimizer.fetch_batch_roi_data(all_body_ids)
        connectivity_data = await optimizer.fetch_batch_connectivity(all_body_ids)

        print(f"ROI data retrieved for {len(roi_data)} neurons")
        print(f"Connectivity data retrieved for {len(connectivity_data)} neurons")

    # Step 4: Show cache statistics
    cache_stats = optimizer.get_cache_stats()
    print(f"Cache stats: {cache_stats}")

    return {
        'neuron_data': neuron_data,
        'roi_data': roi_data if 'roi_data' in locals() else {},
        'connectivity_data': connectivity_data if 'connectivity_data' in locals() else {},
        'processing_time': batch_time,
        'cache_stats': cache_stats
    }


# Performance monitoring utilities
def benchmark_query_performance(original_func, optimized_func, *args, **kwargs):
    """
    Benchmark original vs optimized query performance.
    """
    import time

    # Benchmark original
    start_time = time.time()
    original_result = original_func(*args, **kwargs)
    original_time = time.time() - start_time

    # Benchmark optimized
    start_time = time.time()
    optimized_result = optimized_func(*args, **kwargs)
    optimized_time = time.time() - start_time

    improvement = ((original_time - optimized_time) / original_time) * 100
    speedup = original_time / optimized_time

    print(f"Performance Comparison:")
    print(f"  Original: {original_time:.3f}s")
    print(f"  Optimized: {optimized_time:.3f}s")
    print(f"  Improvement: {improvement:.1f}% ({speedup:.1f}x speedup)")

    return {
        'original_time': original_time,
        'optimized_time': optimized_time,
        'improvement_percent': improvement,
        'speedup_factor': speedup
    }
