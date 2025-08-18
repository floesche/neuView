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
- `generateNeuroglancerUrl(websiteTitle, visibleNeurons, neuronQuery)` - Generates a complete neuroglancer URL
- `updateNeuroglancerLinks(websiteTitle, visibleNeurons, neuronQuery)` - Updates all neuroglancer links/iframes in the DOM
- `initializeNeuroglancerLinks(pageData)` - Convenience function for page initialization

### 2. Template File (`static/js/neuroglancer-clean-template.json`)

- Converted the Jinja2 template `neuroglancer.js.jinja` to a static JSON file
- Replaced Jinja2 variables with placeholder strings:
  - `{{ website_title }}` → `"WEBSITE_TITLE_PLACEHOLDER"`
  - `{{ visible_neurons | tojson }}` → `"VISIBLE_NEURONS_PLACEHOLDER"`
  - `{{ neuron_query|safe }}` → `"NEURON_QUERY_PLACEHOLDER"`

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
// Generate a single URL
const url = await generateNeuroglancerUrl(
    "MyNeuronType", 
    ["123456789", "987654321"], 
    "MyNeuronType"
);

// Update all neuroglancer elements on the page
await updateNeuroglancerLinks(
    "MyNeuronType", 
    ["123456789", "987654321"], 
    "MyNeuronType"
);
```

## Benefits

1. **Reduced Server Load:** URL generation happens on the client
2. **Better Caching:** Template file can be cached by browsers
3. **Dynamic Updates:** URLs can be regenerated without server round-trips
4. **Maintainability:** Single source of truth for neuroglancer configuration

## Requirements

- Modern browser with ES6+ support (async/await, fetch API)
- JavaScript enabled
- Access to static files

## Files Modified

### New Files
- `static/js/neuroglancer-url-generator.js`
- `static/js/neuroglancer-clean-template.json`

### Modified Files
- `src/quickpage/page_generator.py`
- `templates/sections/neuroglancer.html`
- `templates/macros.html`
- `templates/neuron_page.html`
- `test/test_neuroglancer_selection.py`

## Testing

A test page (`test_neuroglancer.html`) has been created to verify the integration works correctly. It tests:
- Template loading
- URL generation
- DOM element updates
- Error handling

## Backward Compatibility

The implementation maintains backward compatibility:
- Server-side generation still works as fallback
- Template context includes all previous variables
- HTML structure remains the same