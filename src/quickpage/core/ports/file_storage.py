"""
File storage port for the core domain layer.

This port defines the contract that the domain layer expects from
external file storage systems for saving and retrieving generated content.
"""

from abc import ABC, abstractmethod
from typing import List


class FileStorage(ABC):
    """
    Port for file storage operations.

    This port defines how the domain layer expects to interact with
    the file system for saving generated content.
    """

    @abstractmethod
    async def save_file(self, path: str, content: str) -> None:
        """
        Save content to a file.

        Args:
            path: File path to save to
            content: Content to save
        """
        pass

    @abstractmethod
    async def read_file(self, path: str) -> str:
        """
        Read content from a file.

        Args:
            path: File path to read from

        Returns:
            File content
        """
        pass

    @abstractmethod
    async def file_exists(self, path: str) -> bool:
        """
        Check if a file exists.

        Args:
            path: File path to check

        Returns:
            True if file exists, False otherwise
        """
        pass

    @abstractmethod
    async def create_directory(self, path: str) -> None:
        """
        Create a directory.

        Args:
            path: Directory path to create
        """
        pass

    @abstractmethod
    async def list_files(self, directory: str) -> List[str]:
        """
        List files in a directory.

        Args:
            directory: Directory path to list

        Returns:
            List of file names in the directory
        """
        pass
