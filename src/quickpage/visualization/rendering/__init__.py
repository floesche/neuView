"""
Rendering system for hexagon grid visualizations.

This module provides dedicated rendering components for generating SVG and PNG
output formats from processed hexagon data. The rendering system is designed
to be modular, testable, and maintainable.

Components:
- SVGRenderer: Handles SVG generation using Jinja2 templates
- PNGRenderer: Handles PNG generation via SVG-to-PNG conversion
- RenderingManager: Coordinates rendering operations and format selection
- BaseRenderer: Abstract base class for all renderers
"""

from .base_renderer import BaseRenderer
from .svg_renderer import SVGRenderer
from .png_renderer import PNGRenderer
from .rendering_manager import RenderingManager
from .rendering_config import RenderingConfig, OutputFormat, LayoutConfig, LegendConfig
from .layout_calculator import LayoutCalculator
from .region_config import RegionConfigRegistry, Region, RegionConfig

__all__ = [
    "BaseRenderer",
    "SVGRenderer",
    "PNGRenderer",
    "RenderingManager",
    "RenderingConfig",
    "OutputFormat",
    "LayoutConfig",
    "LegendConfig",
    "LayoutCalculator",
    "RegionConfigRegistry",
    "Region",
    "RegionConfig",
]
