# Layer Analysis Container Restructure

## Overview

The Layer-Based ROI Analysis has been restructured from a single table format to a 6-container layout for improved data visualization and analysis. This change provides a more intuitive and organized view of synapse data across different brain regions and layers.

## Changes Made

### 1. Data Structure Reorganization

**Before**: Single table with columns:
- Region (ME, LO, LOP, central brain, LA, AME)
- Soma Side (L, R, Both)
- Layer (1, 2, 3, etc., or "—" for non-layer regions)
- Pre-synapses
- Post-synapses
- Total

**After**: 6 separate containers arranged in 3 rows, each with regions/layers as columns and pre/post as rows:

**Row 1**: LA + ME Layers (50/50 split)
- **LA Container** - Single column (LA), two rows (Pre, Post) with row headers
- **ME Layers Container** - Multiple columns (ME 1, ME 2, ME 3, ...), two rows (Pre, Post) without row headers

**Row 2**: LO + AME (50/50 split)  
- **LO Layers Container** - Multiple columns (LO 1, LO 2, LO 3, ...), two rows (Pre, Post) with row headers
- **AME Container** - Single column (AME), two rows (Pre, Post) without row headers

**Row 3**: LOP + Central Brain (50/50 split)
- **LOP Layers Container** - Multiple columns (LOP 1, LOP 2, ...), two rows (Pre, Post) with row headers  
- **Central Brain Container** - Single column (central brain), two rows (Pre, Post) without row headers

### 2. Code Changes

#### Python Backend (`src/quickpage/page_generator.py`)

- **Modified `_analyze_layer_roi_data` method**: Added container organization logic
- **New container data structure**: Creates 6 predefined containers with proper column headers
- **Enhanced layer detection**: Extracts layer information from both dataset queries and actual data
- **Improved data aggregation**: Handles multiple neurons and consolidates data by container type
- **Backwards compatibility**: Maintains original `layers` array for any legacy dependencies

#### HTML Template (`templates/neuron_page.html`)

- **Replaced single table**: Removed large layer analysis table
- **Added 6 container layout in 3 rows**: 
  - Row 1: LA + ME Layers (50/50 split using col-md-6)
  - Row 2: LO Layers + AME (50/50 split using col-md-6)
  - Row 3: LOP Layers + Central Brain (50/50 split using col-md-6)
- **Selective row headers**: Removed "Pre"/"Post" row headers from ME, AME, and Central Brain containers
- **Added legend**: Explanatory note that first row = Pre-synapses, second row = Post-synapses
- **New CSS styling**: Added `.layer-analysis-container` class for consistent styling
- **Responsive design**: Uses flexbox grid system for proper layout on different screen sizes

#### CSS Styling

```css
.layer-analysis-container {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    margin-bottom: 1rem;
    border: 1px solid #e5e7eb;
    height: 100%;
}
```

### 3. Data Flow

1. **Input**: ROI counts DataFrame with layer-pattern ROIs (ME|LO|LOP)_[LR]_layer_\<number>
2. **Processing**: 
   - Extract layer information and aggregate by neuron
   - Query dataset for all available layers
   - Consolidate central brain ROIs
   - Organize data into 6 container structures
3. **Output**: Container object with columns and pre/post data for each container type

### 4. Container Structure

```python
containers = {
    'la': {
        'columns': ['LA'],
        'data': {
            'pre': {'LA': <synapse_count>},
            'post': {'LA': <synapse_count>}
        }
    },
    'me': {
        'columns': ['ME 1', 'ME 2', 'ME 3', ...],
        'data': {
            'pre': {'ME 1': <count>, 'ME 2': <count>, ...},
            'post': {'ME 1': <count>, 'ME 2': <count>, ...}
        }
    },
    # ... similar for lo, lop, ame, central_brain
}
```

## Benefits

### 1. Improved Data Visualization
- **Clear separation**: Each brain region type has its own dedicated container
- **Intuitive layout**: Layers are columns, synapse types are rows
- **Reduced clutter**: No more mixed layer and non-layer entries in one table
- **Balanced presentation**: 3-row layout prevents any single container from dominating

### 2. Better User Experience
- **Easier scanning**: Users can quickly find specific regions or layers
- **Logical grouping**: Related containers are paired (LA with ME, LO with AME, LOP with Central Brain)
- **Cleaner tables**: Removed redundant row headers where context makes them unnecessary
- **Visual hierarchy**: Related data is grouped together with clear spatial organization

### 3. Enhanced Analysis
- **Layer comparison**: Easy to compare synapse counts across layers within a region
- **Region comparison**: Clear distinction between different brain region types  
- **Data completeness**: Shows all available layers, even with zero connections
- **Space efficiency**: 50/50 layout maximizes screen real estate usage

## Testing

Comprehensive testing was performed including:

- **Unit tests**: Container data structure validation
- **Integration tests**: Complete pipeline from data analysis to HTML generation  
- **Edge case testing**: Empty data, single layers, non-layer-only data
- **HTML validation**: Verification of all container sections and data presence
- **Data accuracy**: Validation of synapse count aggregation and consolidation

All tests passed successfully, confirming the restructure works correctly while maintaining data integrity and backwards compatibility.

## Migration Notes

### For Users
- The Layer-Based ROI Analysis section now appears as 6 separate containers arranged in 3 rows instead of one table
- Layout: Row 1 (LA + ME), Row 2 (LO + AME), Row 3 (LOP + Central Brain)
- Some containers no longer show "Pre"/"Post" row labels (ME, AME, Central Brain) but a legend explains the row meanings
- All the same data is available, just organized differently
- No changes to underlying data analysis or calculations

### For Developers
- The original `layers` array is still available in the analysis result for backwards compatibility
- New `containers` object provides the structured data for the new layout
- HTML template uses the new container structure but falls back gracefully if needed

## Files Modified

1. `src/quickpage/page_generator.py` - Added container organization logic
2. `templates/neuron_page.html` - Replaced table with 6-container layout
3. Added CSS styling for `.layer-analysis-container` class

## Validation

The restructure has been validated to:
- ✅ Preserve all original data and calculations
- ✅ Handle all edge cases (empty data, single layers, etc.)
- ✅ Generate proper HTML with all expected sections
- ✅ Maintain responsive design across screen sizes
- ✅ Work with existing dataset adapters and ROI strategies
- ✅ Implement correct 3-row layout with proper container pairing
- ✅ Remove row headers appropriately while maintaining data clarity

This restructure provides a more intuitive and organized way to view layer-based ROI analysis data with a balanced 3-row layout that maximizes screen space efficiency while maintaining full backwards compatibility and data integrity.