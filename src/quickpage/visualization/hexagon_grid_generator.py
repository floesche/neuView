"""
Hexagon grid generator for visualizing column data.

This module provides hexagon grid generation functionality supporting both SVG
and PNG output formats using Cairo for enhanced visualization capabilities.
"""

import math
import colorsys
import logging
import os
from pathlib import Path
from typing import List, Dict, Optional
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)
import tempfile
import os


class HexagonGridGenerator:
    """
    Generate hexagonal grid visualizations for column data.

    Supports both SVG and PNG output formats with consistent styling and
    color mapping across different metrics and regions.
    """

    def __init__(self, hex_size: int = 6, spacing_factor: float = 1.1, output_dir: Optional[Path] = None):
        """
        Initialize the hexagon grid generator.

        Args:
            hex_size: Size of individual hexagons
            spacing_factor: Spacing between hexagons
            output_dir: Directory to save SVG files (optional)
        """
        self.hex_size = hex_size
        self.spacing_factor = spacing_factor
        self.output_dir = output_dir
        self.embed_mode = False
        self.colors = [
            '#fee5d9',  # Lightest (0.0-0.2)
            '#fcbba1',  # Light (0.2-0.4)
            '#fc9272',  # Medium (0.4-0.6)
            '#ef6548',  # Dark (0.6-0.8)
            '#a50f15'   # Darkest (0.8-1.0)
        ]

    def generate_comprehensive_region_hexagonal_grids(self, column_summary: List[Dict],
                                                    all_possible_columns: List[Dict],
                                                    region_columns_map: Dict[str, set],
                                                    neuron_type: str, soma_side: str,
                                                    output_format: str = 'svg',
                                                    save_to_files: bool = False) -> Dict[str, Dict[str, str]]:
        """
        Generate comprehensive hexagonal grid visualizations showing all possible columns.

        Args:
            column_summary: List of column data dictionaries with actual data
            all_possible_columns: List of all possible column coordinates across all regions
            region_columns_map: Map of region_side names (e.g., 'ME_L', 'LO_R') to sets of (hex1_dec, hex2_dec) tuples that exist in each region-side combination
            neuron_type: Type of neuron being visualized
            soma_side: Side of soma (left/right/both)
            output_format: Output format ('svg' or 'png')
            save_to_files: If True, save files to output/static/images and return file paths

        Returns:
            Dictionary mapping region names to visualization data or region-side combinations when soma_side is "both"
        """
        # Set embed mode based on save_to_files parameter
        self.embed_mode = not save_to_files

        if not all_possible_columns:
            return {}

        # Calculate global ranges for consistent color scaling from actual data
        if column_summary:
            global_synapse_min = min(col['total_synapses'] for col in column_summary)
            global_synapse_max = max(col['total_synapses'] for col in column_summary)
            global_cell_min = min(col['neuron_count'] for col in column_summary)
            global_cell_max = max(col['neuron_count'] for col in column_summary)
        else:
            global_synapse_min = global_synapse_max = 0
            global_cell_min = global_cell_max = 0

        region_grids = {}

        # Create data maps for each side
        data_maps = {}
        if soma_side == 'both':
            # For both sides, create separate data maps for L and R
            data_maps['L'] = {}
            data_maps['R'] = {}
            for col in column_summary:
                side = col.get('side')
                if side in ['L', 'R']:
                    key = (col['region'], col['hex1_dec'], col['hex2_dec'])
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
                key = (col['region'], col['hex1_dec'], col['hex2_dec'])
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
                # - For soma_side='both': mirror only L grids to match dedicated left pages
                # - For soma_side='right': don't mirror anything
                if soma_side.lower() == 'left':
                    mirror_side = 'left'  # Mirror everything
                elif soma_side.lower() == 'both' and side == 'L':
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
                                       if (col['hex1_dec'], col['hex2_dec']) in relevant_coords]

                synapse_content = self.generate_comprehensive_single_region_grid(
                    side_filtered_columns, region_column_coords, data_map,
                    'synapse_density', region, global_synapse_min, global_synapse_max,
                    neuron_type, mirror_side, output_format, other_regions_coords
                )
                cell_content = self.generate_comprehensive_single_region_grid(
                    side_filtered_columns, region_column_coords, data_map,
                    'cell_count', region, global_cell_min, global_cell_max,
                    neuron_type, mirror_side, output_format, other_regions_coords
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
                                                global_min: Optional[float] = None,
                                                global_max: Optional[float] = None,
                                                neuron_type: Optional[str] = None,
                                                soma_side: Optional[str] = None,
                                                output_format: str = 'svg',
                                                other_regions_coords: set = None) -> str:
        """
        Generate comprehensive hexagonal grid showing all possible columns for a single region.

        Args:
            all_possible_columns: List of all possible column coordinates
            region_column_coords: Set of (hex1_dec, hex2_dec) tuples that exist in this region
            data_map: Dictionary mapping (region, hex1_dec, hex2_dec) to column data
            metric_type: 'synapse_density' or 'cell_count'
            region_name: Name of the region (ME, LO, LOP)
            global_min: Global minimum value for consistent color scaling
            global_max: Global maximum value for consistent color scaling
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
        min_hex1 = min(col['hex1_dec'] for col in all_possible_columns)
        max_hex1 = max(col['hex1_dec'] for col in all_possible_columns)
        min_hex2 = min(col['hex2_dec'] for col in all_possible_columns)
        max_hex2 = max(col['hex2_dec'] for col in all_possible_columns)

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

        # Define colors for different states
        dark_gray = '#999999'  # Column doesn't exist in this region
        white = '#ffffff'      # Column exists but no data for current dataset

        # Create hexagonal grid coordinates for all possible columns
        hexagons = []
        for col in all_possible_columns:
            # Convert hex1/hex2 to hexagonal grid coordinates
            hex1_coord = col['hex1_dec'] - min_hex1
            hex2_coord = col['hex2_dec'] - min_hex2

            # Map to axial coordinates (q, r) for hexagonal grid positioning
            q = -(hex1_coord - hex2_coord) - 3
            r = -hex2_coord

            # Convert to pixel coordinates using proper hexagonal spacing
            x = self.hex_size * self.spacing_factor * (3/2 * q)
            y = self.hex_size * self.spacing_factor * (math.sqrt(3)/2 * q + math.sqrt(3) * r)

            # Flip x-coordinate for left soma side neurons to mirror the grid
            if soma_side and (soma_side.lower() == 'left' or soma_side == 'L'):
                x = -x

            # Determine color and value based on data availability
            coord_tuple = (col['hex1_dec'], col['hex2_dec'])
            data_key = (region_name, col['hex1_dec'], col['hex2_dec'])

            # Check if column exists in current region
            if coord_tuple in region_column_coords:
                # Column exists in current region
                if data_key in data_map:
                    # Has data for current neuron type - color based on value
                    data_col = data_map[data_key]
                    if metric_type == 'synapse_density':
                        metric_value = data_col['total_synapses']
                    else:  # cell_count
                        metric_value = data_col['neuron_count']

                    normalized_value = (metric_value - min_value) / value_range if value_range > 0 else 0
                    color = self._value_to_color(normalized_value)
                    value = metric_value
                    status = 'has_data'
                else:
                    # Column exists in current region but no data for current neuron type - white
                    color = white
                    value = 0
                    status = 'no_data'
            elif other_regions_coords and coord_tuple in other_regions_coords:
                # Column doesn't exist in current region but exists in other regions - gray
                color = dark_gray
                value = 0
                status = 'not_in_region'
            else:
                # Column doesn't exist in current region or other regions for this soma side - skip
                continue

            hexagons.append({
                'x': x,
                'y': y,
                'value': value,
                'color': color,
                'region': region_name,
                'side': 'combined',  # Since we're showing all possible columns
                'hex1': col['hex1'],
                'hex2': col['hex2'],
                'hex1_dec': col['hex1_dec'],
                'hex2_dec': col['hex2_dec'],
                'neuron_count': value if metric_type == 'cell_count' else 0,
                'column_name': f"{region_name}_col_{col['hex1']}_{col['hex2']}",
                'synapse_value': value if metric_type == 'synapse_density' else 0,
                'status': status
            })

        # Generate visualization based on format
        if output_format.lower() == 'png':
            return self._create_comprehensive_hexagonal_png(hexagons, min_value, max_value, title, subtitle, metric_type, soma_side)
        else:
            return self._create_comprehensive_region_hexagonal_svg(hexagons, min_value, max_value, title, subtitle, metric_type, soma_side)






    def _value_to_color(self, normalized_value: float) -> str:
        """
        Convert normalized value (0-1) to one of 5 distinct colors from lightest to darkest red.

        Args:
            normalized_value: Value between 0 and 1

        Returns:
            Hex color string
        """
        # Define 5 distinct colors from lightest to darkest red
        color_values = [
            (254, 229, 217),  # Lightest (0.0-0.2)
            (252, 187, 161),  # Light (0.2-0.4)
            (252, 146, 114),  # Medium (0.4-0.6)
            (239, 101, 72),   # Dark (0.6-0.8)
            (165, 15, 21)     # Darkest (0.8-1.0)
        ]

        # Determine which color bin the value falls into
        if normalized_value <= 0.2:
            color_index = 0
        elif normalized_value <= 0.4:
            color_index = 1
        elif normalized_value <= 0.6:
            color_index = 2
        elif normalized_value <= 0.8:
            color_index = 3
        else:
            color_index = 4

        r, g, b = color_values[color_index]

        # Convert to hex
        return f"#{r:02x}{g:02x}{b:02x}"


    def _create_comprehensive_region_hexagonal_svg(self, hexagons: List[Dict], min_val: float, max_val: float,
                                                  title: str, subtitle: str, metric_type: str, soma_side: str|None) -> str:
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
            title: Chart title
            subtitle: Chart subtitle
            metric_type: Type of metric being displayed
            soma_side: Side of the soma (left or right)

        Returns:
            SVG content as string rendered from Jinja2 template
        """
        if not hexagons:
            return ""

        # Calculate SVG dimensions
        margin = 10
        number_precision = 2

        # Find bounds
        min_x = min(hex_data['x'] for hex_data in hexagons) - self.hex_size
        max_x = max(hex_data['x'] for hex_data in hexagons) + self.hex_size
        min_y = min(hex_data['y'] for hex_data in hexagons) - self.hex_size
        max_y = max(hex_data['y'] for hex_data in hexagons) + self.hex_size

        width = max_x - min_x + 2 * margin
        height = max_y - min_y + 2 * margin

        # Calculate legend position and ensure width accommodates right-side title and status legend
        legend_width = 12
        if soma_side and soma_side.lower() == 'left':
            legend_x = margin + 5
        else:
            legend_x = width - legend_width - 5 - int(width * 0.1)
        title_x = legend_x + legend_width + 15
        min_width_needed = title_x + 20
        if width < min_width_needed:
            width = min_width_needed

        # Generate hexagon path points
        hex_points = []
        for i in range(6):
            angle = math.pi / 3 * i
            x = self.hex_size * math.cos(angle)
            y = self.hex_size * math.sin(angle)
            hex_points.append(f"{round(x, number_precision)},{round(y, number_precision)}")

        # Process hexagon data with tooltips
        processed_hexagons = []
        for hex_data in hexagons:
            status = hex_data.get('status', 'has_data')

            # Create tooltip text based on status and metric type
            if status == 'not_in_region':
                tooltip = (
                    f"Column: {hex_data['hex1']}, {hex_data['hex2']}\n"
                    f"Status: Not available in {hex_data['region']}"
                )
            elif status == 'no_data':
                tooltip = (
                    f"Column: {hex_data['hex1']}, {hex_data['hex2']}\n"
                    f"Status: No data for current neuron type\n"
                    f"ROI: {hex_data['region']}"
                )
            else:  # has_data
                if metric_type == 'synapse_density':
                    tooltip = (
                        f"Column: {hex_data['hex1']}, {hex_data['hex2']}\n"
                        f"Synapse count: {hex_data['value']}\n"
                        f"ROI: {hex_data['region']} ({soma_side})"
                    )
                else:
                    tooltip = (
                        f"Column: {hex_data['hex1']}, {hex_data['hex2']}\n"
                        f"Cell count: {hex_data['value']}\n"
                        f"ROI: {hex_data['region']}  ({soma_side})"
                    )

            processed_hex = hex_data.copy()
            processed_hex['tooltip'] = tooltip
            processed_hexagons.append(processed_hex)

        # Calculate legend data
        data_hexagons = [h for h in hexagons if h.get('status') == 'has_data']
        legend_data = None

        if data_hexagons:
            legend_height = 60
            legend_y = height - legend_height - 5
            legend_title = "Total Synapses" if metric_type == 'synapse_density' else "Cell Count"
            title_y = legend_y + legend_height // 2
            bin_height = legend_height // 5

            # Calculate threshold values
            thresholds = []
            for i in range(6):
                threshold = min_val + (max_val - min_val) * (i / 5.0)
                thresholds.append(threshold)

            legend_data = {
                'legend_height': legend_height,
                'legend_y': legend_y,
                'legend_title': legend_title,
                'title_y': title_y,
                'bin_height': bin_height,
                'thresholds': thresholds
            }

        # Setup Jinja2 environment
        template_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
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
            **legend_data if legend_data else {}
        )

        return svg_content

    def _create_comprehensive_hexagonal_png(self, hexagons: List[Dict], min_val: float, max_val: float,
                                           title: str, subtitle: str, metric_type: str, soma_side: str|None) -> str:
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
        svg_content = self._create_comprehensive_region_hexagonal_svg(hexagons, min_val, max_val, title, subtitle, metric_type, soma_side)

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

        # Ensure the images directory exists
        images_dir = self.output_dir / "static" / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        # Clean filename and add extension
        clean_filename = filename.replace(" ", "_").replace("(", "").replace(")", "") + ".svg"
        file_path = images_dir / clean_filename

        # Save the SVG file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)

        # Return relative path from HTML location
        return f"static/images/{clean_filename}"

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

        # Ensure the images directory exists
        images_dir = self.output_dir / "static" / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        # Extract base64 data from data URL
        if not png_data_url.startswith('data:image/png;base64,'):
            raise ValueError("Invalid PNG data URL format")

        base64_data = png_data_url.split(',', 1)[1]

        # Clean filename and add extension
        clean_filename = filename.replace(" ", "_").replace("(", "").replace(")", "") + ".png"
        file_path = images_dir / clean_filename

        # Save the PNG file
        import base64
        with open(file_path, 'wb') as f:
            f.write(base64.b64decode(base64_data))

        # Return relative path from HTML location
        return f"static/images/{clean_filename}"
