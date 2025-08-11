"""
Hexagon grid generator for visualizing column data.

This module provides hexagon grid generation functionality supporting both SVG
and PNG output formats using pygal for enhanced visualization capabilities.
"""

import math
import colorsys
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
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

    def generate_region_hexagonal_grids(self, column_summary: List[Dict],
                                      neuron_type: str, soma_side: str,
                                      output_format: str = 'svg',
                                      save_to_files: bool = False) -> Dict[str, Dict[str, str]]:
        """
        Generate separate hexagonal grid visualizations for each region (ME, LO, LOP).

        Args:
            column_summary: List of column data dictionaries
            neuron_type: Type of neuron being visualized
            soma_side: Side of soma (left/right)
            output_format: Output format ('svg' or 'png')
            save_to_files: If True, save files to output/static/images and return file paths.
                          If False, return content directly for embedding in HTML.

        Returns:
            Dictionary mapping region names to visualization data (either file paths or content)
        """
        # Set embed mode based on save_to_files parameter
        self.embed_mode = not save_to_files

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

        # Generate grids for each region with global scaling in specific order
        region_order = ['ME', 'LO', 'LOP']
        for region in region_order:
            if region not in regions:
                continue
            region_columns = regions[region]
            synapse_content = self.generate_single_region_grid(
                region_columns, 'synapse_density', region,
                global_synapse_min, global_synapse_max,
                neuron_type, soma_side, output_format
            )
            cell_content = self.generate_single_region_grid(
                region_columns, 'cell_count', region,
                global_cell_min, global_cell_max,
                neuron_type, soma_side, output_format
            )

            if save_to_files and self.output_dir and not self.embed_mode:
                # Save files and return paths
                if output_format == 'svg':
                    synapse_path = self._save_svg_file(synapse_content, f"{region}_{neuron_type}_{soma_side}_synapse_density")
                    cell_path = self._save_svg_file(cell_content, f"{region}_{neuron_type}_{soma_side}_cell_count")
                elif output_format == 'png':
                    synapse_path = self._save_png_file(synapse_content, f"{region}_{neuron_type}_{soma_side}_synapse_density")
                    cell_path = self._save_png_file(cell_content, f"{region}_{neuron_type}_{soma_side}_cell_count")
                else:
                    raise ValueError(f"Unsupported output format: {output_format}")

                region_grids[region] = {
                    'synapse_density': synapse_path,
                    'cell_count': cell_path
                }
            else:
                # Return content directly for embedding - do not save any files
                region_grids[region] = {
                    'synapse_density': synapse_content,
                    'cell_count': cell_content
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
        Create PNG representation of hexagonal grid using PIL to draw actual hexagons.

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

        try:
            from PIL import Image, ImageDraw, ImageFont
            import math
            import io
            import base64
        except ImportError:
            # Fall back to empty image if PIL is not available
            return ""

        # Calculate image dimensions
        margin = 20
        title_height = 60

        # Find bounds
        min_x = min(hex_data['x'] for hex_data in hexagons) - self.hex_size
        max_x = max(hex_data['x'] for hex_data in hexagons) + self.hex_size
        min_y = min(hex_data['y'] for hex_data in hexagons) - self.hex_size
        max_y = max(hex_data['y'] for hex_data in hexagons) + self.hex_size

        width = int(max_x - min_x + 2 * margin)
        height = int(max_y - min_y + 2 * margin + title_height)

        # Create image
        image = Image.new('RGB', (width, height), '#f8f9fa')
        draw = ImageDraw.Draw(image)

        # Try to load a font, fall back to default if not available
        try:
            font = ImageFont.load_default()
            title_font = ImageFont.load_default()
        except:
            font = None
            title_font = None

        # Draw title
        title_text = f"{title} - {subtitle}"
        if font:
            draw.text((width // 2, 10), title_text, fill='#333333', font=title_font, anchor='mt')
            draw.text((width // 2, 30), f"Color represents {metric_type}", fill='#666666', font=font, anchor='mt')
        else:
            draw.text((width // 2 - len(title_text) * 3, 10), title_text, fill='#333333')

        # Generate hexagon vertices function
        def get_hexagon_points(center_x, center_y, size):
            points = []
            for i in range(6):
                angle = math.pi / 3 * i
                x = center_x + size * math.cos(angle)
                y = center_y + size * math.sin(angle)
                points.append((x, y))
            return points

        # Draw hexagons
        value_range = max_val - min_val if max_val > min_val else 1

        for hex_data in hexagons:
            # Calculate position
            x = hex_data['x'] - min_x + margin
            y = hex_data['y'] - min_y + margin + title_height

            # Calculate color based on value
            normalized_value = (hex_data['value'] - min_val) / value_range if value_range > 0 else 0
            color = self._value_to_color(normalized_value)

            # Convert hex color to RGB tuple
            if color.startswith('#'):
                color = color[1:]
                rgb_color = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            else:
                rgb_color = (128, 128, 128)  # Default gray

            # Get hexagon points
            hex_points = get_hexagon_points(x, y, self.hex_size * 0.8)

            # Draw hexagon
            draw.polygon(hex_points, fill=rgb_color, outline='#333333', width=1)

            # Draw label if hexagon is large enough
            if self.hex_size > 8:
                label = f"{hex_data['hex1']},{hex_data['hex2']}"
                if font:
                    # Get text bbox to center it
                    bbox = draw.textbbox((0, 0), label, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    draw.text((x - text_width // 2, y - text_height // 2), label,
                             fill='white', font=font)
                else:
                    draw.text((x - len(label) * 2, y - 4), label, fill='white')

        # Add color legend
        legend_x = width - 100
        legend_y = title_height + 20
        legend_height = min(200, height - title_height - 40)

        if legend_height > 50:
            # Draw legend background
            draw.rectangle([legend_x - 10, legend_y - 10, width - 10, legend_y + legend_height + 10],
                          fill='white', outline='#cccccc')

            # Draw legend title
            if font:
                draw.text((legend_x, legend_y), 'Values', fill='#333333', font=title_font)
            else:
                draw.text((legend_x, legend_y), 'Values', fill='#333333')

            # Draw legend color bars
            legend_steps = 5
            step_height = (legend_height - 30) // legend_steps

            for i in range(legend_steps):
                y_pos = legend_y + 20 + i * step_height
                normalized = i / (legend_steps - 1)
                color = self._value_to_color(normalized)

                # Convert to RGB
                if color.startswith('#'):
                    color = color[1:]
                    rgb_color = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
                else:
                    rgb_color = (128, 128, 128)

                # Draw color bar
                draw.rectangle([legend_x, y_pos, legend_x + 20, y_pos + step_height - 2],
                              fill=rgb_color)

                # Draw value label
                value = min_val + normalized * value_range
                value_text = f"{value:.0f}"
                if font:
                    draw.text((legend_x + 25, y_pos), value_text, fill='#333333', font=font)
                else:
                    draw.text((legend_x + 25, y_pos), value_text, fill='#333333')

        # Convert to PNG bytes
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG', optimize=True)
        img_buffer.seek(0)

        # Encode as base64 data URL
        base64_data = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{base64_data}"

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
