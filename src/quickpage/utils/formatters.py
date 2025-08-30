"""
Formatters module containing utility functions for formatting numbers, percentages, and synapse counts.

This module extracts formatting functionality from the PageGenerator class
to improve code organization and reusability.
"""

from typing import Any
import pandas as pd


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
    def format_percentage(value: Any) -> str:
        """Format numbers as percentages."""
        if isinstance(value, (int, float)):
            return f"{value:.1f}%"
        return str(value)

    @staticmethod
    def format_percentage_5(value: Any) -> str:
        """Format numbers as percentages with 5 decimal places and ellipsis if truncated."""
        if isinstance(value, (int, float)):
            prec_val = f"{value:.5f}"
            abbr = ""
            if len(prec_val) < len(str(value)):
                abbr = "…"
            return f"{value:.5f}{abbr}%"
        return str(value)


class SynapseFormatter:
    """Utility class for formatting synapse and connection counts."""

    @staticmethod
    def format_synapse_count(value: Any) -> str:
        """Format synapse counts with 1 decimal place display and full precision in tooltip."""
        if isinstance(value, (int, float)):
            # Convert to float to handle int and float inputs
            float_value = float(value)
            # Round to 1 decimal place for display
            # Full precision for tooltip (remove trailing zeros if int)
            rtn = ""
            if float_value.is_integer():
                rounded_display = f"{int(float_value):,}"
                full_precision = f"{int(float_value):,}"
                rtn = f"{rounded_display}"
            else:
                abbr = ""
                rounded_display = f"{float_value:,.1f}"
                full_precision = str(float_value)
                if len(full_precision) < len(str(float_value)):
                    abbr = "…"
                rtn = f'<span title="{full_precision}">{rounded_display}</span>'
            # Return abbr tag with full precision as title and rounded as display
            return rtn
        return str(value)

    @staticmethod
    def format_conn_count(value: Any) -> str:
        """Format connection counts with tooltip for full precision."""
        if isinstance(value, (int, float)):
            # Convert to float to handle int and float inputs
            float_value = float(value)
            # Full precision for tooltip (remove trailing zeros if int)
            rtn = ""
            if float_value.is_integer():
                rounded_display = f"{int(float_value):,}"
                rtn = f"{rounded_display}"
            else:
                abbr = ""
                rounded_display = f"{float_value:,.1f}"
                full_precision = f"{float_value:.5f}"
                if len(full_precision) < len(str(float_value)):
                    abbr = "…"
                rtn = f'<span title="{full_precision}{abbr}">{rounded_display}</span>'
            return rtn
        return str(value)


class NeurotransmitterFormatter:
    """Utility class for formatting neurotransmitter names."""

    # Mapping of common neurotransmitter names to abbreviations
    ABBREVIATIONS = {
        'acetylcholine': 'ACh',
        'dopamine': 'DA',
        'serotonin': '5-HT',
        'octopamine': 'OA',
        'gaba': 'GABA',
        'glutamate': 'Glu',
        'histamine': 'HA',
        'tyramine': 'TA',
        'choline': 'ACh',  # Sometimes appears as just 'choline'
        'norepinephrine': 'NE',
        'epinephrine': 'Epi',
        'glycine': 'Gly',
        'aspartate': 'Asp',
        'unknown': 'Unk',
        'unclear': 'unc',
        'none': '-',
        '': '-',
        'nan': 'Unk'
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
