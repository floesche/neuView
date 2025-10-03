"""
Composite Resource Strategy Implementation

This module provides a composite resource strategy that can delegate to
different resource strategies based on resource path patterns or types.
"""

import re
from typing import Any, Dict, Optional, List, Tuple
from pathlib import Path
import logging

from ..base import ResourceStrategy
from ..exceptions import ResourceLoadError

logger = logging.getLogger(__name__)


class CompositeResourceStrategy(ResourceStrategy):
    """
    Composite resource strategy that delegates to different strategies.

    This strategy allows different resource strategies to be used for
    different types of resources based on path patterns, file extensions,
    or other criteria. For example, local files can use FileSystemResourceStrategy
    while remote URLs use RemoteResourceStrategy.
    """

    def __init__(self, default_strategy: Optional[ResourceStrategy] = None):
        """
        Initialize composite resource strategy.

        Args:
            default_strategy: Default strategy to use when no specific strategy matches
        """
        self.strategies: List[Tuple[re.Pattern, ResourceStrategy]] = []
        self.default_strategy = default_strategy

    def register_strategy(self, pattern: str, strategy: ResourceStrategy) -> None:
        """
        Register a strategy for resources matching a pattern.

        Args:
            pattern: Regular expression pattern to match resource paths
            strategy: Resource strategy to use for matching paths
        """
        compiled_pattern = re.compile(pattern)
        self.strategies.append((compiled_pattern, strategy))
        logger.debug(
            f"Registered strategy {strategy.__class__.__name__} for pattern: {pattern}"
        )

    def set_default_strategy(self, strategy: ResourceStrategy) -> None:
        """Set the default strategy for unmatched resources."""
        self.default_strategy = strategy

    def _get_strategy_for_resource(self, resource_path: str) -> ResourceStrategy:
        """Get the appropriate strategy for a resource path."""
        # Check registered patterns in order
        for pattern, strategy in self.strategies:
            if pattern.match(resource_path):
                return strategy

        # Use default strategy if available
        if self.default_strategy:
            return self.default_strategy

        # No strategy available
        raise ResourceLoadError(f"No strategy available for resource: {resource_path}")

    def load_resource(self, resource_path: str) -> bytes:
        """
        Load a resource using the appropriate strategy.

        Args:
            resource_path: Path to the resource file

        Returns:
            Resource content as bytes

        Raises:
            ResourceNotFoundError: If resource doesn't exist
            ResourceLoadError: If resource can't be loaded
        """
        strategy = self._get_strategy_for_resource(resource_path)
        return strategy.load_resource(resource_path)

    def resource_exists(self, resource_path: str) -> bool:
        """
        Check if a resource exists using the appropriate strategy.

        Args:
            resource_path: Path to the resource file

        Returns:
            True if resource exists, False otherwise
        """
        try:
            strategy = self._get_strategy_for_resource(resource_path)
            return strategy.resource_exists(resource_path)
        except ResourceLoadError:
            return False

    def get_resource_metadata(self, resource_path: str) -> Dict[str, Any]:
        """
        Get metadata for a resource using the appropriate strategy.

        Args:
            resource_path: Path to the resource file

        Returns:
            Dictionary containing resource metadata
        """
        strategy = self._get_strategy_for_resource(resource_path)
        return strategy.get_resource_metadata(resource_path)

    def list_resources(self, resource_dir: Path, pattern: str = "*") -> List[str]:
        """
        List resources from all strategies.

        Args:
            resource_dir: Directory to search for resources
            pattern: Glob pattern to match (default: "*")

        Returns:
            List of resource paths from all strategies
        """
        all_resources = []

        # Get resources from all registered strategies
        for _, strategy in self.strategies:
            try:
                resources = strategy.list_resources(resource_dir, pattern)
                all_resources.extend(resources)
            except Exception as e:
                logger.warning(
                    f"Error listing resources from {strategy.__class__.__name__}: {e}"
                )

        # Get resources from default strategy
        if self.default_strategy:
            try:
                resources = self.default_strategy.list_resources(resource_dir, pattern)
                all_resources.extend(resources)
            except Exception as e:
                logger.warning(f"Error listing resources from default strategy: {e}")

        # Remove duplicates and sort
        return sorted(list(set(all_resources)))

    def copy_resource(self, source_path: str, dest_path: str) -> bool:
        """
        Copy a resource using the appropriate strategy.

        Args:
            source_path: Source resource path
            dest_path: Destination path

        Returns:
            True if copy was successful, False otherwise
        """
        try:
            strategy = self._get_strategy_for_resource(source_path)
            return strategy.copy_resource(source_path, dest_path)
        except Exception as e:
            logger.error(f"Failed to copy resource {source_path}: {e}")
            return False
