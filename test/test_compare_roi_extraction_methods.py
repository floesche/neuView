# Compare Previous and Updated ROI Extraction Methods
# This script demonstrates and compares the previous and updated methods for extracting primary ROIs from the neuprint hierarchy.

# 1. Import Required Libraries and Setup Neuprint Client
import os
from neuprint import Client, fetch_roi_hierarchy

def main():
    # Set up Neuprint Client
    server = 'neuprint-cns.janelia.org'
    dataset = 'cns'
    token = os.environ.get('NEUPRINT_TOKEN')
    connector = Client(server, dataset=dataset, token=token)

    # 2. Define Previous ROI Extraction Method
    def previous_extract_roi_names_from_hierarchy(hierarchy, roi_names=None):
        """
        Recursively extract all ROI names from the hierarchical dictionary structure.
        Args:
            hierarchy: Dictionary or any structure from fetch_roi_hierarchy
            roi_names: Set to collect ROI names (used for recursion)
        Returns:
            Set of all ROI names found in the hierarchy
        """
        if roi_names is None:
            roi_names = set()
        if isinstance(hierarchy, dict):
            for key in hierarchy.keys():
                if isinstance(key, str):
                    roi_names.add(key)
            for value in hierarchy.values():
                previous_extract_roi_names_from_hierarchy(value, roi_names)
        elif isinstance(hierarchy, (list, tuple)):
            for item in hierarchy:
                previous_extract_roi_names_from_hierarchy(item, roi_names)
        return roi_names

    # 3. Define Updated ROI Extraction Method
    def updated_extract_primary_rois(connector):
        """
        Use neuprint's fetch_primary_rois to get primary ROIs.
        Args:
            connector: Neuprint Client
        Returns:
            Set of primary ROI names
        """
        from neuprint.queries import fetch_primary_rois
        return set(fetch_primary_rois())

    # 4. Fetch ROI Hierarchy Data
    roi_hierarchy = fetch_roi_hierarchy(mark_primary=True)

    # 5. Extract ROIs Using Previous Method
    prev_rois = previous_extract_roi_names_from_hierarchy(roi_hierarchy)
    # Filter for ROIs that have a star (*) and remove the star for display
    prev_primary_rois = set()
    for roi_name in prev_rois:
        if roi_name.endswith('*'):
            clean_roi_name = roi_name.rstrip('*')
            prev_primary_rois.add(clean_roi_name)
    print(f"Primary ROIs (previous method): {sorted(prev_primary_rois)}")

    # 6. Extract ROIs Using Updated Method
    updated_primary_rois = updated_extract_primary_rois(connector)
    print(f"Primary ROIs (updated method): {sorted(updated_primary_rois)}")

    # 7. Compare Results of Both Methods
    only_in_previous = prev_primary_rois - updated_primary_rois
    only_in_updated = updated_primary_rois - prev_primary_rois
    in_both = prev_primary_rois & updated_primary_rois
    print(f"Only in previous method: {sorted(only_in_previous)}")
    print(f"Only in updated method: {sorted(only_in_updated)}")
    print(f"In both methods: {sorted(in_both)}")

    # 8. Display Differences and Intersections
    print("\nThe above output shows the ROIs found only by the previous method, only by the updated method, and those found by both.")

if __name__ == "__main__":
    main()
