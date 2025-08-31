"""
Threshold service for handling threshold computations for visualizations.

This module provides utilities for computing thresholds used in hexagon grid
visualizations and other data analysis components.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)


class ThresholdService:
    """
    Handle threshold computations for visualizations.

    This service provides methods for computing thresholds at different
    aggregation levels for synapse counts and neuron counts, used primarily
    in hexagon grid visualizations.
    """

    def __init__(self):
        """Initialize the threshold service."""
        pass

    def compute_thresholds(self, df: pd.DataFrame, n_bins: int = 5) -> Dict[str, Any]:
        """
        Compute threshold lists for synapse and neuron counts at different aggregation levels.

        Parameters
        ----------
        df : pandas.DataFrame
            Input DataFrame with at least the following columns:
            - `"hex1"`, `"hex2"`: Column identifiers
            - `"layer"`: Layer index
            - `"region"`: Region name (e.g., `"ME"`, `"LO"`, `"LOP"`)
            - `"side"`: Side indicator (e.g., `"L"` or `"R"`)
            - `"total_synapses"`: Number of synapses
            - `"bodyId"`: Body identifier for neuron counting
        n_bins : int, optional
            Number of bins to divide the value ranges into. The returned threshold
            lists will each have `n_bins + 1` elements. Default is 5.

        Returns
        -------
        thresholds : dict
            A nested dictionary with the first level keyed by the metric
            ("total_synapses", "neuron_count"), then by scope ("all" or "layers"),
            and within "layers" by region ("ME", "LO", "LOP").

        Notes
        -----
        - Thresholds are computed using `layer_thresholds`,
        which ensures that:
            * Empty lists produce `[0.0, 0.0, ..., 0.0]`
            * Constant-value lists produce a flat threshold list
            * Otherwise thresholds are evenly spaced between min and max.
        """
        thresholds = {
            "total_synapses": {"all": None, "layers": {}},
            "neuron_count": {"all": None, "layers": {}},
        }

        # Guard clause for empty DataFrame
        if df.empty:
            logger.warning("Empty DataFrame provided to compute_thresholds")
            return thresholds

        # Check if required columns exist
        required_columns = ['hex1', 'hex2', 'side', 'region', 'total_synapses', 'bodyId']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.warning(f"Missing required columns in DataFrame: {missing_columns}")
            return thresholds

        try:
            # Across all layers - find the max per column across all regions.
            synapse_data = df.groupby(['hex1', 'hex2', 'side', 'region'])['total_synapses'].sum()
            thresholds["total_synapses"]["all"] = self.layer_thresholds(
                synapse_data,
                n_bins=n_bins
            )

            neuron_data = df.groupby(['hex1', 'hex2', 'side', 'region'])['bodyId'].nunique()
            thresholds["neuron_count"]["all"] = self.layer_thresholds(
                neuron_data,
                n_bins=n_bins
            )

            # Compute thresholds for each region
            for reg in ["ME", "LO", "LOP"]:
                sub = df[df['region'] == reg]

                if not sub.empty:
                    # Across layers - find the max per column/layer within regions
                    synapse_layer_data = sub.groupby(['hex1', 'hex2', 'side', 'layer'])["total_synapses"].sum()
                    thresholds["total_synapses"]["layers"][reg] = self.layer_thresholds(
                        synapse_layer_data,
                        n_bins=n_bins
                    )
                    neuron_layer_data = sub.groupby(['hex1', 'hex2', 'side', 'layer'])["bodyId"].nunique()
                    thresholds["neuron_count"]["layers"][reg] = self.layer_thresholds(
                        neuron_layer_data,
                        n_bins=n_bins
                    )
                else:
                    # Empty region - provide default thresholds
                    thresholds["total_synapses"]["layers"][reg] = [0.0] * (n_bins + 1)
                    thresholds["neuron_count"]["layers"][reg] = [0.0] * (n_bins + 1)

        except Exception as e:
            logger.error(f"Error computing thresholds: {e}")
            # Return empty thresholds on error
            return {
                "total_synapses": {"all": None, "layers": {}},
                "neuron_count": {"all": None, "layers": {}},
            }

        return thresholds

    def layer_thresholds(self, values: Any, n_bins: int = 5) -> List[float]:
        """
        Return n_bins+1 thresholds from min..max for a 1D series of numbers.

        Args:
            values: Pandas Series or DataFrame containing numeric values
            n_bins: Number of bins to create (result will have n_bins + 1 thresholds)

        Returns:
            List of threshold values

        Notes:
            - If values is empty -> [0,0,...,0].
            - If all values are equal -> list of that value repeated.
            - Otherwise -> evenly spaced thresholds between min and max.
        """
        # Handle both Series and DataFrame
        if hasattr(values, 'empty') and values.empty:
            return [0.0] * (n_bins + 1)

        try:
            # Convert to Series if it's a DataFrame
            if isinstance(values, pd.DataFrame):
                values = values.iloc[:, 0] if len(values.columns) > 0 else pd.Series()

            if values.empty:
                return [0.0] * (n_bins + 1)

            vmin = float(values.min())
            vmax = float(values.max())

            if vmax == vmin:
                return [vmin] * (n_bins + 1)

            return [vmin + (vmax - vmin) * (i / n_bins) for i in range(n_bins + 1)]

        except (TypeError, ValueError) as e:
            logger.warning(f"Error computing layer thresholds: {e}")
            return [0.0] * (n_bins + 1)

    def compute_percentile_thresholds(self, values: pd.Series, percentiles: List[float]) -> List[float]:
        """
        Compute thresholds based on percentiles.

        Args:
            values: Pandas Series containing numeric values
            percentiles: List of percentile values (0-100)

        Returns:
            List of threshold values corresponding to the percentiles
        """
        if values.empty:
            return [0.0] * len(percentiles)

        try:
            return [float(values.quantile(p / 100.0)) for p in percentiles]
        except (TypeError, ValueError) as e:
            logger.warning(f"Error computing percentile thresholds: {e}")
            return [0.0] * len(percentiles)

    def compute_adaptive_thresholds(self, values: Any, n_bins: int = 5,
                                   method: str = 'linear') -> List[float]:
        """
        Compute adaptive thresholds using different methods.

        Args:
            values: Pandas Series, DataFrame, or other data structure containing numeric values
            n_bins: Number of bins to create
            method: Threshold computation method ('linear', 'log', 'quantile')

        Returns:
            List of threshold values
        """
        if hasattr(values, 'empty') and values.empty:
            return [0.0] * (n_bins + 1)

        try:
            # Convert to Series if it's a DataFrame
            if isinstance(values, pd.DataFrame):
                values = values.iloc[:, 0] if len(values.columns) > 0 else pd.Series()

            if method == 'linear':
                return self.layer_thresholds(values, n_bins)

            elif method == 'log':
                # Log-scale thresholds for highly skewed data
                if hasattr(values, 'empty') and values.empty:
                    return [0.0] * (n_bins + 1)

                positive_values = values[values > 0]
                if hasattr(positive_values, 'empty') and positive_values.empty:
                    return [0.0] * (n_bins + 1)

                if hasattr(positive_values, 'apply'):
                    log_values = positive_values.apply(lambda x: float(np.log10(x)))
                else:
                    log_values = pd.Series([np.log10(float(x)) for x in positive_values if x > 0])
                log_thresholds = self.layer_thresholds(log_values, n_bins)
                return [10 ** t for t in log_thresholds]

            elif method == 'quantile':
                # Quantile-based thresholds
                percentiles = [i * (100 / n_bins) for i in range(n_bins + 1)]
                return self.compute_percentile_thresholds(values, percentiles)

            else:
                logger.warning(f"Unknown threshold method: {method}, using linear")
                return self.layer_thresholds(values, n_bins)

        except Exception as e:
            logger.error(f"Error computing adaptive thresholds: {e}")
            return [0.0] * (n_bins + 1)

    def validate_thresholds(self, thresholds: List[float]) -> bool:
        """
        Validate that thresholds are properly ordered and contain valid values.

        Args:
            thresholds: List of threshold values to validate

        Returns:
            True if thresholds are valid, False otherwise
        """
        if not thresholds:
            return False

        try:
            # Check that all values are numeric
            numeric_thresholds = [float(t) for t in thresholds]

            # Check that thresholds are in ascending order
            for i in range(1, len(numeric_thresholds)):
                if numeric_thresholds[i] < numeric_thresholds[i-1]:
                    return False

            return True

        except (TypeError, ValueError):
            return False

    def normalize_thresholds(self, thresholds: List[float],
                           target_min: float = 0.0, target_max: float = 1.0) -> List[float]:
        """
        Normalize thresholds to a target range.

        Args:
            thresholds: List of threshold values to normalize
            target_min: Target minimum value
            target_max: Target maximum value

        Returns:
            List of normalized threshold values
        """
        if not thresholds or len(thresholds) < 2:
            return thresholds

        try:
            current_min = min(thresholds)
            current_max = max(thresholds)

            if current_max == current_min:
                # All values are the same
                return [target_min] * len(thresholds)

            # Normalize to target range
            scale = (target_max - target_min) / (current_max - current_min)
            return [target_min + (t - current_min) * scale for t in thresholds]

        except Exception as e:
            logger.error(f"Error normalizing thresholds: {e}")
            return thresholds
