# ROI Query Strategy Integration Guide

This guide shows how to integrate the new ROI query strategy architecture into your existing page generation workflow.

## Architecture Overview

The ROI query strategy pattern provides dataset-specific logic for:
- Defining what constitutes "central brain" regions
- Categorizing ROIs into functional groups
- Filtering ROIs by type (layers, columns, ROIs)
- Handling dataset-specific naming conventions

## Integration Points

### 1. In PageGenerator Class

Update your `PageGenerator` to use dataset-specific ROI strategies:

```python
def _get_dataset_specific_roi_analysis(self, connector, roi_counts_df, neurons_df):
    """Get ROI analysis using dataset-specific strategies."""
    from .dataset_adapters import DatasetAdapterFactory
    
    # Get the appropriate adapter for this dataset
    dataset_name = connector.config.neuprint.dataset
    adapter = DatasetAdapterFactory.create_adapter(dataset_name)
    
    # Extract all ROI names from the data
    if roi_counts_df is not None and not roi_counts_df.empty:
        all_rois = roi_counts_df['roi'].unique().tolist()
    else:
        return {}
    
    # Use dataset-specific queries
    roi_analysis = {
        'central_brain_rois': adapter.query_central_brain_rois(all_rois),
        'primary_rois': adapter.query_primary_rois(all_rois),
        'roi_categories': adapter.categorize_rois(all_rois),
        'layer_rois': adapter.filter_rois_by_type(all_rois, 'layers'),
        'column_rois': adapter.filter_rois_by_type(all_rois, 'columns')
    }
    
    return roi_analysis
```

### 2. Update _get_primary_rois Method

Replace the existing hard-coded primary ROI logic:

```python
def _get_primary_rois(self, connector):
    """Get primary ROIs using dataset-specific strategy."""
    from .dataset_adapters import DatasetAdapterFactory
    
    dataset_name = connector.config.neuprint.dataset
    adapter = DatasetAdapterFactory.create_adapter(dataset_name)
    
    try:
        # First try to get ROIs from NeuPrint hierarchy
        roi_hierarchy = fetch_roi_hierarchy(mark_primary=True)
        if roi_hierarchy:
            all_rois = self._extract_roi_names_from_hierarchy(roi_hierarchy)
            return adapter.query_primary_rois(all_rois)
    except Exception as e:
        print(f"Warning: Could not fetch ROIs from NeuPrint: {e}")
    
    # Fallback: return empty list and let dataset adapter handle it
    return []
```

### 3. Central Brain Analysis

Add a new method for central brain analysis:

```python
def _analyze_central_brain_roi_data(self, roi_counts_df, neurons_df, soma_side, connector):
    """Analyze central brain ROI data using dataset-specific definitions."""
    if roi_counts_df is None or roi_counts_df.empty:
        return None
    
    from .dataset_adapters import DatasetAdapterFactory
    
    dataset_name = connector.config.neuprint.dataset
    adapter = DatasetAdapterFactory.create_adapter(dataset_name)
    
    # Filter for specific soma side
    if 'bodyId' in neurons_df.columns and 'bodyId' in roi_counts_df.columns:
        soma_side_body_ids = set(neurons_df['bodyId'].values)
        roi_counts_filtered = roi_counts_df[roi_counts_df['bodyId'].isin(soma_side_body_ids)]
    else:
        roi_counts_filtered = roi_counts_df
    
    if roi_counts_filtered.empty:
        return None
    
    # Get all ROIs and identify central brain ROIs
    all_rois = roi_counts_filtered['roi'].unique().tolist()
    central_brain_rois = adapter.query_central_brain_rois(all_rois)
    
    # Filter for central brain ROIs only
    central_brain_data = roi_counts_filtered[
        roi_counts_filtered['roi'].isin(central_brain_rois)
    ]
    
    if central_brain_data.empty:
        return None
    
    # Aggregate synapse data
    central_brain_aggregated = central_brain_data.groupby('roi').agg({
        'pre': 'sum',
        'post': 'sum',
    }).reset_index()
    
    # Calculate total synapses per ROI
    central_brain_aggregated['total'] = (
        central_brain_aggregated['pre'] + central_brain_aggregated['post']
    )
    
    # Sort by total synapse count
    central_brain_aggregated = central_brain_aggregated.sort_values(
        'total', ascending=False
    )
    
    return {
        'data': central_brain_aggregated.to_dict('records'),
        'total_central_brain_rois': len(central_brain_rois),
        'total_synapses': central_brain_aggregated['total'].sum(),
        'dataset_strategy': adapter.dataset_info.name if adapter.dataset_info else 'unknown'
    }
```

### 4. Update Template Context

Modify your template context to include the new ROI analysis:

```python
def _build_template_context(self, neuron_type_obj, connector, image_format='svg', embed_images=False):
    """Build template context with dataset-specific ROI analysis."""
    
    # ... existing context building ...
    
    # Add dataset-specific ROI analysis
    roi_analysis = self._get_dataset_specific_roi_analysis(
        connector, 
        neuron_type_obj._roi_counts,
        neuron_type_obj._neurons
    )
    
    # Add central brain analysis
    central_brain_analysis = self._analyze_central_brain_roi_data(
        neuron_type_obj._roi_counts,
        neuron_type_obj._neurons,
        neuron_type_obj.soma_side,
        connector
    )
    
    context.update({
        'roi_analysis': roi_analysis,
        'central_brain_analysis': central_brain_analysis,
        'dataset_name': connector.config.neuprint.dataset,
        # ... other context items ...
    })
    
    return context
```

