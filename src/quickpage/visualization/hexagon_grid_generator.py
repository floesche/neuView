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
from .coordinate_system import HexagonGridCoordinateSystem

logger = logging.getLogger(__name__)


class HexagonGridGenerator:
    """
    Generate hexagonal grid visualizations for column data.

    Supports SVG and PNG output formats with consistent styling and
    color mapping across different metrics and regions.
    """

    def __init__(self, hex_size: int = 6, spacing_factor: float = 1.1, output_dir: Optional[Path] = None, eyemaps_dir: Optional[Path] = None):
        """
        Initialize the hexagon grid generator.

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
        self.coordinate_system = HexagonGridCoordinateSystem(hex_size, spacing_factor, margin=10)

        # Maintain backward compatibility
        self.colors = self.color_palette.get_all_colors()

    def generate_comprehensive_region_hexagonal_grids(self, column_summary: List[Dict],
                                                    thresholds_all: Dict,
                                                    all_possible_columns: List[Dict],
                                                    region_columns_map: Dict[str, set],
                                                    neuron_type: str, soma_side: str,
                                                    output_format: str = 'svg',
                                                    save_to_files: bool = False,
                                                    min_max_data: Optional[Dict] = None) -> Dict[str, Dict[str, str]]:
        """
        Generate comprehensive hexagonal grid visualizations showing all possible columns.

        Args:
            column_summary: List of column data dictionaries with actual data
            thresholds_all: Dict containing the values to use for colorscale thresholds for both neurons and cells.
            all_possible_columns: List of all possible column coordinates across all regions
            region_columns_map: Map of region_side names (e.g., 'ME_L', 'LO_R') to sets of (hex1, hex2) tuples that exist in each region-side combination
            neuron_type: Type of neuron being visualized
            soma_side: Side of soma (left/right/combined)
            output_format: Output format ('svg' or 'png')
            save_to_files: If True, save files to output/static/images and return file paths
            min_max_data: Dict containing min/max values for color normalization

        Returns:
            Dictionary mapping region names to visualization data or region-side combinations when soma_side is "combined"
        """
        # Set embed mode based on save_to_files parameter
        self.embed_mode = not save_to_files

        if not all_possible_columns:
            return {}

        region_grids = {}

        # Create data maps for each side
        data_maps = {}
        if soma_side == 'combined':
            # For combined sides, create separate data maps for L and R
            data_maps['L'] = {}
            data_maps['R'] = {}
            for col in column_summary:
                side = col.get('side')
                if side in ['L', 'R']:
                    key = (col['region'], col['hex1'], col['hex2'])
                    if side not in data_maps:
                        data_maps[side] = {}
                    data_maps[side][key] = col
        else:
            # For single side, determine which side to use and create one data map
            if soma_side in ['left', 'L']:
                target_side = 'L'
            elif soma_side in ['right', 'R']:
                target_side = 'R'
            else:
                # Fallback: use any available side from the data
                target_side = column_summary[0].get('side', 'L') if column_summary else 'L'

            data_maps[target_side] = {}
            for col in column_summary:
                key = (col['region'], col['hex1'], col['hex2'])
                data_maps[target_side][key] = col

        # Generate grids for each region and side
        region_order = ['ME', 'LO', 'LOP']
        for region in region_order:
            for side, data_map in data_maps.items():
                # Use side-specific region columns for accurate "not available" determination
                region_side_key = f"{region}_{side}"
                region_column_coords = region_columns_map.get(region_side_key, set())
                # Determine if mirroring should be applied:
                # - For soma_side='left': mirror everything
                # - For soma_side='combined': mirror only L grids to match dedicated left pages
                # - For soma_side='right': don't mirror anything
                if soma_side.lower() == 'left':
                    mirror_side = 'left'  # Mirror everything
                elif soma_side.lower() == 'combined' and side == 'L':
                    mirror_side = 'left'  # Mirror only L grids
                else:
                    mirror_side = 'right'  # No mirroring

                # Get other regions' column coordinates for the same soma side
                other_regions_coords = set()
                other_regions = [r for r in ['ME', 'LO', 'LOP'] if r != region]
                for other_region in other_regions:
                    other_region_key = f"{other_region}_{side}"
                    if other_region_key in region_columns_map:
                        other_regions_coords.update(region_columns_map[other_region_key])

                # Filter all_possible_columns to only include columns relevant for this soma side
                # (columns that exist in current region OR in other regions for this side)
                relevant_coords = region_column_coords | other_regions_coords
                side_filtered_columns = [col for col in all_possible_columns
                                       if (col['hex1'], col['hex2']) in relevant_coords]

                synapse_content = self.generate_comprehensive_single_region_grid(
                    side_filtered_columns, region_column_coords, data_map,
                    'synapse_density', region, thresholds_all['total_synapses'],
                     neuron_type, mirror_side, output_format, other_regions_coords,
                     min_max_data
                )
                cell_content = self.generate_comprehensive_single_region_grid(
                    side_filtered_columns, region_column_coords, data_map,
                    'cell_count', region, thresholds_all['neuron_count'],
                    neuron_type, mirror_side, output_format, other_regions_coords,
                    min_max_data
                )

                region_side_key = f"{region}_{side}"

                if save_to_files and self.output_dir and not self.embed_mode:
                    # Save files and return paths
                    if output_format == 'svg':
                        synapse_path = self._save_svg_file(synapse_content, f"{region}_{neuron_type}_{side}_synapse_density")
                        cell_path = self._save_svg_file(cell_content, f"{region}_{neuron_type}_{side}_cell_count")
                    elif output_format == 'png':
                        synapse_path = self._save_png_file(synapse_content, f"{region}_{neuron_type}_{side}_synapse_density")
                        cell_path = self._save_png_file(cell_content, f"{region}_{neuron_type}_{side}_cell_count")
                    else:
                        raise ValueError(f"Unsupported output format: {output_format}")

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

        return region_grids


    def generate_comprehensive_single_region_grid(self, all_possible_columns: List[Dict],
                                                region_column_coords: set, data_map: Dict,
                                                metric_type: str, region_name: str,
                                                thresholds: Optional[Dict] = None,
                                                neuron_type: Optional[str] = None,
                                                soma_side: Optional[str] = None,
                                                output_format: str = 'svg',
                                                other_regions_coords: Optional[set] = None,
                                                min_max_data: Optional[Dict] = None) -> str:
        """
        Generate comprehensive hexagonal grid showing all possible columns for a single region.

        Args:
            all_possible_columns: List of all possible column coordinates
            region_column_coords: Set of (hex1, hex2) tuples that exist in this region
            data_map: Dictionary mapping (region, hex1, hex2) to column data
            metric_type: 'synapse_density' or 'cell_count'
            region_name: Name of the region (ME, LO, LOP)
            thresholds: Dict of threshold values for colorscales for either neurons or cells.
            neuron_type: Type of neuron
            soma_side: Side of soma
            output_format: Output format ('svg' or 'png')
            other_regions_coords: Set of coordinate tuples that exist in other regions (for gray columns)

        Returns:
            Generated visualization content as string
        """
        if not all_possible_columns:
            return ""

        # Calculate coordinate ranges from all possible columns
        min_hex1 = min(col['hex1'] for col in all_possible_columns)
        min_hex2 = min(col['hex2'] for col in all_possible_columns)

        # Extract the min and max value per column across regions and hemispheres.
        if thresholds and 'all' in thresholds and thresholds['all']:
            global_min = thresholds['all'][0]
            global_max = thresholds['all'][-1]
        else:
            global_min = 0
            global_max = 1

        # Set up title and range
        if metric_type == 'synapse_density':
            title = f"{region_name} Synapses (All Columns)"
            subtitle = f"{neuron_type} ({soma_side.upper()[:1] if soma_side else ''})"
            min_value = global_min if global_min is not None else 0
            max_value = global_max if global_max is not None else 1
        else:  # cell_count
            title = f"{region_name} Cell Count (All Columns)"
            subtitle = f"{neuron_type} ({soma_side.upper()[:1] if soma_side else ''})"
            min_value = global_min if global_min is not None else 0
            max_value = global_max if global_max is not None else 1

        value_range = max_value - min_value if max_value > min_value else 1

        # Get colors for different states from palette
        state_colors = self.color_palette.get_state_colors()

        # Create hexagonal grid coordinates for all possible columns
        # Convert all columns to include pixel coordinates
        columns_with_coords = self.coordinate_system.convert_column_coordinates(
            all_possible_columns, mirror_side=soma_side
        )

        hexagons = []
        for col in columns_with_coords:

            # Determine color and value based on data availability
            coord_tuple = (col['hex1'], col['hex2'])
            data_key = (region_name, col['hex1'], col['hex2'])

            # Check if column exists in current region
            if coord_tuple in region_column_coords:
                # Column exists in current region
                if data_key in data_map:
                    # Has data for current neuron type - color based on value
                    data_col = data_map[data_key]
                    if metric_type == 'synapse_density':
                        metric_value = data_col['total_synapses']
                        layer_values = data_col['synapses_per_layer']
                        layer_colors = data_col['synapses_list_raw']  # Pass raw synapse counts, will use filter in template
                    else:  # cell_count
                        metric_value = data_col['neuron_count']
                        layer_values = data_col['neurons_per_layer']
                        layer_colors = data_col['neurons_list']  # Pass raw neuron counts, will use filter in template

                    color = self.color_mapper.map_value_to_color(metric_value, min_value, max_value)
                    value = metric_value
                    status = 'has_data'
                else:
                    # Column exists in current region but no data for current neuron type - white
                    color = self.color_palette.white
                    value = 0
                    layer_values = []
                    layer_colors = []
                    status = 'no_data'
            elif other_regions_coords and coord_tuple in other_regions_coords:
                # Column doesn't exist in current region but exists in other regions - gray
                color = self.color_palette.dark_gray
                value = 0
                layer_values = []
                layer_colors = []
                status = 'not_in_region'
            else:
                # Column doesn't exist in current region or other regions for this soma side - skip
                continue

            hexagons.append({
                'x': col['x'],
                'y': col['y'],
                'value': value,
                'layer_values': layer_values,
                'layer_colors': layer_colors,
                'color': color,
                'region': region_name,
                'side': 'combined',  # Since we're showing all possible columns
                'hex1': col['hex1'],
                'hex2': col['hex2'],
                'neuron_count': value if metric_type == 'cell_count' else 0,
                'column_name': f"{region_name}_col_{col['hex1']}_{col['hex2']}",
                'synapse_value': value if metric_type == 'synapse_density' else 0,
                'status': status,
                'metric_type': metric_type
            })

        # Generate visualization based on format
        if output_format.lower() == 'png':
            return self._create_comprehensive_hexagonal_png(hexagons, min_value, max_value, thresholds or {}, title, subtitle, metric_type, soma_side or 'right')
        else:
            return self._create_comprehensive_region_hexagonal_svg(hexagons, min_value, max_value, thresholds or {}, title, subtitle, metric_type, soma_side or 'right', min_max_data)


    def value_to_color(self, normalized_value: float) -> str:
        """
        Convert normalized value (0-1) to one of 5 distinct colors from lightest to darkest red.

        Args:
            normalized_value: Value between 0 and 1

        Returns:
            Hex color string
        """
        return self.color_palette.value_to_color(normalized_value)


    def _create_comprehensive_region_hexagonal_svg(self, hexagons: List[Dict], min_val: float, max_val: float,
                                                   thresholds: Dict, title: str, subtitle: str, metric_type: str
                                                   , soma_side: str|None, min_max_data: Optional[Dict] = None) -> str:
        """
        Create comprehensive SVG representation of hexagonal grid showing all possible columns.

        This method uses a Jinja2 template (templates/comprehensive_hexagon_grid.svg) to generate the SVG,
        making the code more maintainable and separating presentation logic from data processing.
        The generated SVG includes interactive JavaScript tooltips that suppress default browser
        tooltips while preserving accessibility.

        Args:
            hexagons: List of hexagon data dictionaries including status information
            min_val: Minimum value for scaling
            max_val: Maximum value for scaling
            thresholds: Dict containing thresholds for colorscale for either synapses or neurons.
            title: Chart title
            subtitle: Chart subtitle
            metric_type: Type of metric being displayed
            soma_side: Side of the soma (left or right)

        Returns:
            SVG content as string rendered from Jinja2 template
        """
        if not hexagons:
            return ""

        # Calculate SVG layout using coordinate system
        svg_layout = self.coordinate_system.calculate_svg_layout(hexagons, soma_side or 'right')

        if not svg_layout:
            return ""

        # Extract layout information
        width = svg_layout['width']
        height = svg_layout['height']
        min_x = svg_layout['min_x']
        min_y = svg_layout['min_y']
        margin = svg_layout['margin']
        legend_x = svg_layout['legend_x']
        title_x = svg_layout['title_x']
        hex_points = svg_layout['hex_points'].split()

        # Legacy variables for template compatibility
        number_precision = 2
        legend_width = 12

        # Process hexagon data with tooltips
        processed_hexagons = self._add_tooltips_to_hexagons(hexagons, soma_side or 'right', metric_type)

        # Calculate legend data
        data_hexagons = [h for h in hexagons if h.get('status') == 'has_data']
        legend_data = None

        if data_hexagons:
            legend_height = 60
            legend_y = height - legend_height - 5
            legend_title = "Total Synapses" if metric_type == 'synapse_density' else "Cell Count"
            legend_type_name = "Synapses" if metric_type == 'synapse_density' else "Cells"
            title_y = legend_y + legend_height // 2
            bin_height = legend_height // 5

            legend_data = {
                'legend_height': legend_height,
                'legend_y': legend_y,
                'legend_title': legend_title,
                'legend_type_name': legend_type_name,
                'title_y': title_y,
                'bin_height': bin_height,
                'thresholds': thresholds['all'], # Colorscale to use for "all_layers"
                'layer_thresholds': thresholds['layers'] # dict containing colorscales for layers
            }

        # Setup Jinja2 environment
        template_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))

        # Create filter function that captures min_max_data for region-specific normalization
        captured_min_max_data = min_max_data or {}
        captured_color_mapper = self.color_mapper

        def synapses_to_colors(synapses_list, region):
            """Convert synapses_list to synapse_colors using normalization."""
            if not synapses_list or not captured_min_max_data:
                return [captured_color_mapper.palette.white] * len(synapses_list)

            syn_min = float(captured_min_max_data.get('min_syn_region', {}).get(region, 0.0))
            syn_max = float(captured_min_max_data.get('max_syn_region', {}).get(region, 0.0))

            colors = []
            for syn_val in synapses_list:
                if syn_val > 0:
                    color = captured_color_mapper.map_value_to_color(float(syn_val), syn_min, syn_max)
                else:
                    color = captured_color_mapper.palette.white
                colors.append(color)

            return colors

        def neurons_to_colors(neurons_list, region):
            """Convert neurons_list to neuron_colors using normalization."""
            if not neurons_list or not captured_min_max_data:
                return [captured_color_mapper.palette.white] * len(neurons_list) if neurons_list else []

            cel_min = float(captured_min_max_data.get('min_cells_region', {}).get(region, 0.0))
            cel_max = float(captured_min_max_data.get('max_cells_region', {}).get(region, 0.0))

            colors = []
            for cel_val in neurons_list:
                if cel_val > 0:
                    color = captured_color_mapper.map_value_to_color(float(cel_val), cel_min, cel_max)
                else:
                    color = captured_color_mapper.palette.white
                colors.append(color)

            return colors

        env.filters['synapses_to_colors'] = synapses_to_colors
        env.filters['neurons_to_colors'] = neurons_to_colors
        template = env.get_template('comprehensive_hexagon_grid.svg')
        # Render template
        svg_content = template.render(
            width=width,
            height=height,
            title=title,
            subtitle=subtitle,
            hexagons=processed_hexagons,
            hex_points=hex_points,
            min_x=min_x,
            min_y=min_y,
            margin=margin,
            number_precision=number_precision,
            data_hexagons=data_hexagons,
            legend_x=legend_x,
            legend_width=legend_width,
            title_x=title_x,
            colors=self.colors,
            enumerate=enumerate,
            soma_side=soma_side,
            min_max_data=captured_min_max_data,
            **legend_data if legend_data else {}
        )

        return svg_content

    def _add_tooltips_to_hexagons(self, hexagons: list
                                  , soma_side: str
                                  , metric_type: str):
        """
        Add 'tooltip' and 'tooltip_layers' to each hexagon dict.

        - 'tooltip' is the summary tooltip based on status and metric_type.
        - 'tooltip_layers' is a list of per-layer tooltips derived from 'layer_values',
        with ROI strings that include 'layer(<idx>)' where idx is 1-based.

        Args:
            hexagons: list of dicts with keys like 'hex1', 'hex2', 'region'
            , 'status', 'value', 'layer_values' (list[int]).
            soma_side: e.g. "L" or "R".
            metric_type: either "synapse_density" or "cell_count".

        Returns:
            A new list of dicts, each with 'tooltip' and 'tooltip_layers' added.
        """
        lbl_stat_for_zero = "Synapse count" if metric_type == 'synapse_density' else "Cell count"

        processed_hexagons = []
        for hex_data in hexagons:
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
                    f"Column not identified in {region} ({soma_side})"
                )
            elif status == 'no_data':
                tooltip = (
                    f"Column: {hex1}, {hex2}\n"
                    f"{lbl_stat_for_zero}: 0\n"
                    f"ROI: {region} ({soma_side})"
                )
            else:  # has_data
                tooltip = (
                    f"Column: {hex1}, {hex2}\n"
                    f"{lbl_stat_for_zero}: {value}\n"
                    f"ROI: {region} ({soma_side})"
                )

            # --- Per-layer tooltips ---
            tooltip_layers = []
            # Use 1-based index to match layer numbering
            for i, v in enumerate(layer_values, start=1):
                if status == 'not_in_region':
                    layer_tip = (
                        f"Column: {hex1}, {hex2}\n"
                        f"Column not identified in {region} ({soma_side}) layer({i})"
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

    def _create_comprehensive_hexagonal_png(self, hexagons: List[Dict], min_val: float, max_val: float
                                            , thresholds:Dict, title: str, subtitle: str, metric_type: str
                                            , soma_side: str|None) -> str:
        """
        Create comprehensive PNG representation of hexagonal grid showing all possible columns.

        Args:
            hexagons: List of hexagon data dictionaries including status information
            min_val: Minimum value for scaling
            max_val: Maximum value for scaling
            title: Chart title
            subtitle: Chart subtitle
            metric_type: Type of metric being displayed

        Returns:
            Base64 encoded PNG content
        """
        # Generate SVG content and convert to PNG using cairosvg
        svg_content = self._create_comprehensive_region_hexagonal_svg(hexagons
                                                                      , min_val
                                                                      , max_val
                                                                      , thresholds
                                                                      , title
                                                                      , subtitle
                                                                      , metric_type
                                                                      , soma_side)

        # Convert SVG to PNG using similar approach as existing PNG method
        try:
            import cairosvg
            import base64
            import io

            png_buffer = io.BytesIO()
            cairosvg.svg2png(bytestring=svg_content.encode(), write_to=png_buffer)
            png_buffer.seek(0)

            base64_data = base64.b64encode(png_buffer.getvalue()).decode('utf-8')
            return f"data:image/png;base64,{base64_data}"
        except ImportError:
            # Fallback to returning SVG if cairosvg is not available
            logger.warning("cairosvg not available, returning SVG content instead of PNG")
            return svg_content

    def _save_svg_file(self, svg_content: str, filename: str) -> str:
        """
        Save SVG content to a file and return the relative path.

        Args:
            svg_content: SVG content as string
            filename: Base filename without extension

        Returns:
            Relative file path to the saved SVG
        """
        if self.embed_mode:
            raise ValueError("File saving disabled in embed mode")
        if not self.output_dir:
            raise ValueError("output_dir must be set to save files")

        # Ensure the eyemaps directory exists
        if not self.eyemaps_dir:
            raise ValueError("eyemaps_dir must be set to save files")

        self.eyemaps_dir.mkdir(parents=True, exist_ok=True)

        # Clean filename and add extension
        clean_filename = filename.replace(" ", "_").replace("(", "").replace(")", "") + ".svg"
        file_path = self.eyemaps_dir / clean_filename

        # Save the SVG file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)

        # Return relative path from neuron page location (types/ to eyemaps/)
        return f"../eyemaps/{clean_filename}"

    def _save_png_file(self, png_data_url: str, filename: str) -> str:
        """
        Save PNG data URL to a file and return the relative path.

        Args:
            png_data_url: PNG data URL (data:image/png;base64,...)
            filename: Base filename without extension

        Returns:
            Relative file path to the saved PNG
        """
        if self.embed_mode:
            raise ValueError("File saving disabled in embed mode")
        if not self.output_dir:
            raise ValueError("output_dir must be set to save files")

        # Ensure the eyemaps directory exists
        if not self.eyemaps_dir:
            raise ValueError("eyemaps_dir must be set to save files")

        self.eyemaps_dir.mkdir(parents=True, exist_ok=True)

        # Extract base64 data from data URL
        if not png_data_url.startswith('data:image/png;base64,'):
            raise ValueError("Invalid PNG data URL format")

        base64_data = png_data_url.split(',', 1)[1]

        # Clean filename and add extension
        clean_filename = filename.replace(" ", "_").replace("(", "").replace(")", "") + ".png"
        file_path = self.eyemaps_dir / clean_filename

        # Save the PNG file
        import base64
        with open(file_path, 'wb') as f:
            f.write(base64.b64decode(base64_data))

        # Return relative path from neuron page location (types/ to eyemaps/)
        return f"../eyemaps/{clean_filename}"
