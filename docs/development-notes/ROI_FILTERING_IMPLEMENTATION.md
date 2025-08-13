# ROI Filtering Implementation

## Overview

This document describes the implementation of primary ROI filtering and soma side filtering for the QuickPage ROI innervation table using `neuprint.queries.fetch_roi_hierarchy(mark_primary=True)`.

## Background

Previously, the QuickPage tool had two major issues with ROI innervation tables:

1. **All ROIs displayed**: The table showed all ROIs, which could be overwhelming and include many non-scientifically relevant regions
2. **Soma side cross-contamination**: All pages for a neuron type (regardless of soma side) showed identical ROI data aggregated from all neurons, meaning LC10_L.html and LC10_R.html would show the same table including both left and right hemisphere ROIs

The requirements were to:
- Filter the ROI table to show only **primary ROIs** as determined by the NeuPrint database
- Ensure each page only shows ROI data from neurons belonging to that specific soma side

## Implementation

### Core Changes

The main changes were made to the `_get_primary_rois` method in `quickpage/src/quickpage/page_generator.py`:

```python
def _get_primary_rois(self, connector):
    """Get primary ROIs based on dataset type and available data."""
    primary_rois = set()

    # First, try to get primary ROIs from NeuPrint if we have a connector
    if connector and hasattr(connector, 'client') and connector.client:
        try:
            from neuprint.queries import fetch_roi_hierarchy
            import neuprint
            original_client = neuprint.default_client
            neuprint.default_client = connector.client

            # Get ROI hierarchy with primary ROIs marked with stars
            roi_hierarchy = fetch_roi_hierarchy(mark_primary=True)
            neuprint.default_client = original_client

            if roi_hierarchy is not None:
                # Extract all ROI names from the hierarchical dictionary structure
                extracted_rois = self._extract_roi_names_from_hierarchy(roi_hierarchy)

                # Filter for ROIs that have a star (*) and remove the star for display
                for roi_name in extracted_rois:
                    if roi_name.endswith('*'):
                        # Remove the star and add to primary ROIs set
                        clean_roi_name = roi_name.rstrip('*')
                        primary_rois.add(clean_roi_name)

        except Exception as e:
            print(f"Warning: Could not fetch primary ROIs from NeuPrint: {e}")
    
    # ... fallback logic remains unchanged ...
```

A new helper method `_extract_roi_names_from_hierarchy` was added to handle the complex nested dictionary structure:

```python
def _extract_roi_names_from_hierarchy(self, hierarchy, roi_names=None):
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
        # Add all dictionary keys as potential ROI names
        for key in hierarchy.keys():
            if isinstance(key, str):
                roi_names.add(key)

        # Recursively process all dictionary values
        for value in hierarchy.values():
            self._extract_roi_names_from_hierarchy(value, roi_names)

    elif isinstance(hierarchy, (list, tuple)):
        # Process each item in the list/tuple
        for item in hierarchy:
            self._extract_roi_names_from_hierarchy(item, roi_names)

    return roi_names
```

### How It Works

1. **Fetch ROI Hierarchy**: Calls `fetch_roi_hierarchy(mark_primary=True)` to get the complete ROI hierarchy as a nested dictionary structure with primary ROIs marked with a star (`*`).

2. **Extract ROI Names**: Uses `_extract_roi_names_from_hierarchy()` to recursively traverse the nested dictionary structure and extract all ROI names from dictionary keys at every level of nesting.

3. **Filter Primary ROIs**: Iterates through all extracted ROI names and identifies those that end with `*`.

4. **Clean ROI Names**: Strips the star suffix from ROI names before adding them to the primary ROIs set for display.

5. **Fallback Logic**: If the NeuPrint query fails or returns no data, the system falls back to dataset-specific hardcoded lists of primary ROIs.

### Hierarchical Structure Handling

The `fetch_roi_hierarchy(mark_primary=True)` function returns a complex nested dictionary structure like:

