"""
Base renderer abstract class for hexagon grid visualizations.

This module defines the abstract base class that all renderers must implement,
providing a consistent interface and common functionality for rendering operations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from .rendering_config import RenderingConfig, LayoutConfig, LegendConfig

logger = logging.getLogger(__name__)


class BaseRenderer(ABC):
    """
    Abstract base class for all hexagon grid renderers.

    This class defines the interface that all renderers must implement
    and provides common functionality for validation and error handling.
    """

    def __init__(self, config: RenderingConfig):
        """
        Initialize the base renderer.

        Args:
            config: Rendering configuration object
        """
        self.config = config
        self._validate_config()

    def _validate_config(self) -> None:
        """
        Validate the rendering configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        if not isinstance(self.config, RenderingConfig):
            raise ValueError("config must be a RenderingConfig instance")

        if self.config.save_to_files and not self.config.output_dir:
            raise ValueError("output_dir must be set when save_to_files is True")

        if self.config.hex_size <= 0:
            raise ValueError("hex_size must be positive")

        if self.config.spacing_factor <= 0:
            raise ValueError("spacing_factor must be positive")

    @abstractmethod
    def render(self, hexagons: List[Dict[str, Any]],
               layout_config: LayoutConfig,
               legend_config: Optional[LegendConfig] = None) -> str:
        """
        Render hexagons to the target format.

        Args:
            hexagons: List of hexagon data dictionaries
            layout_config: Layout configuration for positioning
            legend_config: Optional legend configuration

        Returns:
            Rendered content as string

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """
        Get the file extension for this renderer's output format.

        Returns:
            File extension including the dot (e.g., '.svg', '.png')

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        pass

    def validate_hexagons(self, hexagons: List[Dict[str, Any]]) -> None:
        """
        Validate hexagon data structure.

        Args:
            hexagons: List of hexagon data dictionaries

        Raises:
            ValueError: If hexagon data is invalid
        """
        if not isinstance(hexagons, list):
            raise ValueError("hexagons must be a list")

        if not hexagons:
            logger.warning("Empty hexagons list provided")
            return

        required_fields = ['x', 'y', 'color', 'hex1', 'hex2']
        for i, hexagon in enumerate(hexagons):
            if not isinstance(hexagon, dict):
                raise ValueError(f"Hexagon at index {i} must be a dictionary")

            for field in required_fields:
                if field not in hexagon:
                    raise ValueError(f"Hexagon at index {i} missing required field: {field}")

            # Validate numeric fields
            try:
                float(hexagon['x'])
                float(hexagon['y'])
                int(hexagon['hex1'])
                int(hexagon['hex2'])
            except (ValueError, TypeError) as e:
                raise ValueError(f"Hexagon at index {i} has invalid numeric field: {e}")

    def save_to_file(self, content: str, filename: str) -> str:
        """
        Save rendered content to a file.

        Args:
            content: Rendered content to save
            filename: Base filename without extension

        Returns:
            Relative path to the saved file

        Raises:
            ValueError: If saving is not configured or fails
        """
        if self.config.embed_mode:
            raise ValueError("File saving disabled in embed mode")

        if not self.config.output_dir:
            raise ValueError("output_dir must be set to save files")

        if not self.config.eyemaps_dir:
            raise ValueError("eyemaps_dir must be set to save files")

        # Ensure the eyemaps directory exists
        self.config.eyemaps_dir.mkdir(parents=True, exist_ok=True)

        # Create clean filename with appropriate extension
        clean_filename = self.config.get_clean_filename(filename)
        file_path = self.config.eyemaps_dir / clean_filename

        try:
            self._write_content_to_file(content, file_path)
            logger.info(f"Saved {self.__class__.__name__} output to {file_path}")

            # Return relative path from neuron page location (types/ to eyemaps/)
            return f"../eyemaps/{clean_filename}"

        except Exception as e:
            logger.error(f"Failed to save file {file_path}: {e}")
            raise ValueError(f"Failed to save file: {e}")

    @abstractmethod
    def _write_content_to_file(self, content: str, file_path: Path) -> None:
        """
        Write content to file using format-specific method.

        Args:
            content: Content to write
            file_path: Path to write to

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        pass

    def get_mime_type(self) -> str:
        """
        Get the MIME type for this renderer's output format.

        Returns:
            MIME type string
        """
        extension = self.get_file_extension()
        mime_types = {
            '.svg': 'image/svg+xml',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg'
        }
        return mime_types.get(extension, 'application/octet-stream')

    def supports_interactive_features(self) -> bool:
        """
        Check if this renderer supports interactive features.

        Returns:
            True if interactive features are supported, False otherwise
        """
        # Default implementation - can be overridden by subclasses
        return False

    def __str__(self) -> str:
        """String representation of the renderer."""
        return f"{self.__class__.__name__}(format={self.config.output_format.value})"

    def __repr__(self) -> str:
        """Detailed string representation of the renderer."""
        return (f"{self.__class__.__name__}("
                f"format={self.config.output_format.value}, "
                f"embed_mode={self.config.embed_mode}, "
                f"save_to_files={self.config.save_to_files})")
