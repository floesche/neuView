# Hexagon Grid Visualization

This module provides hexagonal grid visualization capabilities for neuron column data analysis. The `HexagonGridGenerator` class supports both SVG and PNG output formats with consistent styling and color mapping.

## Features

- **SVG Generation**: Direct SVG creation with embedded tooltips and interactive elements
- **PNG Generation**: High-quality PNG output using pygal with customizable styling  
- **Consistent Color Mapping**: 5-tier color scheme from light to dark red based on data values
- **Region-Specific Grids**: Separate visualizations for different brain regions (ME, LO, LOP)
- **Multiple Metrics**: Support for both synapse density and cell count visualizations
- **Global Color Scaling**: Consistent color ranges across all regions for easy comparison

## Quick Start

```python
from quickpage.visualization import HexagonGridGenerator

# Initialize the generator
generator = HexagonGridGenerator()

# Sample column data
column_data = [
    {
        'hex1_dec': 31, 'hex2_dec': 16, 'region': 'ME', 'side': 'left',
        'hex1': '1F', 'hex2': '10', 'total_synapses': 1200, 'neuron_count': 45,
        'column_name': 'ME_L_1F_10'
    },
    # ... more data
]

# Generate region-specific grids (SVG)
region_grids = generator.generate_region_hexagonal_grids(
    column_data, 
    neuron_type="T4", 
    soma_side="left",
    output_format="svg"
)

# Access generated content
for region, grids in region_grids.items():
    svg_synapse = grids['synapse_density']
    svg_cells = grids['cell_count']
```

## API Reference

### HexagonGridGenerator

Main class for generating hexagonal grid visualizations.

#### Constructor

```python
HexagonGridGenerator(hex_size: int = 6, spacing_factor: float = 1.1)
```

- `hex_size`: Size of individual hexagons in pixels
- `spacing_factor`: Spacing multiplier between hexagons

#### Methods

##### generate_region_hexagonal_grids()

```python
generate_region_hexagonal_grids(
    column_summary: List[Dict],
    neuron_type: str, 
    soma_side: str,
    output_format: str = 'svg'
) -> Dict[str, Dict[str, str]]
```

Generate separate hexagonal grids for each brain region.

**Parameters:**
- `column_summary`: List of column data dictionaries
- `neuron_type`: Type of neuron being visualized
- `soma_side`: Side of soma ('left' or 'right')
- `output_format`: Output format ('svg' or 'png')

**Returns:**
Dictionary with structure: `{region: {metric_type: visualization_content}}`

##### generate_single_region_grid()

```python
generate_single_region_grid(
    region_columns: List[Dict],
    metric_type: str,
    region_name: str,
    global_min: Optional[float] = None,
    global_max: Optional[float] = None,
    neuron_type: Optional[str] = None,
    soma_side: Optional[str] = None,
    output_format: str = 'svg'
) -> str
```

Generate a hexagonal grid for a single region.

**Parameters:**
- `region_columns`: Column data for specific region
- `metric_type`: 'synapse_density' or 'cell_count'  
- `region_name`: Name of the region (e.g., 'ME', 'LO', 'LOP')
- `global_min`/`global_max`: Values for consistent color scaling across regions
- `neuron_type`: Neuron type for labeling
- `soma_side`: Soma side for labeling
- `output_format`: Output format ('svg' or 'png')

##### create_hexagonal_visualization()

```python
create_hexagonal_visualization(
    hexagons: List[Dict],
    min_val: float,
    max_val: float,
    neuron_type: Optional[str] = None,
    output_format: str = 'svg'
) -> str
```

Create a combined hexagonal visualization from prepared hexagon data.

## Data Format

### Column Data Structure

Each column dictionary should contain:

```python
{
    'hex1_dec': int,           # Decimal hex1 coordinate
    'hex2_dec': int,           # Decimal hex2 coordinate  
    'region': str,             # Brain region ('ME', 'LO', 'LOP')
    'side': str,               # Side ('left', 'right')
    'hex1': str,               # Hex string for hex1
    'hex2': str,               # Hex string for hex2
    'total_synapses': float,   # Total synapse count
    'neuron_count': int,       # Number of neurons
    'column_name': str         # Descriptive column name
}
```

### Hexagon Data Structure

For direct hexagon visualization:

```python
{
    'x': float,                # X coordinate in pixel space
    'y': float,                # Y coordinate in pixel space
    'value': float,            # Data value for coloring
    'color': str,              # Hex color code
    'region': str,             # Brain region
    'side': str,               # Side
    'hex1': str,               # Hex1 identifier
    'hex2': str,               # Hex2 identifier
    'neuron_count': int,       # Number of neurons
    'column_name': str         # Column identifier
}
```

## Output Formats

### SVG Output

- Direct SVG markup as string
- Embedded tooltips on hover
- Scalable vector graphics
- Small file sizes
- Web-friendly

### PNG Output

- Base64-encoded PNG data
- High-quality raster images
- Fixed resolution (800x600 default)
- Suitable for reports and presentations
- Requires `cairosvg` dependency

## Color Scheme

The visualization uses a 5-tier red color scheme:

1. **#fee5d9** - Lightest (0-20th percentile)
2. **#fcbba1** - Light (20-40th percentile)
3. **#fc9272** - Medium (40-60th percentile)
4. **#ef6548** - Dark (60-80th percentile)  
5. **#a50f15** - Darkest (80-100th percentile)

Colors are assigned based on normalized data values within the global min/max range.

## Coordinate System

The hexagonal grid uses axial coordinates with the following transformations:

- **Input**: `hex1_dec`, `hex2_dec` values from column data
- **Axial**: `q = -(hex1_coord - hex2_coord) - 3`, `r = -hex2_coord`
- **Pixel**: Standard hexagonal grid pixel conversion

This ensures proper spatial relationships and visual alignment of hexagons.

## Dependencies

- `pygal`: Chart generation library
- `cairosvg`: Required for PNG output (automatically installed)
- `math`: Standard library for coordinate calculations

## Examples

See `example_hexagon_usage.py` for complete working examples demonstrating:

- Region-specific grid generation
- Both SVG and PNG output formats
- Combined visualization creation
- File saving and base64 handling

## Integration

The `HexagonGridGenerator` is integrated into the main `PageGenerator` class and replaces the previous inline hexagon generation methods. The interface remains compatible with existing code while adding new PNG generation capabilities.