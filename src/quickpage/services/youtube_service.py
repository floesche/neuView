"""
YouTube Integration Service

This service handles YouTube video mappings and matching for neuron types.
Provides functionality to load video mappings from CSV and find videos by neuron type.
"""

import re
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class YouTubeService:
    """Service for handling YouTube video integration and matching."""

    def __init__(self):
        """Initialize the YouTube service."""
        self._youtube_mapping = None

    def load_youtube_videos(self) -> Dict[str, str]:
        """
        Load YouTube video mappings from CSV file.

        Returns:
            Dictionary mapping neuron type names to YouTube video IDs
        """
        if self._youtube_mapping is not None:
            return self._youtube_mapping

        # Get input directory path relative to the project root
        project_root = Path(__file__).parent.parent.parent.parent
        youtube_csv_path = project_root / "input" / "youtube.csv"
        youtube_mapping = {}

        if not youtube_csv_path.exists():
            logger.warning(f"YouTube CSV file not found at {youtube_csv_path}")
            self._youtube_mapping = youtube_mapping
            return youtube_mapping

        try:
            with open(youtube_csv_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    # Split on first comma to get video_id and description
                    parts = line.split(",", 1)
                    if len(parts) != 2:
                        continue

                    video_id = parts[0].strip()
                    description = parts[1].strip()

                    # Store mapping with description as key
                    youtube_mapping[description] = video_id

            logger.info(f"Loaded {len(youtube_mapping)} YouTube video mappings")

        except Exception as e:
            logger.warning(f"Failed to load YouTube CSV: {e}")

        self._youtube_mapping = youtube_mapping
        return youtube_mapping

    def find_youtube_video(self, neuron_type: str) -> Optional[str]:
        """
        Find YouTube video ID for a neuron type by matching against descriptions.

        Args:
            neuron_type: Name of the neuron type (without soma side)

        Returns:
            YouTube video ID if found, None otherwise
        """
        # Skip empty or whitespace-only strings
        if not neuron_type or not neuron_type.strip():
            return None

        # Remove soma side suffixes (_L, _R, _M) from neuron type
        clean_neuron_type = re.sub(r"_[LRM]$", "", neuron_type)

        # Skip if cleaned neuron type is empty
        if not clean_neuron_type.strip():
            return None

        # Load YouTube mappings
        youtube_mapping = self.load_youtube_videos()

        # Try to find a match in the descriptions
        for description, video_id in youtube_mapping.items():
            # Look for the neuron type name in the description
            # Case-insensitive search for the clean neuron type name
            if clean_neuron_type.lower() in description.lower():
                logger.debug(f"Found YouTube video for {neuron_type}: {video_id}")
                return video_id

        logger.debug(f"No YouTube video found for {neuron_type}")
        return None

    def clear_cache(self):
        """Clear the cached YouTube mappings to force reload on next access."""
        self._youtube_mapping = None
