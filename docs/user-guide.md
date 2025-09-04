# QuickPage User Guide

A modern Python CLI tool that generates interactive HTML pages for neuron types using data from NeuPrint. This guide will help you get started quickly and make the most of QuickPage's features.

## Quick Start

1. **Install QuickPage**:
   ```bash
   pip install quickpage
   ```

2. **Configure your connection**:
   ```bash
   export NEUPRINT_APPLICATION_CREDENTIALS="your-token-here"
   ```

3. **Generate your first page**:
   ```bash
   quickpage generate -n Dm4
   ```

4. **View the results**: Open `output/index.html` in your browser

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Basic Usage](#basic-usage)
- [Advanced Features](#advanced-features)
- [Generated Website Features](#generated-website-features)
- [Troubleshooting](#troubleshooting)
- [Reference](#reference)

## Installation

### Prerequisites

- **Python 3.8+**
- **pip** package manager
- **NeuPrint access token** (get from [neuprint.janelia.org](https://neuprint.janelia.org))

### Installation Steps

```bash
# Install from PyPI
pip install quickpage

# Or install from source
git clone https://github.com/your-org/quickpage.git
cd quickpage
pip install -e .

# Verify installation
quickpage --version
```

### Setting Up Authentication

**Option 1: Environment Variable (Recommended)**
```bash
export NEUPRINT_APPLICATION_CREDENTIALS="your-token-here"
```

**Option 2: Configuration File**
```yaml
# config.yaml
neuprint:
  token: "your-token-here"
  server: "neuprint.janelia.org"
  dataset: "hemibrain:v1.2.1"
```

## Configuration

### Basic Configuration

Create a `config.yaml` file for your project:

```yaml
# Basic settings
neuprint:
  server: "neuprint.janelia.org"
  dataset: "hemibrain:v1.2.1"
  token: "your-token-here"  # Optional if using env var

output:
  directory: "output"
  template_dir: "templates"
  include_3d_view: true
  generate_json: true

html:
  title_prefix: "Neuron Catalog"
  css_framework: "plume"
  include_images: true
  include_connectivity: true
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

### Custom Neuron Types

Define custom neuron type settings:

```yaml
neuron_types:
  - name: "LC10"
    description: "Lobula Columnar neuron"
    query_type: "custom"
    soma_side: "R"

custom_neuron_types:
  LC10:
    soma_side: "R"
  Dm4:
    custom_field: "value"
```

## Basic Usage

### Essential Commands

**Test your connection**:
```bash
quickpage test-connection
```

**Generate a single neuron type page**:
```bash
quickpage generate -n Dm4
```

**Generate pages for specific hemisphere**:
```bash
quickpage generate -n Dm4 --soma-side L
```

**Generate multiple types**:
```bash
quickpage generate -n Dm4 -n Tm1 -n LC10
```

**Create the main index page**:
```bash
quickpage create-list
```

**Generate everything**:
```bash
quickpage generate-all
```

### Command Options

| Option | Description | Example |
|--------|-------------|---------|
| `-n, --neuron-type` | Specify neuron type | `-n Dm4` |
| `--soma-side` | Filter by hemisphere | `--soma-side L` |
| `-c, --config` | Use custom config | `-c config.yaml` |
| `--verbose` | Enable detailed output | `--verbose` |
| `--force` | Skip cache, regenerate | `--force` |

### Cache Management

QuickPage uses intelligent caching to improve performance:

```bash
# View cache statistics
quickpage cache --action stats

# Clean expired entries
quickpage cache --action clean

# Clear all cache
quickpage cache --action clear
```

## Advanced Features

### Batch Processing with Queue System

Process multiple neuron types efficiently:

```bash
# Add types to queue
quickpage queue --action add-type --neuron-type Dm4
quickpage queue --action add-type --neuron-type Tm1

# Process entire queue
quickpage queue --action process

# View queue status
quickpage queue --action status

# Clear queue
quickpage queue --action clear
```

### Hemisphere Analysis

Generate hemisphere-specific analyses:

```bash
# Left hemisphere only
quickpage generate -n Dm4 --soma-side L

# Right hemisphere only
quickpage generate -n Dm4 --soma-side R

# Compare hemispheres
quickpage generate -n Dm4 --soma-side L
quickpage generate -n Dm4 --soma-side R
```

### Custom Templates

Use custom HTML templates:

```bash
# Specify template directory
quickpage -c config.yaml generate -n Dm4

# config.yaml:
# output:
#   template_dir: "my-templates"
```

### Verbose Mode and Debugging

Get detailed information about processing:

```bash
# Enable verbose output
quickpage --verbose generate -n Dm4

# Enable debug mode
export QUICKPAGE_DEBUG=1
quickpage generate -n Dm4
```

## Generated Website Features

### Interactive Index Page

The main `index.html` provides:

- **Real-time search** with autocomplete
- **Advanced filtering** by cell count, neurotransmitter, brain region
- **Interactive cell count tags** - click to filter by count ranges
- **Hemisphere filtering** - view left, right, or all neurons
- **Responsive design** for mobile and desktop

### Individual Neuron Type Pages

Each neuron type page includes:

**Summary Statistics**:
- Cell counts by hemisphere
- Neurotransmitter predictions
- Brain region innervation

**3D Visualization**:
- Direct links to Neuroglancer
- Interactive 3D neuron models
- Layer-by-layer analysis

**Connectivity Analysis**:
- Input/output connection tables
- Connection strength metrics
- Partner neuron links

**Spatial Coverage**:
- Hexagonal grid visualizations
- Brain region distribution maps
- Hemisphere comparison views

### Interactive Features

**Data Tables**:
- Sortable columns
- Searchable content
- Pagination controls
- Exportable data

**Filtering Controls**:
- Connection strength sliders
- Brain region selections
- Hemisphere toggles
- Cell count ranges

**Navigation**:
- Breadcrumb navigation
- Quick neuron type switcher
- Cross-referenced links
- Mobile-friendly menus

### Understanding the Data

**Neuron Counts**: Based on reconstructed neurons in the dataset
**Connectivity**: Verified synaptic connections from electron microscopy
**Hemisphere Classifications**: Anatomical position based on soma location
**ROI Data**: Regions of Interest with innervation statistics
**Neurotransmitter Predictions**: Computational predictions requiring validation

## Troubleshooting

### Common Issues

**Authentication Problems**
```bash
# Verify token
quickpage test-connection

# Check environment
echo $NEUPRINT_APPLICATION_CREDENTIALS
```

**Connection Issues**
```bash
# Test connection
quickpage test-connection

# Check configuration
quickpage --verbose test-connection
```

**Performance Issues**
```bash
# Check cache status
quickpage cache --action stats

# Clear corrupted cache
quickpage cache --action clear
```

**Missing Output**
```bash
# Verify generation
ls -la output/

# Regenerate with verbose output
quickpage --verbose generate -n YourNeuronType
```

### Debug Mode

Enable detailed troubleshooting:

```bash
export QUICKPAGE_DEBUG=1
quickpage --verbose generate -n Dm4
```

### Getting Help

1. **Check built-in help**: `quickpage --help`
2. **Test connection**: `quickpage test-connection`
3. **Review configuration**: Verify your `config.yaml`
4. **Check cache**: `quickpage cache --action stats`
5. **Use verbose mode**: Add `--verbose` to any command

## Reference

### File Organization

```
output/
├── index.html              # Main navigation and search
├── types.html              # Filterable neuron types list
├── help.html               # Built-in documentation
├── types/                  # Individual neuron pages
│   ├── Dm4.html           # Combined hemispheres
│   ├── Dm4_L.html         # Left hemisphere
│   └── Dm4_R.html         # Right hemisphere
├── eyemaps/                # Spatial visualization images
├── static/                 # CSS, JavaScript, and assets
│   ├── css/
│   ├── js/
│   └── images/
└── .cache/                 # Performance cache (hidden)
```

### Configuration Reference

```yaml
neuprint:
  server: "neuprint.janelia.org"      # NeuPrint server URL
  dataset: "hemibrain:v1.2.1"         # Dataset identifier
  token: "your-token"                 # Access token

output:
  directory: "output"                 # Output directory
  template_dir: "templates"           # Custom templates
  include_3d_view: true              # Enable 3D links
  generate_json: true                # Export JSON data

html:
  title_prefix: "Neuron Catalog"     # Page title prefix
  css_framework: "plume"             # CSS framework
  include_images: true               # Include eyemap images
  include_connectivity: true         # Include connection data

neuron_types:                        # Predefined neuron types
  - name: "Dm4"
    description: "Dorsal medulla neuron"
    query_type: "standard"
```

### Command Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `generate` | Create neuron type pages | `quickpage generate -n Dm4` |
| `create-list` | Generate index page | `quickpage create-list` |
| `generate-all` | Process all known types | `quickpage generate-all` |
| `test-connection` | Verify NeuPrint access | `quickpage test-connection` |
| `cache` | Manage cache system | `quickpage cache --action stats` |
| `queue` | Batch processing | `quickpage queue --action status` |

### Data Citation

When using QuickPage-generated data, include:

1. **Original neuPrint database** and dataset version
2. **QuickPage version** used for generation
3. **Generation date** of the catalog
4. **Specific filtering** or configuration applied

**Example Citation**:
```
Data generated using QuickPage v1.0 from neuPrint database 
(neuprint.janelia.org), dataset: hemibrain v1.2.1, 
catalog generated: 2024-01-15.
```

### Browser Compatibility

**Recommended browsers**: Chrome, Firefox, Safari, Edge (latest versions)
**Required features**: JavaScript enabled, SVG support
**Mobile support**: Responsive design works on tablets and phones

### Performance Tips

1. **Use caching**: Cache provides up to 97.9% speed improvement
2. **Process in batches**: Use queue system for multiple types
3. **Clean cache periodically**: Remove expired entries
4. **Monitor progress**: Use verbose mode for long operations