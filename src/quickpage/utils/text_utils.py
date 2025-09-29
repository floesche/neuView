"""
Text utilities module containing utility functions for text processing and manipulation.

This module extracts text-related functionality from the PageGenerator class
to improve code organization and reusability.
"""

import re
import urllib.parse
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class TextUtils:
    """Utility class for text-related operations."""

    @staticmethod
    def truncate_neuron_name(name: str, max_length: int = 10) -> str:
        """
        Truncate neuron type name for display on index page.

        If name is longer than max_length characters, truncate to (max_length-1) characters + "…"
        and wrap in an <abbr> tag with the full name as title.

        Args:
            name: The neuron type name to truncate
            max_length: Maximum length before truncation (default: 13)

        Returns:
            HTML string with truncated name or <abbr> tag
        """
        if not name or len(name) <= max_length:
            return name

        # Truncate to (max_length-1) characters and add ellipsis
        truncated = name[: max_length - 1] + "…"

        # Return as abbr tag with full name in title
        return truncated

    @staticmethod
    def expand_brackets(expandable: str) -> str:
        """
        Expand bracketed expressions in text.

        Example: "text(a,b)suffix" becomes "texta suffix, textb suffix"

        Args:
            expandable: String containing bracketed expressions

        Returns:
            Expanded string with comma-separated alternatives
        """
        # Pattern: text before brackets, inside bracket, text immediately after
        pattern = re.compile(r"\(([^)]*)\)(\w*)")

        # Function to expand each bracketed section
        def replacer(match):
            inside, suffix = match.groups()
            parts = [part.strip() + suffix for part in inside.split(",")]
            return ", ".join(parts)  # join with commas

        # Replace all bracket groups in the string
        return pattern.sub(replacer, expandable)

    @staticmethod
    def process_synonyms(
        synonyms_string: str, citations: Dict[str, tuple]
    ) -> Dict[str, list]:
        """
        Process synonyms string according to requirements:
        - Split by semicolons and commas
        - Ignore items starting with "fru-"
        - For items with colons, extract synonym name and reference information
        - Return structured data for flexible template rendering

        Args:
            synonyms_string: Raw synonyms string from database
            citations: Dictionary mapping citation keys to (url, title) tuples

        Returns:
            Dict with synonym names as keys and reference info as values:
            {
                'synonym_name': [
                    {'ref': 'reference', 'url': 'url', 'title': 'title'},
                    ...
                ],
                ...
            }
        """
        if not synonyms_string:
            return {}

        # Split by semicolons
        items = [item.strip() for item in synonyms_string.split(";") if item.strip()]

        processed_synonyms = {}

        for item in items:
            # Handle items with colons
            if ":" in item:
                before_colon, after_colon = item.split(":", 1)
                references = []
                if "," in before_colon:
                    references.extend(
                        [
                            reference.strip()
                            for reference in before_colon.split(",")
                            if reference.strip()
                        ]
                    )
                else:
                    references = [before_colon.strip()]

                syn_name = after_colon.strip()

                # Process references
                ref_info = []
                for ref in references:
                    if ref in citations:
                        url, title = citations[ref]
                        ref_info.append(
                            {"ref": ref, "url": url, "title": title if title else ""}
                        )
                    else:
                        logger.warning(f"Citation '{ref}' not found in citations.csv")
                        ref_info.append({"ref": ref, "url": "#", "title": ""})

                processed_synonyms[syn_name] = ref_info
            else:
                # Handle items without colons, split by commas and filter out fru-M
                alit = [
                    lit.strip()
                    for lit in item.split(",")
                    if lit.strip() and not lit.strip().startswith("fru-")
                ]
                for synonym in alit:
                    processed_synonyms[synonym] = []  # No references for these

        return processed_synonyms

    @staticmethod
    def process_flywire_types(
        flywire_type_string: str, neuron_type: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Process flywireType string according to requirements:
        - Split by commas
        - Track which types are different from neuron_type for linking
        - Return structured data for flexible template rendering

        Args:
            flywire_type_string: Raw flywireType string from database
            neuron_type: Current neuron type name for comparison

        Returns:
            Dict with flywire type info:
            {
                'flywire_type_name': {
                    'url': 'flywire_url',
                    'is_different': bool  # True if different from neuron_type
                },
                ...
            }
        """
        if not flywire_type_string or not isinstance(flywire_type_string, str):
            return {}

        try:
            # Split by commas and clean up
            flywire_type_string = TextUtils.expand_brackets(flywire_type_string)
            items = [
                item.strip() for item in flywire_type_string.split(",") if item.strip()
            ]

            if not items:
                return {}

            processed_types = {}
            for item in items:
                # URL encode the flywire type for the search query
                encoded_type = urllib.parse.quote_plus(item)
                flywire_url = f"https://codex.flywire.ai/app/search?dataset=fafb&filter_string=cell_type%3D%3D{encoded_type}"

                # Check if flywire type is different from neuron_type (case-insensitive comparison)
                is_different = item.lower() != neuron_type.lower()

                processed_types[item] = {
                    "url": flywire_url,
                    "is_different": is_different,
                }

                if is_different:
                    logger.debug(
                        f"Created FlyWire link for '{item}' (different from neuron type '{neuron_type}')"
                    )
                else:
                    logger.debug(
                        f"No FlyWire link for '{item}' (same as neuron type '{neuron_type}')"
                    )

            logger.info(
                f"Processed {len(items)} FlyWire type(s) for neuron type '{neuron_type}'"
            )
            return processed_types

        except Exception as e:
            logger.warning(
                f"Error processing FlyWire types '{flywire_type_string}' for neuron type '{neuron_type}': {e}"
            )
            return {}

    @staticmethod
    def clean_roi_name(roi_name: str) -> str:
        """
        Clean ROI name by removing parentheses and underscores for comparison.

        Args:
            roi_name: ROI name to clean

        Returns:
            Cleaned ROI name
        """
        if not roi_name:
            return ""
        return (
            roi_name.replace("(L)", "")
            .replace("(R)", "")
            .replace("_L", "")
            .replace("_R", "")
        )

    @staticmethod
    def normalize_name_for_filename(name: str) -> str:
        """
        Normalize a name for use in filenames by replacing problematic characters.

        Args:
            name: Name to normalize

        Returns:
            Filename-safe name
        """
        if not name:
            return ""
        return (
            name.replace("/", "_")
            .replace(" ", "_")
            .replace("\\", "_")
            .replace(":", "_")
        )

    @staticmethod
    def extract_region_from_roi(roi_name: str) -> str:
        """
        Extract region name from ROI name.

        Args:
            roi_name: Full ROI name

        Returns:
            Region name without side indicators
        """
        # Remove common side indicators
        cleaned = TextUtils.clean_roi_name(roi_name)

        # Handle layer patterns like ME_L_layer_1 -> ME
        layer_pattern = r"^(ME|LO|LOP)_[LR]_layer_\d+$"
        match = re.match(layer_pattern, roi_name)
        if match:
            return match.group(1)

        return cleaned
