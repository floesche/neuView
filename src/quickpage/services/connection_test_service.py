"""
Connection Test Service for QuickPage.

This service handles testing NeuPrint connections and returning
dataset information.
"""

import logging
from ..result import Result, Ok, Err
from ..commands import TestConnectionCommand, DatasetInfo

logger = logging.getLogger(__name__)


class ConnectionTestService:
    """Service for testing NeuPrint connection."""

    def __init__(self, neuprint_connector):
        """Initialize connection test service.

        Args:
            neuprint_connector: NeuPrint connector instance
        """
        self.connector = neuprint_connector

    async def test_connection(
        self, command: TestConnectionCommand
    ) -> Result[DatasetInfo, str]:
        """Test connection to NeuPrint server."""
        try:
            info = self.connector.test_connection()

            dataset_info = DatasetInfo(
                name=info.get("dataset", "Unknown"),
                version=info.get("version", "Unknown"),
                server_url=info.get("server", "Unknown"),
                connection_status="Connected",
            )

            return Ok(dataset_info)

        except Exception as e:
            return Err(f"Connection test failed: {str(e)}")

    def get_connection_info(self) -> dict:
        """Get basic connection information without testing."""
        try:
            # Try to get basic info without making a network call
            return {
                "server_configured": hasattr(self.connector, "server")
                and self.connector.server is not None,
                "credentials_configured": hasattr(self.connector, "token")
                and self.connector.token is not None,
                "client_initialized": hasattr(self.connector, "client")
                and self.connector.client is not None,
            }
        except Exception as e:
            logger.debug(f"Failed to get connection info: {e}")
            return {
                "server_configured": False,
                "credentials_configured": False,
                "client_initialized": False,
                "error": str(e),
            }
