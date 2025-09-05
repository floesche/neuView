# QuickPage User Guide

A modern Python CLI tool that generates interactive HTML pages for neuron types using data from NeuPrint. This guide will help you get started quickly and make the most of QuickPage's features.

## Quick Start

1. **Install QuickPage**:
   ```bash
   # Clone the repository
   git clone https://github.com/floesche/quickpage.git
   cd quickpage
   
   # Install with pixi
   pixi install
   ```

2. **Configure your connection**:
   ```bash
   export NEUPRINT_APPLICATION_CREDENTIALS="your-token-here"
   ```

3. **Generate your first page**:
   ```bash
   pixi run quickpage generate -n Dm4
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

- **pixi** package manager ([installation guide](https://pixi.sh/latest/))
- **Git** for cloning the repository
- **NeuPrint access token** (get from [neuprint.janelia.org](https://neuprint.janelia.org))

> **Note**: Python 3.11+ is automatically managed by pixi - no separate Python installation required.

### Installation Steps

```bash
# Clone the repository
git clone https://github.com/floesche/quickpage.git
cd quickpage

# Install dependencies and set up environment
pixi install

# Verify installation
pixi run quickpage --help

# Set up environment variables (optional)
pixi run setup-env
```

### Setting Up Authentication

**Option 1: Environment File (Recommended with pixi)**
```bash
# Set up environment file template
pixi run setup-env

# Edit the .env file with your token
# .env
NEUPRINT_APPLICATION_CREDENTIALS="your-token-here"
```

**Option 2: Environment Variable**
```bash
export NEUPRINT_APPLICATION_CREDENTIALS="your-token-here"
```

**Option 3: Configuration File**
```yaml
# config.yaml
neuprint:
  token: "your-token-here"
  server: "neuprint.janelia.org"
  dataset: "hemibrain:v1.2.1"
```

## Configuration

### Basic Configuration

QuickPage uses a `config.yaml` file for project settings. A default configuration is included:

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
pixi run quickpage -c config.optic-lobe.yaml generate -n Tm1
```

### Custom Neuron Types

Define custom neuron type settings:

```yaml
neuron_types:
  - name: "LC10"
    description: "Lobula Columnar neuron"
    query_type: "custom"
    soma_side: "right"

custom_neuron_types:
  LC10:
    soma_side: "right"
  Dm4:
    custom_field: "value"
```

## Basic Usage

### Essential Commands

**Test your connection**:
```bash
pixi run quickpage test-connection
```

**Generate a single neuron type page**:
```bash
pixi run quickpage generate -n Dm4
```

**Generate pages for specific hemisphere**:
```bash
pixi run quickpage generate -n Dm4 --soma-side left
```

**Generate multiple types (auto-discovery)**:
```bash
pixi run quickpage generate
```

**Inspect a neuron type**:
```bash
pixi run quickpage inspect Dm4
```

**Create the main index page**:
```bash
pixi run quickpage create-list
```

### Command Options

| Option | Description | Example |
|--------|-------------|---------|
| `-n, --neuron-type` | Specify neuron type | `-n Dm4` |
| `--soma-side` | Filter by hemisphere | `--soma-side left` |
| `--image-format` | Image format for grids | `--image-format svg` |
| `--embed/--no-embed` | Embed images in HTML | `--embed` |
| `--minify/--no-minify` | HTML minification | `--no-minify` |
| `-c, --config` | Use custom config | `-c config.yaml` |
| `--verbose` | Enable detailed output | `--verbose` |

### Neuron Type Inspection

Get detailed information about specific neuron types:

```bash
# Inspect a neuron type
pixi run quickpage inspect Dm4

# Inspect specific hemisphere
pixi run quickpage inspect Dm4 --soma-side left
```

## Advanced Features

### Batch Processing with Queue System

Process multiple neuron types efficiently using the queue system:

```bash
# Add a specific type to queue
pixi run quickpage fill-queue -n Dm4

# Add all discovered types to queue
pixi run quickpage fill-queue --all

# Process a queue file
pixi run quickpage pop
```

