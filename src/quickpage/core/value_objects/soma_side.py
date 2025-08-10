"""
SomaSide value object for the QuickPage domain.

This module contains the SomaSide value object which represents
the anatomical location of a neuron's soma (cell body).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SomaSide:
    """Represents the soma side of a neuron."""
    value: Optional[str]

    VALID_SIDES = {'L', 'R', 'M', 'left', 'right', 'middle', 'all', None}

    def __post_init__(self):
        if self.value is not None:
            normalized = self.value.strip() if isinstance(self.value, str) else str(self.value)
            if normalized not in self.VALID_SIDES:
                raise ValueError(f"Invalid soma side: {self.value}. Must be one of {self.VALID_SIDES}")

    def __str__(self) -> str:
        return self.value if self.value is not None else "unknown"

    def normalize(self) -> str:
        """Return normalized soma side representation."""
        if self.value is None:
            return "unknown"

        side_map = {
            'L': 'left',
            'R': 'right',
            'M': 'middle',
            'left': 'left',
            'right': 'right',
            'middle': 'middle',
            'all': 'all'
        }
        return side_map.get(self.value, self.value)

    def is_left(self) -> bool:
        return self.value in ('L', 'left')

    def is_right(self) -> bool:
        return self.value in ('R', 'right')

    def is_middle(self) -> bool:
        return self.value in ('M', 'middle')
