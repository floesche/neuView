# Checkbox State Refactor - Removal of data-toggle-state Attribute

## Overview

This document describes the refactoring work to remove the redundant `data-toggle-state` attribute from the QuickPage application and replace it with direct checkbox state management.

## Background

Previously, the application used custom `data-toggle-state` attributes on table cells to track the checked/unchecked state of checkboxes within connectivity and ROI tables. This approach was redundant because:

1. **Native checkbox state**: HTML checkboxes already maintain their state via the `checked` property
2. **DataTables preservation**: DataTables preserves DOM elements when hiding/showing rows, so checkbox state is naturally maintained
3. **Code complexity**: Managing both the data attribute and checkbox state created unnecessary complexity and potential for synchronization issues

## Changes Made

### 1. HTML Template Updates

**File: `quickpage/templates/sections/connectivity.html`**
- Removed `data-toggle-state="false"` from upstream connectivity table cells (line 30)
- Removed `data-toggle-state="false"` from downstream connectivity table cells (line 71)

**File: `quickpage/templates/sections/roi_innervation.html`**
- Removed `data-toggle-state="false"` from ROI table cells (line 24)

### 2. JavaScript Updates

**File: `quickpage/static/js/neuroglancer-url-generator.js`**

Removed the following redundant data attribute operations:

- `syncConnectivityCheckboxes()`: Removed `td.dataset.toggleState = allOn.toString()`
- `wireConnectivityCheckboxes()`: Removed `td.dataset.toggleState = checkbox.checked.toString()`
- `syncRoiCheckboxes()`: Removed `td.dataset.toggleState = isSelected.toString()`
- `wireRoiCheckboxes()`: Removed `td.dataset.toggleState = checkbox.checked.toString()`

## How Checkbox State Preservation Works

### DataTables Behavior
DataTables preserves DOM elements when filtering/hiding rows rather than recreating them. This means:
- Checkbox `checked` properties are maintained even when rows are hidden
- No additional state management is required
- The checkbox state automatically persists through table operations

### Direct State Access
The refactored code now uses `checkbox.checked` directly:
```javascript
// Setting checkbox state
checkbox.checked = allOn;

// Reading checkbox state
if (checkbox.checked) {
    // Handle checked state
} else {
    // Handle unchecked state
}
```

### Visual State Management
CSS classes are still used for visual styling:
```javascript
// Apply visual styling based on checkbox state
td.classList.toggle("partner-on", checkbox.checked);
td.classList.toggle("roi-on", checkbox.checked);
```

## Benefits of the Refactor

1. **Simplified Code**: Eliminated redundant state tracking
2. **Reduced HTML Bloat**: Removed unnecessary attributes from templates
3. **Better Maintainability**: Single source of truth for checkbox state
4. **Performance**: Fewer DOM attribute reads/writes
5. **Standards Compliance**: Uses native HTML checkbox behavior

## Testing

A test file (`quickpage/test_checkbox_state.html`) was created to verify that:
- Checkbox states are preserved when DataTables hides/shows rows
- Event handlers work correctly with direct checkbox state access
- Visual styling updates properly based on checkbox state

## Backward Compatibility

This refactor maintains full backward compatibility:
- All existing functionality continues to work
- Neuroglancer link generation remains unchanged
- User interactions behave identically
- No breaking changes to the API

## Future Considerations

With this refactor complete, future checkbox-related features should:
- Use `checkbox.checked` directly instead of data attributes
- Rely on native browser checkbox state management
- Use CSS classes for visual state representation only

This refactor aligns the codebase with web standards and simplifies the state management model while maintaining all existing functionality.