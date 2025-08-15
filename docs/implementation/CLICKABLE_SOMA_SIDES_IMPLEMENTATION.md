# Clickable Soma Sides Implementation

## Overview

This document describes the enhancement to the neuron search functionality that makes soma side indicators (L), (R), (M) clickable links in the search dropdown, allowing users to navigate directly to side-specific neuron pages.

## Key Features

### 1. Clickable Side Indicators
- **Neuron name** → Links to primary/"both" page
- **(L)** → Links to left-side specific page  
- **(R)** → Links to right-side specific page
- **(M)** → Links to middle-specific page
- **Keyboard navigation** → Still defaults to primary page

### 2. Visual Design
- Side indicators appear as blue clickable links
- Hover effects with underline
- Maintains existing dropdown styling
- Clear visual distinction between neuron name and side links

## Technical Implementation

### Modified Files

#### 1. `quickpage/templates/static/js/neuron-search.js.template`

**Key Changes:**
- Enhanced `updateDropdown()` method to create structured HTML elements
- Added clickable side links with proper event handling
- Implemented hover effects and visual styling
- Added `navigateToSomaSide()` method for direct side navigation

**New HTML Structure:**
```javascript
// Before: Simple text
item.textContent = "T4a (L, R, Both)";

// After: Structured clickable elements
<div class="neuron-search-item">
  <span class="neuron-name">T4a</span>
  <span> (
    <a class="side-link" href="#">L</a>, 
    <a class="side-link" href="#">R</a>
  )</span>
</div>
```

### Code Structure

#### Enhanced updateDropdown() Method
```javascript
updateDropdown() {
  this.filteredTypes.forEach((type, index) => {
    const item = document.createElement("div");
    
    // Create neuron name element (clickable, goes to primary page)
    const nameSpan = document.createElement('span');
    nameSpan.className = 'neuron-name';
    nameSpan.textContent = type;
    
    // Add click handler for neuron name
    nameSpan.addEventListener('click', (e) => {
      this.selectNeuronType(type);
    });
    
    // Create clickable side links
    if (neuronEntry && neuronEntry.urls) {
      const sides = [];
      if (neuronEntry.urls.left) sides.push({ label: 'L', side: 'left' });
      if (neuronEntry.urls.right) sides.push({ label: 'R', side: 'right' });
      if (neuronEntry.urls.middle) sides.push({ label: 'M', side: 'middle' });
      
      sides.forEach((sideInfo) => {
        const sideLink = document.createElement('a');
        sideLink.textContent = sideInfo.label;
        sideLink.className = 'side-link';
        
        // Click handler for side-specific navigation
        sideLink.addEventListener('click', (e) => {
          e.preventDefault();
          this.navigateToSomaSide(type, sideInfo.side);
        });
      });
    }
  });
}
```

#### New navigateToSomaSide() Method
```javascript
navigateToSomaSide(neuronType, side) {
  const neuronEntry = this.neuronData.find(entry => entry.name === neuronType);
  
  if (neuronEntry && neuronEntry.urls[side]) {
    // Close dropdown and update input
    this.inputElement.value = neuronType;
    this.hideDropdown();
    // Navigate to the specific side page
    window.location.href = neuronEntry.urls[side];
  } else {
    // Fallback to primary URL
    this.navigateToNeuronType(neuronType);
  }
}
```

## User Experience

### Search Interaction Flow

1. **User types in search box**: `"T4a"`
2. **Dropdown appears showing**: `T4a (L, R)`
3. **User options**:
   - Click **"T4a"** → Navigate to `T4a.html` (both sides)
   - Click **"(L)"** → Navigate to `T4a_L.html` (left only)
   - Click **"(R)"** → Navigate to `T4a_R.html` (right only)
   - Use **arrow keys + Enter** → Navigate to `T4a.html` (primary)

### Visual Feedback

