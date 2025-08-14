# Neuron Type Search Functionality

This document describes the client-side neuron type search and autocomplete functionality that has been implemented for the quickpage project.

## Overview

The neuron search feature provides a real-time, client-side search interface that allows users to quickly find and navigate to specific neuron type pages. The search functionality is integrated into the header of each page and provides intelligent autocomplete suggestions.

## Features

- **Real-time search**: Suggestions appear as you type
- **Build-time generation**: Neuron types embedded during page generation from queue.yaml
- **Intelligent ranking**: Exact matches first, then starts-with, then contains
- **Keyboard navigation**: Arrow keys, Enter, and Escape support
- **Smart file detection**: Automatically finds the correct HTML file for each neuron type
- **Highlighted matches**: Search terms are highlighted in suggestions
- **Responsive design**: Works on desktop and mobile devices

## Files

### JavaScript
- `static/js/neuron-search.js` - Main search functionality

### CSS
- `static/css/neuron-page.css` - Contains search dropdown styles (added to existing file)

### HTML Templates
- `templates/sections/header.html` - Updated to include search script

### Data Sources
- `.queue/queue.yaml` - Primary data source for neuron types
- Fallback discovery from existing HTML files
- Built-in fallback list of common neuron types

### Demo
- `demo-search.html` - Standalone demo page for testing

## How It Works

### 1. Build-time Data Embedding
The search functionality embeds neuron types at build time during the `generate` or `pop` commands:

1. **Primary**: `.queue/queue.yaml` file
   ```yaml
   neuron_types:
     - Dm1
     - Dm2
     - LC4
     - ...
   ```

2. **Fallback**: Built-in fallback list
   - Contains common optic lobe neuron types
   - Used when queue.yaml is empty or unavailable

3. **Generation**: Creates `static/js/neuron-search.js` with embedded data
   - Only generated if the file doesn't exist
   - Contains neuron types as JavaScript constants
   - No runtime data loading required

### 2. Search Algorithm
- Filters neuron types based on user input
- Ranks results by relevance:
  1. Exact matches
  2. Names starting with search term
  3. Names containing search term
- Limits to 10 results for performance
- Case-insensitive matching

### 3. Navigation
When a user selects a neuron type, the system:
- Tests multiple filename patterns:
  - `NeuronType.html`
  - `neurontype.html`
  - `NeuronType_both.html`
  - `neurontype_both.html`
  - `NeuronType_all.html`
  - `neurontype_all.html`
- Navigates to the first existing file
- Falls back to the first pattern if none exist

## Usage

### For End Users

1. **Basic Search**:
   - Click in the search box in the header
   - Start typing a neuron type name
   - Select from dropdown suggestions

2. **Keyboard Navigation**:
   - `↓` / `↑`: Navigate through suggestions
   - `Enter`: Select highlighted suggestion
   - `Escape`: Close dropdown

### For Developers

#### Initialize Search
```javascript
// Automatic initialization on page load
// Search binds to element with id 'menulines'

// Manual initialization
const search = new NeuronSearch('custom-input-id');
```

#### Refresh Data
```javascript
// Reload neuron types from data sources
window.neuronSearch.refresh();
```

#### Access Search Data
```javascript
// Get loaded neuron types
const types = window.neuronSearch.neuronTypes;

// Get current filtered results
const filtered = window.neuronSearch.filteredTypes;
```

## Populating the Queue

To populate the `.queue/queue.yaml` file and generate the search functionality:

### Using the CLI
```bash
# Fill queue with all available neuron types
pixi run quickpage fill-queue --all

# Fill queue with specific neuron type
pixi run quickpage fill-queue --neuron-type Dm4

# Fill queue with multiple options
pixi run quickpage fill-queue --all --soma-side both --output-dir output
```

### Manual Creation
Create `.queue/queue.yaml`:
```yaml
neuron_types:
  - Dm1
  - Dm2
  - Dm3
  - Dm4
  - LC4
  - LC6
  - LPLC1
  - LPLC2
  # ... add more types
updated_at: "2024-01-15T10:30:00"
created_at: "2024-01-15T10:30:00"
count: 73
```

Then generate pages to create the neuron-search.js:
```bash
# Generate any page to create the search file
pixi run quickpage generate --neuron-type Dm4
```

## Configuration

### CSS Customization
Modify search styles in `static/css/neuron-page.css`:

```css
/* Search input styling */
#menulines {
    min-width: 200px;
    padding: 8px 12px;
    /* ... other styles */
}

/* Dropdown styling */
.neuron-search-dropdown {
    max-height: 200px;
    /* ... other styles */
}

/* Item styling */
.neuron-search-item:hover {
    background-color: #f0f8ff;
    color: #0066cc;
}
```

### JavaScript Configuration
```javascript
// The search is automatically initialized with embedded data
// Access the search instance
const search = window.neuronSearch;

// Override navigation behavior
search.navigateToNeuronType = function(neuronType) {
    // Custom navigation logic
    window.location.href = `custom-path/${neuronType}.html`;
};
```

## File Naming Conventions

The search system expects HTML files to follow these naming patterns:
- `NeuronType.html` (exact case match)
- `neurontype.html` (lowercase)
- `NeuronType_both.html` (with soma side)
- `neurontype_both.html` (lowercase with soma side)
- `NeuronType_all.html` (all soma sides)
- `neurontype_all.html` (lowercase all soma sides)

## Testing

### Demo Page
Open `demo-search.html` in a browser to test the functionality:
- Shows search status and loaded neuron types
- Demonstrates all search features
- Safe navigation (shows alerts instead of navigating)

### Manual Testing
1. Verify data loading from different sources
2. Test search with various inputs
3. Check keyboard navigation
4. Verify file detection and navigation
5. Test responsive design on mobile

## Browser Compatibility

- **Modern browsers**: Full functionality
- **IE11+**: Basic functionality (may need polyfills for fetch API)
- **Mobile browsers**: Touch-friendly interface

## Performance

- **Client-side only**: No server requests during search
- **Build-time embedding**: No runtime data loading
- **Instant initialization**: Data already available in JavaScript
- **Efficient filtering**: Optimized string matching
- **Limited results**: Maximum 10 suggestions shown
- **Minimal overhead**: Small JavaScript footprint

## Troubleshooting

### Search Not Working
1. Check browser console for errors
2. Verify `neuron-search.js` is loaded
3. Confirm input element has correct ID (`menulines`)
4. Check CSS is applied correctly

### No Neuron Types Loaded
1. Verify `.queue/queue.yaml` exists in the project
2. Check that neuron-search.js was generated during build
3. Ensure the NEURON_TYPES_DATA constant is populated
4. Regenerate by running a generate or pop command

### Navigation Issues
1. Verify HTML files exist with expected naming
2. Check file permissions and accessibility
3. Test different naming patterns
4. Verify JavaScript navigation logic

## Future Enhancements

- **Advanced filtering**: By brain region, cell count, etc.
- **Search history**: Remember recent searches
- **Fuzzy matching**: Handle typos and partial matches
- **Categories**: Group neuron types by function/location
- **Thumbnails**: Show neuron images in dropdown
- **Real-time updates**: Regenerate search data when queue changes
- **Compressed data**: Optimize embedded data size for large datasets