"""
Remote Resource Strategy Implementation

This module provides a remote resource strategy that can load resources
from remote URLs with support for HTTP/HTTPS protocols and basic caching.
"""

import re
import time
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from typing import Any, Dict, Optional, List
from pathlib import Path
import logging

from .. import ResourceStrategy, ResourceNotFoundError, ResourceLoadError

logger = logging.getLogger(__name__)


class RemoteResourceStrategy(ResourceStrategy):
    """
    Remote resource strategy for loading resources from URLs.

    This strategy loads resources from remote URLs using HTTP/HTTPS protocols.
    It supports basic authentication, custom headers, and timeout configuration.
    """

    def __init__(self, base_url: str, timeout: int = 30, headers: Optional[Dict[str, str]] = None):
        """
        Initialize remote resource strategy.

        Args:
            base_url: Base URL for remote resources
            timeout: Request timeout in seconds
            headers: Optional HTTP headers to include in requests
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.headers = headers or {}

        # Validate base URL
        if not self._is_valid_url(self.base_url):
            raise ValueError(f"Invalid base URL: {base_url}")

    def _is_valid_url(self, url: str) -> bool:
        """Check if a URL is valid."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except Exception:
            return False

    def load_resource(self, resource_path: str) -> bytes:
        """
        Load a resource from remote URL.

        Args:
            resource_path: Path to the resource relative to base URL

        Returns:
            Resource content as bytes

        Raises:
            ResourceNotFoundError: If resource doesn't exist (404)
            ResourceLoadError: If resource can't be loaded
        """
        url = f"{self.base_url}/{resource_path.lstrip('/')}"

        try:
            request = Request(url, headers=self.headers)
            with urlopen(request, timeout=self.timeout) as response:
                return response.read()

        except HTTPError as e:
            if e.code == 404:
                raise ResourceNotFoundError(f"Remote resource not found: {url}")
            else:
                raise ResourceLoadError(f"HTTP error {e.code} loading {url}: {e}")
        except URLError as e:
            raise ResourceLoadError(f"URL error loading {url}: {e}")
        except Exception as e:
            raise ResourceLoadError(f"Failed to load remote resource {url}: {e}")

    def resource_exists(self, resource_path: str) -> bool:
        """
        Check if a remote resource exists.

        Args:
            resource_path: Path to the resource

        Returns:
            True if resource exists, False otherwise
        """
        try:
            self.load_resource(resource_path)
            return True
        except ResourceNotFoundError:
            return False
        except Exception:
            return False

    def get_resource_metadata(self, resource_path: str) -> Dict[str, Any]:
        """
        Get metadata for a remote resource.

        Args:
            resource_path: Path to the resource

        Returns:
            Dictionary containing resource metadata

        Raises:
            ResourceNotFoundError: If resource doesn't exist
            ResourceLoadError: If metadata can't be retrieved
        """
        url = f"{self.base_url}/{resource_path.lstrip('/')}"

        try:
            request = Request(url, headers=self.headers)
            request.get_method = lambda: 'HEAD'  # Use HEAD request for metadata only

            with urlopen(request, timeout=self.timeout) as response:
                metadata = {
                    'url': url,
                    'status_code': response.getcode(),
                    'content_type': response.headers.get('Content-Type', 'unknown'),
                    'content_length': int(response.headers.get('Content-Length', 0)),
                    'last_modified': response.headers.get('Last-Modified'),
                    'etag': response.headers.get('ETag'),
                    'server': response.headers.get('Server'),
                    'headers': dict(response.headers),
                    'retrieved_at': time.time()
                }

                # Parse filename from URL or Content-Disposition header
                if 'Content-Disposition' in response.headers:
                    content_disp = response.headers['Content-Disposition']
                    filename_match = re.search(r'filename="([^"]+)"', content_disp)
                    if filename_match:
                        metadata['filename'] = filename_match.group(1)

                if 'filename' not in metadata:
                    metadata['filename'] = Path(resource_path).name

                return metadata

        except HTTPError as e:
            if e.code == 404:
                raise ResourceNotFoundError(f"Remote resource not found: {url}")
            else:
                raise ResourceLoadError(f"HTTP error {e.code} getting metadata for {url}: {e}")
        except URLError as e:
            raise ResourceLoadError(f"URL error getting metadata for {url}: {e}")
        except Exception as e:
            raise ResourceLoadError(f"Failed to get metadata for remote resource {url}: {e}")

    def list_resources(self, resource_dir: Path, pattern: str = "*") -> List[str]:
        """
        List remote resources (not supported for most remote protocols).

        Args:
            resource_dir: Directory to search (ignored for remote resources)
            pattern: Pattern to match (ignored for remote resources)

        Returns:
            Empty list (remote resource listing not supported)
        """
        logger.warning("Resource listing not supported for remote resources")
        return []

    def copy_resource(self, source_path: str, dest_path: str) -> bool:
        """
        Copy a remote resource to local destination.

        Args:
            source_path: Source resource path (relative to base URL)
            dest_path: Local destination file path

        Returns:
            True if copy was successful, False otherwise
        """
        try:
            content = self.load_resource(source_path)

            dest_file = Path(dest_path)
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            with open(dest_file, 'wb') as f:
                f.write(content)

            return True

        except Exception as e:
            logger.error(f"Failed to copy remote resource {source_path} to {dest_path}: {e}")
            return False
