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
import json
import urllib.parse
import numpy as np
import logging
import time

from .config import Config
from .visualization import HexagonGridGenerator

logger = logging.getLogger(__name__)


class PageGenerator:
    """
    Generate HTML pages for neuron types.

    This class handles the complete page generation process including template
    rendering, static file copying, and output file management.
    """

    def __init__(self, config: Config, output_dir: str, queue_service=None):
        """
        Initialize the page generator.

        Args:
            config: Configuration object with template and output settings
            output_dir: Directory path for generated HTML files
            queue_service: Optional QueueService for checking queued neuron types
        """
        self.config = config
        self.output_dir = Path(output_dir)
        self.template_dir = Path(config.output.template_dir)
        self.queue_service = queue_service

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Jinja2 environment first
        self._setup_jinja_env()

        # Copy static files to output directory
        self._copy_static_files()

        # Initialize hexagon grid generator with output directory
        self.hexagon_generator = HexagonGridGenerator(output_dir=self.output_dir)

        # Initialize caches for expensive operations
        self._all_columns_cache = None
        self._column_analysis_cache = {}

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

        # Copy JS files (except neuron-search.js which is generated during page generation)
        js_source_dir = static_dir / 'js'
        if js_source_dir.exists():
            for js_file in js_source_dir.glob('*.js'):
                if js_file.name != 'neuron-search.js':  # Skip template file
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
        self.env.filters['format_synapse_count'] = self._format_synapse_count
        self.env.filters['abbreviate_neurotransmitter'] = self._abbreviate_neurotransmitter
        self.env.filters['is_png_data'] = self._is_png_data
        self.env.filters['neuron_link'] = self._create_neuron_link
        self.env.filters['truncate_neuron_name'] = self._truncate_neuron_name

    def _generate_neuron_search_js(self):
        """Generate neuron-search.js with embedded neuron types data."""
        output_js_file = self.output_dir / 'static' / 'js' / 'neuron-search.js'

        # Only generate if file doesn't exist
        if output_js_file.exists():
            logger.debug("neuron-search.js already exists, skipping generation")
            return

        # Get neuron types from queue service if available
        neuron_types = []
        if self.queue_service:
            neuron_types = self.queue_service.get_queued_neuron_types()

        # Ensure types are sorted
        neuron_types = sorted(neuron_types)

        # Load the template
        template_path = self.template_dir / 'static' / 'js' / 'neuron-search.js.template'
        if not template_path.exists():
            logger.warning(f"Neuron search template not found at {template_path}")
            return

        try:
            template = self.env.get_template('static/js/neuron-search.js.template')

            # Generate the JavaScript content with manual JSON rendering to avoid HTML escaping
            js_content = template.render(
                neuron_types=neuron_types,
                neuron_types_json=json.dumps(neuron_types, indent=2),
                generation_timestamp=datetime.now().isoformat()
            )

            # Fix HTML entity encoding that Jinja2 applies
            js_content = js_content.replace('&#34;', '"')

            # Write to output directory
            with open(output_js_file, 'w', encoding='utf-8') as f:
                f.write(js_content)

            logger.info(f"Generated neuron-search.js with {len(neuron_types)} neuron types")

        except Exception as e:
            logger.error(f"Failed to generate neuron-search.js: {e}")


    def _minify_html(self, html_content: str, minify_js: bool = True) -> str:
        """
        Minify HTML content by removing unnecessary whitespace.

        Args:
            html_content: Raw HTML content to minify
            minify_js: Whether to minify JavaScript content within script tags

        Returns:
            Minified HTML content
        """

        import minify_html
        import re

        # Check for problematic JavaScript patterns that cause minify-js to panic
        # The minify-js 0.6.0 library has severe bugs with control flow statements
        # Testing shows it fails on: if statements, switch, loops, try-catch, functions
        # Safe patterns: variable declarations, ternary operators, simple function calls
        has_problematic_js = False

        if minify_js:
            # Look for problematic patterns inside script tags
            script_pattern = r'<script[^>]*>(.*?)</script>'
            scripts = re.findall(script_pattern, html_content, re.DOTALL | re.IGNORECASE)

            for i, script_content in enumerate(scripts):
                # Skip external scripts (just src attribute, no inline content)
                if script_content.strip() == '':
                    continue

                # Skip scripts that only contain safe patterns
                # Safe patterns: simple variable declarations, function calls, ternary operators
                safe_only_pattern = r'^[\s\n]*(?:(?:var|let|const)\s+\w+\s*=\s*[^;]+;|[\w.$]+\([^)]*\);|\w+\s*=\s*[^?]*\?[^:]*:[^;]+;|//[^\n]*|/\*.*?\*/|\s)*[\s\n]*$'

                if re.match(safe_only_pattern, script_content, re.DOTALL):
                    logger.debug(f"Script {i}: Contains only safe patterns, allowing minification")
                    continue

                # Check for problematic control flow patterns that cause minify-js to crash
                # These patterns were verified through testing to cause library panics
                problematic_patterns = [
                    (r'if\s*\([^)]+\)\s*\{', "if statement"),
                    (r'switch\s*\([^)]+\)\s*\{', "switch statement"),
                    (r'while\s*\([^)]+\)\s*\{', "while loop"),
                    (r'for\s*\([^)]*\)\s*\{', "for loop"),
                    (r'try\s*\{', "try-catch block"),
                    (r'function\s*\([^)]*\)\s*\{', "function declaration"),
                    (r'=>\s*\{', "arrow function with block"),
                ]

                for pattern, description in problematic_patterns:
                    if re.search(pattern, script_content, re.DOTALL):
                        logger.debug(f"Script {i}: Found {description} - minify-js 0.6.0 cannot handle these reliably")
                        has_problematic_js = True
                        break

                if has_problematic_js:
                    break

        # Use JS minification only if no problematic patterns are detected
        safe_minify_js = minify_js and not has_problematic_js

        if minify_js and has_problematic_js:
            logger.info("Skipping JavaScript minification due to known minify-js 0.6.0 library bugs with control flow statements")

        minified = minify_html.minify(html_content, minify_js=safe_minify_js, minify_css=True, remove_processing_instructions=True)
        return minified



    def _generate_neuroglancer_url(self, neuron_type: str, neuron_data: Dict[str, Any], soma_side: Optional[str] = None) -> str:
        """
        Generate Neuroglancer URL from template with substituted variables.

        Args:
            neuron_type: The neuron type name
            neuron_data: Data containing neuron information including bodyIDs
            soma_side: Soma side filter ('left', 'right', 'both', etc.)

        Returns:
            URL-encoded Neuroglancer URL
        """
        try:
            # Load neuroglancer template
            neuroglancer_template = self.env.get_template('neuroglancer.js.jinja')

            # Get bodyID(s) closest to 95th percentile of synapse count
            neurons_df = neuron_data.get('neurons')
            visible_neurons = []
            if neurons_df is not None and not neurons_df.empty:
                bodyids = neurons_df['bodyId'].tolist() if 'bodyId' in neurons_df.columns else []
                if bodyids:
                    selected_bodyids = self._select_bodyids_by_soma_side(neuron_type, neurons_df, soma_side, 95)
                    visible_neurons = [str(bodyid) for bodyid in selected_bodyids]

            # Prepare template variables
            template_vars = {
                'website_title': neuron_type,
                'visible_neurons': visible_neurons,
                'neuron_query': neuron_type
            }

            # Render the template
            neuroglancer_json = neuroglancer_template.render(**template_vars)

            # Parse as JSON to validate and then convert back to string
            neuroglancer_state = json.loads(neuroglancer_json)
            neuroglancer_json_string = json.dumps(neuroglancer_state, separators=(',', ':'))

            # URL encode the JSON string
            encoded_state = urllib.parse.quote(neuroglancer_json_string, safe='')

            # Create the full Neuroglancer URL
            neuroglancer_url = f"https://clio-ng.janelia.org/#!{encoded_state}"

            return neuroglancer_url

        except Exception as e:
            # Return a fallback URL if template processing fails
            print(f"Warning: Failed to generate Neuroglancer URL for {neuron_type}: {e}")
            return "https://clio-ng.janelia.org/"

    def _select_bodyid_by_synapse_percentile(self, neuron_type: str, neurons_df: pd.DataFrame, percentile: float = 95) -> int:
        """
        Select bodyID of neuron closest to the specified percentile of synapse count.

        Args:
            neurons_df: DataFrame containing neuron data with bodyId, pre, and post columns
            percentile: Target percentile (0-100), defaults to 95

        Returns:
            bodyId of the neuron closest to the target percentile
        """
        if neurons_df.empty:
            raise ValueError("Cannot select from empty neurons DataFrame")

        # Optimization: If only one neuron, select it directly without synapse calculations
        if len(neurons_df) == 1:
            start_time = time.time()
            bodyid = int(neurons_df.iloc[0]['bodyId'])
            end_time = time.time()
            logger.debug(f"Selected single available {neuron_type} bodyId {bodyid} (optimization saved synapse calculation, took {end_time-start_time:.4f}s)")
            return bodyid

        # Start timing for percentile calculation
        start_time = time.time()

        # Calculate total synapse count for each neuron
        pre_col = 'pre' if 'pre' in neurons_df.columns else None
        post_col = 'post' if 'post' in neurons_df.columns else None

        if pre_col and post_col:
            # Both pre and post synapses available
            total_synapses = neurons_df[pre_col] + neurons_df[post_col]
        elif pre_col:
            # Only pre synapses available
            total_synapses = neurons_df[pre_col]
        elif post_col:
            # Only post synapses available
            total_synapses = neurons_df[post_col]
        else:
            # No synapse data available, fall back to first neuron
            logger.warning("No synapse count columns found, selecting first neuron")
            return int(neurons_df.iloc[0]['bodyId'])

        # Calculate the target percentile value
        target_value = np.percentile(total_synapses, percentile)

        # Find the neuron closest to the target percentile
        differences = abs(total_synapses - target_value)
        closest_idx = differences.idxmin()

        selected_bodyid = int(neurons_df.loc[closest_idx, 'bodyId'])

        end_time = time.time()
        logger.debug(f"Selected {neuron_type} bodyId {selected_bodyid} with {total_synapses.loc[closest_idx]} total synapses "
                   f"(closest to {percentile}th percentile: {target_value:.1f}, calculation took {end_time-start_time:.4f}s)")

        return selected_bodyid

    def _select_bodyids_by_soma_side(self, neuron_type: str, neurons_df: pd.DataFrame, soma_side: Optional[str], percentile: float = 95) -> List[int]:
        """
        Select bodyID(s) based on soma side and synapse count percentiles.

        For 'both' soma side, selects one neuron from each side (left and right).
        For specific sides, selects one neuron from that side.
        Optimization: If only one neuron exists for a side, selects it directly without synapse queries.

        Args:
            neurons_df: DataFrame containing neuron data with bodyId, pre, post, and somaSide columns
            soma_side: Target soma side ('left', 'right', 'both', 'all', etc.)
            percentile: Target percentile (0-100), defaults to 95

        Returns:
            List of bodyIds selected based on criteria
        """
        if neurons_df.empty:
            logger.warning("Empty neurons DataFrame, no bodyIds selected")
            return []

        # Ensure we have soma side information
        if 'somaSide' not in neurons_df.columns:
            logger.warning("No somaSide column found, falling back to single selection")
            # Check if only one neuron exists - skip synapse calculation if so
            if len(neurons_df) == 1:
                bodyid = int(neurons_df.iloc[0]['bodyId'])
                logger.debug(f"Selected single available bodyId {bodyid} (no soma side filtering)")
                return [bodyid]
            return [self._select_bodyid_by_synapse_percentile(neuron_type, neurons_df, percentile)]

        selected_bodyids = []

        if soma_side == 'both':
            # Select one neuron from each available side
            available_sides = neurons_df['somaSide'].unique()

            # Map side codes to readable names for logging
            side_names = {'L': 'left', 'R': 'right', 'M': 'middle'}

            for side_code in ['L', 'R']:  # Focus on left and right for 'both'
                if side_code in available_sides:
                    side_neurons_mask = neurons_df['somaSide'] == side_code
                    side_neurons = neurons_df.loc[side_neurons_mask].copy()
                    if not side_neurons.empty:
                        try:
                            # Optimization: If only one neuron for this side, select it directly
                            if len(side_neurons) == 1:
                                start_time = time.time()
                                bodyid = int(side_neurons.iloc[0]['bodyId'])
                                end_time = time.time()
                                side_name = side_names.get(side_code, side_code)
                                logger.debug(f"Selected single available bodyId {bodyid} for {side_name} side (optimization saved synapse calculation, took {end_time-start_time:.4f}s)")
                            else:
                                bodyid = self._select_bodyid_by_synapse_percentile(neuron_type, side_neurons, percentile)
                                side_name = side_names.get(side_code, side_code)
                                logger.debug(f"Selected bodyId {bodyid} for {side_name} side")
                            selected_bodyids.append(bodyid)
                        except Exception as e:
                            logger.warning(f"Could not select neuron for side {side_code}: {e}")

            # If no left/right neurons found, try middle
            if not selected_bodyids and 'M' in available_sides:
                middle_neurons_mask = neurons_df['somaSide'] == 'M'
                middle_neurons = neurons_df.loc[middle_neurons_mask].copy()
                if not middle_neurons.empty:
                    try:
                        # Optimization: If only one middle neuron, select it directly
                        if len(middle_neurons) == 1:
                            start_time = time.time()
                            bodyid = int(middle_neurons.iloc[0]['bodyId'])
                            end_time = time.time()
                            logger.debug(f"Selected single available bodyId {bodyid} for middle side (optimization saved synapse calculation, took {end_time-start_time:.4f}s)")
                        else:
                            bodyid = self._select_bodyid_by_synapse_percentile(neuron_type, middle_neurons, percentile)
                            logger.debug(f"Selected bodyId {bodyid} for middle side (no left/right available)")
                        selected_bodyids.append(bodyid)
                    except Exception as e:
                        logger.warning(f"Could not select neuron for middle side: {e}")

        else:
            # For specific soma sides, filter by that side first
            filtered_neurons = neurons_df

            if soma_side in ['left', 'right', 'middle']:
                # Map readable names to side codes
                side_mapping = {'left': 'L', 'right': 'R', 'middle': 'M'}
                side_code = side_mapping.get(soma_side)

                if side_code and 'somaSide' in neurons_df.columns:
                    side_mask = neurons_df['somaSide'] == side_code
                    filtered_neurons = neurons_df.loc[side_mask].copy()

                    if filtered_neurons.empty:
                        logger.warning(f"No neurons found for {soma_side} side")
                        return []

            # Optimization: If only one neuron after filtering, select it directly
            if len(filtered_neurons) == 1:
                start_time = time.time()
                bodyid = int(filtered_neurons.iloc[0]['bodyId'])
                end_time = time.time()
                logger.debug(f"Selected single available bodyId {bodyid} for {soma_side} side (optimization saved synapse calculation, took {end_time-start_time:.4f}s)")
                selected_bodyids.append(bodyid)
            else:
                # Apply percentile selection to filtered neurons
                try:
                    bodyid = self._select_bodyid_by_synapse_percentile(neuron_type, filtered_neurons, percentile)
                    selected_bodyids.append(bodyid)
                except Exception as e:
                    logger.warning(f"Could not select neuron: {e}")

        # Fallback to first available neuron if no selection was made
        if not selected_bodyids and not neurons_df.empty:
            fallback_bodyid = int(neurons_df.iloc[0]['bodyId'])
            selected_bodyids.append(fallback_bodyid)
            logger.info(f"Fallback: selected first available bodyId {fallback_bodyid}")

        return selected_bodyids

    def _generate_neuprint_url(self, neuron_type: str, neuron_data: Dict[str, Any]) -> str:
        """
        Generate NeuPrint URL from template with substituted variables.

        Args:
            neuron_type: The neuron type name
            neuron_data: Data containing neuron information

        Returns:
            NeuPrint URL for searching this neuron type
        """
        try:
            # Build NeuPrint URL with query parameters
            neuprint_url = (
                f"https://{self.config.neuprint.server}"
                f"/results?dataset={self.config.neuprint.dataset}"
                f"&qt=findneurons"
                f"&qr[0][code]=fn"
                f"&qr[0][ds]={self.config.neuprint.dataset}"
                f"&qr[0][pm][dataset]={self.config.neuprint.dataset}"
                f"&qr[0][pm][all_segments]=false"
                f"&qr[0][pm][enable_contains]=true"
                f"&qr[0][visProps][rowsPerPage]=50"
                f"&tab=0"
                f"&qr[0][pm][neuron_name]={urllib.parse.quote(neuron_type)}"
            )
            if neuron_data.get('soma_side', None) in ['left', 'right']:
                nd = neuron_data.get('soma_side', '')
                neuprint_url += f"_{nd[:1].upper()}"

            return neuprint_url

        except Exception as e:
            # Return a fallback URL if URL generation fails
            print(f"Warning: Failed to generate NeuPrint URL for {neuron_type}: {e}")
            return f"https://{self.config.neuprint.server}/?dataset={self.config.neuprint.dataset}"

    def _get_available_soma_sides(self, neuron_type: str, connector) -> Dict[str, str]:
        """
        Get available soma sides for a neuron type and generate navigation links.

        Args:
            neuron_type: The neuron type name
            connector: NeuPrint connector instance

        Returns:
            Dict with soma sides and their corresponding filenames
        """
        try:
            # Use optimized query for single neuron type instead of querying all types
            available_sides = connector.get_soma_sides_for_type(neuron_type)

            # Map soma side codes to readable names and generate filenames
            side_mapping = {
                'L': ('left', '_L'),
                'R': ('right', '_R'),
                'M': ('middle', '_M')
            }

            soma_side_links = {}

            # Only create navigation if there are multiple sides
            if len(available_sides) > 1:
                # Add individual sides
                for side_code in available_sides:
                    if side_code in side_mapping:
                        side_name, file_suffix = side_mapping[side_code]
                        # Generate filename for this soma side
                        clean_type = neuron_type.replace('/', '_').replace(' ', '_')
                        filename = f"{clean_type}{file_suffix}.html"
                        soma_side_links[side_name] = filename

                # Add "both" link (no suffix)
                clean_type = neuron_type.replace('/', '_').replace(' ', '_')
                both_filename = f"{clean_type}.html"
                soma_side_links['both'] = both_filename

            return soma_side_links

        except Exception as e:
            print(f"Warning: Could not get soma sides for {neuron_type}: {e}")
            return {}

    def generate_page(self, neuron_type: str, neuron_data: Dict[str, Any],
                     soma_side: str, connector, image_format: str = 'svg', embed_images: bool = False, uncompress: bool = False) -> str:
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
            connector,
            file_type=image_format,
            save_to_files=not embed_images
        )

        # Generate Neuroglancer URL
        neuroglancer_url = self._generate_neuroglancer_url(neuron_type, neuron_data, soma_side)

        # Generate NeuPrint URL
        neuprint_url = self._generate_neuprint_url(neuron_type, neuron_data)

        # Get available soma sides for navigation
        soma_side_links = self._get_available_soma_sides(neuron_type, connector)



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
            'neuroglancer_url': neuroglancer_url,
            'neuprint_url': neuprint_url,
            'soma_side_links': soma_side_links,
            'generation_time': datetime.now()
        }



        # Render template
        html_content = template.render(**context)

        # Minify HTML content to reduce whitespace (with JS minification for neuron pages)
        if not uncompress:
            html_content = self._minify_html(html_content, minify_js=True)

        # Generate output filename
        output_filename = self._generate_filename(neuron_type, soma_side)
        output_path = self.output_dir / output_filename

        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Generate neuron-search.js if it doesn't exist (only during page generation)
        self._generate_neuron_search_js()

        return str(output_path)

    def generate_page_from_neuron_type(self, neuron_type_obj, connector, image_format: str = 'svg', embed_images: bool = False, uncompress: bool = False) -> str:
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

        # Analyze layer-based ROI data for neurons with layer assignments
        layer_analysis = self._analyze_layer_roi_data(
            neuron_data.get('roi_counts'),
            neuron_data.get('neurons'),
            neuron_type_obj.soma_side,
            neuron_type_obj.name,
            connector
        )

        # Analyze column-based ROI data for neurons with column assignments
        column_analysis = self._analyze_column_roi_data(
            neuron_data.get('roi_counts'),
            neuron_data.get('neurons'),
            neuron_type_obj.soma_side,
            neuron_type_obj.name,
            connector,
            file_type=image_format,
            save_to_files=not embed_images
        )

        # Generate Neuroglancer URL
        neuroglancer_url = self._generate_neuroglancer_url(neuron_type_obj.name, neuron_data, neuron_type_obj.soma_side)

        # Generate NeuPrint URL
        neuprint_url = self._generate_neuprint_url(neuron_type_obj.name, neuron_data)

        # Get available soma sides for navigation
        soma_side_links = self._get_available_soma_sides(neuron_type_obj.name, connector)



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
            'layer_analysis': layer_analysis,
            'column_analysis': column_analysis,
            'neuroglancer_url': neuroglancer_url,
            'neuprint_url': neuprint_url,
            'soma_side_links': soma_side_links,
            'generation_time': datetime.now()
        }



        # Render template
        html_content = template.render(**context)

        # Minify HTML content to reduce whitespace (with JS minification for neuron pages)
        if not uncompress:
            html_content = self._minify_html(html_content, minify_js=True)

        # Generate output filename
        output_filename = self._generate_filename(neuron_type_obj.name, neuron_type_obj.soma_side)
        output_path = self.output_dir / output_filename

        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Generate neuron-search.js if it doesn't exist (only during page generation)
        self._generate_neuron_search_js()

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
            roi_aggregated['pre_percentage'] = roi_aggregated['pre'] / total_pre_synapses * 100
        else:
            roi_aggregated['pre_percentage'] = 0.0

        total_post_synapses = roi_aggregated['post'].sum()

        # Calculate percentage of post-synapses for each ROI
        if total_post_synapses > 0:
            roi_aggregated['post_percentage'] = roi_aggregated['post'] / total_post_synapses * 100
        else:
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
                'downstream': int(row['downstream']),
                'upstream': int(row['upstream'])
            })

        return roi_summary

    def _analyze_layer_roi_data(self, roi_counts_df, neurons_df, soma_side, neuron_type, connector):
        """
        Analyze ROI data for layer-based regions matching pattern (ME|LO|LOP)_[LR]_layer_<number>.
        When layer innervation is detected, also include AME, LA, and centralBrain regions.
        Returns additional table with layer-specific synapse counts.

        Args:
            roi_counts_df: DataFrame with ROI count data
            neurons_df: DataFrame with neuron data
            soma_side: Side of soma (left/right)
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

        # Pattern to match layer ROIs: (ME|LO|LOP)_[LR]_layer_<number>
        layer_pattern = r'^(ME|LO|LOP)_([LR])_layer_(\d+)$'

        # Filter ROIs that match the layer pattern
        layer_rois = roi_counts_soma_filtered[
            roi_counts_soma_filtered['roi'].str.match(layer_pattern, na=False)
        ].copy()

        # Check if we have any layer connections (ME, LO, or LOP layers)
        has_layer_connections = not layer_rois.empty

        if not has_layer_connections:
            return None

        # Since we have layer connections, always show the table with required entries
        additional_roi_data = []

        # Get dataset-specific central brain ROIs using ROI strategy
        from .dataset_adapters import DatasetAdapterFactory

        # Get the appropriate adapter for this dataset
        if hasattr(self, 'config') and hasattr(self.config.neuprint, 'dataset'):
            dataset_name = self.config.neuprint.dataset
        else:
            dataset_name = 'optic-lobe'  # fallback

        adapter = DatasetAdapterFactory.create_adapter(dataset_name)
        all_rois = roi_counts_soma_filtered['roi'].unique().tolist()
        central_brain_rois = adapter.query_central_brain_rois(all_rois)

        # ALWAYS add consolidated central brain entry (even if 0 synapses)
        central_brain_pre_total = 0
        central_brain_post_total = 0

        # Add central brain ROIs
        for roi in central_brain_rois:
            matching_rois = roi_counts_soma_filtered[
                roi_counts_soma_filtered['roi'] == roi
            ]
            if not matching_rois.empty:
                central_brain_pre_total += matching_rois['pre'].fillna(0).sum()
                central_brain_post_total += matching_rois['post'].fillna(0).sum()

        # Count unique neurons for central brain
        central_brain_bodyids = set()
        for roi in central_brain_rois:
            matching_rois = roi_counts_soma_filtered[
                roi_counts_soma_filtered['roi'] == roi
            ]
            if not matching_rois.empty:
                central_brain_bodyids.update(matching_rois['bodyId'].unique())

        central_brain_neuron_count = len(central_brain_bodyids)

        # Calculate mean synapses per neuron for central brain using dash vs 0.0 logic
        if central_brain_neuron_count == 0 or central_brain_pre_total == 0:
            central_brain_mean_pre = "-"
        else:
            mean_pre = central_brain_pre_total / central_brain_neuron_count
            rounded_mean_pre = round(mean_pre, 2)
            central_brain_mean_pre = rounded_mean_pre if rounded_mean_pre > 0 else 0.0

        if central_brain_neuron_count == 0 or central_brain_post_total == 0:
            central_brain_mean_post = "-"
        else:
            mean_post = central_brain_post_total / central_brain_neuron_count
            rounded_mean_post = round(mean_post, 2)
            central_brain_mean_post = rounded_mean_post if rounded_mean_post > 0 else 0.0

        if central_brain_mean_pre == "-" and central_brain_mean_post == "-":
            central_brain_mean_total = "-"
        elif central_brain_mean_pre == "-":
            central_brain_mean_total = central_brain_mean_post
        elif central_brain_mean_post == "-":
            central_brain_mean_total = central_brain_mean_pre
        else:
            central_brain_mean_total = round(central_brain_mean_pre + central_brain_mean_post, 2)

        additional_roi_data.append({
            'roi': 'central brain',
            'region': 'central brain',
            'side': 'Both',
            'layer': 0,  # Not a layer, but we use 0 to distinguish
            'bodyId': central_brain_neuron_count,
            'pre': central_brain_mean_pre,
            'post': central_brain_mean_post,
            'total': central_brain_mean_total
        })

        # ALWAYS add AME entry (even if 0 synapses)
        ame_pre_total = 0
        ame_post_total = 0
        for roi in all_rois:
            roi_base = roi.replace('(L)', '').replace('(R)', '').replace('_L', '').replace('_R', '')
            if roi_base == 'AME':
                matching_rois = roi_counts_soma_filtered[
                    roi_counts_soma_filtered['roi'] == roi
                ]
                if not matching_rois.empty:
                    ame_pre_total += matching_rois['pre'].fillna(0).sum()
                    ame_post_total += matching_rois['post'].fillna(0).sum()

        # Count unique neurons for AME
        ame_bodyids = set()
        for roi in all_rois:
            roi_base = roi.replace('(L)', '').replace('(R)', '').replace('_L', '').replace('_R', '')
            if roi_base == 'AME':
                matching_rois = roi_counts_soma_filtered[
                    roi_counts_soma_filtered['roi'] == roi
                ]
                if not matching_rois.empty:
                    ame_bodyids.update(matching_rois['bodyId'].unique())

        ame_neuron_count = len(ame_bodyids)

        # Calculate mean synapses per neuron for AME using dash vs 0.0 logic
        if ame_neuron_count == 0 or ame_pre_total == 0:
            ame_mean_pre = "-"
        else:
            mean_pre = ame_pre_total / ame_neuron_count
            rounded_mean_pre = round(mean_pre, 2)
            ame_mean_pre = rounded_mean_pre if rounded_mean_pre > 0 else 0.0

        if ame_neuron_count == 0 or ame_post_total == 0:
            ame_mean_post = "-"
        else:
            mean_post = ame_post_total / ame_neuron_count
            rounded_mean_post = round(mean_post, 2)
            ame_mean_post = rounded_mean_post if rounded_mean_post > 0 else 0.0

        if ame_mean_pre == "-" and ame_mean_post == "-":
            ame_mean_total = "-"
        elif ame_mean_pre == "-":
            ame_mean_total = ame_mean_post
        elif ame_mean_post == "-":
            ame_mean_total = ame_mean_pre
        else:
            ame_mean_total = round(ame_mean_pre + ame_mean_post, 2)

        additional_roi_data.append({
            'roi': 'AME',
            'region': 'AME',
            'side': 'Both',
            'layer': 0,
            'bodyId': ame_neuron_count,
            'pre': ame_mean_pre,
            'post': ame_mean_post,
            'total': ame_mean_total
        })

        # ALWAYS add LA entry (even if 0 synapses)
        la_pre_total = 0
        la_post_total = 0
        for roi in all_rois:
            roi_base = roi.replace('(L)', '').replace('(R)', '').replace('_L', '').replace('_R', '')
            if roi_base == 'LA':
                matching_rois = roi_counts_soma_filtered[
                    roi_counts_soma_filtered['roi'] == roi
                ]
                if not matching_rois.empty:
                    la_pre_total += matching_rois['pre'].fillna(0).sum()
                    la_post_total += matching_rois['post'].fillna(0).sum()

        # Count unique neurons for LA
        la_bodyids = set()
        for roi in all_rois:
            roi_base = roi.replace('(L)', '').replace('(R)', '').replace('_L', '').replace('_R', '')
            if roi_base == 'LA':
                matching_rois = roi_counts_soma_filtered[
                    roi_counts_soma_filtered['roi'] == roi
                ]
                if not matching_rois.empty:
                    la_bodyids.update(matching_rois['bodyId'].unique())

        la_neuron_count = len(la_bodyids)

        # Calculate mean synapses per neuron for LA using dash vs 0.0 logic
        if la_neuron_count == 0 or la_pre_total == 0:
            la_mean_pre = "-"
        else:
            mean_pre = la_pre_total / la_neuron_count
            rounded_mean_pre = round(mean_pre, 2)
            la_mean_pre = rounded_mean_pre if rounded_mean_pre > 0 else 0.0

        if la_neuron_count == 0 or la_post_total == 0:
            la_mean_post = "-"
        else:
            mean_post = la_post_total / la_neuron_count
            rounded_mean_post = round(mean_post, 2)
            la_mean_post = rounded_mean_post if rounded_mean_post > 0 else 0.0

        if la_mean_pre == "-" and la_mean_post == "-":
            la_mean_total = "-"
        elif la_mean_pre == "-":
            la_mean_total = la_mean_post
        elif la_mean_post == "-":
            la_mean_total = la_mean_pre
        else:
            la_mean_total = round(la_mean_pre + la_mean_post, 2)

        additional_roi_data.append({
            'roi': 'LA',
            'region': 'LA',
            'side': 'Both',
            'layer': 0,
            'bodyId': la_neuron_count,
            'pre': la_mean_pre,
            'post': la_mean_post,
            'total': la_mean_total
        })

        # Extract layer information and aggregate by layer
        layer_info = []
        for _, row in layer_rois.iterrows():
            match = re.match(layer_pattern, row['roi'])
            if match:
                region, side, layer_num = match.groups()
                layer_info.append({
                    'roi': row['roi'],
                    'region': region,
                    'side': side,
                    'layer': int(layer_num),
                    'bodyId': row['bodyId'],  # Include bodyId for proper grouping
                    'pre': row.get('pre', 0),
                    'post': row.get('post', 0),
                    'total': row.get('total', row.get('pre', 0) + row.get('post', 0))
                })

        if not layer_info:
            return None

        # Query the ENTIRE dataset for all available layers (not just this neuron type)
        all_dataset_layers = self._get_all_dataset_layers(layer_pattern, connector)

        # Process layer data separately from non-layer data to handle types correctly

        # First process only layer data (numeric calculations)
        layer_df = pd.DataFrame(layer_info)

        # Calculate mean synapses per neuron with special handling for no synapses
        def calculate_mean_or_dash(total_synapses, neuron_count):
            if neuron_count == 0 or total_synapses == 0:
                return "-"  # No synapses at all
            mean = total_synapses / neuron_count
            rounded_mean = round(mean, 2)
            return rounded_mean if rounded_mean > 0 else 0.0  # Show 0.0 if rounds to zero but has synapses

        layer_aggregated = None
        if not layer_df.empty:
            # Group by region, side, and layer number to calculate mean synapses per neuron
            layer_aggregated = layer_df.groupby(['region', 'side', 'layer']).agg({
                'bodyId': 'nunique',
                'pre': 'sum',
                'post': 'sum',
                'total': 'sum'
            }).reset_index()

            # Rename columns for clarity
            layer_aggregated = layer_aggregated.rename(columns={
                'bodyId': 'neuron_count',
                'pre': 'total_pre',
                'post': 'total_post',
                'total': 'total_synapses'
            })

            # Calculate means for layer data
            layer_aggregated['mean_pre'] = layer_aggregated.apply(
                lambda row: calculate_mean_or_dash(row['total_pre'], row['neuron_count']), axis=1
            )
            layer_aggregated['mean_post'] = layer_aggregated.apply(
                lambda row: calculate_mean_or_dash(row['total_post'], row['neuron_count']), axis=1
            )
            layer_aggregated['mean_total'] = layer_aggregated.apply(
                lambda row: calculate_mean_or_dash(row['total_synapses'], row['neuron_count']), axis=1
            )

        # Create complete layer summary including all dataset layers (even with 0 connections)
        layer_summary = []

        # First add non-layer entries (central brain, AME, LA) - these already have calculated means
        for entry in additional_roi_data:
            layer_summary.append({
                'region': entry['region'],
                'side': entry['side'],
                'layer': entry['layer'],
                'neuron_count': entry['bodyId'],
                'pre': entry['pre'],
                'post': entry['post'],
                'total': entry['total'],
                'total_pre': 0,  # These don't have separate total tracking
                'total_post': 0,
                'total_synapses': 0
            })

        # Then add all possible layer entries from dataset
        # Filter layers to match the soma side of the neuron type
        added_layers = set()  # Track which layers we've already added

        # Map soma_side values to layer side letters
        def get_matching_layer_sides(soma_side):
            if soma_side == 'left':
                return ['L']
            elif soma_side == 'right':
                return ['R']
            elif soma_side == 'both' or soma_side == 'all':
                return ['L', 'R']
            else:
                # Default to both sides if soma_side is unclear
                return ['L', 'R']

        matching_sides = get_matching_layer_sides(soma_side)

        for region, side, layer_num in sorted(all_dataset_layers):
            # Skip layers that don't match the soma side
            if side not in matching_sides:
                continue
            layer_key = (region, side, layer_num)
            added_layers.add(layer_key)

            # Check if this layer has data in our aggregated results
            if layer_aggregated is not None:
                matching_rows = layer_aggregated[
                    (layer_aggregated['region'] == region) &
                    (layer_aggregated['side'] == side) &
                    (layer_aggregated['layer'] == layer_num)
                ]

                if not matching_rows.empty:
                    # Use actual data
                    row = matching_rows.iloc[0]
                    layer_summary.append({
                        'region': row['region'],
                        'side': row['side'],
                        'layer': int(row['layer']),
                        'neuron_count': int(row['neuron_count']),
                        'pre': row['mean_pre'] if isinstance(row['mean_pre'], str) else float(row['mean_pre']),
                        'post': row['mean_post'] if isinstance(row['mean_post'], str) else float(row['mean_post']),
                        'total': row['mean_total'] if isinstance(row['mean_total'], str) else float(row['mean_total']),
                        'total_pre': int(row['total_pre']),
                        'total_post': int(row['total_post']),
                        'total_synapses': int(row['total_synapses'])
                    })
                    continue

            # Add with 0 values if no data found
            layer_summary.append({
                'region': region,
                'side': side,
                'layer': layer_num,
                'neuron_count': 0,
                'pre': "-",
                'post': "-",
                'total': "-",
                'total_pre': 0,
                'total_post': 0,
                'total_synapses': 0
            })

        # Also add any actual layer data that wasn't covered by dataset query
        if layer_aggregated is not None:
            layer_entries = layer_aggregated[layer_aggregated['layer'] > 0]
            for _, row in layer_entries.iterrows():
                layer_key = (row['region'], row['side'], int(row['layer']))
                if layer_key not in added_layers:
                    layer_summary.append({
                        'region': row['region'],
                        'side': row['side'],
                        'layer': int(row['layer']),
                        'neuron_count': int(row['neuron_count']),
                        'pre': row['mean_pre'] if isinstance(row['mean_pre'], str) else float(row['mean_pre']),
                        'post': row['mean_post'] if isinstance(row['mean_post'], str) else float(row['mean_post']),
                        'total': row['mean_total'] if isinstance(row['mean_total'], str) else float(row['mean_total']),
                        'total_pre': int(row['total_pre']),
                        'total_post': int(row['total_post']),
                        'total_synapses': int(row['total_synapses'])
                    })

        # Organize data into 6 containers
        containers = {
            'la': {'columns': ['LA'], 'data': {}},
            'me': {'columns': [], 'data': {}},
            'lo': {'columns': [], 'data': {}},
            'lop': {'columns': [], 'data': {}},
            'ame': {'columns': ['AME'], 'data': {}},
            'central_brain': {'columns': ['central brain'], 'data': {}}
        }

        # Collect all layers for each region type from both dataset query and actual data
        me_layers = set()
        lo_layers = set()
        lop_layers = set()

        # First, get layers from dataset query if available
        for region, side, layer_num in all_dataset_layers:
            if region == 'ME':
                me_layers.add(layer_num)
            elif region == 'LO':
                lo_layers.add(layer_num)
            elif region == 'LOP':
                lop_layers.add(layer_num)

        # Also collect layers from actual data in case dataset query failed
        for layer in layer_info:
            region = layer['region']
            layer_num = layer['layer']
            if region == 'ME':
                me_layers.add(layer_num)
            elif region == 'LO':
                lo_layers.add(layer_num)
            elif region == 'LOP':
                lop_layers.add(layer_num)

        # Set up column headers for layer regions
        containers['me']['columns'] = [f'ME {i}' for i in sorted(me_layers)] + ['Total'] if me_layers else []
        containers['lo']['columns'] = [f'LO {i}' for i in sorted(lo_layers)] + ['Total'] if lo_layers else []
        containers['lop']['columns'] = [f'LOP {i}' for i in sorted(lop_layers)] + ['Total'] if lop_layers else []

        # Initialize all container data with dashes (no synapses)
        for container_name, container in containers.items():
            container['data'] = {
                'pre': {col: "-" for col in container['columns']},
                'post': {col: "-" for col in container['columns']},
                'neuron_count': {col: 0 for col in container['columns']}
            }

        # Populate containers with actual mean data
        for layer in layer_summary:
            region = layer['region']
            layer_num = layer['layer']
            pre = layer['pre']
            post = layer['post']
            neuron_count = layer['neuron_count']

            if region == 'LA':
                containers['la']['data']['pre']['LA'] = pre
                containers['la']['data']['post']['LA'] = post
                containers['la']['data']['neuron_count']['LA'] = neuron_count
            elif region == 'AME':
                containers['ame']['data']['pre']['AME'] = pre
                containers['ame']['data']['post']['AME'] = post
                containers['ame']['data']['neuron_count']['AME'] = neuron_count
            elif region == 'central brain':
                containers['central_brain']['data']['pre']['central brain'] = pre
                containers['central_brain']['data']['post']['central brain'] = post
                containers['central_brain']['data']['neuron_count']['central brain'] = neuron_count
            elif region == 'ME' and layer_num > 0:
                col_name = f'ME {layer_num}'
                if col_name in containers['me']['data']['pre']:
                    containers['me']['data']['pre'][col_name] = pre
                    containers['me']['data']['post'][col_name] = post
                    containers['me']['data']['neuron_count'][col_name] = neuron_count
            elif region == 'LO' and layer_num > 0:
                col_name = f'LO {layer_num}'
                if col_name in containers['lo']['data']['pre']:
                    containers['lo']['data']['pre'][col_name] = pre
                    containers['lo']['data']['post'][col_name] = post
                    containers['lo']['data']['neuron_count'][col_name] = neuron_count
            elif region == 'LOP' and layer_num > 0:
                col_name = f'LOP {layer_num}'
                if col_name in containers['lop']['data']['pre']:
                    containers['lop']['data']['pre'][col_name] = pre
                    containers['lop']['data']['post'][col_name] = post
                    containers['lop']['data']['neuron_count'][col_name] = neuron_count

        # Calculate totals for multi-layer regions
        for region_name in ['me', 'lo', 'lop']:
            container = containers[region_name]
            if 'Total' in container['columns']:
                # Sum the mean values for this region (exclude "-" values)
                pre_sum = 0.0
                post_sum = 0.0
                total_neurons = 0
                layers_with_data = 0

                for col in container['columns']:
                    if col != 'Total':
                        pre_val = container['data']['pre'][col]
                        post_val = container['data']['post'][col]
                        neuron_count = container['data']['neuron_count'][col]

                        if isinstance(pre_val, (int, float)) and pre_val != "-":
                            pre_sum += pre_val
                            layers_with_data += 1
                        if isinstance(post_val, (int, float)) and post_val != "-":
                            post_sum += post_val

                        if neuron_count > 0:
                            total_neurons += neuron_count

                # Set totals as sum of layer means
                if layers_with_data > 0:
                    container['data']['pre']['Total'] = round(pre_sum, 1)
                    container['data']['post']['Total'] = round(post_sum, 1)
                    container['data']['neuron_count']['Total'] = total_neurons
                else:
                    container['data']['pre']['Total'] = "-"
                    container['data']['post']['Total'] = "-"
                    container['data']['neuron_count']['Total'] = 0

        # Generate summary statistics
        total_layers = len(layer_summary)
        if total_layers > 0:
            # Calculate mean pre/post across all layers (excluding dash values)
            layers_with_neurons = [layer for layer in layer_summary if layer['neuron_count'] > 0]
            if layers_with_neurons:
                numeric_pre_values = [layer['pre'] for layer in layers_with_neurons if isinstance(layer['pre'], (int, float))]
                numeric_post_values = [layer['post'] for layer in layers_with_neurons if isinstance(layer['post'], (int, float))]

                mean_pre = sum(numeric_pre_values) / len(numeric_pre_values) if numeric_pre_values else 0.0
                mean_post = sum(numeric_post_values) / len(numeric_post_values) if numeric_post_values else 0.0
            else:
                mean_pre = 0.0
                mean_post = 0.0

            # Calculate total synapse counts for reference
            total_pre_synapses = sum(layer.get('total_pre', 0) for layer in layer_summary)
            total_post_synapses = sum(layer.get('total_post', 0) for layer in layer_summary)

            # Group by region for region-specific stats
            region_stats = {}
            for layer in layer_summary:
                region = layer['region']
                if region not in region_stats:
                    region_stats[region] = {
                        'layers': 0,
                        'mean_pre': 0.0,
                        'mean_post': 0.0,
                        'total_pre': 0,
                        'total_post': 0,
                        'neuron_count': 0,
                        'sides': set()
                    }
                region_stats[region]['layers'] += 1
                region_stats[region]['total_pre'] += layer.get('total_pre', 0)
                region_stats[region]['total_post'] += layer.get('total_post', 0)
                region_stats[region]['neuron_count'] += layer['neuron_count']
                region_stats[region]['sides'].add(layer['side'])

            # Calculate mean per region
            for region in region_stats:
                if region_stats[region]['neuron_count'] > 0:
                    region_stats[region]['mean_pre'] = round(region_stats[region]['total_pre'] / region_stats[region]['neuron_count'], 2)
                    region_stats[region]['mean_post'] = round(region_stats[region]['total_post'] / region_stats[region]['neuron_count'], 2)
                else:
                    region_stats[region]['mean_pre'] = 0.0
                    region_stats[region]['mean_post'] = 0.0
                region_stats[region]['sides'] = sorted(list(region_stats[region]['sides']))
        else:
            mean_pre = 0.0
            mean_post = 0.0
            total_pre_synapses = 0
            total_post_synapses = 0
            region_stats = {}

        return {
            'containers': containers,
            'layers': layer_summary,  # Keep original for backwards compatibility
            'summary': {
                'total_layers': total_layers,
                'mean_pre': round(mean_pre, 2),
                'mean_post': round(mean_post, 2),
                'total_pre_synapses': total_pre_synapses,
                'total_post_synapses': total_post_synapses,
                'regions': region_stats
            }
        }

    def _get_all_dataset_layers(self, layer_pattern, connector):
        """
        Query the entire dataset for all available layer patterns.

        Args:
            layer_pattern: Regex pattern to match layer ROIs
            connector: NeuPrint connector to query the database

        Returns:
            List of tuples: (region, side, layer_num) for all layers in dataset
        """
        import re

        try:
            # Query for all ROI names in the dataset
            from neuprint import fetch_roi_hierarchy

            # Try to get all ROIs from hierarchy first
            roi_hierarchy = fetch_roi_hierarchy()
            all_rois = []

            if roi_hierarchy:
                def extract_roi_names(hierarchy_dict):
                    """Recursively extract ROI names from hierarchy."""
                    roi_names = []
                    if isinstance(hierarchy_dict, dict):
                        for key, value in hierarchy_dict.items():
                            # Remove * marker if present
                            clean_key = key.rstrip('*')
                            roi_names.append(clean_key)
                            if isinstance(value, dict):
                                roi_names.extend(extract_roi_names(value))
                    return roi_names

                all_rois = extract_roi_names(roi_hierarchy)

            # Fallback: query database directly if hierarchy fails
            if not all_rois:
                query = """
                MATCH (r:Roi)
                RETURN r.name as roi
                ORDER BY r.name
                """
                result = connector.client.fetch_custom(query)
                if hasattr(result, 'iterrows'):
                    all_rois = [record['roi'] for _, record in result.iterrows()]

            # Extract layer patterns from all ROIs
            all_dataset_layers = []
            for roi in all_rois:
                match = re.match(layer_pattern, roi)
                if match:
                    region = match.group(1)
                    side = match.group(2)
                    layer_num = int(match.group(3))
                    layer_key = (region, side, layer_num)
                    if layer_key not in all_dataset_layers:
                        all_dataset_layers.append(layer_key)

            return sorted(all_dataset_layers)

        except Exception as e:
            print(f"Warning: Could not query dataset for all layers: {e}")
            # Fallback: return empty list, will use only layers from current neuron
            return []

    def _get_columns_for_neuron_type(self, connector, neuron_type: str):
        """
        Query the dataset to get column coordinates that exist for a specific neuron type.
        This optimized version only processes the requested neuron type instead of all neurons.

        Args:
            connector: NeuPrint connector instance for database queries
            neuron_type: Specific neuron type to analyze

        Returns:
            Tuple of (type_columns, region_columns_map) where:
            - type_columns: List of dicts with hex1, hex2, hex1_dec, hex2_dec for this type
            - region_columns_map: Dict mapping region_side names to sets of (hex1_dec, hex2_dec) tuples
        """
        import re
        import time
        start_time = time.time()

        # Check cache first
        cache_key = f"columns_{neuron_type}"
        if hasattr(self, '_neuron_type_columns_cache') and cache_key in self._neuron_type_columns_cache:
            logger.info(f"_get_columns_for_neuron_type({neuron_type}): returning cached result")
            return self._neuron_type_columns_cache[cache_key]

        try:
            # Optimized query for specific neuron type only
            escaped_type = connector._escape_regex_chars(neuron_type)
            query = f"""
                MATCH (n:Neuron)
                WHERE n.type = '{escaped_type}' AND n.roiInfo IS NOT NULL
                WITH n, apoc.convert.fromJsonMap(n.roiInfo) as roiData
                UNWIND keys(roiData) as roiName
                WITH roiName, roiData[roiName] as roiInfo
                WHERE roiName =~ '^(ME|LO|LOP)_[RL]_col_[A-Za-z0-9]+_[A-Za-z0-9]+$'
                AND (roiInfo.pre > 0 OR roiInfo.post > 0)
                WITH roiName,
                     SUM(COALESCE(roiInfo.pre, 0)) as total_pre,
                     SUM(COALESCE(roiInfo.post, 0)) as total_post
                RETURN roiName as roi, total_pre as pre, total_post as post
                ORDER BY roi
            """

            result = connector.client.fetch_custom(query)
            query_time = time.time() - start_time

            if result is None or result.empty:
                logger.info(f"_get_columns_for_neuron_type({neuron_type}): no columns found in {query_time:.3f}s")
                return [], {}

            # Parse ROI data to extract coordinates
            column_pattern = r'^(ME|LO|LOP)_([RL])_col_([A-Za-z0-9]+)_([A-Za-z0-9]+)$'
            column_data = {}
            coordinate_strings = {}

            for _, row in result.iterrows():
                match = re.match(column_pattern, row['roi'])
                if match:
                    region, side, coord1, coord2 = match.groups()

                    # Parse coordinates
                    try:
                        hex1_dec = int(coord1) if coord1.isdigit() else int(coord1, 16)
                        hex2_dec = int(coord2) if coord2.isdigit() else int(coord2, 16)
                    except ValueError:
                        continue

                    coord_key = (hex1_dec, hex2_dec)
                    if coord_key not in column_data:
                        column_data[coord_key] = set()
                    column_data[coord_key].add(f"{region}_{side}")
                    coordinate_strings[coord_key] = (coord1, coord2)

            # Build region columns map
            region_columns_map = {
                'ME_L': set(), 'LO_L': set(), 'LOP_L': set(),
                'ME_R': set(), 'LO_R': set(), 'LOP_R': set(),
                'ME': set(), 'LO': set(), 'LOP': set()
            }

            for coord_key, region_sides in column_data.items():
                for region_side in region_sides:
                    region_columns_map[region_side].add(coord_key)
                    # Add to legacy region keys
                    base_region = region_side.rsplit('_', 1)[0]
                    if base_region in region_columns_map:
                        region_columns_map[base_region].add(coord_key)

            # Build columns list
            type_columns = []
            for coord_key in sorted(column_data.keys()):
                hex1_dec, hex2_dec = coord_key
                hex1_str, hex2_str = coordinate_strings[coord_key]
                type_columns.append({
                    'hex1': hex1_str,
                    'hex2': hex2_str,
                    'hex1_dec': hex1_dec,
                    'hex2_dec': hex2_dec
                })

            # Cache the result
            if not hasattr(self, '_neuron_type_columns_cache'):
                self._neuron_type_columns_cache = {}

            result_tuple = (type_columns, region_columns_map)
            self._neuron_type_columns_cache[cache_key] = result_tuple

            logger.info(f"_get_columns_for_neuron_type({neuron_type}): found {len(type_columns)} columns in {time.time() - start_time:.3f}s")
            return result_tuple

        except Exception as e:
            logger.warning(f"Could not query columns for {neuron_type}: {e}")
            return [], {}

    def _get_all_possible_columns_from_dataset(self, connector):
        """
        Query the dataset to get all possible column coordinates that exist anywhere
        in ME, LO, or LOP regions, determining column existence based on actual
        neuron innervation (pre > 0 OR post > 0) across all neuron types.

        This method is cached to avoid expensive repeated queries.

        Args:
            connector: NeuPrint connector instance for database queries

        Returns:
            Tuple of (all_possible_columns, region_columns_map) where:
            - all_possible_columns: List of dicts with hex1, hex2, hex1_dec, hex2_dec
            - region_columns_map: Dict mapping region_side names to sets of (hex1_dec, hex2_dec) tuples
        """
        # Return cached result if available
        if self._all_columns_cache is not None:
            logger.info("_get_all_possible_columns_from_dataset: returning cached result")
            return self._all_columns_cache
        import re

        try:
            # Query all column ROIs from neuron roiInfo JSON data with aggregated counts
            query = """
                MATCH (n:Neuron)
                WHERE n.roiInfo IS NOT NULL
                WITH n, apoc.convert.fromJsonMap(n.roiInfo) as roiData
                UNWIND keys(roiData) as roiName
                WITH roiName, roiData[roiName] as roiInfo
                WHERE roiName =~ '^(ME|LO|LOP)_[RL]_col_[A-Za-z0-9]+_[A-Za-z0-9]+$'
                AND (roiInfo.pre > 0 OR roiInfo.post > 0)
                WITH roiName,
                     SUM(COALESCE(roiInfo.pre, 0)) as total_pre,
                     SUM(COALESCE(roiInfo.post, 0)) as total_post
                RETURN roiName as roi, total_pre as pre, total_post as post
                ORDER BY roi
            """

            result = connector.client.fetch_custom(query)

            if result is None or result.empty:
                return [], {}

            # Parse all ROI data to extract coordinates and regions with side information
            column_pattern = r'^(ME|LO|LOP)_([RL])_col_([A-Za-z0-9]+)_([A-Za-z0-9]+)$'
            column_data = {}  # Maps (hex1_dec, hex2_dec) to set of region_side combinations that have this column
            coordinate_strings = {}  # Maps (hex1_dec, hex2_dec) to (hex1_str, hex2_str)

            for _, row in result.iterrows():
                match = re.match(column_pattern, row['roi'])
                if match:
                    region, side, coord1, coord2 = match.groups()

                    # Try to parse coordinates as decimal first, then hex if that fails
                    try:
                        hex1_dec = int(coord1)
                    except ValueError:
                        try:
                            hex1_dec = int(coord1, 16)
                        except ValueError:
                            continue  # Skip invalid coordinates

                    try:
                        hex2_dec = int(coord2)
                    except ValueError:
                        try:
                            hex2_dec = int(coord2, 16)
                        except ValueError:
                            continue  # Skip invalid coordinates

                    coord_key = (hex1_dec, hex2_dec)

                    # Track which region_side combinations have this column coordinate
                    if coord_key not in column_data:
                        column_data[coord_key] = set()
                    column_data[coord_key].add(f"{region}_{side}")

                    # Store string representation for later use
                    coordinate_strings[coord_key] = (coord1, coord2)

            # Build side-specific region columns map - each region_side contains only columns where there's actual innervation
            region_columns_map = {
                'ME_L': set(), 'LO_L': set(), 'LOP_L': set(),
                'ME_R': set(), 'LO_R': set(), 'LOP_R': set(),
                # Also maintain legacy keys for backward compatibility
                'ME': set(), 'LO': set(), 'LOP': set()
            }
            for coord_key, region_sides in column_data.items():
                for region_side in region_sides:
                    region_columns_map[region_side].add(coord_key)
                    # Also add to legacy region keys (combined L+R for backward compatibility)
                    if region_side.endswith('_L') or region_side.endswith('_R'):
                        base_region = region_side.rsplit('_', 1)[0]
                        if base_region in region_columns_map:
                            region_columns_map[base_region].add(coord_key)

            # Build all possible columns list from all discovered coordinates
            all_possible_columns = []
            for coord_key in sorted(column_data.keys()):
                hex1_dec, hex2_dec = coord_key
                hex1_str, hex2_str = coordinate_strings[coord_key]
                all_possible_columns.append({
                    'hex1': hex1_str,
                    'hex2': hex2_str,
                    'hex1_dec': hex1_dec,
                    'hex2_dec': hex2_dec
                })

            # Cache the result for future use
            result = (all_possible_columns, region_columns_map)
            self._all_columns_cache = result
            logger.info(f"_get_all_possible_columns_from_dataset: cached {len(all_possible_columns)} columns")
            return result

        except Exception as e:
            logger.warning(f"Could not query dataset for all columns: {e}")
            return [], {}

    def _analyze_column_roi_data(self, roi_counts_df, neurons_df, soma_side, neuron_type, connector, file_type: str = 'svg', save_to_files: bool = True):
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
            connector: NeuPrint connector instance for database queries
            file_type: Output format for hexagonal grids ('svg' or 'png')
            save_to_files: If True, save files to disk; if False, embed content
        """
        import time
        start_time = time.time()

        # Create cache key for this specific analysis
        cache_key = f"{neuron_type}_{soma_side}_{file_type}_{save_to_files}"
        if cache_key in self._column_analysis_cache:
            logger.info(f"_analyze_column_roi_data: returning cached result for {cache_key} in {time.time() - start_time:.3f}s")
            return self._column_analysis_cache[cache_key]
        import re

        # Early exit for empty data
        if roi_counts_df is None or roi_counts_df.empty or neurons_df is None or neurons_df.empty:
            logger.info(f"_analyze_column_roi_data: early exit - no data for {neuron_type}_{soma_side} in {time.time() - start_time:.3f}s")
            return None

        # Early exit if no neurons for this neuron type
        if len(neurons_df) == 0:
            logger.info(f"_analyze_column_roi_data: early exit - no neurons found for {neuron_type}_{soma_side} in {time.time() - start_time:.3f}s")
            return None

        # Filter ROI data to include only neurons that belong to this specific soma side
        if 'bodyId' in neurons_df.columns and 'bodyId' in roi_counts_df.columns:
            soma_side_body_ids = set(neurons_df['bodyId'].values)
            roi_counts_soma_filtered = roi_counts_df[roi_counts_df['bodyId'].isin(soma_side_body_ids)]
        else:
            roi_counts_soma_filtered = roi_counts_df

        if roi_counts_soma_filtered.empty:
            logger.info(f"_analyze_column_roi_data: early exit - no ROI data for {neuron_type}_{soma_side} in {time.time() - start_time:.3f}s")
            return None

        # Pattern to match column ROIs: (ME|LO|LOP)_[RL]_col_hex1_hex2
        column_pattern = r'^(ME|LO|LOP)_([RL])_col_([A-Za-z0-9]+)_([A-Za-z0-9]+)$'

        # Filter ROIs that match the column pattern
        column_rois = roi_counts_soma_filtered[
            roi_counts_soma_filtered['roi'].str.match(column_pattern, na=False)
        ].copy()

        if column_rois.empty:
            logger.info(f"_analyze_column_roi_data: early exit - no column ROIs for {neuron_type}_{soma_side} in {time.time() - start_time:.3f}s")
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
            logger.info(f"_analyze_column_roi_data: early exit - no valid column info for {neuron_type}_{soma_side} in {time.time() - start_time:.3f}s")
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

            # Convert sides set to list for consistency
            for region in region_stats:
                region_stats[region]['sides'] = sorted(list(region_stats[region]['sides']))
                region_stats[region]['avg_neurons_per_column'] = float(region_stats[region]['neurons']) / region_stats[region]['columns']
                region_stats[region]['avg_synapses_per_column'] = float(region_stats[region]['synapses']) / region_stats[region]['columns']
        else:
            avg_neurons_per_column = 0
            avg_synapses_per_column = 0.0
            region_stats = {}

        # Get columns for this specific neuron type (optimized approach)
        type_columns, type_region_columns_map = self._get_columns_for_neuron_type(connector, neuron_type)

        # For proper gray/white hexagon logic, we need comprehensive dataset for region existence
        # but we'll use type-specific data for actual data values
        all_possible_columns, region_columns_map = self._get_all_possible_columns_from_dataset(connector)
        logger.info(f"Using comprehensive dataset for gray/white logic, type-specific data for values")

        # Generate comprehensive grids showing all possible columns
        comprehensive_region_grids = {}
        if all_possible_columns:
            comprehensive_region_grids = self.hexagon_generator.generate_comprehensive_region_hexagonal_grids(
                column_summary, all_possible_columns, region_columns_map,
                neuron_type, soma_side, output_format=file_type, save_to_files=save_to_files
            )

        result = {
            'columns': column_summary,
            'summary': {
                'total_columns': total_columns,
                'total_neurons_with_columns': total_neurons_with_columns,
                'avg_neurons_per_column': round(float(avg_neurons_per_column), 1),
                'avg_synapses_per_column': round(float(avg_synapses_per_column), 1),
                'regions': region_stats
            },
            'comprehensive_region_grids': comprehensive_region_grids,
            'all_possible_columns_count': len(all_possible_columns),
            'region_columns_counts': {region: len(coords) for region, coords in region_columns_map.items()}
        }

        # Cache the result for future use
        self._column_analysis_cache[cache_key] = result
        logger.info(f"_analyze_column_roi_data: cached result for {cache_key} in {time.time() - start_time:.3f}s")
        return result



    def _generate_region_hexagonal_grids(self, column_summary: List[Dict], neuron_type: str, soma_side, file_type: str = 'svg', save_to_files: bool = True, connector=None) -> Dict[str, Dict[str, str]]:
        """
        Generate separate hexagonal grid visualizations for each region (ME, LO, LOP).

        Args:
            column_summary: List of column data dictionaries
            neuron_type: Name of the neuron type
            soma_side: Soma side being analyzed
            file_type: Output format ('svg' or 'png')
            save_to_files: If True, save files to output/static/images and return file paths.
                          If False, return content directly for embedding in HTML.
            connector: NeuPrint connector for getting dataset information

        Returns:
            Dictionary mapping region names to visualization data (either file paths or content)
        """
        if file_type not in ['svg', 'png']:
            raise ValueError("file_type must be either 'svg' or 'png'")

        # Get all possible columns from the dataset if connector is available
        all_possible_columns = []
        region_columns_map = {}
        if connector:
            all_possible_columns, region_columns_map = self._get_all_possible_columns_from_dataset(connector)

        return self.hexagon_generator.generate_comprehensive_region_hexagonal_grids(
            column_summary, all_possible_columns, region_columns_map, neuron_type, soma_side, output_format=file_type, save_to_files=save_to_files
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

    def _format_synapse_count(self, value: Any) -> str:
        """Format synapse counts with 1 decimal place display and full precision in tooltip."""
        if isinstance(value, (int, float)):
            # Convert to float to handle both int and float inputs
            float_value = float(value)
            # Round to 1 decimal place for display
            rounded_display = f"{float_value:.1f}"
            # Full precision for tooltip (remove trailing zeros if int)
            if float_value.is_integer():
                full_precision = f"{int(float_value)}"
            else:
                full_precision = str(float_value)
            # Return abbr tag with full precision as title and rounded as display
            return f'<abbr title="{full_precision}">{rounded_display}</abbr>'
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
                'ME(R)', 'ME(L)', 'LO(R)', 'LO(L)',
                'LOP(R)', 'LOP(L)', 'AME(R)', 'AME(L)', 'LA(R)', 'LA(L)'
            }
            primary_rois.update(optic_primary)
        elif 'cns' in dataset_name:
            # CNS specific primary ROIs
            cns_primary = {
                'ME(R)', 'ME(L)', 'LO(R)', 'LO(L)',
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
                'AL(R)', 'AL(L)', 'MB(R)', 'MB(L)', 'CX', 'PB', 'FB', 'EB', 'NO',
                'BU(R)', 'BU(L)', 'LAL(R)', 'LAL(L)', 'ICL(R)', 'ICL(L)', 'IB',
                'ATL(R)', 'ATL(L)'
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

    def _create_neuron_link(self, neuron_type: str, soma_side: str) -> str:
        """Create HTML link to neuron type page based on type and soma side."""
        # Check if we should create a link (only if neuron type is in queue)
        if self.queue_service:
            queued_types = self.queue_service.get_queued_neuron_types()
            if neuron_type not in queued_types:
                # Return just the display text without a link
                return f"{neuron_type} ({soma_side})"

        # Clean neuron type name for filename
        clean_type = neuron_type.replace('/', '_').replace(' ', '_')

        # Handle different soma side formats with new naming scheme
        if soma_side in ['all', 'both']:
            # General page for neuron type (multiple sides available)
            filename = f"{clean_type}.html"
        else:
            # Specific page for single side
            soma_side_suffix = soma_side
            if soma_side_suffix == 'left':
                soma_side_suffix = 'L'
            elif soma_side_suffix == 'right':
                soma_side_suffix = 'R'
            elif soma_side_suffix == 'middle':
                soma_side_suffix = 'M'
            filename = f"{clean_type}_{soma_side_suffix}.html#sec-connectivity"

        # Create the display text (same as original)
        display_text = f"{neuron_type} ({soma_side})"

        # Return HTML link
        return f'<a href="{filename}">{display_text}</a>'

    def _truncate_neuron_name(self, name: str) -> str:
        """
        Truncate neuron type name for display on index page.

        If name is longer than 15 characters, truncate to 13 characters + "…"
        and wrap in an <abbr> tag with the full name as title.

        Args:
            name: The neuron type name to truncate

        Returns:
            HTML string with truncated name or <abbr> tag
        """
        if not name or len(name) <= 13:
            return name

        # Truncate to 13 characters and add ellipsis
        truncated = name[:12] + "…"

        # Return as abbr tag with full name in title
        return truncated
