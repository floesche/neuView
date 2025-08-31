"""
File Naming Service

Handles file naming logic for generated HTML files, images, and other assets.
Provides consistent naming conventions across the application.
"""

import re
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from .file_service import FileService

logger = logging.getLogger(__name__)


class FileNamingService:
    """Service for generating consistent file names across the application."""

    def __init__(self, config):
        """Initialize the file naming service.

        Args:
            config: Configuration object
        """
        self.config = config

    def generate_neuron_type_filename(self, neuron_type: str, soma_side: str) -> str:
        """
        Generate HTML filename for a neuron type page.

        Args:
            neuron_type: Name of the neuron type
            soma_side: Soma side identifier ('L', 'R', or 'combined')

        Returns:
            HTML filename string
        """
        try:
            # Clean the neuron type name for use in filenames
            clean_type = self._clean_name_for_filename(neuron_type)

            # Determine soma side suffix
            if soma_side and soma_side.lower() in ['l', 'r']:
                soma_side_suffix = soma_side.upper()
            elif soma_side and soma_side.lower() == 'combined':
                soma_side_suffix = 'combined'
            else:
                soma_side_suffix = 'all'

            return f"{clean_type}_{soma_side_suffix}.html"

        except Exception as e:
            logger.error(f"Error generating filename for {neuron_type}: {e}")
            # Fallback to basic naming using consistent format
            return FileService.generate_filename(neuron_type, soma_side)

    def generate_visualization_filename(self, neuron_type: str, soma_side: str,
                                      region: str, viz_type: str,
                                      file_extension: str = 'svg') -> str:
        """
        Generate filename for visualization files (hexagon grids, etc.).

        Args:
            neuron_type: Name of the neuron type
            soma_side: Soma side identifier
            region: Brain region (ME, LO, LOP, etc.)
            viz_type: Type of visualization (density, count, etc.)
            file_extension: File extension without the dot

        Returns:
            Visualization filename string
        """
        try:
            clean_type = self._clean_name_for_filename(neuron_type)
            clean_region = self._clean_name_for_filename(region)
            clean_viz_type = self._clean_name_for_filename(viz_type)

            # Build filename components
            components = [clean_type, soma_side, clean_region, clean_viz_type]
            # Remove any empty components
            components = [c for c in components if c]

            filename = '_'.join(components)
            return f"{filename}.{file_extension}"

        except Exception as e:
            logger.error(f"Error generating visualization filename: {e}")
            return f"{neuron_type}_{region}_{viz_type}.{file_extension}"

    def generate_data_filename(self, neuron_type: str, data_type: str,
                              file_extension: str = 'json') -> str:
        """
        Generate filename for data files (JSON, CSV, etc.).

        Args:
            neuron_type: Name of the neuron type
            data_type: Type of data (connectivity, roi_summary, etc.)
            file_extension: File extension without the dot

        Returns:
            Data filename string
        """
        try:
            clean_type = self._clean_name_for_filename(neuron_type)
            clean_data_type = self._clean_name_for_filename(data_type)

            return f"{clean_type}_{clean_data_type}.{file_extension}"

        except Exception as e:
            logger.error(f"Error generating data filename: {e}")
            return f"{neuron_type}_{data_type}.{file_extension}"

    def generate_index_filename(self, index_type: str = 'main') -> str:
        """
        Generate filename for index pages.

        Args:
            index_type: Type of index (main, search, etc.)

        Returns:
            Index filename string
        """
        try:
            if index_type.lower() == 'main':
                return 'index.html'
            else:
                clean_type = self._clean_name_for_filename(index_type)
                return f"{clean_type}_index.html"

        except Exception as e:
            logger.error(f"Error generating index filename: {e}")
            return 'index.html'

    def generate_static_filename(self, original_name: str, asset_type: str) -> str:
        """
        Generate filename for static assets (CSS, JS, images).

        Args:
            original_name: Original filename
            asset_type: Type of asset (css, js, img, etc.)

        Returns:
            Static asset filename string
        """
        try:
            # Extract extension
            original_path = Path(original_name)
            name_part = original_path.stem
            extension = original_path.suffix

            # Clean the name part
            clean_name = self._clean_name_for_filename(name_part)

            # Add asset type prefix if not already present
            if not clean_name.startswith(asset_type):
                clean_name = f"{asset_type}_{clean_name}"

            return f"{clean_name}{extension}"

        except Exception as e:
            logger.error(f"Error generating static filename: {e}")
            return original_name

    def _clean_name_for_filename(self, name: str) -> str:
        """
        Clean a name to make it safe for use in filenames.

        Args:
            name: Original name string

        Returns:
            Cleaned name safe for filenames
        """
        try:
            if not name:
                return "unnamed"

            # Convert to string if not already
            clean_name = str(name)

            # Replace forward slashes with underscores (common in neuron type names)
            clean_name = clean_name.replace('/', '_')

            # Replace other problematic characters
            clean_name = re.sub(r'[<>:"|?*]', '_', clean_name)

            # Replace spaces with underscores
            clean_name = re.sub(r'\s+', '_', clean_name)

            # Replace multiple underscores with single underscore
            clean_name = re.sub(r'_+', '_', clean_name)

            # Remove leading/trailing underscores
            clean_name = clean_name.strip('_')

            # Ensure it's not empty after cleaning
            if not clean_name:
                clean_name = "unnamed"

            # Limit length to reasonable size
            if len(clean_name) > 100:
                clean_name = clean_name[:100]

            return clean_name

        except Exception as e:
            logger.error(f"Error cleaning name for filename: {e}")
            return "unnamed"

    def validate_filename(self, filename: str) -> bool:
        """
        Validate that a filename is safe and valid.

        Args:
            filename: Filename to validate

        Returns:
            True if filename is valid, False otherwise
        """
        try:
            if not filename:
                return False

            # Check for problematic characters
            problematic_chars = r'[<>:"|?*]'
            if re.search(problematic_chars, filename):
                return False

            # Check length
            if len(filename) > 255:
                return False

            # Check for reserved names (Windows)
            reserved_names = {
                'CON', 'PRN', 'AUX', 'NUL',
                'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
            }

            name_without_ext = Path(filename).stem.upper()
            if name_without_ext in reserved_names:
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating filename: {e}")
            return False

    def get_unique_filename(self, base_filename: str, existing_files: set) -> str:
        """
        Generate a unique filename by adding a number suffix if needed.

        Args:
            base_filename: Base filename to make unique
            existing_files: Set of existing filenames

        Returns:
            Unique filename string
        """
        try:
            if base_filename not in existing_files:
                return base_filename

            # Extract name and extension
            file_path = Path(base_filename)
            name_part = file_path.stem
            extension = file_path.suffix

            # Try adding numbers until we find a unique name
            counter = 1
            while counter < 1000:  # Reasonable limit
                new_filename = f"{name_part}_{counter}{extension}"
                if new_filename not in existing_files:
                    return new_filename
                counter += 1

            # If we can't find a unique name, add timestamp
            import time
            timestamp = int(time.time())
            return f"{name_part}_{timestamp}{extension}"

        except Exception as e:
            logger.error(f"Error generating unique filename: {e}")
            return base_filename

    def normalize_path_separators(self, path: str) -> str:
        """
        Normalize path separators for the current operating system.

        Args:
            path: Path string to normalize

        Returns:
            Normalized path string
        """
        try:
            return str(Path(path))
        except Exception as e:
            logger.error(f"Error normalizing path separators: {e}")
            return path

    def get_file_category(self, filename: str) -> str:
        """
        Determine the category of a file based on its extension.

        Args:
            filename: Filename to categorize

        Returns:
            File category string
        """
        try:
            extension = Path(filename).suffix.lower()

            if extension in ['.html', '.htm']:
                return 'html'
            elif extension in ['.css']:
                return 'css'
            elif extension in ['.js']:
                return 'javascript'
            elif extension in ['.svg', '.png', '.jpg', '.jpeg', '.gif', '.webp']:
                return 'image'
            elif extension in ['.json']:
                return 'data'
            elif extension in ['.csv']:
                return 'data'
            elif extension in ['.pdf']:
                return 'document'
            else:
                return 'other'

        except Exception as e:
            logger.error(f"Error determining file category: {e}")
            return 'other'
