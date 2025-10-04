"""
Tests for CitationService

This module tests the CitationService class functionality.
"""

import pytest

from neuview.services.citation_service import CitationService


class TestCitationService:
    """Test cases for CitationService."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.service = CitationService()

    @pytest.mark.unit
    def test_format_doi_url_works_without_import(self):
        """Test that format_doi_url works without requiring citations to be loaded."""
        # This method should work fine since it doesn't call load_citations
        result = self.service.format_doi_url("10.1234/example")
        assert result == "https://doi.org/10.1234/example"

        result = self.service.format_doi_url("https://doi.org/10.1234/example")
        assert result == "https://doi.org/10.1234/example"

        result = self.service.format_doi_url("")
        assert result == ""

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
