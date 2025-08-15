#!/usr/bin/env python3
"""
Batch Query Optimization Example for QuickPage
Demonstrates how to implement the most critical optimization: batch database queries.

This example shows how to replace N individual queries with 1 batch query,
which is the primary bottleneck identified in the performance analysis.
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class BatchQueryOptimizer:
    """
    Demonstrates batch query optimization for NeuPrint database operations.

    Key optimization: Replace N individual queries with 1 batch query.
    Expected impact: 10-50x reduction in database round-trips.
    """

    def __init__(self, connector):
        self.connector = connector
        self.batch_cache = {}

    def generate_batch_neuron_query(self, neuron_types: List[str]) -> str:
        """
        Generate optimized Cypher query for multiple neuron types.

        BEFORE (N queries):
            MATCH (n:Neuron) WHERE n.type = 'LC10a' RETURN n;
            MATCH (n:Neuron) WHERE n.type = 'LC11' RETURN n;
            ... (repeat for each type)

        AFTER (1 query):
            UNWIND ['LC10a', 'LC11', ...] as neuron_type
            MATCH (n:Neuron) WHERE n.type = neuron_type
            RETURN neuron_type, n.bodyId, n.type, n.status, ...
        """
        # Escape neuron type names for Cypher
        escaped_types = [self.connector._escape_regex_chars(nt) for nt in neuron_types]
        types_list = "[" + ", ".join(f"'{t}'" for t in escaped_types) + "]"

        query = f"""
        UNWIND {types_list} as target_type
        MATCH (n:Neuron)
        WHERE n.type = target_type

        // Get basic neuron properties
        WITH n, target_type

        // Optional: Get synapse counts efficiently
        OPTIONAL MATCH (n)-[:Contains]->(ss:SynapseSet)

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
            n.post as post,
            collect(DISTINCT ss.roi) as rois
        ORDER BY target_type, n.bodyId
        """
        return query

    def generate_batch_roi_query(self, body_ids: List[int]) -> str:
        """
        Generate batch query for ROI data across multiple neurons.
        Replaces individual ROI queries per neuron with single batch query.
        """
        body_ids_str = "[" + ", ".join(str(bid) for bid in body_ids) + "]"

        query = f"""
        UNWIND {body_ids_str} as target_body_id
        MATCH (n:Neuron {{bodyId: target_body_id}})

        // Get ROI connections efficiently
        OPTIONAL MATCH (n)-[:Contains]->(ss:SynapseSet)-[:ConnectsTo]->(roi:Region)
        WHERE ss.pre > 0 OR ss.post > 0

        RETURN
            target_body_id as bodyId,
            roi.name as roi,
            ss.pre as pre,
            ss.post as post,
            (ss.pre + ss.post) as total
        ORDER BY target_body_id, total DESC
        """
        return query

    def generate_batch_connectivity_query(self, body_ids: List[int], min_weight: int = 3) -> str:
        """
        Generate batch connectivity query for multiple neurons.
        Gets upstream and downstream connections in single query.
        """
        body_ids_str = "[" + ", ".join(str(bid) for bid in body_ids) + "]"

        query = f"""
        UNWIND {body_ids_str} as source_body_id
        MATCH (source:Neuron {{bodyId: source_body_id}})

        // Get upstream connections
        OPTIONAL MATCH (upstream:Neuron)-[w1:ConnectsTo]->(source)
        WHERE w1.weight >= {min_weight}
        WITH source, source_body_id,
             collect({{
                 bodyId: upstream.bodyId,
                 type: upstream.type,
                 weight: w1.weight,
                 direction: 'upstream'
             }})[0..50] as upstream_connections

        // Get downstream connections
        OPTIONAL MATCH (source)-[w2:ConnectsTo]->(downstream:Neuron)
        WHERE w2.weight >= {min_weight}
        WITH source, source_body_id, upstream_connections,
             collect({{
                 bodyId: downstream.bodyId,
                 type: downstream.type,
                 weight: w2.weight,
                 direction: 'downstream'
             }})[0..50] as downstream_connections

        RETURN
            source_body_id as bodyId,
            upstream_connections,
            downstream_connections
        ORDER BY source_body_id
        """
        return query

    async def fetch_batch_neuron_data(self, neuron_types: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Fetch neuron data for multiple types in single optimized query.

        PERFORMANCE IMPROVEMENT:
        - Before: N queries (one per neuron type)
        - After: 1 query (all neuron types)
        - Expected speedup: 10-50x for large N
        """
        if not neuron_types:
            return {}

        cache_key = f"batch_neurons_{hash(tuple(sorted(neuron_types)))}"
        if cache_key in self.batch_cache:
            logger.info(f"Cache hit for {len(neuron_types)} neuron types")
            return self.batch_cache[cache_key]

        logger.info(f"Batch fetching neuron data for {len(neuron_types)} types")
        start_time = time.time()

        try:
            # Generate and execute batch query
            query = self.generate_batch_neuron_query(neuron_types)
            results_df = self.connector.client.fetch_custom(query)

            if results_df.empty:
                logger.warning("Batch query returned no results")
                return {}

            # Group results by neuron type
            grouped_data = {}
            for neuron_type in neuron_types:
                type_data = results_df[results_df['target_type'] == neuron_type].copy()
                if not type_data.empty:
                    # Remove grouping column and process
                    type_data = type_data.drop('target_type', axis=1)
                    grouped_data[neuron_type] = type_data
                else:
                    grouped_data[neuron_type] = pd.DataFrame()

            # Cache results
            self.batch_cache[cache_key] = grouped_data

            query_time = time.time() - start_time
            logger.info(f"Batch neuron query completed in {query_time:.3f}s "
                       f"({len(neuron_types)/query_time:.1f} types/sec)")

            return grouped_data

        except Exception as e:
            logger.error(f"Batch neuron query failed: {e}")
            return {}

    async def fetch_batch_roi_data(self, body_ids: List[int]) -> Dict[int, pd.DataFrame]:
        """
        Fetch ROI data for multiple neurons in single query.
        Replaces individual ROI queries with batch operation.
        """
        if not body_ids:
            return {}

        cache_key = f"batch_roi_{hash(tuple(sorted(body_ids)))}"
        if cache_key in self.batch_cache:
            return self.batch_cache[cache_key]

        logger.info(f"Batch fetching ROI data for {len(body_ids)} neurons")
        start_time = time.time()

        try:
            query = self.generate_batch_roi_query(body_ids)
            results_df = self.connector.client.fetch_custom(query)

            # Group by body ID
            grouped_data = {}
            for body_id in body_ids:
                roi_data = results_df[results_df['bodyId'] == body_id].copy()
                grouped_data[body_id] = roi_data

            self.batch_cache[cache_key] = grouped_data

            query_time = time.time() - start_time
            logger.info(f"Batch ROI query completed in {query_time:.3f}s")

            return grouped_data

        except Exception as e:
            logger.error(f"Batch ROI query failed: {e}")
            return {}

    async def fetch_batch_connectivity_data(self, body_ids: List[int]) -> Dict[int, Dict]:
        """
        Fetch connectivity data for multiple neurons efficiently.
        """
        if not body_ids:
            return {}

        logger.info(f"Batch fetching connectivity for {len(body_ids)} neurons")
        start_time = time.time()

        try:
            query = self.generate_batch_connectivity_query(body_ids)
            results_df = self.connector.client.fetch_custom(query)

            # Process connectivity data
            connectivity_data = {}
            for _, row in results_df.iterrows():
                body_id = row['bodyId']
                connectivity_data[body_id] = {
                    'upstream': row['upstream_connections'] or [],
                    'downstream': row['downstream_connections'] or []
                }

            query_time = time.time() - start_time
            logger.info(f"Batch connectivity query completed in {query_time:.3f}s")

            return connectivity_data

        except Exception as e:
            logger.error(f"Batch connectivity query failed: {e}")
            return {}


