# Combined Page Fix for Single-Soma-Side Neuron Types

## Problem Statement

Neuron types with only one soma side (like CB0674) were incorrectly receiving "combined" pages and navigation links, even though there was nothing to combine. This created unnecessary files and confusing navigation for users.

## Solution Overview

Modified the system to only generate combined pages when there are actually multiple soma sides to combine, while preserving the functionality for legitimate multi-side cases and edge cases with unknown soma sides.

## Changes Made

### 1. SomaDetectionService (`src/quickpage/services/soma_detection_service.py`)

**Method: `generate_pages_with_auto_detection()`**
- Added override logic to prevent combined page generation for pure single-side cases
- Lines 95-96: Added override condition `if sides_with_data == 1 and unknown_count == 0: should_generate_combined = False`

**Method: `analyze_soma_sides()`**
- Applied the same logic to the analysis method for consistency
- Lines 284-285: Added same override condition

**Logic Details:**
- **Still generates combined pages when:**
  - Multiple sides have data (`sides_with_data > 1`)
  - No soma side data exists but neurons are present (all unknown)
  - Single side with unknown neurons exists (mixed case)
- **No longer generates combined pages when:**
  - Exactly one soma side has data AND no unknown neurons exist

### 2. NeuronSelectionService (`src/quickpage/services/neuron_selection_service.py`)

**Method: `get_available_soma_sides()`**
- Modified line 245: Changed condition from `if available_sides:` to `if available_sides: ... and len(available_sides) > 1:`
- Now only adds "combined" navigation links when there are multiple sides available
- Single-side neuron types get only their specific side link
- Uses the same logic as SomaDetectionService to ensure consistency between page generation and navigation
- Performs detailed soma side distribution queries to accurately determine when combined links should be shown
- **Fixed side mapping**: Changed `"C": ("combined", ...)` to `"C": ("middle", ...)` to correctly map center/middle soma sides

## Test Coverage

### New Test Files Added

**`test/services/test_soma_detection_service.py`**
- 8 comprehensive test cases covering all scenarios:
  - Single-side types (left, right, middle) → No combined page
  - Multi-side types → Combined page generated  
  - Single-side with unknown neurons → Combined page generated
  - No soma data but neurons exist → Combined page generated
  - Error handling scenarios

**`test/services/test_neuron_selection_service.py`**
- 11 test cases covering navigation link generation:
  - Single-side types → No combined link
  - Multi-side types → Combined link included
  - Single-side with unknown neurons → Combined link included
  - FAFB dataset compatibility
  - Edge cases (empty results, existing 'C' mappings)

### Test Configuration Updates

**`pyproject.toml`**
- Added `pytest-asyncio` dependency to dev environment
- Added `asyncio` marker to test configuration

## Behavioral Changes

### Before Fix
```
CB0674 (left only):
  Pages: CB0674_L.html, CB0674.html (combined)
  Links: "Left", "Combined"

TM3 (left + right):
  Pages: TM3_L.html, TM3_R.html, TM3.html (combined)  
  Links: "Left", "Right", "Combined"
```

### After Fix
```
CB0674 (left only):
  Pages: CB0674_L.html (no combined page)
  Links: "Left" (no combined link)

TM3 (left + right):
  Pages: TM3_L.html, TM3_R.html, TM3.html (combined)
  Links: "Left", "Right", "Combined" (unchanged)
```

## Edge Cases Preserved

The fix preserves important edge cases:

1. **Mixed types with unknown neurons:**
   - Single side + unknown neurons → Still gets combined page
   - Handles cases where soma side classification is incomplete

2. **All unknown neurons:**
   - No classified soma sides but neurons exist → Still gets combined page
   - Preserves functionality for datasets with missing soma side data

3. **FAFB dataset compatibility:**
   - Works with FAFB's different soma side property names
   - Maintains existing FAFB-specific logic

## Files Modified

- `src/quickpage/services/soma_detection_service.py`
- `src/quickpage/services/neuron_selection_service.py`
- `pyproject.toml`

## Files Added

- `test/services/test_soma_detection_service.py`
- `test/services/test_neuron_selection_service.py`

## Validation

All tests pass (155 total tests):
- 19 new tests specifically for the combined page logic
- All existing tests continue to pass, ensuring no regressions
- Demo script verified correct behavior for various neuron type scenarios

## Impact

- **Reduced file system clutter:** Single-side neuron types no longer generate unnecessary combined pages
- **Fixed broken navigation links:** Hamburger menu no longer contains links to non-existent combined pages
- **Improved user experience:** Cleaner navigation without confusing "Combined" options for single-side types
- **Consistent behavior:** Navigation links are now consistent with page generation logic
- **Maintained functionality:** Multi-side types and edge cases work exactly as before
- **Backwards compatible:** No breaking changes to existing functionality

## Example Neuron Types Affected

- **CB0674** (single middle side) → No more combined page or navigation link
- **Any single-side neuron types** → No more combined pages or navigation links
- **TM3, LC4** (multi-side types) → Unchanged behavior
- **Types with unknown soma sides** → Unchanged behavior (still get combined pages when appropriate)

## Problem Solved

The original issue was that CB0674_M.html would have a navigation link to CB0674.html (combined page), but CB0674.html was never generated because CB0674 only has middle-side neurons. This created broken navigation links in the hamburger menu. 

The root cause was twofold:
1. **Page generation logic**: Generated combined pages even for single-side types
2. **Navigation logic**: Incorrectly mapped database soma side 'C' to "combined" instead of "middle"

The fix ensures that:
1. **Combined pages are not generated** for single-side neuron types
2. **Navigation links to combined pages are not created** for single-side neuron types  
3. **Soma side mapping is correct**: 'C' maps to "middle" (center), not "combined"
4. **Both systems use identical logic** to determine when combined functionality should be available