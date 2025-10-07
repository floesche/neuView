"""
Scatter rendering config
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from ...utils import get_templates_dir

@dataclass
class ScatterConfig:
    """
    Configuration for rendering operations.

    This class encapsulates all the parameters needed to control
    the rendering process, including output format, layout settings,
    and file management options.
    """

     # Output configuration
    output_format: str = "svg"
    embed_mode: bool = False
    save_to_files: bool = True

    # File management
    output_dir: Optional[Path] = None
    scatter_dir: Optional[Path] = None

    # Layout configuration
    marker_size: int = 20
    margins: list = (60, 72, 64, 72)
    axis_gap_px: int = 10

    # SVG-specific configuration
    template_name: str = "scatterplot.svg.jinja"

    # Content configuration
    title: str = ""
    xlabel: str = "Population size (no. cells per type)"
    ylabel: str = "Cell size (no. columns per cell)"
    optic_lobe_side: str = None
    region_name: Optional[str] = None

    # Data configuration
    min_max_data: Optional[Dict[str, Any]] = None
    thresholds: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Post-initialization validation and setup."""

        if self.scatter_dir is None and self.output_dir:
            self.scatter_dir = self.output_dir / "scatter"
    
    # def get_template_path(self) -> Optional[Path]:
    #     """Get the full path to the template file."""
    #     # Templates are now loaded from the built-in templates directory
    #     return get_templates_dir() / self.template_name
    
@dataclass
class ScatterLayoutConfig:
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
    legend_title_x: float = 0.0
    legend_title_y: float = 0.0

    # Layer control configuration
    layer_control_x: float = 0.0
    layer_control_y: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert layout config to dictionary for template rendering."""
        return {
            "width": self.width,
            "height": self.height,
            "min_x": self.min_x,
            "min_y": self.min_y,
            "margin": self.margin,
            "legend_x": self.legend_x,
            "title_x": self.title_x,
            "hex_points": self.hex_points,
            "legend_width": self.legend_width,
            "legend_height": self.legend_height,
            "legend_y": self.legend_y,
            "legend_title_x": self.legend_title_x,
            "legend_title_y": self.legend_title_y,
            "layer_control_x": self.layer_control_x,
            "layer_control_y": self.layer_control_y,
        }


@dataclass
class ScatterLegendConfig:
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
            "legend_title": self.legend_title,
            "legend_type_name": self.legend_type_name,
            "title_y": self.title_y,
            "bin_height": self.bin_height,
            "thresholds": self.thresholds,
            "layer_thresholds": self.layer_thresholds,
        }
