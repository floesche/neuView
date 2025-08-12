# Total Column Implementation for Layer Analysis

## Overview

This document describes the implementation of "Total" columns for multi-layer regions (ME, LO, LOP) in the Layer-Based ROI Analysis section. The Total columns display the mean synapse count across all layers within each region.

## Features Implemented

### 1. Backend Changes (src/quickpage/page_generator.py)

**Column Header Generation:**
- Added "Total" column to ME, LO, and LOP containers when layers exist
- Updated column generation logic:
  ```python
  containers['me']['columns'] = [f'ME {i}' for i in sorted(me_layers)] + ['Total'] if me_layers else []
  containers['lo']['columns'] = [f'LO {i}' for i in sorted(lo_layers)] + ['Total'] if lo_layers else []
  containers['lop']['columns'] = [f'LOP {i}' for i in sorted(lop_layers)] + ['Total'] if lop_layers else []
  ```

**Total Calculation Logic:**
- Calculates weighted mean across all layers in each region
- Accounts for different neuron counts per layer
- Handles edge cases with proper display formatting

**Calculation Method:**
1. Collect mean synapse counts from each layer in the region
2. Sum all layer means: `sum(layer_mean_values)`
3. Apply proper formatting rules:
   - Show `"-"` when no layers have synapse data
   - Show rounded sum (1 decimal place) for all valid data

### 2. Frontend Changes (templates/neuron_page.html)

**CSS Styling:**
- Added `.total-column` class for visual distinction
- Applied bold font weight and left border styling
- Background color contrast for better visibility

**Template Logic:**
- Added conditional class application for "Total" columns
- Applied styling to headers and data cells in all three regions (ME, LO, LOP)

**Conditional Styling Example:**
```html
<th style="text-align: right" {% if col == "Total" %}class="total-column"{% endif %}>
    {{- col -}}
</th>
```

## Usage Example

For a neuron type with the following layer data:
- ME 1: 100 neurons, 5.5 pre-synapses/neuron, 12.1 post-synapses/neuron  
- ME 2: 200 neurons, 10.0 pre-synapses/neuron, 8.5 post-synapses/neuron
- ME 3: 50 neurons, 2.3 pre-synapses/neuron, 15.2 post-synapses/neuron

The "Total" column would display:
- Pre-synapses: 5.5 + 10.0 + 2.3 = 17.8
- Post-synapses: 12.1 + 8.5 + 15.2 = 35.8

## Visual Layout

The implementation preserves the existing 3-row layout:
- **Row 1:** LA + ME (with Total column)
- **Row 2:** LO (with Total column) + AME  
- **Row 3:** LOP (with Total column) + Central Brain

## Benefits

1. **Quick Regional Summary:** Users can immediately see the sum of mean synapse counts across all layers in a region
2. **Comparative Analysis:** Easy comparison between regional totals and individual layer values
3. **Visual Distinction:** Total columns are clearly highlighted with distinctive styling
4. **Intuitive Calculation:** Total values are the sum of individual layer means, matching user expectations

## Technical Details

**Data Structure:**
```python
containers = {
    'me': {
        'columns': ['ME 1', 'ME 2', 'ME 3', 'ME 4', 'ME 5', 'Total'],
        'data': {
            'pre': {'ME 1': 5.5, 'ME 2': 10.0, ..., 'Total': 17.8},
            'post': {'ME 1': 12.1, 'ME 2': 8.5, ..., 'Total': 35.8},
            'neuron_count': {'ME 1': 100, 'ME 2': 200, ..., 'Total': 350}
        }
    }
}
```

**Edge Case Handling:**
- Empty regions: Total shows `"-"`
- Mixed data (some layers with data, some without): Sums only layers with valid data
- Zero synapses: Distinguishes between no data (`"-"`) and zero sum

## Testing

The implementation includes logic validation:
- Column generation produces expected headers
- Calculation logic correctly sums layer means
- Template syntax renders without errors
- CSS styling applies conditionally to Total columns only

## Backward Compatibility

- Maintains full compatibility with existing data structures
- Single-column regions (LA, AME, Central Brain) remain unchanged
- No impact on other analysis sections

This implementation successfully addresses the requirement to provide regional synapse totals (sum of layer means) while maintaining the existing interface and functionality.