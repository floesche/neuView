# Comprehensive Hexagon Grid Generation

This document describes the comprehensive hexagon grid functionality that shows all possible column coordinates across ME, LO, and LOP regions, with different visual states based on data availability.

## Overview

The comprehensive hexagon grid feature extends the existing hexagon visualization to display ALL possible column coordinates (hex1, hex2) that exist anywhere in the dataset, rather than just the columns that have data for the current neuron type. This provides a complete picture of the columnar organization across regions.

## Visual Legend

Each hexagon in the comprehensive grid represents a column coordinate and uses the following color scheme:

- **Dark Gray** (#4a4a4a): Column doesn't exist in this specific region
- **White with border** (#ffffff): Column exists in this region but has no data for the current neuron type/dataset
- **Color-coded** (red gradient): Column has data in this region for the current neuron type

## API Usage

### Basic Usage

```python
from quickpage.visualization import HexagonGridGenerator

# Initialize the generator
generator = HexagonGridGenerator()

# Your data
column_summary = [...]  # Actual column data with values
all_possible_columns = [...]  # All column coordinates found anywhere
region_columns_map = {  # Which columns exist in each region
    'ME': {(hex1_dec, hex2_dec), ...},
    'LO': {(hex1_dec, hex2_dec), ...},
    'LOP': {(hex1_dec, hex2_dec), ...}
}

# Generate comprehensive grids
grids = generator.generate_comprehensive_region_hexagonal_grids(
    column_summary=column_summary,
    all_possible_columns=all_possible_columns,
    region_columns_map=region_columns_map,
    neuron_type="T4",
    soma_side="left",
    output_format="svg",
    save_to_files=False
)
```

### Data Structures

#### column_summary
List of dictionaries containing actual data for columns:
```python
[
    {
        'hex1_dec': 31, 'hex2_dec': 16, 'region': 'ME', 'side': 'left',
        'hex1': '1F', 'hex2': '10', 'total_synapses': 1200, 'neuron_count': 45,
        'column_name': 'ME_L_1F_10'
    },
    # ... more columns with data
]
```

#### all_possible_columns
List of all possible column coordinates found anywhere in the dataset:
```python
[
    {'hex1': '1F', 'hex2': '10', 'hex1_dec': 31, 'hex2_dec': 16},
    {'hex1': '1E', 'hex2': '0F', 'hex1_dec': 30, 'hex2_dec': 15},
    # ... all possible columns
]
```

#### region_columns_map
Dictionary mapping regions to sets of column coordinates that exist in each region:
```python
{
    'ME': {(31, 16), (30, 15), (29, 14)},
    'LO': {(28, 13), (27, 12), (26, 11)},
    'LOP': {(25, 10), (24, 9)}
}
```

## Integration with PageGenerator

The `PageGenerator` class automatically collects all possible columns and generates comprehensive grids:

```python
def _analyze_column_roi_data(self, ...):
    # ... existing code ...
    
    # Get all possible columns from the dataset
    all_possible_columns, region_columns_map = self._get_all_possible_columns_from_dataset()
    
    # Generate comprehensive grids
    comprehensive_region_grids = self.hexagon_generator.generate_comprehensive_region_hexagonal_grids(
        column_summary, all_possible_columns, region_columns_map,
        neuron_type, soma_side, output_format=file_type, save_to_files=save_to_files
    )
    
    return {
        'region_grids': region_grids,  # Regular grids (data only)
        'comprehensive_region_grids': comprehensive_region_grids,  # All columns
        # ...
    }
```

## Output Formats

### SVG Format
- Scalable vector graphics suitable for web display
- Includes interactive tooltips
- Color legend and status legend
- Title and subtitle information

### PNG Format
- Raster graphics suitable for reports
- Base64 encoded for easy embedding
- Falls back to SVG if conversion libraries unavailable

## Template Integration

The comprehensive grids can be used in Jinja2 templates:

```html
<!-- Comprehensive grids showing all possible columns -->
{% if column_analysis and column_analysis.comprehensive_region_grids %}
    <h3>Complete Column Map</h3>
    {% for region in ['ME', 'LO', 'LOP'] %}
        {% if column_analysis.comprehensive_region_grids[region] %}
            <h4>{{ region }} - All Possible Columns</h4>
            <div class="grid-pair">
                <div class="grid-item">
                    <h5>Synapse Density</h5>
                    {{ column_analysis.comprehensive_region_grids[region].synapse_density|safe }}
                </div>
                <div class="grid-item">
                    <h5>Cell Count</h5>
                    {{ column_analysis.comprehensive_region_grids[region].cell_count|safe }}
                </div>
            </div>
        {% endif %}
    {% endfor %}
{% endif %}
```

## Database Query

The system automatically queries the dataset to find all possible columns:

```cypher
MATCH (n:Neuron)-[:Contains]->(r:ROI)
WHERE r.roi =~ '^(ME|LO|LOP)_[RL]_col_[A-Za-z0-9]+_[A-Za-z0-9]+$'
RETURN DISTINCT r.roi as roi
```

This finds all ROI names matching the column pattern across the entire dataset, not just for the current neuron type.

## Benefits

1. **Complete Overview**: Shows the full columnar structure across all regions
2. **Data Coverage**: Clearly indicates which columns have data vs. which are empty
3. **Regional Differences**: Highlights which columns exist in which regions
4. **Consistent Layout**: All grids use the same coordinate system for easy comparison

## Comparison with Regular Grids

| Feature | Regular Grids | Comprehensive Grids |
|---------|---------------|---------------------|
| Columns shown | Only with data | All possible columns |
| Empty regions | Not displayed | Shown as white |
| Missing columns | Not displayed | Shown as dark gray |
| Consistency | Varies by dataset | Always complete |
| Use case | Current data focus | Complete overview |

## Testing

Use the test script to verify functionality:

```bash
python test_comprehensive_hexagon_grids.py
```

This generates example grids and a comparison HTML file to demonstrate the differences between regular and comprehensive grids.