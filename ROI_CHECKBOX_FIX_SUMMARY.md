# ROI Checkbox Fix for Combined Pages

## Problem Summary

The ROI innervation tables on combined (C) pages were not displaying checkboxes, preventing users from toggling ROI regions in the neuroglancer view. The L, R, and M pages worked correctly, but C pages showed only static ROI names without interactive checkboxes.

## Root Cause Analysis

The issue occurred because:

1. **ROI Name Transformation**: The ROI combination service merges L/R entries (e.g., "ME(L)" + "ME(R)") into single combined entries (e.g., "ME") for display on C pages.

2. **Neuroglancer Mapping Failure**: The neuroglancer JavaScript functions expected specific sided ROI names (e.g., "ME(L)", "ME(R)") to map them to neuroglancer segment IDs, but the combined ROI names (e.g., "ME") had no direct mapping.

3. **Missing Checkbox Logic**: The checkbox system couldn't handle combined ROI entries that needed to toggle multiple neuroglancer segments simultaneously.

## Solution Implementation

### 1. Enhanced Neuroglancer ROI Mapping

**File**: `templates/static/js/neuroglancer-url-generator.js.jinja`

**Changes**:
- Added `findSidedRoiIds(baseName)` function to map combined ROI names to their sided neuroglancer IDs
- Added `findSidedVncIds(baseName)` function for VNC regions
- Enhanced `roiNameToId()` and `vncNameToId()` to return arrays of IDs for combined ROIs
- Updated all ROI handling functions to work with both single IDs and ID arrays

**Example Mapping**:
```javascript
// Combined ROI "ME" maps to both sided IDs
findSidedRoiIds("ME") → ["3", "4"]  // ME(L) and ME(R)
findSidedRoiIds("LO") → ["15", "16"]  // LO(L) and LO(R)
```

### 2. Updated Checkbox Event Handling

**Changes**:
- Modified `syncRoiCheckboxes()` to store ROI ID arrays in checkbox data attributes
- Updated `wireRoiCheckboxes()` to handle multiple ROI IDs per checkbox
- Enhanced event handlers to toggle all sided ROIs when a combined checkbox is clicked

**Checkbox Interaction Flow**:
1. User clicks "ME" checkbox on C page
2. System retrieves ROI IDs `["3", "4"]` from checkbox data
3. Both ME(L) and ME(R) are toggled in neuroglancer simultaneously
4. Visual feedback updates for all related regions

### 3. ROI Combination Service Integration

**File**: `src/quickpage/services/roi_combination_service.py`

**Functionality**:
- Merges L/R ROI entries for combined pages while preserving individual side data for L/R/M pages
- Handles multiple ROI naming patterns: `ME(L)`, `ME_L`, `ME(R)_layer_1`, etc.
- Recalculates percentages based on combined synapse counts
- Provides side mapping utilities for neuroglancer integration

### 4. Template Context Updates

**File**: `src/quickpage/services/template_context_service.py`

**Integration**:
- ROI combination service is automatically applied for combined pages
- Individual side pages remain unchanged
- Neuroglancer data includes both original and combined ROI mappings

## Technical Details

### ROI Naming Pattern Support

The fix handles multiple ROI naming conventions:
- `ME(L)`, `ME(R)` → `ME`
- `LO_L`, `LO_R` → `LO`
- `AME_L_layer_1`, `AME_R_layer_1` → `AME_layer_1`
- `CRE(L)_col_2`, `CRE(R)_col_2` → `CRE_col_2`

### Neuroglancer Integration

**Combined ROI Behavior**:
- Single checkbox controls multiple neuroglancer segments
- Visual feedback shows all related brain regions
- Consistent with user expectations for bilateral structures

**Individual Page Behavior**:
- L/R/M pages remain unchanged
- Original checkbox functionality preserved
- No performance impact on existing functionality

## Testing

### Automated Tests
- ✅ ROI combination logic verified
- ✅ Neuroglancer mapping functions tested
- ✅ Checkbox interaction simulation passed
- ✅ Template includes all required features

### Expected User Experience
1. **Combined Pages (C)**: Single checkboxes for combined ROIs (e.g., "ME") that toggle both sides in neuroglancer
2. **Individual Pages (L/R/M)**: Separate checkboxes for each side (e.g., "ME(L)", "ME(R)") - unchanged behavior
3. **Neuroglancer Integration**: Proper highlighting of all relevant brain regions when checkboxes are toggled

## Files Modified

### Primary Changes
- `templates/static/js/neuroglancer-url-generator.js.jinja` - Enhanced ROI mapping and checkbox handling
- `src/quickpage/services/roi_combination_service.py` - ROI merging logic (already existed)
- `src/quickpage/services/template_context_service.py` - Service integration (already existed)

### Test Files Added
- `simple_roi_test.py` - Validation of ROI combination logic
- `test_neuroglancer_template.py` - Template feature verification

## Deployment Notes

1. **Automatic Regeneration**: Static neuroglancer JavaScript files are regenerated automatically when pages are built
2. **Backward Compatibility**: No changes to existing L/R/M page behavior
3. **Performance**: Minimal overhead, only affects combined pages
4. **Browser Support**: Uses standard JavaScript features, compatible with all modern browsers

## Future Enhancements

1. **Visual Feedback**: Consider adding visual indicators to show which ROIs are bilateral vs unilateral
2. **Batch Operations**: Could extend to support "select all bilateral ROIs" functionality
3. **Custom Groupings**: Framework could support custom ROI groupings beyond L/R combinations

## Validation

To verify the fix works correctly:

1. Navigate to a combined (C) neuron type page
2. Scroll to the ROI Innervation section
3. Verify checkboxes appear in the first column next to ROI names
4. Click a checkbox for a bilateral ROI (e.g., "ME", "LO")
5. Confirm both sided regions highlight in the neuroglancer view
6. Verify individual L/R/M pages still work as before

The fix ensures that combined pages now have full ROI checkbox functionality while maintaining backward compatibility with existing individual side pages.