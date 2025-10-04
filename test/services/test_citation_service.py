"""
Tests for CitationService

This module tests the CitationService class, particularly focusing on catching
import errors and testing citation loading functionality.
"""

import pytest

from neuview.services.citation_service import CitationService


class TestCitationService:
    """Test cases for CitationService."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.service = CitationService()

    @pytest.mark.unit
    def test_import_error_on_load_citations(self):
        """Test that load_citations fails due to missing get_input_dir import."""
        # This test should catch the NameError when get_input_dir() is called
        # without being imported
        with pytest.raises(NameError, match="name 'get_input_dir' is not defined"):
            self.service.load_citations()

    @pytest.mark.unit
    def test_import_error_propagates_to_get_citations(self):
        """Test that the import error propagates to get_citations method."""
        with pytest.raises(NameError, match="name 'get_input_dir' is not defined"):
            self.service.get_citations()

    @pytest.mark.unit
    def test_import_error_propagates_to_get_citation(self):
        """Test that the import error propagates to get_citation method."""
        with pytest.raises(NameError, match="name 'get_input_dir' is not defined"):
            self.service.get_citation("test_citation")

    @pytest.mark.unit
    def test_import_error_propagates_to_get_citation_url(self):
        """Test that the import error propagates to get_citation_url method."""
        with pytest.raises(NameError, match="name 'get_input_dir' is not defined"):
            self.service.get_citation_url("test_citation")

    @pytest.mark.unit
    def test_import_error_propagates_to_get_citation_title(self):
        """Test that the import error propagates to get_citation_title method."""
        with pytest.raises(NameError, match="name 'get_input_dir' is not defined"):
            self.service.get_citation_title("test_citation")

    @pytest.mark.unit
    def test_import_error_propagates_to_get_all_citation_keys(self):
        """Test that the import error propagates to get_all_citation_keys method."""
        with pytest.raises(NameError, match="name 'get_input_dir' is not defined"):
            self.service.get_all_citation_keys()

    @pytest.mark.unit
    def test_import_error_propagates_to_reload_citations(self):
        """Test that the import error propagates to reload_citations method."""
        with pytest.raises(NameError, match="name 'get_input_dir' is not defined"):
            self.service.reload_citations()

    @pytest.mark.unit
    def test_import_error_propagates_to_len(self):
        """Test that the import error propagates to __len__ method."""
        with pytest.raises(NameError, match="name 'get_input_dir' is not defined"):
            len(self.service)

    @pytest.mark.unit
    def test_import_error_propagates_to_contains(self):
        """Test that the import error propagates to __contains__ method."""
        with pytest.raises(NameError, match="name 'get_input_dir' is not defined"):
            "test_citation" in self.service

    @pytest.mark.unit
    def test_format_doi_url_works_without_import(self):
        """Test that format_doi_url works without requiring get_input_dir import."""
        # This method should work fine since it doesn't call load_citations
        result = self.service.format_doi_url("10.1234/example")
        assert result == "https://doi.org/10.1234/example"

        result = self.service.format_doi_url("https://doi.org/10.1234/example")
        assert result == "https://doi.org/10.1234/example"

        result = self.service.format_doi_url("")
        assert result == ""

    @pytest.mark.unit
    def test_add_citation_triggers_import_error(self):
        """Test that add_citation triggers the import error when loading citations."""
        with pytest.raises(NameError, match="name 'get_input_dir' is not defined"):
            self.service.add_citation("test", "https://example.com", "Test Title")

    @pytest.mark.unit
    def test_create_citation_link_triggers_import_error(self):
        """Test create_citation_link behavior when citations can't be loaded due to import error."""
        # The method should trigger the import error when trying to load citations
        with pytest.raises(NameError, match="name 'get_input_dir' is not defined"):
            self.service.create_citation_link("NonexistentCitation")

    @pytest.mark.unit
    def test_citation_service_initialization(self):
        """Test that CitationService initializes correctly."""
        assert self.service.citations == {}
        assert self.service._loaded is False
        assert self.service._citation_logger is None

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "doi_input,expected_output",
        [
            ("10.1234/example", "https://doi.org/10.1234/example"),
            ("https://doi.org/10.1234/example", "https://doi.org/10.1234/example"),
            ("https://example.com/paper", "https://example.com/paper"),
            ("", ""),
            ("  10.5678/test  ", "https://doi.org/10.5678/test"),
        ],
    )
    def test_format_doi_url_parametrized(self, doi_input, expected_output):
        """Test format_doi_url with various inputs."""
        result = self.service.format_doi_url(doi_input)
        assert result == expected_output

    @pytest.mark.unit
    def test_import_error_fails_fast(self):
        """Test that the import error causes immediate failure without graceful degradation."""
        # Ensure that the service doesn't try to handle the error gracefully
        # and that it fails fast when the import is missing
        with pytest.raises(NameError, match="name 'get_input_dir' is not defined"):
            self.service.load_citations()

        # Verify that the service state is not modified when the error occurs
        assert self.service._loaded is False
        assert len(self.service.citations) == 0
