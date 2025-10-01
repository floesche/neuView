# Synonym and Flywire Type Filtering Feature

## Overview

The Types page now includes enhanced filtering functionality for synonym and Flywire type tags. When you click on a synonym tag, the page will filter to show all neuron types that have synonyms. When you click on a Flywire type tag, the page will filter to show all neuron types that have **displayable** Flywire types (i.e., Flywire synonyms that are different from the neuron type name). Each filter type works independently.

## How It Works

### Previous Behavior
- Clicking on synonym or Flywire type tags had limited or inconsistent filtering behavior

### New Behavior
- Clicking on **any** synonym tag filters to show all neuron types that have synonyms
- Clicking on **any** Flywire type tag filters to show all neuron types that have **displayable** Flywire types (Flywire synonyms different from the neuron name)
- Each filter type works independently - synonym tags only filter for synonyms, Flywire tags only filter for displayable Flywire types
- Only one filter type can be active at a time

### Visual Feedback
- When the synonym filter is active, **all** synonym tags are highlighted with their selected styles
- When the Flywire type filter is active, **all** Flywire type tags are highlighted with their selected styles
- This provides clear visual indication of which filter type is currently active

## Use Cases

This feature is particularly useful for:

1. **Research Discovery**: Finding all neuron types that have synonyms or finding all that have meaningful Flywire cross-references (different from their own name)
2. **Data Quality**: Identifying which neuron types have been cross-referenced with specific naming systems and have different identifiers
3. **Comparative Analysis**: Quickly filtering to see which neuron types have specific types of additional metadata that provides real alternative naming information

## Technical Implementation

### JavaScript Changes
- Enhanced separate filtering for `currentSynonymFilter` and `currentFlywireTypeFilter` variables
- Modified click handlers to activate independent filters for synonym and Flywire type tags
- Updated highlighting logic to show the appropriate tag type as selected when its filter is active
- Enhanced the Flywire filtering logic to check only for **displayable** Flywire types (processed flywire types that are different from the neuron name)

### Template Changes
- Updated the click event handlers to use separate handlers for each tag type
- Modified the filter application logic to include independent filter checks for each type
- Enhanced the Flywire filtering system to only check `processedFlywireTypes` data attribute (contains only displayable types)

### Filter Logic
The filters work independently:

**Synonym Filter:**
```javascript
const hasSynonyms = synonyms !== "" || processedSynonyms !== "";
return hasSynonyms;
```

**Flywire Filter (Displayable Types Only):**
```javascript
// Only check processed flywire types - these contain only displayable (different) types
return processedFlywireTypes !== "";
```

Note: `processedFlywireTypes` contains only Flywire synonyms that are different from the neuron type name. For example, if neuron type "AOTU019" has Flywire synonym "AOTU019", it won't appear in `processedFlywireTypes` and won't be shown when filtering for Flywire types.

## Usage Instructions

1. Navigate to the Types page
2. Look for neuron type cards that have synonym tags (blue) or Flywire type tags (green)
3. Click on any synonym tag to filter for neuron types that have synonyms
4. OR click on any Flywire type tag to filter for neuron types that have displayable Flywire types (different from their name)
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

The enhancement provides independent filtering for synonym and Flywire type tags, with Flywire filtering specifically designed to show only neuron types with meaningful alternative Flywire identifiers, while preserving all other existing functionality.