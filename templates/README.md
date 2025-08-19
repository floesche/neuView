# Template Architecture Documentation

This document describes the refactored Jinja2 template architecture for the QuickPage project, which separates the monolithic template into reusable blocks and components using template inheritance.

## Template Structure Overview

### Base Templates

#### `base.html`
The main base template that provides the common HTML structure for all pages.

**Blocks defined:**
- `title`: Page title (defaults to `config.html.title_prefix`)
- `css`: CSS imports (includes default stylesheets)
- `extra_head`: Additional head content
- `header`: Page header section
- `content`: Main page content
- `footer`: Page footer section
- `scripts`: JavaScript imports (includes jQuery and DataTables)
- `extra_scripts`: Additional JavaScript content

#### `macros.html`
Contains reusable Jinja2 macros for common UI components.

**Available macros:**
- `stat_card(number, label, class="")`: Renders statistic cards
- `data_table(table_id, headers, rows, ...)`: Renders DataTables with standard configuration
- `layer_table(container_data, table_class, region_name)`: Renders layer analysis tables
- `layer_row_labels()`: Renders layer analysis row labels
- `connectivity_table(table_id, connections, neuron_type, direction)`: Renders connectivity tables
- `roi_row(roi)`: Renders ROI innervation table rows
- `iframe_embed(src, width, height, title)`: Renders iframe embeds
- `grid_row(items, col_class)`: Renders grid layouts

### Page Templates

#### `neuron_page_refactored.html`
The main neuron page template that extends `base.html` and includes various section templates.

**Template inheritance:**
```jinja2
{% extends "base.html" %}
{% block title %}{{ config.html.title_prefix }} - {{ neuron_data.type }}{% endblock %}
{% block header %}{% include "sections/header.html" %}{% endblock %}
{% block content %}
    {% include "sections/summary_stats.html" %}
    {% include "sections/analysis_details.html" %}
    {% include "sections/neuroglancer.html" %}
    {% include "sections/layer_analysis.html" %}
    {% include "sections/roi_innervation.html" %}
    {% include "sections/connectivity.html" %}
{% endblock %}
```

### Section Templates

All section templates are located in the `templates/sections/` directory:

#### `header.html`
Renders the neuron page header with neuron type and count information.

#### `summary_stats.html`
Displays summary statistics cards with consistent complete neuron type information across all soma side pages.
All cards (Total Neurons, Left Side, Right Side) show complete neuron type statistics regardless of soma side filter.
The Total Neurons card includes hemisphere breakdown and log ratio (base 2) calculated from complete type data.
Ensures AOTU019_L and AOTU019_R pages show identical summary statistics for the complete AOTU019 neuron type.
Uses macros for consistent stat card rendering.

#### `analysis_details.html`
Shows analysis details including soma side and average synapse counts.
Uses macros for consistent stat card rendering.

#### `neuroglancer.html`
Embeds the Neuroglancer visualization iframe.
Uses macros for consistent iframe rendering.

#### `layer_analysis.html`
Complex section showing layer analysis tables for different brain regions (LA, ME, LO, LOP, AME, Central Brain).
Conditionally renders based on available data.

#### `roi_innervation.html`
Displays ROI innervation data in a sortable, filterable DataTable.
Includes cumulative percentage calculations.

#### `connectivity.html`
Shows upstream and downstream connectivity analysis in separate tables.
Includes filtering and cumulative percentage functionality.

#### `neuron_page_scripts.html`
Contains all JavaScript functionality as a Jinja2 template, including:
- Direct access to template variables (roi_summary, connectivity, etc.)
- DataTable initialization and configuration
- Filtering and slider functionality with logarithmic scales
- Cumulative percentage calculations
- Tooltip initialization
- Interactive features with proper conditional rendering

#### `footer.html`
Simple footer with generation timestamp and dataset information.

## Benefits of the Refactored Architecture

### 1. **Modularity**
- Each section is self-contained and can be modified independently
- Easy to add, remove, or reorder sections
- Sections can be reused across different page types

### 2. **Maintainability**
- Reduced code duplication through macros
- Consistent styling and behavior across components
- Easier debugging with smaller, focused template files

### 3. **Reusability**
- Macros can be used across multiple templates
- Base template can be extended for different page types
- Section templates can be included in different contexts

### 4. **Template Inheritance**
- Child templates only need to define content-specific blocks
- Common structure and styling handled by base template
- Easy to maintain consistent site-wide changes

### 5. **Performance**
- Jinja2 template caching works more effectively with smaller templates
- Conditional includes reduce rendering overhead
- JavaScript template has direct access to data (no JSON serialization needed)

## Usage Guidelines

### Adding New Sections
1. Create a new template in `templates/sections/`
2. Add the include statement to the appropriate parent template
3. Use existing macros where possible for consistency

### Creating New Macros
1. Add macro definitions to `macros.html`
2. Import macros in templates that use them: `{% from "macros.html" import macro_name %}`
3. Document macro parameters and usage

### Extending Base Template
```jinja2
{% extends "base.html" %}

{% block title %}Custom Page Title{% endblock %}

{% block content %}
    <!-- Your custom content here -->
{% endblock %}
```

### Using Macros
```jinja2
{% from "macros.html" import stat_card %}

    {{ stat_card(123, "My Statistic") }}
```

### Including JavaScript Template
```jinja2
{% block extra_scripts %}
<script>
{% include "sections/neuron_page_scripts.html" %}
</script>
{% endblock %}
```

## Migration from Original Template

The original `neuron_page.html` has been preserved for reference. The new architecture maintains all original functionality while providing better organization and maintainability.

### Key Changes:
- Monolithic template split into base + sections
- Repetitive HTML converted to reusable macros
- JavaScript functionality moved to separate template with template variable access
- CSS and JS imports centralized in base template
- Conditional sections preserved with same logic

### Compatibility:
- All original variables and filters are still used
- Template context requirements remain the same
- Generated HTML structure is functionally equivalent
- All interactive features preserved

## Future Enhancements

### Potential Improvements:
1. **Additional Page Types**: Create templates for summary pages, comparison views
2. **Component Library**: Expand macros for more UI components  
3. **JavaScript Modules**: Split JavaScript template into smaller, reusable components
4. **Theme Support**: Add theming blocks for different visual styles
5. **Mobile Optimization**: Add responsive design blocks
6. **Internationalization**: Add translation support through template blocks