"""
Persistent cache system for neuron type information.

This module provides caching functionality to store neuron type data during
page generation and reuse it during index creation, avoiding expensive
database re-queries.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

from .models import NeuronTypeName, SomaSide

logger = logging.getLogger(__name__)


@dataclass
class NeuronTypeCacheData:
    """Data structure for cached neuron type information."""
    neuron_type: str
    total_count: int
    soma_side_counts: Dict[str, int]
    synapse_stats: Dict[str, float]
    roi_summary: List[Dict[str, Any]]
    parent_roi: str
    generation_timestamp: float
    soma_sides_available: List[str]
    has_connectivity: bool
    metadata: Dict[str, Any]
    consensus_nt: Optional[str] = None
    celltype_predicted_nt: Optional[str] = None
    celltype_predicted_nt_confidence: Optional[float] = None
    celltype_total_nt_predictions: Optional[int] = None
    cell_class: Optional[str] = None
    cell_subclass: Optional[str] = None
    cell_superclass: Optional[str] = None
    dimorphism: Optional[str] = None
    # Enhanced cache data for index creation
    body_ids: Optional[List[int]] = None
    upstream_partners: Optional[List[Dict[str, Any]]] = None
    downstream_partners: Optional[List[Dict[str, Any]]] = None
    neurotransmitter_distribution: Optional[Dict[str, int]] = None
    class_distribution: Optional[Dict[str, int]] = None
    subclass_distribution: Optional[Dict[str, int]] = None
    superclass_distribution: Optional[Dict[str, int]] = None
    # Column data for optic lobe neurons
    columns_data: Optional[List[Dict[str, Any]]] = None
    region_columns_map: Optional[Dict[str, List[tuple]]] = None
    connectivity_summary: Optional[Dict[str, Any]] = None
    # Meta information to avoid queries during index creation
    original_neuron_name: Optional[str] = None
    synonyms: Optional[str] = None
    flywire_types: Optional[str] = None

    @classmethod
    def from_neuron_collection(cls, neuron_collection, roi_summary: List[Dict[str, Any]] = None,
                               parent_roi: str = "", has_connectivity: bool = True,
                               connectivity_data: Optional[Dict[str, Any]] = None,
                               neuron_data_df: Optional[Any] = None,
                               columns_data: Optional[List[Dict[str, Any]]] = None,
                               region_columns_map: Optional[Dict[str, List[tuple]]] = None) -> 'NeuronTypeCacheData':
        """Create cache data from a NeuronCollection object with enhanced connectivity and distribution data."""
        from .models import NeuronCollection
        import pandas as pd

        if not isinstance(neuron_collection, NeuronCollection):
            raise ValueError("Expected NeuronCollection object")

        soma_side_counts = neuron_collection.get_soma_side_counts()
        synapse_stats = neuron_collection.get_synapse_statistics()

        # Determine available soma sides
        soma_sides_available = []
        if soma_side_counts.get("left", 0) > 0:
            soma_sides_available.append("left")
        if soma_side_counts.get("right", 0) > 0:
            soma_sides_available.append("right")
        if soma_side_counts.get("middle", 0) > 0:
            soma_sides_available.append("middle")

        # Add "combined" page if:
        # 1. Multiple assigned sides exist, OR
        # 2. Unknown sides exist alongside any assigned side, OR
        # 3. Only unknown sides exist
        unknown_count = soma_side_counts.get("unknown", 0)
        if (len(soma_sides_available) > 1 or
            (unknown_count > 0 and len(soma_sides_available) > 0) or
            (unknown_count > 0 and len(soma_sides_available) == 0)):
            soma_sides_available.append("combined")

        # Extract class/subclass/superclass from first neuron if available
        cell_class = None
        cell_subclass = None
        cell_superclass = None
        consensus_nt = None
        celltype_predicted_nt = None
        celltype_predicted_nt_confidence = None
        celltype_total_nt_predictions = None

        if neuron_collection.neurons:
            first_neuron = neuron_collection.neurons[0]
            cell_class = first_neuron.cell_class
            cell_subclass = first_neuron.cell_subclass
            cell_superclass = first_neuron.cell_superclass

        # Extract body IDs from neuron collection
        body_ids = [int(neuron.body_id) for neuron in neuron_collection.neurons]

        # Extract connectivity data if provided
        upstream_partners = None
        downstream_partners = None
        connectivity_summary = None
        if connectivity_data:
            upstream_partners = connectivity_data.get('upstream', [])
            downstream_partners = connectivity_data.get('downstream', [])
            connectivity_summary = {
                'upstream_count': len(upstream_partners),
                'downstream_count': len(downstream_partners),
                'total_upstream_weight': sum(p.get('weight', 0) for p in upstream_partners),
                'total_downstream_weight': sum(p.get('weight', 0) for p in downstream_partners),
                'regional_connections': connectivity_data.get('regional_connections', {}),
                'note': connectivity_data.get('note', '')
            }

        # Calculate distributions from neuron data if available
        neurotransmitter_distribution = None
        class_distribution = None
        subclass_distribution = None
        superclass_distribution = None
        dimorphism = None
        synonyms = None
        flywire_types = None

        if neuron_data_df is not None and hasattr(neuron_data_df, 'iterrows'):
            # Neurotransmitter distribution
            nt_counts = {}
            class_counts = {}
            subclass_counts = {}
            superclass_counts = {}

            for _, row in neuron_data_df.iterrows():
                # Count neurotransmitters
                consensus_nt_val = row.get('consensusNt_y') if 'consensusNt_y' in neuron_data_df.columns else None
                if pd.notna(consensus_nt_val):
                    nt_counts[consensus_nt_val] = nt_counts.get(consensus_nt_val, 0) + 1
                    if consensus_nt is None:  # Set from first valid value
                        consensus_nt = consensus_nt_val

                # Count cell classes
                class_val = row.get('cellClass') if 'cellClass' in neuron_data_df.columns else None
                if pd.notna(class_val):
                    class_counts[class_val] = class_counts.get(class_val, 0) + 1

                subclass_val = row.get('cellSubclass') if 'cellSubclass' in neuron_data_df.columns else None
                if pd.notna(subclass_val):
                    subclass_counts[subclass_val] = subclass_counts.get(subclass_val, 0) + 1

                superclass_val = row.get('cellSuperclass') if 'cellSuperclass' in neuron_data_df.columns else None
                if pd.notna(superclass_val):
                    superclass_counts[superclass_val] = superclass_counts.get(superclass_val, 0) + 1

                # Extract other neurotransmitter data from first row if not set
                if celltype_predicted_nt is None:
                    celltype_predicted_nt_val = row.get('celltypePredictedNt_y') if 'celltypePredictedNt_y' in neuron_data_df.columns else None
                    if pd.notna(celltype_predicted_nt_val):
                        celltype_predicted_nt = celltype_predicted_nt_val

                if celltype_predicted_nt_confidence is None:
                    confidence_val = row.get('celltypePredictedNtConfidence_y') if 'celltypePredictedNtConfidence_y' in neuron_data_df.columns else None
                    if pd.notna(confidence_val):
                        celltype_predicted_nt_confidence = confidence_val

                if celltype_total_nt_predictions is None:
                    total_val = row.get('celltypeTotalNtPredictions_y') if 'celltypeTotalNtPredictions_y' in neuron_data_df.columns else None
                    if pd.notna(total_val):
                        celltype_total_nt_predictions = total_val

                # Extract dimorphism from first row if not set
                if dimorphism is None:
                    dimorphism_val = row.get('dimorphism_y') if 'dimorphism_y' in neuron_data_df.columns else row.get('dimorphism')
                    if pd.notna(dimorphism_val):
                        dimorphism = dimorphism_val

                # Extract synonyms from first row if not set
                if synonyms is None:
                    synonyms_val = row.get('synonyms_y') if 'synonyms_y' in neuron_data_df.columns else row.get('synonyms')
                    if pd.notna(synonyms_val):
                        synonyms = synonyms_val

                # Extract flywire_types from first row if not set
                if flywire_types is None:
                    flywire_types_val = row.get('flywireType_y') if 'flywireType_y' in neuron_data_df.columns else row.get('flywireType')
                    if pd.notna(flywire_types_val):
                        flywire_types = flywire_types_val

            neurotransmitter_distribution = nt_counts if nt_counts else None
            class_distribution = class_counts if class_counts else None
            subclass_distribution = subclass_counts if subclass_counts else None
            superclass_distribution = superclass_counts if superclass_counts else None

        return cls(
            neuron_type=str(neuron_collection.type_name),
            total_count=neuron_collection.count,
            soma_side_counts=soma_side_counts,
            synapse_stats=synapse_stats,
            roi_summary=roi_summary or [],
            parent_roi=parent_roi,
            generation_timestamp=time.time(),
            soma_sides_available=soma_sides_available,
            has_connectivity=has_connectivity,
            metadata=neuron_collection.metadata.copy(),
            original_neuron_name=str(neuron_collection.type_name),
            consensus_nt=consensus_nt,
            celltype_predicted_nt=celltype_predicted_nt,
            celltype_predicted_nt_confidence=celltype_predicted_nt_confidence,
            celltype_total_nt_predictions=celltype_total_nt_predictions,
            cell_class=cell_class,
            cell_subclass=cell_subclass,
            cell_superclass=cell_superclass,
            dimorphism=dimorphism,
            body_ids=body_ids,
            upstream_partners=upstream_partners,
            downstream_partners=downstream_partners,
            neurotransmitter_distribution=neurotransmitter_distribution,
            class_distribution=class_distribution,
            subclass_distribution=subclass_distribution,
            superclass_distribution=superclass_distribution,
            columns_data=columns_data,
            region_columns_map=region_columns_map,
            connectivity_summary=connectivity_summary,
            synonyms=synonyms,
            flywire_types=flywire_types
        )



    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        import json
        import numpy as np

        def convert_numpy_types(obj):
            """Convert numpy types to native Python types for JSON serialization."""
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            return obj

        data = asdict(self)
        return convert_numpy_types(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NeuronTypeCacheData':
        """Create instance from dictionary."""
        # Create a copy to avoid modifying the original data
        migrated_data = data.copy()

        # Ensure all required fields have defaults if missing
        defaults = {
            'metadata': {},
            'soma_sides_available': [],
            'has_connectivity': True,
            'consensus_nt': None,
            'celltype_predicted_nt': None,
            'celltype_predicted_nt_confidence': None,
            'celltype_total_nt_predictions': None,
            'cell_class': None,
            'cell_subclass': None,
            'cell_superclass': None,
            'dimorphism': None,
            'body_ids': None,
            'upstream_partners': None,
            'downstream_partners': None,
            'neurotransmitter_distribution': None,
            'class_distribution': None,
            'subclass_distribution': None,
            'superclass_distribution': None,
            'columns_data': None,
            'region_columns_map': None,
            'connectivity_summary': None,
            'original_neuron_name': None,
            'synonyms': None,
            'flywire_types': None
        }

        for field, default_value in defaults.items():
            if field not in migrated_data:
                migrated_data[field] = default_value

        return cls(**migrated_data)


class LazyCacheDataDict:
    """Dictionary-like object that loads cache data on-demand."""

    def __init__(self, cache_manager: 'NeuronTypeCacheManager'):
        """Initialize with a cache manager."""
        self._cache_manager = cache_manager
        self._cache = {}  # In-memory cache of loaded data
        self._available_types = None  # Lazy-loaded list of available types

    def _get_available_types(self) -> List[str]:
        """Get list of available neuron types (cached)."""
        if self._available_types is None:
            self._available_types = self._cache_manager.list_cached_neuron_types()
        return self._available_types

    def get(self, neuron_type: str, default=None) -> Optional[NeuronTypeCacheData]:
        """Get cache data for a neuron type, loading if necessary."""
        if neuron_type in self._cache:
            return self._cache[neuron_type]

        # Load from disk
        cache_data = self._cache_manager.load_neuron_type_cache(neuron_type)
        if cache_data:
            self._cache[neuron_type] = cache_data
            return cache_data

        return default

    def __getitem__(self, neuron_type: str) -> NeuronTypeCacheData:
        """Get cache data for a neuron type, raising KeyError if not found."""
        result = self.get(neuron_type)
        if result is None:
            raise KeyError(f"No cache data found for neuron type: {neuron_type}")
        return result

    def __contains__(self, neuron_type: str) -> bool:
        """Check if neuron type has cache data available."""
        if neuron_type in self._cache:
            return True
        return self._cache_manager.has_cached_data(neuron_type)

    def keys(self):
        """Get iterator over available neuron type names."""
        return iter(self._get_available_types())

    def values(self):
        """Get iterator over all cache data values (loads all files)."""
        for neuron_type in self._get_available_types():
            yield self.get(neuron_type)

    def items(self):
        """Get iterator over (neuron_type, cache_data) pairs (loads all files)."""
        for neuron_type in self._get_available_types():
            cache_data = self.get(neuron_type)
            if cache_data:
                yield neuron_type, cache_data

    def __len__(self) -> int:
        """Get number of available neuron types."""
        return len(self._get_available_types())

    def __iter__(self):
        """Iterate over available neuron type names."""
        return iter(self._get_available_types())


class NeuronTypeCacheManager:
    """Manager for neuron type cache operations."""

    def __init__(self, cache_dir: str):
        """Initialize cache manager.

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._roi_hierarchy_cache_path = self.cache_dir / "roi_hierarchy.json"
        logger.debug(f"Initialized cache manager with directory: {self.cache_dir}")

        # Cache expiry time (24 hours)
        self.cache_expiry_seconds = 24 * 3600

    def _get_cache_file_path(self, neuron_type: str) -> Path:
        """Get cache file path for a neuron type."""
        # Sanitize neuron type name for filename
        safe_name = "".join(c for c in neuron_type if c.isalnum() or c in "._-")
        return self.cache_dir / f"{safe_name}.json"

    def save_neuron_type_cache(self, cache_data: NeuronTypeCacheData) -> bool:
        """Save neuron type cache data to disk.

        Args:
            cache_data: Cache data to save

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            cache_file = self._get_cache_file_path(cache_data.neuron_type)

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data.to_dict(), f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved cache for neuron type {cache_data.neuron_type} to {cache_file}")
            return True

        except Exception as e:
            logger.warning(f"Failed to save cache for {cache_data.neuron_type}: {e}")
            return False

    def save_roi_hierarchy(self, hierarchy_data: dict) -> bool:
        """Save ROI hierarchy data to persistent cache.

        Args:
            hierarchy_data: ROI hierarchy dictionary

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            import time

            cache_data = {
                'hierarchy': hierarchy_data,
                'timestamp': time.time(),
                'cache_version': '1.0'
            }

            with open(self._roi_hierarchy_cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved ROI hierarchy to cache: {self._roi_hierarchy_cache_path}")
            return True

        except Exception as e:
            logger.warning(f"Failed to save ROI hierarchy to cache: {e}")
            return False

    def load_roi_hierarchy(self) -> Optional[dict]:
        """Load ROI hierarchy data from persistent cache.

        Returns:
            ROI hierarchy dictionary if available and valid, None otherwise
        """
        try:
            if not self._roi_hierarchy_cache_path.exists():
                return None

            with open(self._roi_hierarchy_cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # Check cache validity (24 hours)
            if 'timestamp' in cache_data:
                import time
                cache_age = time.time() - cache_data['timestamp']
                if cache_age > self.cache_expiry_seconds:
                    logger.debug(f"ROI hierarchy cache expired (age: {cache_age:.1f}s)")
                    return None

            hierarchy = cache_data.get('hierarchy')
            if hierarchy:
                logger.debug(f"Loaded ROI hierarchy from cache: {self._roi_hierarchy_cache_path}")
                return hierarchy

        except Exception as e:
            logger.debug(f"Failed to load ROI hierarchy from cache: {e}")

        return None

    def load_neuron_type_cache(self, neuron_type: str) -> Optional[NeuronTypeCacheData]:
        """Load neuron type cache data from disk.

        Args:
            neuron_type: Name of neuron type to load

        Returns:
            Cache data if found and valid, None otherwise
        """
        try:
            cache_file = self._get_cache_file_path(neuron_type)

            if not cache_file.exists():
                return None

            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            cache_data = NeuronTypeCacheData.from_dict(data)

            # Check if cache is expired
            cache_age = time.time() - cache_data.generation_timestamp
            if cache_age > self.cache_expiry_seconds:
                logger.debug(f"Cache for {neuron_type} is expired ({cache_age:.1f}s old)")
                return None

            logger.debug(f"Loaded cache for neuron type {neuron_type} from {cache_file}")
            return cache_data

        except Exception as e:
            logger.warning(f"Failed to load cache for {neuron_type}: {e}")
            return None

    def invalidate_neuron_type_cache(self, neuron_type: str) -> bool:
        """Remove cache file for a neuron type.

        Args:
            neuron_type: Name of neuron type to invalidate

        Returns:
            True if removed successfully, False otherwise
        """
        try:
            cache_file = self._get_cache_file_path(neuron_type)
            if cache_file.exists():
                cache_file.unlink()
                logger.debug(f"Invalidated cache for neuron type {neuron_type}")
                return True
            return False

        except Exception as e:
            logger.warning(f"Failed to invalidate cache for {neuron_type}: {e}")
            return False

    def list_cached_neuron_types(self) -> List[str]:
        """Get list of neuron types that have valid cache files (lazy - no file loading).

        Returns:
            List of cached neuron type names
        """
        cached_types = []

        try:
            for cache_file in self.cache_dir.glob("*.json"):
                # Skip ROI hierarchy cache file - it's not a neuron type cache
                if cache_file.name == "roi_hierarchy.json":
                    continue

                # Skip cache manifest file - it's not a neuron type cache
                if cache_file.name == "manifest.json":
                    continue

                # Skip auxiliary cache files (columns, etc.) - they're not neuron type caches
                if "_columns.json" in cache_file.name:
                    continue

                # Extract neuron type from filename and verify file is readable
                neuron_type = cache_file.stem
                if neuron_type and cache_file.exists() and cache_file.stat().st_size > 0:
                    # Quick validation - check if it's a JSON file with basic structure
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            # Just peek at the first few chars to see if it looks like JSON
                            first_char = f.read(1)
                            if first_char == '{':
                                cached_types.append(neuron_type)
                    except Exception:
                        # Skip files that can't be read
                        pass

        except Exception as e:
            logger.warning(f"Failed to list cached neuron types: {e}")

        return sorted(cached_types)

    def get_all_cached_data(self) -> Dict[str, NeuronTypeCacheData]:
        """Get all valid cached neuron type data.

        WARNING: This method loads ALL cache files at once. Consider using
        get_cached_data_lazy() or load_neuron_type_cache() for individual types.

        Returns:
            Dictionary mapping neuron type names to cache data
        """
        cached_data = {}

        for neuron_type in self.list_cached_neuron_types():
            cache_data = self.load_neuron_type_cache(neuron_type)
            if cache_data:
                cached_data[neuron_type] = cache_data

        return cached_data

    def get_cached_data_lazy(self) -> 'LazyCacheDataDict':
        """Get a lazy-loading dictionary for cached neuron type data.

        Returns a dictionary-like object that only loads cache files when accessed.

        Returns:
            LazyCacheDataDict that loads data on-demand
        """
        return LazyCacheDataDict(self)

    def has_cached_data(self, neuron_type: str) -> bool:
        """Check if cache data exists for a neuron type without loading it.

        Args:
            neuron_type: Name of neuron type to check

        Returns:
            True if cache file exists, False otherwise
        """
        cache_file = self._get_cache_file_path(neuron_type)
        return cache_file.exists()

    def cleanup_expired_cache(self) -> int:
        """Remove expired cache files.

        Returns:
            Number of files removed
        """
        removed_count = 0

        try:
            for cache_file in self.cache_dir.glob("*.json"):
                # Skip ROI hierarchy cache file - it has its own expiry logic
                if cache_file.name == "roi_hierarchy.json":
                    continue

                # Skip cache manifest file - it's not a neuron type cache
                if cache_file.name == "manifest.json":
                    continue

                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    cache_data = NeuronTypeCacheData.from_dict(data)
                    cache_age = time.time() - cache_data.generation_timestamp

                    if cache_age > self.cache_expiry_seconds:
                        cache_file.unlink()
                        removed_count += 1
                        logger.debug(f"Removed expired cache file {cache_file}")

                except Exception as e:
                    # If we can't parse the file, it's probably corrupted, remove it
                    logger.debug(f"Removing corrupted cache file {cache_file}: {e}")
                    cache_file.unlink()
                    removed_count += 1

        except Exception as e:
            logger.warning(f"Failed to cleanup expired cache: {e}")

        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} expired/corrupted cache files")

        return removed_count

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            total_files = len(cache_files)
            valid_files = 0
            expired_files = 0
            corrupted_files = 0
            total_size = 0

            for cache_file in cache_files:
                # Skip ROI hierarchy cache file - it has its own logic
                if cache_file.name == "roi_hierarchy.json":
                    continue

                # Skip cache manifest file - it's not a neuron type cache
                if cache_file.name == "manifest.json":
                    continue

                try:
                    total_size += cache_file.stat().st_size

                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    cache_data = NeuronTypeCacheData.from_dict(data)
                    cache_age = time.time() - cache_data.generation_timestamp

                    if cache_age <= self.cache_expiry_seconds:
                        valid_files += 1
                    else:
                        expired_files += 1

                except Exception:
                    corrupted_files += 1

            return {
                'cache_dir': str(self.cache_dir),
                'total_files': total_files,
                'valid_files': valid_files,
                'expired_files': expired_files,
                'corrupted_files': corrupted_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }

        except Exception as e:
            logger.warning(f"Failed to get cache stats: {e}")
            return {
                'cache_dir': str(self.cache_dir),
                'error': str(e)
            }


def create_cache_manager(output_dir: str) -> NeuronTypeCacheManager:
    """Create a cache manager for the given output directory.

    Args:
        output_dir: Output directory where cache should be stored

    Returns:
        Configured cache manager instance
    """
    cache_dir = Path(output_dir) / ".cache"
    return NeuronTypeCacheManager(str(cache_dir))
