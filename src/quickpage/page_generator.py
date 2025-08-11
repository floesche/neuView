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
import re

from .config import Config
from .visualization import HexagonGridGenerator


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

        # Initialize hexagon grid generator with output directory
        self.hexagon_generator = HexagonGridGenerator(output_dir=self.output_dir)

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
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Add custom filters
        self.env.filters['format_number'] = self._format_number
        self.env.filters['format_percentage'] = self._format_percentage
        self.env.filters['abbreviate_neurotransmitter'] = self._abbreviate_neurotransmitter
        self.env.filters['is_png_data'] = self._is_png_data

    def _minify_html(self, html_content: str) -> str:
        """
        Minify HTML content by removing unnecessary whitespace.

        Args:
            html_content: Raw HTML content to minify

        Returns:
            Minified HTML content
        """
        # Store script and style content to preserve formatting
        preserved_blocks = []

        def preserve_block(match):
            preserved_blocks.append(match.group(0))
            return f"<!--PRESERVE_BLOCK_{len(preserved_blocks)-1}-->"

        # Preserve script, style, pre, and textarea content
        html_content = re.sub(r'<(script|style|pre|textarea)[^>]*>.*?</\1>',
                             preserve_block, html_content, flags=re.DOTALL | re.IGNORECASE)

        # Remove HTML comments (but preserve our preserve markers)
        html_content = re.sub(r'<!--(?!PRESERVE_BLOCK_).*?-->', '', html_content, flags=re.DOTALL)

        # Remove whitespace between tags (but not within tags)
        html_content = re.sub(r'>\s+<', '><', html_content)

        # Remove leading and trailing whitespace from lines
        html_content = re.sub(r'^\s+', '', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'\s+$', '', html_content, flags=re.MULTILINE)

        # Collapse multiple whitespace characters within text content
        # But preserve single spaces that are meaningful
        html_content = re.sub(r'[ \t]{2,}', ' ', html_content)

        # Remove multiple consecutive newlines
        html_content = re.sub(r'\n{2,}', '\n', html_content)

        # Restore preserved blocks
        for i, block in enumerate(preserved_blocks):
            html_content = html_content.replace(f"<!--PRESERVE_BLOCK_{i}-->", block)

        return html_content.strip()


    def generate_page(self, neuron_type: str, neuron_data: Dict[str, Any],
                     soma_side: str, image_format: str = 'svg', embed_images: bool = False) -> str:
        """
        Generate an HTML page for a neuron type.

        Args:
            neuron_type: The neuron type name
            neuron_data: Data returned from NeuPrintConnector
            soma_side: Soma side filter used
            image_format: Format for hexagon grid images ('svg' or 'png')
            embed_images: If True, embed images in HTML; if False, save to files

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
            neuron_type,
            file_type=image_format,
            save_to_files=not embed_images
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

        # Minify HTML content to reduce whitespace
        html_content = self._minify_html(html_content)

        # Generate output filename
        output_filename = self._generate_filename(neuron_type, soma_side)
        output_path = self.output_dir / output_filename

        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(output_path)

    def generate_page_from_neuron_type(self, neuron_type_obj, connector, image_format: str = 'svg', embed_images: bool = False) -> str:
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
            neuron_type_obj.name,
            file_type=image_format,
            save_to_files=not embed_images
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

    def _analyze_column_roi_data(self, roi_counts_df, neurons_df, soma_side, neuron_type, file_type: str = 'svg', save_to_files: bool = True):
        """
        Analyze ROI data for column-based regions matching pattern (ME|LO|LOP)_[RL]_col_hex1_hex2.
        Returns additional table with mean synapses per column per neuron type.

        Args:
            roi_counts_df: DataFrame with ROI count data
            neurons_df: DataFrame with neuron data
            soma_side: Side of soma (left/right)
            neuron_type: Type of neuron being analyzed
            file_type: Output format for hexagonal grids ('svg' or 'png')
            save_to_files: If True, save files to disk; if False, embed content
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
        region_grids = self._generate_region_hexagonal_grids(column_summary, neuron_type, soma_side, file_type, save_to_files=save_to_files)

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



    def _generate_region_hexagonal_grids(self, column_summary: List[Dict], neuron_type: str, soma_side, file_type: str = 'svg', save_to_files: bool = True) -> Dict[str, Dict[str, str]]:
        """
        Generate separate hexagonal grid visualizations for each region (ME, LO, LOP).
        Creates both synapse density and cell count visualizations for each region.
        Uses global color scaling for consistency across regions.

        Args:
            column_summary: List of column data dictionaries
            neuron_type: Type of neuron being visualized
            soma_side: Side of soma (left/right)
            file_type: Output format ('svg' or 'png')
            save_to_files: If True, save files to output/static/images and return file paths.
                          If False, return content directly for embedding in HTML.

        Returns:
            Dictionary mapping region names to visualization data (either file paths or content)
        """
        if file_type not in ['svg', 'png']:
            raise ValueError("file_type must be either 'svg' or 'png'")

        return self.hexagon_generator.generate_region_hexagonal_grids(
            column_summary, neuron_type, soma_side, output_format=file_type, save_to_files=save_to_files
        )

    def _generate_region_hexagonal_grids_png(self, column_summary: List[Dict], neuron_type: str, soma_side) -> Dict[str, Dict[str, str]]:
        """
        Generate separate hexagonal grid visualizations for each region (ME, LO, LOP) in PNG format.
        Creates both synapse density and cell count visualizations for each region.
        Uses global color scaling for consistency across regions.
        Returns base64-encoded PNG data.

        .. deprecated::
            Use _generate_region_hexagonal_grids(column_summary, neuron_type, soma_side, file_type='png') instead.
        """
        return self.hexagon_generator.generate_region_hexagonal_grids(
            column_summary, neuron_type, soma_side, output_format='png', save_to_files=False
        )








    def generate_and_save_hexagon_grids(self, column_summary: List[Dict], neuron_type: str, soma_side, file_type: str = 'png') -> Dict[str, Dict[str, str]]:
        """
        Generate hexagon grids and save them to files.
        Convenience method for external use or when files are specifically needed.

        Args:
            column_summary: List of column data dictionaries
            neuron_type: Type of neuron being visualized
            soma_side: Side of soma (left/right)
            file_type: Output format ('svg' or 'png')

        Returns:
            Dictionary mapping region names to file paths
        """
        return self._generate_region_hexagonal_grids(
            column_summary, neuron_type, soma_side, file_type, save_to_files=True
        )

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

    def _is_png_data(self, content: str) -> bool:
        """Check if content is a PNG data URL."""
        if isinstance(content, str):
            return content.startswith('data:image/png;base64,')
        return False
