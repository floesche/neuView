# HexagonGridGenerator Usage Guide

This document describes how to use the `HexagonGridGenerator` class after the recent cleanup that simplified the API and made file saving work consistently for both PNG and SVG formats.

## Key Changes

1. **Removed `return_content` parameter** - No longer needed
2. **Simplified `save_to_files` logic** - Now works for both PNG and SVG formats
3. **Consistent file saving** - Files are saved to `output/static/images/` directory
4. **Cleaner API** - Fewer parameters, clearer behavior

## Basic Usage

### Embedded Content (Default)

When `save_to_files=False` (default), content is returned directly for embedding in HTML:

```python
from quickpage.visualization.hexagon_grid_generator import HexagonGridGenerator

generator = HexagonGridGenerator(output_dir="output")

# Generate SVG content for direct embedding
svg_grids = generator.generate_region_hexagonal_grids(
    column_data, 
    neuron_type="T4", 
    soma_side="left",
    output_format="svg",
    save_to_files=False  # Default
)

# Returns: {'ME': {'synapse_density': '<svg>...</svg>', 'cell_count': '<svg>...</svg>'}, ...}

# Generate PNG content for direct embedding  
png_grids = generator.generate_region_hexagonal_grids(
    column_data,
    neuron_type="T4",
    soma_side="left", 
    output_format="png",
    save_to_files=False  # Default
)

# Returns: {'ME': {'synapse_density': 'data:image/png;base64,...', 'cell_count': 'data:image/png;base64,...'}, ...}
```

### File Saving

When `save_to_files=True`, files are saved to disk and file paths are returned:

```python
# Save SVG files
svg_paths = generator.generate_region_hexagonal_grids(
    column_data,
    neuron_type="T4", 
    soma_side="left",
    output_format="svg",
    save_to_files=True
)

# Returns: {'ME': {'synapse_density': 'static/images/ME_T4_left_synapse_density.svg', ...}, ...}
# Files saved to: output/static/images/ME_T4_left_synapse_density.svg

# Save PNG files
png_paths = generator.generate_region_hexagonal_grids(
    column_data,
    neuron_type="T4",
    soma_side="left", 
    output_format="png",
    save_to_files=True
)

# Returns: {'ME': {'synapse_density': 'static/images/ME_T4_left_synapse_density.png', ...}, ...}
# Files saved to: output/static/images/ME_T4_left_synapse_density.png
```

## PageGenerator Integration

The `PageGenerator` class provides convenient methods that use the cleaned up API:

### Default Behavior (Embedded Content)

```python
from quickpage.page_generator import PageGenerator

page_gen = PageGenerator(config, output_dir="output")

# Generate embedded content (default)
region_grids = page_gen._generate_region_hexagonal_grids(
    column_data, "T4", "left", file_type="png"
)
# Content is embedded directly in HTML
```

### File Saving

```python
# Save files and get paths
file_paths = page_gen.generate_and_save_hexagon_grids(
    column_data, "T4", "left", file_type="png"
)
# Files are saved to output/static/images/
```

### Explicit Control

```python
# Explicit control over saving behavior
embedded_grids = page_gen._generate_region_hexagonal_grids(
    column_data, "T4", "left", 
    file_type="png", 
    save_to_files=False  # Embed content
)

saved_grids = page_gen._generate_region_hexagonal_grids(
    column_data, "T4", "left",
    file_type="png",
    save_to_files=True   # Save files
)
```

## Template Usage

The HTML template automatically handles both embedded content and file paths:

```html
<!-- Template automatically detects content type -->
{%- if grids.synapse_density | is_png_data -%}
    <!-- PNG data URL - display as image -->
    <img src="{{ grids.synapse_density }}" alt="Synapse Density" />
{%- elif grids.synapse_density.endswith('.png') -%}
    <!-- PNG file path - display as image -->
    <img src="{{ grids.synapse_density }}" alt="Synapse Density" />
{%- elif grids.synapse_density.endswith('.svg') -%}
    <!-- SVG file path - display as object -->
    <object data="{{ grids.synapse_density }}" type="image/svg+xml">
        <img src="{{ grids.synapse_density }}" alt="Synapse Density" />
    </object>
{%- else -%}
    <!-- SVG content - embed directly -->
    {{ grids.synapse_density | safe }}
{%- endif -%}
```

## File Structure

When `save_to_files=True`, files are organized as follows:

```
output/
├── neuron_page.html
└── static/
    └── images/
        ├── ME_T4_left_synapse_density.svg
        ├── ME_T4_left_cell_count.svg
        ├── LO_T4_left_synapse_density.png
        ├── LO_T4_left_cell_count.png
        └── ...
```

## Migration from Old API

### Before (deprecated)
```python
# OLD - with return_content parameter
grids = generator.generate_region_hexagonal_grids(
    data, "T4", "left", 
    output_format="svg",
    return_content=True,      # REMOVED
    save_to_files=False
)
```

### After (current)
```python
# NEW - simplified API
grids = generator.generate_region_hexagonal_grids(
    data, "T4", "left",
    output_format="svg",
    save_to_files=False  # Controls both behavior
)
```

## Best Practices

1. **For HTML embedding**: Use `save_to_files=False` (default)
2. **For external files**: Use `save_to_files=True`
3. **PNG format**: Better for complex visualizations with many hexagons
4. **SVG format**: Better for simple visualizations, smaller file sizes
5. **File organization**: Files are automatically organized in `static/images/`
6. **Template compatibility**: The template handles all formats automatically

## Error Handling

```python
try:
    grids = generator.generate_region_hexagonal_grids(
        column_data, "T4", "left", output_format="png", save_to_files=True
    )
except ValueError as e:
    print(f"Invalid parameters: {e}")
except Exception as e:
    print(f"Generation failed: {e}")
```

## Dependencies

- **For PNG generation**: Requires `pycairo` and `cairosvg`
- **For SVG generation**: No additional dependencies
- **File saving**: Requires write permissions to output directory

The API is now cleaner, more consistent, and easier to use while maintaining full backward compatibility.