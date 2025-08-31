#!/usr/bin/env python3
"""
Phase 1 Refactoring Demonstration

This script demonstrates the usage of the services extracted from PageGenerator
in Phase 1 of the refactoring. It shows how each service can be used independently
and how they work together.
"""

import sys
from pathlib import Path

# Add the src directory to the path so we can import quickpage modules
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from quickpage.services.brain_region_service import BrainRegionService
from quickpage.services.citation_service import CitationService
from quickpage.services.partner_analysis_service import PartnerAnalysisService
from quickpage.services.jinja_template_service import JinjaTemplateService
from quickpage.services.neuron_search_service import NeuronSearchService
from quickpage.config import Config
from pathlib import Path
import tempfile


def demo_brain_region_service():
    """Demonstrate BrainRegionService functionality."""
    print("\n=== Brain Region Service Demo ===")

    service = BrainRegionService()

    # Load brain regions (will load from CSV if available)
    regions = service.load_brain_regions()
    print(f"Loaded {len(regions)} brain regions")

    # Add a test region for demonstration
    service.add_brain_region("TEST", "Test Region")

    # Test ROI abbreviation filtering
    test_cases = [
        "ME(R)",
        "LO(L)",
        "TEST",
        "UNKNOWN",
        None,
        ""
    ]

    print("\nROI Abbreviation Filtering:")
    for roi in test_cases:
        result = service.roi_abbr_filter(roi)
        print(f"  {roi!r} -> {result}")

    # Test service features
    print(f"\nService contains 'TEST': {'TEST' in service}")
    print(f"Service length: {len(service)}")
    print(f"Full name for 'TEST': {service.get_full_name('TEST')}")


def demo_citation_service():
    """Demonstrate CitationService functionality."""
    print("\n=== Citation Service Demo ===")

    service = CitationService()

    # Load citations (will load from CSV if available)
    citations = service.load_citations()
    print(f"Loaded {len(citations)} citations")

    # Add test citations for demonstration
    service.add_citation("Smith2023", "10.1234/example", "Example Paper Title")
    service.add_citation("Doe2022", "https://example.com", "Another Paper")

    # Test citation operations
    print(f"\nCitation service length: {len(service)}")
    print(f"Contains 'Smith2023': {'Smith2023' in service}")

    # Test URL formatting
    doi_cases = [
        "10.1234/example",
        "https://doi.org/10.1234/example",
        "https://example.com"
    ]

    print("\nDOI URL Formatting:")
    for doi in doi_cases:
        formatted = service.format_doi_url(doi)
        print(f"  {doi!r} -> {formatted}")

    # Test citation link creation
    print("\nCitation Link Generation:")
    citation_cases = ["Smith2023", "Doe2022", "NonExistent"]
    for citation in citation_cases:
        link = service.create_citation_link(citation)
        print(f"  {citation} -> {link}")


def demo_partner_analysis_service():
    """Demonstrate PartnerAnalysisService functionality."""
    print("\n=== Partner Analysis Service Demo ===")

    service = PartnerAnalysisService()

    # Create test connectivity data
    connected_bids = {
        'upstream': {
            'Dm4_L': [1001, 1002, 1003],
            'Dm4_R': [2001, 2002],
            'Tm1': [3001, 3002, 3003, 3004],
            'LC4': {'L': [4001, 4002], 'R': [4003, 4004]}
        },
        'downstream': {
            'T4_L': [5001, 5002],
            'T4_R': [6001, 6002, 6003],
            'LPLC2': [7001, 7002, 7003]
        }
    }

    # Test partner data extraction
    test_cases = [
        ({'type': 'Dm4', 'soma_side': 'L'}, 'upstream'),
        ({'type': 'Dm4', 'soma_side': 'R'}, 'upstream'),
        ({'type': 'Dm4'}, 'upstream'),  # No side specified
        ('Tm1', 'upstream'),  # String input
        ({'type': 'LC4', 'soma_side': 'L'}, 'upstream'),  # Dict data structure
        ({'type': 'T4', 'soma_side': 'R'}, 'downstream'),
        ({'type': 'NonExistent'}, 'upstream'),  # Non-existent type
    ]

    print("Partner Body ID Extraction:")
    for partner_data, direction in test_cases:
        body_ids = service.get_partner_body_ids(partner_data, direction, connected_bids)
        print(f"  {partner_data} ({direction}) -> {body_ids}")

    # Test connectivity analysis
    partners = [
        {'type': 'Dm4', 'soma_side': 'L'},
        {'type': 'T4', 'soma_side': 'R'},
        'Tm1'
    ]

    analysis = service.analyze_partner_connectivity(connected_bids, partners)
    print(f"\nConnectivity Analysis for {len(partners)} partners:")
    for partner_name, directions in analysis.items():
        print(f"  {partner_name}:")
        for direction, body_ids in directions.items():
            print(f"    {direction}: {len(body_ids)} body IDs")

    # Test statistics
    stats = service.get_partner_statistics(connected_bids)
    print(f"\nConnectivity Statistics:")
    print(f"  Directions: {stats['directions']}")
    print(f"  Total partner types: {stats['total_partner_types']}")
    print(f"  Types by direction: {stats['types_by_direction']}")
    print(f"  Side-specific types: {stats['side_specific_types']}")


