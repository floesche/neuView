"""
Bulk operation commands for the QuickPage application layer.

This module contains command objects for bulk operations like generating
multiple pages and discovering neuron types.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from ...core.value_objects import NeuronTypeName, SomaSide
from .generate_page_command import GeneratePageCommand


@dataclass(frozen=True)
class GenerateBulkPagesCommand:
    """
    Command to generate pages for multiple neuron types.

    This command handles bulk generation operations with shared settings.
    """
    neuron_types: List[NeuronTypeName]
    soma_side: SomaSide
    output_directory: Optional[str] = None
    template_name: str = "default"
    include_connectivity: bool = True
    include_3d_view: bool = False
    min_synapse_count: int = 0
    max_concurrent: int = 5
    skip_existing: bool = False
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

        if not self.neuron_types:
            errors.append("At least one neuron type must be specified")

        for neuron_type in self.neuron_types:
            if not str(neuron_type).strip():
                errors.append(f"Neuron type cannot be empty: {neuron_type}")

        if self.min_synapse_count < 0:
            errors.append("Minimum synapse count cannot be negative")

        if self.max_concurrent <= 0:
            errors.append("Max concurrent operations must be positive")

        if not self.template_name.strip():
            errors.append("Template name cannot be empty")

        return errors

    def is_valid(self) -> bool:
        """Check if the command is valid."""
        return len(self.validate()) == 0

    def to_individual_commands(self) -> List[GeneratePageCommand]:
        """
        Convert this bulk command into individual page generation commands.

        Returns:
            List of individual GeneratePageCommand instances
        """
        return [
            GeneratePageCommand(
                neuron_type=neuron_type,
                soma_side=self.soma_side,
                output_directory=self.output_directory,
                template_name=self.template_name,
                include_connectivity=self.include_connectivity,
                include_3d_view=self.include_3d_view,
                min_synapse_count=self.min_synapse_count,
                requested_at=self.requested_at
            )
            for neuron_type in self.neuron_types
        ]


@dataclass(frozen=True)
class DiscoverNeuronTypesCommand:
    """
    Command to discover available neuron types from the dataset.

    This command handles auto-discovery of neuron types with filtering options.
    """
    max_types: int = 10
    type_filter_pattern: Optional[str] = None
    exclude_types: List[str] = field(default_factory=list)
    include_only: List[str] = field(default_factory=list)
    randomize: bool = True
    min_neuron_count: int = 0
    requested_at: Optional[datetime] = None

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

        if self.max_types <= 0:
            errors.append("Max types must be positive")

        if self.min_neuron_count < 0:
            errors.append("Minimum neuron count cannot be negative")

        if self.include_only and self.exclude_types:
            # Check for conflicts between include_only and exclude_types
            conflicts = set(self.include_only) & set(self.exclude_types)
            if conflicts:
                errors.append(f"Types cannot be both included and excluded: {conflicts}")

        return errors

    def is_valid(self) -> bool:
        """Check if the command is valid."""
        return len(self.validate()) == 0
