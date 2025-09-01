"""
Hexagon grid generator for visualizing column data.

This module provides hexagon grid generation functionality supporting SVG
and PNG output formats using Cairo for enhanced visualization capabilities.
"""

import math
import logging
import os
from pathlib import Path
from typing import List, Dict, Optional
from jinja2 import Environment, FileSystemLoader

from .color import ColorPalette, ColorMapper
from .coordinate_system import EyemapCoordinateSystem
from .data_processing import DataProcessor
from .data_processing.data_structures import (
    MetricType, SomaSide, ProcessingConfig, ColumnStatus
)
from .rendering import RenderingManager, RenderingConfig, OutputFormat
from .data_transfer_objects import (
    GridGenerationRequest, SingleRegionGridRequest, RenderingRequest,
    GeneratorConfiguration, TooltipGenerationRequest, GridGenerationResult,
    create_grid_generation_request, create_rendering_request, create_single_region_request
)

logger = logging.getLogger(__name__)


class EyemapGenerator:
    """
    Generate hexagonal grid visualizations for column data.

    Supports SVG and PNG output formats with consistent styling and
    color mapping across different metrics and regions.
    """

    def __init__(self, hex_size: int = 6, spacing_factor: float = 1.1, output_dir: Optional[Path] = None, eyemaps_dir: Optional[Path] = None):
        """
        Initialize the eyemap generator.

        Args:
            hex_size: Size of individual hexagons
            spacing_factor: Spacing between hexagons
            output_dir: Directory to save SVG files (optional)
            eyemaps_dir: Directory to save eyemap images (optional, defaults to output_dir/eyemaps)
        """
        self.hex_size = hex_size
        self.spacing_factor = spacing_factor
        self.output_dir = output_dir
        self.eyemaps_dir = eyemaps_dir if eyemaps_dir is not None else (output_dir / 'eyemaps' if output_dir else None)
        self.embed_mode = False

        # Initialize color management components
        self.color_palette = ColorPalette()
        self.color_mapper = ColorMapper(self.color_palette)

        # Initialize coordinate system components
        self.coordinate_system = EyemapCoordinateSystem(hex_size, spacing_factor, margin=10)

        # Initialize data processing components
        self.data_processor = DataProcessor()

        # Initialize rendering system components
        self.rendering_config = RenderingConfig(
            hex_size=hex_size,
            spacing_factor=spacing_factor,
            output_dir=output_dir,
            eyemaps_dir=self.eyemaps_dir,
            margin=10
        )
        self.rendering_manager = RenderingManager(self.rendering_config, self.color_mapper)



    def generate_comprehensive_region_hexagonal_grids(self, request: GridGenerationRequest) -> GridGenerationResult:
        """
        Generate comprehensive hexagonal grid visualizations showing all possible columns.

        Args:
            request: GridGenerationRequest containing all generation parameters

        Returns:
            GridGenerationResult with generation results and metadata
        """
        import time
        start_time = time.time()

        # Set embed mode based on save_to_files parameter
        self.embed_mode = not request.save_to_files

        if not request.all_possible_columns:
            return GridGenerationResult(
                region_grids={},
                processing_time=0,
                success=False,
                error_message="No columns provided"
            )

        region_grids = {}
        warnings = []

        try:
            # Organize data using data processor
            data_maps = self.data_processor.column_data_manager.organize_data_by_side(
                request.column_summary, request.soma_side
            )

            # Generate grids for each region and side
            region_order = ['ME', 'LO', 'LOP']
            for region in region_order:
                for side, data_map in data_maps.items():
                    # Use side-specific region columns for accurate "not available" determination
                    region_side_key = f"{region}_{side}"
                    region_column_coords = request.region_columns_map.get(region_side_key, set())
                    # Determine if mirroring should be applied:
                    # - For soma_side='left': mirror everything
                    # - For soma_side='combined': mirror only L grids to match dedicated left pages
                    # - For soma_side='right': don't mirror anything
                    if request.soma_side.lower() == 'left':
                        mirror_side = 'left'  # Mirror everything
                    elif request.soma_side.lower() == 'combined' and side == 'L':
                        mirror_side = 'left'  # Mirror only L grids
                    else:
                        mirror_side = 'right'  # No mirroring

                    # Get other regions' column coordinates for the same soma side
                    other_regions_coords = self.data_processor._get_other_regions_coords(
                        request.region_columns_map, region, side
                    )

                    # Filter all_possible_columns to only include columns relevant for this soma side
                    side_filtered_columns = self.data_processor._filter_columns_for_side(
                        request.all_possible_columns, request.region_columns_map, region, side
                    )

                    # Create requests for single region grid generation
                    synapse_request = create_single_region_request(
                        side_filtered_columns, region_column_coords, data_map,
                        'synapse_density', region,
                        thresholds=request.thresholds_all['total_synapses'],
                        neuron_type=request.neuron_type,
                        soma_side=mirror_side,
                        output_format=request.output_format,
                        other_regions_coords=other_regions_coords,
                        min_max_data=request.min_max_data
                    )

                    cell_request = create_single_region_request(
                        side_filtered_columns, region_column_coords, data_map,
                        'cell_count', region,
                        thresholds=request.thresholds_all['neuron_count'],
                        neuron_type=request.neuron_type,
                        soma_side=mirror_side,
                        output_format=request.output_format,
                        other_regions_coords=other_regions_coords,
                        min_max_data=request.min_max_data
                    )

                    synapse_content = self.generate_comprehensive_single_region_grid(synapse_request)
                    cell_content = self.generate_comprehensive_single_region_grid(cell_request)

                    region_side_key = f"{region}_{side}"

                    if request.save_to_files and self.output_dir and not self.embed_mode:
                    # Save files and return paths
                        # Save files using rendering manager directly
                        format_enum = OutputFormat.SVG if request.output_format == 'svg' else OutputFormat.PNG

                        if request.output_format in ['svg', 'png']:
                            renderer = self.rendering_manager._get_renderer(format_enum)
                            synapse_path = renderer.save_to_file(synapse_content, f"{region}_{request.neuron_type}_{side}_synapse_density")
                            cell_path = renderer.save_to_file(cell_content, f"{region}_{request.neuron_type}_{side}_cell_count")
                        else:
                            raise ValueError(f"Unsupported output format: {request.output_format}")

                        region_grids[region_side_key] = {
                            'synapse_density': synapse_path,
                            'cell_count': cell_path
                        }
                    else:
                        # Return content directly for embedding
                        region_grids[region_side_key] = {
                            'synapse_density': synapse_content,
                            'cell_count': cell_content
                        }

            processing_time = time.time() - start_time
            return GridGenerationResult(
                region_grids=region_grids,
                processing_time=processing_time,
                success=True,
                warnings=warnings
            )

        except Exception as e:
            processing_time = time.time() - start_time
            return GridGenerationResult(
                region_grids={},
                processing_time=processing_time,
                success=False,
                error_message=str(e)
            )


    def generate_comprehensive_single_region_grid(self, request: SingleRegionGridRequest) -> str:
        """
        Generate comprehensive hexagonal grid showing all possible columns for a single region.

        Args:
            request: SingleRegionGridRequest containing all generation parameters

        Returns:
            Generated visualization content as string
        """
        if not request.all_possible_columns:
            return ""

        # Calculate coordinate ranges from all possible columns
        min_hex1 = min(col['hex1'] for col in request.all_possible_columns)
        min_hex2 = min(col['hex2'] for col in request.all_possible_columns)

        # Extract the min and max value per column across regions and hemispheres.
        if request.thresholds and 'all' in request.thresholds and request.thresholds['all']:
            global_min = request.thresholds['all'][0]
            global_max = request.thresholds['all'][-1]
        else:
            global_min = 0
            global_max = 1

        # Set up title and range
        if request.metric_type == 'synapse_density':
            title = f"{request.region_name} Synapses (All Columns)"
            subtitle = f"{request.neuron_type} ({request.soma_side.upper()[:1] if request.soma_side else ''})"
            min_value = global_min if global_min is not None else 0
            max_value = global_max if global_max is not None else 1
        else:  # cell_count
            title = f"{request.region_name} Cell Count (All Columns)"
            subtitle = f"{request.neuron_type} ({request.soma_side.upper()[:1] if request.soma_side else ''})"
            min_value = global_min if global_min is not None else 0
            max_value = global_max if global_max is not None else 1

        value_range = max_value - min_value if max_value > min_value else 1

        # Get colors for different states from palette
        state_colors = self.color_palette.get_state_colors()

        # Convert metric type to enum
        if request.metric_type == 'synapse_density':
            metric_enum = MetricType.SYNAPSE_DENSITY
        else:
            metric_enum = MetricType.CELL_COUNT

        # Convert soma_side to enum
        if request.soma_side in ['left', 'L']:
            soma_enum = SomaSide.LEFT
        elif request.soma_side in ['right', 'R']:
            soma_enum = SomaSide.RIGHT
        else:
            soma_enum = SomaSide.COMBINED

        # Create processing configuration
        config = ProcessingConfig(
            metric_type=metric_enum,
            soma_side=soma_enum,
            region_name=request.region_name,
            neuron_type=request.neuron_type,
            output_format=request.output_format
        )

        # Process the data using the data processor
        processing_result = self.data_processor._process_side_data(
            request.all_possible_columns,
            request.region_column_coords,
            request.data_map,
            config,
            request.other_regions_coords or set(),
            request.thresholds,
            request.min_max_data,
            request.soma_side
        )

        if not processing_result.is_successful:
            logger.warning(f"Data processing failed: {processing_result.validation_result.errors}")
            return ""

        # Convert processed columns to pixel coordinates
        columns_with_coords = self.coordinate_system.convert_column_coordinates(
            request.all_possible_columns, mirror_side=request.soma_side
        )

        # Create coordinate mapping
        coord_to_pixel = {
            (col['hex1'], col['hex2']): {'x': col['x'], 'y': col['y']}
            for col in columns_with_coords
        }

        hexagons = []
        for processed_col in processing_result.processed_columns:
            coord_tuple = (processed_col.hex1, processed_col.hex2)

            if coord_tuple not in coord_to_pixel:
                continue

            pixel_coords = coord_to_pixel[coord_tuple]

            # Get raw data for layer colors
            if processed_col.status == ColumnStatus.HAS_DATA:
                data_key = (request.region_name, processed_col.hex1, processed_col.hex2)
                data_col = request.data_map.get(data_key)

                if data_col and request.metric_type == 'synapse_density':
                    layer_colors = data_col.get('synapses_list_raw', processed_col.layer_colors)
                elif data_col and request.metric_type == 'cell_count':
                    layer_colors = data_col.get('neurons_list', processed_col.layer_colors)
                else:
                    layer_colors = processed_col.layer_colors
            else:
                layer_colors = []

            # Map color using color mapper
            if processed_col.status == ColumnStatus.HAS_DATA:
                color = self.color_mapper.map_value_to_color(processed_col.value, min_value, max_value)
            elif processed_col.status == ColumnStatus.NO_DATA:
                color = self.color_palette.white
            elif processed_col.status == ColumnStatus.NOT_IN_REGION:
                color = self.color_palette.dark_gray
            else:
                continue

            hexagon_data = {
                'x': pixel_coords['x'],
                'y': pixel_coords['y'],
                'value': processed_col.value,
                'layer_values': processed_col.layer_values,
                'layer_colors': layer_colors,
                'color': color,
                'region': request.region_name,
                'side': 'combined',  # Since we're showing all possible columns
                'hex1': processed_col.hex1,
                'hex2': processed_col.hex2,
                'neuron_count': processed_col.value if request.metric_type == 'cell_count' else 0,
                'column_name': f"{request.region_name}_col_{processed_col.hex1}_{processed_col.hex2}",
                'synapse_value': processed_col.value if request.metric_type == 'synapse_density' else 0,
                'status': processed_col.status.value,
                'metric_type': request.metric_type
            }
            hexagons.append(hexagon_data)

        # Add tooltips to hexagons before rendering
        tooltip_request = TooltipGenerationRequest(
            hexagons=hexagons,
            soma_side=request.soma_side or 'right',
            metric_type=request.metric_type
        )
        hexagons_with_tooltips = self._add_tooltips_to_hexagons(tooltip_request)

        # Create rendering request
        rendering_request = create_rendering_request(
            hexagons=hexagons_with_tooltips,
            min_val=min_value,
            max_val=max_value,
            thresholds=request.thresholds or {},
            title=title,
            subtitle=subtitle,
            metric_type=request.metric_type,
            soma_side=request.soma_side or 'right',
            output_format=request.output_format,
            save_to_file=False
        )

        # Use rendering manager to generate visualization
        return self.rendering_manager.render_comprehensive_grid(
            hexagons=rendering_request.hexagons,
            min_val=rendering_request.min_val,
            max_val=rendering_request.max_val,
            thresholds=rendering_request.thresholds,
            title=rendering_request.title,
            subtitle=rendering_request.subtitle,
            metric_type=rendering_request.metric_type,
            soma_side=rendering_request.soma_side,
            output_format=OutputFormat.PNG if rendering_request.output_format.lower() == 'png' else OutputFormat.SVG,
            save_to_file=rendering_request.save_to_file
        )


    def value_to_color(self, normalized_value: float) -> str:
        """
        Convert normalized value (0-1) to one of 5 distinct colors from lightest to darkest red.

        Args:
            normalized_value: Value between 0 and 1

        Returns:
            Hex color string
        """
        return self.color_palette.value_to_color(normalized_value)




    def _add_tooltips_to_hexagons(self, request: TooltipGenerationRequest):
        """
        Add 'tooltip' and 'tooltip_layers' to each hexagon dict.

        - 'tooltip' is the summary tooltip based on status and metric_type.
        - 'tooltip_layers' is a list of per-layer tooltips derived from 'layer_values',
        with ROI strings that include 'layer(<idx>)' where idx is 1-based.

        Args:
            request: TooltipGenerationRequest containing hexagons and parameters

        Returns:
            A new list of dicts, each with 'tooltip' and 'tooltip_layers' added.
        """
        lbl_stat_for_zero = "Synapse count" if request.metric_type == 'synapse_density' else "Cell count"

        processed_hexagons = []
        for hex_data in request.hexagons:
            status = hex_data.get('status', 'has_data')
            region = hex_data.get('region', '')
            hex1 = hex_data.get('hex1', '')
            hex2 = hex_data.get('hex2', '')
            value = hex_data.get('value', 0)
            layer_values = hex_data.get('layer_values') or []  # expect list[int]; handle None

            # --- Main (summary) tooltip, like your original ---
            if status == 'not_in_region':
                tooltip = (
                    f"Column: {hex1}, {hex2}\n"
                    f"Column not identified in {region} ({request.soma_side})"
                )
            elif status == 'no_data':
                tooltip = (
                    f"Column: {hex1}, {hex2}\n"
                    f"{lbl_stat_for_zero}: 0\n"
                    f"ROI: {region} ({request.soma_side})"
                )
            else:  # has_data
                tooltip = (
                    f"Column: {hex1}, {hex2}\n"
                    f"{lbl_stat_for_zero}: {int(value)}\n"
                    f"ROI: {region} ({request.soma_side})"
                )

            # --- Per-layer tooltips ---
            tooltip_layers = []
            # Use 1-based index to match layer numbering
            for i, v in enumerate(layer_values, start=1):
                if status == 'not_in_region':
                    layer_tip = (
                        f"Column: {hex1}, {hex2}\n"
                        f"Column not identified in {region} ({request.soma_side}) layer({i})"
                    )
                elif status == 'no_data':
                    # even if layer_values are present, 'no_data' implies 0 for display
                    layer_tip = (
                        f"0\n"
                        f"ROI: {region}{i}"
                    )
                else:  # has_data
                    # Choose label based on metric_type and take value from layer_values
                    layer_tip = (
                        f"{int(v)}\n"
                        f"ROI: {region}{i}"
                    )
                tooltip_layers.append(layer_tip)

            processed_hex = hex_data.copy()
            processed_hex['tooltip'] = tooltip
            processed_hex['tooltip_layers'] = tooltip_layers
            processed_hexagons.append(processed_hex)

        return processed_hexagons

    def update_configuration(self, hex_size: int = None, spacing_factor: float = None):
        """
        Update hexagon grid generator configuration in-place.

        Args:
            hex_size: New hexagon size (optional)
            spacing_factor: New spacing factor (optional)
        """
        # Update instance variables
        if hex_size is not None:
            self.hex_size = hex_size
        if spacing_factor is not None:
            self.spacing_factor = spacing_factor

        # Update coordinate system in-place
        self.coordinate_system.update_configuration(
            hex_size=hex_size,
            spacing_factor=spacing_factor,
            margin=10
        )

        # Update rendering config in-place
        config_updates = {}
        if hex_size is not None:
            config_updates['hex_size'] = hex_size
        if spacing_factor is not None:
            config_updates['spacing_factor'] = spacing_factor

        if config_updates:
            # Update rendering manager configuration in-place
            self.rendering_manager.update_config(**config_updates)

            # Update the local rendering config reference
            self.rendering_config = self.rendering_config.copy(**config_updates)

    # Convenience methods for backward compatibility
    def generate_comprehensive_region_hexagonal_grids_legacy(self, column_summary: List[Dict],
                                                           thresholds_all: Dict,
                                                           all_possible_columns: List[Dict],
                                                           region_columns_map: Dict[str, set],
                                                           neuron_type: str, soma_side: str,
                                                           output_format: str = 'svg',
                                                           save_to_files: bool = True,
                                                           min_max_data: Optional[Dict] = None) -> Dict[str, Dict[str, str]]:
        """
        Legacy interface for generate_comprehensive_region_hexagonal_grids.

        Maintains backward compatibility while using the new data transfer object system internally.
        """
        request = create_grid_generation_request(
            column_summary=column_summary,
            thresholds_all=thresholds_all,
            all_possible_columns=all_possible_columns,
            region_columns_map=region_columns_map,
            neuron_type=neuron_type,
            soma_side=soma_side,
            output_format=output_format,
            save_to_files=save_to_files,
            min_max_data=min_max_data
        )

        result = self.generate_comprehensive_region_hexagonal_grids(request)
        return result.region_grids

    def generate_comprehensive_single_region_grid_legacy(self, all_possible_columns: List[Dict],
                                                        region_column_coords: set, data_map: Dict,
                                                        metric_type: str, region_name: str,
                                                        thresholds: Optional[Dict] = None,
                                                        neuron_type: Optional[str] = None,
                                                        soma_side: Optional[str] = None,
                                                        output_format: str = 'svg',
                                                        other_regions_coords: Optional[set] = None,
                                                        min_max_data: Optional[Dict] = None) -> str:
        """
        Legacy interface for generate_comprehensive_single_region_grid.

        Maintains backward compatibility while using the new data transfer object system internally.
        """
        request = create_single_region_request(
            all_possible_columns=all_possible_columns,
            region_column_coords=region_column_coords,
            data_map=data_map,
            metric_type=metric_type,
            region_name=region_name,
            thresholds=thresholds,
            neuron_type=neuron_type,
            soma_side=soma_side,
            output_format=output_format,
            other_regions_coords=other_regions_coords,
            min_max_data=min_max_data
        )

        return self.generate_comprehensive_single_region_grid(request)
