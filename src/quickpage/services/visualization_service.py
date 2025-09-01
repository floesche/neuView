"""
Visualization Service

Handles visualization generation including hexagonal grids, region-based
visualizations, and other graphical elements for neuron type pages.
"""

import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class VisualizationService:
    """Service for generating visualizations and graphical elements."""

    def __init__(self, config, eyemap_generator, color_utils):
        """Initialize the visualization service.

        Args:
            config: Configuration object
            eyemap_generator: EyemapGenerator instance
            color_utils: ColorUtils instance for color operations
        """
        self.config = config
        self.eyemap_generator = eyemap_generator
        self.color_utils = color_utils

    def generate_region_hexagonal_grids(self, column_summary: List[Dict], neuron_type: str,
                                      soma_side: str, file_type: str = 'svg',
                                      save_to_files: bool = True, connector=None,
                                      min_max_data: Optional[Dict] = None) -> Dict[str, Dict[str, str]]:
        """
        Generate separate hexagonal grid visualizations for each region (ME, LO, LOP).

        Args:
            column_summary: List of column data dictionaries
            neuron_type: Name of the neuron type
            soma_side: Soma side for the visualization
            file_type: Output file format ('svg' or 'png')
            save_to_files: Whether to save files or return embedded content
            connector: Database connector for additional data
            min_max_data: Optional min/max values for normalization

        Returns:
            Dictionary containing visualization data for each region
        """
        try:
            if not column_summary:
                logger.debug(f"No column summary data for {neuron_type}")
                return {}

            # Group data by region
            regions_data = self._group_data_by_region(column_summary)

            if not regions_data:
                logger.debug(f"No region data found for {neuron_type}")
                return {}

            # Generate grids for each region
            region_grids = {}
            for region, data in regions_data.items():
                try:
                    grid_result = self._generate_single_region_grid(
                        region, data, neuron_type, soma_side,
                        file_type, save_to_files, min_max_data
                    )
                    if grid_result:
                        region_grids[region] = grid_result
                        logger.debug(f"Generated grid for region {region}")

                except Exception as e:
                    logger.error(f"Error generating grid for region {region}: {e}")
                    continue

            return region_grids

        except Exception as e:
            logger.error(f"Error generating region hexagonal grids: {e}")
            return {}

    def _group_data_by_region(self, column_summary: List[Dict]) -> Dict[str, List[Dict]]:
        """Group column summary data by region (ME, LO, LOP)."""
        regions_data = {}

        for item in column_summary:
            region = item.get('region')
            if region and region in ['ME', 'LO', 'LOP']:
                if region not in regions_data:
                    regions_data[region] = []
                regions_data[region].append(item)

        return regions_data

    def _generate_single_region_grid(self, region: str, data: List[Dict],
                                   neuron_type: str, soma_side: str,
                                   file_type: str, save_to_files: bool,
                                   min_max_data: Optional[Dict] = None) -> Optional[Dict[str, str]]:
        """Generate hexagonal grid for a single region."""
        try:
            # Prepare data for hexagon generator
            hex_data = []
            for item in data:
                hex_data.append({
                    'hex1': item.get('hex1', 0),
                    'hex2': item.get('hex2', 0),
                    'synapse_density': item.get('synapse_density', 0),
                    'neuron_count': item.get('neuron_count', 0),
                    'column': item.get('column', '')
                })

            if not hex_data:
                return None

            # Generate base filename
            filename_base = f"{neuron_type}_{soma_side}_{region}".replace('/', '_').replace(' ', '_')

            # Generate visualizations
            grid_results = {}

            # Generate synapse density grid
            density_result = self.eyemap_generator.generate_grid(
                hex_data,
                value_key='synapse_density',
                title=f"{region} - Synapse Density",
                filename_base=f"{filename_base}_density",
                file_type=file_type,
                save_to_files=save_to_files,
                min_max_values=min_max_data.get('density') if min_max_data else None
            )

            if density_result:
                grid_results['density'] = density_result

            # Generate neuron count grid
            count_result = self.eyemap_generator.generate_grid(
                hex_data,
                value_key='neuron_count',
                title=f"{region} - Neuron Count",
                filename_base=f"{filename_base}_count",
                file_type=file_type,
                save_to_files=save_to_files,
                min_max_values=min_max_data.get('count') if min_max_data else None
            )

            if count_result:
                grid_results['count'] = count_result

            return grid_results if grid_results else None

        except Exception as e:
            logger.error(f"Error generating grid for region {region}: {e}")
            return None

    def generate_and_save_hexagon_grids(self, column_summary: List[Dict],
                                      neuron_type: str, soma_side: str,
                                      file_type: str = 'svg') -> Dict[str, Any]:
        """
        Generate and save hexagon grids for all regions.

        Args:
            column_summary: Column data summary
            neuron_type: Name of the neuron type
            soma_side: Soma side identifier
            file_type: Output file format

        Returns:
            Dictionary containing generated grid information
        """
        return self.generate_region_hexagonal_grids(
            column_summary, neuron_type, soma_side,
            file_type=file_type, save_to_files=True
        )

    def create_color_scale(self, values: List[float], color_scheme: str = 'viridis') -> Dict[str, Any]:
        """
        Create a color scale for visualizations.

        Args:
            values: List of numeric values to create scale for
            color_scheme: Color scheme name

        Returns:
            Dictionary containing color scale information
        """
        try:
            if not values or len(values) == 0:
                return {'colors': [], 'scale': []}

            # Remove any None or invalid values
            clean_values = [v for v in values if v is not None and not pd.isna(v)]

            if not clean_values:
                return {'colors': [], 'scale': []}

            # Calculate scale points
            min_val = min(clean_values)
            max_val = max(clean_values)

            if min_val == max_val:
                # Single value case
                return {
                    'colors': [self.color_utils.get_color_for_value(min_val, min_val, max_val)],
                    'scale': [min_val],
                    'min': min_val,
                    'max': max_val
                }

            # Create scale with multiple points
            scale_points = []
            colors = []
            num_points = 5  # Number of points in the scale

            for i in range(num_points):
                scale_value = min_val + (max_val - min_val) * (i / (num_points - 1))
                scale_points.append(scale_value)
                colors.append(self.color_utils.get_color_for_value(scale_value, min_val, max_val))

            return {
                'colors': colors,
                'scale': scale_points,
                'min': min_val,
                'max': max_val
            }

        except Exception as e:
            logger.error(f"Error creating color scale: {e}")
            return {'colors': [], 'scale': []}

    def generate_legend(self, title: str, color_scale: Dict[str, Any],
                       units: str = '') -> str:
        """
        Generate HTML legend for visualizations.

        Args:
            title: Legend title
            color_scale: Color scale data
            units: Units for the values

        Returns:
            HTML string for the legend
        """
        try:
            if not color_scale or not color_scale.get('colors'):
                return ""

            colors = color_scale['colors']
            scale = color_scale['scale']

            if len(colors) != len(scale):
                return ""

            # Generate legend HTML
            legend_html = f'<div class="visualization-legend">'
            legend_html += f'<h4>{title}</h4>'
            legend_html += f'<div class="color-scale">'

            for i, (color, value) in enumerate(zip(colors, scale)):
                legend_html += f'<div class="scale-item">'
                legend_html += f'<span class="color-box" style="background-color: {color};"></span>'
                legend_html += f'<span class="scale-value">{value:.2f}{units}</span>'
                legend_html += f'</div>'

            legend_html += f'</div></div>'

            return legend_html

        except Exception as e:
            logger.error(f"Error generating legend: {e}")
            return ""

    def validate_visualization_data(self, data: List[Dict]) -> bool:
        """
        Validate data for visualization generation.

        Args:
            data: List of data dictionaries

        Returns:
            True if data is valid for visualization
        """
        try:
            if not data or len(data) == 0:
                return False

            required_fields = ['hex1', 'hex2']

            for item in data:
                if not isinstance(item, dict):
                    return False

                for field in required_fields:
                    if field not in item:
                        return False

                # Check that hex coordinates are numeric
                try:
                    float(item['hex1'])
                    float(item['hex2'])
                except (ValueError, TypeError):
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating visualization data: {e}")
            return False

    def get_supported_file_types(self) -> List[str]:
        """Get list of supported file types for visualizations."""
        return ['svg', 'png', 'pdf']

    def cleanup_visualization_files(self, neuron_type: str, soma_side: str) -> int:
        """
        Clean up old visualization files for a neuron type.

        Args:
            neuron_type: Name of the neuron type
            soma_side: Soma side identifier

        Returns:
            Number of files cleaned up
        """
        try:
            files_cleaned = 0

            # Get eyemaps directory from eyemap generator
            if hasattr(self.eyemap_generator, 'eyemaps_dir'):
                eyemaps_dir = Path(self.eyemap_generator.eyemaps_dir)

                if eyemaps_dir.exists():
                    # Pattern for files to clean up
                    pattern_base = f"{neuron_type}_{soma_side}".replace('/', '_').replace(' ', '_')

                    for file_path in eyemaps_dir.glob(f"{pattern_base}*"):
                        try:
                            file_path.unlink()
                            files_cleaned += 1
                        except Exception as e:
                            logger.warning(f"Could not delete file {file_path}: {e}")

            logger.debug(f"Cleaned up {files_cleaned} visualization files")
            return files_cleaned

        except Exception as e:
            logger.error(f"Error cleaning up visualization files: {e}")
            return 0
