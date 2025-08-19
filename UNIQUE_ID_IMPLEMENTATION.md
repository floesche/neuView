# Unique ID Implementation for Connectivity Tables

## Overview

This document describes the implementation changes made to replace dictionary-based lookup of precise percentage data with array-based access using unique row IDs.

## Problem Statement

Previously, precise percentages for upstream and downstream connections were stored in dictionaries (`uPD` and `dPD`) and matched to table rows via neuron type name. This approach had potential issues with name conflicts and was less efficient.

## Solution

Each table row now has a unique ID containing a number (e.g., `u0`, `u1`, `u2` for upstream; `d0`, `d1`, `d2` for downstream). Precise numbers are stored in arrays, and the precise numbers for each row are accessed via the index extracted from the unique row ID.

## Implementation Details

### 1. Template Changes (`templates/sections/neuron_page_scripts.html`)

**Before:**
```javascript
// Create lookup map for precise upstream connection percentages
var uPD = {};
{% if connectivity.upstream %}{% for partner in connectivity.upstream %}
uPD['{{- partner.get("type", "Unknown") }} ({{- partner.get("soma_side", "") -}})'] = {{- partner.get("percentage", 0) | round(5) -}};
{% endfor %}{% endif %}

// Create lookup map for precise downstream connection percentages
var dPD = {};
{% if connectivity.downstream %}{% for partner in connectivity.downstream %}
dPD['{{- partner.get("type", "Unknown") }} ({{- partner.get("soma_side", "") -}})'] = {{- partner.get("percentage", 0) | round(5) -}};
{% endfor %}{% endif %}
```

**After:**
```javascript
// Create arrays for precise upstream connection percentages with unique IDs
var upstreamPreciseData = [];
{% if connectivity.upstream %}{% for partner in connectivity.upstream %}
upstreamPreciseData[{{ loop.index0 }}] = {{- partner.get("percentage", 0) | round(5) -}};
{% endfor %}{% endif %}

// Create arrays for precise downstream connection percentages with unique IDs
var downstreamPreciseData = [];
{% if connectivity.downstream %}{% for partner in connectivity.downstream %}
downstreamPreciseData[{{ loop.index0 }}] = {{- partner.get("percentage", 0) | round(5) -}};
{% endfor %}{% endif %}
```

### 2. HTML Template Changes (`templates/sections/connectivity.html`)

**Before:**
```html
<tr>
    <td><strong>{{- partner.get('type', 'Unknown') | neuron_link(partner.get('soma_side')) | safe -}}</strong></td>
    ...
</tr>
```

**After:**
```html
<!-- Upstream table rows -->
<tr id="u{{ loop.index0 }}">
    <td><strong>{{- partner.get('type', 'Unknown') | neuron_link(partner.get('soma_side')) | safe -}}</strong></td>
    ...
</tr>

<!-- Downstream table rows -->
<tr id="d{{ loop.index0 }}">
    <td><strong>{{- partner.get('type', 'Unknown') | neuron_link(partner.get('soma_side')) | safe -}}</strong></td>
    ...
</tr>
```

### 3. JavaScript Function Changes (`static/js/neuron-page.js`)

**Before:**
```javascript
function calculateUpstreamCumulativePercentages(table, percentageCol, cumulativeCol, uPD) {
    var cumulativeSum = 0;
    table.rows({ order: "current", search: "applied" }).every(function (rowIdx) {
        var data = this.data();
        var roiName = data[0].replace(/<[^>]*>/g, ""); // Remove HTML tags from ROI name
        var preciseValue = uPD[roiName] || 0;
        // ... rest of function
    });
}
```

**After:**
```javascript
function calculateUpstreamCumulativePercentages(table, percentageCol, cumulativeCol, upstreamPreciseData) {
    var cumulativeSum = 0;
    table.rows({ order: "current", search: "applied" }).every(function (rowIdx) {
        var rowNode = this.node();
        var rowId = rowNode.id;
        
        // Extract index from row ID (format: u0, u1, u2, etc.)
        var index = parseInt(rowId.substring(1));
        
        var preciseValue = upstreamPreciseData[index] || 0;
        // ... rest of function
    });
}
```

## Row ID Format

- **Upstream connections**: `u0`, `u1`, `u2`, ..., `u{n}`
- **Downstream connections**: `d0`, `d1`, `d2`, ..., `d{n}`

Where `{n}` corresponds to the zero-based index in the respective data array.

## Index Extraction

The JavaScript code extracts the numeric index from the row ID using:
```javascript
var index = parseInt(rowId.substring(1));
```

This extracts everything after the first character (`u` or `d`) and converts it to an integer.

## Benefits

1. **Performance**: Array access by index is faster than dictionary lookup by string key
2. **Reliability**: Eliminates potential issues with neuron type name conflicts or special characters
3. **Simplicity**: Clear numeric indexing system that's easy to understand and debug
4. **Scalability**: Works efficiently with large numbers of connections (e.g., i1, i2, ..., i800, ...)

## Data Flow

1. **Template Generation**: Jinja2 templates generate unique row IDs and populate arrays
2. **HTML Rendering**: Table rows are created with unique IDs (`u0`, `u1`, etc.)
3. **JavaScript Processing**: Functions extract index from row ID and access array data
4. **Cumulative Calculation**: Precise percentages are used for accurate cumulative calculations

## Example

For a neuron with 3 upstream connections:

**Generated JavaScript:**
```javascript
var upstreamPreciseData = [];
upstreamPreciseData[0] = 25.3456;
upstreamPreciseData[1] = 18.7891;
upstreamPreciseData[2] = 12.4567;
```

**Generated HTML:**
```html
<tr id="u0"><!-- LC10 (R) --></tr>
<tr id="u1"><!-- Tm3 (L) --></tr>
<tr id="u2"><!-- Mi1 (R) --></tr>
```

**JavaScript Access:**
```javascript
// For row with id="u1"
var index = parseInt("u1".substring(1)); // index = 1
var preciseValue = upstreamPreciseData[1]; // 18.7891
```

## Backward Compatibility

This change maintains the same visual output and functionality while improving the underlying data access mechanism. No user-facing changes are visible.

## Testing

The implementation has been tested with the `test_unique_ids.py` script, which verifies:
- Unique ID generation
- Index extraction from row IDs
- Array-based data access
- Cumulative percentage calculations
- Template output simulation

All tests pass successfully, confirming the implementation works as expected.