"""
Formatters module containing utility functions for formatting numbers, percentages, and synapse counts.

This module extracts formatting functionality from the PageGenerator class
to improve code organization and reusability.
"""

from typing import Any
import pandas as pd
import math


class NumberFormatter:
    """Utility class for formatting numbers."""

    @staticmethod
    def format_number(value: Any) -> str:
        """Format numbers with commas."""
        if isinstance(value, (int, float)):
            return f"{value:,.2f}"
        return str(value)


class PercentageFormatter:
    """Utility class for formatting percentages."""

    @staticmethod
    def format_percentage(value: Any, precision: int = 1) -> str:
        """Format numbers as percentages with specified decimal places."""
        if isinstance(value, (int, float)):
            return f"{value:.{precision}f}%"
        return str(value)

    @staticmethod
    def format_percentage_5(value: Any) -> str:
        """Format numbers as percentages with 5 decimal places (for backward compatibility)."""
        return PercentageFormatter.format_percentage(value, precision=5)


class SynapseFormatter:
    """Utility class for formatting synapse and connection counts."""

    @staticmethod
    def _format_count_with_tooltip(value: Any, precision: int = None) -> str:
        """
        Common formatting logic for counts with tooltips.

        Args:
            value: Value to format
            precision: Decimal precision for tooltip (None for full precision)

        Returns:
            Formatted string with tooltip if needed
        """
        if isinstance(value, (int, float)):
            float_value = float(value)

            if float_value.is_integer():
                # Integer values don't need tooltips
                return f"{int(float_value):,}"
            else:
                # Float values get tooltips with full or specified precision
                rounded_display = f"{float_value:,.1f}"

                if precision is not None:
                    full_precision = f"{float_value:.{precision}f}"
                    abbr = "…" if len(full_precision) < len(str(float_value)) else ""
                    return (
                        f'<span title="{full_precision}{abbr}">{rounded_display}</span>'
                    )
                else:
                    full_precision = str(float_value)
                    abbr = "…" if len(full_precision) < len(str(float_value)) else ""
                    return (
                        f'<span title="{full_precision}{abbr}">{rounded_display}</span>'
                    )

        return str(value)

    @staticmethod
    def format_synapse_count(value: Any) -> str:
        """Format synapse counts with 1 decimal place display and full precision in tooltip."""
        return SynapseFormatter._format_count_with_tooltip(value)

    @staticmethod
    def format_conn_count(value: Any) -> str:
        """Format connection counts with tooltip for full precision."""
        return SynapseFormatter._format_count_with_tooltip(value, precision=5)


class NeurotransmitterFormatter:
    """Utility class for formatting neurotransmitter names."""

    # Mapping of common neurotransmitter names to abbreviations
    ABBREVIATIONS = {
        "acetylcholine": "ACh",
        "dopamine": "DA",
        "serotonin": "5-HT",
        "octopamine": "OA",
        "gaba": "GABA",
        "glutamate": "Glu",
        "histamine": "HA",
        "tyramine": "TA",
        "choline": "ACh",  # Sometimes appears as just 'choline'
        "norepinephrine": "NE",
        "epinephrine": "Epi",
        "glycine": "Gly",
        "aspartate": "Asp",
        "unknown": "Unk",
        "unclear": "unc",
        "none": "-",
        "": "-",
        "nan": "Unk",
    }

    @classmethod
    def abbreviate_neurotransmitter(cls, neurotransmitter: str) -> str:
        """Convert neurotransmitter names to abbreviated forms with HTML abbr tag."""
        if not neurotransmitter or pd.isna(neurotransmitter):
            return '<abbr title="Unknown">Unk</abbr>'

        # Convert to lowercase for case-insensitive matching
        original_nt = str(neurotransmitter).strip()
        nt_lower = original_nt.lower()

        # Get abbreviated form
        abbreviated = cls.ABBREVIATIONS.get(nt_lower)

        if abbreviated:
            # If we found an abbreviation, wrap it in abbr tag with original name as title
            return f'<abbr title="{original_nt}">{abbreviated}</abbr>'
        else:
            # For unknown neurotransmitters, truncate if too long but keep original in title
            if len(original_nt) > 5:
                truncated = original_nt[:4] + "..."
                return f'<abbr title="{original_nt}">{truncated}</abbr>'
            else:
                # Short enough to display as-is, but still wrap in abbr for consistency
                return f'<abbr title="{original_nt}">{original_nt}</abbr>'


class MathematicalFormatter:
    """Utility class for mathematical calculations and formatting."""

    @staticmethod
    def log_ratio(a: Any, b: Any) -> float:
        """
        Calculate the log ratio of two numbers.

        Args:
            a: First number (numerator)
            b: Second number (denominator)

        Returns:
            Log base 2 ratio of a/b, with special handling for edge cases:
            - If both are 0: returns 0.0
            - If a is 0: returns -inf
            - If b is 0: returns inf
            - Otherwise: returns log2(a/b)
        """
        # Handle None values
        if a is None:
            a = 0
        if b is None:
            b = 0

        # Convert to numeric values if possible
        try:
            a = float(a) if a != 0 else 0
            b = float(b) if b != 0 else 0
        except (ValueError, TypeError):
            # If conversion fails, treat as 0
            a = 0
            b = 0

        # Handle edge cases
        if a == 0 and b == 0:
            return 0.0
        elif a == 0:
            return -math.inf
        elif b == 0:
            return math.inf
        else:
            return math.log2(a / b)
