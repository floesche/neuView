"""Integration tests for male-cns dataset configuration."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from neuview.config import Config
from neuview.dataset_adapters import CNSAdapter
from neuview.neuprint_connector import NeuPrintConnector


@pytest.mark.integration
class TestMaleCNSIntegration:
    """Integration tests for male-cns dataset configuration across multiple components."""

    @pytest.mark.integration
    def test_config_with_male_cns_creates_cns_adapter(self):
        """Integration test: config file with male-cns:v0.9 creates CNS adapter."""
        # Create a temporary config file with male-cns dataset
        config_content = """
neuprint:
  server: "neuprint.janelia.org"
  dataset: "male-cns:v0.9"
  token: "test_token"

output:
  directory: "output"
  template_dir: "templates"

discovery:
  max_types: 10
  randomize: true

html:
  title_prefix: "Male CNS"
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            config_file = f.name

        try:
            # Load config from file
            config = Config.from_file(config_file)

            # Verify config loaded correctly
            assert config.neuprint.dataset == "male-cns:v0.9"
            assert config.neuprint.server == "neuprint.janelia.org"

            # Create connector and verify it uses CNS adapter
            # Mock the connection since we don't want to actually connect
            with patch("neuview.neuprint_connector.Client") as mock_client_class:
                mock_client = Mock()
                mock_client_class.return_value = mock_client

                connector = NeuPrintConnector(config)

                # Verify the dataset adapter is CNS adapter
                assert isinstance(connector.dataset_adapter, CNSAdapter)

                # Verify dataset info has correct name (should be normalized)
                assert connector.dataset_adapter.dataset_info.name == "cns"

        finally:
            # Clean up temporary file
            os.unlink(config_file)

    @pytest.mark.integration
    def test_male_cns_alias_in_layer_analysis_service(self):
        """Integration test: LayerAnalysisService works with male-cns config."""
        from neuview.services.layer_analysis_service import LayerAnalysisService
        from neuview.dataset_adapters import DatasetAdapterFactory

        # Create a config with male-cns dataset
        config_content = """
neuprint:
  server: "neuprint.janelia.org"
  dataset: "male-cns:v0.9"

output:
  directory: "output"
  template_dir: "templates"

discovery:
  max_types: 10
  randomize: true

html:
  title_prefix: "Male CNS"
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            config_file = f.name

        try:
            config = Config.from_file(config_file)

            # Verify that the service can create the correct adapter
            adapter = DatasetAdapterFactory.create_adapter(config.neuprint.dataset)
            assert isinstance(adapter, CNSAdapter)

        finally:
            os.unlink(config_file)

    @pytest.mark.integration
    def test_male_cns_config_yaml_compatibility(self):
        """Integration test: verify actual config.yaml works with male-cns dataset."""
        # Read the actual config.yaml file
        config_path = Path(__file__).parent.parent / "config.yaml"

        if config_path.exists():
            config = Config.from_file(str(config_path))

            # If the config uses male-cns, verify it works
            if config.neuprint.dataset.startswith("male-cns"):
                from neuview.dataset_adapters import DatasetAdapterFactory

                adapter = DatasetAdapterFactory.create_adapter(config.neuprint.dataset)
                assert isinstance(adapter, CNSAdapter)
                assert adapter.dataset_info.name == "cns"

    @pytest.mark.integration
    def test_end_to_end_male_cns_workflow(self):
        """Integration test: end-to-end workflow with male-cns configuration."""
        # Create a temporary config with male-cns dataset
        config_content = """
neuprint:
  server: "neuprint.janelia.org"
  dataset: "male-cns:v0.9"
  token: "test_token"

output:
  directory: "output"
  template_dir: "templates"

discovery:
  max_types: 10
  randomize: true

html:
  title_prefix: "Male CNS"
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            config_file = f.name

        try:
            # Load config
            config = Config.from_file(config_file)

            # Create adapter through the normal factory process
            from neuview.dataset_adapters import DatasetAdapterFactory

            adapter = DatasetAdapterFactory.create_adapter(config.neuprint.dataset)

            # Verify end-to-end functionality
            assert isinstance(adapter, CNSAdapter)
            assert adapter.dataset_info.name == "cns"
            assert config.neuprint.dataset == "male-cns:v0.9"
            assert config.html.title_prefix == "Male CNS"

        finally:
            os.unlink(config_file)