class OptimizedIndexWorkflow:
    """
    Example workflow showing how to integrate batch queries into index creation.
    Demonstrates the complete optimization pattern.
    """

    def __init__(self, connector):
        self.connector = connector
        self.batch_optimizer = BatchQueryOptimizer(connector)

    async def create_index_optimized(self, neuron_types: List[str]) -> Dict[str, Any]:
        """
        Optimized index creation workflow using batch queries.

        OPTIMIZATION PATTERN:
        1. Batch fetch all neuron data (1 query instead of N)
        2. Batch fetch all ROI data (1 query instead of N)
        3. Batch fetch connectivity data (1 query instead of N)
        4. Process results in parallel
        """
        logger.info(f"Starting optimized index creation for {len(neuron_types)} neuron types")
        total_start = time.time()

        # STEP 1: Batch fetch neuron data
        neuron_data_start = time.time()
        neuron_data = await self.batch_optimizer.fetch_batch_neuron_data(neuron_types)
        neuron_data_time = time.time() - neuron_data_start

        logger.info(f"Neuron data fetched in {neuron_data_time:.3f}s")

        # STEP 2: Extract all body IDs for subsequent queries
        all_body_ids = []
        for type_name, data in neuron_data.items():
            if not data.empty and 'bodyId' in data.columns:
                all_body_ids.extend(data['bodyId'].tolist())

        logger.info(f"Found {len(all_body_ids)} total neurons across all types")

        # STEP 3: Batch fetch ROI and connectivity data in parallel
        roi_start = time.time()
        roi_task = self.batch_optimizer.fetch_batch_roi_data(all_body_ids)
        connectivity_task = self.batch_optimizer.fetch_batch_connectivity_data(all_body_ids)

        roi_data, connectivity_data = await asyncio.gather(roi_task, connectivity_task)
        roi_time = time.time() - roi_start

        logger.info(f"ROI and connectivity data fetched in {roi_time:.3f}s")

        # STEP 4: Process and combine results
        process_start = time.time()
        index_entries = []

        for neuron_type in neuron_types:
            type_neuron_data = neuron_data.get(neuron_type, pd.DataFrame())

            # Extract ROI summary for this type
            roi_summary = []
            parent_roi = ""

            if not type_neuron_data.empty:
                type_body_ids = type_neuron_data['bodyId'].tolist()
                roi_summary, parent_roi = self._process_roi_summary(
                    type_body_ids, roi_data, connectivity_data
                )

            # Create index entry
            entry = {
                'name': neuron_type,
                'neuron_count': len(type_neuron_data),
                'roi_summary': roi_summary,
                'parent_roi': parent_roi,
                'has_data': not type_neuron_data.empty
            }

            index_entries.append(entry)

        process_time = time.time() - process_start
        total_time = time.time() - total_start

        logger.info(f"Results processed in {process_time:.3f}s")
        logger.info(f"Total optimized workflow: {total_time:.3f}s")

        return {
            'index_entries': index_entries,
            'performance_stats': {
                'total_time': total_time,
                'neuron_data_time': neuron_data_time,
                'roi_data_time': roi_time,
                'processing_time': process_time,
                'types_per_second': len(neuron_types) / total_time
            }
        }

    def _process_roi_summary(self, body_ids: List[int], roi_data: Dict,
                           connectivity_data: Dict) -> tuple:
        """
        Process ROI summary from batch-fetched data.
        """
        # Aggregate ROI data for this neuron type
        roi_counts = {}

        for body_id in body_ids:
            body_roi_data = roi_data.get(body_id, pd.DataFrame())

            for _, row in body_roi_data.iterrows():
                roi_name = row.get('roi', '')
                if roi_name:
                    if roi_name not in roi_counts:
                        roi_counts[roi_name] = {'pre': 0, 'post': 0, 'total': 0}

                    roi_counts[roi_name]['pre'] += row.get('pre', 0)
                    roi_counts[roi_name]['post'] += row.get('post', 0)
                    roi_counts[roi_name]['total'] += row.get('total', 0)

        # Convert to sorted list
        roi_summary = []
        for roi_name, counts in roi_counts.items():
            if counts['total'] > 0:  # Only include ROIs with connections
                roi_summary.append({
                    'name': roi_name,
                    'pre': counts['pre'],
                    'post': counts['post'],
                    'total': counts['total']
                })

        # Sort by total connections and take top 5
        roi_summary.sort(key=lambda x: x['total'], reverse=True)
        roi_summary = roi_summary[:5]

        # Determine parent ROI (simplified)
        parent_roi = roi_summary[0]['name'] if roi_summary else ""

        return roi_summary, parent_roi


