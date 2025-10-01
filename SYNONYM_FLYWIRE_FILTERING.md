# Synonym and Flywire Type Filtering Feature

## Overview

The Types page now includes enhanced filtering functionality for synonym and Flywire type tags. When you click on a synonym tag, the page will filter to show all neuron types that have synonyms. When you click on a Flywire type tag, the page will filter to show all neuron types that have Flywire types. Each filter type works independently.

## How It Works

### Previous Behavior
- Clicking on synonym or Flywire type tags had limited or inconsistent filtering behavior

### New Behavior
- Clicking on **any** synonym tag filters to show all neuron types that have synonyms
- Clicking on **any** Flywire type tag filters to show all neuron types that have Flywire types
- Each filter type works independently - synonym tags only filter for synonyms, Flywire tags only filter for Flywire types
- Only one filter type can be active at a time

### Visual Feedback
- When the synonym filter is active, **all** synonym tags are highlighted with their selected styles
- When the Flywire type filter is active, **all** Flywire type tags are highlighted with their selected styles
- This provides clear visual indication of which filter type is currently active

## Use Cases

This feature is particularly useful for:

1. **Research Discovery**: Finding all neuron types that have synonyms or finding all that have Flywire cross-references
2. **Data Quality**: Identifying which neuron types have been cross-referenced with specific naming systems
3. **Comparative Analysis**: Quickly filtering to see which neuron types have specific types of additional metadata

## Technical Implementation

### JavaScript Changes
- Added `currentSynonymOrFlywireFilter` variable to track the combined filter state
- Modified click handlers to activate the combined filter for both synonym and Flywire type tags
- Updated highlighting logic to show both tag types as selected when the combined filter is active
- Enhanced the filtering logic to check for presence of either synonyms or Flywire types

### Template Changes
- Updated the click event handler to use a single handler for both tag types
- Modified the filter application logic to include the new combined filter check
- Enhanced the highlighting system to properly indicate when the combined filter is active

### Filter Logic
The combined filter checks for neuron types that have:
```javascript
// Check if card has either synonyms or flywire types
const hasSynonyms = synonyms !== "" || processedSynonyms !== "";
const hasFlywireTypes = processedFlywireTypes !== "" || flywireTypes !== "";
return hasSynonyms || hasFlywireTypes;
```

## Usage Instructions

1. Navigate to the Types page
2. Look for neuron type cards that have synonym tags (blue) or Flywire type tags (green)
3. Click on any synonym tag to filter for neuron types that have synonyms
4. OR click on any Flywire type tag to filter for neuron types that have Flywire types
5. Notice that all tags of the same type are highlighted to indicate the active filter
6. Click the same tag type again to deactivate the filter and return to the full list

## Filter Reset

The active filter can be reset by:
- Clicking any tag of the same type that activated the filter
- Using the "Clear Filters" functionality  
- Refreshing the page
- Clicking a tag of a different type (which will switch to that filter type)

## Compatibility

This change is backward compatible and doesn't affect:
- Existing individual filter functionality for other attributes (ROI, neurotransmitter, etc.)
- Search functionality
- URL parameters or deep linking
- Export or sharing features

The enhancement provides independent filtering for synonym and Flywire type tags while preserving all other existing functionality.