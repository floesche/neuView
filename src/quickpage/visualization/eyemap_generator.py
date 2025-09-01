"""
Hexagon grid generator for visualizing column data.

This module provides hexagon grid generation functionality supporting SVG
and PNG output formats using Cairo for enhanced visualization capabilities.
"""

import logging
import time
from pathlib import Path
from typing import List, Dict, Optional

from .constants import (
    ERROR_NO_COLUMNS, METRIC_SYNAPSE_DENSITY, METRIC_CELL_COUNT,
    TOOLTIP_SYNAPSE_LABEL, TOOLTIP_CELL_LABEL
)
from .config_manager import ConfigurationManager, EyemapConfiguration
from .color import ColorPalette, ColorMapper
from .coordinate_system import EyemapCoordinateSystem
from .data_processing import DataProcessor
from .data_processing.data_structures import (
    MetricType, SomaSide, ProcessingConfig, ColumnStatus
)
from .rendering import RenderingManager, OutputFormat
from .data_transfer_objects import (
    GridGenerationRequest, SingleRegionGridRequest, RenderingRequest,
    TooltipGenerationRequest, GridGenerationResult,
    create_rendering_request
)
from .region_grid_processor import RegionGridProcessor, RegionGridProcessorFactory
from .file_output_manager import FileOutputManager, FileOutputManagerFactory

logger = logging.getLogger(__name__)