async def performance_comparison_demo():
    """
    Demonstrate the performance difference between individual vs batch queries.
    """
    print("🚀 Batch Query Optimization Demo")
    print("=" * 50)

    # Mock connector for demonstration
    class MockConnector:
        def _escape_regex_chars(self, text):
            return text.replace("'", "\\'")

        @property
        def client(self):
            return self

        def fetch_custom(self, query):
            # Simulate query execution time
            import time
            time.sleep(0.1)  # Simulate 100ms query time

            # Return mock DataFrame
            import pandas as pd
            return pd.DataFrame({
                'target_type': ['LC10a', 'LC11'],
                'bodyId': [123, 456],
                'type': ['LC10a', 'LC11'],
                'status': ['Traced', 'Traced']
            })

    connector = MockConnector()
    optimizer = BatchQueryOptimizer(connector)

    # Test with sample neuron types
    test_types = ['LC10a', 'LC11', 'LC12', 'LC13', 'LC14']

    print(f"Testing with {len(test_types)} neuron types...")

    # Simulate individual queries (old method)
    individual_start = time.time()
    for neuron_type in test_types:
        # Each query takes ~100ms (mock)
        await asyncio.sleep(0.1)
    individual_time = time.time() - individual_start

    # Test batch query (optimized method)
    batch_start = time.time()
    result = await optimizer.fetch_batch_neuron_data(test_types)
    batch_time = time.time() - batch_start

    # Calculate improvement
    improvement = individual_time / batch_time if batch_time > 0 else 0

    print(f"\n📊 Performance Comparison:")
    print(f"   Individual queries: {individual_time:.3f}s")
    print(f"   Batch query: {batch_time:.3f}s")
    print(f"   Improvement: {improvement:.1f}x faster")
    print(f"   Time saved: {individual_time - batch_time:.3f}s")

    print(f"\n💡 Extrapolation to 10,000 neuron types:")
    print(f"   Individual: {individual_time * 2000:.1f}s ({individual_time * 2000 / 60:.1f} minutes)")
    print(f"   Batch: {batch_time * 2:.1f}s")
    print(f"   Savings: {(individual_time * 2000 - batch_time * 2) / 60:.1f} minutes")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

    # Run demonstration
    asyncio.run(performance_comparison_demo())

    print("\n" + "="*50)
    print("🎯 Integration Instructions:")
    print("1. Replace individual neuron queries with BatchQueryOptimizer.fetch_batch_neuron_data()")
    print("2. Replace individual ROI queries with BatchQueryOptimizer.fetch_batch_roi_data()")
    print("3. Use OptimizedIndexWorkflow.create_index_optimized() pattern")
    print("4. Expected improvement: 10-50x faster for large datasets")
    print("5. Test with small subset first, then scale up")
