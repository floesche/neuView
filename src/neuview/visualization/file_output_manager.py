"""
File output manager for handling eyemap file operations.

This module provides a service class that handles all file-related operations
for eyemap generation, including saving files, managing directories, and
determining output paths.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Optional, Union

from .rendering import OutputFormat

logger = logging.getLogger(__name__)


class FileOutputManager:
    """
    Service class for managing file output operations in eyemap generation.

    This class encapsulates all file-related operations including directory
    creation, file path generation, and coordinating with renderers for
    file saving operations.
    """

    def __init__(
        self, output_dir: Optional[Path] = None, eyemaps_dir: Optional[Path] = None
    ):
        """
        Initialize the file output manager.

        Args:
            output_dir: Base directory for output files
            eyemaps_dir: Specific directory for eyemap files
        """
        self.output_dir = output_dir
        self.eyemaps_dir = eyemaps_dir
        self._ensure_directories_exist()

    def _ensure_directories_exist(self):
        """Ensure that required directories exist."""
        if self.output_dir and not self.output_dir.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created output directory: {self.output_dir}")

        if self.eyemaps_dir and not self.eyemaps_dir.exists():
            self.eyemaps_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created eyemaps directory: {self.eyemaps_dir}")

    def handle_grid_output(
        self,
        request,
        region: str,
        side: str,
        synapse_content: str,
        cell_content: str,
        rendering_manager,
    ) -> Dict:
        """
        Handle saving or returning grid content based on request configuration.

        Args:
            request: GridGenerationRequest containing output configuration
            region: Region name
            side: Side identifier
            synapse_content: Generated synapse grid content
            cell_content: Generated cell grid content
            rendering_manager: RenderingManager instance for file operations

        Returns:
            Dictionary with 'synapse_density' and 'cell_count' keys mapping to
            either file paths (if saving) or content strings (if embedding)
        """
        if self._should_save_to_files(request):
            return self._save_grids_to_files(
                request, region, side, synapse_content, cell_content, rendering_manager
            )
        else:
            return self._return_grid_content(synapse_content, cell_content)

    def _should_generate_eyemap(self, filename: str) -> bool:
        """
        Check if eyemap file should be generated (doesn't exist yet).

        Args:
            filename: The filename to check

        Returns:
            True if file should be generated, False if it already exists
        """
        if not self.eyemaps_dir:
            return True

        file_path = self.eyemaps_dir / filename
        if file_path.exists():
            logger.debug(f"Eyemap already exists, skipping generation: {filename}")
            return False

        return True

    def _should_save_to_files(self, request) -> bool:
        """
        Determine if grids should be saved to files.

        Args:
            request: GridGenerationRequest containing configuration

        Returns:
            True if files should be saved, False otherwise
        """
        return request.save_to_files and self.output_dir is not None

    def _save_grids_to_files(
        self,
        request,
        region: str,
        side: str,
        synapse_content: str,
        cell_content: str,
        rendering_manager,
    ) -> Dict:
        """
        Save grid content to files and return file paths.

        Args:
            request: GridGenerationRequest containing configuration
            region: Region name
            side: Side identifier
            synapse_content: Generated synapse grid content
            cell_content: Generated cell grid content
            rendering_manager: RenderingManager instance for file operations

        Returns:
            Dictionary mapping metric types to file paths
        """
        format_enum = self._get_output_format_enum(request.output_format)

        if request.output_format not in ["svg", "png"]:
            raise ValueError(f"Unsupported output format: {request.output_format}")

        renderer = rendering_manager._get_renderer(format_enum)

        # Generate file names
        synapse_filename = self._generate_filename(
            region, request.neuron_type, side, "synapse_density"
        )
        cell_filename = self._generate_filename(
            region, request.neuron_type, side, "cell_count"
        )

        # Check if files already exist and return existing paths if so
        synapse_path = None
        cell_path = None

        if self._should_generate_eyemap(synapse_filename):
            synapse_path = renderer.save_to_file(synapse_content, synapse_filename)
        else:
            synapse_path = self.eyemaps_dir / synapse_filename

        if self._should_generate_eyemap(cell_filename):
            cell_path = renderer.save_to_file(cell_content, cell_filename)
        else:
            cell_path = self.eyemaps_dir / cell_filename

        if synapse_path and cell_path:
            logger.debug(
                f"Generated/reused grids for {region}_{side}: {synapse_path}, {cell_path}"
            )

        return {"synapse_density": str(synapse_path), "cell_count": str(cell_path)}

    def _return_grid_content(self, synapse_content: str, cell_content: str) -> Dict:
        """
        Return grid content directly for embedding.

        Args:
            synapse_content: Generated synapse grid content
            cell_content: Generated cell grid content

        Returns:
            Dictionary mapping metric types to content strings
        """
        return {"synapse_density": synapse_content, "cell_count": cell_content}

    def _get_output_format_enum(self, output_format: str) -> OutputFormat:
        """
        Convert string output format to OutputFormat enum.

        Args:
            output_format: String format ('svg' or 'png')

        Returns:
            Corresponding OutputFormat enum value
        """
        if output_format.lower() == "svg":
            return OutputFormat.SVG
        elif output_format.lower() == "png":
            return OutputFormat.PNG
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _generate_filename(
        self, region: str, neuron_type: str, side: str, metric_type: str
    ) -> str:
        """
        Generate a standardized filename for eyemap files.

        Args:
            region: Region name
            neuron_type: Neuron type identifier
            side: Side identifier
            metric_type: Type of metric ('synapse_density' or 'cell_count')

        Returns:
            Generated filename (without extension)
        """
        return f"{region}_{neuron_type}_{side}_{metric_type}"

    def get_output_path(
        self, filename: str, use_eyemaps_dir: bool = True
    ) -> Optional[Path]:
        """
        Get the full output path for a given filename.

        Args:
            filename: Base filename
            use_eyemaps_dir: Whether to use eyemaps directory or base output directory

        Returns:
            Full path where the file should be saved, or None if no output directory is set
        """
        if use_eyemaps_dir and self.eyemaps_dir:
            return self.eyemaps_dir / filename
        elif self.output_dir:
            return self.output_dir / filename
        else:
            return None

    def validate_output_configuration(self) -> bool:
        """
        Validate that the output configuration is valid for file operations.

        Returns:
            True if configuration is valid, False otherwise
        """
        if not self.output_dir:
            logger.warning("No output directory configured")
            return False

        if not self.output_dir.exists():
            try:
                self.output_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created output directory: {self.output_dir}")
            except Exception as e:
                logger.error(
                    f"Failed to create output directory {self.output_dir}: {e}"
                )
                return False

        if not self.output_dir.is_dir():
            logger.error(f"Output path is not a directory: {self.output_dir}")
            return False

        if not os.access(self.output_dir, os.W_OK):
            logger.error(f"Output directory is not writable: {self.output_dir}")
            return False

        return True

    def clean_output_directory(self, pattern: str = "*.svg") -> int:
        """
        Clean files matching a pattern from the output directory.

        Args:
            pattern: Glob pattern for files to remove

        Returns:
            Number of files removed
        """
        if not self.output_dir or not self.output_dir.exists():
            return 0

        removed_count = 0
        for file_path in self.output_dir.glob(pattern):
            try:
                file_path.unlink()
                removed_count += 1
                logger.debug(f"Removed file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to remove file {file_path}: {e}")

        if removed_count > 0:
            logger.info(f"Cleaned {removed_count} files from {self.output_dir}")

        return removed_count

    def get_output_statistics(self) -> Dict:
        """
        Get statistics about the output directory.

        Returns:
            Dictionary containing output directory statistics
        """
        stats = {
            "output_dir": str(self.output_dir) if self.output_dir else None,
            "eyemaps_dir": str(self.eyemaps_dir) if self.eyemaps_dir else None,
            "output_dir_exists": self.output_dir.exists() if self.output_dir else False,
            "eyemaps_dir_exists": self.eyemaps_dir.exists()
            if self.eyemaps_dir
            else False,
            "file_count": 0,
            "total_size_bytes": 0,
        }

        if self.output_dir and self.output_dir.exists():
            try:
                files = list(self.output_dir.glob("*"))
                stats["file_count"] = len([f for f in files if f.is_file()])
                stats["total_size_bytes"] = sum(
                    f.stat().st_size for f in files if f.is_file()
                )
            except Exception as e:
                logger.warning(f"Failed to get directory statistics: {e}")

        return stats

    def update_directories(
        self, output_dir: Optional[Path] = None, eyemaps_dir: Optional[Path] = None
    ):
        """
        Update the configured directories.

        Args:
            output_dir: New output directory (optional)
            eyemaps_dir: New eyemaps directory (optional)
        """
        if output_dir is not None:
            self.output_dir = output_dir

        if eyemaps_dir is not None:
            self.eyemaps_dir = eyemaps_dir

        self._ensure_directories_exist()


class FileOutputManagerFactory:
    """
    Factory class for creating FileOutputManager instances.
    """

    @staticmethod
    def create_manager(
        output_dir: Optional[Union[str, Path]] = None,
        eyemaps_dir: Optional[Union[str, Path]] = None,
    ) -> FileOutputManager:
        """
        Create a new FileOutputManager instance.

        Args:
            output_dir: Base directory for output files
            eyemaps_dir: Specific directory for eyemap files

        Returns:
            New FileOutputManager instance
        """
        # Convert strings to Path objects
        if isinstance(output_dir, str):
            output_dir = Path(output_dir)
        if isinstance(eyemaps_dir, str):
            eyemaps_dir = Path(eyemaps_dir)

        return FileOutputManager(output_dir, eyemaps_dir)

    @staticmethod
    def create_from_config(config) -> FileOutputManager:
        """
        Create a FileOutputManager from an EyemapConfiguration.

        Args:
            config: EyemapConfiguration instance

        Returns:
            New FileOutputManager instance
        """
        return FileOutputManager(
            output_dir=config.output_dir, eyemaps_dir=config.eyemaps_dir
        )

    @staticmethod
    def create_temporary_manager(
        base_dir: Optional[Union[str, Path]] = None,
    ) -> FileOutputManager:
        """
        Create a FileOutputManager with temporary directories.

        Args:
            base_dir: Base directory for temporary files (optional)

        Returns:
            New FileOutputManager instance with temporary directories
        """
        import tempfile

        if base_dir:
            if isinstance(base_dir, str):
                base_dir = Path(base_dir)
            temp_dir = base_dir / "temp_eyemaps"
        else:
            temp_dir = Path(tempfile.mkdtemp(prefix="eyemaps_"))

        return FileOutputManager(output_dir=temp_dir, eyemaps_dir=temp_dir / "eyemaps")
