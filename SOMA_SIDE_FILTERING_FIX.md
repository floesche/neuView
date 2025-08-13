# Soma Side Filtering Fix for Layer Analysis

## Problem Description

Previously, the Mean Synapse count per layer table showed ALL dataset layers regardless of the neuron type's soma side. This meant:

- **Tm3 (L)** would show both `ME_L_layer_01` AND `ME_R_layer_01`
- **Tm3 (R)** would show both `ME_L_layer_01` AND `ME_R_layer_01`
- The layer analysis was not consistent with the neuron's soma side

## Solution

Modified the `_analyze_layer_roi_data()` function in `src/quickpage/page_generator.py` to filter layers based on the neuron type's soma side.

### Implementation Details

1. **Added soma side mapping function**:
   ```python
   def get_matching_layer_sides(soma_side):
       if soma_side == 'left':
           return ['L']
       elif soma_side == 'right':
           return ['R']
       elif soma_side == 'both' or soma_side == 'all':
           return ['L', 'R']
       else:
           # Default to both sides if soma_side is unclear
           return ['L', 'R']
   ```

2. **Added filtering logic**:
   ```python
   matching_sides = get_matching_layer_sides(soma_side)
   
   for region, side, layer_num in sorted(all_dataset_layers):
       # Skip layers that don't match the soma side
       if side not in matching_sides:
           continue
       # ... rest of processing
   ```

### Behavior After Fix

- **Tm3 (L)**: Shows only `ME_L_layer_01`, `ME_L_layer_02`, etc.
- **Tm3 (R)**: Shows only `ME_R_layer_01`, `ME_R_layer_02`, etc.
- **Tm3 (both)**: Shows both L and R side layers

## Files Modified

- `src/quickpage/page_generator.py`: Added soma side filtering logic in `_analyze_layer_roi_data()` function

## Files Added

- `test_soma_side_filtering.py`: Comprehensive test suite to verify the filtering logic works correctly

## Testing

The fix has been thoroughly tested with:

1. **Unit tests** for the soma side mapping logic
2. **Integration tests** with mock dataset layers
3. **Realistic pattern tests** simulating actual layer data

All tests pass, confirming that:
- ✅ `soma_side='left'` shows only L-side layers
- ✅ `soma_side='right'` shows only R-side layers  
- ✅ `soma_side='both'` shows both L and R side layers
- ✅ Edge cases (empty/None soma_side) default to both sides

## Impact

This fix ensures that the layer analysis table is consistent with the neuron type's soma side, making the data presentation more accurate and meaningful for analysis.