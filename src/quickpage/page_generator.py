"""
HTML page generator using Jinja2 templates.

This module provides comprehensive HTML page generation functionality for
neuron type reports, including template rendering, static file management,
and output directory organization.
"""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import pandas as pd
from pandas.api.types import is_scalar
import shutil
import re
import json
import urllib.parse
import numpy as np
import logging
import time
from typing import Dict, Any, Optional, List, Tuple

from .config import Config
from .visualization import HexagonGridGenerator
from .utils import (
    NumberFormatter, PercentageFormatter, SynapseFormatter, NeurotransmitterFormatter,
    HTMLUtils, ColorUtils, TextUtils
)
from .services.layer_analysis_service import LayerAnalysisService
from .services.column_analysis_service import ColumnAnalysisService
from .services.url_generation_service import URLGenerationService
from .services.resource_manager_service import ResourceManagerService

logger = logging.getLogger(__name__)


class PageGenerator:
    """
    Generate HTML pages for neuron types.

    This class handles the complete page generation process including template
    rendering, static file copying, and output file management.
    """

    def __init__(self, config: Config, output_dir: str, queue_service=None, cache_manager=None):
        """
        Initialize the page generator.

        Args:
            config: Configuration object with template and output settings
            output_dir: Directory path for generated HTML files
            queue_service: Optional QueueService for checking queued neuron types
            cache_manager: Optional cache manager for accessing cached neuron data
        """
        self.config = config
        self.output_dir = Path(output_dir)
        self.template_dir = Path(config.output.template_dir)
        self.queue_service = queue_service
        self._neuron_cache_manager = cache_manager

        # Load brain regions data for the abbr filter
        self._load_brain_regions()

        # Load citations data for synonyms links
        self._load_citations()

        # Initialize resource manager service
        self.resource_manager = ResourceManagerService(config, self.output_dir)

        # Set up output directories using resource manager
        directories = self.resource_manager.setup_output_directories()
        self.types_dir = directories['types']
        self.eyemaps_dir = directories['eyemaps']

        # Initialize hexagon grid generator with eyemaps directory
        self.hexagon_generator = HexagonGridGenerator(output_dir=self.output_dir, eyemaps_dir=self.eyemaps_dir)

        # Initialize utility classes (must be done before Jinja setup)
        self.color_utils = ColorUtils(self.hexagon_generator)
        self.html_utils = HTMLUtils()
        self.text_utils = TextUtils()
        self.number_formatter = NumberFormatter()
        self.percentage_formatter = PercentageFormatter()
        self.synapse_formatter = SynapseFormatter()
        self.neurotransmitter_formatter = NeurotransmitterFormatter()

        # Initialize service dependencies
        self.layer_analysis_service = LayerAnalysisService(config)
        self.column_analysis_service = ColumnAnalysisService(self, config)

        # Initialize Jinja2 environment (after utility classes are available)
        self._setup_jinja_env()

        # Initialize URL generation service (after Jinja environment is set up)
        self.url_generation_service = URLGenerationService(config, self.env, self)

        # Copy static files to output directory using resource manager
        self.resource_manager.copy_static_files()

        # Initialize caches for expensive operations
        self._all_columns_cache = None
        self._column_analysis_cache = {}



    def _load_brain_regions(self):
        """Load brain regions data from CSV for the abbr filter."""
        try:
            # Get the project root directory
            project_root = Path(__file__).parent.parent.parent
            brain_regions_file = project_root / 'input' / 'brainregions.csv'

            if brain_regions_file.exists():
                # Load CSV manually to handle commas in brain region names
                # Split only on the first comma to separate abbreviation from full name
                brain_regions_dict = {}
                with open(brain_regions_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and ',' in line:
                            # Split on first comma only
                            parts = line.split(',', 1)
                            if len(parts) == 2:
                                abbr = parts[0].strip()
                                full_name = parts[1].strip()
                                brain_regions_dict[abbr] = full_name
                self.brain_regions = brain_regions_dict
            else:
                logger.warning(f"Brain regions file not found: {brain_regions_file}")
                self.brain_regions = {}
        except Exception as e:
            logger.error(f"Error loading brain regions data: {e}")
            self.brain_regions = {}

    def _load_citations(self):
        """Load citations data from CSV for synonyms links."""
        try:
            # Get the project root directory
            project_root = Path(__file__).parent.parent.parent
            citations_file = project_root / 'input' / 'citations.csv'

            if citations_file.exists():
                # Load CSV manually to handle potential commas in citations
                citations_dict = {}
                with open(citations_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and ',' in line:
                            # Split on commas, but handle quoted titles
                            import csv
                            import io
                            reader = csv.reader(io.StringIO(line))
                            row = next(reader)

                            if len(row) >= 2:
                                citation = row[0].strip()
                                url = row[1].strip()
                                title = row[2].strip().strip('"') if len(row) >= 3 else ""

                                # Convert DOI to full URL if it starts with "10."
                                if url.startswith("10."):
                                    url = f"https://doi.org/{url}"

                                # Store as tuple: (url, title)
                                citations_dict[citation] = (url, title)
                self.citations = citations_dict
                logger.info(f"Loaded {len(self.citations)} citations from {citations_file}")
            else:
                logger.warning(f"Citations file not found: {citations_file}")
                self.citations = {}
        except Exception as e:
            logger.error(f"Error loading citations data: {e}")
            self.citations = {}

    def _roi_abbr_filter(self, roi_name):
        """
        Convert ROI abbreviation to HTML abbr tag with full name in title.

        Args:
            roi_name: The ROI abbreviation

        Returns:
            HTML abbr tag if full name found, otherwise the original abbreviation
        """
        if not roi_name or not isinstance(roi_name, str):
            return roi_name

        # Strip whitespace
        roi_abbr = re.sub(r'\([RL]\)', '', roi_name)
        roi_abbr = roi_abbr.strip()

        # Look up the full name
        full_name = self.brain_regions.get(roi_abbr)

        if full_name:
            return f'<abbr title="{full_name}">{roi_name}</abbr>'
        else:
            # Return the original abbreviation if not found
            logger.warning(f"abbr {roi_name} not found")
            return roi_name

    def _get_partner_body_ids(self, partner_data, direction, connected_bids):
        """
        Return a de-duplicated, order-preserving list of partner bodyIds for a given
        direction, optionally restricted to a soma side.

        Behavior
        --------
        - If `partner_data` specifies a `soma_side` ('L' or 'R'), only bodyIds that
        match BOTH the partner `type` and that side are returned. The function looks
        first for keys like ``"{type}_L"`` or ``"{type}_R"`` under
        ``connected_bids[direction]``. If only a bare ``"{type}"`` key exists:
            * if its value is a dict (e.g., ``{'L': [...], 'R': [...]}``), the
            side-specific list is used;
            * if its value is a list (no side information), that list is returned
            as-is.
        If neither a side-specific nor a filterable bare entry is present, an
        empty list is returned.
        - If `soma_side` is missing/None, the result is the union of
        ``"{type}_L"``, ``"{type}_R"``, and the bare ``"{type}"`` entries (when present).

        Parameters
        ----------
        partner_data : dict or str
            Partner descriptor. When a dict, should contain:
            - ``'type'`` (str): partner cell type (e.g., "Dm4")
            - ``'soma_side'`` (optional, str): 'L' or 'R'
            When a str, it is treated as the partner type; side is assumed None.
        direction : {'upstream', 'downstream'}
            Which connectivity direction to use when looking up IDs.
        connected_bids : dict
            Mapping with shape like:
            {
            'upstream':   { 'Dm4_L': [...], 'Dm4_R': [...], 'Dm4': [...](optional) },
            'downstream': { 'Dm4_L': [...], 'Dm4_R': [...], 'Dm4': [...](optional) }
            }
            Values may be lists (IDs), or for the bare type, optionally a dict
            keyed by side (e.g., ``{'L': [...], 'R': [...]}``).

        Returns
        -------
        list
            A list of bodyIds (as provided by `connected_bids`), de-duplicated while
            preserving first-seen order. Returns an empty list if `direction` is
            absent or no matching entries are found.

        Notes
        -----
        - Item types are not coerced; IDs are returned as stored (e.g., int/str).
        Callers may cast as needed.
        - When a side is explicitly requested but unavailable, the function prefers
        to return an empty list rather than mixing sides.
        - If `partner_data` lacks `soma_side`, all sides (and any bare entry) are
        merged for backward compatibility.

        """
        if not connected_bids or direction not in connected_bids:
            return []

        # Extract partner name and soma side from partner data
        if isinstance(partner_data, dict):
            partner_name = partner_data.get('type', 'Unknown')
            soma_side = partner_data.get('soma_side')
        else:
            # Fallback for string input
            partner_name = str(partner_data)
            soma_side = None


        dmap = connected_bids[direction] or {}

        def unique(seq):
            seen, out = set(), []
            for x in seq:
                sx = str(x)
                if sx not in seen:
                    seen.add(sx)
                    out.append(x)
            return out
        # If we know the side, prefer keys like "Dm4_L" / "Dm4_R"
        if soma_side in ('L', 'R'):
            keyed = dmap.get(f"{partner_name}_{soma_side}", [])
            if keyed:
                return unique(keyed)
            # Some datasets store a dict/array under bare type; try to filter if shaped
            bare = dmap.get(partner_name)
            if isinstance(bare, dict):
                # If keys contain side-specific lists (e.g., {'L': [...], 'R': [...]})
                candidate = bare.get(soma_side) or bare.get(f"{partner_name}_{soma_side}") or []
                return unique(candidate if isinstance(candidate, list) else [candidate])
            if isinstance(bare, list):
                # No side info here; fall back to the bare list
                return unique(bare)
            # Nothing side-specific; return empty rather than all-sides
            return []
        elif soma_side is None:
            # No side: return all sides (legacy behavior)
            vals = []
            for k in (f"{partner_name}_L", f"{partner_name}_R", partner_name):
                v = dmap.get(k, [])
                if isinstance(v, list):
                    vals.extend(v)
                elif v:
                    vals.append(v)
            return unique(vals)

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
        self.env.filters['format_number'] = self.number_formatter.format_number
        self.env.filters['format_percentage'] = self.percentage_formatter.format_percentage
        self.env.filters['format_percentage_5'] = self.percentage_formatter.format_percentage_5
        self.env.filters['format_synapse_count'] = self.synapse_formatter.format_synapse_count
        self.env.filters['format_conn_count'] = self.synapse_formatter.format_conn_count
        self.env.filters['abbreviate_neurotransmitter'] = self.neurotransmitter_formatter.abbreviate_neurotransmitter
        self.env.filters['is_png_data'] = self.html_utils.is_png_data
        self.env.filters['neuron_link'] = lambda neuron_type, soma_side: self.html_utils.create_neuron_link(neuron_type, soma_side, self.queue_service)
        self.env.filters['truncate_neuron_name'] = self.text_utils.truncate_neuron_name
        self.env.filters['roi_abbr'] = self._roi_abbr_filter
        self.env.filters['get_partner_body_ids'] = self._get_partner_body_ids
        self.env.filters['synapses_to_colors'] = self.color_utils.synapses_to_colors
        self.env.filters['neurons_to_colors'] = self.color_utils.neurons_to_colors


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
                neuron_types_data_json=json.dumps([], indent=2),
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






    def _generate_neuroglancer_url(self, neuron_type: str, neuron_data: Dict[str, Any], soma_side: Optional[str] = None, connector=None) -> tuple[str, Dict[str, Any]]:
        """
        Generate Neuroglancer URL from template with substituted variables.

        Args:
            neuron_type: The neuron type name
            neuron_data: Data containing neuron information including bodyIDs
            soma_side: Soma side filter ('left', 'right', 'combined', etc.)
            connector: NeuPrint connector instance

        Returns:
            Tuple of (URL-encoded Neuroglancer URL, template variables dict)
        """
        # Delegate to the URL generation service
        return self.url_generation_service.generate_neuroglancer_url(
            neuron_type, neuron_data, soma_side, connector
        )

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

        For 'combined' soma side, selects one neuron from each side (left and right).
        For specific sides, selects one neuron from that side.
        Optimization: If only one neuron exists for a side, selects it directly without synapse queries.

        Args:
            neurons_df: DataFrame containing neuron data with bodyId, pre, post, and somaSide columns
            soma_side: Target soma side ('left', 'right', 'combined', 'all', etc.)
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

        if soma_side == 'combined':
            # Select one neuron from each available side
            available_sides = neurons_df['somaSide'].unique()

            # Map side codes to readable names for logging
            side_names = {'L': 'left', 'R': 'right', 'M': 'middle'}

            for side_code in ['L', 'R']:  # Focus on left and right for 'combined'
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

    def _get_connected_bids(self, visible_neurons: List[int], connector) -> Dict:
        """
        Get bodyIds of the top cell from each type that are connected with the
        current 'visible_neuron' in the Neuroglancer view. If there are multiple
          visible_neurons, then the bodyIds are aggregated by type and soma side.
        Args:
            visible_neurons: List of the visible neuron's bodyId.
            connector: NeuPrint connector instance.

        Returns:
            Dictionary of the connected bodyIds, with keys 'downstream' and 'upstream'.
            Each direction contains keys like 'L1_R' and 'L1_L' for soma side-specific lookups.
        """
        results = {"downstream": {}, "upstream": {}}

        for conn_dir in ["downstream", "upstream"]:
            if conn_dir == "downstream":
                dir_str = "(n:Neuron)-[c:ConnectsTo]->(m:Neuron)"
            else:
                dir_str = "(n:Neuron)<-[c:ConnectsTo]-(m:Neuron)"

            for bid in visible_neurons:
                cql = f"""
                MATCH {dir_str}
                WHERE n.bodyId = {bid} AND exists(m.type) AND m.type IS NOT NULL
                WITH m.type AS type,
                     COALESCE(
                         m.somaSide,
                         apoc.coll.flatten(apoc.text.regexGroups(m.instance, '_([LR])$'))[1],
                         ''
                     ) as soma_side,
                     m.bodyId AS bodyId,
                     c.weight AS weight
                ORDER BY type, soma_side, weight DESC
                WITH type, soma_side, collect({{bodyId: bodyId, weight: weight}})[0] AS top
                RETURN type, soma_side, top.bodyId AS bodyId, top.weight AS weight
                ORDER BY type, soma_side
                """
                df = connector.client.fetch_custom(cql)

                # Merge bodyIds per type+soma_side across bids (dedupe, preserve order)
                for t, s, b in zip(df["type"], df["soma_side"], df["bodyId"]):
                    # Create key that includes soma side information
                    key = f"{t}_{s}" if s else t
                    bucket = results[conn_dir].setdefault(key, [])
                    if b not in bucket:
                        bucket.append(b)

                    # Also add to fallback key without soma side for backward compatibility
                    fallback_bucket = results[conn_dir].setdefault(t, [])
                    if b not in fallback_bucket:
                        fallback_bucket.append(b)

        return results

    def _generate_neuprint_url(self, neuron_type: str, neuron_data: Dict[str, Any]) -> str:
        """
        Generate NeuPrint URL from template with substituted variables.

        Args:
            neuron_type: The neuron type name
            neuron_data: Data containing neuron information

        Returns:
            NeuPrint URL for searching this neuron type
        """
        # Delegate to the URL generation service
        return self.url_generation_service.generate_neuprint_url(neuron_type, neuron_data)

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

            # Get neuron data to check for unknown soma sides
            neuron_data = connector.get_neuron_data(neuron_type, 'combined')
            neurons_df = neuron_data.get('neurons', pd.DataFrame())

            # Calculate unknown soma side count
            total_count = len(neurons_df) if not neurons_df.empty else 0
            assigned_count = 0
            if not neurons_df.empty and 'somaSide' in neurons_df.columns:
                assigned_count = len(neurons_df[neurons_df['somaSide'].isin(['L', 'R', 'M'])])
            unknown_count = total_count - assigned_count

            # Map soma side codes to readable names and generate filenames
            side_mapping = {
                'L': ('left', '_L'),
                'R': ('right', '_R'),
                'M': ('middle', '_M')
            }

            soma_side_links = {}

            # Create navigation if:
            # 1. Multiple assigned sides exist, OR
            # 2. Unknown sides exist alongside any assigned side
            should_create_navigation = (
                len(available_sides) > 1 or
                (unknown_count > 0 and len(available_sides) > 0)
            )

            if should_create_navigation:
                # Add individual sides
                for side_code in available_sides:
                    if side_code in side_mapping:
                        side_name, file_suffix = side_mapping[side_code]
                        # Generate filename for this soma side
                        clean_type = neuron_type.replace('/', '_').replace(' ', '_')
                        filename = f"{clean_type}{file_suffix}.html"
                        soma_side_links[side_name] = filename

                # Add "combined" link (no suffix for URL compatibility)
                clean_type = neuron_type.replace('/', '_').replace(' ', '_')
                combined_filename = f"{clean_type}.html"
                soma_side_links['combined'] = combined_filename

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
        neuroglancer_url, neuroglancer_vars = self._generate_neuroglancer_url(neuron_type, neuron_data, soma_side)

        # Generate NeuPrint URL
        neuprint_url = self._generate_neuprint_url(neuron_type, neuron_data)

        # Get available soma sides for navigation
        soma_side_links = self._get_available_soma_sides(neuron_type, connector)

        # Find YouTube video for this neuron type (only for right soma side)
        youtube_url = None
        if soma_side == 'right':
            youtube_video_id = self._find_youtube_video(neuron_type)
            if youtube_video_id:
                youtube_url = f"https://www.youtube.com/watch?v={youtube_video_id}"

        # Process synonyms if available
        processed_synonyms = {}
        processed_flywire_types = {}
        if not neuron_data['neurons'].empty:
            synonyms_raw = None
            # Check for synonyms column (may be renamed during merge)
            if 'synonyms_y' in neuron_data['neurons'].columns:
                synonyms_raw = neuron_data['neurons']['synonyms_y'].iloc[0]
            elif 'synonyms' in neuron_data['neurons'].columns:
                synonyms_raw = neuron_data['neurons']['synonyms'].iloc[0]

            if pd.notna(synonyms_raw):
                processed_synonyms = self.text_utils.process_synonyms(str(synonyms_raw), self.citations)

            # Process flywireType if available - collect all unique values
            flywire_type_raw = None
            if 'flywireType_y' in neuron_data['neurons'].columns:
                # Get all unique flywireType values, excluding NaN
                unique_types = neuron_data['neurons']['flywireType_y'].dropna().unique()
                if len(unique_types) > 0:
                    flywire_type_raw = ', '.join(sorted(set(str(t) for t in unique_types)))
            elif 'flywireType' in neuron_data['neurons'].columns:
                # Get all unique flywireType values, excluding NaN
                unique_types = neuron_data['neurons']['flywireType'].dropna().unique()
                if len(unique_types) > 0:
                    flywire_type_raw = ', '.join(sorted(set(str(t) for t in unique_types)))

            if flywire_type_raw:
                processed_flywire_types = self.text_utils.process_flywire_types(flywire_type_raw, neuron_type)

        # Prepare template context
        normalized_soma_side = soma_side

        context = {
            'config': self.config,
            'neuron_data': neuron_data,
            'neuron_type': neuron_type,
            'soma_side': normalized_soma_side,
            'summary': neuron_data['summary'],
            'complete_summary': neuron_data.get('complete_summary', neuron_data['summary']),
            'neurons_df': neuron_data['neurons'],
            'connectivity': neuron_data.get('connectivity', {}),
            'column_analysis': column_analysis,
            'neuroglancer_url': neuroglancer_url,
            'neuprint_url': neuprint_url,
            'soma_side_links': soma_side_links,
            'generation_time': datetime.now(),
            'visible_neurons': neuroglancer_vars['visible_neurons'],
            'visible_rois': neuroglancer_vars['visible_rois'],
            'website_title': neuroglancer_vars['website_title'],
            'neuron_query': neuroglancer_vars['neuron_query'],
            'connected_bids': neuroglancer_vars['connected_bids'],
            'youtube_url': youtube_url,
            'processed_synonyms': processed_synonyms,
            'processed_flywire_types': processed_flywire_types,
            'is_neuron_page': True
        }

        # Render template
        html_content = template.render(**context)

        # Minify HTML content to reduce whitespace (with JS minification for neuron pages)
        if not uncompress:
            html_content = self.html_utils.minify_html(html_content, minify_js=True)

        # Generate output filename
        output_filename = self._generate_filename(neuron_type, soma_side)
        output_path = self.types_dir / output_filename

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
        neuroglancer_url, neuroglancer_vars = self._generate_neuroglancer_url(neuron_type_obj.name, neuron_data, neuron_type_obj.soma_side, connector)

        # Generate NeuPrint URL
        neuprint_url = self._generate_neuprint_url(neuron_type_obj.name, neuron_data)

        # Get available soma sides for navigation
        soma_side_links = self._get_available_soma_sides(neuron_type_obj.name, connector)

        # Find YouTube video for this neuron type (only for right soma side)
        youtube_url = None
        if neuron_type_obj.soma_side == 'right':
            youtube_video_id = self._find_youtube_video(neuron_type_obj.name)
            if youtube_video_id:
                youtube_url = f"https://www.youtube.com/watch?v={youtube_video_id}"

        # Process synonyms if available
        processed_synonyms = {}
        processed_flywire_types = {}
        if not neuron_data['neurons'].empty:
            synonyms_raw = None
            # Check for synonyms column (may be renamed during merge)
            if 'synonyms_y' in neuron_data['neurons'].columns:
                synonyms_raw = neuron_data['neurons']['synonyms_y'].iloc[0]
            elif 'synonyms' in neuron_data['neurons'].columns:
                synonyms_raw = neuron_data['neurons']['synonyms'].iloc[0]

            if pd.notna(synonyms_raw):
                processed_synonyms = self.text_utils.process_synonyms(str(synonyms_raw), self.citations)

            # Process flywireType if available - collect all unique values
            flywire_type_raw = None
            if 'flywireType_y' in neuron_data['neurons'].columns:
                # Get all unique flywireType values, excluding NaN
                unique_types = neuron_data['neurons']['flywireType_y'].dropna().unique()
                if len(unique_types) > 0:
                    flywire_type_raw = ', '.join(sorted(set(str(t) for t in unique_types)))
            elif 'flywireType' in neuron_data['neurons'].columns:
                # Get all unique flywireType values, excluding NaN
                unique_types = neuron_data['neurons']['flywireType'].dropna().unique()
                if len(unique_types) > 0:
                    flywire_type_raw = ', '.join(sorted(set(str(t) for t in unique_types)))

            if flywire_type_raw:
                processed_flywire_types = self.text_utils.process_flywire_types(flywire_type_raw, neuron_type_obj.name)

        # Find the type's assigned "region" - used for setting the NG view.
        type_region = self._get_region_for_type(neuron_type_obj.name, connector)
        # Prepare template context
        normalized_soma_side = neuron_type_obj.soma_side

        context = {
            'config': self.config,
            'neuron_data': neuron_data,
            'neuron_type': neuron_type_obj.name,
            'soma_side': normalized_soma_side,
            'summary': neuron_data['summary'],
            'complete_summary': neuron_data.get('complete_summary', neuron_data['summary']),
            'neurons_df': neuron_data['neurons'],
            'connectivity': neuron_data.get('connectivity', {}),
            'roi_summary': roi_summary,
            'layer_analysis': layer_analysis,
            'column_analysis': column_analysis,
            'neuroglancer_url': neuroglancer_url,
            'neuprint_url': neuprint_url,
            'soma_side_links': soma_side_links,
            'visible_neurons': neuroglancer_vars['visible_neurons'],
            'visible_rois': neuroglancer_vars['visible_rois'],
            'website_title': neuroglancer_vars['website_title'],
            'neuron_query': neuroglancer_vars['neuron_query'],
            'connected_bids': neuroglancer_vars['connected_bids'],
            'youtube_url': youtube_url,
            'generation_time': datetime.now(),
            'processed_synonyms': processed_synonyms,
            'processed_flywire_types': processed_flywire_types,
            'is_neuron_page': True,
            'type_region': type_region
        }

        # Render template
        html_content = template.render(**context)

        # Minify HTML content to reduce whitespace (with JS minification for neuron pages)
        if not uncompress:
            html_content = self.html_utils.minify_html(html_content, minify_js=True)

        # Generate output filename
        output_filename = self._generate_filename(neuron_type_obj.name, neuron_type_obj.soma_side)
        output_path = self.types_dir / output_filename

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
            neuron_type: Name of the neuron type
            connector: Database connector for additional queries
        """
        # Delegate to the layer analysis service
        return self.layer_analysis_service.analyze_layer_roi_data(
            roi_counts_df, neurons_df, soma_side, neuron_type, connector
        )

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
            # Get all ROI names from cached hierarchy
            roi_hierarchy = connector._get_roi_hierarchy()
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
            - type_columns: List of dicts with hex1, hex2 (integers) for this type
            - region_columns_map: Dict mapping region_side names to sets of (hex1, hex2) tuples
        """
        import re
        import time
        start_time = time.time()

        # Check in-memory cache first
        cache_key = f"columns_{neuron_type}"
        if hasattr(self, '_neuron_type_columns_cache') and cache_key in self._neuron_type_columns_cache:
            logger.info(f"_get_columns_for_neuron_type({neuron_type}): returning in-memory cached result")
            return self._neuron_type_columns_cache[cache_key]

        # Check persistent neuron cache second
        cached_columns, cached_region_map = self._get_columns_from_neuron_cache(neuron_type)
        if cached_columns is not None and cached_region_map is not None:
            result_tuple = (cached_columns, cached_region_map)
            # Store in memory cache for future calls
            if not hasattr(self, '_neuron_type_columns_cache'):
                self._neuron_type_columns_cache = {}
            self._neuron_type_columns_cache[cache_key] = result_tuple
            logger.info(f"_get_columns_for_neuron_type({neuron_type}): returning persistent cached result")
            return result_tuple

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
                type_columns.append({
                    'hex1': hex1_dec,
                    'hex2': hex2_dec
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

    def _get_columns_from_neuron_cache(self, neuron_type: str):
        """
        Extract column data from neuron type cache if available.

        Args:
            neuron_type: The neuron type to get cached column data for

        Returns:
            Tuple of (columns_data, region_columns_map) or (None, None) if not cached
        """
        try:
            if hasattr(self, '_neuron_cache_manager') and self._neuron_cache_manager is not None:
                cache_data = self._neuron_cache_manager.load_neuron_type_cache(neuron_type)
                if cache_data and cache_data.columns_data and cache_data.region_columns_map:
                    # Convert region_columns_map back to sets from lists
                    region_map = {}
                    for region, coords_list in cache_data.region_columns_map.items():
                        region_map[region] = set(tuple(coord) for coord in coords_list)

                    logger.debug(f"Retrieved column data from cache for {neuron_type}: {len(cache_data.columns_data)} columns")
                    return cache_data.columns_data, region_map
        except Exception as e:
            logger.debug(f"Failed to get column data from cache for {neuron_type}: {e}")

        return None, None

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
            - all_possible_columns: List of dicts with hex1, hex2 (integers)
            - region_columns_map: Dict mapping region_side names to sets of (hex1, hex2) tuples
        """
        # Return cached result if available
        if self._all_columns_cache is not None:
            logger.info("_get_all_possible_columns_from_dataset: returning cached result")
            return self._all_columns_cache

        # Generate cache key based on server and dataset
        cache_key = f"all_columns_{connector.config.neuprint.server}_{connector.config.neuprint.dataset}"

        # Try to load from any existing neuron cache first
        if hasattr(self, '_neuron_cache_manager') and self._neuron_cache_manager is not None:
            try:
                cached_neuron_types = self._neuron_cache_manager.list_cached_neuron_types()
                for neuron_type in cached_neuron_types:
                    cached_columns, cached_region_map = self._get_columns_from_neuron_cache(neuron_type)
                    if cached_columns is not None and cached_region_map is not None:
                        result_tuple = (cached_columns, cached_region_map)
                        self._all_columns_cache = result_tuple
                        logger.info(f"_get_all_possible_columns_from_dataset: loaded from {neuron_type} neuron cache ({len(cached_columns)} columns)")
                        return result_tuple
            except Exception as e:
                logger.debug(f"Failed to load column data from neuron cache: {e}")

        # Check persistent standalone cache as fallback
        persistent_result = self._load_persistent_columns_cache(cache_key)
        if persistent_result is not None:
            self._all_columns_cache = persistent_result
            return persistent_result

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
            column_data = {}  # Maps (hex1, hex2) to set of region_side combinations that have this column

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
                    region_side = f"{region}_{side}"
                    if coord_key not in column_data:
                        column_data[coord_key] = set()
                    column_data[coord_key].add(region_side)

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
            # Build final results
            all_possible_columns = []
            for coord_key in sorted(column_data.keys()):
                hex1_dec, hex2_dec = coord_key
                all_possible_columns.append({
                    'hex1': hex1_dec,
                    'hex2': hex2_dec
                })

            # Cache the result for future use (in-memory only, no longer saving standalone cache)
            result = (all_possible_columns, region_columns_map)
            self._all_columns_cache = result
            # self._save_persistent_columns_cache(cache_key, result)  # Disabled: using neuron cache instead
            logger.info(f"_get_all_possible_columns_from_dataset: cached {len(all_possible_columns)} columns")
            return result

        except Exception as e:
            logger.warning(f"Could not query dataset for all columns: {e}")
            return [], {}

    def _load_persistent_columns_cache(self, cache_key):
        """Load persistent cache for all columns dataset query."""
        try:
            import json
            import hashlib
            from pathlib import Path

            # Create cache directory
            cache_dir = Path("output/.cache")
            cache_dir.mkdir(parents=True, exist_ok=True)

            # Use hash of cache key for filename to avoid filesystem issues
            cache_filename = hashlib.md5(cache_key.encode()).hexdigest() + "_columns.json"
            cache_file = cache_dir / cache_filename

            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    data = json.load(f)

                # Check cache age (expire after 24 hours)
                import time
                cache_age = time.time() - data.get('timestamp', 0)
                if cache_age < 86400:  # 24 hours
                    # Reconstruct the tuple from JSON
                    all_columns = data['all_columns']
                    region_map = {}
                    for region, coords_list in data['region_map'].items():
                        region_map[region] = set(tuple(coord) for coord in coords_list)

                    logger.info(f"Loaded {len(all_columns)} columns from persistent cache (age: {cache_age/3600:.1f}h)")
                    return (all_columns, region_map)
                else:
                    logger.info("Persistent columns cache expired, will refresh")
                    cache_file.unlink()

        except Exception as e:
            logger.warning(f"Failed to load persistent columns cache: {e}")

        return None

    # def _save_persistent_columns_cache(self, cache_key, result):
    #     """Save persistent cache for all columns dataset query."""
    #     # DISABLED: No longer saving standalone columns cache - using neuron cache instead
    #     pass

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
        # Delegate to the column analysis service
        return self.column_analysis_service.analyze_column_roi_data(
            roi_counts_df, neurons_df, soma_side, neuron_type, connector,
            file_type, save_to_files
        )

    def _get_col_layer_values(self, neuron_type: str, connector):
        """
        Query the dataset to get the synapse density and neuron count per column
        across the layer ROIs for a specific neuron type.

        Args:
            neuron_type: Type of neuron being analyzed
            connector: NeuPrint connector instance for database queries
        """

        cache_dir = Path("output/.cache/col_layers")
        cache_dir.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r'[^A-Za-z0-9._-]+', '_', neuron_type).strip('_')
        cache_path = cache_dir / f"{safe_name}.json"

        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    cached = json.load(f)
                if isinstance(cached, dict) and "results" in cached and "thresholds" in cached:
                    results_df = pd.DataFrame(cached["results"])
                    # Handle both old cache format (without min_max_data) and new format
                    min_max_data = cached.get("min_max_data", {})
                    return results_df, cached["thresholds"], min_max_data
            except Exception:
                # Corrupt/old cache -> fall through to recompute
                pass

        layer_pattern = r'^(ME|LO|LOP)_([LR])_layer_(\d+)$'

        query = fr"""
        MATCH (n:Neuron)-[:Contains]->(nss:SynapseSet)-[:Contains]->(ns:Synapse)
        WHERE n.type = '{neuron_type}'
        WITH ns,  CASE
               WHEN exists(ns['ME(R)']) THEN ['ME', 'R']
               WHEN exists(ns['ME(L)']) THEN ['ME', 'L']
               WHEN exists(ns['LO(R)']) THEN ['LO', 'R']
               WHEN exists(ns['LO(L)']) THEN ['LO', 'L']
               WHEN exists(ns['LOP(R)']) THEN ['LOP', 'R']
               WHEN exists(ns['LOP(L)']) THEN ['LOP', 'L']
             END AS layerKey,
             count(ns) AS n_synapses
        RETURN
            ns.olHex1 AS hex1,
            ns.olHex2 AS hex2,
            ns.olLayer AS layer,
            layerKey[0] as region,
            layerKey[1] as side,
            sum(n_synapses) as total_synapses,
            ns.bodyId as bodyId,
            count(DISTINCT ns.bodyId) as neuron_count
        ORDER BY hex1, hex2, layer
        """
        df = connector.client.fetch_custom(query)
        df = df.dropna(subset=['layer'])
        df['layer'] = df['layer'].astype(int)
        df['hex1'] = df['hex1'].astype(int)
        df['hex2'] = df['hex2'].astype(int)

        # # Get "threshold" values for colorscales in eyemaps plots # #
        thresholds = self._compute_thresholds(df, n_bins=5)

        df_unique = (
            df.groupby(['hex1', 'hex2', 'layer', 'side', 'region'], as_index=False)
            .agg(
                total_synapses=('total_synapses', 'sum'),
                neuron_count=('bodyId', pd.Series.nunique)
            )
        )

        # # Get lists of values and fill colours per layer # #
        # Get all possible layers per region/side
        all_layers = self._get_all_dataset_layers(layer_pattern, connector)
        layer_map = {}
        for region, side, layer in all_layers:
            layer_map.setdefault((region, side), []).append(layer)

        results = []

        max_syn_region = df_unique.groupby(['region'])['total_synapses'].max()
        max_cells_region = df_unique.groupby(['region'])['neuron_count'].max()
        min_syn_region = df_unique.groupby(['region'])['total_synapses'].min()
        min_cells_region = df_unique.groupby(['region'])['neuron_count'].min()

        # For each column-layer grouping per side
        for (hex1, hex2, region, side), group in df_unique.groupby(['hex1', 'hex2', 'region','side']):
            layers_for_group = sorted(layer_map[(region, side)])
            max_layer = max(layers_for_group)

            # Initialize lists with zeros (counts)
            synapse_list = [0] * max_layer
            neuron_list = [0] * max_layer

            # Fill values where data exists
            for _, row in group.iterrows():
                idx = int(row['layer']) - 1
                synapse_list[idx] = int(row['total_synapses'])
                neuron_list[idx] = int(row['neuron_count'])

            results.append({
                'hex1': int(hex1),
                'hex2': int(hex2),
                'region': region,
                'side': side,
                'synapses_list': synapse_list,
                'neurons_list': neuron_list
            })

        results = pd.DataFrame(results)

        # Add min/max data for color normalization
        min_max_data = {
            'min_syn_region': min_syn_region.to_dict(),
            'max_syn_region': max_syn_region.to_dict(),
            'min_cells_region': min_cells_region.to_dict(),
            'max_cells_region': max_cells_region.to_dict()
        }

        # Save to cache
        try:
            # Convert DataFrame to JSON-serializable format
            results_dict = results.to_dict('records')

            # Add min/max data to the cache
            cache_data = {
                'results': results_dict,
                'min_max_data': min_max_data
            }

            # Ensure all values are JSON-serializable (convert numpy types to Python types)
            for record in results_dict:
                for key, value in record.items():
                    if key in ['hex1', 'hex2']:
                        # Ensure hex1 and hex2 are always integers
                        record[key] = int(value)
                    elif isinstance(value, (np.integer, np.floating)):
                        record[key] = value.item()
                    elif isinstance(value, np.ndarray):
                        record[key] = value.tolist()
                    elif isinstance(value, list):
                        # Convert any numpy types within lists
                        record[key] = [v.item() if isinstance(v, (np.integer, np.floating)) else v for v in value]

            # Ensure thresholds are also JSON-serializable
            json_thresholds = {}
            for key, value in thresholds.items():
                if isinstance(value, (np.integer, np.floating)):
                    json_thresholds[key] = value.item()
                elif isinstance(value, np.ndarray):
                    json_thresholds[key] = value.tolist()
                elif isinstance(value, list):
                    json_thresholds[key] = [v.item() if isinstance(v, (np.integer, np.floating)) else v for v in value]
                else:
                    json_thresholds[key] = value

            cache_data = {
                "results": results_dict,
                "thresholds": json_thresholds,
                "min_max_data": min_max_data
            }
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception:
            # If saving fails, still return results
            pass

        return results, thresholds, min_max_data

    def _compute_thresholds(self, df: pd.DataFrame, n_bins: int = 5):
        """
        Compute threshold lists for synapse and neuron counts at different aggregation levels.

        Parameters
        ----------
        df : pandas.DataFrame
            Input DataFrame with at least the following columns:
            - `"hex1"`, `"hex2"`: Column identifiers
            - `"layer"`: Layer index
            - `"region"`: Region name (e.g., `"ME"`, `"LO"`, `"LOP"`)
            - `"side"`: Side indicator (e.g., `"L"` or `"R"`)
            - `"total_synapses"`: Number of synapses
            - `"neuron_count"`: Number of unique neurons
        n_bins : int, optional
            Number of bins to divide the value ranges into. The returned threshold
            lists will each have `n_bins + 1` elements. Default is 5.

        Returns
        -------
        thresholds : dict
            A nested dictionary with the first level keyed by the metric
            ("total_synapses", "neuron_count"), then by scope ("all" or "layers"),
            and within "layers" by region ("ME", "LO", "LOP").

        Notes
        -----
        - Thresholds are computed using `self.hexagon_generator._layer_thresholds`,
        which ensures that:
            * Empty lists produce `[0.0, 0.0, ..., 0.0]`
            * Constant-value lists produce a flat threshold list
            * Otherwise thresholds are evenly spaced between min and max.
        """
        thresholds = {
        "total_synapses": {"all": None, "layers": {}},
        "neuron_count": {"all": None, "layers": {}},
        }

        # Across all layers - find the max per column across all regions.
        thresholds["total_synapses"]["all"] = self._layer_thresholds(
            df.groupby(['hex1', 'hex2','side','region'])\
                ['total_synapses'].sum(), n_bins=n_bins
        )
        # print(df.groupby(['hex1', 'hex2','side', 'region'])\
        #         ['total_synapses'].sum())
        thresholds["neuron_count"]["all"] = self._layer_thresholds(
            df.groupby(['hex1', 'hex2','side', 'region'])\
                ['bodyId'].nunique(), n_bins=n_bins
            )

        for reg in ["ME", "LO", "LOP"]:

            sub = df[df['region']==reg]

            # Across layers - find the max per column/layer within regions
            thresholds["total_synapses"]["layers"][reg] = self._layer_thresholds(
                sub.groupby(['hex1', 'hex2','side', 'layer'])\
                ["total_synapses"].sum(), n_bins=n_bins
            )
            thresholds["neuron_count"]["layers"][reg] = self._layer_thresholds(
                sub.groupby(['hex1', 'hex2','side', 'layer'])\
                ["bodyId"].nunique(), n_bins=n_bins
            )

        return thresholds

    def _layer_thresholds(self, values, n_bins=5):
        """
        Return n_bins+1 thresholds from min..max for a 1D list of numbers.
        If values is empty -> [0,0,...,0].
        If all values are equal -> list of that value repeated.
        """
        if values.empty:
            return [0.0] * (n_bins + 1)
        vmin = min(values)
        vmax = max(values)
        if vmax == vmin:
            return [float(vmin)] * (n_bins + 1)
        return [vmin + (vmax - vmin) * (i / n_bins) for i in range(n_bins + 1)]

    def _generate_region_hexagonal_grids(self, column_summary: List[Dict], neuron_type: str, soma_side, file_type: str = 'svg', save_to_files: bool = True, connector=None, min_max_data: Optional[Dict] = None) -> Dict[str, Dict[str, str]]:
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

        # Compute thresholds from column_summary
        df = pd.DataFrame(column_summary)
        thresholds_all = self._compute_thresholds(df, n_bins=5) if not df.empty else {}

        # Get all possible columns from the dataset if connector is available
        all_possible_columns = []
        region_columns_map = {}
        if connector:
            all_possible_columns, region_columns_map = self._get_all_possible_columns_from_dataset(connector)

        return self.hexagon_generator.generate_comprehensive_region_hexagonal_grids(
            column_summary, thresholds_all, all_possible_columns, region_columns_map, neuron_type, soma_side, output_format=file_type, save_to_files=save_to_files, min_max_data=min_max_data or {}
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

    @staticmethod
    def generate_filename(neuron_type: str, soma_side: str) -> str:
        """
        Generate HTML filename for a neuron type and soma side.

        This is a static utility method that doesn't require PageGenerator instantiation.

        Args:
            neuron_type: The neuron type name
            soma_side: The soma side ('left', 'right', 'middle', 'all', 'combined')

        Returns:
            HTML filename string
        """
        # Clean neuron type name for filename
        clean_type = neuron_type.replace('/', '_').replace(' ', '_')

        # Handle different soma side formats with new naming scheme
        if soma_side in ['all', 'combined']:
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

    def _generate_filename(self, neuron_type: str, soma_side: str) -> str:
        """Instance method wrapper for backwards compatibility."""
        return self.generate_filename(neuron_type, soma_side)

    def _load_youtube_videos(self) -> Dict[str, str]:
        """
        Load YouTube video mappings from CSV file.

        Returns:
            Dictionary mapping neuron type names to YouTube video IDs
        """
        # Get input directory path relative to the project root
        project_root = Path(__file__).parent.parent.parent
        youtube_csv_path = project_root / "input" / "youtube.csv"
        youtube_mapping = {}

        if not youtube_csv_path.exists():
            logger.warning(f"YouTube CSV file not found at {youtube_csv_path}")
            return youtube_mapping

        try:
            with open(youtube_csv_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    # Split on first comma to get video_id and description
                    parts = line.split(',', 1)
                    if len(parts) != 2:
                        continue

                    video_id = parts[0].strip()
                    description = parts[1].strip()

                    # Store mapping with description as key
                    youtube_mapping[description] = video_id

        except Exception as e:
            logger.warning(f"Failed to load YouTube CSV: {e}")

        return youtube_mapping

    def _find_youtube_video(self, neuron_type: str) -> Optional[str]:
        """
        Find YouTube video ID for a neuron type by matching against descriptions.

        Args:
            neuron_type: Name of the neuron type (without soma side)

        Returns:
            YouTube video ID if found, None otherwise
        """
        # Skip empty or whitespace-only strings
        if not neuron_type or not neuron_type.strip():
            return None

        # Remove soma side suffixes (_L, _R, _M) from neuron type
        clean_neuron_type = re.sub(r'_[LRM]$', '', neuron_type)

        # Skip if cleaned neuron type is empty
        if not clean_neuron_type.strip():
            return None

        # Load YouTube mappings
        youtube_mapping = self._load_youtube_videos()

        # Try to find a match in the descriptions
        for description, video_id in youtube_mapping.items():
            # Look for the neuron type name in the description
            # Case-insensitive search for the clean neuron type name
            if clean_neuron_type.lower() in description.lower():
                return video_id

        return None



    def _get_primary_rois(self, connector):
        """Get primary ROIs based on dataset type and available data."""
        primary_rois = set()

        # First, try to get primary ROIs from NeuPrint if we have a connector
        if connector and hasattr(connector, 'client') and connector.client:
            try:
                # Get ROI hierarchy from cached connector method
                roi_hierarchy = connector._get_roi_hierarchy()

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









    def _get_region_for_type(self, neuron_type: str, connector) -> str:
        """
        Internal helper to return the 'region' (entry['parent_roi'])
        for a given neuron type.

        Strategy:
          1) Try the cache manager for this neuron type (fast path).
          2) If not cached, compute from NeuPrint data:
             - fetch neuron data,
             - aggregate ROI summary,
             - pick the top ROI (≥1.5% pre or post),
             - resolve its parent via the ROI hierarchy.

        Returns:
            Cleaned parent ROI string, or "" if unavailable.
        """

        def _clean_roi_name(name: str) -> str:
            if not name:
                return ""
            name = name.rstrip("*").strip()
            return re.sub(r"\s*\([RLM]\)$", "", name).strip()

        def _find_parent_recursive(target: str, tree: dict, parent: str = "") -> str:
            for k, v in (tree or {}).items():
                ck = _clean_roi_name(k)
                if ck == target:
                    return parent
                if isinstance(v, dict):
                    hit = _find_parent_recursive(target, v, ck)
                    if hit:
                        return hit
            return ""

        def _get_parent_from_hierarchy(roi_name: str, connector) -> str:
            try:
                hierarchy = connector._get_roi_hierarchy()
            except Exception:
                return ""
            if not hierarchy:
                return ""
            return _find_parent_recursive(_clean_roi_name(roi_name), hierarchy) or ""

        # ---- 1) check cache ---------------------------------------------------
        try:
            from .cache import create_cache_manager
            cache_manager = create_cache_manager(self.config.output.directory)
            cache_entry = cache_manager.load_neuron_type_cache(neuron_type)
            if cache_entry and getattr(cache_entry, "parent_roi", None):
                return _clean_roi_name(cache_entry.parent_roi)
        except Exception:
            pass

        # ---- 2) compute from NeuPrint data -----------------------------------
        try:
            data = connector.get_neuron_data(neuron_type, soma_side="combined")
            if not data:
                return ""

            roi_counts = data.get("roi_counts")
            neurons_df = data.get("neurons")
            if roi_counts is None or getattr(roi_counts, "empty", True) or neurons_df is None or getattr(neurons_df, "empty", True):
                return ""

            # Reuse this class's own aggregator
            roi_summary = self._aggregate_roi_data(roi_counts, neurons_df, "combined", connector)

            threshold = 1.5
            seen = set()
            top_roi_clean = None
            for roi in roi_summary or []:
                name = roi.get("name", "")
                pre_pct = roi.get("pre_percentage", 0.0) or 0.0
                post_pct = roi.get("post_percentage", 0.0) or 0.0
                if pre_pct >= threshold or post_pct >= threshold:
                    cleaned = _clean_roi_name(name)
                    if cleaned and cleaned not in seen:
                        top_roi_clean = cleaned
                        break

            if not top_roi_clean:
                return ""

            return _clean_roi_name(_get_parent_from_hierarchy(top_roi_clean, connector))
        except Exception:
            return ""
