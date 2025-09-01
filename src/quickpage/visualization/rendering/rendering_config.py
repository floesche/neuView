"""
Configuration classes and enums for the rendering system.

This module defines the configuration structures used by the rendering system
to control output format, layout parameters, and rendering behavior.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path


class OutputFormat(Enum):
    """Supported output formats for rendering."""
    SVG = "svg"
    PNG = "png"


@dataclass
class RenderingConfig:
    """
    Configuration for rendering operations.

    This class encapsulates all the parameters needed to control
    the rendering process, including output format, layout settings,
    and file management options.
    """

    # Output configuration
    output_format: OutputFormat = OutputFormat.SVG
    embed_mode: bool = False
    save_to_files: bool = False

    # File management
    output_dir: Optional[Path] = None
    eyemaps_dir: Optional[Path] = None

    # Layout configuration
    hex_size: int = 6
    spacing_factor: float = 1.5
    margin: int = 10

    # SVG-specific configuration
    template_dir: Optional[Path] = None
    template_name: str = "comprehensive_hexagon_grid.svg"

    # PNG-specific configuration
    png_quality: int = 90
    png_scale: float = 1.0

    # Content configuration
    title: str = ""
    subtitle: str = ""
    metric_type: str = ""
    soma_side: Optional[str] = None
    neuron_type: Optional[str] = None
    region_name: Optional[str] = None

    # Data configuration
    min_max_data: Optional[Dict[str, Any]] = None
    thresholds: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Post-initialization validation and setup."""
        if self.save_to_files and not self.output_dir:
            raise ValueError("output_dir must be set when save_to_files is True")

        if self.eyemaps_dir is None and self.output_dir:
            self.eyemaps_dir = self.output_dir / 'eyemaps'

    @property
    def should_save_files(self) -> bool:
        """Check if files should be saved to disk."""
        return self.save_to_files and not self.embed_mode and self.output_dir is not None

    def get_template_path(self) -> Optional[Path]:
        """Get the full path to the template file."""
        if not self.template_dir:
            return None
        return self.template_dir / self.template_name

    def get_clean_filename(self, base_filename: str) -> str:
        """Get a cleaned filename suitable for file system use."""
        clean_name = base_filename.replace(" ", "_").replace("(", "").replace(")", "")
        extension = ".svg" if self.output_format == OutputFormat.SVG else ".png"
        return clean_name + extension

    def copy(self, **overrides) -> 'RenderingConfig':
        """Create a copy of this config with optional overrides."""
        from dataclasses import replace
        return replace(self, **overrides)


@dataclass
class LayoutConfig:
    """
    Configuration for layout calculations.

    This class contains parameters specific to layout computation
    and coordinate transformations.
    """

    width: int = 0
    height: int = 0
    min_x: float = 0.0
    min_y: float = 0.0
    margin: int = 10
    legend_x: float = 0.0
    title_x: float = 0.0
    hex_points: str = ""

    # Legend configuration
    legend_width: int = 12
    legend_height: int = 60
    legend_y: float = 0.0

    # Template compatibility
    number_precision: int = 2

    def to_dict(self) -> Dict[str, Any]:
        """Convert layout config to dictionary for template rendering."""
        return {
            'width': self.width,
            'height': self.height,
            'min_x': self.min_x,
            'min_y': self.min_y,
            'margin': self.margin,
            'legend_x': self.legend_x,
            'title_x': self.title_x,
            'hex_points': self.hex_points,
            'legend_width': self.legend_width,
            'legend_height': self.legend_height,
            'legend_y': self.legend_y,
            'number_precision': self.number_precision
        }


@dataclass
class LegendConfig:
    """
    Configuration for legend rendering.

    This class contains parameters for rendering the color legend
    and associated UI elements.
    """

    legend_title: str = ""
    legend_type_name: str = ""
    title_y: float = 0.0
    bin_height: int = 12
    thresholds: Optional[Dict[str, Any]] = None
    layer_thresholds: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert legend config to dictionary for template rendering."""
        return {
            'legend_title': self.legend_title,
            'legend_type_name': self.legend_type_name,
            'title_y': self.title_y,
            'bin_height': self.bin_height,
            'thresholds': self.thresholds,
            'layer_thresholds': self.layer_thresholds
        }
