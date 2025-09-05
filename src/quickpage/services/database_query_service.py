"""
Database Query Service for handling NeuPrint database operations.

This service centralizes all database query operations that were previously
scattered throughout the PageGenerator class, providing a clean interface
for database interactions and improving testability.
"""

import logging
import re
from typing import Dict, Optional, List, Tuple, Set
import pandas as pd

logger = logging.getLogger(__name__)


class DatabaseQueryService:
    """
    Service for handling NeuPrint database queries and operations.

    This service extracts complex database query logic from the PageGenerator
    to provide a centralized, testable interface for database operations.
    """

    def __init__(self, config, cache_manager=None, data_processing_service=None):
        """
        Initialize the database query service.

        Args:
            config: Configuration object
            cache_manager: Optional cache manager for caching query results
            data_processing_service: Optional data processing service for ROI aggregation
        """
        self.config = config
        self.cache_manager = cache_manager
        self.data_processing_service = data_processing_service
        self._all_columns_cache = None

    def get_all_possible_columns_from_dataset(
        self, connector
    ) -> Tuple[List[Dict], Dict[str, Set]]:
        """
        Query the dataset to get all possible column coordinates that exist anywhere
        in ME, LO, or LOP regions, determining column existence based on actual
        neuron innervation (pre > 0 OR post > 0) across all neuron types.

        This method is cached to avoid expensive repeated queries.

        Args:
            connector: NeuPrint connector instance for database queries

        Returns:
            Tuple of (all_possible_columns, region_columns_map) where:
            - all_possible_columns: List of dicts with hex1, hex2 (integers)
            - region_columns_map: Dict mapping region_side names to sets of (hex1, hex2) tuples
        """
        # Return cached result if available
        if self._all_columns_cache is not None:
            logger.info(
                "get_all_possible_columns_from_dataset: returning cached result"
            )
            return self._all_columns_cache

        # Generate cache key based on server and dataset
        cache_key = f"all_columns_{connector.config.neuprint.server}_{connector.config.neuprint.dataset}"

        # Try to load from any existing neuron cache first
        if hasattr(self, "cache_manager") and self.cache_manager is not None:
            try:
                cached_neuron_types = self.cache_manager.list_cached_neuron_types()
                for neuron_type in cached_neuron_types:
                    cached_columns, cached_region_map = (
                        self._get_columns_from_neuron_cache(neuron_type)
                    )
                    if cached_columns is not None and cached_region_map is not None:
                        result_tuple = (cached_columns, cached_region_map)
                        self._all_columns_cache = result_tuple
                        logger.info(
                            f"get_all_possible_columns_from_dataset: loaded from {neuron_type} neuron cache ({len(cached_columns)} columns)"
                        )
                        return result_tuple
            except Exception as e:
                logger.debug(f"Failed to load column data from neuron cache: {e}")

        # Check persistent standalone cache as fallback
        persistent_result = self._load_persistent_columns_cache(cache_key)
        if persistent_result is not None:
            self._all_columns_cache = persistent_result
            return persistent_result

        try:
            # Query all column ROIs from neuron roiInfo JSON data with aggregated counts
            query = """
                MATCH (n:Neuron)
                WHERE n.roiInfo IS NOT NULL
                WITH n, apoc.convert.fromJsonMap(n.roiInfo) as roiData
                UNWIND keys(roiData) as roiName
                WITH roiName, roiData[roiName] as roiInfo
                WHERE roiName =~ '^(ME|LO|LOP)_[RL]_col_[A-Za-z0-9]+_[A-Za-z0-9]+$'
                AND (roiInfo.pre > 0 OR roiInfo.post > 0)
                WITH roiName,
                     SUM(COALESCE(roiInfo.pre, 0)) as total_pre,
                     SUM(COALESCE(roiInfo.post, 0)) as total_post
                RETURN roiName as roi, total_pre as pre, total_post as post
                ORDER BY roi
            """

            result = connector.client.fetch_custom(query)

            if result is None or result.empty:
                return [], {}

            # Parse all ROI data to extract coordinates and regions with side information
            column_pattern = r"^(ME|LO|LOP)_([RL])_col_([A-Za-z0-9]+)_([A-Za-z0-9]+)$"
            column_data = {}  # Maps (hex1, hex2) to set of region_side combinations that have this column

            for _, row in result.iterrows():
                match = re.match(column_pattern, row["roi"])
                if match:
                    region, side, coord1, coord2 = match.groups()

                    # Try to parse coordinates as decimal first, then hex if that fails
                    try:
                        hex1_dec = int(coord1)
                    except ValueError:
                        try:
                            hex1_dec = int(coord1, 16)
                        except ValueError:
                            continue  # Skip invalid coordinates

                    try:
                        hex2_dec = int(coord2)
                    except ValueError:
                        try:
                            hex2_dec = int(coord2, 16)
                        except ValueError:
                            continue  # Skip invalid coordinates

                    coord_key = (hex1_dec, hex2_dec)

                    # Track which region_side combinations have this column coordinate
                    region_side = f"{region}_{side}"
                    if coord_key not in column_data:
                        column_data[coord_key] = set()
                    column_data[coord_key].add(region_side)

            # Build side-specific region columns map - each region_side contains only columns where there's actual innervation
            region_columns_map = {
                "ME_L": set(),
                "LO_L": set(),
                "LOP_L": set(),
                "ME_R": set(),
                "LO_R": set(),
                "LOP_R": set(),
            }
            for coord_key, region_sides in column_data.items():
                for region_side in region_sides:
                    region_columns_map[region_side].add(coord_key)

            # Build all possible columns list from all discovered coordinates
            all_possible_columns = []
            for coord_key in sorted(column_data.keys()):
                hex1_dec, hex2_dec = coord_key
                all_possible_columns.append({"hex1": hex1_dec, "hex2": hex2_dec})

            # Cache the result for future use (in-memory only, no longer saving standalone cache)
            result = (all_possible_columns, region_columns_map)
            self._all_columns_cache = result
            logger.info(
                f"get_all_possible_columns_from_dataset: cached {len(all_possible_columns)} columns"
            )
            return result

        except Exception as e:
            logger.warning(f"Could not query dataset for all columns: {e}")
            return [], {}

    def get_connected_bodyids(self, visible_neurons: List[int], connector) -> Dict:
        """
        Get bodyIds of the top cell from each type that are connected with the
        current 'visible_neuron' in the Neuroglancer view. If there are multiple
        visible_neurons, then the bodyIds are aggregated by type and soma side.

        Args:
            visible_neurons: List of the visible neuron's bodyId.
            connector: NeuPrint connector instance.

        Returns:
            Dictionary of the connected bodyIds, with keys 'downstream' and 'upstream'.
            Each direction contains keys like 'L1_R' and 'L1_L' for soma side-specific lookups.
        """
        if not visible_neurons:
            return {"downstream": {}, "upstream": {}}

        try:
            # Query for downstream and upstream connections
            bodyid_list = ", ".join(map(str, visible_neurons))

            # Get downstream connections (neurons that receive input from visible neurons)
            downstream_query = f"""
                MATCH (n:Neuron)-[e:ConnectsTo]->(m:Neuron)
                WHERE n.bodyId IN [{bodyid_list}]
                AND m.type IS NOT NULL
                RETURN m.bodyId as bodyId, m.type as type, m.somaSide as somaSide,
                       SUM(e.weight) as total_weight, m.pre as pre, m.post as post
                ORDER BY m.type, total_weight DESC
            """

            # Get upstream connections (neurons that provide input to visible neurons)
            upstream_query = f"""
                MATCH (n:Neuron)-[e:ConnectsTo]->(m:Neuron)
                WHERE m.bodyId IN [{bodyid_list}]
                AND n.type IS NOT NULL
                RETURN n.bodyId as bodyId, n.type as type, n.somaSide as somaSide,
                       SUM(e.weight) as total_weight, n.pre as pre, n.post as post
                ORDER BY n.type, total_weight DESC
            """

            downstream_result = connector.client.fetch_custom(downstream_query)
            upstream_result = connector.client.fetch_custom(upstream_query)

            def process_connections(result_df):
                """Process connection results to get top neuron by type and soma side."""
                if result_df is None or result_df.empty:
                    return {}

                connections = {}

                # Group by type and soma side to get the top neuron for each combination
                for neuron_type in result_df["type"].unique():
                    type_mask = result_df["type"] == neuron_type
                    type_neurons = result_df.loc[type_mask].copy()

                    # Get top neuron for each soma side within this type
                    for soma_side in type_neurons["somaSide"].unique():
                        if pd.isna(soma_side):
                            continue

                        side_mask = type_neurons["somaSide"] == soma_side
                        side_neurons = type_neurons.loc[side_mask].copy()

                        if not side_neurons.empty:
                            # Sort by total weight (connection strength) and get top neuron
                            side_neurons_sorted = side_neurons.sort_values(
                                "total_weight", ascending=False
                            )
                            top_neuron = side_neurons_sorted.iloc[0]

                            # Create key combining type and soma side
                            key = f"{neuron_type}_{soma_side}"
                            connections[key] = [int(top_neuron["bodyId"])]

                return connections

            downstream_connections = process_connections(downstream_result)
            upstream_connections = process_connections(upstream_result)

            return {
                "downstream": downstream_connections,
                "upstream": upstream_connections,
            }

        except Exception as e:
            logger.error(f"Error getting connected bodyIds: {e}")
            return {"downstream": {}, "upstream": {}}

    def get_partner_body_ids(
        self,
        neuron_type: str,
        connector,
        include_downstream: bool = True,
        include_upstream: bool = True,
        soma_side: Optional[str] = None,
    ) -> Dict:
        """
        Get partner bodyIds for a neuron type, with optional filtering by connection direction.

        Args:
            neuron_type: The neuron type to find partners for
            connector: NeuPrint connector instance
            include_downstream: Whether to include downstream partners
            include_upstream: Whether to include upstream partners
            soma_side: Optional soma side filter

        Returns:
            Dictionary with 'downstream' and 'upstream' keys containing partner information
        """
        try:
            partners = {"downstream": {}, "upstream": {}}

            # Base query to get neurons of the specified type
            type_query = f"""
                MATCH (n:Neuron)
                WHERE n.type = "{neuron_type}"
                RETURN n.bodyId as bodyId, n.somaSide as somaSide
            """

            type_result = connector.client.fetch_custom(type_query)
            if type_result is None or type_result.empty:
                return partners

            # Filter by soma side if specified
            if soma_side and soma_side != "all":
                if soma_side == "left":
                    type_result = type_result[type_result["somaSide"] == "L"]
                elif soma_side == "right":
                    type_result = type_result[type_result["somaSide"] == "R"]
                elif soma_side == "middle":
                    type_result = type_result[type_result["somaSide"] == "M"]

            if type_result.empty:
                return partners

            bodyid_list = ", ".join(map(str, type_result["bodyId"].tolist()))

            # Get downstream partners if requested
            if include_downstream:
                downstream_query = f"""
                    MATCH (n:Neuron)-[e:ConnectsTo]->(m:Neuron)
                    WHERE n.bodyId IN [{bodyid_list}]
                    AND m.type IS NOT NULL AND m.type <> '{neuron_type}'
                    RETURN m.type as partner_type, m.somaSide as partner_soma_side,
                           m.bodyId as partner_bodyId, SUM(e.weight) as total_weight,
                           m.pre as pre, m.post as post
                    ORDER BY partner_type, total_weight DESC
                """

                downstream_result = connector.client.fetch_custom(downstream_query)
                if downstream_result is not None and not downstream_result.empty:
                    partners["downstream"] = self._process_partner_results(
                        downstream_result
                    )

            # Get upstream partners if requested
            if include_upstream:
                upstream_query = f"""
                    MATCH (n:Neuron)-[e:ConnectsTo]->(m:Neuron)
                    WHERE m.bodyId IN [{bodyid_list}]
                    AND n.type IS NOT NULL AND n.type <> '{neuron_type}'
                    RETURN n.type as partner_type, n.somaSide as partner_soma_side,
                           n.bodyId as partner_bodyId, SUM(e.weight) as total_weight,
                           n.pre as pre, n.post as post
                    ORDER BY partner_type, total_weight DESC
                """

                upstream_result = connector.client.fetch_custom(upstream_query)
                if upstream_result is not None and not upstream_result.empty:
                    partners["upstream"] = self._process_partner_results(
                        upstream_result
                    )

            return partners

        except Exception as e:
            logger.error(f"Error getting partner bodyIds for {neuron_type}: {e}")
            return {"downstream": {}, "upstream": {}}

    def get_region_for_neuron_type(self, neuron_type: str, connector) -> str:
        """
        Get the primary region for a neuron type based on ROI analysis.

        Args:
            neuron_type: The neuron type to analyze
            connector: NeuPrint connector instance

        Returns:
            Cleaned parent ROI string, or "" if unavailable
        """

        def _clean_roi_name(name: str) -> str:
            if not name:
                return ""
            name = name.rstrip("*").strip()
            return re.sub(r"\s*\([RLM]\)$", "", name).strip()

        def _find_parent_recursive(target: str, tree: dict, parent: str = "") -> str:
            for k, v in (tree or {}).items():
                ck = _clean_roi_name(k)
                if ck == target:
                    return parent
                if isinstance(v, dict):
                    hit = _find_parent_recursive(target, v, ck)
                    if hit:
                        return hit
            return ""

        def _get_parent_from_hierarchy(roi_name: str, connector) -> str:
            try:
                hierarchy = connector._get_roi_hierarchy()
            except Exception:
                return ""
            if not hierarchy:
                return ""
            return _find_parent_recursive(_clean_roi_name(roi_name), hierarchy) or ""

        # Check cache first
        try:
            if hasattr(self, "cache_manager") and self.cache_manager is not None:
                cache_entry = self.cache_manager.load_neuron_type_cache(neuron_type)
                if cache_entry and getattr(cache_entry, "parent_roi", None):
                    return _clean_roi_name(cache_entry.parent_roi)
        except Exception:
            pass

        # Compute from NeuPrint data
        try:
            data = connector.get_neuron_data(neuron_type, soma_side="combined")
            if not data:
                return ""

            roi_counts = data.get("roi_counts")
            neurons_df = data.get("neurons")
            if (
                roi_counts is None
                or getattr(roi_counts, "empty", True)
                or neurons_df is None
                or getattr(neurons_df, "empty", True)
            ):
                return ""

            # Aggregate ROI data (this would need to be implemented or imported)
            roi_summary = self._aggregate_roi_data(
                roi_counts, neurons_df, "combined", connector
            )

            # Use configurable threshold from ThresholdService
            from .threshold_service import ThresholdService

            threshold_service = ThresholdService()
            threshold = threshold_service.get_roi_filtering_threshold()
            seen = set()
            top_roi_clean = None
            for roi in roi_summary or []:
                name = roi.get("name", "")
                pre_pct = roi.get("pre_percentage", 0.0) or 0.0
                post_pct = roi.get("post_percentage", 0.0) or 0.0
                if pre_pct >= threshold or post_pct >= threshold:
                    cleaned = _clean_roi_name(name)
                    if cleaned and cleaned not in seen:
                        top_roi_clean = cleaned
                        break

            if not top_roi_clean:
                return ""

            return _clean_roi_name(_get_parent_from_hierarchy(top_roi_clean, connector))
        except Exception:
            return ""

    def _process_partner_results(self, result_df: pd.DataFrame) -> Dict:
        """
        Process partner query results to get top partner for each type and soma side.

        Args:
            result_df: DataFrame with partner query results

        Returns:
            Dictionary with partner information organized by type and soma side
        """
        partners = {}

        for partner_type in result_df["partner_type"].unique():
            type_mask = result_df["partner_type"] == partner_type
            type_partners = result_df.loc[type_mask].copy()

            for soma_side in type_partners["partner_soma_side"].unique():
                if pd.isna(soma_side):
                    continue

                side_mask = type_partners["partner_soma_side"] == soma_side
                side_partners = type_partners.loc[side_mask].copy()

                if not side_partners.empty:
                    # Get top partner by connection weight
                    top_partner = side_partners.sort_values(
                        "total_weight", ascending=False
                    ).iloc[0]

                    key = f"{partner_type}_{soma_side}"
                    partners[key] = {
                        "bodyId": int(top_partner["partner_bodyId"]),
                        "weight": top_partner["total_weight"],
                        "pre": top_partner["pre"],
                        "post": top_partner["post"],
                    }

        return partners

    def _get_columns_from_neuron_cache(
        self, neuron_type: str
    ) -> Tuple[Optional[List], Optional[Dict]]:
        """
        Try to load column data from neuron cache.

        Args:
            neuron_type: Neuron type to load cache for

        Returns:
            Tuple of (columns, region_map) or (None, None) if not available
        """
        try:
            if hasattr(self, "cache_manager") and self.cache_manager is not None:
                cache_entry = self.cache_manager.load_neuron_type_cache(neuron_type)
                if (
                    cache_entry
                    and hasattr(cache_entry, "columns")
                    and hasattr(cache_entry, "region_columns_map")
                ):
                    return cache_entry.columns, cache_entry.region_columns_map
        except Exception as e:
            logger.debug(
                f"Failed to load columns from neuron cache for {neuron_type}: {e}"
            )

        return None, None

    def _load_persistent_columns_cache(self, cache_key: str) -> Optional[Tuple]:
        """
        Load persistent columns cache.

        Args:
            cache_key: Cache key to load

        Returns:
            Cached result tuple or None
        """
        # This would implement persistent cache loading logic
        # For now, return None as this is being phased out in favor of neuron cache
        return None

    def _aggregate_roi_data(self, roi_counts, neurons_df, soma_side, connector):
        """
        Aggregate ROI data for analysis.
        Delegates to data processing service if available.
        """
        if self.data_processing_service:
            return self.data_processing_service.aggregate_roi_data(
                roi_counts, neurons_df, soma_side, connector
            )
        else:
            logger.warning("Data processing service not available for ROI aggregation")
            return []
