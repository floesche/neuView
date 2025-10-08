"""
Scatter rendering config
"""
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from ...utils import get_templates_dir

@dataclass
class ScatterConfig:
    """
    Scatter config
    """

     # Output configuration
    output_format: str = "svg"
    save_to_files: bool = True

    # File management
    scatter_dir: Optional[Path] = "output/scatter"
    scatter_fname = f"scatter.{output_format}"

    # Layout configuration
    margins: list = (60, 72, 64, 72)
    axis_gap_px: int = 10

    # Marker features
    marker_size: int = 4
    marker_line_width: float = 0.5

    # SVG-specific configuration
    template_name: str = "scatterplot.svg.jinja"

    # Content configuration
    title: str = ""
    xlabel: str = "Population size (no. cells per type)"
    ylabel: str = "Cell size (no. columns per cell)"
    legend_label: str = "Coverage factor (cells per column)"

    # Data configuration
    min_max_data: Optional[Dict[str, Any]] = None
    thresholds: Optional[Dict[str, Any]] = None

    top, right, bottom, left = margins
    margin_top = top
    margin_right = right
    margin_bottom = bottom
    margin_left = left
    width = 680
    height = 460
    plot_w = width - left - right
    plot_h = height - top - bottom

    side_px = min(plot_w, plot_h)
    plot_w = side_px
    plot_h = side_px
    
    xticks = [1, 10, 100, 1000]
    yticks = [1, 10, 100, 1000]

    legend_w = 12
    
    def get_template_path(self) -> Optional[Path]:
        """Get the full path to the template file."""
        # Templates are now loaded from the built-in templates directory
        return get_templates_dir() / self.template_name

    def to_dict(self) -> Dict[str, Any]:
        """Convert layout config to dictionary for template rendering."""
        return {
            "width": self.width,
            "height": self.height,
            "xticks": self.xticks,
            "yticks": self.yticks,
            "marker_size": self.marker_size,
            "margin_top": self.top,
            "margin_right": self.right,
            "margin_bottom": self.bottom,
            "margin_left": self.left,
            "legend_w": self.legend_w,
            "xlabel": self.xlabel,
            "ylabel": self.ylabel,
            "legend_label": self.legend_label,
            "axis_gap_px": self.axis_gap_px, 
            "plot_h": self.plot_h,
            "plot_w": self.plot_w,
        }
