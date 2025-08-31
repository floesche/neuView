"""
Optimized Resource Strategy Implementation

This module provides an optimized resource strategy that wraps another
resource strategy with additional optimization features like minification,
compression, and content optimization for web resources.
"""

import re
import gzip
from typing import Any, Dict, Optional, List
from pathlib import Path
import logging

from .. import ResourceStrategy, ResourceNotFoundError, ResourceLoadError

logger = logging.getLogger(__name__)


class OptimizedResourceStrategy(ResourceStrategy):
    """
    Optimized resource strategy that adds optimization features.

    This strategy wraps another resource strategy and adds optimization
    features such as CSS/JS minification, image optimization, and gzip
    compression for better web performance.
    """

    def __init__(self, base_strategy: ResourceStrategy, enable_minification: bool = True, enable_compression: bool = True):
        """
        Initialize optimized resource strategy.

        Args:
            base_strategy: Base resource strategy to wrap
            enable_minification: Whether to enable CSS/JS minification
            enable_compression: Whether to enable gzip compression
        """
        self.base_strategy = base_strategy
        self.enable_minification = enable_minification
        self.enable_compression = enable_compression

    def _should_minify(self, resource_path: str) -> bool:
        """Check if a resource should be minified."""
        if not self.enable_minification:
            return False

        extension = Path(resource_path).suffix.lower()
        return extension in ['.css', '.js'] and not resource_path.endswith('.min.css') and not resource_path.endswith('.min.js')

    def _should_compress(self, resource_path: str) -> bool:
        """Check if a resource should be compressed."""
        if not self.enable_compression:
            return False

        extension = Path(resource_path).suffix.lower()
        return extension in ['.css', '.js', '.html', '.xml', '.json', '.txt']

    def _minify_css(self, content: str) -> str:
        """Basic CSS minification."""
        try:
            # Remove comments
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            # Remove unnecessary whitespace
            content = re.sub(r'\s+', ' ', content)
            # Remove whitespace around specific characters
            content = re.sub(r'\s*([{}:;,>+~])\s*', r'\1', content)
            return content.strip()
        except Exception as e:
            logger.warning(f"CSS minification failed: {e}")
            return content

    def _minify_js(self, content: str) -> str:
        """Basic JavaScript minification."""
        try:
            # Remove single-line comments (be careful with URLs)
            content = re.sub(r'(?<!:)//.*$', '', content, flags=re.MULTILINE)
            # Remove multi-line comments
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            # Remove unnecessary whitespace
            content = re.sub(r'\s+', ' ', content)
            # Remove whitespace around operators and punctuation
            content = re.sub(r'\s*([{}();,=+\-*/&|!<>])\s*', r'\1', content)
            return content.strip()
        except Exception as e:
            logger.warning(f"JavaScript minification failed: {e}")
            return content

    def _optimize_content(self, content: bytes, resource_path: str) -> bytes:
        """Apply optimizations to resource content."""
        try:
            # Convert to string for text-based optimizations
            text_content = content.decode('utf-8')

            # Apply minification if applicable
            if self._should_minify(resource_path):
                extension = Path(resource_path).suffix.lower()
                if extension == '.css':
                    text_content = self._minify_css(text_content)
                elif extension == '.js':
                    text_content = self._minify_js(text_content)

            # Convert back to bytes
            optimized_content = text_content.encode('utf-8')

            # Apply compression if applicable
            if self._should_compress(resource_path):
                optimized_content = gzip.compress(optimized_content)

            return optimized_content

        except UnicodeDecodeError:
            # Binary content, only apply compression if applicable
            if self._should_compress(resource_path):
                return gzip.compress(content)
            return content
        except Exception as e:
            logger.warning(f"Content optimization failed for {resource_path}: {e}")
            return content

    def load_resource(self, resource_path: str) -> bytes:
        """
        Load and optimize a resource.

        Args:
            resource_path: Path to the resource file

        Returns:
            Optimized resource content as bytes

        Raises:
            ResourceNotFoundError: If resource doesn't exist
            ResourceLoadError: If resource can't be loaded
        """
        # Load content from base strategy
        content = self.base_strategy.load_resource(resource_path)

        # Apply optimizations
        return self._optimize_content(content, resource_path)

    def resource_exists(self, resource_path: str) -> bool:
        """
        Check if a resource exists.

        Args:
            resource_path: Path to the resource file

        Returns:
            True if resource exists, False otherwise
        """
        return self.base_strategy.resource_exists(resource_path)

    def get_resource_metadata(self, resource_path: str) -> Dict[str, Any]:
        """
        Get metadata for a resource with optimization info.

        Args:
            resource_path: Path to the resource file

        Returns:
            Dictionary containing resource metadata including optimization info
        """
        metadata = self.base_strategy.get_resource_metadata(resource_path)

        # Add optimization metadata
        metadata['optimized'] = True
        metadata['minifiable'] = self._should_minify(resource_path)
        metadata['compressible'] = self._should_compress(resource_path)

        return metadata

    def list_resources(self, resource_dir: Path, pattern: str = "*") -> List[str]:
        """
        List resources from base strategy.

        Args:
            resource_dir: Directory to search for resources
            pattern: Glob pattern to match (default: "*")

        Returns:
            List of resource paths
        """
        return self.base_strategy.list_resources(resource_dir, pattern)

    def copy_resource(self, source_path: str, dest_path: str) -> bool:
        """
        Copy and optimize a resource to destination.

        Args:
            source_path: Source resource path
            dest_path: Destination path

        Returns:
            True if copy was successful, False otherwise
        """
        try:
            # Load and optimize content
            optimized_content = self.load_resource(source_path)

            # Write to destination
            dest_file = Path(dest_path)
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            with open(dest_file, 'wb') as f:
                f.write(optimized_content)

            return True

        except Exception as e:
            logger.error(f"Failed to copy and optimize resource {source_path} to {dest_path}: {e}")
            return False
