"""
SVG renderer for hexagon grid visualizations.

This module provides SVG-specific rendering functionality using Jinja2 templates
to generate interactive SVG visualizations with tooltips and legends.
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from jinja2 import Environment, FileSystemLoader, Template

from .base_renderer import BaseRenderer
from .rendering_config import RenderingConfig, LayoutConfig, LegendConfig, OutputFormat
from .layout_calculator import LayoutCalculator

logger = logging.getLogger(__name__)


class SVGRenderer(BaseRenderer):
    """
    SVG renderer for hexagon grid visualizations.

    This renderer generates interactive SVG content using Jinja2 templates,
    supporting features like tooltips, legends, and layer controls.
    """

    def __init__(self, config: RenderingConfig, color_mapper=None):
        """
        Initialize the SVG renderer.

        Args:
            config: Rendering configuration object
            color_mapper: Color mapping utility (for template filters)
        """
        # Ensure output format is SVG
        if config.output_format != OutputFormat.SVG:
            config = config.copy(output_format=OutputFormat.SVG)

        super().__init__(config)
        self.color_mapper = color_mapper
        self.layout_calculator = LayoutCalculator(
            hex_size=config.hex_size,
            spacing_factor=config.spacing_factor,
            margin=config.margin
        )
        self._template_env = None
        self._template = None

    def render(self, hexagons: List[Dict[str, Any]],
               layout_config: LayoutConfig,
               legend_config: Optional[LegendConfig] = None) -> str:
        """
        Render hexagons to SVG format.

        Args:
            hexagons: List of hexagon data dictionaries
            layout_config: Layout configuration for positioning
            legend_config: Optional legend configuration

        Returns:
            SVG content as string
        """
        self.validate_hexagons(hexagons)

        if not hexagons:
            logger.warning("No hexagons provided for SVG rendering")
            return ""

        try:
            # Process hexagons with tooltips
            processed_hexagons = self._add_tooltips_to_hexagons(hexagons)

            # Setup template environment
            template = self._get_template()

            # Prepare template variables
            template_vars = self._prepare_template_variables(
                processed_hexagons, layout_config, legend_config
            )

            # Render SVG content
            svg_content = template.render(**template_vars)

            logger.debug(f"Successfully rendered SVG with {len(hexagons)} hexagons")
            return svg_content

        except Exception as e:
            logger.error(f"Failed to render SVG: {e}")
            raise ValueError(f"SVG rendering failed: {e}")

    def get_file_extension(self) -> str:
        """Get the file extension for SVG files."""
        return ".svg"

    def supports_interactive_features(self) -> bool:
        """SVG supports interactive features like tooltips and hover effects."""
        return True

    def _write_content_to_file(self, content: str, file_path: Path) -> None:
        """
        Write SVG content to file.

        Args:
            content: SVG content to write
            file_path: Path to write to
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _get_template(self) -> Template:
        """
        Get or load the Jinja2 template for SVG rendering.

        Returns:
            Jinja2 Template object

        Raises:
            ValueError: If template cannot be loaded
        """
        if self._template is not None:
            return self._template

        try:
            # Setup template environment
            if not self._template_env:
                template_dir = self._get_template_directory()
                self._template_env = Environment(loader=FileSystemLoader(template_dir))
                self._setup_template_filters()

            # Load template
            self._template = self._template_env.get_template(self.config.template_name)
            return self._template

        except Exception as e:
            logger.error(f"Failed to load SVG template: {e}")
            raise ValueError(f"Template loading failed: {e}")

    def _get_template_directory(self) -> str:
        """
        Get the template directory path.

        Returns:
            Path to template directory

        Raises:
            ValueError: If template directory cannot be found
        """
        if self.config.template_dir:
            return str(self.config.template_dir)

        # Default to templates directory relative to this module
        current_dir = Path(__file__).parent
        template_dir = current_dir / '..' / '..' / '..' / '..' / 'templates'
        template_dir = template_dir.resolve()

        if not template_dir.exists():
            raise ValueError(f"Template directory not found: {template_dir}")

        return str(template_dir)

    def _setup_template_filters(self) -> None:
        """Setup custom Jinja2 filters for the template."""
        if not self._template_env or not self.color_mapper:
            return

        # Create filter functions that capture min_max_data for region-specific normalization
        min_max_data = self.config.min_max_data or {}

        def synapses_to_colors(synapses_list, region):
            """Convert synapses_list to synapse_colors using normalization."""
            if not synapses_list or not min_max_data:
                return [self.color_mapper.palette.white] * len(synapses_list)

            syn_min = float(min_max_data.get('min_syn_region', {}).get(region, 0.0))
            syn_max = float(min_max_data.get('max_syn_region', {}).get(region, 0.0))

            colors = []
            for syn_val in synapses_list:
                if syn_val > 0:
                    color = self.color_mapper.map_value_to_color(float(syn_val), syn_min, syn_max)
                else:
                    color = self.color_mapper.palette.white
                colors.append(color)

            return colors

        def neurons_to_colors(neurons_list, region):
            """Convert neurons_list to neuron_colors using normalization."""
            if not neurons_list or not min_max_data:
                return [self.color_mapper.palette.white] * len(neurons_list) if neurons_list else []

            cel_min = float(min_max_data.get('min_cells_region', {}).get(region, 0.0))
            cel_max = float(min_max_data.get('max_cells_region', {}).get(region, 0.0))

            colors = []
            for cel_val in neurons_list:
                if cel_val > 0:
                    color = self.color_mapper.map_value_to_color(float(cel_val), cel_min, cel_max)
                else:
                    color = self.color_mapper.palette.white
                colors.append(color)

            return colors

        # Register filters
        self._template_env.filters['synapses_to_colors'] = synapses_to_colors
        self._template_env.filters['neurons_to_colors'] = neurons_to_colors

    def _prepare_template_variables(self, hexagons: List[Dict[str, Any]],
                                   layout_config: LayoutConfig,
                                   legend_config: Optional[LegendConfig]) -> Dict[str, Any]:
        """
        Prepare variables for template rendering.

        Args:
            hexagons: Processed hexagon data
            layout_config: Layout configuration
            legend_config: Optional legend configuration

        Returns:
            Dictionary of template variables
        """
        # Get data hexagons for legend
        data_hexagons = [h for h in hexagons if h.get('status') == 'has_data']

        # Prepare template variables
        template_vars = {
            'width': layout_config.width,
            'height': layout_config.height,
            'title': self.config.title,
            'subtitle': self.config.subtitle,
            'hexagons': hexagons,
            'hex_points': layout_config.hex_points.split(),
            'min_x': layout_config.min_x,
            'min_y': layout_config.min_y,
            'margin': layout_config.margin,
            'number_precision': layout_config.number_precision,
            'data_hexagons': data_hexagons,
            'legend_x': layout_config.legend_x,
            'legend_y': layout_config.legend_y,
            'legend_width': layout_config.legend_width,
            'legend_height': layout_config.legend_height,
            'legend_title_x': layout_config.legend_title_x,
            'legend_title_y': layout_config.legend_title_y,
            'title_x': layout_config.title_x,
            'layer_control_x': layout_config.layer_control_x,
            'layer_control_y': layout_config.layer_control_y,
            'enumerate': enumerate,
            'soma_side': self.config.soma_side,
            'min_max_data': self.config.min_max_data or {}
        }

        # Add color information if available
        if self.color_mapper:
            template_vars['colors'] = self.color_mapper.palette.get_all_colors()

        # Add legend configuration if available
        if legend_config:
            template_vars.update(legend_config.to_dict())

        return template_vars

    def _add_tooltips_to_hexagons(self, hexagons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process tooltip data for hexagons that already have tooltip information.

        Args:
            hexagons: List of hexagon data dictionaries with existing tooltip data

        Returns:
            List of hexagons with properly formatted tooltip data for SVG template
        """
        processed_hexagons = []

        for hexagon in hexagons:
            # Create a copy to avoid modifying original data
            processed_hex = hexagon.copy()

            # Check if tooltip data already exists, if not generate it
            if 'tooltip' not in hexagon or 'tooltip_layers' not in hexagon:
                tooltip_data = self._generate_tooltip_data(hexagon)
                processed_hex.update(tooltip_data)
            else:
                # Use existing tooltip data but format for SVG template
                import json
                processed_hex['base-title'] = json.dumps(hexagon.get('tooltip', ''))
                processed_hex['tooltip-layers'] = json.dumps(hexagon.get('tooltip_layers', []))

            processed_hexagons.append(processed_hex)

        return processed_hexagons

    def _generate_tooltip_data(self, hexagon: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate tooltip data for a single hexagon.

        Args:
            hexagon: Hexagon data dictionary

        Returns:
            Dictionary with tooltip-related data
        """
        # Extract basic hexagon information
        region = hexagon.get('region', 'Unknown')
        hex1 = hexagon.get('hex1', 0)
        hex2 = hexagon.get('hex2', 0)
        status = hexagon.get('status', 'unknown')
        value = hexagon.get('value', 0)
        metric_type = hexagon.get('metric_type', 'synapse_density')

        # Generate base tooltip similar to original hexagon generator
        if status == 'not_in_region':
            base_title = f"Column: {hex1}, {hex2}\nColumn not identified in {region}"
        elif status == 'no_data':
            label = "Synapse count" if metric_type == 'synapse_density' else "Cell count"
            base_title = f"Column: {hex1}, {hex2}\n{label}: 0\nROI: {region}"
        else:  # has_data
            label = "Synapse count" if metric_type == 'synapse_density' else "Cell count"
            base_title = f"Column: {hex1}, {hex2}\n{label}: {int(value)}\nROI: {region}"

        # Generate layer-specific tooltip information
        layer_values = hexagon.get('layer_values', [])
        tooltip_layers = []

        if layer_values and isinstance(layer_values, list):
            for i, layer_value in enumerate(layer_values, start=1):
                if status == 'not_in_region':
                    layer_tip = f"Column: {hex1}, {hex2}\nColumn not identified in {region} layer({i})"
                elif status == 'no_data':
                    layer_tip = f"0\nROI: {region}{i}"
                else:  # has_data
                    layer_tip = f"{int(layer_value)}\nROI: {region}{i}"
                tooltip_layers.append(1)

        # Prepare tooltip data for template
        import json
        tooltip_data = {
            'base-title': json.dumps(base_title),
            'tooltip-layers': json.dumps(tooltip_layers),
            'tooltip-region': region,
            'tooltip-hex1': hex1,
            'tooltip-hex2': hex2,
            'tooltip-value': value,
            'tooltip-status': status
        }

        return tooltip_data

    def update_config(self, **config_updates) -> None:
        """
        Update rendering configuration and reset cached components.

        Args:
            **config_updates: Configuration parameters to update
        """
        self.config = self.config.copy(**config_updates)
        self._template = None
        self._template_env = None
        self.layout_calculator = LayoutCalculator(
            hex_size=self.config.hex_size,
            spacing_factor=self.config.spacing_factor,
            margin=self.config.margin
        )
