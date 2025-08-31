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
from typing import Dict, Any, Optional, List

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
from .services.template_context_service import TemplateContextService
from .services.data_processing_service import DataProcessingService
from .services.database_query_service import DatabaseQueryService
from .services.neuron_selection_service import NeuronSelectionService
from .services.file_service import FileService
from .services.threshold_service import ThresholdService
from .services.youtube_service import YouTubeService
from .services.roi_analysis_service import ROIAnalysisService
from .services.cache_service import CacheService
from .services.page_generation_orchestrator import PageGenerationOrchestrator
from .models.page_generation import PageGenerationRequest

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

        # Copy static files to output directory using resource manager
        self.resource_manager.copy_static_files()

        # Initialize new services
        self.template_context_service = TemplateContextService(self)
        self.data_processing_service = DataProcessingService(self)
        self.database_query_service = DatabaseQueryService(config, cache_manager, self.data_processing_service)
        self.neuron_selection_service = NeuronSelectionService(config)
        self.file_service = FileService()
        self.threshold_service = ThresholdService()

        # Initialize Phase 1 refactored services
        self.youtube_service = YouTubeService()
        self.cache_service = CacheService(cache_manager, self)
        self.roi_analysis_service = ROIAnalysisService(self)

        # Initialize URL generation service (after new services are available)
        self.url_generation_service = URLGenerationService(
            config, self.env, self,
            self.neuron_selection_service,
            self.database_query_service
        )

        # Initialize caches for expensive operations
        self._all_columns_cache = None
        self._column_analysis_cache = {}

        # Initialize page generation orchestrator
        self.orchestrator = PageGenerationOrchestrator(self)



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

        Delegates to the neuron selection service.
        """
        return self.neuron_selection_service.select_bodyid_by_synapse_percentile(neuron_type, neurons_df, percentile)

    def _select_bodyids_by_soma_side(self, neuron_type: str, neurons_df: pd.DataFrame, soma_side: Optional[str], percentile: float = 95) -> List[int]:
        """
        Select bodyID(s) based on soma side and synapse count percentiles.

        Delegates to the neuron selection service.
        """
        return self.neuron_selection_service.select_bodyids_by_soma_side(neuron_type, neurons_df, soma_side, percentile)

    def _get_connected_bids(self, visible_neurons: List[int], connector) -> Dict:
        """
        Get bodyIds of the top cell from each type that are connected with the
        current 'visible_neuron' in the Neuroglancer view.

        Delegates to the database query service.
        """
        return self.database_query_service.get_connected_bodyids(visible_neurons, connector)

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
            connector: NeuPrint connector instance
            image_format: Format for hexagon grid images ('svg' or 'png')
            embed_images: If True, embed images in HTML; if False, save to files
            uncompress: If True, don't minify HTML output

        Returns:
            Path to the generated HTML file
        """
        return self.orchestrator.generate_page_legacy(
            neuron_type, neuron_data, soma_side, connector,
            image_format, embed_images, uncompress
        )

    def generate_page_from_neuron_type(self, neuron_type_obj, connector, image_format: str = 'svg', embed_images: bool = False, uncompress: bool = False) -> str:
        """
        Generate an HTML page from a NeuronType object.

        Args:
            neuron_type_obj: NeuronType instance with data
            connector: NeuPrint connector instance
            image_format: Format for hexagon grid images ('svg' or 'png')
            embed_images: If True, embed images in HTML; if False, save to files
            uncompress: If True, don't minify HTML output

        Returns:
            Path to the generated HTML file
        """
        # Import here to avoid circular imports
        from .neuron_type import NeuronType

        if not isinstance(neuron_type_obj, NeuronType):
            raise TypeError("Expected NeuronType object")

        return self.orchestrator.generate_page_from_neuron_type_legacy(
            neuron_type_obj, connector, image_format, embed_images, uncompress
        )

    def generate_page_unified(self, request: PageGenerationRequest):
        """
        Generate an HTML page using the unified orchestrator workflow.

        This is the new unified method that replaces both generate_page and
        generate_page_from_neuron_type methods. It provides a single interface
        for all page generation needs.

        Args:
            request: PageGenerationRequest containing all generation parameters

        Returns:
            PageGenerationResponse with the result including output path and metadata
        """
        return self.orchestrator.generate_page(request)




    def _aggregate_roi_data(self, roi_counts_df, neurons_df, soma_side, connector=None):
        """Aggregate ROI data across neurons matching the specific soma side to get total pre/post synapses per ROI (primary ROIs only)."""
        return self.data_processing_service.aggregate_roi_data(roi_counts_df, neurons_df, soma_side, connector)

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
        return self.roi_analysis_service.get_all_dataset_layers(layer_pattern, connector)

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
        return self.roi_analysis_service.get_columns_for_neuron_type(connector, neuron_type)

    def _get_columns_from_neuron_cache(self, neuron_type: str):
        """
        Extract column data from neuron type cache if available.

        Args:
            neuron_type: The neuron type to get cached column data for

        Returns:
            Tuple of (columns_data, region_columns_map) or (None, None) if not cached
        """
        return self.cache_service.get_columns_from_neuron_cache(neuron_type)

    def _get_all_possible_columns_from_dataset(self, connector):
        """
        Query the dataset to get all possible column coordinates.

        Delegates to the database query service.
        """
        return self.database_query_service.get_all_possible_columns_from_dataset(connector)

    def _load_persistent_columns_cache(self, cache_key):
        """Load persistent cache for all columns dataset query."""
        return self.cache_service.load_persistent_columns_cache(cache_key)

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
        return self.data_processing_service.get_column_layer_values(neuron_type, connector)

    def _compute_thresholds(self, df: pd.DataFrame, n_bins: int = 5):
        """
        Compute threshold lists for synapse and neuron counts at different aggregation levels.

        Delegates to ThresholdService for the actual computation.
        """
        return self.threshold_service.compute_thresholds(df, n_bins)

    def _layer_thresholds(self, values, n_bins=5):
        """
        Return n_bins+1 thresholds from min..max for a 1D list of numbers.

        Delegates to ThresholdService for the actual computation.
        """
        return self.threshold_service.layer_thresholds(values, n_bins)

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
            all_possible_columns, region_columns_map = self.database_query_service.get_all_possible_columns_from_dataset(connector)

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
        Delegates to FileService for the actual generation.

        Args:
            neuron_type: The neuron type name
            soma_side: The soma side ('left', 'right', 'middle', 'all', 'combined')

        Returns:
            HTML filename string
        """
        return FileService.generate_filename(neuron_type, soma_side)

    def _generate_filename(self, neuron_type: str, soma_side: str) -> str:
        """Instance method wrapper for backwards compatibility."""
        return self.file_service.generate_filename_instance(neuron_type, soma_side)

    def _load_youtube_videos(self) -> Dict[str, str]:
        """
        Load YouTube video mappings from CSV file.

        Returns:
            Dictionary mapping neuron type names to YouTube video IDs
        """
        return self.youtube_service.load_youtube_videos()

    def _find_youtube_video(self, neuron_type: str) -> Optional[str]:
        """
        Find YouTube video ID for a neuron type by matching against descriptions.

        Args:
            neuron_type: Name of the neuron type (without soma side)

        Returns:
            YouTube video ID if found, None otherwise
        """
        return self.youtube_service.find_youtube_video(neuron_type)



    def _get_primary_rois(self, connector):
        """Get primary ROIs based on dataset type and available data."""
        return self.roi_analysis_service.get_primary_rois(connector)

    def _extract_roi_names_from_hierarchy(self, hierarchy, roi_names=None):
        """
        Recursively extract all ROI names from the hierarchical dictionary structure.

        Args:
            hierarchy: Dictionary or any structure from fetch_roi_hierarchy
            roi_names: Set to collect ROI names (used for recursion)

        Returns:
            Set of all ROI names found in the hierarchy
        """
        return self.roi_analysis_service.extract_roi_names_from_hierarchy(hierarchy, roi_names)

    def _get_region_for_type(self, neuron_type: str, connector) -> str:
        """Find the type's assigned "region" - used for setting the NG view."""
        return self.roi_analysis_service.get_region_for_type(neuron_type, connector)