def demo_jinja_template_service():
    """Demonstrate JinjaTemplateService functionality."""
    print("\n=== Jinja Template Service Demo ===")

    # Create a temporary directory for templates
    with tempfile.TemporaryDirectory() as temp_dir:
        template_dir = Path(temp_dir)

        # Create a simple test template
        test_template_content = """
Hello {{ name }}!
Number: {{ value | format_test }}
"""
        test_template_path = template_dir / "test.html"
        test_template_path.write_text(test_template_content.strip())

        # Initialize the service
        service = JinjaTemplateService(template_dir)

        # Create mock utility services
        class MockFormatter:
            def format_test(self, value):
                return f"formatted_{value}"

        utility_services = {
            'test_formatter': MockFormatter(),
        }

        # Add custom filter
        env = service.setup_jinja_env(utility_services)
        service.add_custom_filter('format_test', utility_services['test_formatter'].format_test)

        print(f"Template service initialized: {service.is_initialized()}")
        print(f"Available templates: {service.list_templates()}")
        print(f"Template 'test.html' exists: {service.template_exists('test.html')}")

        # Test template rendering
        context = {'name': 'World', 'value': 42}
        rendered = service.render_template('test.html', context)
        print(f"\nRendered template:")
        print(rendered)

        # Test string rendering
        string_template = "Quick test: {{ msg | upper }}"
        service.add_custom_filter('upper', str.upper)
        string_result = service.render_string(string_template, {'msg': 'hello'})
        print(f"\nString template result: {string_result}")


def demo_integration():
    """Demonstrate how services work together."""
    print("\n=== Integration Demo ===")

    # Initialize all services
    brain_service = BrainRegionService()
    citation_service = CitationService()
    partner_service = PartnerAnalysisService()

    # Add some test data
    brain_service.add_brain_region("ME", "Medulla")
    brain_service.add_brain_region("LO", "Lobula")

    citation_service.add_citation("Paper1", "10.1234/test", "Test Paper")

    # Simulate a workflow
    print("Simulated Page Generation Workflow:")

    # 1. Process ROI data
    roi_names = ["ME(R)", "LO(L)", "UNKNOWN"]
    print("1. Processing ROI names:")
    for roi in roi_names:
        processed = brain_service.roi_abbr_filter(roi)
        print(f"   {roi} -> {processed}")

    # 2. Process citations
    citations = ["Paper1", "NonExistent"]
    print("\n2. Processing citations:")
    for citation in citations:
        link = citation_service.create_citation_link(citation)
        print(f"   {citation} -> {link[:50]}{'...' if len(link) > 50 else ''}")

    # 3. Analyze connectivity
    connectivity_data = {
        'upstream': {'Tm1_L': [1, 2, 3], 'Tm1_R': [4, 5]},
        'downstream': {'T4_L': [6, 7, 8]}
    }

    partners = [{'type': 'Tm1', 'soma_side': 'L'}, 'T4']
    print("\n3. Analyzing partner connectivity:")
    for partner in partners:
        if isinstance(partner, dict):
            direction = 'upstream'
        else:
            direction = 'downstream'
            partner = {'type': partner}

        body_ids = partner_service.get_partner_body_ids(partner, direction, connectivity_data)
        print(f"   {partner} ({direction}) -> {len(body_ids)} connections")

    print("\nAll services working together successfully!")


def main():
    """Run all demonstrations."""
    print("Phase 1 Refactoring - Service Extraction Demonstration")
    print("=" * 60)

    try:
        demo_brain_region_service()
        demo_citation_service()
        demo_partner_analysis_service()
        demo_jinja_template_service()
        demo_integration()

        print("\n" + "=" * 60)
        print("✅ Phase 1 demonstration completed successfully!")
        print("\nKey Achievements:")
        print("• Extracted 5 specialized services from PageGenerator")
        print("• Each service has focused responsibility")
        print("• Services can be tested independently")
        print("• Services can be reused in different contexts")
        print("• Maintained backward compatibility")
        print("• Improved error handling and logging")

    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
