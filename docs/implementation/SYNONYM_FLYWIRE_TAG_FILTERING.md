# Synonym and FlyWire Type Tag Filtering Implementation

## Overview

This document describes the implementation of clickable filtering for synonym and FlyWire type tags on the types page. When users click on these tags, the page filters to show only neuron types that contain the selected synonym or FlyWire type.

## User Requirements

- Clicking on a synonym or FlyWire type tag should filter cards to show only those that have any synonyms or FlyWire types respectively
- Clicking an activated tag again should reset that filter
- No dropdown filters should be created for these tag types (unlike other filters)
- Tags should behave consistently with existing tag filtering patterns

## Implementation Details

### 1. JavaScript Filter State Management

#### Virtual Filter Variables
```javascript
// Virtual filters for tags that don't have dropdown selectors
let currentSynonymFilter = 'all';
let currentFlywireTypeFilter = 'all';
```

Unlike other filters that use dropdown elements with `.val()` methods, synonym and FlyWire type filters use simple JavaScript variables since they don't have UI dropdown components.

#### Click Handler Extension
```javascript
// Extended click handler to include synonym and flywire type tags
$(document).on('click', '.roi-tag, .nt-tag, .class-tag, .dimorphism-tag, .synonym-tag, .flywire-type-tag, .view-indicator', function(e) {
```

### 2. Tag Click Logic

#### Synonym Tag Handling
```javascript
} else if (tagElement.hasClass('synonym-tag')) {
  // Synonym tag (virtual filter)
  showContentSpinner('Filtering by synonym...');
  
  // If clicking on the currently selected synonym, reset the filter
  currentSynonymFilter = currentSynonymFilter === tagName ? 'all' : tagName;
```

#### FlyWire Type Tag Handling
```javascript
} else if (tagElement.hasClass('flywire-type-tag')) {
  // FlyWire type tag (virtual filter)
  showContentSpinner('Filtering by FlyWire type...');
  
  // If clicking on the currently selected flywire type, reset the filter
  currentFlywireTypeFilter = currentFlywireTypeFilter === tagName ? 'all' : tagName;
```

### 3. Filtering Logic

#### Synonym Matching
```javascript
// Check synonym filter
const matchesSynonym = (() => {
  if (selectedSynonym === 'all') return true;
  
  // When a synonym is selected, show all cards that have any synonyms
  // Check processed synonyms first
  const processedSynonyms = cardWrapper.data('processed-synonyms') || '';
  if (processedSynonyms) {
    // Card has processed synonyms, so it should be visible
    return true;
  }
  
  // Fallback to raw synonyms
  const synonyms = cardWrapper.data('synonyms') || '';
  if (synonyms && synonyms.trim()) {
    // Card has raw synonyms, so it should be visible
    return true;
  }
  
  return false;
})();
```

#### FlyWire Type Matching
```javascript
// Check flywire type filter
const matchesFlywireType = (() => {
  if (selectedFlywireType === 'all') return true;
  
  // When a flywire type is selected, show all cards that have any flywire types
  // Check processed flywire types first
  const processedFlywireTypes = cardWrapper.data('processed-flywire-types') || '';
  if (processedFlywireTypes) {
    // Card has processed flywire types, so it should be visible
    return true;
  }
  
  // Fallback to raw flywire types
  const flywireTypes = cardWrapper.data('flywire-types') || '';
  if (flywireTypes && flywireTypes.trim()) {
    // Card has raw flywire types, so it should be visible
    return true;
  }
  
  return false;
})();
```

#### Combined Filter Logic
```javascript
// All filters must match for a card to be shown
if (matchesName && matchesFilter && matchesRoi && matchesRegion && matchesNt && 
    matchesCellCount && matchesSuperclass && matchesClass && matchesSubclass && 
    matchesDimorphism && matchesSynonym && matchesFlywireType) {
  // Card passes all filters
}
```

### 4. Visual Highlighting

#### Highlighting Logic
```javascript
// Update synonym tag highlighting - highlight ALL synonym tags when filter is active
$('#filtered-results-container .synonym-tag').removeClass('selected');
if (currentSynonymFilterValue !== 'all') {
  $('#filtered-results-container .synonym-tag').addClass('selected');
}

// Update flywire type tag highlighting - highlight ALL flywire type tags when filter is active
$('#filtered-results-container .flywire-type-tag').removeClass('selected');
if (currentFlywireTypeFilterValue !== 'all') {
  $('#filtered-results-container .flywire-type-tag').addClass('selected');
}
```

### 5. CSS Styling

#### Base Tag Styles
```css
.synonym-tag {
    background-color: #f0f4ff;
    color: #4338ca;
    border-color: #e0e7ff;
    cursor: pointer; /* Changed from default to pointer */
}

.flywire-type-tag {
    background-color: #ecfdf5;
    color: #059669;
    border-color: #d1fae5;
    cursor: pointer; /* Changed from default to pointer */
}
```

#### Selected State Styles
```css
.synonym-tag.selected {
    background-color: #4338ca;
    color: white;
    border-color: #3730a3;
    box-shadow: 0 2px 4px rgba(67, 56, 202, 0.3);
}

.flywire-type-tag.selected {
    background-color: #059669;
    color: white;
    border-color: #047857;
    box-shadow: 0 2px 4px rgba(5, 150, 105, 0.3);
}
```

#### Hover Effects for Selected State
```css
.synonym-tag.selected:hover {
    background-color: #3730a3;
    transform: translateY(-1px);
}

.flywire-type-tag.selected:hover {
    background-color: #047857;
    transform: translateY(-1px);
}
```

## Data Flow

