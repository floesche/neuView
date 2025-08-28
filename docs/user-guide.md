# QuickPage User Guide

A modern Python CLI tool that generates HTML pages for neuron types using data from NeuPrint. This guide covers everything you need to know to install, configure, and use QuickPage effectively.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Basic Usage](#basic-usage)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)
- [Migration Guide](#migration-guide)

## Features

### Core Features
- **Modern CLI Interface**: Built with Click and async support for responsive commands
- **NeuPrint Integration**: Fetches neuron data directly from NeuPrint servers with intelligent caching
- **Dataset Adapters**: Automatically handles differences between datasets (CNS, Hemibrain, Optic-lobe)
- **HTML Generation**: Creates beautiful HTML reports using Jinja2 templates with custom filters
- **Plume CSS**: Modern, responsive design using Plume CSS framework
- **Soma Side Filtering**: Generate reports for left, right, middle, or all hemispheres
- **Persistent Cache System**: Intelligent caching reduces database load and improves performance
### Interactive Features

- **Advanced Search**: Real-time neuron type search with autocomplete and synonym support
- **Filtering System**: Filter by cell count, neurotransmitter, brain region, and more
- **Interactive Cell Count Tags**: Click any cell count number to filter by that range
- **Neuron Count Display**: Live count updates as filters are applied
- **Tooltip System**: Rich tooltips with detailed neuron information
- **Clickable Soma Sides**: Navigate between left/right hemisphere views
- **3D Visualization**: Direct links to Neuroglancer for 3D neuron viewing
- **Responsive Design**: Mobile-friendly interface with collapsible navigation

### Performance Features
- **Persistent Cache**: Up to 97.9% speed improvement for subsequent runs
- **Query Optimization**: Intelligent caching of database queries
- **Cross-session Benefits**: Cache survives application restarts
- **Memory Efficient**: Optimized data structures and caching strategies

## Installation

### Prerequisites
- Python 3.8 or higher
- Pixi package manager (recommended) or pip
- NeuPrint account and authentication token

### Installation Steps

1. **Clone the repository:**
```bash
git clone <repository-url>
cd quickpage
```

2. **Install dependencies using Pixi (recommended):**
```bash
pixi install
```

   **Alternative: Install with pip:**
```bash
pip install -e .
```

3. **Set up your NeuPrint token** (choose one method):

   **Option 1: Using .env file (recommended):**
```bash
pixi run setup-env
# Edit .env and add your NeuPrint token
```

   **Option 2: Manual .env setup:**
```bash
cp .env.example .env
# Edit .env file and add: NEUPRINT_TOKEN="your-token-here"
```

   **Option 3: Environment variable:**
```bash
export NEUPRINT_TOKEN="your-token-here"
```

   **Option 4: Configuration file:**
```bash
# Add to config.yaml:
# neuprint:
#   token: "your-token-here"
```

## Configuration

### Main Configuration File (`config.yaml`)

The main configuration file controls all aspects of QuickPage behavior:

```yaml
# NeuPrint server settings
neuprint:
  server: "neuprint.janelia.org"
  dataset: "hemibrain:v1.2.1"
  token: ""  # Optional, can use NEUPRINT_TOKEN env var

# Output settings
output:
  directory: "output"
  template_dir: "templates"
  include_3d_view: true
  generate_json: true

# Neuron types to process
neuron_types:
  - name: "LC10"
    description: "Lobula Columnar 10"
    query_type: "type"
  - name: "LPLC2"
    description: "Lobula Plate Lobula Columnar 2"
    query_type: "type"

# HTML generation settings
html:
  title_prefix: "Neuron Type Report"
  css_framework: "plume"
  include_images: true
  include_connectivity: true
```

### Custom Neuron Type Settings

You can add custom settings for specific neuron types:

```yaml
neuron_types:
  - name: "LPLC2"
    description: "Lobula Plate Lobula Columnar 2"
    query_type: "type"
    soma_side: "both"

# Additional configurations for neuron types not in the main list
custom_neuron_types:
  LC10:
    soma_side: "both"
  Dm4:
    custom_field: "value"
```

### Dataset-Specific Configurations

QuickPage includes pre-configured settings for different datasets:

- `config.cns.yaml` - Central Nervous System dataset
- `config.optic-lobe.yaml` - Optic Lobe dataset
- `config.example.yaml` - Template configuration

Use a specific configuration:
```bash
quickpage -c config.optic-lobe.yaml generate -n Tm1
```

## Basic Usage

### Quick Start

1. **Test your connection:**
```bash
pixi run test-connection
# or
quickpage test-connection
```

2. **List available neuron types:**
```bash
quickpage list-types
```

3. **Generate a single neuron type:**
```bash
quickpage generate -n Dm4
```

4. **Generate multiple neuron types:**
```bash
quickpage generate -n Dm4,Tm1,LC10
```

5. **View your results:**
Open `output/index.html` in your browser to see the generated reports.

### CLI Commands

#### Test Connection
```bash
quickpage test-connection
```
Verifies connectivity to NeuPrint server and validates your token.

#### List Available Neuron Types
```bash
# List all types
quickpage list-types

# List with details
quickpage list-types --detailed

# Filter by pattern
quickpage list-types --filter "LC*"
```

#### Generate HTML Pages
```bash
# Generate single neuron type
quickpage generate -n Dm4

# Generate multiple types
quickpage generate -n "Dm4,Tm1,LC10"

# Generate with verbose output
quickpage --verbose generate -n Dm4

# Generate specific soma side
quickpage generate -n Dm4 --soma-side left
```

#### Inspect Neuron Types
```bash
# Get basic information
quickpage inspect Dm4

# Get detailed connectivity
quickpage inspect Dm4 --detailed

# Get ROI information
quickpage inspect Dm4 --roi-info
```

### Cache Management

QuickPage includes a sophisticated caching system for optimal performance:

```bash
# View comprehensive cache statistics
quickpage cache --action stats

# Clear all cache types
quickpage cache --action clear

# Clean expired cache entries only
quickpage cache --action clean

# Clear cache for specific neuron type
quickpage cache --action clear --neuron-type AOTU019
```

**Cache Performance Benefits:**
- Up to 97.9% speed improvement on subsequent runs
- Cross-session persistence (cache survives restarts)
- Multiple cache types: neuron data, ROI hierarchy, columns, soma sides
- Automatic expiration: Different TTL for different cache types

## Advanced Usage

### Verbose Mode

Enable verbose output to see detailed progress and performance metrics:

```bash
quickpage --verbose generate -n Dm4
```

This shows:
- Database query details
- Cache hit/miss statistics
- Processing time for each step
- Memory usage information

### Custom Configuration

Create and use custom configuration files:

```bash
# Create custom config
cp config.example.yaml my-config.yaml
# Edit my-config.yaml

# Use custom config
quickpage -c my-config.yaml generate -n Dm4
```

### Pixi Task Shortcuts

QuickPage includes convenient Pixi tasks for common operations:

```bash
# Development shortcuts
pixi run test-connection    # Test NeuPrint connection
pixi run generate-sample   # Generate sample neuron types
pixi run clean-output     # Clean output directory
pixi run lint             # Run code linting
pixi run test             # Run test suite

# Example generations
pixi run dm4              # Generate Dm4 neuron type
pixi run tm1              # Generate Tm1 neuron type
pixi run lc10             # Generate LC10 neuron type
```

### Batch Processing

Process multiple neuron types efficiently:

```bash
# Using comma-separated list
quickpage generate -n "Dm4,Tm1,Tm2,LC10,LPLC2"

# Using configuration file
# Add multiple entries to config.yaml neuron_types section
quickpage create-list

# Using queue system for batch processing
quickpage fill-queue --all  # Populate queue with all available types
quickpage pop              # Process next item in queue
```

### Soma Side Processing

Generate reports for specific hemisphere or all:

```bash
# Left hemisphere only
quickpage generate -n Dm4 --soma-side left

# Right hemisphere only  
quickpage generate -n Dm4 --soma-side right

# Both hemispheres (default)
quickpage generate -n Dm4 --soma-side both

# Middle (for neurons with middle soma)
quickpage generate -n SomeType --soma-side middle
```

## Troubleshooting

### Common Issues

#### Authentication Problems
**Problem**: "Authentication failed" or "Invalid token"
**Solution**: 
1. Verify your token is correct
2. Check token hasn't expired
3. Ensure token is properly set in environment or config

#### Connection Issues
**Problem**: "Failed to connect to NeuPrint server"
**Solution**:
1. Check internet connection
2. Verify server URL in config
3. Test with: `quickpage test-connection`

#### Missing Neuron Types
**Problem**: "Neuron type not found" 
**Solution**:
1. List available types: `quickpage list-types`
2. Check spelling and case sensitivity
3. Verify neuron type exists in your dataset

#### Cache Issues
**Problem**: Outdated or corrupted cache
**Solution**:
1. Clear cache: `quickpage cache --action clear`
2. Clean expired entries: `quickpage cache --action clean`
3. Check cache stats: `quickpage cache --action stats`

#### Performance Issues
**Problem**: Slow generation times
**Solution**:
1. Enable caching (default)
2. Use verbose mode to identify bottlenecks
3. Clear and rebuild cache if corrupted
4. Check network connectivity to NeuPrint

### Debug Mode

Enable debug mode for detailed troubleshooting:

```bash
# Enable debug logging
export QUICKPAGE_DEBUG=1
quickpage --verbose generate -n Dm4

# Or use Python logging
python -m quickpage --verbose generate -n Dm4
```

### File Organization

QuickPage organizes output files in a logical structure:

```
output/
├── index.html              # Main navigation page with search
├── types.html              # Filterable neuron types list
├── help.html               # Help and documentation
├── types/                  # Individual neuron pages
│   ├── Dm4_L.html         # Left hemisphere specific
│   ├── Dm4_R.html         # Right hemisphere specific
│   ├── Dm4_both.html      # Both hemispheres
│   └── ...
├── eyemaps/                # Eyemap images
│   ├── Dm4_eyemap.svg
│   └── ...
├── static/                 # CSS, JS, and other assets
│   ├── css/
│   ├── js/
│   │   └── neuron-search.js # Generated search functionality
│   └── images/
├── .cache/                 # Cache files (hidden)
│   ├── neuron_data/
│   ├── columns/
│   ├── soma_sides/
│   └── roi_hierarchy/
└── .queue/                 # Queue system (hidden)
    └── queue.yaml          # Neuron types queue
```

### Getting Help

If you encounter issues:

1. **Check the help page**: Open `output/help.html` for built-in documentation
2. **Use verbose mode**: Add `--verbose` flag for detailed output
3. **Check cache status**: Use `quickpage cache --action stats`
4. **Test connection**: Run `quickpage test-connection`
5. **Review configuration**: Verify your `config.yaml` settings
6. **Search functionality**: Ensure `neuron-search.js` is generated in `output/static/js/`
7. **Queue system**: Check `.queue/queue.yaml` for batch processing issues

## Migration Guide

### Migrating from Previous Versions

If you're upgrading from an older version of QuickPage, you may need to migrate your directory structure and understand new features.

#### Directory Structure Changes

Recent versions organize output files differently:
- **Neuron pages** moved from `output/` to `output/types/`
- **Eyemap images** moved from `output/static/images/` to `output/eyemaps/`
- **Main pages** remain in `output/` (index.html, types.html, help.html)
- **Search functionality** added in `output/static/js/neuron-search.js`
- **Queue system** added in `output/.queue/queue.yaml`
- **Enhanced caching** with multiple cache types in `output/.cache/`

#### Migration Steps

1. **Backup your existing output:**
```bash
cp -r output output_backup
```

2. **Move neuron pages to types/ subdirectory:**
```bash
mkdir -p output/types
find output -maxdepth 1 -name "*.html" \
  ! -name "index.html" \
  ! -name "types.html" \
  ! -name "help.html" \
  -exec mv {} output/types/ \;
```

3. **Move eyemap images to eyemaps/ subdirectory:**
```bash
mkdir -p output/eyemaps
if [ -d "output/static/images" ]; then
  mv output/static/images/* output/eyemaps/ 2>/dev/null || true
  rmdir output/static/images 2>/dev/null || true
fi
```

4. **Regenerate the index:**
```bash
quickpage create-list
```

#### Verification

After migration, verify everything works:

```bash
# Check directory structure
ls -la output/
ls -la output/types/
ls -la output/eyemaps/

# Test in browser
# Open output/index.html and verify all links work
```

#### Web Server Configuration

If you're using a web server, you may need to add redirects for old URLs:

**Apache (.htaccess):**
```apache
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteRule ^([^/]+\.html)$ types/$1 [R=301,L]
RewriteCond %{REQUEST_URI} !^/(index|types|help)\.html$
RewriteRule ^static/images/(.+)$ eyemaps/$1 [R=301,L]
```

**Nginx:**
```nginx
location ~ ^/([^/]+\.html)$ {
    if ($uri !~ ^/(index|types|help)\.html$) {
        return 301 /types$uri;
    }
}
location ~ ^/static/images/(.+)$ {
    return 301 /eyemaps/$1;
}
```

### Rollback Plan

If migration causes issues, you can rollback:

```bash
# Stop web server if applicable
sudo systemctl stop apache2  # or nginx

# Restore from backup
rm -rf output
mv output_backup output

# Restart web server
sudo systemctl start apache2  # or nginx
```

## Advanced Features

### Neuron Type Search

QuickPage includes a powerful search system that helps you quickly find specific neuron types:

#### Features
- **Real-time Search**: Suggestions appear as you type
- **Intelligent Ranking**: Exact matches first, then starts-with, then contains
- **Synonym Support**: Search by alternative names and FlyWire tags
- **Keyboard Navigation**: Use arrow keys, Enter, and Escape
- **Smart File Detection**: Automatically finds the correct HTML file

#### Usage
1. **Access Search**: Click in the search box in the page header
2. **Start Typing**: Enter neuron type name or synonym
3. **Navigate Results**: Use arrow keys or mouse to select
4. **Quick Access**: Press Enter or click to navigate to neuron page

#### Search Data Sources
- Primary: `.queue/queue.yaml` file (populated during generation)
- Fallback: Built-in list of common neuron types
- Enhanced: Synonyms and FlyWire tag integration

### Hemisphere Balance Analysis

Individual neuron pages include sophisticated hemisphere balance analysis:

#### Features
- **Log Ratio Calculation**: Quantitative measure of hemisphere bias
- **Balance Interpretation**: Human-readable descriptions (balanced, left bias, right bias)
- **Consistent Display**: Same values shown across all soma side pages
- **Interactive Navigation**: Click between left/right hemisphere views

#### Understanding Balance Metrics
- **Log Ratio = 0**: Perfectly balanced between hemispheres
- **Positive Values**: Left hemisphere bias
- **Negative Values**: Right hemisphere bias
- **Values > ±1.0**: Strong bias (2:1 ratio or greater)

### 3D Visualization Integration

QuickPage provides seamless integration with Neuroglancer for 3D neuron visualization:

#### Features
- **Direct Links**: One-click access to 3D visualization
- **Soma Side Specific**: Separate links for left/right hemisphere views
- **Color Coding**: Different colors for different soma sides
- **Context Options**: Include brain slices and anatomical context
- **Dataset Optimization**: Specialized configurations for different datasets

#### Usage
1. **Open Neuron Page**: Navigate to any neuron type page
2. **Find 3D Section**: Look for "3D Visualization" or Neuroglancer links
3. **Choose View**: Select all neurons or specific hemisphere
4. **Customize**: Toggle brain context and slice visibility options

### Queue System for Batch Processing

The queue system enables efficient batch processing of multiple neuron types:

#### Commands
```bash
# Populate queue with all available neuron types
quickpage fill-queue --all

# Add specific neuron type to queue
quickpage fill-queue --neuron-type Dm4

# Process next item in queue
quickpage pop

# View queue status
quickpage queue --action status
```

#### Benefits
- **Batch Processing**: Process large numbers of neuron types efficiently
- **Resume Capability**: Stop and resume processing at any time
- **Progress Tracking**: Monitor completion status
- **Search Integration**: Queue data powers the search functionality

---

This user guide provides comprehensive coverage of QuickPage functionality. For technical implementation details, architecture information, and development workflows, see the [Developer Guide](developer-guide.md).