### Hemisphere Analysis

Generate hemisphere-specific analyses:

```bash
# Left hemisphere only
pixi run quickpage generate -n Dm4 --soma-side left

# Right hemisphere only
pixi run quickpage generate -n Dm4 --soma-side right

# Middle or combined analysis
pixi run quickpage generate -n Dm4 --soma-side middle
pixi run quickpage generate -n Dm4 --soma-side combined

# All hemispheres (default)
pixi run quickpage generate -n Dm4 --soma-side all
```

### Custom Templates

Use custom HTML templates:

```bash
# Specify template directory
pixi run quickpage -c config.yaml generate -n Dm4

# config.yaml:
# output:
#   template_dir: "my-templates"
```

### Verbose Mode and Debugging

Get detailed information about processing:

```bash
# Enable verbose output
pixi run quickpage --verbose generate -n Dm4

# Run with environment variables
QUICKPAGE_DEBUG=1 pixi run quickpage generate -n Dm4
```

### Pixi Tasks

QuickPage includes several convenient pixi tasks for common workflows:

```bash
# Set up environment file with template
pixi run setup-env

# Clean output directory
pixi run clean-output

# Generate all pages in one command
pixi run create-all-pages

# Fill queue with all neuron types
pixi run fill-all

# Process all queue files in parallel
pixi run pop-all

# Fill queue for a specific type
pixi run fill-type Dm4

# Run development help
pixi run dev
```

**Complete Workflow Example**:
```bash
# Clean start and generate everything
pixi run clean-output
pixi run fill-all
pixi run pop-all
pixi run create-list
```

## Generated Website Features

### Interactive Index Page

The main `index.html` provides:

- **Real-time search** with autocomplete
- **Advanced filtering** by cell count, neurotransmitter, brain region
- **Interactive cell count tags** - click to filter by count ranges
- **Hemisphere filtering** - view left, right, middle, combined, or all neurons
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
pixi run quickpage test-connection

# Check environment
echo $NEUPRINT_APPLICATION_CREDENTIALS
```

**Connection Issues**
```bash
# Test connection
pixi run quickpage test-connection

# Check configuration with detailed info
pixi run quickpage test-connection --detailed
```

**Performance Issues**
```bash
# Use queue system for batch processing
pixi run quickpage fill-queue --all
pixi run quickpage pop

# Process with verbose output
pixi run quickpage --verbose generate -n YourNeuronType
```

**Missing Output**
```bash
# Verify generation
ls -la output/

# Regenerate with verbose output
pixi run quickpage --verbose generate -n YourNeuronType

# Inspect neuron type details
pixi run quickpage inspect YourNeuronType
```

### Debug Mode

Enable detailed troubleshooting:

```bash
pixi run quickpage --verbose generate -n Dm4
```

### Getting Help

1. **Check built-in help**: `pixi run quickpage --help`
2. **Test connection**: `pixi run quickpage test-connection`
3. **Review configuration**: Verify your `config.yaml`
4. **Inspect neuron types**: `pixi run quickpage inspect NeuronType`
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
└── static/                 # CSS, JavaScript, and assets
    ├── css/
    ├── js/
    └── images/
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
| `generate` | Create neuron type pages | `pixi run quickpage generate -n Dm4` |
| `create-list` | Generate index page | `pixi run quickpage create-list` |
| `inspect` | Inspect neuron type details | `pixi run quickpage inspect Dm4` |
| `test-connection` | Verify NeuPrint access | `pixi run quickpage test-connection` |
| `fill-queue` | Add items to processing queue | `pixi run quickpage fill-queue -n Dm4` |
| `pop` | Process queue file | `pixi run quickpage pop` |

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
**System requirements**: Python 3.11+ (automatically managed by pixi)

### Performance Tips

1. **Process in batches**: Use queue system for multiple types
2. **Use verbose mode**: Monitor progress for long operations
3. **Optimize image format**: Choose SVG for smaller files, PNG for compatibility
4. **Use minification**: Keep HTML minification enabled for faster loading