### 1. Template Data
- Processed synonym and FlyWire type data is passed from IndexService to template
- Raw data is maintained for backward compatibility
- Both processed and raw data are available as data attributes

### 2. Data Attributes
```html
data-processed-synonyms="syn1,syn2,syn3"
data-processed-flywire-types="type1,type2"
```

### 3. Filtering Process
1. User clicks on synonym or FlyWire type tag
2. Virtual filter variable is updated (toggle behavior - any tag can activate/deactivate the filter)
3. `rebuildFilteredView()` is called
4. Each card is checked - cards with any synonyms/FlyWire types are shown when filter is active
5. Only matching cards are displayed
6. Visual highlighting is updated (all tags of the filtered type are highlighted)

## Integration with Existing System

### Consistency with Other Filters
- Uses same click handler pattern as ROI, NT, and class tags
- Follows same toggle behavior (click to activate, click again to deactivate)
- Uses same highlighting system with `.selected` class
- Integrates with existing spinner and filter application flow

### Data Compatibility
- Works with both processed and raw data formats
- Prioritizes processed data for accuracy
- Falls back to raw data processing for compatibility
- Maintains existing search functionality

### Visual Consistency
- Tags maintain existing visual design
- Selected state follows established color and styling patterns
- Hover effects consistent with other interactive elements
- Cursor changes to indicate clickability

## Benefits

1. **Improved Discoverability**: Users can easily filter to see which neuron types have synonyms or FlyWire type annotations
2. **Consistent UX**: Behavior matches other tag filtering patterns
3. **No UI Clutter**: No additional dropdown filters needed
4. **Data Flexibility**: Works with both processed and raw data formats
5. **Performance**: Efficient filtering using data attributes and existing infrastructure

## Bug Fixes

### Empty Processed Data Issue
A bug was identified where cards without FlyWire types (like Tm3) were still showing when the FlyWire filter was active. This was caused by empty dictionaries `{}` being processed and creating empty data attributes.

**Root Cause**: The template condition `{% if neuron.processed_flywire_types %}` was true for empty dictionaries, causing `data-processed-flywire-types=""` to be rendered.

**Fix**: Updated template conditions to check for actual content:
```jinja2
{% if neuron.processed_flywire_types and neuron.processed_flywire_types|length > 0 %}
```

This ensures data attributes are only populated when there is actual processed data.

### Display Logic Consistency Issue
A critical bug was identified where the **filtering logic** and **display logic** were inconsistent, causing cards to appear in filtered results even when they had no visible tags.

**Root Cause**: 
- **Display Logic**: FlyWire type tags are only shown if `flywire_info.is_different` is true (processed) or if the type differs from neuron name (raw)
- **Filtering Logic**: Originally checked for ANY FlyWire data, regardless of whether it would be displayed
- **Result**: Cards like "AOTU019" with FlyWire type "AOTU019" had no visible tags but still appeared in filtered results

**Fix**: Updated both template data generation and filtering logic to match display logic exactly:

**Template Fix**: Generate data attributes to only include displayable FlyWire types:
```jinja2
data-processed-flywire-types="{% if neuron.processed_flywire_types and neuron.processed_flywire_types|length > 0 %}
  {% set displayable_types = [] %}
  {% for flywire_name, flywire_info in neuron.processed_flywire_types.items() %}
    {% if flywire_info.is_different %}{{ displayable_types.append(flywire_name) or '' }}{% endif %}
  {% endfor %}
  {{ displayable_types | join(',') }}
{% endif %}"
```

**JavaScript Fix**: Check raw FlyWire types against neuron name:
```javascript
// FlyWire Type Filtering - now matches display logic
const flywireTypeList = flywireTypes.split(',').map(s => s.trim());
const hasDisplayableTypes = flywireTypeList.some(flywireType => {
  return flywireType && flywireType.toLowerCase() !== neuronName.toLowerCase();
});
return hasDisplayableTypes;
```

```javascript
// Synonym Filtering - now matches processing logic  
const commaSeparatedItems = synonym.split(',').map(item => item.trim());
return commaSeparatedItems.some(item => {
  if (!item) return false;
  // Skip items starting with "fru-M" (matches processing logic)
  if (item.startsWith('fru-M')) return false;
  return true;
});
```

This ensures that only cards with actually visible tags are shown when filters are active. Cards where the FlyWire type matches the neuron name (and therefore show no FlyWire tags) are correctly excluded from filtered results.

## Testing Recommendations

1. Test clicking synonym tags to ensure cards with any synonyms are shown
2. Test clicking FlyWire type tags to ensure cards with any FlyWire types are shown
3. **Critical**: Verify that cards without synonyms/FlyWire types are properly hidden when filters are active
4. **Critical**: Test specific cases like "Tm3", "AOTU019", "AOTU103m" to ensure they don't appear when FlyWire filter is active
5. **Critical**: Verify that cards with FlyWire types matching their neuron name (no visible tags) are properly hidden
6. **Critical**: Test that both processed and raw FlyWire type matching logic works correctly
7. Verify toggle behavior (click any tag to activate, click any tag of same type to deactivate)
8. Test that clicking different synonym tags when filter is active deactivates the filter
9. Test that clicking different FlyWire type tags when filter is active deactivates the filter
10. Test combination with other filters to ensure all work together
11. Verify visual highlighting updates correctly (all tags highlighted when active)
12. Test with both processed and raw data scenarios
13. Verify fallback behavior when processed data is unavailable
14. Test edge cases with empty dictionaries and empty strings
15. Verify consistency between what tags are displayed and what cards are filtered
16. Test cards with multiple FlyWire types where some match neuron name and others don't