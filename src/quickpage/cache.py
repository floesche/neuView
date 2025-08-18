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

    @classmethod
    def from_neuron_collection(cls, neuron_collection, roi_summary: List[Dict[str, Any]] = None,
                               parent_roi: str = "", has_connectivity: bool = False) -> 'NeuronTypeCacheData':
        """Create cache data from a NeuronCollection object."""
        from .models import NeuronCollection

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
        if len(soma_sides_available) > 1:
            soma_sides_available.append("both")

        # Extract class/subclass/superclass from first neuron if available
        cell_class = None
        cell_subclass = None
        cell_superclass = None

        if neuron_collection.neurons:
            first_neuron = neuron_collection.neurons[0]
            cell_class = first_neuron.cell_class
            cell_subclass = first_neuron.cell_subclass
            cell_superclass = first_neuron.cell_superclass

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
            consensus_nt=None,
            celltype_predicted_nt=None,
            celltype_predicted_nt_confidence=None,
            celltype_total_nt_predictions=None,
            cell_class=cell_class,
            cell_subclass=cell_subclass,
            cell_superclass=cell_superclass
        )

    @classmethod
    def from_legacy_data(cls, neuron_type: str, legacy_data: Dict[str, Any],
                        roi_summary: List[Dict[str, Any]] = None, parent_roi: str = "",
                        has_connectivity: bool = False) -> 'NeuronTypeCacheData':
        """Create cache data from legacy neuron type data format."""
        # Extract counts from legacy format
        neurons_df = legacy_data.get('neurons', None)
        total_count = len(neurons_df) if neurons_df is not None and hasattr(neurons_df, '__len__') else 0

        # Calculate soma side counts from dataframe if available
        soma_side_counts = {"left": 0, "right": 0, "middle": 0, "unknown": 0}
        soma_sides_available = []

        if neurons_df is not None and hasattr(neurons_df, 'iterrows'):
            for _, row in neurons_df.iterrows():
                # Try both 'somaSide' (from database) and 'soma_side' (processed)
                soma_side = row.get('somaSide', row.get('soma_side', 'unknown'))
                if soma_side in ['L', 'left']:
                    soma_side_counts["left"] += 1
                elif soma_side in ['R', 'right']:
                    soma_side_counts["right"] += 1
                elif soma_side in ['M', 'middle']:
                    soma_side_counts["middle"] += 1
                else:
                    soma_side_counts["unknown"] += 1

        # Determine available soma sides
        if soma_side_counts["left"] > 0:
            soma_sides_available.append("left")
        if soma_side_counts["right"] > 0:
            soma_sides_available.append("right")
        if soma_side_counts["middle"] > 0:
            soma_sides_available.append("middle")
        if len(soma_sides_available) > 1:
            soma_sides_available.append("both")

        # Calculate basic synapse stats
        synapse_stats = {"avg_pre": 0.0, "avg_post": 0.0, "avg_total": 0.0,
                        "median_total": 0.0, "std_dev_total": 0.0}

        if neurons_df is not None and hasattr(neurons_df, 'iterrows') and total_count > 0:
            pre_counts = []
            post_counts = []

            for _, row in neurons_df.iterrows():
                pre_counts.append(row.get('pre', 0))
                post_counts.append(row.get('post', 0))

            if pre_counts:
                synapse_stats["avg_pre"] = sum(pre_counts) / len(pre_counts)
                synapse_stats["avg_post"] = sum(post_counts) / len(post_counts)

                total_counts = [pre + post for pre, post in zip(pre_counts, post_counts)]
                synapse_stats["avg_total"] = sum(total_counts) / len(total_counts)

                # Median
                sorted_totals = sorted(total_counts)
                n = len(sorted_totals)
                if n % 2 == 0:
                    synapse_stats["median_total"] = (sorted_totals[n//2 - 1] + sorted_totals[n//2]) / 2
                else:
                    synapse_stats["median_total"] = sorted_totals[n//2]

                # Standard deviation
                avg = synapse_stats["avg_total"]
                variance = sum((x - avg) ** 2 for x in total_counts) / len(total_counts)
                synapse_stats["std_dev_total"] = variance ** 0.5

        # Extract neurotransmitter data if available
        consensus_nt = None
        celltype_predicted_nt = None
        celltype_predicted_nt_confidence = None
        celltype_total_nt_predictions = None

        if neurons_df is not None and hasattr(neurons_df, 'iterrows') and total_count > 0:
            # Get first row for neurotransmitter data (should be consistent across type)
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

        # Extract class/subclass/superclass data if available
        cell_class = None
        cell_subclass = None
        cell_superclass = None

        if neurons_df is not None and hasattr(neurons_df, 'iterrows') and total_count > 0:
            # Get first row for class data (should be consistent across type)
            first_row = neurons_df.iloc[0]

            # Try _y suffixed columns first (from merged custom query), then fallback to original columns
            cell_class = None
            if 'cellClass_y' in neurons_df.columns:
                cell_class = first_row.get('cellClass_y')
            elif 'cellClass' in neurons_df.columns:
                cell_class = first_row.get('cellClass')

            cell_subclass = None
            if 'cellSubclass_y' in neurons_df.columns:
                cell_subclass = first_row.get('cellSubclass_y')
            elif 'cellSubclass' in neurons_df.columns:
                cell_subclass = first_row.get('cellSubclass')

            cell_superclass = None
            if 'cellSuperclass_y' in neurons_df.columns:
                cell_superclass = first_row.get('cellSuperclass_y')
            elif 'cellSuperclass' in neurons_df.columns:
                cell_superclass = first_row.get('cellSuperclass')

            # Clean up None values and NaN
            import pandas as pd
            if pd.isna(cell_class):
                cell_class = None
            if pd.isna(cell_subclass):
                cell_subclass = None
            if pd.isna(cell_superclass):
                cell_superclass = None

        return cls(
            neuron_type=neuron_type,
            total_count=int(total_count) if total_count is not None else 0,
            soma_side_counts=soma_side_counts,
            synapse_stats=synapse_stats,
            roi_summary=roi_summary or [],
            parent_roi=parent_roi,
            generation_timestamp=time.time(),
            soma_sides_available=soma_sides_available,
            has_connectivity=has_connectivity,
            metadata={},
            consensus_nt=str(consensus_nt) if consensus_nt is not None else None,
            celltype_predicted_nt=str(celltype_predicted_nt) if celltype_predicted_nt is not None else None,
            celltype_predicted_nt_confidence=float(celltype_predicted_nt_confidence) if celltype_predicted_nt_confidence is not None else None,
            celltype_total_nt_predictions=int(celltype_total_nt_predictions) if celltype_total_nt_predictions is not None else None,
            cell_class=str(cell_class) if cell_class is not None else None,
            cell_subclass=str(cell_subclass) if cell_subclass is not None else None,
            cell_superclass=str(cell_superclass) if cell_superclass is not None else None
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
        return cls(**data)


class NeuronTypeCacheManager:
    """Manager for persistent neuron type caches."""

    def __init__(self, cache_dir: str):
        """Initialize cache manager.

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

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
        """Get list of neuron types that have valid cache files.

        Returns:
            List of cached neuron type names
        """
        cached_types = []

        try:
            for cache_file in self.cache_dir.glob("*.json"):
                # Try to load and validate each cache file
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    cache_data = NeuronTypeCacheData.from_dict(data)

                    # Check if cache is not expired
                    cache_age = time.time() - cache_data.generation_timestamp
                    if cache_age <= self.cache_expiry_seconds:
                        cached_types.append(cache_data.neuron_type)

                except Exception as e:
                    logger.debug(f"Skipping invalid cache file {cache_file}: {e}")
                    continue

        except Exception as e:
            logger.warning(f"Failed to list cached neuron types: {e}")

        return sorted(cached_types)

    def get_all_cached_data(self) -> Dict[str, NeuronTypeCacheData]:
        """Get all valid cached neuron type data.

        Returns:
            Dictionary mapping neuron type names to cache data
        """
        cached_data = {}

        for neuron_type in self.list_cached_neuron_types():
            cache_data = self.load_neuron_type_cache(neuron_type)
            if cache_data:
                cached_data[neuron_type] = cache_data

        return cached_data

    def cleanup_expired_cache(self) -> int:
        """Remove expired cache files.

        Returns:
            Number of files removed
        """
        removed_count = 0

        try:
            for cache_file in self.cache_dir.glob("*.json"):
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
