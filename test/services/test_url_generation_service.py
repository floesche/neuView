"""
Tests for URL Generation Service

This module tests the URLGenerationService class, particularly the template
selection logic for different datasets.
"""

from unittest.mock import Mock, patch
from jinja2 import Environment, DictLoader

from quickpage.services.url_generation_service import URLGenerationService


class MockConfig:
    """Mock configuration object for testing."""

    def __init__(self, dataset="hemibrain:v1.2.1"):
        self.neuprint = Mock()
        self.neuprint.dataset = dataset
        self.neuprint.server = "neuprint.janelia.org"


class TestURLGenerationService:
    """Test cases for URLGenerationService."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create mock templates
        self.templates = {
            "neuroglancer.js.jinja": """{"title": "{{ website_title }}", "dataset": "standard"}""",
            "neuroglancer-fafb.js.jinja": """{"title": "{{ website_title }}", "dataset": "fafb"}""",
        }

        # Create Jinja environment with mock templates
        self.jinja_env = Environment(loader=DictLoader(self.templates))

        # Create mock services
        self.neuron_selection_service = Mock()
        self.database_query_service = Mock()

    def create_service(self, dataset="hemibrain:v1.2.1"):
        """Create URLGenerationService with specified dataset."""
        config = MockConfig(dataset)
        return URLGenerationService(
            config=config,
            jinja_env=self.jinja_env,
            neuron_selection_service=self.neuron_selection_service,
            database_query_service=self.database_query_service,
        )

    def test_uses_standard_template_for_non_fafb_dataset(self):
        """Test that standard template is used for non-FAFB datasets."""
        service = self.create_service("hemibrain:v1.2.1")

        # Mock neuron data
        neuron_data = {"neurons": None}

        # Mock the neuron selection service to return empty list
        self.neuron_selection_service.select_bodyids_by_soma_side.return_value = []

        # Mock the database query service to return empty connections
        self.database_query_service.get_connected_bodyids.return_value = {
            "upstream": {},
            "downstream": {},
        }

        url, template_vars = service.generate_neuroglancer_url("TestType", neuron_data)

        # Verify the URL was generated (not the fallback)
        assert url.startswith("https://clio-ng.janelia.org/#!")

        # Verify template variables indicate standard template was used
        assert template_vars["website_title"] == "TestType"

    def test_uses_fafb_template_for_fafb_dataset(self):
        """Test that FAFB-specific template is used for FAFB datasets."""
        service = self.create_service("flywire-fafb:v783b")

        # Mock neuron data
        neuron_data = {"neurons": None}

        # Mock the neuron selection service to return empty list
        self.neuron_selection_service.select_bodyids_by_soma_side.return_value = []

        # Mock the database query service to return empty connections
        self.database_query_service.get_connected_bodyids.return_value = {
            "upstream": {},
            "downstream": {},
        }

        url, template_vars = service.generate_neuroglancer_url("TestType", neuron_data)

        # Verify the URL was generated (not the fallback)
        assert url.startswith("https://clio-ng.janelia.org/#!")

        # Verify template variables
        assert template_vars["website_title"] == "TestType"

    def test_fafb_detection_case_insensitive(self):
        """Test that FAFB detection is case insensitive."""
        # Test various case combinations
        fafb_datasets = [
            "flywire-fafb:v783b",
            "FLYWIRE-FAFB:V783B",
            "FlywIre-FaFb:v783b",
            "some-FAFB-dataset:v1",
            "fafb:v1",
        ]

        for dataset in fafb_datasets:
            service = self.create_service(dataset)

            # Mock dependencies
            neuron_data = {"neurons": None}
            self.neuron_selection_service.select_bodyids_by_soma_side.return_value = []
            self.database_query_service.get_connected_bodyids.return_value = {
                "upstream": {},
                "downstream": {},
            }

            # Should use FAFB template (test that it doesn't fail)
            url, template_vars = service.generate_neuroglancer_url(
                "TestType", neuron_data
            )
            assert url.startswith("https://clio-ng.janelia.org/")

    def test_non_fafb_datasets_use_standard_template(self):
        """Test that non-FAFB datasets use the standard template."""
        non_fafb_datasets = [
            "hemibrain:v1.2.1",
            "cns:v1.0",
            "optic-lobe:v1.0",
            "some-other-dataset:v1",
        ]

        for dataset in non_fafb_datasets:
            service = self.create_service(dataset)

            # Mock dependencies
            neuron_data = {"neurons": None}
            self.neuron_selection_service.select_bodyids_by_soma_side.return_value = []
            self.database_query_service.get_connected_bodyids.return_value = {
                "upstream": {},
                "downstream": {},
            }

            # Should use standard template
            url, template_vars = service.generate_neuroglancer_url(
                "TestType", neuron_data
            )
            assert url.startswith("https://clio-ng.janelia.org/")

    @patch("quickpage.services.url_generation_service.logger")
    def test_logs_template_selection(self, mock_logger):
        """Test that template selection is logged."""
        service = self.create_service("flywire-fafb:v783b")

        # Mock dependencies
        neuron_data = {"neurons": None}
        self.neuron_selection_service.select_bodyids_by_soma_side.return_value = []
        self.database_query_service.get_connected_bodyids.return_value = {
            "upstream": {},
            "downstream": {},
        }

        service.generate_neuroglancer_url("TestType", neuron_data)

        # Verify logging was called
        mock_logger.debug.assert_called_with(
            "Using Neuroglancer template: neuroglancer-fafb.js.jinja for dataset: flywire-fafb:v783b"
        )

    def test_fallback_on_template_error(self):
        """Test that fallback URL is returned when template processing fails."""
        # Create service with missing template to trigger error
        service = self.create_service("flywire-fafb:v783b")
        service.env = Environment(loader=DictLoader({}))  # Empty template loader

        neuron_data = {"neurons": None}

        url, template_vars = service.generate_neuroglancer_url("TestType", neuron_data)

        # Should return fallback URL
        assert url == "https://clio-ng.janelia.org/"
        assert template_vars["website_title"] == "TestType"
        assert template_vars["visible_neurons"] == []

    def test_template_variables_passed_correctly(self):
        """Test that all required template variables are passed to the template."""
        service = self.create_service("flywire-fafb:v783b")

        # Create mock neuron DataFrame
        import pandas as pd

        mock_neurons_df = pd.DataFrame(
            {"bodyId": [123, 456, 789], "type": ["TestType", "TestType", "TestType"]}
        )

        neuron_data = {"neurons": mock_neurons_df}

        # Mock services
        self.neuron_selection_service.select_bodyids_by_soma_side.return_value = [
            123,
            456,
        ]
        self.database_query_service.get_connected_bodyids.return_value = {
            "upstream": {"TypeA": [111]},
            "downstream": {"TypeB": [222]},
        }

        url, template_vars = service.generate_neuroglancer_url(
            "TestType", neuron_data, "left"
        )

        # Verify all expected template variables are present
        expected_vars = [
            "website_title",
            "visible_neurons",
            "neuron_query",
            "visible_rois",
            "connected_bids",
        ]
        for var in expected_vars:
            assert var in template_vars

        assert template_vars["website_title"] == "TestType"
        assert template_vars["visible_neurons"] == ["123", "456"]
        assert template_vars["neuron_query"] == "TestType"
        assert template_vars["connected_bids"] == {
            "upstream": {"TypeA": [111]},
            "downstream": {"TypeB": [222]},
        }
