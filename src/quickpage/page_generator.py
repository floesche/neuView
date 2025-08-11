"""
HTML page generator using Jinja2 templates.

This module provides comprehensive HTML page generation functionality for
neuron type reports, including template rendering, static file management,
and output directory organization.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import pandas as pd
import shutil
import pygal
import math
import colorsys

from .config import Config


class PageGenerator:
    """
    Generate HTML pages for neuron types.

    This class handles the complete page generation process including template
    rendering, static file copying, and output file management.
    """

    def __init__(self, config: Config, output_dir: str):
        """
        Initialize the page generator.

        Args:
            config: Configuration object with template and output settings
            output_dir: Directory path for generated HTML files
        """
        self.config = config
        self.output_dir = Path(output_dir)
        self.template_dir = Path(config.output.template_dir)

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Copy static files to output directory
        self._copy_static_files()

        # Initialize Jinja2 environment
        self._setup_jinja_env()

    def _copy_static_files(self):
        """Copy static CSS and JS files to the output directory."""
        # Get the project root directory (where static files are stored)
        project_root = Path(__file__).parent.parent.parent
        static_dir = project_root / 'static'

        if not static_dir.exists():
            return  # Skip if static directory doesn't exist

        # Create static directories in output
        output_static_dir = self.output_dir / 'static'
        output_css_dir = output_static_dir / 'css'
        output_js_dir = output_static_dir / 'js'

        output_css_dir.mkdir(parents=True, exist_ok=True)
        output_js_dir.mkdir(parents=True, exist_ok=True)

        # Copy CSS files
        css_source_dir = static_dir / 'css'
        if css_source_dir.exists():
            for css_file in css_source_dir.glob('*.css'):
                shutil.copy2(css_file, output_css_dir / css_file.name)

        # Copy JS files
        js_source_dir = static_dir / 'js'
        if js_source_dir.exists():
            for js_file in js_source_dir.glob('*.js'):
                shutil.copy2(js_file, output_js_dir / js_file.name)

    def _setup_jinja_env(self):
        """Set up Jinja2 environment with templates."""
        # Create template directory if it doesn't exist
        self.template_dir.mkdir(parents=True, exist_ok=True)

        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )

        # Add custom filters
        self.env.filters['format_number'] = self._format_number
        self.env.filters['format_percentage'] = self._format_percentage
        self.env.filters['abbreviate_neurotransmitter'] = self._abbreviate_neurotransmitter


    def generate_page(self, neuron_type: str, neuron_data: Dict[str, Any],
                     soma_side: str) -> str:
        """
        Generate an HTML page for a neuron type.

        Args:
            neuron_type: The neuron type name
            neuron_data: Data returned from NeuPrintConnector
            soma_side: Soma side filter used

        Returns:
            Path to the generated HTML file
        """
        # Load template
        template = self.env.get_template('neuron_page.html')

        # Analyze column-based ROI data for neurons with column assignments
        column_analysis = self._analyze_column_roi_data(
            neuron_data.get('roi_counts'),
            neuron_data.get('neurons'),
            soma_side,
            neuron_type
        )

        # Prepare template context
        context = {
            'config': self.config,
            'neuron_data': neuron_data,
            'neuron_type': neuron_type,
            'soma_side': soma_side,
            'summary': neuron_data['summary'],
            'neurons_df': neuron_data['neurons'],
            'connectivity': neuron_data.get('connectivity', {}),
            'column_analysis': column_analysis,
            'generation_time': datetime.now()
        }

        # Render template
        html_content = template.render(**context)

        # Generate output filename
        output_filename = self._generate_filename(neuron_type, soma_side)
        output_path = self.output_dir / output_filename

        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(output_path)

    def generate_page_from_neuron_type(self, neuron_type_obj, connector=None):
        """
        Generate an HTML page from a NeuronType object.

        Args:
            neuron_type_obj: NeuronType instance with data

        Returns:
            Path to the generated HTML file
        """
        # Import here to avoid circular imports
        from .neuron_type import NeuronType

        if not isinstance(neuron_type_obj, NeuronType):
            raise TypeError("Expected NeuronType object")

        # Load template
        template = self.env.get_template('neuron_page.html')

        # Get data from neuron type object
        neuron_data = neuron_type_obj.to_dict()

        # Aggregate ROI data across neurons matching this soma side only
        roi_summary = self._aggregate_roi_data(
            neuron_data.get('roi_counts'),
            neuron_data.get('neurons'),
            neuron_type_obj.soma_side,
            connector
        )

        # Analyze column-based ROI data for neurons with column assignments
        column_analysis = self._analyze_column_roi_data(
            neuron_data.get('roi_counts'),
            neuron_data.get('neurons'),
            neuron_type_obj.soma_side,
            neuron_type_obj.name
        )

        # Prepare template context
        context = {
            'config': self.config,
            'neuron_data': neuron_data,
            'neuron_type': neuron_type_obj.name,
            'soma_side': neuron_type_obj.soma_side,
            'summary': neuron_data['summary'],
            'neurons_df': neuron_data['neurons'],
            'connectivity': neuron_data.get('connectivity', {}),
            'roi_summary': roi_summary,
            'column_analysis': column_analysis,
            'generation_time': datetime.now(),
            'neuron_type_obj': neuron_type_obj  # Provide access to the object itself
        }

        # Render template
        html_content = template.render(**context)

        # Generate output filename
        output_filename = self._generate_filename(neuron_type_obj.name, neuron_type_obj.soma_side)
        output_path = self.output_dir / output_filename

        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Generate JSON file if enabled
        if self.config.output.generate_json:
            from .json_generator import JsonGenerator
            json_generator = JsonGenerator(self.config, str(self.output_dir))
            json_output_path = json_generator.generate_json_from_neuron_type(neuron_type_obj)
            if json_output_path:
                return f"{str(output_path)}, JSON: {json_output_path}"

        return str(output_path)

    def _aggregate_roi_data(self, roi_counts_df, neurons_df, soma_side, connector=None):
        """Aggregate ROI data across neurons matching the specific soma side to get total pre/post synapses per ROI (primary ROIs only)."""
        if roi_counts_df is None or roi_counts_df.empty or neurons_df is None or neurons_df.empty:
            return []

        # Filter ROI data to include only neurons that belong to this specific soma side
        if 'bodyId' in neurons_df.columns and 'bodyId' in roi_counts_df.columns:
            # Get bodyIds of neurons that match this soma side
            soma_side_body_ids = set(neurons_df['bodyId'].values)
            # Filter ROI counts to include only these neurons
            roi_counts_soma_filtered = roi_counts_df[roi_counts_df['bodyId'].isin(soma_side_body_ids)]
        else:
            # If bodyId columns are not available, fall back to using all ROI data
            # This shouldn't happen in normal operation but provides a safety net
            roi_counts_soma_filtered = roi_counts_df

        if roi_counts_soma_filtered.empty:
            return []

        # Get dataset-aware primary ROIs
        primary_rois = self._get_primary_rois(connector)

        # Filter ROI counts to include only primary ROIs
        if len(primary_rois) > 0:
            roi_counts_filtered = roi_counts_soma_filtered[roi_counts_soma_filtered['roi'].isin(primary_rois)]
        else:
            # If no primary ROIs available, return empty
            return []

        if roi_counts_filtered.empty:
            return []

        # Group by ROI and sum pre/post synapses across all neurons
        roi_aggregated = roi_counts_filtered.groupby('roi').agg({
            'pre': 'sum',
            'post': 'sum',
            'downstream': 'sum',
            'upstream': 'sum'
        }).reset_index()

        # Calculate total synapses per ROI
        roi_aggregated['total'] = roi_aggregated['pre'] + roi_aggregated['post']

        # Calculate total pre-synapses across all ROIs for percentage calculation
        total_pre_synapses = roi_aggregated['pre'].sum()

        # Calculate percentage of pre-synapses for each ROI
        if total_pre_synapses > 0:
            roi_aggregated['pre_percentage_precise'] = roi_aggregated['pre'] / total_pre_synapses * 100
            roi_aggregated['pre_percentage'] = roi_aggregated['pre_percentage_precise'].round(1)
        else:
            roi_aggregated['pre_percentage_precise'] = 0.0
            roi_aggregated['pre_percentage'] = 0.0

        total_post_synapses = roi_aggregated['post'].sum()

        # Calculate percentage of post-synapses for each ROI
        if total_post_synapses > 0:
            roi_aggregated['post_percentage_precise'] = roi_aggregated['post'] / total_post_synapses * 100
            roi_aggregated['post_percentage'] = roi_aggregated['post_percentage_precise'].round(1)
        else:
            roi_aggregated['post_percentage_precise'] = 0.0
            roi_aggregated['post_percentage'] = 0.0

        # Sort by total synapses (descending) to show most innervated ROIs first
        roi_aggregated = roi_aggregated.sort_values('total', ascending=False)

        # Convert to list of dictionaries for template
        roi_summary = []
        for _, row in roi_aggregated.iterrows():
            roi_summary.append({
                'name': row['roi'],
                'pre': int(row['pre']),
                'post': int(row['post']),
                'total': int(row['total']),
                'pre_percentage': float(row['pre_percentage']),
                'post_percentage': float(row['post_percentage']),
                'pre_percentage_precise': float(row['pre_percentage_precise']),
                'post_percentage_precise': float(row['post_percentage_precise']),
                'downstream': int(row['downstream']),
                'upstream': int(row['upstream'])
            })

        return roi_summary

    def _analyze_column_roi_data(self, roi_counts_df, neurons_df, soma_side, neuron_type):
        """
        Analyze ROI data for column-based regions matching pattern (ME|LO|LOP)_[RL]_col_hex1_hex2.
        Returns additional table with mean synapses per column per neuron type.
        """
        import re

        if roi_counts_df is None or roi_counts_df.empty or neurons_df is None or neurons_df.empty:
            return None

        # Filter ROI data to include only neurons that belong to this specific soma side
        if 'bodyId' in neurons_df.columns and 'bodyId' in roi_counts_df.columns:
            soma_side_body_ids = set(neurons_df['bodyId'].values)
            roi_counts_soma_filtered = roi_counts_df[roi_counts_df['bodyId'].isin(soma_side_body_ids)]
        else:
            roi_counts_soma_filtered = roi_counts_df

        if roi_counts_soma_filtered.empty:
            return None

        # Pattern to match column ROIs: (ME|LO|LOP)_[RL]_col_hex1_hex2
        column_pattern = r'^(ME|LO|LOP)_([RL])_col_([A-Za-z0-9]+)_([A-Za-z0-9]+)$'

        # Filter ROIs that match the column pattern
        column_rois = roi_counts_soma_filtered[
            roi_counts_soma_filtered['roi'].str.match(column_pattern, na=False)
        ].copy()

        if column_rois.empty:
            return None

        # Extract column information
        roi_info = []
        for _, row in column_rois.iterrows():
            match = re.match(column_pattern, row['roi'])
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

                roi_info.append({
                    'roi': row['roi'],
                    'bodyId': row['bodyId'],
                    'region': region,
                    'side': side,
                    'hex1': coord1,
                    'hex2': coord2,
                    'hex1_dec': row_dec,
                    'hex2_dec': col_dec,
                    'pre': row.get('pre', 0),
                    'post': row.get('post', 0),
                    'total': row.get('total', row.get('pre', 0) + row.get('post', 0))
                })

        if not roi_info:
            return None

        # Convert to DataFrame for easier analysis
        column_df = pd.DataFrame(roi_info)

        # Count neurons per column
        neurons_per_column = column_df.groupby(['region', 'side', 'hex1_dec', 'hex2_dec']).agg({
            'bodyId': 'nunique',
            'pre': 'sum',
            'post': 'sum',
            'total': 'sum'
        }).reset_index()

        # Calculate mean synapses per neuron for each column
        neurons_per_column['mean_pre_per_neuron'] = neurons_per_column['pre'] / neurons_per_column['bodyId']
        neurons_per_column['mean_post_per_neuron'] = neurons_per_column['post'] / neurons_per_column['bodyId']
        neurons_per_column['mean_total_per_neuron'] = neurons_per_column['total'] / neurons_per_column['bodyId']

        # Sort by region, side, then by hex1 and hex2
        neurons_per_column = neurons_per_column.sort_values(['region', 'side', 'hex1_dec', 'hex2_dec'])

        # Add original coordinate strings back to the aggregated data for display
        coord_map = {}
        for info in roi_info:
            key = (info['region'], info['side'], info['hex1_dec'], info['hex2_dec'])
            if key not in coord_map:
                coord_map[key] = (info['hex1'], info['hex2'])

        # Convert to list of dictionaries for template
        column_summary = []
        for _, row in neurons_per_column.iterrows():
            key = (row['region'], row['side'], row['hex1_dec'], row['hex2_dec'])
            hex1, hex2 = coord_map.get(key, (str(row['hex1_dec']), str(row['hex2_dec'])))

            column_summary.append({
                'region': row['region'],
                'side': row['side'],
                'hex1': hex1,
                'hex2': hex2,
                'hex1_dec': int(row['hex1_dec']),
                'hex2_dec': int(row['hex2_dec']),
                'column_name': f"{row['region']}_{row['side']}_col_{hex1}_{hex2}",
                'neuron_count': int(row['bodyId']),
                'total_pre': int(row['pre']),
                'total_post': int(row['post']),
                'total_synapses': int(row['total']),
                'mean_pre_per_neuron': float(round(float(row['mean_pre_per_neuron']), 1)),
                'mean_post_per_neuron': float(round(float(row['mean_post_per_neuron']), 1)),
                'mean_total_per_neuron': float(round(float(row['mean_total_per_neuron']), 1))
            })

        # Generate summary statistics
        total_columns = len(column_summary)
        total_neurons_with_columns = sum(col['neuron_count'] for col in column_summary)

        if total_columns > 0:
            avg_neurons_per_column = total_neurons_with_columns / total_columns
            avg_synapses_per_column = float(sum(col['total_synapses'] for col in column_summary)) / total_columns

            # Group by region for region-specific stats
            region_stats = {}
            for col in column_summary:
                region = col['region']
                if region not in region_stats:
                    region_stats[region] = {
                        'columns': 0,
                        'neurons': 0,
                        'synapses': 0,
                        'sides': set()
                    }
                region_stats[region]['columns'] += 1
                region_stats[region]['neurons'] += col['neuron_count']
                region_stats[region]['synapses'] += col['total_synapses']
                region_stats[region]['sides'].add(col['side'])

            # Convert sides set to list for JSON serialization
            for region in region_stats:
                region_stats[region]['sides'] = sorted(list(region_stats[region]['sides']))
                region_stats[region]['avg_neurons_per_column'] = float(region_stats[region]['neurons']) / region_stats[region]['columns']
                region_stats[region]['avg_synapses_per_column'] = float(region_stats[region]['synapses']) / region_stats[region]['columns']
        else:
            avg_neurons_per_column = 0
            avg_synapses_per_column = 0.0
            region_stats = {}

        # Generate region-specific hexagonal grids
        region_grids = self._generate_region_hexagonal_grids(column_summary)

        return {
            'columns': column_summary,
            'summary': {
                'total_columns': total_columns,
                'total_neurons_with_columns': total_neurons_with_columns,
                'avg_neurons_per_column': round(float(avg_neurons_per_column), 1),
                'avg_synapses_per_column': round(float(avg_synapses_per_column), 1),
                'regions': region_stats
            },

            'region_grids': region_grids
        }



    def _generate_region_hexagonal_grids(self, column_summary: List[Dict]) -> Dict[str, Dict[str, str]]:
        """
        Generate separate hexagonal grid visualizations for each region (ME, LO, LOP).
        Creates both synapse density and cell count visualizations for each region.
        Uses global color scaling for consistency across regions.
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
                'synapse_density': self._generate_single_region_grid(region_columns, 'synapse_density', region,
                                                                    global_synapse_min, global_synapse_max),
                'cell_count': self._generate_single_region_grid(region_columns, 'cell_count', region,
                                                              global_cell_min, global_cell_max)
            }

        return region_grids

    def _generate_single_region_grid(self, region_columns: List[Dict], metric_type: str, region_name: str,
                                    global_min: Optional[float] = None, global_max: Optional[float] = None) -> str:
        """
        Generate hexagonal grid for a single region with specified metric.

        Args:
            region_columns: List of column data for the region
            metric_type: 'synapse_density' or 'cell_count'
            region_name: Name of the region (ME, LO, LOP)
            global_min: Global minimum value for consistent color scaling
            global_max: Global maximum value for consistent color scaling
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
            subtitle = "Color = Total Synapses"
            min_value = global_min if global_min is not None else min(values)
            max_value = global_max if global_max is not None else max(values)
        else:  # cell_count
            values = [col['neuron_count'] for col in region_columns]
            title = f"{region_name} Region - Cell Count"
            subtitle = "Color = Number of Neurons"
            min_value = global_min if global_min is not None else min(values)
            max_value = global_max if global_max is not None else max(values)

        value_range = max_value - min_value if max_value > min_value else 1

        # Create hexagonal grid coordinates
        hexagons = []
        for col in region_columns:
            # Convert hex1/hex2 to hexagonal grid coordinates
            # Normalized coordinates relative to minimum values in the region
            hex1_coord = col['hex1_dec'] - min_hex1
            hex2_coord = col['hex2_dec'] - min_hex2

            # Map to axial coordinates (q, r) for hexagonal grid positioning
            # This mapping ensures hexagons (31,16), (30,15), (29,14), (28,13), (27,12)
            # form a vertical line on the left side with (31,16) above (30,15)
            # Complete transformation: vertical line + left positioning + horizontal mirror + vertical order reversal
            q = -(hex1_coord - hex2_coord) - 3  # Creates vertical alignment on left side
            r = -hex2_coord             # Controls vertical spacing (negative for screen coordinates where smaller Y = higher position)

            # Convert to pixel coordinates using proper hexagonal spacing
            hex_size = 6
            spacing_factor = 1.1
            # Hexagonal grid pixel conversion with positive y for proper vertical ordering
            x = hex_size * spacing_factor * (3/2 * q)
            y = hex_size * spacing_factor * (math.sqrt(3)/2 * q + math.sqrt(3) * r)

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

        # Generate SVG
        svg_content = self._create_region_hexagonal_svg(hexagons, min_value, max_value, title, subtitle, metric_type)
        return svg_content

    def _create_region_hexagonal_svg(self, hexagons: List[Dict], min_val: float, max_val: float,
                                   title: str, subtitle: str, metric_type: str) -> str:
        """
        Create SVG representation of hexagonal grid for a specific region.
        """
        if not hexagons:
            return ""

        # Calculate SVG dimensions
        margin = 20
        hex_size = 6

        # Find bounds
        min_x = min(hex_data['x'] for hex_data in hexagons) - hex_size
        max_x = max(hex_data['x'] for hex_data in hexagons) + hex_size
        min_y = min(hex_data['y'] for hex_data in hexagons) - hex_size
        max_y = max(hex_data['y'] for hex_data in hexagons) + hex_size

        width = max_x - min_x + 2 * margin
        height = max_y - min_y + 2 * margin

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
        svg_parts.append(f'<text x="10" y="20" text-anchor="left" font-family="Arial, sans-serif" font-size="12" fill="#CCCCCC">{title}</text>')
        svg_parts.append(f'<text x="{width/2}" y="35" text-anchor="middle" font-family="Arial, sans-serif" font-size="10">High hex1 values positioned west, {subtitle}</text>')

        # Generate hexagon path
        hex_points = []
        for i in range(6):
            angle = math.pi / 3 * i
            x = hex_size * math.cos(angle)
            y = hex_size * math.sin(angle)
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
            else:  # cell_count
                tooltip = (f"{hex_data['column_name']}\\n"
                          f"Region: {hex_data['region']} {hex_data['side']}\\n"
                          f"Hex1: {hex_data['hex1']} Hex2: {hex_data['hex2']}\\n"
                          f"Cell Count: {hex_data['value']}\\n"
                          f"Total Synapses: {hex_data['synapse_value']}")

            # Draw hexagon (without outline)
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

        # Add color legend in bottom-right corner
        legend_width = 12
        legend_height = 60
        legend_x = width - legend_width - 15
        legend_y = height - legend_height - 20

        legend_title = "Total Synapses" if metric_type == 'synapse_density' else "Cell Count"
        svg_parts.append(f'<text x="{legend_x}" y="{legend_y - 5}" font-family="Arial, sans-serif" font-size="8" font-weight="bold">{legend_title}</text>')

        # Create gradient for legend with 5 distinct colors
        svg_parts.append(f'<defs><linearGradient id="legend-gradient-{metric_type}" x1="0%" y1="100%" x2="0%" y2="0%">')
        svg_parts.append(f'<stop offset="0%" style="stop-color:#fee5d9;stop-opacity:1" />')
        svg_parts.append(f'<stop offset="25%" style="stop-color:#fcbba1;stop-opacity:1" />')
        svg_parts.append(f'<stop offset="50%" style="stop-color:#fc9272;stop-opacity:1" />')
        svg_parts.append(f'<stop offset="75%" style="stop-color:#ef6548;stop-opacity:1" />')
        svg_parts.append(f'<stop offset="100%" style="stop-color:#a50f15;stop-opacity:1" />')
        svg_parts.append(f'</linearGradient></defs>')

        # Draw legend bar
        svg_parts.append(f'<rect x="{legend_x}" y="{legend_y}" width="{legend_width}" height="{legend_height}" fill="url(#legend-gradient-{metric_type})" stroke="#333" stroke-width="1"/>')

        # Add legend labels
        svg_parts.append(f'<text x="{legend_x + legend_width + 3}" y="{legend_y + 5}" font-family="Arial, sans-serif" font-size="8">{max_val:.0f}</text>')
        svg_parts.append(f'<text x="{legend_x + legend_width + 3}" y="{legend_y + legend_height}" font-family="Arial, sans-serif" font-size="8">{min_val:.0f}</text>')

        svg_parts.append('</svg>')

        return ''.join(svg_parts)

    def _value_to_color(self, normalized_value: float) -> str:
        """
        Convert normalized value (0-1) to one of 5 distinct colors from lightest to darkest red.
        """
        # Define 5 distinct colors from lightest to darkest red
        colors = [
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

        r, g, b = colors[color_index]

        # Convert to hex
        r_hex = format(r, '02x')
        g_hex = format(g, '02x')
        b_hex = format(b, '02x')

        return f"#{r_hex}{g_hex}{b_hex}"

    def _create_hexagonal_svg(self, hexagons: List[Dict], min_val: float, max_val: float) -> str:
        """
        Create SVG representation of hexagonal grid.
        """
        if not hexagons:
            return ""

        # Calculate SVG dimensions
        margin = 15
        hex_size = 6

        # Find bounds
        min_x = min(hex_data['x'] for hex_data in hexagons) - hex_size
        max_x = max(hex_data['x'] for hex_data in hexagons) + hex_size
        min_y = min(hex_data['y'] for hex_data in hexagons) - hex_size
        max_y = max(hex_data['y'] for hex_data in hexagons) + hex_size

        width = max_x - min_x + 2 * margin
        height = max_y - min_y + 2 * margin

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
        svg_parts.append(f'<text x="{width/2}" y="35" text-anchor="middle" font-family="Arial, sans-serif" font-size="10">Hex1 ↑ Upward, Hex2 ↗ Upward-Right, Color = Total Synapses</text>')

        # Generate hexagon path
        hex_points = []
        for i in range(6):
            angle = math.pi / 3 * i
            x = hex_size * math.cos(angle)
            y = hex_size * math.sin(angle)
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

            # Draw hexagon (without internal text, no outline)
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

        # Add color legend in bottom-right corner
        legend_width = 12
        legend_height = 60
        legend_x = width - legend_width - 15
        legend_y = height - legend_height - 20

        svg_parts.append(f'<text x="{legend_x}" y="{legend_y - 5}" font-family="Arial, sans-serif" font-size="8" font-weight="bold">Total Synapses</text>')

        # Create gradient for legend with 5 distinct colors
        svg_parts.append(f'<defs><linearGradient id="legend-gradient-main" x1="0%" y1="100%" x2="0%" y2="0%">')
        svg_parts.append(f'<stop offset="0%" style="stop-color:#fee5d9;stop-opacity:1" />')
        svg_parts.append(f'<stop offset="25%" style="stop-color:#fcbba1;stop-opacity:1" />')
        svg_parts.append(f'<stop offset="50%" style="stop-color:#fc9272;stop-opacity:1" />')
        svg_parts.append(f'<stop offset="75%" style="stop-color:#ef6548;stop-opacity:1" />')
        svg_parts.append(f'<stop offset="100%" style="stop-color:#a50f15;stop-opacity:1" />')
        svg_parts.append(f'</linearGradient></defs>')

        # Draw legend bar
        svg_parts.append(f'<rect x="{legend_x}" y="{legend_y}" width="{legend_width}" height="{legend_height}" fill="url(#legend-gradient-main)" stroke="#333" stroke-width="1"/>')

        # Add legend labels
        svg_parts.append(f'<text x="{legend_x + legend_width + 3}" y="{legend_y + 5}" font-family="Arial, sans-serif" font-size="8">{max_val:.0f}</text>')
        svg_parts.append(f'<text x="{legend_x + legend_width + 3}" y="{legend_y + legend_height}" font-family="Arial, sans-serif" font-size="8">{min_val:.0f}</text>')

        svg_parts.append('</svg>')

        return ''.join(svg_parts)

    def _generate_filename(self, neuron_type: str, soma_side: str) -> str:
        # Clean neuron type name for filename
        clean_type = neuron_type.replace('/', '_').replace(' ', '_')

        # Handle different soma side formats with new naming scheme
        if soma_side in ['all', 'both']:
            # General page for neuron type (multiple sides available)
            return f"{clean_type}.html"
        else:
            # Specific page for single side
            soma_side_suffix = soma_side
            if soma_side_suffix == 'left':
                soma_side_suffix = 'L'
            elif soma_side_suffix == 'right':
                soma_side_suffix = 'R'
            elif soma_side_suffix == 'middle':
                soma_side_suffix = 'M'
            return f"{clean_type}_{soma_side_suffix}.html"

    def _format_number(self, value: Any) -> str:
        """Format numbers with commas."""
        if isinstance(value, (int, float)):
            return f"{value:,}"
        return str(value)

    def _get_primary_rois(self, connector):
        """Get primary ROIs based on dataset type and available data."""
        primary_rois = set()

        # First, try to get primary ROIs from NeuPrint if we have a connector
        if connector and hasattr(connector, 'client') and connector.client:
            try:
                from neuprint.queries import fetch_roi_hierarchy
                import neuprint
                original_client = neuprint.default_client
                neuprint.default_client = connector.client

                # Get ROI hierarchy with primary ROIs marked with stars
                roi_hierarchy = fetch_roi_hierarchy(mark_primary=True)
                neuprint.default_client = original_client

                if roi_hierarchy is not None:
                    # Extract all ROI names from the hierarchical dictionary structure
                    extracted_rois = self._extract_roi_names_from_hierarchy(roi_hierarchy)

                    # Filter for ROIs that have a star (*) and remove the star for display
                    for roi_name in extracted_rois:
                        if roi_name.endswith('*'):
                            # Remove the star and add to primary ROIs set
                            clean_roi_name = roi_name.rstrip('*')
                            primary_rois.add(clean_roi_name)

            except Exception as e:
                print(f"Warning: Could not fetch primary ROIs from NeuPrint: {e}")

        # Dataset-specific primary ROIs based on dataset name
        dataset_name = ""
        if connector and hasattr(connector, 'config'):
            dataset_name = connector.config.neuprint.dataset.lower()

        # Add dataset-specific primary ROIs
        if 'optic' in dataset_name or 'ol' in dataset_name:
            # Optic-lobe specific primary ROIs
            optic_primary = {
                'OL(R)', 'OL(L)', 'ME(R)', 'ME(L)', 'LO(R)', 'LO(L)',
                'LOP(R)', 'LOP(L)', 'AME(R)', 'AME(L)', 'LA(R)', 'LA(L)'
            }
            primary_rois.update(optic_primary)
        elif 'cns' in dataset_name:
            # CNS specific primary ROIs
            cns_primary = {
                'Optic(R)', 'Optic(L)', 'ME(R)', 'ME(L)', 'LO(R)', 'LO(L)',
                'AL(R)', 'AL(L)', 'MB(R)', 'MB(L)', 'CX', 'PB', 'FB', 'EB'
            }
            primary_rois.update(cns_primary)
        elif 'hemibrain' in dataset_name:
            # Hemibrain specific primary ROIs
            hemibrain_primary = {
                'ME(R)', 'ME(L)', 'LO(R)', 'LO(L)', 'LOP(R)', 'LOP(L)',
                'AL(R)', 'AL(L)', 'MB(R)', 'MB(L)', 'CX', 'PB', 'FB', 'EB', 'NO'
            }
            primary_rois.update(hemibrain_primary)

        # If we still have no primary ROIs, use a comprehensive fallback
        if len(primary_rois) == 0:
            primary_rois = {
                'ME(R)', 'ME(L)', 'LO(R)', 'LO(L)', 'LOP(R)', 'LOP(L)',
                'OL(R)', 'OL(L)', 'Optic(R)', 'Optic(L)', 'AL(R)', 'AL(L)',
                'MB(R)', 'MB(L)', 'CX', 'PB', 'FB', 'EB', 'NO', 'BU(R)', 'BU(L)',
                'LAL(R)', 'LAL(L)', 'ICL(R)', 'ICL(L)', 'IB', 'ATL(R)', 'ATL(L)'
            }

        return primary_rois

    def _extract_roi_names_from_hierarchy(self, hierarchy, roi_names=None):
        """
        Recursively extract all ROI names from the hierarchical dictionary structure.

        Args:
            hierarchy: Dictionary or any structure from fetch_roi_hierarchy
            roi_names: Set to collect ROI names (used for recursion)

        Returns:
            Set of all ROI names found in the hierarchy
        """
        if roi_names is None:
            roi_names = set()

        if isinstance(hierarchy, dict):
            # Add all dictionary keys as potential ROI names
            for key in hierarchy.keys():
                if isinstance(key, str):
                    roi_names.add(key)

            # Recursively process all dictionary values
            for value in hierarchy.values():
                self._extract_roi_names_from_hierarchy(value, roi_names)

        elif isinstance(hierarchy, (list, tuple)):
            # Process each item in the list/tuple
            for item in hierarchy:
                self._extract_roi_names_from_hierarchy(item, roi_names)

        # For other types (strings, numbers, etc.), we don't extract anything
        # as they're likely values rather than ROI names

        return roi_names

    def _format_percentage(self, value: Any) -> str:
        """Format numbers as percentages."""
        if isinstance(value, (int, float)):
            return f"{value:.1f}%"
        return str(value)

    def _abbreviate_neurotransmitter(self, neurotransmitter: str) -> str:
        """Convert neurotransmitter names to abbreviated forms with HTML abbr tag."""
        # Mapping of common neurotransmitter names to abbreviations
        abbreviations = {
            'acetylcholine': 'ACh',
            'dopamine': 'DA',
            'serotonin': '5-HT',
            'octopamine': 'OA',
            'gaba': 'GABA',
            'glutamate': 'Glu',
            'histamine': 'HA',
            'tyramine': 'TA',
            'choline': 'ACh',  # Sometimes appears as just 'choline'
            'norepinephrine': 'NE',
            'epinephrine': 'Epi',
            'glycine': 'Gly',
            'aspartate': 'Asp',
            'unknown': 'Unk',
            'unclear': 'unc',
            'none': '-',
            '': '-',
            'nan': 'Unk'
        }

        if not neurotransmitter or pd.isna(neurotransmitter):
            return '<abbr title="Unknown">Unk</abbr>'

        # Convert to lowercase for case-insensitive matching
        original_nt = str(neurotransmitter).strip()
        nt_lower = original_nt.lower()

        # Get abbreviated form
        abbreviated = abbreviations.get(nt_lower)

        if abbreviated:
            # If we found an abbreviation, wrap it in abbr tag with original name as title
            return f'<abbr title="{original_nt}">{abbreviated}</abbr>'
        else:
            # For unknown neurotransmitters, truncate if too long but keep original in title
            if len(original_nt) > 5:
                truncated = original_nt[:4] + "..."
                return f'<abbr title="{original_nt}">{truncated}</abbr>'
            else:
                # Short enough to display as-is, but still wrap in abbr for consistency
                return f'<abbr title="{original_nt}">{original_nt}</abbr>'
