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
        Analyze ROI data for column-based regions matching pattern (ME|LO|LOP)_[RL]_col_HEX1_HEX2.
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

        # Pattern to match column ROIs: (ME|LO|LOP)_[RL]_col_HEX1_HEX2
        column_pattern = r'^(ME|LO|LOP)_([RL])_col_([A-Fa-f0-9]+)_([A-Fa-f0-9]+)$'

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
                region, side, hex1, hex2 = match.groups()
                roi_info.append({
                    'roi': row['roi'],
                    'bodyId': row['bodyId'],
                    'region': region,
                    'side': side,
                    'row_hex': hex1,
                    'col_hex': hex2,
                    'row_dec': int(hex1, 16),
                    'col_dec': int(hex2, 16),
                    'pre': row.get('pre', 0),
                    'post': row.get('post', 0),
                    'total': row.get('pre', 0) + row.get('post', 0)
                })

        if not roi_info:
            return None

        # Convert to DataFrame for easier analysis
        column_df = pd.DataFrame(roi_info)

        # Count neurons per column
        neurons_per_column = column_df.groupby(['region', 'side', 'row_dec', 'col_dec']).agg({
            'bodyId': 'nunique',
            'pre': 'sum',
            'post': 'sum',
            'total': 'sum'
        }).reset_index()

        # Calculate mean synapses per neuron for each column
        neurons_per_column['mean_pre_per_neuron'] = neurons_per_column['pre'] / neurons_per_column['bodyId']
        neurons_per_column['mean_post_per_neuron'] = neurons_per_column['post'] / neurons_per_column['bodyId']
        neurons_per_column['mean_total_per_neuron'] = neurons_per_column['total'] / neurons_per_column['bodyId']

        # Sort by region, side, then by row and column
        neurons_per_column = neurons_per_column.sort_values(['region', 'side', 'row_dec', 'col_dec'])

        # Convert to list of dictionaries for template
        column_summary = []
        for _, row in neurons_per_column.iterrows():
            column_summary.append({
                'region': row['region'],
                'side': row['side'],
                'row_hex': f"{row['row_dec']:X}",
                'col_hex': f"{row['col_dec']:X}",
                'row_dec': int(row['row_dec']),
                'col_dec': int(row['col_dec']),
                'column_name': f"{row['region']}_{row['side']}_col_{row['row_dec']:X}_{row['col_dec']:X}",
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

        # Generate hexagonal grid visualization
        hex_grid_svg = self._generate_hexagonal_grid(column_summary)

        return {
            'columns': column_summary,
            'summary': {
                'total_columns': total_columns,
                'total_neurons_with_columns': total_neurons_with_columns,
                'avg_neurons_per_column': round(float(avg_neurons_per_column), 1),
                'avg_synapses_per_column': round(float(avg_synapses_per_column), 1),
                'regions': region_stats
            },
            'hexagonal_grid': hex_grid_svg
        }

    def _generate_hexagonal_grid(self, column_summary: List[Dict]) -> str:
        """
        Generate a hexagonal grid visualization using pygal.
        30° dimension represents row (HEX1), 150° dimension represents col (HEX2).
        Color coding from white to red represents mean total synapses per neuron.
        """
        if not column_summary:
            return ""

        # Create a custom pygal chart for hexagonal grid
        from pygal import Config as PygalConfig
        from pygal.style import Style

        # Calculate coordinate ranges and synapse value range
        min_row = min(col['row_dec'] for col in column_summary)
        max_row = max(col['row_dec'] for col in column_summary)
        min_col = min(col['col_dec'] for col in column_summary)
        max_col = max(col['col_dec'] for col in column_summary)

        min_synapses = min(col['mean_total_per_neuron'] for col in column_summary)
        max_synapses = max(col['mean_total_per_neuron'] for col in column_summary)
        synapse_range = max_synapses - min_synapses if max_synapses > min_synapses else 1

        # Create hexagonal grid coordinates
        hexagons = []
        for col in column_summary:
            # Convert row/col to hexagonal grid coordinates
            # 30° represents row, 150° represents col
            row_coord = col['row_dec']
            col_coord = col['col_dec']

            # Calculate hexagonal position
            # Using axial coordinates for hexagonal grid
            q = col_coord - min_col  # column position
            r = row_coord - min_row  # row position

            # Convert to pixel coordinates for hexagonal layout
            hex_size = 30
            x = hex_size * (3/2 * q)
            y = hex_size * (math.sqrt(3)/2 * q + math.sqrt(3) * r)

            # Normalize synapse value for color mapping (0-1)
            normalized_value = (col['mean_total_per_neuron'] - min_synapses) / synapse_range

            # Create color from white to red based on value
            color = self._value_to_color(normalized_value)

            hexagons.append({
                'x': x,
                'y': y,
                'value': col['mean_total_per_neuron'],
                'color': color,
                'region': col['region'],
                'side': col['side'],
                'row_hex': col['row_hex'],
                'col_hex': col['col_hex'],
                'neuron_count': col['neuron_count'],
                'column_name': col['column_name']
            })

        # Generate SVG using custom hexagonal drawing
        svg_content = self._create_hexagonal_svg(hexagons, min_synapses, max_synapses)

        return svg_content

    def _value_to_color(self, normalized_value: float) -> str:
        """
        Convert normalized value (0-1) to color from white to red.
        """
        # Interpolate from white (1,1,1) to red (1,0,0)
        r = 1.0
        g = 1.0 - normalized_value
        b = 1.0 - normalized_value

        # Convert to hex
        r_hex = format(int(r * 255), '02x')
        g_hex = format(int(g * 255), '02x')
        b_hex = format(int(b * 255), '02x')

        return f"#{r_hex}{g_hex}{b_hex}"

    def _create_hexagonal_svg(self, hexagons: List[Dict], min_val: float, max_val: float) -> str:
        """
        Create SVG representation of hexagonal grid.
        """
        if not hexagons:
            return ""

        # Calculate SVG dimensions
        margin = 50
        hex_size = 25

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
            f'.hex-text {{ font-family: Arial, sans-serif; font-size: 10px; text-anchor: middle; }}',
            f'</style>',
            f'</defs>'
        ]

        # Add background
        svg_parts.append(f'<rect width="{width}" height="{height}" fill="#f8f9fa" stroke="none"/>')

        # Add title
        svg_parts.append(f'<text x="{width/2}" y="30" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" font-weight="bold">Column Organization Grid</text>')
        svg_parts.append(f'<text x="{width/2}" y="45" text-anchor="middle" font-family="Arial, sans-serif" font-size="12">30° = Row, 150° = Column, Color = Mean Synapses/Neuron</text>')

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
                      f"Row: {hex_data['row_hex']} Col: {hex_data['col_hex']}\\n"
                      f"Neurons: {hex_data['neuron_count']}\\n"
                      f"Mean Synapses: {hex_data['value']:.1f}")

            # Draw hexagon
            svg_parts.append(
                f'<g transform="translate({x},{y})">'
                f'<path d="{hex_path}" '
                f'fill="{color}" '
                f'stroke="#333" '
                f'stroke-width="1" '
                f'opacity="0.8">'
                f'<title>{tooltip}</title>'
                f'</path>'
                f'<text y="5" class="hex-text" fill="#000">{hex_data["value"]:.0f}</text>'
                f'</g>'
            )

        # Add color legend
        legend_x = width - 200
        legend_y = 80
        legend_height = 150
        legend_width = 20

        svg_parts.append(f'<text x="{legend_x}" y="{legend_y - 10}" font-family="Arial, sans-serif" font-size="12" font-weight="bold">Synapses/Neuron</text>')

        # Create gradient for legend
        svg_parts.append(f'<defs><linearGradient id="legend-gradient" x1="0%" y1="100%" x2="0%" y2="0%">')
        svg_parts.append(f'<stop offset="0%" style="stop-color:#ffffff;stop-opacity:1" />')
        svg_parts.append(f'<stop offset="100%" style="stop-color:#ff0000;stop-opacity:1" />')
        svg_parts.append(f'</linearGradient></defs>')

        # Draw legend bar
        svg_parts.append(f'<rect x="{legend_x}" y="{legend_y}" width="{legend_width}" height="{legend_height}" fill="url(#legend-gradient)" stroke="#333" stroke-width="1"/>')

        # Add legend labels
        svg_parts.append(f'<text x="{legend_x + legend_width + 5}" y="{legend_y + 5}" font-family="Arial, sans-serif" font-size="10">{max_val:.0f}</text>')
        svg_parts.append(f'<text x="{legend_x + legend_width + 5}" y="{legend_y + legend_height}" font-family="Arial, sans-serif" font-size="10">{min_val:.0f}</text>')

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