```python
{
    'CX*': {                    # Central Complex - Primary
        'PB*': {               # Protocerebral Bridge - Primary
            'PB(L)*': {},      # Left PB - Primary
            'PB(R)*': {},      # Right PB - Primary
            'glomerulus': {    # Not primary
                'PB_glom_1': {},
                'PB_glom_2': {}
            }
        },
        'FB*': {               # Fan-shaped Body - Primary
            'FB_upper*': {},   # Primary
            'FB_lower*': {},   # Primary
            'FB_columns': {    # Not primary
                'FB_col_1': {},
                'FB_col_2': {}
            }
        }
    },
    'OL(R)*': {               # Right Optic Lobe - Primary
        'ME(R)*': {           # Medulla Right - Primary
            'M1*': {},        # Primary
            'M2*': {},        # Primary
            'M4': {}          # Not primary
        }
    }
}
```

The recursive extraction function traverses all levels of this nested structure and collects ROI names from dictionary keys, regardless of nesting depth.

### Integration with Existing System

The filtered primary ROIs are used in the updated `_aggregate_roi_data` method, which now also filters by soma side:

```python
def _aggregate_roi_data(self, roi_counts_df, neurons_df, soma_side, connector=None):
    """Aggregate ROI data across neurons matching the specific soma side to get total pre/post synapses per ROI (primary ROIs only)."""
    if roi_counts_df is None or roi_counts_df.empty or neurons_df is None or neurons_df.empty:
        return []

    # Filter ROI data to include only neurons that belong to this specific soma side
    if 'bodyId' in neurons_df.columns and 'bodyId' in roi_counts_df.columns:
        # Get bodyIds of neurons that match this soma side
        soma_side_body_ids = set(neurons_df['bodyId'].values)
        # Filter ROI counts to include only these neurons
        roi_counts_soma_filtered = roi_counts_df[roi_counts_df['bodyId'].isin(soma_side_body_ids)]
    else:
        # Fall back to using all ROI data if bodyId columns not available
        roi_counts_soma_filtered = roi_counts_df

    # Get dataset-aware primary ROIs
    primary_rois = self._get_primary_rois(connector)

    # Filter ROI counts to include only primary ROIs
    if len(primary_rois) > 0:
        roi_counts_filtered = roi_counts_soma_filtered[roi_counts_soma_filtered['roi'].isin(primary_rois)]
    else:
        # If no primary ROIs available, return empty
        return []
    
    # ... aggregation logic continues ...
```

### Soma Side Filtering

A major improvement was added to ensure each page only shows ROI data from neurons belonging to the specific soma side:

```python
# In generate_page_from_neuron_type method:
roi_summary = self._aggregate_roi_data(
    neuron_data.get('roi_counts'),
    neuron_data.get('neurons'),        # Pass neurons DataFrame
    neuron_type_obj.soma_side,         # Pass specific soma side
    connector
)
```

This ensures that:
- `LC10_L.html` only shows ROI data from left-side LC10 neurons
- `LC10_R.html` only shows ROI data from right-side LC10 neurons  
- `LC10_M.html` only shows ROI data from middle/central LC10 neurons
- `LC10.html` (general page) shows aggregated data appropriately

### HTML Template Integration

The ROI innervation table in `templates/neuron_page.html` remains unchanged and continues to use the `roi_summary` data:

```html
<!-- ROI Innervation - Full width -->
{% if roi_summary and roi_summary|length > 0 %}
<section>
    <h2>ROI Innervation</h2>
    <div class="data-table">
        <table>
            <thead>
                <tr>
                    <th>ROI Name</th>
                    <th style="text-align: right;">Pre-synapses</th>
                    <th style="text-align: right;">Post-synapses</th>
                    <th style="text-align: right;">Total Synapses</th>
                </tr>
            </thead>
            <tbody>
                {% for roi in roi_summary %}
                <tr>
                    <td>{{ roi.name }}</td>
                    <td style="text-align: right;">{{ roi.pre|format_number }}</td>
                    <td style="text-align: right;">{{ roi.post|format_number }}</td>
                    <td style="text-align: right;"><strong>{{ roi.total|format_number }}</strong></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</section>
{% endif %}
```

