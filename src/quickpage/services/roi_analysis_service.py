"""
ROI Analysis Service

Handles ROI summary analysis for neuron types, including ROI data aggregation
and parent ROI determination.
"""

import logging
from typing import List, Tuple, Dict, Any

logger = logging.getLogger(__name__)


class ROIAnalysisService:
    """Service for analyzing ROI data and generating summaries for neuron types."""

    def __init__(self, page_generator, roi_hierarchy_service):
        self.page_generator = page_generator
        self.roi_hierarchy_service = roi_hierarchy_service

    def get_roi_summary_for_neuron_type(self, neuron_type: str, connector, skip_roi_analysis=False) -> Tuple[List[Dict[str, Any]], str]:
        """Get ROI summary for a specific neuron type."""
        # Skip expensive ROI analysis if requested for faster indexing
        if skip_roi_analysis:
            return [], ""

        try:
            # Get neuron data for all sides
            neuron_data = connector.get_neuron_data(neuron_type, soma_side='combined')

            roi_counts = neuron_data.get('roi_counts')
            neurons = neuron_data.get('neurons')

            if (not neuron_data or
                roi_counts is None or roi_counts.empty or
                neurons is None or neurons.empty):
                return [], ""

            # Use the page generator's ROI aggregation method
            roi_summary = self.page_generator._aggregate_roi_data(
                neuron_data.get('roi_counts'),
                neuron_data.get('neurons'),
                'combined',
                connector
            )

            # Filter ROIs by threshold and clean names
            # Only show ROIs with ≥1.5% of either input (post) or output (pre) connections
            # This ensures only significant innervation targets are displayed
            threshold = 1.5  # Percentage threshold for ROI significance
            cleaned_roi_summary = []
            seen_names = set()

            for roi in roi_summary:
                # Only include ROIs that pass the 1.5% threshold for input OR output
                if roi['pre_percentage'] >= threshold or roi['post_percentage'] >= threshold:
                    cleaned_name = self.roi_hierarchy_service._clean_roi_name(roi['name'])
                    if cleaned_name and cleaned_name not in seen_names:
                        cleaned_roi_summary.append({
                            'name': cleaned_name,
                            'total': roi['total'],
                            'pre_percentage': roi['pre_percentage'],
                            'post_percentage': roi['post_percentage']
                        })
                        seen_names.add(cleaned_name)

                        if len(cleaned_roi_summary) >= 5:  # Limit to top 5
                            break

            # Get parent ROI for the highest ranking (first) ROI
            parent_roi = ""
            if cleaned_roi_summary:
                highest_roi = cleaned_roi_summary[0]['name']
                parent_roi = self.roi_hierarchy_service.get_roi_hierarchy_parent(highest_roi, connector)

            return cleaned_roi_summary, parent_roi

        except Exception as e:
            # If there's any error fetching ROI data, return empty list and parent
            logger.warning(f"Failed to get ROI summary for {neuron_type}: {e}")
            return [], ""

    def collect_filter_options_from_index_data(self, index_data: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Collect filter options from neuron data for the index page."""
        roi_options = set()
        region_options = set()
        nt_options = set()
        superclass_options = set()
        class_options = set()
        subclass_options = set()
        dimorphism_options = set()

        for entry in index_data:
            # Collect ROIs from roi_summary
            if entry.get('roi_summary'):
                for roi_info in entry['roi_summary']:
                    if isinstance(roi_info, dict) and 'name' in roi_info:
                        roi_name = roi_info['name']
                        if roi_name and roi_name.strip():
                            roi_options.add(roi_name.strip())

            # Collect regions from parent_roi
            if entry.get('parent_roi') and entry['parent_roi'].strip():
                # Clean region name by removing side suffixes
                clean_parent_roi = self.roi_hierarchy_service._clean_roi_name(entry['parent_roi'].strip())
                if clean_parent_roi:
                    region_options.add(clean_parent_roi)

            # Collect neurotransmitters
            if entry.get('consensus_nt') and entry['consensus_nt'].strip():
                nt_options.add(entry['consensus_nt'].strip())
            elif entry.get('celltype_predicted_nt') and entry['celltype_predicted_nt'].strip():
                nt_options.add(entry['celltype_predicted_nt'].strip())

            # Collect class hierarchy
            if entry.get('cell_superclass') and entry['cell_superclass'].strip():
                superclass_options.add(entry['cell_superclass'].strip())
            if entry.get('cell_class') and entry['cell_class'].strip():
                class_options.add(entry['cell_class'].strip())
            if entry.get('cell_subclass') and entry['cell_subclass'].strip():
                subclass_options.add(entry['cell_subclass'].strip())

            # Collect dimorphism
            if entry.get('dimorphism') and entry['dimorphism'].strip():
                dimorphism_options.add(entry['dimorphism'].strip())

        # Sort filter options
        sorted_roi_options = sorted(roi_options)
        sorted_region_options = sorted(region_options)
        # Put 'Other' at the end if it exists
        if 'Other' in sorted_region_options:
            sorted_region_options.remove('Other')
            sorted_region_options.append('Other')

        return {
            'rois': sorted_roi_options,
            'regions': sorted_region_options,
            'neurotransmitters': sorted(nt_options),
            'superclasses': sorted(superclass_options),
            'classes': sorted(class_options),
            'subclasses': sorted(subclass_options),
            'dimorphisms': sorted(dimorphism_options)
        }

    def calculate_cell_count_ranges(self, index_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate cell count ranges using fixed values for filtering."""
        cell_count_ranges = []
        if index_data:
            # Extract all cell counts
            cell_counts = [entry['total_count'] for entry in index_data if entry.get('total_count', 0) > 0]

            if cell_counts:
                # Define fixed ranges: 1, 2, 3, 4, 5, 6-10, 10-50, 50-100, 100-500, 500-1000, 1000-2000, 2000-5000, >5000
                fixed_ranges = [
                    {'lower': 1, 'upper': 1, 'label': '1', 'value': '1-1'},
                    {'lower': 2, 'upper': 2, 'label': '2', 'value': '2-2'},
                    {'lower': 3, 'upper': 3, 'label': '3', 'value': '3-3'},
                    {'lower': 4, 'upper': 4, 'label': '4', 'value': '4-4'},
                    {'lower': 5, 'upper': 5, 'label': '5', 'value': '5-5'},
                    {'lower': 6, 'upper': 10, 'label': '6-10', 'value': '6-10'},
                    {'lower': 10, 'upper': 50, 'label': '10-50', 'value': '10-50'},
                    {'lower': 50, 'upper': 100, 'label': '50-100', 'value': '50-100'},
                    {'lower': 100, 'upper': 500, 'label': '100-500', 'value': '100-500'},
                    {'lower': 500, 'upper': 1000, 'label': '500-1000', 'value': '500-1000'},
                    {'lower': 1000, 'upper': 2000, 'label': '1000-2000', 'value': '1000-2000'},
                    {'lower': 2000, 'upper': 5000, 'label': '2000-5000', 'value': '2000-5000'},
                    {'lower': 5001, 'upper': float('inf'), 'label': '>5000', 'value': '5001-999999'}
                ]

                # Only include ranges that contain actual data
                for range_def in fixed_ranges:
                    has_data = any(
                        range_def['lower'] <= count <= range_def['upper']
                        for count in cell_counts
                    )
                    if has_data:
                        cell_count_ranges.append(range_def)

        return cell_count_ranges
