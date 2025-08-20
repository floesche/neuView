# Neuron Search Implementation Summary

## Overview

The `create-list` command has been enhanced to automatically generate and update the `neuron-search.js` file based on the HTML files discovered during index creation. This provides intelligent autocomplete and navigation functionality for neuron types with support for different soma sides (Left, Right, Middle, Both).

## What Was Implemented

### 1. Enhanced Index Service

**File:** `quickpage/src/quickpage/services.py`

- Modified `IndexService.create_index()` method to call `_generate_neuron_search_js()` after creating the index
- Added new private method `_generate_neuron_search_js()` that:
  - Scans discovered neuron types and their available HTML files
  - Creates structured data with URLs for each neuron type and soma side
  - Generates JavaScript file using Jinja2 template
  - Ensures proper directory structure (`static/js/`) is created

### 2. Enhanced JavaScript Template

**File:** `quickpage/templates/static/js/neuron-search.js.template`

**Key improvements:**
- Added `NEURON_DATA` constant with detailed neuron information including available URLs
- Enhanced dropdown display to show available soma sides (L, R, M, Both)
- Improved navigation logic with direct URL mapping instead of file detection
- Added new methods:
  - `navigateToNeuronType()` - Uses known URLs for direct navigation
  - `navigateToNeuronTypeWithDetection()` - Fallback method for unknown files
  - `getNeuronUrls()` - Returns available URLs for a neuron type
  - `navigateToSomaSide()` - Direct navigation to specific soma side pages

### 3. Generated JavaScript Structure

The generated `neuron-search.js` file contains:

```javascript
// Simple array for basic search functionality
const NEURON_TYPES_DATA = ["LC10", "Mi1", "T4a"];

// Detailed data structure with URLs
const NEURON_DATA = [
  {
    "name": "T4a",
    "urls": {
      "both": "T4a.html",
      "left": "T4a_L.html", 
      "right": "T4a_R.html"
    },
    "primary_url": "T4a.html"
  },
  // ... more neuron entries
];
```

## How It Works

### 1. File Discovery Process

During `create-list` execution:

1. Scans output directory for HTML files matching pattern: `([A-Za-z0-9_-]+?)(?:_([LRM]))?\.html`
2. Extracts neuron type names and identifies soma sides:
   - `NeuronType.html` → Both sides
   - `NeuronType_L.html` → Left side
   - `NeuronType_R.html` → Right side  
   - `NeuronType_M.html` → Middle
3. Groups files by neuron type and builds URL mappings

### 2. Search Functionality

**Enhanced Autocomplete:**
- Shows neuron type names with available sides indicator
- Example: "T4a (L, R, Both)" for a neuron with multiple variations
- Maintains existing keyboard navigation and highlighting

**Smart Navigation:**
- Primary URL priority: Both > Left > Right > Middle
- Direct navigation using pre-mapped URLs (no HTTP requests needed)
- Fallback to detection method for edge cases

### 3. Integration Points

**Index Template Integration:**
- `quickpage/templates/types.html` includes `<script src="static/js/neuron-search.js"></script>`
- Search input field has `id="menulines"` for automatic initialization

**Header Template Integration:**
- `quickpage/templates/sections/header.html` also includes the script for other pages

## Usage Examples

### Command Line Usage

```bash
# Generate index with neuron search functionality
python -m quickpage create-list --output-dir /path/to/output

# Uses default output directory from config
python -m quickpage create-list
```

### JavaScript API Usage

```javascript
// Access search instance
const search = window.neuronSearch;

// Get available URLs for a neuron type
const urls = search.getNeuronUrls('T4a');
// Returns: { both: "T4a.html", left: "T4a_L.html", right: "T4a_R.html" }

// Navigate directly to specific soma side
search.navigateToSomaSide('T4a', 'left'); // Goes to T4a_L.html
```

## File Structure

After running `create-list`, the output directory contains:

```
output_directory/
├── index.html                 # Main index page
├── static/
│   └── js/
│       └── neuron-search.js   # Generated search functionality
├── NeuronType.html            # Individual neuron pages
├── NeuronType_L.html          # Left-side specific pages
├── NeuronType_R.html          # Right-side specific pages
└── NeuronType_M.html          # Middle-specific pages
```

## Key Features

### 1. Automatic Generation
- No manual intervention required
- Updates automatically when `create-list` is run
- Reflects current state of HTML files in output directory

### 2. Intelligent Navigation
- Links to "both" pages by default when available
- Shows available soma sides in search results
- Direct URL mapping eliminates network requests during navigation

### 3. Enhanced User Experience
- Visual indicators for available neuron variations
- Consistent with existing search behavior
- Backward compatible with original functionality

## Testing

A comprehensive test was created demonstrating the functionality:

### Test Setup
```bash
# Create test files
touch test_index_output/T4a.html        # Both sides
touch test_index_output/T4a_L.html      # Left only  
touch test_index_output/T4a_R.html      # Right only
touch test_index_output/LC10.html       # Both sides
touch test_index_output/Mi1_M.html      # Middle only

# Generate index
python -m quickpage create-list --output-dir test_index_output
```

### Generated Results
- ✅ JavaScript file created at `static/js/neuron-search.js`
- ✅ Proper JSON structure with neuron data
- ✅ Correct URL mappings for all discovered files
- ✅ Search functionality shows available sides: "T4a (L, R, Both)"

## Technical Details

### Template Processing
- Uses Jinja2 `|safe` filter to prevent HTML encoding of JSON data
- Generation timestamp included in JavaScript comments
- Neuron count displayed in file header

### Error Handling
- Graceful fallback if template or directory creation fails
- Maintains existing behavior if JavaScript generation encounters issues
- Comprehensive error messages in CLI output

### Performance Considerations
- Pre-computed URL mappings eliminate runtime file detection
- JSON data embedded at build time for fast client-side access
- Efficient search algorithm with relevance-based sorting

## Future Enhancements

Potential improvements for future versions:

1. **Advanced Filtering:** Add region/ROI-based search filters
2. **Fuzzy Search:** Implement approximate string matching
3. **Keyboard Shortcuts:** Add hotkeys for quick neuron access
4. **Search History:** Remember recent searches
5. **Deep Linking:** URL parameters for direct search state

## Conclusion

The enhanced `create-list` functionality now provides a complete, automatically-generated neuron search experience that intelligently links users to the appropriate neuron pages based on discovered HTML files. This implementation eliminates manual maintenance while providing superior user experience through smart navigation and visual feedback about available neuron variations.