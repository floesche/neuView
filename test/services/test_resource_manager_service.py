"""
Tests for ResourceManagerService

This module tests the ResourceManagerService class, particularly focusing on catching
import errors related to the missing project_root function import.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from neuview.services.resource_manager_service import ResourceManagerService


class TestResourceManagerService:
    """Test cases for ResourceManagerService."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create a mock config
        self.mock_config = Mock()
        self.mock_config.output = Mock()
        self.mock_config.output.directory = "output"

        # Create temporary output directory
        self.temp_dir = Path(tempfile.mkdtemp())

        # Create mock jinja environment
        self.mock_jinja_env = Mock()

        # Initialize service with jinja environment
        self.service = ResourceManagerService(
            config=self.mock_config,
            output_dir=self.temp_dir,
            jinja_env=self.mock_jinja_env,
        )

        # Mock the neuroglancer JS service to return success
        mock_neuroglancer_service = Mock()
        mock_neuroglancer_service.generate_neuroglancer_js.return_value = True
        self.service._neuroglancer_js_service = mock_neuroglancer_service

        # Create the expected neuroglancer JS file with required content
        js_output_dir = self.temp_dir / "static" / "js"
        js_output_dir.mkdir(parents=True, exist_ok=True)
        neuroglancer_js_file = js_output_dir / "neuroglancer-url-generator.js"
        neuroglancer_js_file.write_text(
            "function initializeNeuroglancerLinks() { /* mock */ }"
        )

    @pytest.mark.unit
    @patch("neuview.services.resource_manager_service.get_static_dir")
    def test_copy_static_files_should_work_but_fails_due_to_missing_import(
        self, mock_get_static_dir
    ):
        """Test that copy_static_files should work but fails due to missing project_root import."""
        # Mock get_static_dir to return a temporary directory with required structure
        mock_static_dir = self.temp_dir / "mock_static"
        mock_static_dir.mkdir(exist_ok=True)
        (mock_static_dir / "css").mkdir(exist_ok=True)
        (mock_static_dir / "js").mkdir(exist_ok=True)
        (mock_static_dir / "images").mkdir(exist_ok=True)
        mock_get_static_dir.return_value = mock_static_dir

        # This test expects copy_static_files to work normally
        # It will FAIL when project_root is not defined, exposing the import issue
        result = self.service.copy_static_files(mode="force_all")
        assert result is True, (
            "copy_static_files should succeed when imports are correct"
        )

    @pytest.mark.unit
    @patch("neuview.services.resource_manager_service.get_static_dir")
    def test_resource_manager_template_copying_should_work(self, mock_get_static_dir):
        """Test that resource manager template copying should work normally."""
        # Mock get_static_dir to return a temporary directory with required structure
        mock_static_dir = self.temp_dir / "mock_static"
        mock_static_dir.mkdir(exist_ok=True)
        (mock_static_dir / "css").mkdir(exist_ok=True)
        (mock_static_dir / "js").mkdir(exist_ok=True)
        (mock_static_dir / "images").mkdir(exist_ok=True)
        mock_get_static_dir.return_value = mock_static_dir

        # This should work when imports are correct - will fail if project_root is undefined
        result = self.service.copy_static_files(mode="force_all")
        assert result is True, (
            "Resource manager should successfully copy template files"
        )

    @pytest.mark.integration
    @patch("neuview.services.resource_manager_service.get_static_dir")
    def test_resource_manager_handles_template_static_assets(self, mock_get_static_dir):
        """Integration test: Resource manager should handle template static assets."""
        # Mock get_static_dir to return a temporary directory with required structure
        mock_static_dir = self.temp_dir / "mock_static"
        mock_static_dir.mkdir(exist_ok=True)
        (mock_static_dir / "css").mkdir(exist_ok=True)
        (mock_static_dir / "js").mkdir(exist_ok=True)
        mock_get_static_dir.return_value = mock_static_dir

        # This should successfully copy template static assets
        # Will fail with NameError if project_root import is missing
        result = self.service.copy_static_files(mode="force_all")
        assert result is True, (
            "Should successfully handle template static asset copying"
        )

    @pytest.mark.unit
    def test_resource_manager_service_initialization(self):
        """Test that ResourceManagerService initializes correctly."""
        # This should work fine since initialization doesn't use project_root
        assert self.service.config == self.mock_config
        assert self.service.output_dir == self.temp_dir
        assert (
            self.service._neuroglancer_js_service is not None
        )  # Mock service is set in setup

    @pytest.mark.unit
    @patch("neuview.services.resource_manager_service.get_static_dir")
    def test_methods_not_using_project_root_work(self, mock_get_static_dir):
        """Test that methods not using project_root work correctly."""
        # Mock get_static_dir to return a temporary directory
        mock_static_dir = self.temp_dir / "mock_static"
        mock_static_dir.mkdir(exist_ok=True)
        mock_get_static_dir.return_value = mock_static_dir

        # Create some mock static files
        (mock_static_dir / "css").mkdir(exist_ok=True)
        (mock_static_dir / "js").mkdir(exist_ok=True)

        # Test setup_output_directories
        self.service.setup_output_directories()

        # Test ensure_directory_exists
        test_dir = self.temp_dir / "test"
        self.service.ensure_directory_exists(test_dir)
        assert test_dir.exists()

    @pytest.mark.integration
    @patch("neuview.services.resource_manager_service.get_static_dir")
    def test_static_files_copying_complete_workflow(self, mock_get_static_dir):
        """
        Integration test: Complete static files copying workflow should work.

        This test will FAIL if project_root import is missing, exposing the issue.
        """
        # Mock get_static_dir to return a temporary directory with required structure
        mock_static_dir = self.temp_dir / "mock_static"
        mock_static_dir.mkdir(exist_ok=True)
        (mock_static_dir / "css").mkdir(exist_ok=True)
        (mock_static_dir / "js").mkdir(exist_ok=True)
        (mock_static_dir / "images").mkdir(exist_ok=True)
        mock_get_static_dir.return_value = mock_static_dir

        # This should successfully copy all static files including template assets
        result = self.service.copy_static_files(mode="force_all")
        assert result is True, "Complete static files workflow should succeed"

    @pytest.mark.integration
    @patch("neuview.services.resource_manager_service.get_static_dir")
    def test_production_like_static_file_management(self, mock_get_static_dir):
        """
        Integration test: Production-like static file management workflow.

        This test simulates real application usage and will FAIL if imports are missing.
        """
        # Mock get_static_dir to return a temporary directory with required structure
        mock_static_dir = self.temp_dir / "mock_static"
        mock_static_dir.mkdir(exist_ok=True)
        (mock_static_dir / "css").mkdir(exist_ok=True)
        (mock_static_dir / "js").mkdir(exist_ok=True)
        mock_get_static_dir.return_value = mock_static_dir

        # Set up a realistic output directory structure
        static_output_dir = self.temp_dir / "static"
        static_output_dir.mkdir(exist_ok=True)

        # This should work in production - will fail if project_root is undefined
        result = self.service.copy_static_files(mode="force_all")
        assert result is True, "Production static file workflow should work correctly"

    @pytest.mark.integration
    @patch("neuview.services.resource_manager_service.get_static_dir")
    def test_neuroglancer_integration_with_static_files(self, mock_get_static_dir):
        """
        Integration test: Neuroglancer service integration with static files should work.

        This test will FAIL if project_root import is missing.
        """
        # Mock get_static_dir to return a temporary directory with required structure
        mock_static_dir = self.temp_dir / "mock_static"
        mock_static_dir.mkdir(exist_ok=True)
        (mock_static_dir / "css").mkdir(exist_ok=True)
        (mock_static_dir / "js").mkdir(exist_ok=True)
        mock_get_static_dir.return_value = mock_static_dir

        # This should work with neuroglancer service integration
        result = self.service.copy_static_files(mode="force_all")
        assert result is True, "Neuroglancer integration should work with static files"

    @pytest.mark.integration
    @patch("neuview.services.resource_manager_service.get_static_dir")
    def test_template_static_directory_access_should_work(self, mock_get_static_dir):
        """
        Integration test: Template static directory access should work normally.

        This test will FAIL when project_root is undefined, exposing the import issue.
        """
        # Mock get_static_dir to return a temporary directory with required structure
        mock_static_dir = self.temp_dir / "mock_static"
        mock_static_dir.mkdir(exist_ok=True)
        (mock_static_dir / "css").mkdir(exist_ok=True)
        (mock_static_dir / "js").mkdir(exist_ok=True)
        mock_get_static_dir.return_value = mock_static_dir

        # Should successfully access template static directory when imports are correct
        result = self.service.copy_static_files(mode="force_all")
        assert result is True, "Template static directory access should work"

    @pytest.mark.unit
    @patch("neuview.services.resource_manager_service.get_static_dir")
    def test_resource_manager_basic_functionality(self, mock_get_static_dir):
        """Test basic resource manager functionality should work."""
        # Mock get_static_dir to return a temporary directory with required structure
        mock_static_dir = self.temp_dir / "mock_static"
        mock_static_dir.mkdir(exist_ok=True)
        (mock_static_dir / "css").mkdir(exist_ok=True)
        (mock_static_dir / "js").mkdir(exist_ok=True)
        mock_get_static_dir.return_value = mock_static_dir

        # Basic functionality should work - will fail if imports are missing
        result = self.service.copy_static_files(mode="force_all")
        assert result is True, "Basic resource management functionality should work"

    def teardown_method(self):
        """Clean up after each test method."""
        # Clean up temporary directory
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)


