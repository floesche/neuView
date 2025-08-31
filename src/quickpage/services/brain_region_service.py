"""
Brain region data service for handling ROI abbreviations and full names.

This service manages the loading of brain region data from CSV files and provides
filtering functionality for converting ROI abbreviations to HTML abbr tags.
"""

from pathlib import Path
import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class BrainRegionService:
    """
    Service for managing brain region data and ROI abbreviation filtering.

    This service handles:
    - Loading brain region mappings from CSV files
    - Converting ROI abbreviations to HTML abbr tags with full names
    - Caching brain region data for performance
    """

    def __init__(self, config=None):
        """
        Initialize the brain region service.

        Args:
            config: Optional configuration object (for future extensibility)
        """
        self.config = config
        self.brain_regions: Dict[str, str] = {}
        self._loaded = False

    def load_brain_regions(self) -> Dict[str, str]:
        """
        Load brain regions data from CSV file.

        The CSV file should have format: abbreviation,full_name
        Handles commas in brain region names by splitting only on first comma.

        Returns:
            Dictionary mapping abbreviations to full names

        Raises:
            FileNotFoundError: If brain regions file cannot be found
            ValueError: If CSV format is invalid
        """
        if self._loaded:
            return self.brain_regions

        try:
            # Get the project root directory
            project_root = Path(__file__).parent.parent.parent.parent
            brain_regions_file = project_root / 'input' / 'brainregions.csv'

            if not brain_regions_file.exists():
                logger.warning(f"Brain regions file not found: {brain_regions_file}")
                self.brain_regions = {}
                self._loaded = True
                return self.brain_regions

            # Load CSV manually to handle commas in brain region names
            # Split only on the first comma to separate abbreviation from full name
            brain_regions_dict = {}

            with open(brain_regions_file, 'r', encoding='utf-8') as f:
                line_num = 0
                for line in f:
                    line_num += 1
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue

                    if ',' not in line:
                        logger.warning(f"Invalid format in brain regions file at line {line_num}: {line}")
                        continue

                    # Split on first comma only
                    parts = line.split(',', 1)
                    if len(parts) == 2:
                        abbr = parts[0].strip()
                        full_name = parts[1].strip()

                        if abbr and full_name:
                            brain_regions_dict[abbr] = full_name
                        else:
                            logger.warning(f"Empty abbreviation or name at line {line_num}: {line}")

            self.brain_regions = brain_regions_dict
            self._loaded = True

            logger.info(f"Loaded {len(self.brain_regions)} brain regions from {brain_regions_file}")
            return self.brain_regions

        except Exception as e:
            logger.error(f"Error loading brain regions data: {e}")
            self.brain_regions = {}
            self._loaded = True
            return self.brain_regions

    def get_brain_regions(self) -> Dict[str, str]:
        """
        Get the loaded brain regions dictionary.

        Loads brain regions if not already loaded.

        Returns:
            Dictionary mapping abbreviations to full names
        """
        if not self._loaded:
            self.load_brain_regions()
        return self.brain_regions.copy()

    def get_full_name(self, abbreviation: str) -> Optional[str]:
        """
        Get the full name for a brain region abbreviation.

        Args:
            abbreviation: The brain region abbreviation

        Returns:
            Full name if found, None otherwise
        """
        if not self._loaded:
            self.load_brain_regions()
        return self.brain_regions.get(abbreviation)

    def roi_abbr_filter(self, roi_name: str) -> str:
        """
        Convert ROI abbreviation to HTML abbr tag with full name in title.

        This method processes ROI names by:
        1. Stripping side indicators like (L) or (R)
        2. Looking up the full name in the brain regions data
        3. Returning an HTML abbr tag if found, otherwise the original name

        Args:
            roi_name: The ROI abbreviation (may include side indicators)

        Returns:
            HTML abbr tag if full name found, otherwise the original abbreviation

        Examples:
            >>> service.roi_abbr_filter("ME(R)")
            '<abbr title="medulla">ME(R)</abbr>'

            >>> service.roi_abbr_filter("UnknownROI")
            'UnknownROI'
        """
        if not roi_name or not isinstance(roi_name, str):
            return roi_name or ""

        # Ensure brain regions are loaded
        if not self._loaded:
            self.load_brain_regions()

        # Strip side indicators like (L) or (R) to get base abbreviation
        roi_abbr = re.sub(r'\([RL]\)', '', roi_name)
        roi_abbr = roi_abbr.strip()

        # Look up the full name
        full_name = self.brain_regions.get(roi_abbr)

        if full_name:
            # Escape HTML characters in full name for safe HTML attribute
            escaped_full_name = (full_name
                                .replace('&', '&amp;')
                                .replace('<', '&lt;')
                                .replace('>', '&gt;')
                                .replace('"', '&quot;')
                                .replace("'", '&#x27;'))

            return f'<abbr title="{escaped_full_name}">{roi_name}</abbr>'
        else:
            # Return the original abbreviation if not found
            logger.debug(f"Brain region abbreviation not found: {roi_name}")
            return roi_name

    def reload_brain_regions(self) -> Dict[str, str]:
        """
        Force reload of brain regions data from file.

        This method clears the cache and reloads the data, useful for
        testing or when the source file has been updated.

        Returns:
            Dictionary mapping abbreviations to full names
        """
        self._loaded = False
        self.brain_regions.clear()
        return self.load_brain_regions()

    def add_brain_region(self, abbreviation: str, full_name: str) -> None:
        """
        Add or update a brain region mapping.

        This method allows runtime addition of brain region mappings,
        useful for testing or dynamic configuration.

        Args:
            abbreviation: The brain region abbreviation
            full_name: The full name of the brain region
        """
        if not self._loaded:
            self.load_brain_regions()

        self.brain_regions[abbreviation] = full_name
        logger.debug(f"Added brain region mapping: {abbreviation} -> {full_name}")

    def __len__(self) -> int:
        """Return the number of loaded brain regions."""
        if not self._loaded:
            self.load_brain_regions()
        return len(self.brain_regions)

    def __contains__(self, abbreviation: str) -> bool:
        """Check if an abbreviation exists in the brain regions data."""
        if not self._loaded:
            self.load_brain_regions()
        return abbreviation in self.brain_regions
