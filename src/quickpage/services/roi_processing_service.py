"""
ROI Processing Service for QuickPage.

This service handles ROI name cleaning and hierarchy operations that were
previously part of the PageGenerationService.
"""

import logging

logger = logging.getLogger(__name__)


class ROIProcessingService:
    """Service for handling ROI name cleaning and hierarchy operations."""

    def __init__(self, cache_manager=None):
        """Initialize ROI processing service.

        Args:
            cache_manager: Optional cache manager for ROI hierarchy data
        """
        self.cache_manager = cache_manager

    def clean_roi_name(self, roi_name: str) -> str:
        """Remove (R) and (L) suffixes from ROI names."""
        import re
        # Remove (R), (L), or (M) suffixes from ROI names
        cleaned = re.sub(r'\s*\([RLM]\)$', '', roi_name)
        return cleaned.strip()

    def get_roi_hierarchy_parent(self, roi_name: str, connector=None) -> str:
        """Get the parent ROI of the given ROI from the hierarchy."""
        try:
            # Load ROI hierarchy from cache or fetch if needed
            hierarchy_data = None
            if self.cache_manager:
                hierarchy_data = self.cache_manager.load_roi_hierarchy()

            if not hierarchy_data and connector:
                # Fallback to fetching from database using existing connector
                hierarchy_data = connector._get_roi_hierarchy()

            if not hierarchy_data:
                return ""

            # Clean the ROI name first (remove (R), (L), (M) suffixes)
            cleaned_roi = self.clean_roi_name(roi_name)

            # Search recursively for the ROI and its parent
            parent = self.find_roi_parent_recursive(cleaned_roi, hierarchy_data)
            return parent if parent else ""

        except Exception as e:
            logger.debug(f"Failed to get parent ROI for {roi_name}: {e}")
            return ""

    def find_roi_parent_recursive(self, roi_name: str, hierarchy: dict, parent_name: str = "") -> str:
        """Recursively search for ROI in hierarchy and return its parent."""
        for key, value in hierarchy.items():
            # Direct match
            if key == roi_name:
                return parent_name

            # Handle ROI naming variations:
            # - Remove side suffixes: "AOTU(L)*" -> "AOTU"
            # - Remove asterisks: "AOTU*" -> "AOTU"
            cleaned_key = key.replace('(L)', '').replace('(R)', '').replace('(M)', '').replace('*', '').strip()
            if cleaned_key == roi_name:
                return parent_name

            # Also check if the ROI name matches the beginning of the key
            if key.startswith(roi_name) and (len(key) == len(roi_name) or key[len(roi_name)] in '(*'):
                return parent_name

            # Recursive search
            if isinstance(value, dict):
                result = self.find_roi_parent_recursive(roi_name, value, key)
                if result:
                    return result
        return ""

    def filter_roi_summary(self, roi_summary_full, threshold: float = 1.5, max_rois: int = 5):
        """Filter ROIs by threshold and clean names."""
        cleaned_roi_summary = []
        seen_names = set()

        for roi in roi_summary_full:
            if roi['pre_percentage'] >= threshold or roi['post_percentage'] >= threshold:
                cleaned_name = self.clean_roi_name(roi['name'])
                if cleaned_name and cleaned_name not in seen_names:
                    cleaned_roi_summary.append({
                        'name': cleaned_name,
                        'total': roi['total'],
                        'pre_percentage': roi['pre_percentage'],
                        'post_percentage': roi['post_percentage']
                    })
                    seen_names.add(cleaned_name)

                    if len(cleaned_roi_summary) >= max_rois:
                        break

        return cleaned_roi_summary
