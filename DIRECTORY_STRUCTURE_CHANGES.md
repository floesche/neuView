# Directory Structure Changes Summary

This document summarizes the changes made to reorganize the quickpage output directory structure.

## Overview

The quickpage application has been updated to organize generated files into a more logical directory structure:

- **Neuron pages** are now generated in `output/types/`
- **Eyemap images** are now stored in `output/eyemaps/`
- **Main pages** (index.html, types.html, help.html) remain in `output/`

## Before and After

### Previous Structure
```
output/
├── index.html
├── types.html
├── help.html
├── Neuron1.html
├── Neuron1_L.html
├── Neuron1_R.html
├── Neuron2.html
├── ...
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│       ├── eyemap1.svg
│       ├── eyemap2.png
│       └── ...
```

### New Structure
```
output/
├── index.html
├── types.html
├── help.html
├── types/
│   ├── Neuron1.html
│   ├── Neuron1_L.html
│   ├── Neuron1_R.html
│   ├── Neuron2.html
│   └── ...
├── eyemaps/
│   ├── eyemap1.svg
│   ├── eyemap2.png
│   └── ...
└── static/
    ├── css/
    ├── js/
    └── ...
```

## Changes Made

### 1. Page Generator (`src/quickpage/page_generator.py`)

- **New directories creation**: Modified `__init__` method to create `types/` and `eyemaps/` subdirectories
- **Neuron page output**: Updated `generate_page()` and `generate_page_from_neuron_type()` to save neuron pages in `types/` subdirectory
- **Template variables**: Added `is_neuron_page: True` to template context for neuron pages

### 2. Hexagon Grid Generator (`src/quickpage/visualization/hexagon_grid_generator.py`)

- **Constructor**: Added `eyemaps_dir` parameter to support custom eyemaps directory
- **File saving**: Updated `_save_svg_file()` and `_save_png_file()` methods to save images in `eyemaps/` directory
- **Relative paths**: Changed returned paths from `static/images/` to `../eyemaps/` for correct relative linking from neuron pages

### 3. Services (`src/quickpage/services.py`)

- **URL generation**: Updated `create_index()` method to generate URLs with `types/` prefix for neuron pages
- **Template data**: Added `is_neuron_page: False` to template context for main pages (index, types, help)

### 4. Templates

#### Header Templates (`templates/sections/header.html` & `templates/sections/simple_header.html`)
- **Conditional paths**: Updated navigation links to use relative paths based on `is_neuron_page` variable
- **JavaScript**: Updated neuron-search.js script path for neuron pages

#### Index Template (`templates/index.html`)
- **Search navigation**: Updated JavaScript search function to look for neuron files in `types/` directory

#### Neuron Search Template (`templates/static/js/neuron-search.js.template`)
- **Fallback navigation**: Updated file detection to check `types/` directory for neuron pages

## Link Behavior

### Navigation Links

| From Page Type | To Page Type | Link Format | Example |
|----------------|--------------|-------------|---------|
| Main pages | Main pages | Direct | `index.html`, `types.html`, `help.html` |
| Main pages | Neuron pages | With prefix | `types/Neuron1.html` |
| Neuron pages | Main pages | With parent | `../index.html`, `../types.html`, `../help.html` |
| Neuron pages | Neuron pages | Direct | `Neuron2.html` (same directory) |

### Resource Links

| From Page Type | To Resource | Link Format | Example |
|----------------|-------------|-------------|---------|
| Main pages | Static files | Direct | `static/js/script.js` |
| Neuron pages | Static files | With parent | `../static/js/script.js` |
| Neuron pages | Eyemaps | With parent | `../eyemaps/image.svg` |

## Template Variable Changes

### New Template Variables

- `is_neuron_page`: Boolean indicating whether the current page is a neuron page
  - `True` for individual neuron pages in `types/` directory
  - `False` for main pages (index, types, help) in root directory

### Usage in Templates

```jinja2
<!-- Navigation links with conditional paths -->
<a href="{{ '../' if is_neuron_page else '' }}index.html">Home</a>
<a href="{{ '../' if is_neuron_page else '' }}types.html">Types List</a>
<a href="{{ '../' if is_neuron_page else '' }}help.html">Help</a>

<!-- JavaScript includes -->
<script src="{{ '../' if is_neuron_page else '' }}static/js/neuron-search.js"></script>
```

## JavaScript Changes

### Search Functionality

The neuron search JavaScript has been updated to:

1. **URL generation**: Generate URLs with `types/` prefix when navigating to neuron pages
2. **File detection**: Check for neuron files in the correct directory structure
3. **Fallback behavior**: Default to `types/` directory for unknown neuron types

### Example JavaScript Changes

```javascript
// Old behavior
window.location.href = `${neuronType}.html`;

// New behavior  
window.location.href = `types/${neuronType}.html`;
```

## Backward Compatibility

The changes maintain backward compatibility in the following ways:

1. **URL structure**: Existing bookmarks to main pages continue to work
2. **API consistency**: The `generate` and `pop` commands work the same way
3. **Configuration**: No changes to configuration files required

## Benefits

1. **Organization**: Cleaner separation between main pages and neuron-specific content
2. **Scalability**: Easier to manage large numbers of neuron pages
3. **Maintenance**: More logical file organization for development and deployment
4. **SEO**: Better URL structure for search engines

## Testing

A test structure has been created in `test_output/` to verify:

- ✅ Directory structure creation
- ✅ Relative path linking
- ✅ JavaScript navigation
- ✅ Image path resolution
- ✅ Template rendering

## Migration Notes

For existing deployments:

1. **File movement**: Existing neuron HTML files need to be moved to `types/` subdirectory
2. **Image relocation**: Existing eyemap images need to be moved from `static/images/` to `eyemaps/`
3. **Link updates**: Any external links to neuron pages need `types/` prefix added
4. **Server configuration**: Web server configurations may need updates for new directory structure

## Commands Affected

Both `generate` and `pop` commands now:

- Create neuron pages in `output/types/`
- Store eyemap images in `output/eyemaps/`
- Generate correct relative links between pages
- Maintain proper navigation functionality