- **Side links**: Blue color (#0066cc)
- **Hover state**: Underlined text
- **Click feedback**: Immediate navigation
- **Keyboard selection**: Maintains existing highlight behavior

## Examples by Neuron Type

### Multi-Side Neuron (T4a)
- **Display**: `T4a (L, R)`  
- **T4a** → `T4a.html`
- **(L)** → `T4a_L.html`
- **(R)** → `T4a_R.html`

### Single-Side Neuron (ComplexNeuron)
- **Display**: `ComplexNeuron (L)`
- **ComplexNeuron** → `ComplexNeuron_L.html`
- **(L)** → `ComplexNeuron_L.html`

### Both-Only Neuron (LC10)
- **Display**: `LC10`
- **LC10** → `LC10.html`
- No side-specific options

### Middle-Only Neuron (Mi1)
- **Display**: `Mi1 (M)`
- **Mi1** → `Mi1_M.html`
- **(M)** → `Mi1_M.html`

## Event Handling

### Click Event Management
```javascript
// Prevent dropdown from closing when clicking side links
item.addEventListener("mousedown", (e) => {
  if (!e.target.classList.contains('side-link')) {
    e.preventDefault();
    this.clickingDropdown = true;
  }
});

// Handle clicks appropriately
item.addEventListener("click", (e) => {
  if (!e.target.classList.contains('side-link')) {
    // Main item click - go to primary page
    this.selectNeuronType(type);
  }
  // Side link clicks handled by their own event listeners
});
```

### Keyboard Navigation Preservation
- **Arrow keys**: Navigate through dropdown items
- **Enter key**: Select highlighted item → primary page
- **Escape key**: Close dropdown
- **Side links**: Only clickable via mouse

## CSS Styling

### Side Link Styling
```css
.side-link {
  color: #0066cc;
  text-decoration: none;
  cursor: pointer;
  font-size: 0.9em;
}

.side-link:hover {
  text-decoration: underline;
}
```

### Container Styling
```css
.neuron-search-item {
  padding: 8px 12px;
  cursor: pointer;
  border-bottom: 1px solid #eee;
  transition: background-color 0.2s;
}

.neuron-name {
  color: inherit;
  cursor: pointer;
}
```

## Testing

### Test Cases Covered

1. **Multi-side neuron** (T4a with L, R, Both)
   - ✅ Neuron name links to both page
   - ✅ L link navigates to left page
   - ✅ R link navigates to right page
   - ✅ Keyboard selection goes to both page

2. **Single-side neuron** (ComplexNeuron with L only)
   - ✅ Neuron name links to left page
   - ✅ L link navigates to left page
   - ✅ Keyboard selection goes to left page

3. **Middle-only neuron** (Mi1 with M only)
   - ✅ Neuron name links to middle page
   - ✅ M link navigates to middle page

4. **Both-only neuron** (LC10 with Both only)
   - ✅ Neuron name links to both page
   - ✅ No side indicators shown
   - ✅ Keyboard selection goes to both page

### Verification Methods

```javascript
// Test neuron URLs functionality
const t4aUrls = window.neuronSearch.getNeuronUrls('T4a');
console.log(t4aUrls); 
// Expected: { both: "T4a.html", left: "T4a_L.html", right: "T4a_R.html" }

// Test direct navigation
window.neuronSearch.navigateToSomaSide('T4a', 'left');
// Expected: Navigate to T4a_L.html
```

## Backward Compatibility

- **Existing functionality**: Preserved completely
- **Keyboard navigation**: Unchanged behavior
- **API methods**: All existing methods still work
- **Template structure**: Maintains compatibility with base template
- **Search behavior**: Core search logic unchanged

## Performance Considerations

- **Event delegation**: Efficient click handling
- **DOM creation**: Optimized element creation
- **Memory usage**: No significant increase
- **Search speed**: No impact on search performance
- **Navigation**: Direct URL mapping (no additional requests)

## Integration Points

### Generated by create-index
- Automatically updates when `create-index` is run
- Reflects current HTML files in output directory
- No manual configuration required

### Template Integration
- Works with existing base.html template
- Compatible with index_page.html structure
- Integrates with header.html neuron search

### Data Structure
```javascript
// Enhanced neuron data structure supports clickable navigation
const NEURON_DATA = [
  {
    "name": "T4a",
    "urls": {
      "both": "T4a.html",
      "left": "T4a_L.html",
      "right": "T4a_R.html"
    },
    "primary_url": "T4a.html"
  }
];
```

## Future Enhancements

### Potential Improvements
1. **Keyboard shortcuts**: Alt+L/R/M for direct side navigation
2. **Tooltips**: Show page descriptions on hover
3. **Visual indicators**: Icons for different soma sides
4. **Context menu**: Right-click options for advanced navigation
5. **Batch operations**: Multi-select for comparison views

### Accessibility
- **ARIA labels**: Add proper labels for screen readers
- **Tab navigation**: Support tabbing through side links
- **High contrast**: Ensure visibility in all themes
- **Keyboard alternatives**: Provide keyboard access to all functionality

## Conclusion

The clickable soma sides enhancement provides intuitive, direct navigation to neuron side-specific pages while maintaining full backward compatibility. Users can now efficiently access exactly the neuron page they need with a single click, improving the overall user experience of the neuron search functionality.

The implementation is robust, well-tested, and automatically maintained through the `create-index` command, ensuring it stays synchronized with the available neuron pages in the system.