# HTML Tooltip Usage Guide

This document explains how to use the new HTML tooltip functionality that has been added to the codebase.

## Overview

The HTML tooltip system allows you to create rich, styled tooltips that can contain any HTML content. Unlike simple `title` attribute tooltips, these tooltips support:

- Rich HTML content (lists, formatted text, etc.)
- Custom styling
- Responsive width adaptation based on screen size
- Automatic positioning to avoid viewport overflow
- Mobile-optimized display and interaction
- Smooth hover interactions

## Basic Usage

To create an HTML tooltip, use the following structure:

```html
<div class="html-tooltip">
    <div class="tooltip-content">
        <!-- Your tooltip content goes here -->
        <p>This is a rich HTML tooltip!</p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
    </div>
    <!-- The element that triggers the tooltip -->
    Your trigger text or element
</div>
```

## Examples

### Simple Text Tooltip

```html
<div class="html-tooltip">
    <div class="tooltip-content">
        This is a simple tooltip with plain text.
    </div>
    ?
</div>
```

### Rich Content Tooltip (as seen in neuroglancer.html.jinja)

```html
<div class="html-tooltip">
    <div class="tooltip-content">
        <dl>
            <dt>Neuroglancer</dt>
            <dd>Neuroglancer is a web-based visualization tool for large-scale neuroscientific data.</dd>
        </dl>
    </div>
    ?
</div>
```

### Multi-line Information Tooltip

```html
<div class="html-tooltip">
    <div class="tooltip-content">
        <h4>Data Analysis</h4>
        <p>This section contains:</p>
        <ul>
            <li>Statistical summaries</li>
            <li>Connection matrices</li>
            <li>Regional breakdowns</li>
        </ul>
        <p><strong>Note:</strong> Data is updated hourly.</p>
    </div>
    <span class="info-icon">ℹ️</span>
</div>
```

## Positioning

By default, tooltips appear above the trigger element. The system automatically adjusts positioning to prevent overflow:

- **Default**: Above the element (centered)
- **Auto-adjust**: If tooltip would overflow the viewport, it repositions to:
  - Left side if overflowing right
  - Right side if overflowing left  
  - Below if overflowing top

You can also manually control positioning by adding classes to the `.html-tooltip` element:

```html
<!-- Force tooltip to appear on the right -->
<div class="html-tooltip tooltip-right">
    <div class="tooltip-content">Right-side tooltip</div>
    Trigger
</div>

<!-- Force tooltip to appear on the left -->
<div class="html-tooltip tooltip-left">
    <div class="tooltip-content">Left-side tooltip</div>
    Trigger
</div>

<!-- Force tooltip to appear below -->
<div class="html-tooltip tooltip-bottom">
    <div class="tooltip-content">Bottom tooltip</div>
    Trigger
</div>
```

## Styling

### Default Styling

The tooltips come with sensible defaults:
- Dark background (#333)
- White text
- Rounded corners
- Drop shadow
- Responsive width adaptation:
  - Mobile (≤ 768px): Up to 95vw width, smaller font (13px)
  - Desktop (1200px+): Up to 500px width
  - Large screens (1600px+): Up to 600px width
  - Very small screens (≤ 480px): Simplified center positioning
- Responsive text wrapping

### Custom Styling

You can add custom CSS to style your tooltip content:

```html
<div class="html-tooltip">
    <div class="tooltip-content custom-tooltip">
        <style>
        .custom-tooltip {
            background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: 2px solid #fff;
        }
        </style>
        <p>This tooltip has custom styling!</p>
    </div>
    Custom Styled
</div>
```

## Integration Notes

### Automatic Initialization

The HTML tooltip functionality is automatically initialized when:
- The page loads (via `initializeAllTooltips()`)
- DataTables are redrawn (for dynamic content)

### Performance

- Tooltips are hidden by default with `display: none`
- Only visible tooltips trigger positioning calculations
- Event listeners are efficiently managed to prevent memory leaks
- Responsive calculations are optimized with minimal DOM queries
- Width constraints prevent expensive layout recalculations

### Accessibility

- Tooltips use `cursor: help` to indicate interactive content
- Content is properly hidden from screen readers when not visible
- Tooltips disappear on mouse leave for clear interaction patterns
- Mobile-friendly sizing ensures readability on touch devices
- Simplified positioning on small screens improves usability

## Technical Implementation

The functionality consists of:

1. **CSS** (`quickpage/static/css/neuron-page.css`):
   - `.html-tooltip` styles for container
   - `.tooltip-content` styles for the tooltip box
   - Responsive media queries for different screen sizes
   - Positioning classes for different orientations
   - Arrow/pointer styling
   - Mobile-specific overrides for optimal display

2. **JavaScript** (`quickpage/static/js/neuron-page.js`):
   - `initializeHtmlTooltips()` function
   - Automatic viewport overflow detection with responsive margins
   - Dynamic positioning adjustment based on screen size
   - Enhanced mobile positioning logic
   - Integration with existing tooltip system

3. **Integration**:
   - Called automatically via `initializeAllTooltips()`
   - Works with dynamic content (DataTables, etc.)
   - Prevents duplicate initialization

## Troubleshooting

### Tooltip Not Appearing
- Ensure `.tooltip-content` is a direct child of `.html-tooltip`
- Check that JavaScript is loaded and `initializeAllTooltips()` is called
- Verify CSS is properly loaded

### Positioning Issues
- Check for CSS conflicts that might affect `position: relative/absolute`
- Ensure parent containers don't have `overflow: hidden` that clips tooltips
- Try manual positioning classes if auto-positioning isn't working

### Content Formatting
- Remember that `.tooltip-content` supports full HTML
- Use appropriate semantic markup (headings, lists, etc.)
- Content automatically adapts to screen size constraints
- On very small screens (≤ 480px), tooltips use simplified center positioning

## Responsive Behavior

### Screen Size Breakpoints

- **≤ 480px**: Mobile phones
  - Max width: 98vw
  - Font size: 12px
  - Forced center positioning for all tooltips
  - Simplified arrow positioning
  
- **≤ 768px**: Tablets and small screens
  - Max width: 95vw
  - Font size: 13px
  - Enhanced overflow protection
  
- **1200px+**: Large desktops
  - Max width: 500px
  - Full positioning options available
  
- **1600px+**: Extra large screens
  - Max width: 600px
  - Optimal spacing and readability

### Automatic Adaptations

The tooltip system automatically:
- Adjusts width based on viewport size
- Simplifies positioning on mobile devices
- Ensures tooltips never exceed screen boundaries
- Provides appropriate margins for touch interaction
- Optimizes font sizes for different screen densities