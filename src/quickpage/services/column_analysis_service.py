"""
Column Analysis Service for QuickPage.

This service handles column-based ROI analysis that was previously part of the
PageGenerator class. It analyzes ROI data for column-based regions matching
patterns like (ME|LO|LOP)_[RL]_col_hex1_hex2 and provides comprehensive
column analysis including hexagonal grid generation.
"""

import logging
import re
import time
import numpy as np
import pandas as pd
from pandas.api.types import is_scalar
from typing import Dict, Any, List, Optional

from ..visualization.data_transfer_objects import (
    create_grid_generation_request,
    SomaSide,
)
from ..visualization.data_processing.data_adapter import DataAdapter

logger = logging.getLogger(__name__)


class ColumnAnalysisService:
    """Service for analyzing column-based ROI data and generating column summaries."""

    def __init__(self, page_generator):
        """Initialize column analysis service.

        Args:
            page_generator: PageGenerator instance for accessing hexagon generator and column methods
        """
        self.page_generator = page_generator
        self._column_analysis_cache = {}

    def analyze_column_roi_data(
        self,
        roi_counts_df: pd.DataFrame,
        neurons_df: pd.DataFrame,
        soma_side: str,
        neuron_type: str,
        connector,
        file_type: str = "svg",
        save_to_files: bool = True,
        hex_size: int = 6,
        spacing_factor: float = 1.1,
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze ROI data for column-based regions matching pattern (ME|LO|LOP)_[RL]_col_hex1_hex2.
        Returns additional table with mean synapses per column per neuron type.
        Now includes comprehensive hexagonal grids showing all possible columns.

        This method uses caching to avoid expensive repeated column analysis.

        Args:
            roi_counts_df: DataFrame with ROI count data
            neurons_df: DataFrame with neuron data
            soma_side: Side of soma (left/right)
            neuron_type: Type of neuron being analyzed
            connector: NeuPrint connector instance
            file_type: Output format for hexagonal grids ('svg' or 'png')
            save_to_files: If True, save files to disk; if False, embed content
            hex_size: Size of hexagons in visualization
            spacing_factor: Spacing factor between hexagons

        Returns:
            Dictionary containing column analysis results or None if no column data
        """
        start_time = time.time()

        # Create cache key for this specific analysis
        cache_key = f"{neuron_type}_{soma_side}_{file_type}_{save_to_files}_{hex_size}_{spacing_factor}"
        if cache_key in self._column_analysis_cache:
            logger.info(
                f"analyze_column_roi_data: returning cached result for {cache_key} in {time.time() - start_time:.3f}s"
            )
            return self._column_analysis_cache[cache_key]

        try:
            # Early exit for empty data
            if (
                roi_counts_df is None
                or roi_counts_df.empty
                or neurons_df is None
                or neurons_df.empty
            ):
                logger.info(
                    f"analyze_column_roi_data: early exit - no data for {neuron_type}_{soma_side} in {time.time() - start_time:.3f}s"
                )
                return None

            # Early exit if no neurons for this neuron type
            if len(neurons_df) == 0:
                logger.info(
                    f"analyze_column_roi_data: early exit - no neurons found for {neuron_type}_{soma_side} in {time.time() - start_time:.3f}s"
                )
                return None

            # Filter ROI data to include only neurons that belong to this specific soma side
            roi_counts_soma_filtered = self._filter_roi_data_by_soma_side(
                roi_counts_df, neurons_df
            )

            if roi_counts_soma_filtered.empty:
                logger.info(
                    f"analyze_column_roi_data: early exit - no ROI data for {neuron_type}_{soma_side} in {time.time() - start_time:.3f}s"
                )
                return None

            # Pattern to match column ROIs: (ME|LO|LOP)_[RL]_col_hex1_hex2
            column_pattern = r"^(ME|LO|LOP)_([RL])_col_([A-Za-z0-9]+)_([A-Za-z0-9]+)$"

            # Filter ROIs that match the column pattern
            column_rois = roi_counts_soma_filtered[
                roi_counts_soma_filtered["roi"].str.match(column_pattern, na=False)
            ].copy()

            if column_rois.empty:
                logger.info(
                    f"analyze_column_roi_data: early exit - no column ROIs for {neuron_type}_{soma_side} in {time.time() - start_time:.3f}s"
                )
                return None

            # Extract column information
            roi_info = self._extract_column_information(column_rois, column_pattern)

            if not roi_info:
                logger.info(
                    f"analyze_column_roi_data: early exit - no valid column info for {neuron_type}_{soma_side} in {time.time() - start_time:.3f}s"
                )
                return None

            # Analyze column data
            column_summary = self._analyze_column_data(roi_info, neuron_type, connector)

            # Generate summary statistics
            summary_stats = self._generate_column_summary_statistics(column_summary)

            # Get comprehensive column data for hexagon grids
            all_possible_columns, region_columns_map = (
                self.page_generator.database_query_service.get_all_possible_columns_from_dataset(
                    connector
                )
            )
            type_columns, type_region_map = (
                self.page_generator._get_columns_for_neuron_type(connector, neuron_type)
            )

            logger.info(
                "Using comprehensive dataset for gray/white logic, type-specific data for values"
            )

            # Generate comprehensive grids showing all possible columns
            comprehensive_region_grids = {}
            if all_possible_columns:
                # Get thresholds and min_max_data for grid generation
                col_layer_values, thresholds_all, min_max_data = (
                    self.page_generator.data_processing_service.get_column_layer_values(
                        neuron_type, connector
                    )
                )

                # Create eyemap generator with custom configuration if needed
                if hex_size != 6 or spacing_factor != 1.1:
                    from ..visualization.config_manager import ConfigurationManager

                    config = ConfigurationManager.create_for_generation(
                        hex_size=hex_size, spacing_factor=spacing_factor
                    )
                    # Use a temporary generator with custom config for this operation
                    from ..visualization import EyemapGenerator

                    generator = EyemapGenerator(config)
                else:
                    generator = self.page_generator.eyemap_generator

                # Convert dictionary input to structured ColumnData objects
                column_data = DataAdapter.normalize_input(column_summary)

                # Convert string soma_side to SomaSide enum
                soma_side_enum = (
                    SomaSide(soma_side) if isinstance(soma_side, str) else soma_side
                )

                # Create grid generation request
                grid_request = create_grid_generation_request(
                    column_data=column_data,
                    thresholds_all=thresholds_all,
                    all_possible_columns=all_possible_columns,
                    region_columns_map=region_columns_map,
                    neuron_type=neuron_type,
                    soma_side=soma_side_enum,
                    output_format=file_type,
                    save_to_files=save_to_files,
                    min_max_data=min_max_data,
                )

                # Generate grids using new interface
                result_obj = generator.generate_comprehensive_region_hexagonal_grids(
                    grid_request
                )
                comprehensive_region_grids = result_obj.region_grids

            result = {
                "columns": column_summary,
                "summary": summary_stats,
                "comprehensive_region_grids": comprehensive_region_grids,
                "all_possible_columns_count": len(all_possible_columns),
                "region_columns_counts": {
                    region: len(coords) for region, coords in region_columns_map.items()
                },
            }

            # Cache the result for future use
            self._column_analysis_cache[cache_key] = result

            # Also update the neuron type columns cache with full column data for CacheService
            self._update_neuron_type_columns_cache(
                neuron_type, column_summary, region_columns_map
            )

            logger.info(
                f"analyze_column_roi_data: cached result for {cache_key} in {time.time() - start_time:.3f}s"
            )
            return result

        except Exception as e:
            logger.warning(
                f"Error during column analysis for {neuron_type}_{soma_side}: {e}"
            )
            return None

    def _filter_roi_data_by_soma_side(
        self, roi_counts_df: pd.DataFrame, neurons_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Filter ROI data to include only neurons from specific soma side."""
        if "bodyId" in neurons_df.columns and "bodyId" in roi_counts_df.columns:
            soma_side_body_ids = list(neurons_df["bodyId"].values)
            return roi_counts_df[roi_counts_df["bodyId"].isin(soma_side_body_ids)]
        else:
            return roi_counts_df

    def _extract_column_information(
        self, column_rois: pd.DataFrame, column_pattern: str
    ) -> List[Dict[str, Any]]:
        """Extract column information from column ROIs."""
        roi_info = []

        for _, row in column_rois.iterrows():
            roi_name = str(row["roi"])
            match = re.match(column_pattern, roi_name)
            if match:
                region, side, coord1, coord2 = match.groups()

                # Try to parse coordinates as decimal first, then hex if that fails
                try:
                    row_dec = int(coord1)
                except ValueError:
                    try:
                        row_dec = int(coord1, 16)
                    except ValueError:
                        continue  # Skip invalid coordinates

                try:
                    col_dec = int(coord2)
                except ValueError:
                    try:
                        col_dec = int(coord2, 16)
                    except ValueError:
                        continue  # Skip invalid coordinates

                pre_val = row.get("pre", 0) if "pre" in row else 0
                post_val = row.get("post", 0) if "post" in row else 0
                total_val = row.get("total") if "total" in row else (pre_val + post_val)

                roi_info.append(
                    {
                        "roi": roi_name,
                        "bodyId": row["bodyId"],
                        "region": region,
                        "side": side,
                        "hex1": row_dec,
                        "hex2": col_dec,
                        "pre": pre_val,
                        "post": post_val,
                        "total": total_val,
                    }
                )

        return roi_info

    def _analyze_column_data(
        self, roi_info: List[Dict[str, Any]], neuron_type: str, connector
    ) -> List[Dict[str, Any]]:
        """Analyze column data and calculate statistics."""
        # Convert to DataFrame for easier analysis
        column_df = pd.DataFrame(roi_info)

        # Count neurons per column
        neurons_per_column = (
            column_df.groupby(["region", "side", "hex1", "hex2"])
            .agg({"bodyId": "nunique", "pre": "sum", "post": "sum", "total": "sum"})
            .reset_index()
        )

        # Calculate mean synapses per neuron for each column
        neurons_per_column["mean_pre_per_neuron"] = (
            neurons_per_column["pre"] / neurons_per_column["bodyId"]
        )
        neurons_per_column["mean_post_per_neuron"] = (
            neurons_per_column["post"] / neurons_per_column["bodyId"]
        )
        neurons_per_column["mean_total_per_neuron"] = (
            neurons_per_column["total"] / neurons_per_column["bodyId"]
        )

        # Sort by region, side, then by hex1 and hex2
        neurons_per_column = neurons_per_column.sort_values(
            ["region", "side", "hex1", "hex2"]
        )

        # Create coordinate mapping for display
        coord_map = {}
        for info in roi_info:
            key = (info["region"], info["side"], info["hex1"], info["hex2"])
            if key not in coord_map:
                coord_map[key] = (info["hex1"], info["hex2"])

        # Get synapse density and neuron count per column across layers
        col_layer_values, thresholds_all, min_max_data = (
            self.page_generator.data_processing_service.get_column_layer_values(
                neuron_type, connector
            )
        )

        # Merge col_layer_values into neurons_per_column
        neurons_per_column = pd.merge(
            neurons_per_column,
            col_layer_values,
            on=["hex1", "hex2", "region", "side"],
            how="left",
        )

        # Fill NaN values in synapse and neuron lists with empty lists
        obj_cols = neurons_per_column.select_dtypes(include="object").columns
        neurons_per_column[obj_cols] = neurons_per_column[obj_cols].map(
            lambda v: [] if (is_scalar(v) and pd.isna(v)) else v
        )

        # Convert to list of dictionaries for template
        column_summary = []
        for _, row in neurons_per_column.iterrows():
            key = (row["region"], row["side"], row["hex1"], row["hex2"])
            hex1, hex2 = coord_map.get(key, (row["hex1"], row["hex2"]))

            column_summary.append(
                {
                    "region": row["region"],
                    "side": row["side"],
                    "hex1": int(hex1),
                    "hex2": int(hex2),
                    "column_name": f"{row['region']}_{row['side']}_col_{hex1}_{hex2}",
                    "neuron_count": int(row["bodyId"]),
                    "total_pre": int(row["pre"]),
                    "total_post": int(row["post"]),
                    "total_synapses": int(
                        np.nan_to_num(
                            sum(row.get("synapses_list", []))
                            if isinstance(row.get("synapses_list", []), list)
                            and len(row.get("synapses_list", [])) > 0
                            else 0,
                            nan=0.0,
                        )
                    ),
                    "mean_pre_per_neuron": float(
                        round(float(row["mean_pre_per_neuron"]), 1)
                    ),
                    "mean_post_per_neuron": float(
                        round(float(row["mean_post_per_neuron"]), 1)
                    ),
                    "mean_total_per_neuron": float(
                        round(float(row["mean_total_per_neuron"]), 1)
                    ),
                    "layers": [
                        {
                            "layer_index": i + 1,
                            "synapse_count": int(row.get("synapses_list", [])[i])
                            if i < len(row.get("synapses_list", []))
                            else 0,
                            "neuron_count": int(row.get("neurons_list", [])[i])
                            if i < len(row.get("neurons_list", []))
                            else 0,
                            "value": float(row.get("synapses_list", [])[i])
                            if i < len(row.get("synapses_list", []))
                            else 0.0,
                        }
                        for i in range(
                            max(
                                len(row.get("synapses_list", []))
                                if isinstance(row.get("synapses_list", []), list)
                                else 0,
                                len(row.get("neurons_list", []))
                                if isinstance(row.get("neurons_list", []), list)
                                else 0,
                            )
                        )
                    ],
                }
            )

        return column_summary

    def _generate_column_summary_statistics(
        self, column_summary: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate summary statistics for column analysis."""
        total_columns = len(column_summary)
        total_neurons_with_columns = sum(col["neuron_count"] for col in column_summary)

        if total_columns > 0:
            avg_neurons_per_column = total_neurons_with_columns / total_columns
            avg_synapses_per_column = (
                float(sum(col["total_synapses"] for col in column_summary))
                / total_columns
            )

            # Group by region for region-specific stats
            region_stats = {}
            for col in column_summary:
                region = col["region"]
                if region not in region_stats:
                    region_stats[region] = {
                        "columns": 0,
                        "neurons": 0,
                        "synapses": 0,
                        "sides": set(),
                    }
                region_stats[region]["columns"] += 1
                region_stats[region]["neurons"] += col["neuron_count"]
                region_stats[region]["synapses"] += col["total_synapses"]
                region_stats[region]["sides"].add(col["side"])

            # Convert sides set to list for consistency
            for region in region_stats:
                region_stats[region]["sides"] = sorted(
                    list(region_stats[region]["sides"])
                )
                region_stats[region]["avg_neurons_per_column"] = (
                    float(region_stats[region]["neurons"])
                    / region_stats[region]["columns"]
                )
                region_stats[region]["avg_synapses_per_column"] = (
                    float(region_stats[region]["synapses"])
                    / region_stats[region]["columns"]
                )
        else:
            avg_neurons_per_column = 0
            avg_synapses_per_column = 0.0
            region_stats = {}

        return {
            "total_columns": total_columns,
            "total_neurons_with_columns": total_neurons_with_columns,
            "avg_neurons_per_column": float(avg_neurons_per_column),
            "avg_synapses_per_column": float(avg_synapses_per_column),
            "regions": region_stats,
        }

    def _update_neuron_type_columns_cache(
        self,
        neuron_type: str,
        column_summary: List[Dict[str, Any]],
        region_columns_map: Dict[str, List],
    ) -> None:
        """Update the neuron type columns cache with full column data for CacheService."""
        neuron_cache_key = f"columns_{neuron_type}"
        if not hasattr(self.page_generator, "_neuron_type_columns_cache"):
            self.page_generator._neuron_type_columns_cache = {}
        self.page_generator._neuron_type_columns_cache[neuron_cache_key] = (
            column_summary,
            region_columns_map,
        )

    def clear_cache(self) -> None:
        """Clear the column analysis cache."""
        self._column_analysis_cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the column analysis cache."""
        return {
            "cache_size": len(self._column_analysis_cache),
            "cache_keys": list(self._column_analysis_cache.keys()),
        }
