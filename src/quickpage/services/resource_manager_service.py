"""
Resource Manager Service for QuickPage.

This service handles resource management logic that was previously part of the
PageGenerator class. It provides methods for copying static files, managing
directories, and handling other file system operations.
"""

import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class ResourceManagerService:
    """Service for managing static files, directories, and other resources."""

    def __init__(self, config, output_dir: Path):
        """Initialize resource manager service.

        Args:
            config: Configuration object containing paths and settings
            output_dir: Base output directory for generated files
        """
        self.config = config
        self.output_dir = Path(output_dir)
        self.template_dir = Path(config.output.template_dir)

    def setup_output_directories(self) -> Dict[str, Path]:
        """
        Create and set up all required output directories.

        Returns:
            Dictionary mapping directory names to their paths
        """
        directories = {}

        # Create main output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        directories['output'] = self.output_dir

        # Create types subdirectory for neuron type pages
        types_dir = self.output_dir / 'types'
        types_dir.mkdir(parents=True, exist_ok=True)
        directories['types'] = types_dir

        # Create eyemaps directory for hexagon grid images
        eyemaps_dir = self.output_dir / 'eyemaps'
        eyemaps_dir.mkdir(parents=True, exist_ok=True)
        directories['eyemaps'] = eyemaps_dir

        # Create static directory for CSS, JS, and other assets
        static_dir = self.output_dir / 'static'
        static_dir.mkdir(parents=True, exist_ok=True)
        directories['static'] = static_dir

        # Create subdirectories within static
        css_dir = static_dir / 'css'
        css_dir.mkdir(parents=True, exist_ok=True)
        directories['css'] = css_dir

        js_dir = static_dir / 'js'
        js_dir.mkdir(parents=True, exist_ok=True)
        directories['js'] = js_dir

        # Create cache directory for temporary files
        cache_dir = self.output_dir / '.cache'
        cache_dir.mkdir(parents=True, exist_ok=True)
        directories['cache'] = cache_dir

        logger.info(f"Set up output directories: {list(directories.keys())}")
        return directories

    def copy_static_files(self) -> bool:
        """
        Copy static CSS and JS files to the output directory.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the project root directory (where static files are stored)
            project_root = Path(__file__).parent.parent.parent.parent
            static_source_dir = project_root / 'static'

            if not static_source_dir.exists():
                logger.warning(f"Static source directory not found: {static_source_dir}")
                return False

            # Set up output directories
            directories = self.setup_output_directories()
            output_static_dir = directories['static']

            # Copy CSS files
            css_source_dir = static_source_dir / 'css'
            if css_source_dir.exists():
                output_css_dir = directories['css']
                self._copy_files_recursive(css_source_dir, output_css_dir, '*.css')

            # Copy JS files
            js_source_dir = static_source_dir / 'js'
            if js_source_dir.exists():
                output_js_dir = directories['js']
                self._copy_files_recursive(js_source_dir, output_js_dir, '*.js')

            # Copy other static assets (images, fonts, etc.)
            for item in static_source_dir.iterdir():
                if item.is_file() and item.suffix in ['.ico', '.png', '.jpg', '.jpeg', '.gif', '.svg']:
                    shutil.copy2(item, output_static_dir / item.name)

            logger.info("Successfully copied static files to output directory")
            return True

        except Exception as e:
            logger.error(f"Failed to copy static files: {e}")
            return False

    def _copy_files_recursive(self, source_dir: Path, dest_dir: Path, pattern: str = '*') -> None:
        """
        Recursively copy files matching a pattern from source to destination.

        Args:
            source_dir: Source directory
            dest_dir: Destination directory
            pattern: File pattern to match (e.g., '*.css', '*.js')
        """
        try:
            for item in source_dir.rglob(pattern):
                if item.is_file():
                    # Maintain directory structure
                    relative_path = item.relative_to(source_dir)
                    dest_path = dest_dir / relative_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest_path)
                    logger.debug(f"Copied {item} to {dest_path}")
        except Exception as e:
            logger.error(f"Failed to copy files from {source_dir} to {dest_dir}: {e}")

    def copy_template_files(self, template_names: Optional[List[str]] = None) -> bool:
        """
        Copy template files to the output directory.

        Args:
            template_names: Optional list of specific template names to copy.
                          If None, copies all templates.

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.template_dir.exists():
                logger.warning(f"Template directory not found: {self.template_dir}")
                return False

            output_templates_dir = self.output_dir / 'templates'
            output_templates_dir.mkdir(parents=True, exist_ok=True)

            if template_names:
                # Copy specific templates
                for template_name in template_names:
                    template_path = self.template_dir / template_name
                    if template_path.exists():
                        shutil.copy2(template_path, output_templates_dir / template_name)
                        logger.debug(f"Copied template {template_name}")
                    else:
                        logger.warning(f"Template not found: {template_path}")
            else:
                # Copy all templates
                self._copy_files_recursive(self.template_dir, output_templates_dir, '*.html')
                self._copy_files_recursive(self.template_dir, output_templates_dir, '*.jinja')
                self._copy_files_recursive(self.template_dir, output_templates_dir, '*.j2')

            logger.info("Successfully copied template files")
            return True

        except Exception as e:
            logger.error(f"Failed to copy template files: {e}")
            return False

    def clean_output_directory(self, preserve_cache: bool = True) -> bool:
        """
        Clean the output directory, optionally preserving cache.

        Args:
            preserve_cache: If True, preserves the .cache directory

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.output_dir.exists():
                logger.info("Output directory does not exist, nothing to clean")
                return True

            cache_dir = self.output_dir / '.cache'
            cache_contents = []

            # Back up cache if preserving
            if preserve_cache and cache_dir.exists():
                import tempfile
                temp_cache = Path(tempfile.mkdtemp())
                shutil.copytree(cache_dir, temp_cache / '.cache')
                cache_contents = list((temp_cache / '.cache').rglob('*'))

            # Remove output directory
            shutil.rmtree(self.output_dir)

            # Recreate directories
            directories = self.setup_output_directories()

            # Restore cache if it was preserved
            if preserve_cache and cache_contents:
                temp_cache_dir = cache_contents[0].parent if cache_contents else None
                if temp_cache_dir and temp_cache_dir.exists():
                    shutil.copytree(temp_cache_dir, cache_dir, dirs_exist_ok=True)
                    shutil.rmtree(temp_cache_dir.parent)

            logger.info(f"Cleaned output directory: {self.output_dir}")
            return True

        except Exception as e:
            logger.error(f"Failed to clean output directory: {e}")
            return False

    def ensure_directory_exists(self, directory_path: Path) -> bool:
        """
        Ensure a directory exists, creating it if necessary.

        Args:
            directory_path: Path to the directory

        Returns:
            True if directory exists or was created successfully
        """
        try:
            directory_path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {directory_path}: {e}")
            return False

    def get_file_size(self, file_path: Path) -> Optional[int]:
        """
        Get the size of a file in bytes.

        Args:
            file_path: Path to the file

        Returns:
            File size in bytes, or None if file doesn't exist or error occurs
        """
        try:
            if file_path.exists() and file_path.is_file():
                return file_path.stat().st_size
            return None
        except Exception as e:
            logger.error(f"Failed to get file size for {file_path}: {e}")
            return None

    def list_directory_contents(self, directory_path: Path,
                              pattern: str = '*', recursive: bool = False) -> List[Path]:
        """
        List contents of a directory with optional pattern matching.

        Args:
            directory_path: Path to the directory
            pattern: File pattern to match (default: '*' for all files)
            recursive: If True, search recursively

        Returns:
            List of matching file paths
        """
        try:
            if not directory_path.exists() or not directory_path.is_dir():
                return []

            if recursive:
                return list(directory_path.rglob(pattern))
            else:
                return list(directory_path.glob(pattern))

        except Exception as e:
            logger.error(f"Failed to list directory contents for {directory_path}: {e}")
            return []

    def copy_file(self, source_path: Path, dest_path: Path,
                  create_dirs: bool = True) -> bool:
        """
        Copy a single file from source to destination.

        Args:
            source_path: Source file path
            dest_path: Destination file path
            create_dirs: If True, create destination directories if they don't exist

        Returns:
            True if successful, False otherwise
        """
        try:
            if not source_path.exists():
                logger.error(f"Source file does not exist: {source_path}")
                return False

            if create_dirs:
                dest_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(source_path, dest_path)
            logger.debug(f"Copied {source_path} to {dest_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to copy {source_path} to {dest_path}: {e}")
            return False

    def move_file(self, source_path: Path, dest_path: Path,
                  create_dirs: bool = True) -> bool:
        """
        Move a file from source to destination.

        Args:
            source_path: Source file path
            dest_path: Destination file path
            create_dirs: If True, create destination directories if they don't exist

        Returns:
            True if successful, False otherwise
        """
        try:
            if not source_path.exists():
                logger.error(f"Source file does not exist: {source_path}")
                return False

            if create_dirs:
                dest_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.move(str(source_path), str(dest_path))
            logger.debug(f"Moved {source_path} to {dest_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to move {source_path} to {dest_path}: {e}")
            return False

    def delete_file(self, file_path: Path) -> bool:
        """
        Delete a file.

        Args:
            file_path: Path to the file to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                logger.debug(f"Deleted file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False

    def get_resource_stats(self) -> Dict[str, Any]:
        """
        Get statistics about managed resources.

        Returns:
            Dictionary containing resource statistics
        """
        try:
            stats = {
                'output_dir': str(self.output_dir),
                'output_dir_exists': self.output_dir.exists(),
                'template_dir': str(self.template_dir),
                'template_dir_exists': self.template_dir.exists(),
                'directories': {},
                'file_counts': {}
            }

            if self.output_dir.exists():
                # Get directory information
                for subdir in ['types', 'eyemaps', 'static', '.cache']:
                    dir_path = self.output_dir / subdir
                    stats['directories'][subdir] = {
                        'exists': dir_path.exists(),
                        'path': str(dir_path)
                    }
                    if dir_path.exists():
                        files = self.list_directory_contents(dir_path, recursive=True)
                        stats['file_counts'][subdir] = len([f for f in files if f.is_file()])

            return stats

        except Exception as e:
            logger.error(f"Failed to get resource stats: {e}")
            return {'error': str(e)}
