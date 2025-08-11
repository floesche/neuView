# Column-Based ROI Analysis Feature

## Overview

The Column-Based ROI Analysis feature provides specialized analysis for neurons with synapses in column-structured Regions of Interest (ROIs). This feature specifically targets ROIs that follow the naming pattern `(ME|LO|LOP)_[RL]_col_HEX1_HEX2`, where:

- **Region**: `ME` (Medulla), `LO` (Lobula), or `LOP` (Lobula Plate)
- **Side**: `L` (Left) or `R` (Right)
- **Column Identifier**: `col_HEX1_HEX2` where HEX1 and HEX2 are hexadecimal values representing row and column indices

## Features

### Automatic Detection
The system automatically detects neurons that have pre or post synapses in column-structured ROIs and provides additional analysis when such data is present.

### Hexagonal Grid Visualization
When neurons with column assignments are found, a hexagonal grid visualization is generated showing:

- **Spatial Layout**: Hexagonal grid where 30° dimension represents row (HEX1) and 150° dimension represents column (HEX2)
- **Color Coding**: White to red gradient representing mean total synapses per neuron
- **Interactive Elements**: Hover tooltips with detailed column information
- **Visual Mapping**: Each hexagon represents a column with specific coordinates
- **Numeric Labels**: Mean synapse count displayed within each hexagon

### Summary Statistics
- Total number of columns with neuron assignments
- Total neurons that have column assignments
- Average number of neurons per column
- Average number of synapses per column
- Region-specific statistics

### Region Summary
Aggregated statistics grouped by brain region (ME, LO, LOP) showing:
- Number of columns per region
- Total neurons per region
- Sides represented (L, R, or both)
- Average metrics per column within each region

## Implementation Details

### Pattern Matching
The feature uses a regular expression to identify column ROIs:
```regex
^(ME|LO|LOP)_([RL])_col_([A-Fa-f0-9]+)_([A-Fa-f0-9]+)$
```

### Data Processing
1. **ROI Filtering**: Identifies ROIs matching the column pattern
2. **Coordinate Extraction**: Extracts region, side, and hex coordinates
3. **Decimal Conversion**: Converts hex coordinates to decimal for sorting
4. **Aggregation**: Groups data by column coordinates
5. **Statistics Calculation**: Computes mean synapses per neuron per column

### Code Integration
The feature is integrated into:
- **PageGenerator**: `_analyze_column_roi_data()` method
- **HTML Templates**: Additional table section with interactive features
- **JSON Export**: Column analysis data included in generated JSON files

## Usage

### Automatic Activation
The column analysis feature activates automatically when:
1. Neuron data contains ROI information
2. ROIs matching the column pattern are detected
3. Neurons have synapses in the detected column ROIs

### HTML Output
When active, the feature adds a new section to generated HTML pages:
- **Column-Based ROI Analysis** section with hexagonal grid visualization
- Interactive SVG grid showing spatial organization of columns
- Color-coded hexagons representing synapse density
- Collapsible detailed table for numerical data
- Summary statistics cards and region-specific breakdown

### JSON Output
Column analysis data is included in JSON exports under the `column_analysis` key:
```json
{
  "column_analysis": {
    "columns": [
      {
        "region": "ME",
        "side": "L",
        "row_hex": "A",
        "col_hex": "1",
        "row_dec": 10,
        "col_dec": 1,
        "column_name": "ME_L_col_A_1",
        "neuron_count": 2,
        "total_pre": 55,
        "total_post": 65,
        "total_synapses": 120,
        "mean_pre_per_neuron": 27.5,
        "mean_post_per_neuron": 32.5,
        "mean_total_per_neuron": 60.0
      }
    ],
    "summary": {
      "total_columns": 9,
      "total_neurons_with_columns": 11,
      "avg_neurons_per_column": 1.2,
      "avg_synapses_per_column": 61.3,
      "regions": {
        "ME": {
          "columns": 4,
          "neurons": 5,
          "synapses": 245,
          "sides": ["L", "R"],
          "avg_neurons_per_column": 1.2,
          "avg_synapses_per_column": 61.25
        }
      }
    },
    "hexagonal_grid": "<svg>...</svg>"
  }
}
```

## Example ROI Names

### Valid Column ROIs
- `ME_L_col_A_1` - Medulla, Left, Row A (10), Column 1
- `LO_R_col_FF_2A` - Lobula, Right, Row FF (255), Column 2A (42)
- `LOP_L_col_1_B` - Lobula Plate, Left, Row 1, Column B (11)

### Invalid ROI Names (Ignored)
- `ME_L_not_column` - Missing "col" keyword
- `OTHER_L_col_A_1` - Invalid region (not ME/LO/LOP)
- `ME_X_col_A_1` - Invalid side (not L/R)
- `ME_L_col_G_Z` - Invalid hex characters

## Benefits

1. **Visual Spatial Organization**: Hexagonal grid provides intuitive spatial representation of columnar structure
2. **Retinotopic Mapping**: Clear visualization of how columns map to visual field positions
3. **Synapse Density Patterns**: Color coding reveals patterns in synaptic processing intensity
4. **Interactive Analysis**: Hover tooltips provide detailed information for each column
5. **Biological Insight**: 30°/150° orientation reflects natural hexagonal organization in visual systems
6. **Comparative Analysis**: Easy visual comparison of synaptic densities across regions
7. **Publication Ready**: High-quality SVG output suitable for scientific publications

## Technical Requirements

- Pandas for data manipulation
- Regular expressions for pattern matching
- Pygal for SVG hexagonal grid generation
- Mathematical functions (math, colorsys) for coordinate and color calculations
- Jinja2 templates for HTML generation
- SVG rendering capabilities in web browsers

## Testing

The feature includes comprehensive tests in `test_column_analysis/test_column_analysis.py` that validate:
- Pattern matching accuracy
- Data aggregation correctness
- Statistics calculations
- Edge case handling (empty data, no matches)
- Integration with existing workflow

## Future Enhancements

Potential improvements could include:
- Interactive zoom and pan functionality for large grids
- Animation of temporal synapse changes
- 3D hexagonal prism visualization showing depth information
- Customizable color schemes and scaling options
- Export to specialized formats (PDF, PNG, interactive HTML widgets)
- Integration with neuroanatomy databases for coordinate validation
- Cross-neuron type column comparison overlays
- Statistical clustering analysis with visual highlighting