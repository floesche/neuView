"""
PageGenerator Builder - Phase 1 Refactoring

This builder provides a fluent interface for constructing PageGenerator instances
with different configurations, making it easier to create PageGenerators for
testing, different environments, or specific use cases.
"""

import logging
from pathlib import Path
from typing import Optional

from ..config import Config

logger = logging.getLogger(__name__)


class PageGeneratorBuilder:
    """Builder pattern for PageGenerator configuration and creation."""

    def __init__(self):
        """Initialize builder with default values."""
        self._config: Optional[Config] = None
        self._output_dir: Optional[str] = None
        self._queue_service = None
        self._cache_manager = None
        self._use_factory: bool = True
        self._validate_config: bool = True

    def with_config(self, config: Config):
        """
        Set the configuration object.

        Args:
            config: Configuration object with template and output settings

        Returns:
            Self for method chaining
        """
        self._config = config
        return self

    def with_output_directory(self, output_dir: str):
        """
        Set the output directory path.

        Args:
            output_dir: Directory path for generated HTML files

        Returns:
            Self for method chaining
        """
        self._output_dir = output_dir
        return self

    def with_queue_service(self, queue_service):
        """
        Set the queue service.

        Args:
            queue_service: QueueService for checking queued neuron types

        Returns:
            Self for method chaining
        """
        self._queue_service = queue_service
        return self

    def with_cache_manager(self, cache_manager):
        """
        Set the cache manager.

        Args:
            cache_manager: Cache manager for accessing cached neuron data

        Returns:
            Self for method chaining
        """
        self._cache_manager = cache_manager
        return self

    def use_legacy_initialization(self, use_legacy: bool = True):
        """
        Control whether to use legacy initialization or the new factory.

        Args:
            use_legacy: If True, use legacy __init__; if False, use factory

        Returns:
            Self for method chaining
        """
        self._use_factory = not use_legacy
        return self

    def skip_config_validation(self, skip: bool = True):
        """
        Control whether to validate configuration before building.

        Args:
            skip: If True, skip validation; if False, validate

        Returns:
            Self for method chaining
        """
        self._validate_config = not skip
        return self

    def build(self):
        """
        Build and return configured PageGenerator instance.

        Returns:
            Configured PageGenerator instance

        Raises:
            ValueError: If required configuration is missing
            RuntimeError: If configuration validation fails
        """
        self._validate_required_parameters()

        if self._validate_config:
            self._validate_configuration()

        if self._use_factory:
            return self._build_with_factory()
        else:
            return self._build_legacy()

    def build_for_testing(self):
        """
        Build a lightweight PageGenerator suitable for testing.

        Returns:
            PageGenerator instance with minimal dependencies
        """
        self._validate_required_parameters()

        # Use legacy initialization with minimal setup for testing
        from ..page_generator import PageGenerator

        logger.info("Building PageGenerator for testing")
        return PageGenerator(
            config=self._config,
            output_dir=self._output_dir,
            queue_service=None,  # No queue service for testing
            cache_manager=None,  # No cache manager for testing
            services=None  # Use legacy initialization
        )

    def _validate_required_parameters(self):
        """Validate that required parameters are set."""
        if self._config is None:
            raise ValueError("Configuration is required. Use with_config() to set it.")

        if self._output_dir is None:
            raise ValueError("Output directory is required. Use with_output_directory() to set it.")

    def _validate_configuration(self):
        """Validate that the configuration is suitable for PageGenerator creation."""
        try:
            if not hasattr(self._config, 'output'):
                raise RuntimeError("Configuration missing 'output' section")

            if not hasattr(self._config.output, 'template_dir'):
                raise RuntimeError("Configuration missing 'output.template_dir'")

            if not hasattr(self._config.output, 'directory'):
                raise RuntimeError("Configuration missing 'output.directory'")

            # Check that template directory exists
            template_dir = Path(self._config.output.template_dir)
            if not template_dir.exists():
                logger.warning(f"Template directory does not exist: {template_dir}")

            # Check that output directory is writable
            output_dir = Path(self._output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            if not output_dir.is_dir():
                raise RuntimeError(f"Cannot create output directory: {output_dir}")

        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise RuntimeError(f"Invalid configuration: {e}")

    def _build_with_factory(self):
        """Build PageGenerator using the service factory."""
        logger.info("Building PageGenerator with service factory")

        from ..page_generator import PageGenerator
        return PageGenerator.create_with_factory(
            config=self._config,
            output_dir=self._output_dir,
            queue_service=self._queue_service,
            cache_manager=self._cache_manager
        )

    def _build_legacy(self):
        """Build PageGenerator using legacy initialization."""
        logger.info("Building PageGenerator with legacy initialization")

        from ..page_generator import PageGenerator
        return PageGenerator(
            config=self._config,
            output_dir=self._output_dir,
            queue_service=self._queue_service,
            cache_manager=self._cache_manager,
            services=None  # Trigger legacy initialization
        )

    @classmethod
    def create(cls):
        """
        Create a new builder instance.

        Returns:
            New PageGeneratorBuilder instance
        """
        return cls()

    @classmethod
    def default_config(cls, config: Config, output_dir: str):
        """
        Create a builder with default configuration.

        Args:
            config: Configuration object
            output_dir: Output directory path

        Returns:
            Configured builder ready to build
        """
        return cls().with_config(config).with_output_directory(output_dir)

    @classmethod
    def for_testing(cls, config: Config, output_dir: str):
        """
        Create a builder configured for testing.

        Args:
            config: Configuration object
            output_dir: Output directory path

        Returns:
            Builder configured for testing
        """
        return (cls()
                .with_config(config)
                .with_output_directory(output_dir)
                .use_legacy_initialization(True)
                .skip_config_validation(True))
