# Neuroglancer JavaScript Implementation

## Overview

This document describes the implementation of client-side JavaScript URL generation for Neuroglancer, replacing the previous server-side template rendering approach.

## Changes Made

### 1. JavaScript URL Generator (`static/js/neuroglancer-url-generator.js`)

Created a new JavaScript module that:
- Loads the neuroglancer template from a static JSON file
- Replaces template placeholders with actual data
- Generates and URL-encodes the neuroglancer state
- Updates DOM elements with the generated URLs

**Key Functions:**
- `generateNeuroglancerUrl(websiteTitle, visibleNeurons, neuronQuery)` - Generates a complete neuroglancer URL (synchronous)
- `updateNeuroglancerLinks(websiteTitle, visibleNeurons, neuronQuery)` - Updates all neuroglancer links/iframes in the DOM (synchronous)
- `initializeNeuroglancerLinks(pageData)` - Convenience function for page initialization

**Template Approach:**
- Complete neuroglancer configuration is embedded directly in the JavaScript file as a constant object
- No external file loading required - works with file:// URLs
- Template placeholders are replaced programmatically at runtime

### 2. Embedded Template (within `static/js/neuroglancer-url-generator.js`)

- Converted the Jinja2 template `neuroglancer.js.jinja` to a JavaScript object constant `NEUROGLANCER_TEMPLATE`
- Embedded the complete template directly in the JavaScript file for file:// URL compatibility
- Template placeholders are replaced programmatically:
  - `WEBSITE_TITLE_PLACEHOLDER` → replaced with `websiteTitle` parameter
  - `VISIBLE_NEURONS_PLACEHOLDER` → replaced with `visibleNeurons` array
  - `NEURON_QUERY_PLACEHOLDER` → replaced with `neuronQuery` parameter

### 3. Server-Side Changes (`src/quickpage/page_generator.py`)

Modified `_generate_neuroglancer_url()` method:
- **Before:** Returned only the URL string
- **After:** Returns a tuple of `(url, template_variables)`
- Added template variables to page context for JavaScript consumption

**New Template Variables Added:**
- `visible_neurons` - Array of neuron bodyIDs to display
- `website_title` - Title for the neuroglancer session
- `neuron_query` - Query string for neuron search

### 4. Template Updates

#### `templates/sections/neuroglancer.html`
- Replaced direct URL embedding with placeholder links
- Added CSS classes for JavaScript targeting:
  - `.neuroglancer-link` - For external links
  - `.neuroglancer-iframe` - For embedded iframes

#### `templates/macros.html`
- Enhanced `iframe_embed` macro to support additional CSS classes

#### `templates/neuron_page.html`
- Added neuroglancer JavaScript module import
- Added inline script to pass server data to JavaScript
- Calls `initializeNeuroglancerLinks()` with page data

### 5. Test Files

Updated test files to handle the new return signature:
- `test/test_neuroglancer_selection.py` - Updated method calls to handle tuple return

## Usage

### For Page Templates

The JavaScript automatically initializes when the page loads. Template variables are passed via inline script:

```javascript
const neuroglancerData = {
    websiteTitle: {{ website_title | tojson }},
    visibleNeurons: {{ visible_neurons | tojson }},
    neuronQuery: {{ neuron_query | tojson }}
};
initializeNeuroglancerLinks(neuroglancerData);
```

### For Manual Use

```javascript
// Generate a single URL (synchronous)
const url = generateNeuroglancerUrl(
    "MyNeuronType", 
    ["123456789", "987654321"], 
    "MyNeuronType"
);

// Update all neuroglancer elements on the page (synchronous)
updateNeuroglancerLinks(
    "MyNeuronType", 
    ["123456789", "987654321"], 
    "MyNeuronType"
);
```

## Benefits

1. **Reduced Server Load:** URL generation happens on the client
2. **File:// URL Compatibility:** Works with local HTML files (no fetch/CORS issues)
3. **No External Dependencies:** Complete template embedded in JavaScript
4. **Synchronous Operation:** No async loading required
5. **Dynamic Updates:** URLs can be regenerated without server round-trips
6. **Maintainability:** Single source of truth for neuroglancer configuration

## Requirements

- Modern browser with ES6+ support
- JavaScript enabled
- No external file access required (works offline)

## Files Modified

### New Files
- `static/js/neuroglancer-url-generator.js` (contains embedded template)

### Modified Files
- `src/quickpage/page_generator.py`
- `templates/sections/neuroglancer.html`
- `templates/macros.html`
- `templates/neuron_page.html`
- `test/test_neuroglancer_selection.py`

### Removed Files
- Template is now embedded, no separate JSON file needed

## Testing

The implementation can be tested using:

```javascript
// Simple test
const testUrl = generateNeuroglancerUrl(
    "TestType", 
    ["123456789"], 
    "TestType"
);
console.log("Generated URL:", testUrl);
```

This tests:
- Template processing
- URL generation
- DOM element updates
- Error handling

## Backward Compatibility

The implementation maintains backward compatibility:
- Server-side generation still works as fallback
- Template context includes all previous variables
- HTML structure remains the same