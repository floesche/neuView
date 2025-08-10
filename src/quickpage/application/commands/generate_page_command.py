"""
GeneratePageCommand for the QuickPage application layer.

This module contains the command object for generating HTML pages for neuron types.
It encapsulates all the information needed to generate a neuron type page including
filtering and output options.
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from ...core.value_objects import NeuronTypeName, SomaSide


@dataclass(frozen=True)
class GeneratePageCommand:
    """
    Command to generate an HTML page for a neuron type.

    This command encapsulates all the information needed to generate
    a neuron type page including filtering and output options.
    """
    neuron_type: NeuronTypeName
    soma_side: SomaSide
    output_directory: Optional[str] = None
    template_name: str = "default"
    include_connectivity: bool = True
    include_3d_view: bool = False
    min_synapse_count: int = 0
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

        if not str(self.neuron_type).strip():
            errors.append("Neuron type cannot be empty")

        if self.min_synapse_count < 0:
            errors.append("Minimum synapse count cannot be negative")

        if not self.template_name.strip():
            errors.append("Template name cannot be empty")

        return errors

    def is_valid(self) -> bool:
        """Check if the command is valid."""
        return len(self.validate()) == 0
