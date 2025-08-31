"""
Cache Service for QuickPage.

This service handles all caching operations for neuron data, including
saving neuron type data and ROI hierarchy to persistent cache.
"""

import json
import hashlib
import time
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import pandas as pd

from ..models import NeuronCollection, NeuronTypeName, Neuron, BodyId, SynapseCount, SomaSide
from ..commands import GeneratePageCommand

logger = logging.getLogger(__name__)


class CacheService:
    """Service for handling all caching operations."""

    def __init__(self, cache_manager, page_generator=None):
        """Initialize cache service.

        Args:
            cache_manager: Cache manager instance
            page_generator: Optional page generator for ROI data extraction
        """
        self.cache_manager = cache_manager
        self.page_generator = page_generator

    async def save_neuron_type_to_cache(self, neuron_type_name: str, neuron_type_obj, command: GeneratePageCommand, connector=None):
        """Save neuron type data to persistent cache for later index generation."""
        if not self.cache_manager:
            return  # No cache manager available

        try:
            from ..cache import NeuronTypeCacheData

            # Save ROI hierarchy during generation to avoid queries during index creation
            await self.save_roi_hierarchy_to_cache()

            # Get full neuron data from the neuron type object
            neuron_data_dict = neuron_type_obj.to_dict()
            neurons_df = neuron_data_dict.get('neurons')
            connectivity_data = neuron_data_dict.get('connectivity', {})
            summary_data = neuron_data_dict.get('summary', {})

            # Convert DataFrame to NeuronCollection for enhanced cache processing
            neuron_collection = NeuronCollection(type_name=NeuronTypeName(neuron_type_name))

            if neurons_df is not None and not neurons_df.empty:
                for _, row in neurons_df.iterrows():
                    # Extract soma side
                    soma_side = None
                    if 'somaSide' in row and pd.notna(row['somaSide']):
                        soma_side_val = row['somaSide']
                        if soma_side_val == 'L':
                            soma_side = SomaSide.LEFT
                        elif soma_side_val == 'R':
                            soma_side = SomaSide.RIGHT
                        elif soma_side_val == 'M':
                            soma_side = SomaSide.MIDDLE

                    # Create Neuron object
                    neuron = Neuron(
                        body_id=BodyId(int(row['bodyId'])),
                        type_name=NeuronTypeName(neuron_type_name),
                        instance=row.get('instance'),
                        status=row.get('status'),
                        soma_side=soma_side,
                        soma_x=row.get('somaLocation', {}).get('x') if isinstance(row.get('somaLocation'), dict) else None,
                        soma_y=row.get('somaLocation', {}).get('y') if isinstance(row.get('somaLocation'), dict) else None,
                        soma_z=row.get('somaLocation', {}).get('z') if isinstance(row.get('somaLocation'), dict) else None,
                        synapse_count=SynapseCount(
                            pre=int(row.get('pre', 0)),
                            post=int(row.get('post', 0))
                        ),
                        cell_class=row.get('cellClass'),
                        cell_subclass=row.get('cellSubclass'),
                        cell_superclass=row.get('cellSuperclass')
                    )
                    neuron_collection.add_neuron(neuron)

            # Extract ROI summary and parent ROI from neuron type data
            roi_summary = []
            parent_roi = ""

            # Get ROI data if available in the neuron data
            roi_counts_df = neuron_data_dict.get('roi_counts')
            if roi_counts_df is not None and not roi_counts_df.empty and self.page_generator:
                try:
                    # Use the page generator's ROI aggregation method with correct connector
                    active_connector = connector or (self.page_generator.connector if hasattr(self.page_generator, 'connector') else None)
                    if not active_connector:
                        logger.debug(f"No connector available for ROI data extraction for {neuron_type_name}")
                        roi_summary = []
                        parent_roi = ""
                    else:
                        roi_summary_full = self.page_generator._aggregate_roi_data(
                            roi_counts_df, neurons_df, 'combined', active_connector
                        )

                        # Filter ROIs by threshold and clean names (same logic as IndexService)
                        threshold = 1.5
                        cleaned_roi_summary = []
                        seen_names = set()

                        for roi in roi_summary_full:
                            if roi['pre_percentage'] >= threshold or roi['post_percentage'] >= threshold:
                                cleaned_name = self._clean_roi_name(roi['name'])
                                if cleaned_name and cleaned_name not in seen_names:
                                    cleaned_roi_summary.append({
                                        'name': cleaned_name,
                                        'total': roi['total'],
                                        'pre_percentage': roi['pre_percentage'],
                                        'post_percentage': roi['post_percentage']
                                    })
                                    seen_names.add(cleaned_name)

                                    if len(cleaned_roi_summary) >= 5:
                                        break

                        roi_summary = cleaned_roi_summary

                        # Get parent ROI for the highest ranking (first) ROI
                        if roi_summary:
                            highest_roi = roi_summary[0]['name']
                            parent_roi = self._get_roi_hierarchy_parent(highest_roi, active_connector)

                        logger.debug(f"Extracted ROI data for {neuron_type_name}: {len(roi_summary)} ROIs, parent: {parent_roi}")

                except Exception as e:
                    logger.debug(f"Failed to extract ROI data for {neuron_type_name}: {e}")
                    roi_summary = []
                    parent_roi = ""

            # Extract column data from PageGenerator if available
            columns_data = None
            region_columns_map = None
            try:
                if hasattr(self.page_generator, '_neuron_type_columns_cache'):
                    cache_key = f"columns_{neuron_type_name}"
                    if cache_key in self.page_generator._neuron_type_columns_cache:
                        type_columns, type_region_map = self.page_generator._neuron_type_columns_cache[cache_key]
                        columns_data = type_columns
                        # Convert sets to lists for JSON serialization
                        region_columns_map = {}
                        for region, coords_set in type_region_map.items():
                            region_columns_map[region] = list(coords_set)
                        logger.debug(f"Extracted column data for {neuron_type_name}: {len(columns_data)} columns")
            except Exception as e:
                logger.debug(f"Failed to extract column data for {neuron_type_name}: {e}")

            # Create enhanced cache data with connectivity and distribution information
            cache_data = NeuronTypeCacheData.from_neuron_collection(
                neuron_collection=neuron_collection,
                roi_summary=roi_summary,
                parent_roi=parent_roi,
                connectivity_data=connectivity_data,
                neuron_data_df=neurons_df,
                columns_data=columns_data,
                region_columns_map=region_columns_map
            )

            # Save to cache
            success = self.cache_manager.save_neuron_type_cache(cache_data)
            if success:
                logger.debug(f"Saved enhanced cache data for neuron type {neuron_type_name}")
            else:
                logger.warning(f"Failed to save cache data for neuron type {neuron_type_name}")

        except Exception as e:
            logger.warning(f"Error saving cache for {neuron_type_name}: {e}")
            import traceback
            logger.debug(f"Cache save error details: {traceback.format_exc()}")

    async def save_roi_hierarchy_to_cache(self):
        """Save ROI hierarchy to cache during generation to avoid queries during index creation."""
        try:
            # Check if ROI hierarchy is already cached
            if self.cache_manager and self.cache_manager.load_roi_hierarchy():
                logger.debug("ROI hierarchy already cached, skipping fetch")
                return

            logger.debug("Fetching ROI hierarchy from database for caching")
            # Use the existing connector's method to fetch ROI hierarchy
            if hasattr(self.page_generator, 'connector') and self.page_generator.connector:
                hierarchy_data = self.page_generator.connector._get_roi_hierarchy()
            else:
                logger.debug("No connector available for fetching ROI hierarchy")
                return

            # Save to cache
            if hierarchy_data and self.cache_manager:
                success = self.cache_manager.save_roi_hierarchy(hierarchy_data)
                if success:
                    logger.info("✅ Saved ROI hierarchy to cache during generation - will speed up index creation")
                else:
                    logger.warning("Failed to save ROI hierarchy to cache")

        except Exception as e:
            logger.debug(f"Failed to cache ROI hierarchy during generation: {e}")

    def _clean_roi_name(self, roi_name: str) -> str:
        """Remove (R) and (L) suffixes from ROI names."""
        import re
        # Remove (R), (L), or (M) suffixes from ROI names
        cleaned = re.sub(r'\s*\([RLM]\)$', '', roi_name)
        return cleaned.strip()

    def _get_roi_hierarchy_parent(self, roi_name: str, connector=None) -> str:
        """Get the parent ROI of the given ROI from the hierarchy."""
        try:
            # Load ROI hierarchy from cache or fetch if needed
            hierarchy_data = None
            if self.cache_manager:
                hierarchy_data = self.cache_manager.load_roi_hierarchy()

            if not hierarchy_data and connector:
                # Fallback to fetching from database using provided connector
                hierarchy_data = connector._get_roi_hierarchy()
            elif not hierarchy_data and hasattr(self.page_generator, 'connector') and self.page_generator.connector:
                # Fallback to using page generator's connector
                hierarchy_data = self.page_generator.connector._get_roi_hierarchy()

            if not hierarchy_data:
                return ""

            # Clean the ROI name first (remove (R), (L), (M) suffixes)
            cleaned_roi = self._clean_roi_name(roi_name)

            # Search recursively for the ROI and its parent
            parent = self._find_roi_parent_recursive(cleaned_roi, hierarchy_data)
            return parent if parent else ""

        except Exception as e:
            logger.debug(f"Failed to get parent ROI for {roi_name}: {e}")
            return ""

    def load_persistent_columns_cache(self, cache_key: str) -> Optional[Tuple[list, Dict[str, set]]]:
        """
        Load persistent cache for all columns dataset query.

        Args:
            cache_key: Unique key for the cache entry

        Returns:
            Tuple of (all_columns, region_map) if cache is valid, None otherwise
        """
        try:
            # Create cache directory
            cache_dir = Path("output/.cache")
            cache_dir.mkdir(parents=True, exist_ok=True)

            # Use hash of cache key for filename to avoid filesystem issues
            cache_filename = hashlib.md5(cache_key.encode()).hexdigest() + "_columns.json"
            cache_file = cache_dir / cache_filename

            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    data = json.load(f)

                # Check cache age (expire after 24 hours)
                cache_age = time.time() - data.get('timestamp', 0)
                if cache_age < 86400:  # 24 hours
                    # Reconstruct the tuple from JSON
                    all_columns = data['all_columns']
                    region_map = {}
                    for region, coords_list in data['region_map'].items():
                        region_map[region] = set(tuple(coord) for coord in coords_list)

                    logger.info(f"Loaded {len(all_columns)} columns from persistent cache (age: {cache_age/3600:.1f}h)")
                    return (all_columns, region_map)
                else:
                    logger.info("Persistent columns cache expired, will refresh")
                    cache_file.unlink()

        except Exception as e:
            logger.warning(f"Failed to load persistent columns cache: {e}")

        return None

    def save_persistent_columns_cache(self, cache_key: str, all_columns: list, region_map: Dict[str, set]):
        """
        Save columns data to persistent cache.

        Args:
            cache_key: Unique key for the cache entry
            all_columns: List of column data
            region_map: Dictionary mapping regions to coordinate sets
        """
        try:
            # Create cache directory
            cache_dir = Path("output/.cache")
            cache_dir.mkdir(parents=True, exist_ok=True)

            # Use hash of cache key for filename to avoid filesystem issues
            cache_filename = hashlib.md5(cache_key.encode()).hexdigest() + "_columns.json"
            cache_file = cache_dir / cache_filename

            # Convert sets to lists for JSON serialization
            serializable_region_map = {}
            for region, coords_set in region_map.items():
                serializable_region_map[region] = list(coords_set)

            data = {
                'timestamp': time.time(),
                'all_columns': all_columns,
                'region_map': serializable_region_map
            }

            with open(cache_file, 'w') as f:
                json.dump(data, f)

            logger.info(f"Saved {len(all_columns)} columns to persistent cache")

        except Exception as e:
            logger.warning(f"Failed to save persistent columns cache: {e}")

    def get_columns_from_neuron_cache(self, neuron_type: str) -> Tuple[Optional[list], Optional[Dict[str, set]]]:
        """
        Extract column data from neuron type cache if available.

        Args:
            neuron_type: The neuron type to get cached column data for

        Returns:
            Tuple of (columns_data, region_columns_map) or (None, None) if not cached
        """
        try:
            if self.cache_manager is not None:
                cache_data = self.cache_manager.load_neuron_type_cache(neuron_type)
                if cache_data and cache_data.columns_data and cache_data.region_columns_map:
                    # Convert region_columns_map back to sets from lists
                    region_map = {}
                    for region, coords_list in cache_data.region_columns_map.items():
                        region_map[region] = set(tuple(coord) for coord in coords_list)

                    logger.debug(f"Retrieved column data from cache for {neuron_type}: {len(cache_data.columns_data)} columns")
                    return cache_data.columns_data, region_map
        except Exception as e:
            logger.debug(f"Failed to get column data from cache for {neuron_type}: {e}")

        return None, None

    def _find_roi_parent_recursive(self, roi_name: str, hierarchy: dict, parent_name: str = "") -> str:
        """Recursively search for ROI in hierarchy and return its parent."""
        for key, value in hierarchy.items():
            # Direct match
            if key == roi_name:
                return parent_name

            # Handle ROI naming variations:
            # - Remove side suffixes: "AOTU(L)*" -> "AOTU"
            # - Remove asterisks: "AOTU*" -> "AOTU"
            cleaned_key = key.replace('(L)', '').replace('(R)', '').replace('(M)', '').replace('*', '').strip()
            if cleaned_key == roi_name:
                return parent_name

            # Also check if the ROI name matches the beginning of the key
            if key.startswith(roi_name) and (len(key) == len(roi_name) or key[len(roi_name)] in '(*'):
                return parent_name

            # Recursive search
            if isinstance(value, dict):
                result = self._find_roi_parent_recursive(roi_name, value, key)
                if result:
                    return result
        return ""