## Benefits

1. **Scientific Accuracy**: Only scientifically relevant primary ROIs are displayed.
2. **Dataset Awareness**: Uses the authoritative NeuPrint database to determine primary ROIs.
3. **Hierarchical Structure Support**: Handles complex nested ROI hierarchies from any NeuPrint dataset.
4. **Complete Coverage**: Extracts ROI names from all levels of nesting in the hierarchy.
5. **Soma Side Specificity**: Each page shows ROI data only from neurons belonging to that specific soma side.
6. **Hemisphere Separation**: Left and right hemisphere pages show distinct, relevant ROI patterns.
7. **Cleaner Display**: ROI names are displayed without the star suffix for better readability.
8. **Robust Fallback**: Maintains dataset-specific fallbacks if NeuPrint queries fail.
9. **No Breaking Changes**: Existing templates and CLI interfaces remain unchanged.

## Dataset Support

The implementation supports all major NeuPrint datasets:
- **Optic Lobe**: `optic-lobe:v1.1`
- **CNS**: `cns:v1.0` 
- **Hemibrain**: `hemibrain:v1.2.1`

Each dataset has its own fallback list of primary ROIs if the NeuPrint query fails.

## Error Handling

- Gracefully handles cases where `fetch_roi_hierarchy` is not available
- Falls back to dataset-specific ROI lists if NeuPrint queries fail
- Logs warnings for debugging without breaking the page generation process
- Returns empty ROI table rather than failing completely if no primary ROIs can be determined

## Testing

The implementation was validated with comprehensive tests covering:
- ROI hierarchy fetching and star filtering logic
- Hierarchical dictionary structure traversal at multiple nesting levels
- Mixed data structures (dictionaries, lists, nested combinations)
- Edge cases (empty hierarchies, non-string keys, None inputs)
- **Soma side filtering and cross-contamination prevention**
- **BodyId-based neuron filtering for ROI aggregation**
- **Hemisphere-specific ROI table generation**
- Integration with PageGenerator methods
- Data aggregation with filtered ROIs
- Fallback behavior for different datasets

All tests pass successfully, confirming the implementation correctly handles complex nested structures, properly filters by soma side, and works as expected across various scenarios.

### Test Results Summary

The comprehensive test suite validates:
- ✅ **Primary ROI filtering**: Only ROIs marked with `*` are included
- ✅ **Hierarchical extraction**: ROI names extracted from all nesting levels
- ✅ **Soma side isolation**: Left neurons only contribute to left pages, etc.
- ✅ **Cross-contamination prevention**: No leakage between hemisphere pages
- ✅ **Edge case handling**: Empty data, missing columns, no matches handled gracefully

## Future Considerations

- Consider adding caching for ROI hierarchy queries to improve performance
- Monitor NeuPrint API changes that might affect `fetch_roi_hierarchy`
- Potentially add configuration options to override primary ROI determination
- Could extend to support custom ROI filtering rules per research project
- Consider adding depth limits for extremely deep hierarchies if needed
- Potential optimization for very large ROI hierarchies with thousands of regions
- **Add support for bilateral neuron types** that span both hemispheres
- **Consider adding soma side statistics** to show distribution across hemispheres
- **Potential for soma side-specific connectivity analysis** in future versions

## Impact on User Experience

### Before Implementation
- ROI tables were identical across all soma side pages for a neuron type
- Tables included non-primary ROIs cluttering the display
- Users couldn't distinguish hemisphere-specific innervation patterns
- Left-side pages showed right-hemisphere ROIs and vice versa

### After Implementation  
- Each soma side page shows distinct, relevant ROI data
- Only primary ROIs are displayed, focusing on scientifically meaningful regions
- Users can compare hemisphere-specific patterns (e.g., LC10_L.html vs LC10_R.html)
- ROI tables accurately reflect the spatial organization of neural circuits
- Cleaner, more focused presentation of neuron type characteristics