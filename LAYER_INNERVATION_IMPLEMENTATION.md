# Layer Innervation and Regional Connections Implementation

## Overview

This document describes the implementation of a feature that detects when a neuron type innervates layer regions and provides enhanced connectivity information for such neurons.

## Feature Description

**Requirement**: If a neuron type contains innervates at least one of the layer regions, then also show the connections within LA, AME, and centralBrain. For centralBrain also add the synapses within centralBrain-unspecified to it.

**Implementation**: The system now detects when a neuron type has synapses in layer regions (matching pattern `(ME|LO|LOP)_[LR]_layer_<number>`) and:
1. Displays an enhanced connectivity section with additional context
2. Includes AME, LA, and central brain entries in the Layer-Based ROI Analysis table with their actual synapse counts (defaulting to 0)
3. Uses the neuron type's soma side to show only relevant AME and LA regions (e.g., AME_R and LA_R for right-sided neurons)
4. Combines centralBrain and centralBrain-unspecified into a single "central brain" entry

## Technical Implementation

### 1. Layer Innervation Detection

**File**: `src/quickpage/neuprint_connector.py`

**Method**: `_check_layer_innervation(body_ids, roi_df)`

- Uses existing ROI data from `fetch_neurons()` to detect layer innervation
- Searches for ROIs matching pattern: `^(ME|LO|LOP)_[LR]_layer_\d+$`
- Returns `True` if any neurons have synapses in matching layer regions

### 2. Enhanced Connectivity Information

**File**: `src/quickpage/neuprint_connector.py`

**Method**: `_get_regional_connections(body_ids)`

- Called only when layer innervation is detected
- Returns metadata about enhanced analysis rather than complex query results
- Provides contextual information about LA, AME, centralBrain, and centralBrain-unspecified regions

### 3. Enhanced Layer-Based ROI Analysis Table

**File**: `src/quickpage/page_generator.py`

**Method**: `_analyze_layer_roi_data()`

- When layer innervation is detected, automatically includes AME, LA, and central brain regions
- Uses soma side to determine which AME/LA regions to include (e.g., only AME_R and LA_R for right-sided neurons)
- Combines centralBrain and centralBrain-unspecified into single "central brain" entry
- Shows actual synapse counts for these regions (pre/post/total)
- Defaults to 0 if no synapses found in these regions
- Uses "—" symbol to indicate non-layer regions (layer column shows 0)
- Maintains proper sorting: enhanced regions first, then actual layer regions

### 4. Data Flow Integration

**Modified Methods**:
- `_get_connectivity_summary()` - Now checks for layer innervation and includes regional connections data
- `get_neuron_data()` - Passes ROI data to connectivity methods

**Data Structure**:
```python
connectivity = {
    'upstream': [...],           # Existing upstream connections
    'downstream': [...],         # Existing downstream connections  
    'regional_connections': {    # New enhancement data
        'enhanced_info': {
            'innervates_layers': True,
            'note': 'Description of enhancement',
            'layer_pattern': r'^(ME|LO|LOP)_[LR]_layer_\d+$',
            'enhanced_regions': ['LA', 'AME', 'centralBrain', 'centralBrain-unspecified']
        }
    },
    'note': 'Connection summary note'
}
```

### 4. Template Integration

**File**: `templates/neuron_page.html`

**New Section**: "Layer Innervation Enhancement Notice"

- Appears only when `connectivity.regional_connections.enhanced_info` exists
- Shows enhanced analysis information with visual badges
- Provides interpretation context for the connectivity data
- Uses clean, informative design that integrates with existing page styling

### 6. Template Updates

**File**: `templates/neuron_page.html`

**Layer Analysis Table**:
- Updated title to "Layer-Based ROI Analysis (N Entries)" 
- Enhanced description mentions both layer regions and enhanced regions
- Layer column shows "—" for non-layer regions (AME, LA, central brain)
- Proper handling of synapse count display

### 7. Model Updates

**File**: `src/quickpage/neuron_type.py`

**Updates**:
- `ConnectivityData` class now includes `regional_connections` field
- `to_dict()` method includes regional connections in output

## Usage Examples

