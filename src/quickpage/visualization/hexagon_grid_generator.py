"""
Hexagon grid generator for visualizing column data.

This module provides hexagon grid generation functionality supporting both SVG
and PNG output formats using pygal for enhanced visualization capabilities.
"""

import math
import colorsys
from typing import Dict, Any, Optional, List, Tuple
import pygal
from pygal.style import Style
import tempfile
import os


class HexagonGridGenerator:
    """
    Generate hexagonal grid visualizations for column data.

    Supports both SVG and PNG output formats with consistent styling and
    color mapping across different metrics and regions.
    """

    def __init__(self, hex_size: int = 6, spacing_factor: float = 1.1):
        """
        Initialize the hexagon grid generator.

        Args:
            hex_size: Size of individual hexagons
            spacing_factor: Spacing between hexagons
        """
        self.hex_size = hex_size
        self.spacing_factor = spacing_factor
        self.colors = [
            '#fee5d9',  # Lightest (0.0-0.2)
            '#fcbba1',  # Light (0.2-0.4)
            '#fc9272',  # Medium (0.4-0.6)
            '#ef6548',  # Dark (0.6-0.8)
            '#a50f15'   # Darkest (0.8-1.0)
        ]

    def generate_region_hexagonal_grids(self, column_summary: List[Dict],
                                      neuron_type: str, soma_side: str,
                                      output_format: str = 'svg') -> Dict[str, Dict[str, str]]:
        """
        Generate separate hexagonal grid visualizations for each region (ME, LO, LOP).

        Args:
            column_summary: List of column data dictionaries
            neuron_type: Type of neuron being visualized
            soma_side: Side of soma (left/right)
            output_format: Output format ('svg' or 'png')

        Returns:
            Dictionary mapping region names to visualization data
        """
        if not column_summary:
            return {}

        # Calculate global ranges for consistent color scaling
        global_synapse_min = min(col['total_synapses'] for col in column_summary)
        global_synapse_max = max(col['total_synapses'] for col in column_summary)
        global_cell_min = min(col['neuron_count'] for col in column_summary)
        global_cell_max = max(col['neuron_count'] for col in column_summary)

        # Group columns by region
        regions = {}
        for col in column_summary:
            region = col['region']
            if region not in regions:
                regions[region] = []
            regions[region].append(col)

        region_grids = {}

        # Generate grids for each region with global scaling
        for region, region_columns in regions.items():
            region_grids[region] = {
                'synapse_density': self.generate_single_region_grid(
                    region_columns, 'synapse_density', region,
                    global_synapse_min, global_synapse_max,
                    neuron_type, soma_side, output_format
                ),
                'cell_count': self.generate_single_region_grid(
                    region_columns, 'cell_count', region,
                    global_cell_min, global_cell_max,
                    neuron_type, soma_side, output_format
                )
            }

        return region_grids

    def generate_single_region_grid(self, region_columns: List[Dict],
                                   metric_type: str, region_name: str,
                                   global_min: Optional[float] = None,
                                   global_max: Optional[float] = None,
                                   neuron_type: Optional[str] = None,
                                   soma_side: Optional[str] = None,
                                   output_format: str = 'svg') -> str:
        """
        Generate hexagonal grid for a single region with specified metric.

        Args:
            region_columns: List of column data for the region
            metric_type: 'synapse_density' or 'cell_count'
            region_name: Name of the region (ME, LO, LOP)
            global_min: Global minimum value for consistent color scaling
            global_max: Global maximum value for consistent color scaling
            neuron_type: Type of neuron
            soma_side: Side of soma
            output_format: Output format ('svg' or 'png')

        Returns:
            Generated visualization content as string
        """
        if not region_columns:
            return ""

        # Calculate coordinate ranges
        min_hex1 = min(col['hex1_dec'] for col in region_columns)
        max_hex1 = max(col['hex1_dec'] for col in region_columns)
        min_hex2 = min(col['hex2_dec'] for col in region_columns)
        max_hex2 = max(col['hex2_dec'] for col in region_columns)

        # Choose metric and use global range for consistent color scaling
        if metric_type == 'synapse_density':
            values = [col['total_synapses'] for col in region_columns]
            title = f"{region_name} Synapses"
            subtitle = f"{neuron_type} ({soma_side.upper()[:1] if soma_side else ''})"
            min_value = global_min if global_min is not None else min(values)
            max_value = global_max if global_max is not None else max(values)
        else:  # cell_count
            values = [col['neuron_count'] for col in region_columns]
            title = f"{region_name} Cell Count"
            subtitle = f"{neuron_type} ({soma_side.upper()[:1] if soma_side else ''})"
            min_value = global_min if global_min is not None else min(values)
            max_value = global_max if global_max is not None else max(values)

        value_range = max_value - min_value if max_value > min_value else 1

        # Create hexagonal grid coordinates
        hexagons = []
        for col in region_columns:
            # Convert hex1/hex2 to hexagonal grid coordinates
            hex1_coord = col['hex1_dec'] - min_hex1
            hex2_coord = col['hex2_dec'] - min_hex2

            # Map to axial coordinates (q, r) for hexagonal grid positioning
            q = -(hex1_coord - hex2_coord) - 3
            r = -hex2_coord

            # Convert to pixel coordinates using proper hexagonal spacing
            x = self.hex_size * self.spacing_factor * (3/2 * q)
            y = self.hex_size * self.spacing_factor * (math.sqrt(3)/2 * q + math.sqrt(3) * r)

            # Get metric value and normalize
            if metric_type == 'synapse_density':
                metric_value = col['total_synapses']
            else:  # cell_count
                metric_value = col['neuron_count']

            normalized_value = (metric_value - min_value) / value_range
            color = self._value_to_color(normalized_value)

            hexagons.append({
                'x': x,
                'y': y,
                'value': metric_value,
                'color': color,
                'region': col['region'],
                'side': col['side'],
                'hex1': col['hex1'],
                'hex2': col['hex2'],
                'neuron_count': col['neuron_count'],
                'column_name': col['column_name'],
                'synapse_value': col['total_synapses']
            })

        # Generate visualization based on format
        if output_format.lower() == 'png':
            return self._create_hexagonal_png(hexagons, min_value, max_value, title, subtitle, metric_type)
        else:
            return self._create_region_hexagonal_svg(hexagons, min_value, max_value, title, subtitle, metric_type)

    def create_hexagonal_visualization(self, hexagons: List[Dict],
                                     min_val: float, max_val: float,
                                     neuron_type: Optional[str] = None,
                                     output_format: str = 'svg') -> str:
        """
        Create hexagonal visualization in specified format.

        Args:
            hexagons: List of hexagon data dictionaries
            min_val: Minimum value for color scaling
            max_val: Maximum value for color scaling
            neuron_type: Type of neuron for title
            output_format: Output format ('svg' or 'png')

        Returns:
            Generated visualization content as string
        """
        if output_format.lower() == 'png':
            title = "Column Organization Grid"
            subtitle = f"Hex1 ↑ Upward, Hex2 ↗ Upward-Right, Color = Total Synapses, Type = {neuron_type}" if neuron_type else "Hex1 ↑ Upward, Hex2 ↗ Upward-Right, Color = Total Synapses"
            return self._create_hexagonal_png(hexagons, min_val, max_val, title, subtitle, "synapse_density")
        else:
            return self._create_hexagonal_svg(hexagons, min_val, max_val, neuron_type)

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

    def _create_hexagonal_png(self, hexagons: List[Dict], min_val: float, max_val: float,
                             title: str, subtitle: str, metric_type: str) -> str:
        """
        Create PNG representation of hexagonal grid using pygal.

        Args:
            hexagons: List of hexagon data dictionaries
            min_val: Minimum value for scaling
            max_val: Maximum value for scaling
            title: Chart title
            subtitle: Chart subtitle
            metric_type: Type of metric being displayed

        Returns:
            Base64 encoded PNG data
        """
        if not hexagons:
            return ""

        # Create custom style for hexagon visualization
        custom_style = Style(
            background='#f8f9fa',
            plot_background='#f8f9fa',
            foreground='#333333',
            foreground_strong='#000000',
            foreground_subtle='#666666',
            colors=self.colors,
            font_family='Arial, sans-serif',
            title_font_size=12,
            label_font_size=8,
            major_label_font_size=10,
            value_font_size=8,
            legend_font_size=8
        )

        # Create XY chart for scatter plot representation
        chart = pygal.XY(
            title=f"{title} - {subtitle}",
            style=custom_style,
            width=800,
            height=600,
            show_legend=True,
            x_title="X Coordinate",
            y_title="Y Coordinate",
            print_values=False,
            dots_size=self.hex_size * 2,
            stroke_style={'width': 0},
            show_x_guides=False,
            show_y_guides=False,
            show_x_labels=False,
            show_y_labels=False
        )

        # Group hexagons by color for legend
        color_groups = {}
        value_range = max_val - min_val if max_val > min_val else 1

        for hex_data in hexagons:
            normalized_value = (hex_data['value'] - min_val) / value_range

            # Determine color group
            if normalized_value <= 0.2:
                group_name = f"Low ({min_val:.0f} - {min_val + 0.2 * value_range:.0f})"
                group_index = 0
            elif normalized_value <= 0.4:
                group_name = f"Low-Med ({min_val + 0.2 * value_range:.0f} - {min_val + 0.4 * value_range:.0f})"
                group_index = 1
            elif normalized_value <= 0.6:
                group_name = f"Medium ({min_val + 0.4 * value_range:.0f} - {min_val + 0.6 * value_range:.0f})"
                group_index = 2
            elif normalized_value <= 0.8:
                group_name = f"Med-High ({min_val + 0.6 * value_range:.0f} - {min_val + 0.8 * value_range:.0f})"
                group_index = 3
            else:
                group_name = f"High ({min_val + 0.8 * value_range:.0f} - {max_val:.0f})"
                group_index = 4

            if group_name not in color_groups:
                color_groups[group_name] = {'points': [], 'index': group_index}

            # Create tooltip text
            if metric_type == 'synapse_density':
                tooltip = (f"{hex_data['column_name']}, "
                          f"Region: {hex_data['region']} {hex_data['side']}, "
                          f"Hex1: {hex_data['hex1']} Hex2: {hex_data['hex2']}, "
                          f"Neurons: {hex_data['neuron_count']}, "
                          f"Total Synapses: {hex_data['value']}")
            else:
                tooltip = (f"{hex_data['column_name']}, "
                          f"Region: {hex_data['region']} {hex_data['side']}, "
                          f"Hex1: {hex_data['hex1']} Hex2: {hex_data['hex2']}, "
                          f"Cell Count: {hex_data['value']}, "
                          f"Total Synapses: {hex_data['synapse_value']}")

            color_groups[group_name]['points'].append({
                'value': (hex_data['x'], hex_data['y']),
                'label': tooltip
            })

        # Add series to chart, ordered by color intensity
        for group_name in sorted(color_groups.keys(), key=lambda x: color_groups[x]['index']):
            group_data = color_groups[group_name]
            chart.add(group_name, group_data['points'])

        # Generate PNG and return as base64
        png_data = chart.render_to_png()
        if png_data:
            import base64
            return base64.b64encode(png_data).decode('utf-8')
        return ""

    def _create_region_hexagonal_svg(self, hexagons: List[Dict], min_val: float, max_val: float,
                                   title: str, subtitle: str, metric_type: str) -> str:
        """
        Create SVG representation of hexagonal grid for a specific region.

        Args:
            hexagons: List of hexagon data dictionaries
            min_val: Minimum value for scaling
            max_val: Maximum value for scaling
            title: Chart title
            subtitle: Chart subtitle
            metric_type: Type of metric being displayed

        Returns:
            SVG content as string
        """
        if not hexagons:
            return ""

        # Calculate SVG dimensions
        margin = 10

        # Find bounds
        min_x = min(hex_data['x'] for hex_data in hexagons) - self.hex_size
        max_x = max(hex_data['x'] for hex_data in hexagons) + self.hex_size
        min_y = min(hex_data['y'] for hex_data in hexagons) - self.hex_size
        max_y = max(hex_data['y'] for hex_data in hexagons) + self.hex_size

        width = max_x - min_x + 2 * margin
        height = max_y - min_y + 2 * margin

        # Calculate legend position and ensure width accommodates right-side title
        legend_width = 12
        legend_x = width - legend_width - 5 - int(width * 0.1)
        title_x = legend_x + legend_width + 15
        min_width_needed = title_x + 20
        if width < min_width_needed:
            width = min_width_needed

        # Start SVG
        svg_parts = [
            f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
            f'<defs>',
            f'<style>',
            f'.hex-tooltip {{ font-family: Arial, sans-serif; font-size: 12px; }}',
            f'</style>',
            f'</defs>'
        ]

        # Add background
        svg_parts.append(f'<rect width="{width}" height="{height}" fill="#f8f9fa" stroke="none"/>')

        # Add title
        svg_parts.append(f'<text x="5" y="15" text-anchor="start" font-family="Arial, sans-serif" font-size="12" fill="#CCCCCC">{title}</text>')
        svg_parts.append(f'<text x="5" y="28" text-anchor="start" font-family="Arial, sans-serif" font-size="10" fill="#CCCCCC">{subtitle}</text>')

        # Generate hexagon path
        hex_points = []
        for i in range(6):
            angle = math.pi / 3 * i
            x = self.hex_size * math.cos(angle)
            y = self.hex_size * math.sin(angle)
            hex_points.append(f"{x},{y}")
        hex_path = "M" + " L".join(hex_points) + " Z"

        # Draw hexagons
        for hex_data in hexagons:
            x = hex_data['x'] - min_x + margin
            y = hex_data['y'] - min_y + margin
            color = hex_data['color']

            # Create tooltip text based on metric type
            if metric_type == 'synapse_density':
                tooltip = (f"{hex_data['column_name']}\\n"
                          f"Region: {hex_data['region']} {hex_data['side']}\\n"
                          f"Hex1: {hex_data['hex1']} Hex2: {hex_data['hex2']}\\n"
                          f"Neurons: {hex_data['neuron_count']}\\n"
                          f"Total Synapses: {hex_data['value']}")
            else:
                tooltip = (f"{hex_data['column_name']}\\n"
                          f"Region: {hex_data['region']} {hex_data['side']}\\n"
                          f"Hex1: {hex_data['hex1']} Hex2: {hex_data['hex2']}\\n"
                          f"Cell Count: {hex_data['value']}\\n"
                          f"Total Synapses: {hex_data['synapse_value']}")

            # Draw hexagon
            svg_parts.append(
                f'<g transform="translate({x},{y})">'
                f'<path d="{hex_path}" '
                f'fill="{color}" '
                f'stroke="none" '
                f'opacity="0.8">'
                f'<title>{tooltip}</title>'
                f'</path>'
                f'</g>'
            )

        # Add color legend
        legend_height = 60
        legend_y = height - legend_height - 5

        legend_title = "Total Synapses" if metric_type == 'synapse_density' else "Cell Count"
        title_y = legend_y + legend_height // 2
        svg_parts.append(f'<text x="{title_x}" y="{title_y}" font-family="Arial, sans-serif" font-size="8" font-weight="bold" text-anchor="middle" transform="rotate(-90 {title_x} {title_y})">{legend_title}</text>')

        # Create discrete color legend with 5 bins
        bin_height = legend_height // 5

        # Calculate threshold values
        thresholds = []
        for i in range(6):
            threshold = min_val + (max_val - min_val) * (i / 5.0)
            thresholds.append(threshold)

        # Draw 5 discrete color rectangles
        for i, color in enumerate(self.colors):
            rect_y = legend_y + legend_height - (i + 1) * bin_height
            svg_parts.append(f'<rect x="{legend_x}" y="{rect_y}" width="{legend_width}" height="{bin_height}" fill="{color}" stroke="#999999" stroke-width="0.2"/>')

        # Add threshold labels
        for i, threshold in enumerate(thresholds):
            label_y = legend_y + legend_height - i * bin_height
            svg_parts.append(f'<text x="{legend_x - 3}" y="{label_y + 3}" font-family="Arial, sans-serif" text-anchor="end" font-size="8">{threshold:.0f}</text>')

        svg_parts.append('</svg>')
        return ''.join(svg_parts)

    def _create_hexagonal_svg(self, hexagons: List[Dict], min_val: float, max_val: float,
                             neuron_type: Optional[str] = None) -> str:
        """
        Create SVG representation of hexagonal grid.

        Args:
            hexagons: List of hexagon data dictionaries
            min_val: Minimum value for scaling
            max_val: Maximum value for scaling
            neuron_type: Type of neuron for title

        Returns:
            SVG content as string
        """
        if not hexagons:
            return ""

        # Calculate SVG dimensions
        margin = 10

        # Find bounds
        min_x = min(hex_data['x'] for hex_data in hexagons) - self.hex_size
        max_x = max(hex_data['x'] for hex_data in hexagons) + self.hex_size
        min_y = min(hex_data['y'] for hex_data in hexagons) - self.hex_size
        max_y = max(hex_data['y'] for hex_data in hexagons) + self.hex_size

        width = max_x - min_x + 2 * margin
        height = max_y - min_y + 2 * margin

        # Calculate legend position
        legend_width = 12
        legend_x = width - legend_width - 5 - int(width * 0.1)
        title_x = legend_x + legend_width + 15
        min_width_needed = title_x + 20
        if width < min_width_needed:
            width = min_width_needed

        # Start SVG
        svg_parts = [
            f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
            f'<defs>',
            f'<style>',
            f'.hex-tooltip {{ font-family: Arial, sans-serif; font-size: 12px; }}',
            f'</style>',
            f'</defs>'
        ]

        # Add background
        svg_parts.append(f'<rect width="{width}" height="{height}" fill="#f8f9fa" stroke="none"/>')

        # Add title
        svg_parts.append(f'<text x="{width/2}" y="20" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" font-weight="bold">Column Organization Grid</text>')
        subtitle = f"Hex1 ↑ Upward, Hex2 ↗ Upward-Right, Color = Total Synapses, Type = {neuron_type}" if neuron_type else "Hex1 ↑ Upward, Hex2 ↗ Upward-Right, Color = Total Synapses"
        svg_parts.append(f'<text x="{width/2}" y="35" text-anchor="middle" font-family="Arial, sans-serif" font-size="10">{subtitle}</text>')

        # Generate hexagon path
        hex_points = []
        for i in range(6):
            angle = math.pi / 3 * i
            x = self.hex_size * math.cos(angle)
            y = self.hex_size * math.sin(angle)
            hex_points.append(f"{x},{y}")
        hex_path = "M" + " L".join(hex_points) + " Z"

        # Draw hexagons
        for hex_data in hexagons:
            x = hex_data['x'] - min_x + margin
            y = hex_data['y'] - min_y + margin
            color = hex_data['color']

            # Create tooltip text
            tooltip = (f"{hex_data['column_name']}\\n"
                      f"Region: {hex_data['region']} {hex_data['side']}\\n"
                      f"Hex1: {hex_data['hex1']} Hex2: {hex_data['hex2']}\\n"
                      f"Neurons: {hex_data['neuron_count']}\\n"
                      f"Total Synapses: {hex_data['value']}")

            # Draw hexagon
            svg_parts.append(
                f'<g transform="translate({x},{y})">'
                f'<path d="{hex_path}" '
                f'fill="{color}" '
                f'stroke="none" '
                f'opacity="0.8">'
                f'<title>{tooltip}</title>'
                f'</path>'
                f'</g>'
            )

        # Add color legend
        legend_height = 60
        legend_y = height - legend_height - 5

        title_y = legend_y + legend_height // 2
        svg_parts.append(f'<text x="{title_x}" y="{title_y}" font-family="Arial, sans-serif" font-size="8" font-weight="bold" text-anchor="middle" transform="rotate(-90 {title_x} {title_y})">Total Synapses</text>')

        # Create discrete color legend with 5 bins
        bin_height = legend_height // 5

        # Calculate threshold values
        thresholds = []
        for i in range(6):
            threshold = min_val + (max_val - min_val) * (i / 5.0)
            thresholds.append(threshold)

        # Draw 5 discrete color rectangles
        for i, color in enumerate(self.colors):
            rect_y = legend_y + legend_height - (i + 1) * bin_height
            svg_parts.append(f'<rect x="{legend_x}" y="{rect_y}" width="{legend_width}" height="{bin_height}" fill="{color}" stroke="none"/>')

        # Add threshold labels
        for i, threshold in enumerate(thresholds):
            label_y = legend_y + legend_height - i * bin_height
            svg_parts.append(f'<text x="{legend_x + legend_width + 3}" y="{label_y + 3}" font-family="Arial, sans-serif" font-size="8">{threshold:.0f}</text>')

        svg_parts.append('</svg>')
        return ''.join(svg_parts)
