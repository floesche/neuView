# QuickPage Development Guide

This document provides technical implementation details for developers working on the QuickPage neuron visualization system.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Cell Count Filter Implementation](#cell-count-filter-implementation)
- [Tooltip System Implementation](#tooltip-system-implementation)
- [Server-Side Dropdown Population](#server-side-dropdown-population)
- [Filtering System Architecture](#filtering-system-architecture)
- [Frontend JavaScript Architecture](#frontend-javascript-architecture)
- [Data Flow](#data-flow)
- [Performance Considerations](#performance-considerations)
- [Testing Strategy](#testing-strategy)
- [Code Style and Patterns](#code-style-and-patterns)

## Architecture Overview

QuickPage follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│           Frontend (HTML/JS)            │
├─────────────────────────────────────────┤
│         Template Layer (Jinja2)         │
├─────────────────────────────────────────┤
│        Service Layer (Python)           │
├─────────────────────────────────────────┤
│      Data Access Layer (NeuPrint)       │
└─────────────────────────────────────────┘
```

### Key Components

- **IndexService**: Orchestrates index page generation with batch processing
- **PageGenerator**: Handles individual neuron page generation
- **NeuPrintConnector**: Manages database connections and queries
- **Template System**: Jinja2 templates with custom filters and server-side rendering

## Cell Count Filter Implementation

### Backend Implementation (services.py)

The cell count filter uses 10th percentile-based ranges calculated server-side:

```python
# Calculate cell count ranges using 10th percentiles
cell_count_ranges = []
if index_data:
    import numpy as np
    # Extract all cell counts
    cell_counts = [entry['total_count'] for entry in index_data if entry.get('total_count', 0) > 0]

    if cell_counts:
        # Calculate 10th percentiles (0th, 10th, 20th, ..., 100th)
        percentiles = np.percentile(cell_counts, [i * 10 for i in range(11)])

        # Create ranges from the percentiles
        for i in range(len(percentiles) - 1):
            lower = int(np.floor(percentiles[i]))
            upper = int(np.floor(percentiles[i + 1]))

            # Skip ranges where lower == upper (except for the last range)
            if lower < upper or i == len(percentiles) - 2:
                if i == len(percentiles) - 2:  # Last range
                    cell_count_ranges.append({
                        'lower': lower,
                        'upper': upper,
                        'label': f"{lower}-{upper}",
                        'value': f"{lower}-{upper}"
                    })
                else:
                    cell_count_ranges.append({
                        'lower': lower,
                        'upper': upper - 1,  # Make ranges non-overlapping
                        'label': f"{lower}-{upper - 1}",
                        'value': f"{lower}-{upper - 1}"
                    })
```

#### Key Design Decisions

1. **Non-overlapping Ranges**: Each range ends at `upper - 1` to prevent overlap
2. **Percentile-based**: Ensures roughly equal distribution across ranges
3. **Server-side Calculation**: Computed once during index generation for efficiency
4. **Dynamic Ranges**: Automatically adjusts to actual data distribution

### Frontend Implementation (index_page.html)

#### HTML Structure

```html
<div class="col-xs-6 col-sm-2 col-md-2">
  <label for="cell-count-filter" class="filter-label">Cell Count:</label>
  <select id="cell-count-filter" class="filter-dropdown">
    <option value="all">All Counts</option>
    {% for range in filter_options.cell_count_ranges %}
    <option value="{{ range.value }}">{{ range.label }}</option>
    {% endfor %}
  </select>
</div>
```

#### Data Attributes

Each neuron card includes the cell count as a data attribute:

```html
<div class="neuron-card-wrapper" data-cell-count="{{ neuron.total_count if neuron.total_count else 0 }}">
```

#### Interactive Cell Count Tags

```html
<span class="neuron-count-tag clickable-count" data-count="{{ neuron.total_count }}">{{ neuron.total_count }}</span>
```

#### JavaScript Filtering Logic

```javascript
// Check cell count filter
let matchesCellCount = true;
if (selectedCellCount !== 'all') {
  const cardCellCount = parseInt(cardWrapper.data('cell-count')) || 0;
  const [rangeMin, rangeMax] = selectedCellCount.split('-').map(num => parseInt(num));
  matchesCellCount = cardCellCount >= rangeMin && cardCellCount <= rangeMax;
}
```

#### Click Handler with Toggle Behavior

```javascript
// Add click handler for cell count tags to activate/deactivate filter
$(document).on('click', '.clickable-count', function(e) {
  e.preventDefault();
  const cellCount = parseInt($(this).data('count'));
  
  // Find the appropriate range for this cell count
  const cellCountFilter = $('#cell-count-filter');
  const currentFilter = cellCountFilter.val();
  const options = cellCountFilter.find('option');
  
  for (let i = 1; i < options.length; i++) { // Skip "All Counts" option
    const optionValue = $(options[i]).val();
    const [rangeMin, rangeMax] = optionValue.split('-').map(num => parseInt(num));
    
    if (cellCount >= rangeMin && cellCount <= rangeMax) {
      // Toggle behavior: if this range is already selected, deactivate it
      if (currentFilter === optionValue) {
        cellCountFilter.val('all');
      } else {
        cellCountFilter.val(optionValue);
      }
      cellCountFilter.trigger('change');
      break;
    }
  }
});
```

## Tooltip System Implementation

### Core Architecture

The tooltip system provides enhanced hover information while preserving accessibility:

```javascript
function initializeTitleTooltips() {
  // Create tooltip element if it doesn't exist
  var tooltip = document.getElementById('title-tooltip');
  if (!tooltip) {
    tooltip = document.createElement('div');
    tooltip.id = 'title-tooltip';
    tooltip.style.position = 'absolute';
    tooltip.style.backgroundColor = '#999';
    tooltip.style.color = 'white';
    tooltip.style.padding = '5px 10px';
    tooltip.style.borderRadius = '4px';
    tooltip.style.fontSize = '14px';
    tooltip.style.pointerEvents = 'none';
    tooltip.style.zIndex = '9999';
    tooltip.style.display = 'none';
    tooltip.style.maxWidth = '200px';
    tooltip.style.wordWrap = 'break-word';
    document.body.appendChild(tooltip);
  }
```

### Key Features

#### 1. Title Attribute Preservation

```javascript
element.addEventListener('mouseenter', function(e) {
  // Temporarily remove title to suppress default browser tooltip
  var currentTitle = element.getAttribute('title');
  element.removeAttribute('title');
  
  // Show custom tooltip
  tooltip.textContent = currentTitle;
  tooltip.style.display = 'block';
});

element.addEventListener('mouseleave', function() {
  // Restore title attribute
  element.setAttribute('title', tooltipText);
  
  // Hide custom tooltip
  tooltip.style.display = 'none';
});
```

#### 2. Dynamic Positioning

```javascript
var updateTooltipPosition = function(event) {
  var x = event.clientX + window.scrollX;
  var y = event.clientY + window.scrollY;
  tooltip.style.left = (x + 20) + 'px';  // 20px offset to the right
  tooltip.style.top = (y - 10) + 'px';   // 10px offset above
};
```

#### 3. Dynamic Content Support

The tooltip system automatically reinitializes after DOM changes:

```javascript
function applyFilters() {
  rebuildFilteredView();
  setTimeout(function() {
    updateHighlighting();
    hideContentSpinner();
    // Reinitialize tooltips after filtering
    initializeTitleTooltips();
  }, 100);
}
```

## Server-Side Dropdown Population

### Implementation Strategy

All filter dropdowns are populated server-side using Jinja2 templates, moving away from client-side JavaScript population for better performance and SEO.

#### Filter Options Collection

```python
# Collect filter options from neuron data
roi_options = set()
region_options = set()
nt_options = set()
superclass_options = set()
class_options = set()
subclass_options = set()

for entry in index_data:
    # Collect ROIs from roi_summary
    if entry.get('roi_summary'):
        for roi_info in entry['roi_summary']:
            if isinstance(roi_info, dict) and 'name' in roi_info:
                roi_name = roi_info['name']
                if roi_name and roi_name.strip():
                    roi_options.add(roi_name.strip())

    # Collect neurotransmitters
    if entry.get('consensus_nt') and entry['consensus_nt'].strip():
        nt_options.add(entry['consensus_nt'].strip())
    elif entry.get('celltype_predicted_nt') and entry['celltype_predicted_nt'].strip():
        nt_options.add(entry['celltype_predicted_nt'].strip())

    # ... (similar for other options)
```

#### Template Integration

```python
template_data = {
    'config': self.config,
    'neuron_types': index_data,
    'grouped_neuron_types': sorted_groups,
    'total_types': len(index_data),
    'generation_time': command.requested_at,
    'filter_options': {
        'rois': sorted_roi_options,
        'regions': sorted_region_options,
        'neurotransmitters': sorted_nt_options,
        'superclasses': sorted_superclass_options,
        'classes': sorted_class_options,
        'subclasses': sorted_subclass_options,
        'cell_count_ranges': cell_count_ranges
    }
}
```

#### Template Rendering

```html
<select id="nt-filter" class="filter-dropdown">
  <option value="all">All NTs</option>
  {% for nt in filter_options.neurotransmitters %}
  <option value="{{ nt }}">{{ nt }}</option>
  {% endfor %}
</select>
```

### Benefits

1. **Performance**: No client-side option generation
2. **SEO**: Fully rendered HTML with all options
3. **Consistency**: Server has authoritative data
4. **Caching**: Options are computed once during generation

## Filtering System Architecture

### Filter State Management

The filtering system maintains state through DOM elements and applies filters in a coordinated manner:

```javascript
function rebuildFilteredView() {
  const nameTerm = nameFilter.val().toLowerCase().trim();
  const selectedFilter = somaFilter.val();
  const selectedRoi = roiFilter.val();
  const selectedRegion = regionFilter.val();
  const selectedNt = ntFilter.val();
  const selectedCellCount = cellCountFilter.val();
  const selectedSuperclass = superclassFilter.val();
  const selectedClass = classFilter.val();
  const selectedSubclass = subclassFilter.val();
  
  // Apply all filters in combination
  if (matchesName && matchesFilter && matchesRoi && matchesRegion && 
      matchesNt && matchesCellCount && matchesSuperclass && 
      matchesClass && matchesSubclass) {
    // Include in results
  }
}
```

### Filter Coordination

All filters work together through a unified filtering function that:

1. **Collects** all filter states
2. **Evaluates** each card against all criteria
3. **Groups** results by region
4. **Rebuilds** the display
5. **Updates** highlighting

### Performance Optimizations

#### Debounced Updates

```javascript
nameFilter.on('input', function() {
  showContentSpinner('Filtering by name...');
  setTimeout(function() {
    applyFilters();
  }, 50);
});
```

#### Efficient DOM Manipulation

- Cards are cloned rather than moved for better performance
- Spinner feedback prevents UI blocking during filtering
- Highlighting updates are batched after filtering

## Frontend JavaScript Architecture

### Module Organization

The frontend JavaScript is organized into logical sections:

1. **Variable Declarations**: All jQuery selectors and constants
2. **Utility Functions**: Spinner control, highlighting, tooltip management
3. **Event Handlers**: Filter changes, clicks, keyboard interactions
4. **Core Logic**: Filtering, rebuilding, highlighting functions

### Event Handling Strategy

#### Delegated Events

```javascript
// Use delegated events for dynamic content
$(document).on('click', '.clickable-count', function(e) {
  // Handle click on dynamically added elements
});
```

#### Debounced Input

```javascript
// Debounce rapid input changes
let inputTimeout;
nameFilter.on('input', function() {
  clearTimeout(inputTimeout);
  inputTimeout = setTimeout(function() {
    applyFilters();
  }, 300);
});
```

### State Management

State is managed through:

1. **DOM Elements**: Filter dropdowns and inputs hold current state
2. **Data Attributes**: Cards store filterable metadata
3. **CSS Classes**: Visual state (selected, highlighted) through classes

## Data Flow

### Index Generation Flow

```
1. Scan HTML files → Extract neuron types
2. Batch fetch neuron data → Get cell counts, classifications
3. Calculate filter options → Including cell count ranges
4. Generate template data → Server-side option population
5. Render HTML → Complete index with all filters
```

### Client-Side Filtering Flow

```
1. User interaction → Filter change or click
2. Collect filter state → Read all dropdown values
3. Evaluate each card → Apply all filter criteria
4. Group by region → Maintain original structure
5. Rebuild display → Update visible cards
6. Update highlighting → Show active filters
7. Reinitialize tooltips → Handle dynamic content
```

## Performance Considerations

### Server-Side Optimizations

1. **Batch Processing**: Single database query for all neuron types
2. **Persistent Caching**: ROI hierarchy and neuron data caching
3. **Efficient Calculations**: One-time percentile computation
4. **Template Compilation**: Jinja2 template caching

### Client-Side Optimizations

1. **Debounced Events**: Prevent excessive filtering calls
2. **DOM Cloning**: Efficient card duplication vs. movement
3. **Event Delegation**: Efficient handling of dynamic content
4. **CSS-based Highlighting**: Hardware-accelerated visual feedback

### Memory Management

1. **Event Cleanup**: Proper removal of mouse move listeners
2. **Tooltip Reuse**: Single tooltip element for all interactions
3. **Efficient Selectors**: Cached jQuery objects for repeated use

## Testing Strategy

### Unit Testing

#### Cell Count Ranges

```python
def test_cell_count_ranges():
    """Test the cell count ranges calculation logic."""
    sample_cell_counts = [1, 2, 2, 3, 4, 5, 6, 7, 8, 9, 10, ...]
    
    percentiles = np.percentile(sample_cell_counts, [i * 10 for i in range(11)])
    # Verify ranges cover all data points
    # Verify ranges are non-overlapping
    # Verify JavaScript compatibility
```

#### JavaScript Compatibility

```python
def test_javascript_compatibility():
    """Test that ranges work with JavaScript parsing."""
    test_range_values = ["1-2", "3-5", "10-15", "50-75", "100-200"]
    
    for range_value in test_range_values:
        range_parts = range_value.split('-')
        range_min = int(range_parts[0])
        range_max = int(range_parts[1])
        # Verify parsing works correctly
```

### Integration Testing

1. **Filter Combinations**: Test all filter combinations work together
2. **Dynamic Content**: Verify tooltips work after filtering
3. **Click Behavior**: Test toggle functionality on all interactive elements
4. **Performance**: Measure filtering performance with large datasets

### Browser Testing

1. **Tooltip Positioning**: Verify custom tooltips work across browsers
2. **Event Handling**: Test click and hover behavior
3. **CSS Compatibility**: Verify styling works consistently

## Code Style and Patterns

### Python Conventions

1. **Type Hints**: Use type hints for better IDE support and documentation
2. **Error Handling**: Comprehensive exception handling with logging
3. **Documentation**: Detailed docstrings for all public methods
4. **Separation of Concerns**: Clear separation between data access, business logic, and presentation

### JavaScript Conventions

1. **jQuery Patterns**: Consistent use of jQuery selectors and event handling
2. **Function Organization**: Logical grouping of related functionality
3. **Error Prevention**: Defensive programming for DOM manipulation
4. **Performance**: Efficient event handling and DOM updates

### CSS Conventions

1. **BEM-like Naming**: Descriptive class names (e.g., `neuron-count-tag`, `clickable-count`)
2. **State Classes**: Clear visual state indication (e.g., `selected`, `highlighted`)
3. **Responsive Design**: Mobile-first responsive breakpoints
4. **Performance**: Hardware-accelerated animations and transitions

### Template Conventions

1. **Server-Side Rendering**: Populate data server-side when possible
2. **Semantic HTML**: Proper use of semantic elements and ARIA attributes
3. **Data Attributes**: Consistent use of data attributes for JavaScript interaction
4. **Accessibility**: Maintain accessibility features (title attributes, proper labels)

## Future Considerations

### Potential Enhancements

1. **URL State**: Preserve filter state in URL for bookmarking
2. **Advanced Ranges**: Custom range input for cell counts
3. **Export Functionality**: Export filtered results
4. **Keyboard Navigation**: Full keyboard support for accessibility
5. **Real-time Updates**: WebSocket integration for live data updates

### Scalability Considerations

1. **Virtual Scrolling**: For handling very large datasets
2. **Search Indexing**: Client-side search index for faster name filtering
3. **Progressive Loading**: Load additional data on demand
4. **Service Workers**: Offline capability and caching

## Testing Files and Examples

The project includes several test files and examples for verification and development:

### Test Scripts

#### `test_cell_count_filter.py`
Comprehensive test for the cell count filter implementation:

```bash
python test_cell_count_filter.py
```

Tests include:
- 10th percentile calculation verification
- Range coverage and distribution
- JavaScript compatibility testing
- Performance validation

#### `test_truncate_filter.py`
Tests for the neuron name truncation filter:

```bash
python test_truncate_filter.py
```

Validates:
- Name truncation logic
- Jinja2 filter integration
- HTML output formatting
- Edge case handling

#### `test_truncated_names.html`
Static HTML file for visual testing of truncated names and tooltips.

### Running Tests

```bash
# Run all tests from project root
cd quickpage

# Test cell count filter
python test_cell_count_filter.py

# Test truncate filter
python test_truncate_filter.py

# Run pixi tasks (if configured)
pixi run test
```

### Example Configurations

The project includes several example configuration files:

- `config.example.yaml`: Template configuration
- `config.cns.yaml`: Central nervous system specific settings
- `config.optic-lobe.yaml`: Optic lobe specific configuration

### Development Workflow

1. **Setup**: Copy `config.example.yaml` to `config.yaml` and configure
2. **Test**: Run test scripts to verify functionality
3. **Develop**: Make changes to source files
4. **Validate**: Re-run tests to ensure changes work correctly
5. **Generate**: Run QuickPage to generate updated HTML files

### Implementation Summaries

Additional documentation is available in:

- `IMPLEMENTATION_SUMMARY_CLASS_FIELDS.md`: Class hierarchy implementation details
- `IMPLEMENTATION_SUMMARY_TRUNCATE_FILTER.md`: Truncation filter technical summary
- `TRUNCATE_FILTER_IMPLEMENTATION.md`: Detailed truncation implementation guide