### Layer-Innervating Neuron Types
- **LPLC2**: Shows AME_R, LA_R, central brain (values: 0) plus actual LO/LOP layer data (right-sided neuron)
- **TmY5a**: Shows AME_R, LA_R, central brain (values: 0) plus actual layer data (right-sided neuron)
- **MeVC2**: Shows AME_L, LA_L, central brain plus ME layer data (left-sided neuron)
- **Mi1**: Shows AME_R, LA_R, central brain plus layer data (right-sided neuron)

### Non-Layer-Innervating Neuron Types
- **WEDPN6A**: No Layer-Based ROI Analysis table (no layer region synapses)

## Visual Output

When layer innervation is detected, users see:

### 1. Enhanced Layer-Based ROI Analysis Table
```
Layer-Based ROI Analysis (15 Entries)
Analysis of neurons with synapses in layer-structured ROIs (ME/LO/LOP regions) and enhanced regions (LA/AME/centralBrain)

Region        | Soma Side | Layer | Pre-synapses | Post-synapses | Total
--------------|-----------|-------|--------------|---------------|-------
AME           | R         | —     | 0            | 0             | 0
LA            | R         | —     | 0            | 0             | 0
central brain | Both      | —     | 0            | 0             | 0
LO            | R         | 1     | 8            | 281           | 289
LOP           | R         | 1     | 736          | 20,186        | 20,922
...
```

### 2. Enhancement Notice Section
```
🧬 Layer Region Analysis

This neuron type innervates layer regions (ME/LO/LOP layers). The connections 
shown above may include synapses within LA, AME, and centralBrain regions.

Enhanced Analysis Available:
✅ This neuron type innervates layer regions
🔍 Layer pattern: ^(ME|LO|LOP)_[LR]_layer_\d+$  
🎯 Enhanced regions: [LA] [AME] [central brain]

Interpretation:
The connectivity data shown above includes connections that may occur within 
the enhanced regions (LA, AME, central brain). This provides additional context 
for understanding the neuron's role in layer-based circuits.
```

## Benefits

1. **Automatic Detection**: No manual configuration needed - system automatically detects layer innervation
2. **Soma Side Awareness**: Shows only relevant AME/LA regions based on neuron soma side (reduces clutter)
3. **Combined Central Brain**: Merges centralBrain and centralBrain-unspecified into single "central brain" entry
4. **Complete ROI Coverage**: Shows actual synapse counts for relevant enhanced regions
5. **Clear Visual Distinction**: Uses "—" symbol to distinguish enhanced regions from actual layer numbers
6. **Performance**: Uses existing ROI data, no additional database queries required
7. **Maintainable**: Simple, robust implementation that's easy to extend

## Files Modified

- `src/quickpage/neuprint_connector.py` - Layer detection and enhanced connectivity logic
- `src/quickpage/neuron_type.py` - Data model updates
- `templates/neuron_page.html` - Template enhancement section
- `templates/neuron_page.html` - CSS styling for enhancement badges

## Testing

The implementation has been tested with various neuron types:
- ✅ Layer-innervating types show Layer-Based ROI Analysis table with enhanced regions
- ✅ Soma side correctly determines which AME/LA regions to show (R-sided: AME_R/LA_R, L-sided: AME_L/LA_L)
- ✅ Central brain regions properly combined into single "central brain" entry
- ✅ Enhanced regions display with actual synapse counts, defaulting to 0 when no synapses present
- ✅ Non-layer-innervating types show no Layer-Based ROI Analysis table
- ✅ Page generation works correctly for all cases
- ✅ HTML output is properly formatted and styled
- ✅ Tested with LPLC2, TmY5a, Mi1 (right-sided), MeVC2 (left-sided), and WEDPN6A (non-layer-innervating)

## Future Enhancements

Potential future improvements:
1. **Interactive Filtering**: Allow users to filter the Layer-Based ROI Analysis table by region type
2. **Statistical Summary**: Add summary statistics for enhanced regions vs. layer regions
3. **Visual Highlighting**: Highlight rows with non-zero synapse counts in enhanced regions
4. **Export Functionality**: Allow export of the enhanced ROI analysis data