class EyemapGenerator:
    """
    Generate hexagonal grid visualizations for column data.

    Supports SVG and PNG output formats with consistent styling and
    color mapping across different metrics and regions.
    """

    def __init__(self,
                 hex_size: int = None,
                 spacing_factor: float = None,
                 output_dir: Optional[Path] = None,
                 eyemaps_dir: Optional[Path] = None,
                 config: Optional[EyemapConfiguration] = None):
        """
        Initialize the eyemap generator.

        Args:
            hex_size: Size of individual hexagons (optional, for backward compatibility)
            spacing_factor: Spacing between hexagons (optional, for backward compatibility)
            output_dir: Directory to save SVG files (optional, for backward compatibility)
            eyemaps_dir: Directory to save eyemap images (optional, for backward compatibility)
            config: Unified configuration object (recommended)
        """
        # Initialize configuration
        if config is not None:
            self.config = config
        else:
            # Create configuration from individual parameters
            config_params = {}
            if hex_size is not None:
                config_params['hex_size'] = hex_size
            if spacing_factor is not None:
                config_params['spacing_factor'] = spacing_factor
            if output_dir is not None:
                config_params['output_dir'] = output_dir
            if eyemaps_dir is not None:
                config_params['eyemaps_dir'] = eyemaps_dir

            self.config = ConfigurationManager.create_for_generation(**config_params)

        # Convenience properties for direct access
        self.hex_size = self.config.hex_size
        self.spacing_factor = self.config.spacing_factor
        self.output_dir = self.config.output_dir
        self.eyemaps_dir = self.config.eyemaps_dir
        self.embed_mode = self.config.embed_mode

        # Initialize color management components
        self.color_palette = ColorPalette()
        self.color_mapper = ColorMapper(self.color_palette)

        # Initialize coordinate system components
        coord_params = self.config.get_coordinate_system_params()
        self.coordinate_system = EyemapCoordinateSystem(
            hex_size=coord_params['hex_size'],
            spacing_factor=coord_params['spacing_factor'],
            margin=coord_params['margin']
        )

        # Initialize data processing components
        self.data_processor = DataProcessor()

        # Initialize rendering system components
        self.rendering_config = self.config.to_rendering_config()
        self.rendering_manager = RenderingManager(self.rendering_config, self.color_mapper)

        # Initialize service components
        self.region_processor = RegionGridProcessorFactory.create_processor(self.data_processor)
        self.file_manager = FileOutputManagerFactory.create_from_config(self.config)



    def generate_comprehensive_region_hexagonal_grids(self, request: GridGenerationRequest) -> GridGenerationResult:
        """
        Generate comprehensive hexagonal grid visualizations showing all possible columns.

        Args:
            request: GridGenerationRequest containing all generation parameters

        Returns:
            GridGenerationResult with generation results and metadata
        """
        start_time = time.time()

        # Set embed mode based on save_to_files parameter
        self.embed_mode = not request.save_to_files
        self.config.update(embed_mode=self.embed_mode, save_to_files=request.save_to_files)

        if not request.all_possible_columns:
            return GridGenerationResult(
                region_grids={},
                processing_time=0,
                success=False,
                error_message=ERROR_NO_COLUMNS
            )

        warnings = []

        try:
            # Organize data by side
            data_maps = self._organize_data_by_side(request)

            # Process all regions and sides to generate grids using the processor
            processed_grids = self.region_processor.process_all_regions_and_sides(
                request, data_maps, self.generate_comprehensive_single_region_grid
            )

            # Handle output for all processed grids
            region_grids = self._handle_all_grid_outputs(request, processed_grids)

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

    def _organize_data_by_side(self, request: GridGenerationRequest) -> Dict:
        """
        Organize column data by soma side using the data processor.

        Args:
            request: GridGenerationRequest containing column data and soma side info

        Returns:
            Dictionary mapping sides to their organized data maps
        """
        return self.data_processor.column_data_manager.organize_data_by_side(
            request.column_summary, request.soma_side
        )

    def _handle_all_grid_outputs(self, request: GridGenerationRequest, processed_grids: Dict) -> Dict:
        """
        Handle output for all processed grids using the file output manager.

        Args:
            request: GridGenerationRequest containing output configuration
            processed_grids: Dictionary of processed grids from region processor

        Returns:
            Dictionary mapping region_side keys to their final output
        """
        region_grids = {}

        for region_side_key, grid_data in processed_grids.items():
            region = grid_data['region']
            side = grid_data['side']
            synapse_content = grid_data['synapse_content']
            cell_content = grid_data['cell_content']

            # Use file manager to handle output
            region_grids[region_side_key] = self.file_manager.handle_grid_output(
                request, region, side, synapse_content, cell_content, self.rendering_manager
            )

        return region_grids


    def generate_comprehensive_single_region_grid(self, request: SingleRegionGridRequest) -> str:
        """
        Generate comprehensive hexagonal grid showing all possible columns for a single region.

        Args:
            request: SingleRegionGridRequest containing all generation parameters

        Returns:
            Generated visualization content as string
        """
        # Validate request and return early if invalid
        if not self._validate_single_region_request(request):
            return ""

        # Calculate coordinate ranges and value ranges
        coordinate_ranges = self._calculate_coordinate_ranges(request.all_possible_columns)
        value_range = self._determine_value_range(request.thresholds)

        # Set up visualization metadata
        grid_metadata = self._setup_grid_metadata(request, value_range)

        # Create processing configuration
        processing_config = self._create_processing_configuration(request)

        # Process the data
        processing_result = self._process_single_region_data(request, processing_config)
        if not processing_result.is_successful:
            logger.warning(f"Data processing failed: {processing_result.validation_result.errors}")
            return ""

        # Convert coordinates and create hexagon data
        coord_to_pixel = self._convert_coordinates_to_pixels(request.all_possible_columns, request.soma_side)
        hexagons = self._create_hexagon_data_collection(
            processing_result, coord_to_pixel, request, value_range
        )

        # Finalize visualization
        return self._finalize_single_region_visualization(hexagons, request, grid_metadata, value_range)

    def _validate_single_region_request(self, request: SingleRegionGridRequest) -> bool:
        """
        Validate the single region grid request.

        Checks that the request contains the minimum required data to proceed
        with grid generation. Currently validates that all_possible_columns
        is not empty.

        Args:
            request: The request to validate

        Returns:
            True if request is valid, False otherwise
        """
        return bool(request.all_possible_columns)

    def _calculate_coordinate_ranges(self, all_possible_columns: List[Dict]) -> Dict[str, int]:
        """
        Calculate coordinate ranges from all possible columns.

        Analyzes the hex1 and hex2 coordinates across all columns to determine
        the minimum values. This is used for coordinate system calculations
        and grid positioning.

        Args:
            all_possible_columns: List of column dictionaries with hex1, hex2 coordinates

        Returns:
            Dictionary containing min_hex1 and min_hex2 values
        """
        return {
            'min_hex1': min(col['hex1'] for col in all_possible_columns),
            'min_hex2': min(col['hex2'] for col in all_possible_columns)
        }

    def _determine_value_range(self, thresholds: Optional[Dict]) -> Dict[str, float]:
        """
        Determine the value range from thresholds.

        Extracts the minimum and maximum values from the threshold configuration
        to establish the color mapping range. Falls back to default range of 0-1
        if no thresholds are provided.

        Args:
            thresholds: Optional threshold dictionary containing 'all' key with min/max values

        Returns:
            Dictionary containing global_min, global_max, min_value, max_value, and value_range
        """
        if thresholds and 'all' in thresholds and thresholds['all']:
            global_min = thresholds['all'][0]
            global_max = thresholds['all'][-1]
        else:
            global_min = 0
            global_max = 1

        min_value = global_min if global_min is not None else 0
        max_value = global_max if global_max is not None else 1
        value_range = max_value - min_value if max_value > min_value else 1

        return {
            'global_min': global_min,
            'global_max': global_max,
            'min_value': min_value,
            'max_value': max_value,
            'value_range': value_range
        }

    def _setup_grid_metadata(self, request: SingleRegionGridRequest, value_range: Dict[str, float]) -> Dict[str, str]:
        """
        Set up title and subtitle for the grid visualization.

        Creates appropriate titles based on the metric type (synapse density or cell count)
        and includes region name and neuron type information. The subtitle includes
        soma side information if available.

        Args:
            request: The single region grid request containing region and metric info
            value_range: Value range information (currently unused but kept for consistency)

        Returns:
            Dictionary containing title and subtitle strings
        """
        if request.metric_type == METRIC_SYNAPSE_DENSITY:
            title = f"{request.region_name} Synapses (All Columns)"
            subtitle = f"{request.neuron_type} ({request.soma_side.upper()[:1] if request.soma_side else ''})"
        else:  # cell_count
            title = f"{request.region_name} Cell Count (All Columns)"
            subtitle = f"{request.neuron_type} ({request.soma_side.upper()[:1] if request.soma_side else ''})"

        return {
            'title': title,
            'subtitle': subtitle
        }

    def _create_processing_configuration(self, request: SingleRegionGridRequest) -> ProcessingConfig:
        """
        Create processing configuration from request parameters.

        Converts string-based parameters from the request into strongly-typed
        enum values required by the data processing system. Handles metric type
        conversion (synapse_density vs cell_count) and soma side conversion
        (left/right/combined).

        Args:
            request: The single region grid request with string parameters

        Returns:
            ProcessingConfig object with properly typed enum values
        """
        # Convert metric type to enum
        if request.metric_type == METRIC_SYNAPSE_DENSITY:
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

        return ProcessingConfig(
            metric_type=metric_enum,
            soma_side=soma_enum,
            region_name=request.region_name,
            neuron_type=request.neuron_type,
            output_format=request.output_format
        )

    def _process_single_region_data(self, request: SingleRegionGridRequest, config: ProcessingConfig):
        """
        Process the single region data using the data processor.

        Delegates to the data processor to handle coordinate mapping, value extraction,
        and status determination for each column. This step transforms raw data into
        processed column objects with standardized values and metadata.

        Args:
            request: The single region grid request containing raw data
            config: Processing configuration with enum values

        Returns:
            Data processing result containing processed columns and validation info
        """
        return self.data_processor._process_side_data(
            request.all_possible_columns,
            request.region_column_coords,
            request.data_map,
            config,
            request.other_regions_coords or set(),
            request.thresholds,
            request.min_max_data,
            request.soma_side or 'right'
        )

    def _convert_coordinates_to_pixels(self, all_possible_columns: List[Dict], soma_side: Optional[str]) -> Dict:
        """
        Convert processed columns to pixel coordinates and create coordinate mapping.

        Uses the coordinate system to transform hex1/hex2 coordinates into pixel
        positions for rendering. Creates a lookup dictionary for efficient coordinate
        to pixel mapping during hexagon creation.

        Args:
            all_possible_columns: List of column dictionaries with hex coordinates
            soma_side: Optional soma side specification for mirroring

        Returns:
            Dictionary mapping (hex1, hex2) tuples to {'x': x, 'y': y} pixel coordinates
        """
        columns_with_coords = self.coordinate_system.convert_column_coordinates(
            all_possible_columns, mirror_side=soma_side
        )

        return {
            (col['hex1'], col['hex2']): {'x': col['x'], 'y': col['y']}
            for col in columns_with_coords
        }

    def _create_hexagon_data_collection(self, processing_result, coord_to_pixel: Dict,
                                      request: SingleRegionGridRequest, value_range: Dict[str, float]) -> List[Dict]:
        """
        Create hexagon data collection from processed results.

        Transforms processed column data into hexagon dictionaries suitable for rendering.
        Each hexagon includes position, value, color, layer information, and metadata
        needed for visualization and tooltips.

        Args:
            processing_result: Result from data processing containing processed columns
            coord_to_pixel: Coordinate to pixel mapping dictionary
            request: The single region grid request with raw data access
            value_range: Value range information for color mapping

        Returns:
            List of hexagon data dictionaries ready for rendering
        """
        hexagons = []
        min_value = value_range['min_value']
        max_value = value_range['max_value']

        for processed_col in processing_result.processed_columns:
            coord_tuple = (processed_col.hex1, processed_col.hex2)

            if coord_tuple not in coord_to_pixel:
                continue

            pixel_coords = coord_to_pixel[coord_tuple]

            # Get raw data for layer colors
            layer_colors = self._extract_layer_colors(processed_col, request)

            # Map color using color mapper
            color = self._determine_hexagon_color(processed_col, min_value, max_value)
            if color is None:
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
                'neuron_count': processed_col.value if request.metric_type == METRIC_CELL_COUNT else 0,
                'column_name': f"{request.region_name}_col_{processed_col.hex1}_{processed_col.hex2}",
                'synapse_value': processed_col.value if request.metric_type == METRIC_SYNAPSE_DENSITY else 0,
                'status': processed_col.status.value,
                'metric_type': request.metric_type
            }
            hexagons.append(hexagon_data)

        return hexagons

    def _extract_layer_colors(self, processed_col, request: SingleRegionGridRequest) -> List:
        """
        Extract layer colors for a processed column.

        Retrieves raw layer-specific data from the original data map based on
        the metric type. For synapse density, gets 'synapses_list_raw'; for
        cell count, gets 'neurons_list'. Falls back to processed layer colors
        if raw data is unavailable.

        Args:
            processed_col: Processed column data with coordinate and status info
            request: The single region grid request with access to raw data map

        Returns:
            List of layer colors or values for the column
        """
        if processed_col.status == ColumnStatus.HAS_DATA:
            data_key = (request.region_name, processed_col.hex1, processed_col.hex2)
            data_col = request.data_map.get(data_key)

            if data_col and request.metric_type == METRIC_SYNAPSE_DENSITY:
                return data_col.get('synapses_list_raw', processed_col.layer_colors)
            elif data_col and request.metric_type == METRIC_CELL_COUNT:
                return data_col.get('neurons_list', processed_col.layer_colors)
            else:
                return processed_col.layer_colors
        else:
            return []

    def _determine_hexagon_color(self, processed_col, min_value: float, max_value: float) -> Optional[str]:
        """
        Determine the color for a hexagon based on its status and value.

        Maps column status to appropriate colors: data columns get value-based colors,
        no-data columns get white, not-in-region columns get dark gray. Other statuses
        are skipped (return None).

        Args:
            processed_col: Processed column data with status and value
            min_value: Minimum value for color mapping range
            max_value: Maximum value for color mapping range

        Returns:
            Color string (hex code) or None if hexagon should be skipped
        """
        if processed_col.status == ColumnStatus.HAS_DATA:
            return self.color_mapper.map_value_to_color(processed_col.value, min_value, max_value)
        elif processed_col.status == ColumnStatus.NO_DATA:
            return self.color_palette.white
        elif processed_col.status == ColumnStatus.NOT_IN_REGION:
            return self.color_palette.dark_gray
        else:
            return None

    def _finalize_single_region_visualization(self, hexagons: List[Dict], request: SingleRegionGridRequest,
                                            grid_metadata: Dict[str, str], value_range: Dict[str, float]) -> str:
        """
        Finalize the visualization by adding tooltips and rendering.

        Completes the visualization pipeline by adding interactive tooltips to hexagons,
        creating a rendering request with all necessary parameters, and delegating to
        the rendering manager for final output generation.

        Args:
            hexagons: List of hexagon data dictionaries ready for rendering
            request: The single region grid request with output preferences
            grid_metadata: Grid metadata including title and subtitle strings
            value_range: Value range information for color scale

        Returns:
            Generated visualization content as string (SVG or PNG data)
        """
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
            min_val=value_range['min_value'],
            max_val=value_range['max_value'],
            thresholds=request.thresholds or {},
            title=grid_metadata['title'],
            subtitle=grid_metadata['subtitle'],
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
        lbl_stat_for_zero = TOOLTIP_SYNAPSE_LABEL if request.metric_type == METRIC_SYNAPSE_DENSITY else TOOLTIP_CELL_LABEL

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

    def update_configuration(self, hex_size: int = None, spacing_factor: float = None, **kwargs):
        """
        Update hexagon grid generator configuration in-place.

        Args:
            hex_size: New hexagon size (optional)
            spacing_factor: New spacing factor (optional)
            **kwargs: Additional configuration parameters
        """
        # Collect all updates
        updates = {}
        if hex_size is not None:
            updates['hex_size'] = hex_size
        if spacing_factor is not None:
            updates['spacing_factor'] = spacing_factor
        updates.update(kwargs)

        if updates:
            # Update main configuration
            self.config.update(**updates)

            # Update convenience properties
            self.hex_size = self.config.hex_size
            self.spacing_factor = self.config.spacing_factor
            self.output_dir = self.config.output_dir
            self.eyemaps_dir = self.config.eyemaps_dir
            self.embed_mode = self.config.embed_mode

            # Update coordinate system
            coord_params = self.config.get_coordinate_system_params()
            self.coordinate_system.update_configuration(
                hex_size=coord_params.get('hex_size'),
                spacing_factor=coord_params.get('spacing_factor'),
                margin=coord_params.get('margin')
            )

            # Update rendering components
            self.rendering_config = self.config.to_rendering_config()

            # Update rendering manager with new config
            config_updates = {k: v for k, v in updates.items()
                            if k in ['hex_size', 'spacing_factor']}
            if config_updates:
                self.rendering_manager.update_config(**config_updates)
