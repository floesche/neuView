# QuickPage CLI Options

This document describes the command-line interface options for QuickPage, with emphasis on the new image format and embedding options.

## Generate Command

The `generate` command creates HTML pages for neuron types with various visualization options.

### Basic Usage

```bash
quickpage generate --neuron-type T4
```

### Image Format Options

#### `--image-format [svg|png]`

Controls the format of hexagon grid visualizations.

- **Default**: `svg`
- **Options**: `svg`, `png`

```bash
# Generate with SVG hexagon grids (default)
quickpage generate --neuron-type T4 --image-format svg

# Generate with PNG hexagon grids  
quickpage generate --neuron-type T4 --image-format png
```

**SVG Format:**
- Smaller file sizes
- Scalable vector graphics
- Better for simple visualizations
- Interactive tooltips work in browsers
- Best for web display

**PNG Format:**
- Raster images with fixed resolution
- Better for complex visualizations with many hexagons
- Consistent appearance across all platforms
- Larger file sizes
- Good for print or presentations

#### `--embed`

Controls whether images are embedded directly in HTML or saved as separate files.

- **Default**: `false` (save to files)
- **When specified**: Images are embedded directly in HTML

```bash
# Save hexagon grids as separate files (default)
quickpage generate --neuron-type T4

# Embed hexagon grids directly in HTML
quickpage generate --neuron-type T4 --embed
```

**File Mode (default `--embed` not specified):**
- Images saved to `output/static/images/`
- HTML references image files
- Smaller HTML file size
- Images can be used separately
- Better for web deployment with static assets

**Embed Mode (`--embed` specified):**
- Images embedded directly in HTML
- Single self-contained HTML file
- Larger HTML file size
- Easier to share/distribute
- No external dependencies

### Usage Examples

#### Default Behavior
```bash
quickpage generate --neuron-type T4
# Result: SVG files saved to output/static/images/
#         HTML references these files
```

#### PNG Files to Disk
```bash
quickpage generate --neuron-type T4 --image-format png
# Result: PNG files saved to output/static/images/
#         HTML references these files
```

#### SVG Embedded in HTML
```bash
quickpage generate --neuron-type T4 --embed
# Result: SVG content embedded directly in HTML
#         No separate image files created
```

#### PNG Embedded in HTML
```bash
quickpage generate --neuron-type T4 --image-format png --embed
# Result: PNG data URLs embedded directly in HTML
#         No separate image files created
```

#### Multiple Types with Custom Options
```bash
quickpage generate --image-format png --embed --soma-side left
# Result: Auto-discover types, generate with PNG embedded
```

### File Organization

When using file mode (`--embed` not specified), files are organized as:

```
output/
├── T4.html                          # Main HTML file
├── T4_left.html                     # Left-specific page
├── T4_right.html                    # Right-specific page
└── static/
    └── images/
        ├── ME_T4_left_synapse_density.svg    # SVG format
        ├── ME_T4_left_cell_count.svg
        ├── LO_T4_left_synapse_density.png    # PNG format  
        ├── LO_T4_left_cell_count.png
        └── ...
```

### Other Generate Options

#### Basic Options
- `--neuron-type TEXT`: Specific neuron type to generate
- `--soma-side [left|right|middle|both|all]`: Soma side filter (default: all)
- `--output-dir TEXT`: Custom output directory

#### Advanced Options
#### Configuration
- `-c, --config TEXT`: Configuration file path
- `-v, --verbose`: Enable verbose output

### Complete Example

```bash
quickpage generate \
  --neuron-type T4 \
  --soma-side left \
  --image-format png \
  --embed \
  --output-dir ./results \
  --verbose
```

This generates a T4 left hemisphere page with PNG hexagon grids embedded directly in the HTML, saving only neurons with 100+ synapses, with verbose output.

## Migration from Previous Versions

### Old Behavior
Previously, hexagon grids were always generated as SVG files saved to disk.

### New Behavior
You can now:
1. Choose between SVG and PNG formats
2. Choose between file saving and HTML embedding
3. Customize the behavior per generation run

### Backward Compatibility
The default behavior remains the same as before:
- SVG format
- Files saved to disk
- HTML references the files

Existing scripts and workflows continue to work without changes.

## Performance Considerations

### SVG vs PNG
- **SVG**: Faster generation, smaller files, scalable
- **PNG**: Slower generation, larger files, fixed resolution, better for complex grids

### File vs Embed
- **File Mode**: Faster HTML generation, smaller HTML files, better for web deployment
- **Embed Mode**: Slower HTML generation, larger HTML files, better for distribution

### Recommendations
- **Development/Testing**: Use SVG with embed for quick iterations
- **Production Web**: Use SVG with files for performance
- **Documentation/Reports**: Use PNG with embed for self-contained files
- **Print Materials**: Use PNG with files for consistent quality