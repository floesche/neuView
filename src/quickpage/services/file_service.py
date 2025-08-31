"""
File service for handling file naming and path generation.

This module provides utilities for generating consistent filenames and managing
file paths for the page generation system.
"""

from pathlib import Path
from typing import Optional


class FileService:
    """
    Handle file naming and path generation for the page generation system.

    This service provides utilities for generating consistent filenames for
    neuron pages and managing file paths throughout the application.
    """

    @staticmethod
    def generate_filename(neuron_type: str, soma_side: str) -> str:
        """
        Generate HTML filename for a neuron type and soma side.

        This is a static utility method that doesn't require FileService instantiation.

        Args:
            neuron_type: The neuron type name
            soma_side: The soma side ('left', 'right', 'middle', 'all', 'combined')

        Returns:
            HTML filename string

        Example:
            >>> FileService.generate_filename("KC/a", "left")
            'KC_a_L.html'
            >>> FileService.generate_filename("Mi1", "all")
            'Mi1.html'
        """
        # Clean neuron type name for filename
        clean_type = neuron_type.replace('/', '_').replace(' ', '_')

        # Handle different soma side formats with new naming scheme
        if soma_side in ['all', 'combined']:
            # General page for neuron type (multiple sides available)
            return f"{clean_type}.html"
        else:
            # Specific page for single side
            soma_side_suffix = soma_side
            if soma_side_suffix == 'left':
                soma_side_suffix = 'L'
            elif soma_side_suffix == 'right':
                soma_side_suffix = 'R'
            elif soma_side_suffix == 'middle':
                soma_side_suffix = 'M'
            return f"{clean_type}_{soma_side_suffix}.html"

    def generate_filename_instance(self, neuron_type: str, soma_side: str) -> str:
        """
        Instance method wrapper for backwards compatibility.

        Args:
            neuron_type: The neuron type name
            soma_side: The soma side

        Returns:
            HTML filename string
        """
        return self.generate_filename(neuron_type, soma_side)

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize a filename by replacing problematic characters.

        Args:
            filename: The filename to sanitize

        Returns:
            Sanitized filename string
        """
        # Replace common problematic characters
        sanitized = filename.replace('/', '_').replace('\\', '_')
        sanitized = sanitized.replace(' ', '_').replace(':', '_')
        sanitized = sanitized.replace('?', '_').replace('*', '_')
        sanitized = sanitized.replace('<', '_').replace('>', '_')
        sanitized = sanitized.replace('|', '_').replace('"', '_')

        # Remove multiple consecutive underscores
        while '__' in sanitized:
            sanitized = sanitized.replace('__', '_')

        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')

        return sanitized

    @staticmethod
    def ensure_extension(filename: str, extension: str) -> str:
        """
        Ensure a filename has the specified extension.

        Args:
            filename: The filename to check
            extension: The extension to ensure (with or without leading dot)

        Returns:
            Filename with the correct extension
        """
        if not extension.startswith('.'):
            extension = f'.{extension}'

        if not filename.endswith(extension):
            return f"{filename}{extension}"

        return filename

    @staticmethod
    def create_safe_path(base_path: Path, *path_parts: str) -> Path:
        """
        Create a safe file path by joining path parts and ensuring the directory exists.

        Args:
            base_path: The base directory path
            *path_parts: Additional path components

        Returns:
            Complete Path object
        """
        full_path = base_path
        for part in path_parts:
            # Sanitize each path component
            safe_part = FileService.sanitize_filename(part)
            full_path = full_path / safe_part

        # Ensure parent directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)

        return full_path

    @staticmethod
    def get_relative_path(file_path: Path, base_path: Path) -> str:
        """
        Get the relative path from base_path to file_path.

        Args:
            file_path: The target file path
            base_path: The base directory path

        Returns:
            Relative path as string
        """
        try:
            return str(file_path.relative_to(base_path))
        except ValueError:
            # If paths are not relative, return absolute path
            return str(file_path)

    @staticmethod
    def validate_output_path(output_path: Path, base_dir: Path) -> bool:
        """
        Validate that an output path is within the expected base directory.

        Args:
            output_path: The output path to validate
            base_dir: The base directory that should contain the output

        Returns:
            True if the path is valid, False otherwise
        """
        try:
            resolved_output = output_path.resolve()
            resolved_base = base_dir.resolve()
            return str(resolved_output).startswith(str(resolved_base))
        except (OSError, ValueError):
            return False