## Template Updates

### Add ROI Category Display

In your HTML templates, you can now display ROI categories:

```html
<!-- Dataset-specific ROI Categories -->
{% if roi_analysis and roi_analysis.roi_categories %}
<div class="roi-categories">
    <h3>ROI Categories</h3>
    {% for category, rois in roi_analysis.roi_categories.items() %}
        {% if rois %}
        <div class="roi-category">
            <h4>{{ category|title }}</h4>
            <ul>
                {% for roi in rois|sort %}
                <li>{{ roi }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
    {% endfor %}
</div>
{% endif %}
```

### Central Brain Section

```html
<!-- Central Brain Analysis -->
{% if central_brain_analysis %}
<div class="central-brain-analysis">
    <h3>Central Brain Regions</h3>
    <p>Strategy: {{ central_brain_analysis.dataset_strategy }}</p>
    <p>Total Central Brain ROIs: {{ central_brain_analysis.total_central_brain_rois }}</p>
    <p>Total Synapses: {{ central_brain_analysis.total_synapses }}</p>
    
    {% if central_brain_analysis.data %}
    <table class="central-brain-table">
        <thead>
            <tr>
                <th>ROI</th>
                <th>Pre</th>
                <th>Post</th>
                <th>Total</th>
            </tr>
        </thead>
        <tbody>
            {% for roi_data in central_brain_analysis.data %}
            <tr>
                <td>{{ roi_data.roi }}</td>
                <td>{{ roi_data.pre }}</td>
                <td>{{ roi_data.post }}</td>
                <td>{{ roi_data.total }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}
</div>
{% endif %}
```

## Configuration Updates

### Add ROI Strategy Settings

You can add ROI-specific settings to your configuration files:

```yaml
# config.optic-lobe.yaml
neuprint:
  server: "neuprint.janelia.org"
  dataset: "optic-lobe:v1.1"

roi_analysis:
  # Override default ROI strategy settings
  include_central_brain: true
  include_layer_analysis: true
  include_column_analysis: true
  # Minimum synapse count for ROI inclusion
  min_roi_synapses: 10
  # Maximum number of ROIs to display in each category
  max_rois_per_category: 20

# config.cns.yaml
roi_analysis:
  include_central_brain: true
  include_layer_analysis: false  # CNS doesn't have layer structure
  include_column_analysis: false
  min_roi_synapses: 5
```

## Usage Examples

### Generate Page with Custom ROI Analysis

```python
from src.quickpage.dataset_adapters import DatasetAdapterFactory

def generate_page_with_roi_analysis(neuron_type, dataset_name):
    """Generate page with dataset-specific ROI analysis."""
    
    # Get appropriate adapter
    adapter = DatasetAdapterFactory.create_adapter(dataset_name)
    
    # ... get neuron data ...
    
    # Analyze ROIs using dataset strategy
    all_rois = roi_data['roi'].unique().tolist()
    roi_categories = adapter.categorize_rois(all_rois)
    
    # Generate different sections based on dataset capabilities
    if 'layers' in roi_categories and roi_categories['layers']:
        # Generate layer analysis (for optic-lobe)
        layer_analysis = analyze_layer_structure(roi_categories['layers'])
    
    if 'central_brain' in roi_categories:
        # Generate central brain analysis
        central_analysis = analyze_central_brain(roi_categories['central_brain'])
    
    # ... rest of page generation ...
```

### Query Specific ROI Types

```python
def get_connectivity_by_roi_type(neuron_type, dataset_name, roi_type):
    """Get connectivity data filtered by ROI type."""
    
    adapter = DatasetAdapterFactory.create_adapter(dataset_name)
    
    # Get neuron data
    neuron_data = connector.get_neuron_data(neuron_type)
    roi_df = neuron_data['roi_counts']
    
    # Get all ROIs
    all_rois = roi_df['roi'].unique().tolist()
    
    # Filter by specific type
    target_rois = adapter.filter_rois_by_type(all_rois, roi_type)
    
    # Filter connectivity data
    filtered_connectivity = roi_df[roi_df['roi'].isin(target_rois)]
    
    return filtered_connectivity
```

## Benefits

This architecture provides:

1. **Dataset Flexibility**: Each dataset can define its own ROI categorization logic
2. **Maintainability**: ROI logic is centralized in strategy classes
3. **Extensibility**: Easy to add new datasets or modify existing ones
4. **Consistency**: Same interface for all datasets
5. **Testability**: Each strategy can be unit tested independently

## Migration Strategy

To migrate existing code:

1. Replace hard-coded ROI lists with dataset adapter queries
2. Update template contexts to use the new ROI analysis structure
3. Modify templates to display ROI categories appropriately
4. Test with each supported dataset to ensure correctness
5. Add configuration options for ROI analysis settings

The existing functionality will continue to work, but you'll get enhanced, dataset-specific ROI analysis.