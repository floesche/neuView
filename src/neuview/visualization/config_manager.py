"""
Unified configuration manager for eyemap generation.

This module provides a centralized configuration management system that consolidates
all configuration objects used by the EyemapGenerator and related components.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any

from .constants import (
    DEFAULT_HEX_SIZE,
    DEFAULT_SPACING_FACTOR,
    DEFAULT_MARGIN,
    MIN_HEX_SIZE,
    MAX_HEX_SIZE,
    MIN_SPACING_FACTOR,
    MAX_SPACING_FACTOR,
    OUTPUT_FORMAT_SVG,
    SUPPORTED_OUTPUT_FORMATS,
    EYEMAPS_SUBDIRECTORY,
)
from .rendering.rendering_config import RenderingConfig

logger = logging.getLogger(__name__)


@dataclass
class EyemapConfiguration:
    """
    Unified configuration for eyemap generation.

    This class consolidates all configuration parameters needed for eyemap
    generation, validation, and rendering operations.
    """

    # Core visualization parameters
    hex_size: int = DEFAULT_HEX_SIZE
    spacing_factor: float = DEFAULT_SPACING_FACTOR
    margin: int = DEFAULT_MARGIN

    # Directory configuration
    output_dir: Optional[Path] = None
    eyemaps_dir: Optional[Path] = None
    template_dir: Optional[Path] = None

    # Operation modes
    embed_mode: bool = False
    save_to_files: bool = True

    # Output configuration
    output_format: str = OUTPUT_FORMAT_SVG

    # Performance settings
    enable_caching: bool = True
    cache_size: int = 100
    processing_timeout: int = 300
    max_concurrent_renders: int = 4

    # Validation settings
    strict_validation: bool = True

    # Debug and logging
    debug_mode: bool = False
    log_level: str = "INFO"

    # Advanced settings
    custom_settings: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Post-initialization validation and setup."""
        self._validate_configuration()
        self._setup_directories()
        self._setup_logging()

    def _validate_configuration(self):
        """Validate configuration parameters."""
        if not MIN_HEX_SIZE <= self.hex_size <= MAX_HEX_SIZE:
            raise ValueError(
                f"hex_size must be between {MIN_HEX_SIZE} and {MAX_HEX_SIZE}, "
                f"got {self.hex_size}"
            )

        if not MIN_SPACING_FACTOR <= self.spacing_factor <= MAX_SPACING_FACTOR:
            raise ValueError(
                f"spacing_factor must be between {MIN_SPACING_FACTOR} and "
                f"{MAX_SPACING_FACTOR}, got {self.spacing_factor}"
            )

        if self.output_format not in SUPPORTED_OUTPUT_FORMATS:
            raise ValueError(
                f"output_format must be one of {SUPPORTED_OUTPUT_FORMATS}, "
                f"got {self.output_format}"
            )

        if self.margin < 0:
            raise ValueError(f"margin must be non-negative, got {self.margin}")

        if self.cache_size < 0:
            raise ValueError(f"cache_size must be non-negative, got {self.cache_size}")

        if self.processing_timeout < 0:
            raise ValueError(
                f"processing_timeout must be non-negative, got {self.processing_timeout}"
            )

        if self.max_concurrent_renders < 1:
            raise ValueError(
                f"max_concurrent_renders must be at least 1, got {self.max_concurrent_renders}"
            )

    def _setup_directories(self):
        """Setup and validate directory paths."""
        if self.eyemaps_dir is None and self.output_dir is not None:
            self.eyemaps_dir = self.output_dir / EYEMAPS_SUBDIRECTORY

        # Convert string paths to Path objects
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)

        if isinstance(self.eyemaps_dir, str):
            self.eyemaps_dir = Path(self.eyemaps_dir)

        # Create directories if they don't exist and we're saving files
        if self.save_to_files:
            if self.output_dir and not self.output_dir.exists():
                self.output_dir.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created output directory: {self.output_dir}")

            if self.eyemaps_dir and not self.eyemaps_dir.exists():
                self.eyemaps_dir.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created eyemaps directory: {self.eyemaps_dir}")

    def _setup_logging(self):
        """Setup logging configuration."""
        if self.debug_mode and self.log_level == "INFO":
            self.log_level = "DEBUG"

        # Set logger level for the visualization module
        viz_logger = logging.getLogger("neuview.visualization")
        viz_logger.setLevel(getattr(logging, self.log_level.upper()))

    def copy(self, **kwargs) -> "EyemapConfiguration":
        """
        Create a copy of the configuration with optional parameter overrides.

        Args:
            **kwargs: Parameters to override in the copy

        Returns:
            New EyemapConfiguration instance with updated parameters
        """
        # Get current values
        current_values = {
            "hex_size": self.hex_size,
            "spacing_factor": self.spacing_factor,
            "margin": self.margin,
            "output_dir": self.output_dir,
            "eyemaps_dir": self.eyemaps_dir,
            "embed_mode": self.embed_mode,
            "save_to_files": self.save_to_files,
            "output_format": self.output_format,
            "enable_caching": self.enable_caching,
            "cache_size": self.cache_size,
            "processing_timeout": self.processing_timeout,
            "max_concurrent_renders": self.max_concurrent_renders,
            "strict_validation": self.strict_validation,
            "debug_mode": self.debug_mode,
            "log_level": self.log_level,
            "custom_settings": self.custom_settings.copy(),
        }

        # Apply overrides
        current_values.update(kwargs)

        return EyemapConfiguration(**current_values)

    def update(self, **kwargs) -> None:
        """
        Update configuration parameters in-place.

        Args:
            **kwargs: Parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown configuration parameter: {key}")

        # Re-validate after updates
        self._validate_configuration()
        self._setup_directories()
        self._setup_logging()

    def to_rendering_config(self) -> RenderingConfig:
        """
        Convert to RenderingConfig for rendering operations.

        Returns:
            RenderingConfig instance with equivalent settings
        """
        return RenderingConfig(
            hex_size=self.hex_size,
            spacing_factor=self.spacing_factor,
            output_dir=self.output_dir,
            eyemaps_dir=self.eyemaps_dir,
            margin=self.margin,
            save_to_files=self.save_to_files,
            embed_mode=self.embed_mode,
            template_dir=self.template_dir,
        )

    def get_coordinate_system_params(self) -> Dict[str, Any]:
        """
        Get parameters needed for coordinate system initialization.

        Returns:
            Dictionary of coordinate system parameters
        """
        return {
            "hex_size": self.hex_size,
            "spacing_factor": self.spacing_factor,
            "margin": self.margin,
        }

    def get_performance_settings(self) -> Dict[str, Any]:
        """
        Get performance-related settings.

        Returns:
            Dictionary of performance settings
        """
        return {
            "enable_caching": self.enable_caching,
            "cache_size": self.cache_size,
            "processing_timeout": self.processing_timeout,
            "max_concurrent_renders": self.max_concurrent_renders,
        }

    def get_output_settings(self) -> Dict[str, Any]:
        """
        Get output-related settings.

        Returns:
            Dictionary of output settings
        """
        return {
            "output_format": self.output_format,
            "save_to_files": self.save_to_files,
            "embed_mode": self.embed_mode,
            "output_dir": self.output_dir,
            "eyemaps_dir": self.eyemaps_dir,
        }

    def is_file_output_enabled(self) -> bool:
        """
        Check if file output is enabled and properly configured.

        Returns:
            True if file output is enabled and directories are set
        """
        return (
            self.save_to_files and not self.embed_mode and self.output_dir is not None
        )

    def __str__(self) -> str:
        """String representation of configuration."""
        return (
            f"EyemapConfiguration("
            f"hex_size={self.hex_size}, "
            f"spacing_factor={self.spacing_factor}, "
            f"output_format={self.output_format}, "
            f"save_to_files={self.save_to_files}, "
            f"embed_mode={self.embed_mode}"
            f")"
        )

    def __repr__(self) -> str:
        """Detailed representation of configuration."""
        return (
            f"EyemapConfiguration(\n"
            f"  hex_size={self.hex_size},\n"
            f"  spacing_factor={self.spacing_factor},\n"
            f"  margin={self.margin},\n"
            f"  output_dir={self.output_dir},\n"
            f"  eyemaps_dir={self.eyemaps_dir},\n"
            f"  embed_mode={self.embed_mode},\n"
            f"  save_to_files={self.save_to_files},\n"
            f"  output_format={self.output_format},\n"
            f"  enable_caching={self.enable_caching},\n"
            f"  debug_mode={self.debug_mode}\n"
            f")"
        )


class ConfigurationManager:
    """
    Manager for creating and maintaining eyemap configurations.

    This class provides factory methods and utilities for creating
    and managing EyemapConfiguration instances.
    """

    _default_config: Optional[EyemapConfiguration] = None

    @classmethod
    def create_default(cls) -> EyemapConfiguration:
        """
        Create a default configuration instance.

        Returns:
            EyemapConfiguration with default settings
        """
        if cls._default_config is None:
            cls._default_config = EyemapConfiguration()

        return cls._default_config.copy()

    @classmethod
    def create_for_generation(
        cls,
        hex_size: int = DEFAULT_HEX_SIZE,
        spacing_factor: float = DEFAULT_SPACING_FACTOR,
        output_dir: Optional[Path] = None,
        eyemaps_dir: Optional[Path] = None,
        template_dir: Optional[Path] = None,
        save_to_files: bool = True,
        output_format: str = OUTPUT_FORMAT_SVG,
        **kwargs,
    ) -> EyemapConfiguration:
        """
        Create configuration optimized for eyemap generation.

        Args:
            hex_size: Size of individual hexagons
            spacing_factor: Spacing between hexagons
            output_dir: Directory to save SVG files
            eyemaps_dir: Directory to save eyemap images
            template_dir: Directory containing templates
            save_to_files: Whether to save files to disk
            output_format: Output format (svg or png)
            **kwargs: Additional configuration parameters

        Returns:
            EyemapConfiguration instance optimized for generation
        """
        config_params = {
            "hex_size": hex_size,
            "spacing_factor": spacing_factor,
            "output_dir": output_dir,
            "eyemaps_dir": eyemaps_dir,
            "template_dir": template_dir,
            "save_to_files": save_to_files,
            "output_format": output_format,
            "embed_mode": not save_to_files,
            **kwargs,
        }

        return EyemapConfiguration(**config_params)

    @classmethod
    def create_for_embedding(
        cls,
        hex_size: int = DEFAULT_HEX_SIZE,
        spacing_factor: float = DEFAULT_SPACING_FACTOR,
        template_dir: Optional[Path] = None,
        output_format: str = OUTPUT_FORMAT_SVG,
        **kwargs,
    ) -> EyemapConfiguration:
        """
        Create configuration optimized for embedding (no file output).

        Args:
            hex_size: Size of individual hexagons
            spacing_factor: Spacing between hexagons
            template_dir: Directory containing templates
            output_format: Output format (svg or png)
            **kwargs: Additional configuration parameters

        Returns:
            EyemapConfiguration instance optimized for embedding
        """
        config_params = {
            "hex_size": hex_size,
            "spacing_factor": spacing_factor,
            "template_dir": template_dir,
            "output_format": output_format,
            "embed_mode": True,
            "save_to_files": False,
            "output_dir": None,
            "eyemaps_dir": None,
            **kwargs,
        }

        return EyemapConfiguration(**config_params)

    @classmethod
    def create_debug_config(
        cls, base_config: Optional[EyemapConfiguration] = None, **kwargs
    ) -> EyemapConfiguration:
        """
        Create configuration with debug settings enabled.

        Args:
            base_config: Base configuration to extend (optional)
            **kwargs: Additional configuration parameters

        Returns:
            EyemapConfiguration instance with debug settings
        """
        if base_config is None:
            base_config = cls.create_default()

        debug_params = {
            "debug_mode": True,
            "log_level": "DEBUG",
            "strict_validation": True,
            **kwargs,
        }

        return base_config.copy(**debug_params)

    @staticmethod
    def validate_config(config: EyemapConfiguration) -> bool:
        """
        Validate a configuration instance.

        Args:
            config: Configuration to validate

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        try:
            # Validation is performed in __post_init__, so we just need to
            # trigger it by creating a copy
            config.copy()
            return True
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise

    @staticmethod
    def merge_configs(
        base_config: EyemapConfiguration, override_config: EyemapConfiguration
    ) -> EyemapConfiguration:
        """
        Merge two configurations, with override_config taking precedence.

        Args:
            base_config: Base configuration
            override_config: Configuration with override values

        Returns:
            New merged configuration
        """
        # Get all non-default values from override config
        override_values = {}
        default_config = EyemapConfiguration()

        for field_name in [
            "hex_size",
            "spacing_factor",
            "margin",
            "output_dir",
            "eyemaps_dir",
            "embed_mode",
            "save_to_files",
            "output_format",
            "enable_caching",
            "cache_size",
            "processing_timeout",
            "max_concurrent_renders",
            "strict_validation",
            "debug_mode",
            "log_level",
        ]:
            override_value = getattr(override_config, field_name)
            default_value = getattr(default_config, field_name)

            if override_value != default_value:
                override_values[field_name] = override_value

        # Merge custom settings
        merged_custom = base_config.custom_settings.copy()
        merged_custom.update(override_config.custom_settings)
        override_values["custom_settings"] = merged_custom

        return base_config.copy(**override_values)
