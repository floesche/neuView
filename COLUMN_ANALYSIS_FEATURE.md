# Column-Based ROI Analysis Feature

## Overview

The Column-Based ROI Analysis feature provides specialized analysis for neurons with synapses in column-structured Regions of Interest (ROIs). This feature specifically targets ROIs that follow the naming pattern `(ME|LO|LOP)_[RL]_col_HEX1_HEX2`, where:

- **Region**: `ME` (Medulla), `LO` (Lobula), or `LOP` (Lobula Plate)
- **Side**: `L` (Left) or `R` (Right)
- **Column Identifier**: `col_HEX1_HEX2` where HEX1 and HEX2 are hexadecimal values representing row and column indices

## Features

### Automatic Detection
The system automatically detects neurons that have pre or post synapses in column-structured ROIs and provides additional analysis when such data is present.

### Column Analysis Table
When neurons with column assignments are found, an additional table is generated showing:

- **Column Information**: Region, side, row/column coordinates (both hex and decimal)
- **Neuron Counts**: Number of neurons with synapses in each column
- **Synapse Totals**: Total pre, post, and combined synapses per column
- **Mean Synapses**: Average number of synapses per neuron for each column

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
- **Column-Based ROI Analysis** section appears after the standard ROI table
- Interactive DataTable with sorting and filtering capabilities
- Summary statistics cards
- Region-specific breakdown table

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
    }
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

1. **Retinotopic Analysis**: Enables analysis of retinotopic organization in visual system neurons
2. **Spatial Distribution**: Shows how neurons are distributed across columnar structures
3. **Connectivity Patterns**: Reveals column-specific connectivity preferences
4. **Comparative Analysis**: Allows comparison of synaptic densities between columns
5. **Data Export**: Provides structured data for further computational analysis

## Technical Requirements

- Pandas for data manipulation
- Regular expressions for pattern matching
- Jinja2 templates for HTML generation
- DataTables for interactive table features

## Testing

The feature includes comprehensive tests in `test_column_analysis/test_column_analysis.py` that validate:
- Pattern matching accuracy
- Data aggregation correctness
- Statistics calculations
- Edge case handling (empty data, no matches)
- Integration with existing workflow

## Future Enhancements

Potential improvements could include:
- Visualization of columnar organization
- Statistical analysis of column preferences
- Export to specialized formats (e.g., for retinotopic mapping tools)
- Integration with 3D visualization systems
- Cross-neuron type column comparison analysis