@pytest.mark.integration
class TestResourceManagerServiceIntegration:
    """Integration tests for ResourceManagerService that reveal import issues."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create a more realistic mock config
        self.mock_config = Mock()
        self.mock_config.output = Mock()
        self.mock_config.output.directory = "output"
        self.mock_config.neuroglancer = Mock()
        self.mock_config.neuroglancer.base_url = "https://example.com"

        # Create temporary output directory
        self.temp_dir = Path(tempfile.mkdtemp())

        # Create mock jinja environment
        self.mock_jinja_env = Mock()

        # Initialize service with jinja environment
        self.service = ResourceManagerService(
            config=self.mock_config,
            output_dir=self.temp_dir,
            jinja_env=self.mock_jinja_env,
        )

        # Mock the neuroglancer JS service to return success
        mock_neuroglancer_service = Mock()
        mock_neuroglancer_service.generate_neuroglancer_js.return_value = True
        self.service._neuroglancer_js_service = mock_neuroglancer_service

        # Create the expected neuroglancer JS file with required content
        js_output_dir = self.temp_dir / "static" / "js"
        js_output_dir.mkdir(parents=True, exist_ok=True)
        neuroglancer_js_file = js_output_dir / "neuroglancer-url-generator.js"
        neuroglancer_js_file.write_text(
            "function initializeNeuroglancerLinks() { /* mock */ }"
        )

    @pytest.mark.integration
    @patch("neuview.services.resource_manager_service.get_static_dir")
    def test_complete_page_generation_resource_workflow(self, mock_get_static_dir):
        """
        Integration test: Complete page generation resource workflow should work.

        This test will FAIL if project_root import is missing, exposing the issue.
        """
        # Mock get_static_dir to return a temporary directory with required structure
        mock_static_dir = self.temp_dir / "mock_static"
        mock_static_dir.mkdir(exist_ok=True)
        (mock_static_dir / "css").mkdir(exist_ok=True)
        (mock_static_dir / "js").mkdir(exist_ok=True)
        mock_get_static_dir.return_value = mock_static_dir

        # Step 1: Setup output directories (should work)
        self.service.setup_output_directories()

        # Step 2: Copy static files (should work when imports are correct)
        result = self.service.copy_static_files(mode="force_all")
        assert result is True, "Complete resource workflow should succeed"

    @pytest.mark.integration
    @patch("neuview.services.resource_manager_service.get_static_dir")
    def test_template_asset_management_workflow(self, mock_get_static_dir):
        """
        Integration test: Template asset management should work correctly.

        This test will FAIL when project_root is undefined, clearly showing the problem.
        """
        # Mock get_static_dir to return a temporary directory with required structure
        mock_static_dir = self.temp_dir / "mock_static"
        mock_static_dir.mkdir(exist_ok=True)
        (mock_static_dir / "css").mkdir(exist_ok=True)
        (mock_static_dir / "js").mkdir(exist_ok=True)
        mock_get_static_dir.return_value = mock_static_dir

        # Create some mock static content that would normally trigger template copying
        static_dir = self.temp_dir / "static"
        static_dir.mkdir(exist_ok=True)

        # Create a mock file to ensure the copying logic is triggered
        test_file = static_dir / "test.css"
        test_file.write_text("/* test css */")

        # Template asset management should work when imports are correct
        result = self.service.copy_static_files(mode="force_all")
        assert result is True, "Template asset management workflow should succeed"

    @pytest.mark.integration
    @patch("neuview.services.resource_manager_service.get_static_dir")
    def test_resource_manager_reliability_and_consistency(self, mock_get_static_dir):
        """
        Integration test: Resource manager should be reliable and consistent.

        This test will FAIL if there are import issues, exposing the problem.
        """
        # Mock get_static_dir to return a temporary directory with required structure
        mock_static_dir = self.temp_dir / "mock_static"
        mock_static_dir.mkdir(exist_ok=True)
        (mock_static_dir / "css").mkdir(exist_ok=True)
        (mock_static_dir / "js").mkdir(exist_ok=True)
        mock_get_static_dir.return_value = mock_static_dir

        # Should work reliably when all imports are correct
        result = self.service.copy_static_files(mode="force_all")
        assert result is True, "Resource manager should work reliably"

        # Verify the service state is consistent
        assert self.service.config == self.mock_config
        assert self.service.output_dir == self.temp_dir

    def teardown_method(self):
        """Clean up after each test method."""
        # Clean up temporary directory
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
