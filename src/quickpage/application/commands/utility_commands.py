"""
Utility commands for the QuickPage application layer.

This module contains command objects for utility operations like testing
connections and clearing caches.
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass(frozen=True)
class TestConnectionCommand:
    """
    Command to test connection to the neuron data source.

    This command verifies that the application can connect to
    and retrieve data from the configured data source.
    """
    timeout_seconds: int = 30
    include_dataset_info: bool = True
    requested_at: datetime = None

    def __post_init__(self):
        if self.requested_at is None:
            object.__setattr__(self, 'requested_at', datetime.now())

    def validate(self) -> List[str]:
        """
        Validate the command parameters.

        Returns:
            List of validation errors, empty if valid
        """
        errors = []

        if self.timeout_seconds <= 0:
            errors.append("Timeout must be positive")

        return errors

    def is_valid(self) -> bool:
        """Check if the command is valid."""
        return len(self.validate()) == 0


@dataclass(frozen=True)
class ClearCacheCommand:
    """
    Command to clear cached data.

    This command handles cache management operations.
    """
    cache_pattern: Optional[str] = None  # Pattern to match keys, None = clear all
    older_than_hours: Optional[int] = None  # Clear entries older than specified hours
    requested_at: datetime = None

    def __post_init__(self):
        if self.requested_at is None:
            object.__setattr__(self, 'requested_at', datetime.now())

    def validate(self) -> List[str]:
        """
        Validate the command parameters.

        Returns:
            List of validation errors, empty if valid
        """
        errors = []

        if self.older_than_hours is not None and self.older_than_hours <= 0:
            errors.append("Hours must be positive if specified")

        return errors

    def is_valid(self) -> bool:
        """Check if the command is valid."""
        return len(self.validate()) == 0
