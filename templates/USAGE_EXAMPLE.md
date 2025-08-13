# Template Usage Examples

This file demonstrates how to use the refactored template architecture in your Python code.

## Switching to the Refactored Template

To use the new refactored template instead of the original monolithic template, update your Python code as follows:

### Before (Original Template)
```python
# In page_generator.py
template = self.env.get_template('neuron_page.html')
```

### After (Refactored Template)
```python
# In page_generator.py
template = self.env.get_template('neuron_page_refactored.html')
```

## Template Context Requirements

The refactored template uses the same context variables as the original template:

### Required Context Variables
```python
context = {
    'config': config,
    'neuron_data': neuron_data,
    'neuron_type': neuron_type,
    'soma_side': soma_side,
    'summary': summary_stats,
    'neuroglancer_url': neuroglancer_url,
    'layer_analysis': layer_analysis,
    'roi_summary': roi_summary,
    'connectivity': connectivity,
    'generation_time': datetime.now(),
    # ... other context variables
}
```

## Creating Custom Page Templates

### Example: Simple Neuron Summary Page
```python
# templates/neuron_summary.html
{% extends "base.html" %}
{% from "macros.html" import stat_card, section_header, section_footer %}

{% block title %}{{ neuron_type }} Summary{% endblock %}

{% block content %}
{{ section_header("Neuron Summary") }}
<div class="row">
    <div class="col-md-6">
        {{ stat_card(neuron_count, "Total Neurons") }}
    </div>
    <div class="col-md-6">
        {{ stat_card(avg_synapses, "Avg Synapses") }}
    </div>
</div>
{{ section_footer() }}
{% endblock %}
```

### Example: Custom Analysis Page
```python
# templates/custom_analysis.html
{% extends "base.html" %}

{% block title %}Custom Analysis - {{ analysis_name }}{% endblock %}

{% block content %}
    {% include "sections/header.html" %}
    {% include "sections/summary_stats.html" %}
    
    <!-- Custom section -->
    <section>
        <h2>Custom Analysis Results</h2>
        <p>{{ analysis_description }}</p>
        <!-- Your custom analysis content here -->
    </section>
    
    {% include "sections/connectivity.html" %}
{% endblock %}

{% block extra_scripts %}
<script>
// Custom JavaScript for this page
$(document).ready(function() {
    // Custom functionality
});
</script>
{% endblock %}
```

## Using Macros in Custom Templates

### Basic Macro Usage
```python
# Import macros at the top of your template
{% from "macros.html" import stat_card, data_table, connectivity_table %}

# Use macros in your template
{{ stat_card(value, "Label", "custom-class") }}

# Create data table
{% set headers = [
    {'text': 'Name', 'class': 'text-left'},
    {'text': 'Count', 'class': 'text-right'},
    {'text': 'NT', 'tooltip': 'Neurotransmitter'}
] %}
{% set rows = [...] %}  # Your data rows
{{ data_table('my-table', headers, rows) }}
```

### Custom Macro Example
```python
# Add to macros.html
{% macro analysis_card(title, data, chart_type="bar") %}
<div class="analysis-card">
    <h3>{{ title }}</h3>
    <div class="chart-container" data-chart-type="{{ chart_type }}">
        {% for item in data %}
        <div class="chart-item" data-value="{{ item.value }}">
            <span class="label">{{ item.label }}</span>
            <span class="value">{{ item.value }}</span>
        </div>
        {% endfor %}
    </div>
</div>
{% endmacro %}

# Use in template
{% from "macros.html" import analysis_card %}
{{ analysis_card("Synapse Distribution", synapse_data, "pie") }}
```

## Conditional Section Rendering

### Including Sections Based on Data Availability
```python
# Only include sections when data is available
{% if roi_summary and roi_summary|length > 0 %}
    {% include "sections/roi_innervation.html" %}
{% endif %}

{% if connectivity and (connectivity.upstream or connectivity.downstream) %}
    {% include "sections/connectivity.html" %}
{% endif %}

{% if layer_analysis and layer_analysis.containers %}
    {% include "sections/layer_analysis.html" %}
{% endif %}
```

### Custom Conditional Logic
```python
{% if neuron_type in special_neuron_types %}
    {% include "sections/special_analysis.html" %}
{% elif neuron_count > threshold %}
    {% include "sections/high_count_analysis.html" %}
{% else %}
    {% include "sections/standard_analysis.html" %}
{% endif %}
```

## JavaScript Integration

### Adding Page-Specific Scripts
```python
{% block extra_scripts %}
<script src="static/js/custom-charts.js"></script>
<script>
$(document).ready(function() {
    // Initialize custom functionality
    initializeCharts();
    
    // Custom event handlers
    $('.custom-button').click(function() {
        // Handle click
    });
});
</script>
{% endblock %}
```

### Including External Script Templates
```python
{% block extra_scripts %}
{% include "sections/custom_page_scripts.html" %}
{% endblock %}
```

## CSS Customization

### Adding Custom Styles
```python
{% block extra_head %}
<style>
.custom-section {
    background-color: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
}

.highlight-stat {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}
</style>
{% endblock %}

{% block content %}
<section class="custom-section">
    <h2>Custom Analysis</h2>
    {{ stat_card(important_value, "Important Metric", "highlight-stat") }}
</section>
{% endblock %}
```

### Including External CSS
```python
{% block css %}
{{ super() }}  <!-- Include default CSS -->
<link rel="stylesheet" href="static/css/custom-analysis.css" />
{% endblock %}
```

## Error Handling in Templates

### Safe Data Access
```python
{# Use get() method for safe dictionary access #}
{{ partner.get('type', 'Unknown') }}

{# Use default filter for None values #}
{{ neuron_count | default(0) }}

{# Conditional rendering with safe checks #}
{% if summary and summary.total_count %}
    {{ stat_card(summary.total_count, "Total") }}
{% endif %}
```

### Template Debugging
```python
{# Debug template variables #}
{% if config.debug %}
<div class="debug-info">
    <h4>Debug Information</h4>
    <pre>{{ context_vars | pprint }}</pre>
</div>
{% endif %}
```

## Performance Optimization

### Template Caching
```python
# In Python code
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(
    loader=FileSystemLoader('templates'),
    autoescape=select_autoescape(['html', 'xml']),
    cache_size=400,  # Enable template caching
    auto_reload=False  # Disable auto-reload in production
)
```

### Lazy Loading Sections
```python
{# Only process expensive sections when needed #}
{% if show_detailed_analysis %}
    {% include "sections/detailed_analysis.html" %}
{% else %}
    <div class="placeholder">
        <button onclick="loadDetailedAnalysis()">Load Detailed Analysis</button>
    </div>
{% endif %}
```

## Migration Checklist

When migrating from the original template to the refactored version:

1. ✅ Update template name in Python code
2. ✅ Verify all context variables are still provided
3. ✅ Test all conditional sections render correctly
4. ✅ Ensure JavaScript functionality works as expected
5. ✅ Validate CSS styles are applied correctly
6. ✅ Test interactive features (tables, filters, tooltips)
7. ✅ Check responsive design on different screen sizes
8. ✅ Verify all external links and resources load properly

## Template Development Workflow

1. **Start with base template**: Extend `base.html` for consistent structure
2. **Use existing sections**: Include relevant section templates
3. **Create custom sections**: Add new sections in `templates/sections/`
4. **Leverage macros**: Use existing macros for consistency
5. **Add interactivity**: Include JavaScript in `extra_scripts` block
6. **Test thoroughly**: Verify all functionality works correctly
7. **Document changes**: Update this file with new examples