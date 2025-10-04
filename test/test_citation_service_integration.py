"""
Integration tests for CitationService that will fail due to missing imports.

This test file contains integration tests that use CitationService in realistic
scenarios, which will expose the missing get_input_dir import and cause test
failures that help identify the issue.
"""

import tempfile
import pytest

from neuview.services.citation_service import CitationService


@pytest.mark.integration
class TestCitationServiceIntegration:
    """Integration tests for CitationService that reveal import issues."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.service = CitationService()

    @pytest.mark.integration
    def test_citation_service_loads_citations_from_input_directory(self):
        """
        Integration test: CitationService should load citations from input directory.

        This test will FAIL due to the missing get_input_dir() import in citation_service.py.
        The failure will expose the import issue that needs to be fixed.
        """
        # This should attempt to load citations from the input directory
        # but will fail with NameError: name 'get_input_dir' is not defined
        citations = self.service.load_citations()

        # If the import was working, we would expect either:
        # - A dictionary with citations loaded from input/citations.csv
        # - An empty dictionary if the file doesn't exist
        assert isinstance(citations, dict)

    @pytest.mark.integration
    def test_citation_service_get_citations_integration(self):
        """
        Integration test: get_citations() should work in realistic usage.

        This test will FAIL due to the missing get_input_dir() import.
        """
        # This should trigger loading citations from the input directory
        citations = self.service.get_citations()
        assert isinstance(citations, dict)

    @pytest.mark.integration
    def test_citation_service_create_citation_link_integration(self):
        """
        Integration test: create_citation_link() should work with real citation data.

        This test will FAIL when it tries to load citations due to missing import.
        """
        # This should attempt to load citations and then create a link
        # The load_citations() call will fail with the import error
        link = self.service.create_citation_link("SomeReference2023")

        # Even if no citation is found, this should return the citation key
        assert isinstance(link, str)

    @pytest.mark.integration
    def test_citation_service_get_all_citation_keys_integration(self):
        """
        Integration test: get_all_citation_keys() should return available citations.

        This test will FAIL due to the missing get_input_dir() import.
        """
        # This should load citations and return all available keys
        keys = self.service.get_all_citation_keys()
        assert isinstance(keys, list)

    @pytest.mark.integration
    def test_citation_service_contains_check_integration(self):
        """
        Integration test: __contains__ should work with loaded citations.

        This test will FAIL due to the missing get_input_dir() import.
        """
        # This should trigger citation loading via __contains__
        result = "SomeReference2023" in self.service
        assert isinstance(result, bool)

    @pytest.mark.integration
    def test_citation_service_length_integration(self):
        """
        Integration test: len() should return number of loaded citations.

        This test will FAIL due to the missing get_input_dir() import.
        """
        # This should trigger citation loading via __len__
        length = len(self.service)
        assert isinstance(length, int)
        assert length >= 0

    @pytest.mark.integration
    def test_citation_service_add_citation_integration(self):
        """
        Integration test: add_citation() should work with existing citation data.

        This test will FAIL when it tries to load existing citations first.
        """
        # This should load existing citations first, then add a new one
        self.service.add_citation("TestRef2023", "https://example.com", "Test Paper")

        # Verify the citation was added
        assert "TestRef2023" in self.service.citations

    @pytest.mark.integration
    def test_citation_service_reload_citations_integration(self):
        """
        Integration test: reload_citations() should refresh citation data.

        This test will FAIL due to the missing get_input_dir() import.
        """
        # This should attempt to reload citations from the input directory
        citations = self.service.reload_citations()
        assert isinstance(citations, dict)

    @pytest.mark.integration
    def test_citation_service_with_output_dir_logging(self):
        """
        Integration test: citation service with output directory for logging.

        This test will FAIL due to the missing get_input_dir() import.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # This should try to load citations and set up logging
            link = self.service.create_citation_link(
                "NonexistentCitation", output_dir=temp_dir
            )
            assert isinstance(link, str)

    @pytest.mark.integration
    def test_citation_service_realistic_workflow(self):
        """
        Integration test: realistic workflow that a page generator would use.

        This test simulates how CitationService would actually be used in the
        application and will FAIL due to the missing import.
        """
        # Step 1: Load citations (this will fail with NameError)
        citations = self.service.load_citations()

        # Step 2: Check if a specific citation exists
        has_citation = "Smith2023" in self.service

        # Step 3: Get citation count
        citation_count = len(self.service)

        # Step 4: Create citation links
        link1 = self.service.create_citation_link("Smith2023")
        link2 = self.service.create_citation_link("Jones2022", "Custom Text")

        # Step 5: Get all available citations
        all_keys = self.service.get_all_citation_keys()

        # These assertions would only run if the import issue was fixed
        assert isinstance(citations, dict)
        assert isinstance(has_citation, bool)
        assert isinstance(citation_count, int)
        assert isinstance(link1, str)
        assert isinstance(link2, str)
        assert isinstance(all_keys, list)
