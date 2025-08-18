# Balance Index Enhancement

## Overview

This enhancement improves the Summary Statistics section of neuron pages by ensuring consistent display of complete neuron type information across all soma side pages, enhanced with detailed hemisphere breakdown and a newly calculated balance index.

## Changes Made

### Template Modifications

**File:** `quickpage/templates/sections/summary_stats.html`

- Replaced filtered neuron counts with complete neuron type statistics in summary cards
- All soma side pages (AOTU019_L, AOTU019_R, AOTU019_both) now show identical neuron type totals
- Added inline display of complete left and right soma side counts
- Implemented balance index calculation from complete neuron type data
- Added robust handling for edge cases (None values, zero counts)

### Key Features

1. **Consistent Total Neurons Card:**
   - Shows complete neuron type count (not filtered by soma side)
   - Displays complete left and right soma side counts inline
   - Shows calculated balance index with 2 decimal precision
   - Identical across all soma side pages (AOTU019_L, AOTU019_R, AOTU019_both)

2. **Consistent Side Cards:**
   - Left Side card shows complete left hemisphere count
   - Right Side card shows complete right hemisphere count
   - Same values displayed regardless of which soma side page is viewed

3. **Balance Index Calculation:**
   - Formula: `(left_count - right_count) / (left_count + right_count)`
   - Range: -1.0 to 1.0
   - Values:
     - `0.0`: Equal left and right counts
     - `1.0`: All neurons on left side
     - `-1.0`: All neurons on right side
     - Intermediate values indicate bias toward left (positive) or right (negative)

4. **Edge Case Handling:**
   - Handles `None` values for left_count or right_count
   - Shows "Soma side information not available" when appropriate
   - Gracefully handles zero counts while maintaining total count display

### Visual Example

Before (AOTU019_L page showed only left neurons):
```
┌─────────────────┬─────────────────┬─────────────────┐
│       12        │        12       │        0        │
│ Total Neurons   │   Left Side     │  Right Side     │
└─────────────────┴─────────────────┴─────────────────┘
```

After (ALL AOTU019 pages show complete type statistics):
```
┌─────────────────┬─────────────────┬─────────────────┐
│       25        │        12       │       13        │
│ Total Neurons   │   Left Side     │  Right Side     │
│ Left: 12 | Right: 13 │                 │                 │
│ Balance: -0.04  │                 │                 │
└─────────────────┴─────────────────┴─────────────────┘
```

### Implementation Details

- **Complete Type Statistics:** All summary cards show statistics for the entire neuron type, regardless of soma side filter
- **Cross-Page Consistency:** AOTU019_L, AOTU019_R, and AOTU019_both pages show identical summary statistics
- **Selective Data Usage:** Summary cards use complete data, analysis sections use filtered data
- **Calculation Logic:** Safe division with zero-check to prevent division by zero
- **Display Format:** Two decimal places for balance index (e.g., "0.40", "-0.04")
- **Styling:** Maintains existing stat-card styling with additional smaller text for details
- **Responsive:** Works with existing responsive grid system

### Edge Cases Handled

1. **Equal Counts:** `left=5, right=5` → Balance: `0.00`
2. **All Left:** `left=10, right=0` → Balance: `1.00`
3. **All Right:** `left=0, right=10` → Balance: `-1.00`
4. **None Values:** `left=None, right=None` → Shows "Soma side information not available"
5. **Zero Counts:** `left=0, right=0, total=10` → Shows "Soma side information not available"
6. **Cross-Page Consistency:** AOTU019_L and AOTU019_R show identical statistics

### Testing

A comprehensive test suite was created and validated:
- Balance index calculation accuracy
- Complete summary vs filtered summary functionality  
- Cross-page consistency (AOTU019_L, AOTU019_R, AOTU019_both showing identical totals)
- Individual card consistency (Left Side, Right Side cards show complete counts)
- Selective data usage (summary cards use complete, analysis uses filtered)
- Edge case handling
- Template rendering
- HTML structure validation
- Filter compatibility

All tests passed successfully, confirming the implementation works correctly across all scenarios.

### Documentation Updates

- Updated `quickpage/templates/README.md` to reflect the new functionality
- Added description of enhanced total neurons card with balance index feature
- Updated enhancement documentation with complete summary functionality

## Benefits

1. **Enhanced Information Density:** More useful information in the same space
2. **Bilateral Assessment:** Quick visual assessment of left/right hemisphere distribution
3. **Quantitative Balance:** Precise numerical indicator of neuron distribution bias
4. **Complete Cross-Page Consistency:** All soma side pages show identical neuron type statistics
5. **No Confusion:** Clear distinction between complete type data vs filtered analysis data
6. **Complete Context:** Users always see total neuron type information regardless of page
7. **Intuitive Navigation:** Consistent reference data across all related pages
8. **Backward Compatibility:** Maintains all existing functionality and styling
9. **Robust Error Handling:** Gracefully handles missing or incomplete soma side data

## Implementation Details

### Code Changes

**NeuPrint Connector (`src/quickpage/neuprint_connector.py`):**
- Added calculation of `complete_summary` from unfiltered neuron data
- Both filtered `summary` and `complete_summary` are returned in the data structure
- Complete summary always represents the entire neuron type statistics

**Page Generator (`src/quickpage/page_generator.py`):**
- Updated template context to include `complete_summary` 
- Both `generate_page` and `generate_page_from_neuron_type` methods pass complete summary to templates

**Template (`templates/sections/summary_stats.html`):**
- Total Neurons card uses `complete_summary` for total count and hemisphere breakdown
- Left Side and Right Side cards use `complete_summary` for consistent counts
- Balance index calculated from complete neuron type left/right counts
- Pre-synapses card continues to use filtered `summary` for soma side-specific data

### Data Flow

1. **Raw Data Fetch:** Complete neuron type data retrieved from NeuPrint
2. **Filtering:** Data filtered by soma side for specific analyses  
3. **Dual Summary:** Both filtered and complete summaries calculated
4. **Template Context:** Both summaries passed to template
5. **Selective Display:** Summary cards use complete, analysis sections use filtered
6. **Consistent Display:** All soma side pages show identical summary statistics

## Future Enhancements

Potential improvements to consider:
- Color coding for balance index (red for right bias, blue for left bias)
- Tooltip explanations for balance index interpretation
- Visual indicators (progress bars) for balance representation
- Integration with other hemisphere-related analyses
- Visual highlighting when viewing soma side subset vs complete type
- Breadcrumb indication showing "Complete Type View" vs "Filtered Analysis"
- Summary consistency indicators across related pages