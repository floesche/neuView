"""
Local file storage adapter for the infrastructure layer.

This adapter implements the FileStorage port using the local
filesystem for all file operations.
"""

import asyncio
from pathlib import Path
from typing import List
import logging

from ...core.ports import FileStorage

logger = logging.getLogger(__name__)


class LocalFileStorage(FileStorage):
    """
    File storage adapter using the local filesystem.

    This adapter implements the FileStorage port using the local
    filesystem for all file operations.
    """

    async def save_file(self, path: str, content: str) -> None:
        """
        Save content to a file.

        Args:
            path: File path to save to
            content: Content to save
        """
        try:
            file_path = Path(path)

            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: file_path.write_text(content, encoding='utf-8')
            )

            logger.debug(f"Saved file: {path}")

        except Exception as e:
            logger.error(f"Failed to save file {path}: {e}")
            raise

    async def read_file(self, path: str) -> str:
        """
        Read content from a file.

        Args:
            path: File path to read from

        Returns:
            File content
        """
        try:
            file_path = Path(path)

            # Read file in executor to avoid blocking
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(
                None,
                lambda: file_path.read_text(encoding='utf-8')
            )

            logger.debug(f"Read file: {path}")
            return content

        except Exception as e:
            logger.error(f"Failed to read file {path}: {e}")
            raise

    async def file_exists(self, path: str) -> bool:
        """
        Check if a file exists.

        Args:
            path: File path to check

        Returns:
            True if file exists, False otherwise
        """
        try:
            file_path = Path(path)
            return file_path.exists() and file_path.is_file()
        except Exception:
            return False

    async def create_directory(self, path: str) -> None:
        """
        Create a directory.

        Args:
            path: Directory path to create
        """
        try:
            dir_path = Path(path)
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {path}")
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {e}")
            raise

    async def list_files(self, directory: str) -> List[str]:
        """
        List files in a directory.

        Args:
            directory: Directory path to list

        Returns:
            List of file names in the directory
        """
        try:
            dir_path = Path(directory)
            if not dir_path.exists() or not dir_path.is_dir():
                return []

            files = []
            for file_path in dir_path.iterdir():
                if file_path.is_file():
                    files.append(file_path.name)

            return sorted(files)

        except Exception as e:
            logger.error(f"Failed to list files in {directory}: {e}")
            return []
