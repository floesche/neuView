"""
Test scatterplot service
"""

import pytest
import sys
import os

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from neuview.config import Config
from neuview.neuprint_connector import NeuPrintConnector
from neuview.services.scatterplot_service import ScatterplotService

class TestScatterPlotService:
    """Test scatterplot data"""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        # Try to load from actual config file if available, otherwise use minimal config
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")

        if os.path.exists(config_path):
            try:
                return Config.load(config_path)
            except Exception:
                # Fall back to minimal config if loading fails
                return Config.create_minimal_for_testing()
        else:
            return Config.create_minimal_for_testing()

    @pytest.fixture
    def neuprint_connector(self, config):
        """Create NeuPrint connector instance."""
        return NeuPrintConnector(config)

    @pytest.fixture
    def service(self):
        # Build with a dummy config; we'll override the output dir per-test
        return ScatterplotService(config=self.config, page_generator=None)
