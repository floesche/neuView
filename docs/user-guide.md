# QuickPage User Guide

A comprehensive guide for users of QuickPage, a modern Python CLI tool that generates interactive HTML pages for neuron types using data from NeuPrint. This guide covers installation, configuration, usage, and troubleshooting for all supported datasets.

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Basic Usage](#basic-usage)
- [Advanced Features](#advanced-features)
- [Generated Website Features](#generated-website-features)
- [Dataset-Specific Features](#dataset-specific-features)
- [Understanding the Interface](#understanding-the-interface)
- [Troubleshooting](#troubleshooting)
- [Reference](#reference)

## Quick Start

Get up and running with QuickPage in minutes:

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
   pixi run setup-env
   # Edit .env and add your NeuPrint token
   export NEUPRINT_APPLICATION_CREDENTIALS="your-token-here"
   ```

3. **Generate your first page**:
   ```bash
   pixi run quickpage generate -n Dm4
   ```

4. **View the results**: 
   Open `output/index.html` in your browser to see your interactive neuron catalog

## Installation

### Prerequisites

- **pixi** package manager ([installation guide](https://pixi.sh/latest/))
- **Git** for cloning the repository
- **NeuPrint access token** (get from [neuprint.janelia.org](https://neuprint.janelia.org))

### Installation Steps

```bash
# Clone the repository
git clone <repository-url>
cd quickpage

# Install dependencies using pixi
pixi install

# Verify installation
pixi run quickpage --version

# Verify installation
pixi run quickpage --help
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

**Getting Your Token**:
1. Visit [neuprint.janelia.org](https://neuprint.janelia.org)
2. Log in with your Google account
3. Click on your profile icon → "Account"
4. Copy your "Auth Token"

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
  generate_json: true

html:
  title_prefix: "Neuron Catalog"
  include_connectivity: true
```

### Dataset-Specific Configurations

QuickPage includes pre-configured settings for different datasets:

- `config/config.cns.yaml` - Central Nervous System dataset
- `config/config.optic-lobe.yaml` - Optic Lobe dataset
- `config/config.fafb.yaml` - FAFB (FlyWire) dataset
- `config/config.example.yaml` - Template configuration

Use a specific configuration:
```bash
pixi run quickpage -c config/config.optic-lobe.yaml generate -n Tm1
```

### Dataset Aliases

QuickPage supports dataset aliases to handle different naming conventions for the same underlying dataset. This allows you to use alternative dataset names in your configuration without any warnings.

#### Supported Aliases

**CNS Dataset Aliases:**
- `male-cns` → Uses CNS adapter
- `male-cns:v0.9` → Uses CNS adapter  
- `male-cns:v1.0` → Uses CNS adapter

#### Usage Example

```yaml
# config.yaml
neuprint:
  server: "neuprint-cns.janelia.org"
  dataset: "male-cns:v0.9"  # Will automatically use CNS adapter
  token: "your-token-here"
```

This configuration will work seamlessly without any warnings. The system automatically:
- Recognizes `male-cns:v0.9` as a CNS dataset
- Uses the appropriate CNS adapter
- Handles all CNS-specific database queries correctly

#### Adding New Aliases

If you need support for additional dataset aliases, please refer to the Developer Guide for implementation details.

### Custom Neuron Types

Define custom neuron type settings:

```yaml
neuron_types:
  - name: "LC10"
    description: "Lobula Columnar neuron"
    query_type: "custom"

custom_neuron_types:
  LC10:
    custom_field: "value"
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

**Generate all available pages for a neuron type**:
```bash
pixi run quickpage generate -n Dm4
```

**Generate multiple types (auto-discovery)**:
```bash
pixi run quickpage generate -n Dm4 -n Tm1 -n LC10
```

**Inspect a neuron type**:
```bash
pixi run quickpage create-list
```

**Create the main index page**:
```bash
pixi run quickpage generate-all
```

### Command Options

| Option | Description | Example |
|--------|-------------|---------|
| `-n, --neuron-type` | Specify neuron type | `-n Dm4` |
| `--image-format` | Image format for grids | `--image-format svg` |
| `--embed/--no-embed` | Embed images in HTML | `--embed` |
| `--minify/--no-minify` | HTML minification | `--no-minify` |
| `-c, --config` | Use custom config | `-c config.yaml` |
| `--verbose` | Enable detailed output | `--verbose` |

### Neuron Type Inspection

Get detailed information about specific neuron types:

```bash
# View cache statistics
pixi run quickpage cache --action stats

# Clean expired entries
pixi run quickpage cache --action clean

# Clear all cache
pixi run quickpage cache --action clear
```

## Advanced Features

### Batch Processing with Queue System

Process multiple neuron types efficiently using the queue system:

```bash
# Add types to queue
pixi run quickpage queue --action add-type --neuron-type Dm4
pixi run quickpage queue --action add-type --neuron-type Tm1

# Process entire queue
pixi run quickpage queue --action process

# View queue status
pixi run quickpage queue --action status

# Clear queue
pixi run quickpage queue --action clear
```

### Automatic Page Generation

QuickPage automatically detects available soma sides and generates all appropriate pages:

```bash
# Generates all available pages based on data distribution
pixi run quickpage generate -n Dm4

# For neuron types with data on multiple sides, this creates:
# - Dm4_L.html (left hemisphere neurons)
# - Dm4_R.html (right hemisphere neurons) 
# - Dm4.html (combined view)

# For neuron types with data on only one side:
# - Only creates the side-specific page (e.g., Dm4_L.html)
# - No combined page is generated
```

**Automatic Detection Logic**:
- **Multiple hemispheres**: Creates individual side pages + combined page
- **Single hemisphere**: Creates only the relevant side page
- **Mixed data**: Handles unknown/unassigned soma sides intelligently
- **No user intervention required**: System analyzes data and creates optimal page set

### Custom Templates

Use custom HTML templates:

```bash
# Specify template directory
pixi run quickpage -c config.yaml generate -n Dm4

# config.yaml:
# output:
#   template_dir: "my-templates"
```

### Citation Management

QuickPage automatically tracks missing citations and logs them for easy maintenance:

**Monitoring Missing Citations**

```bash
# Check for missing citations after page generation
cat output/.log/missing_citations.log

# Follow citation log in real-time
tail -f output/.log/missing_citations.log

# Count unique missing citations
grep "Missing citation" output/.log/missing_citations.log | cut -d"'" -f2 | sort | uniq -c
```

**Adding Missing Citations**

When citations are missing, add them to `input/citations.csv`:

```csv
Smith2023,10.1234/example,Smith et al. 2023 - Example Paper
Jones2024,https://doi.org/10.5678/jones,Jones et al. 2024 - Another Study
Brown2025,10.9012/brown,Brown et al. 2025 - Research Title
```

**Citation Log Features**

- **Automatic Tracking**: Missing citations are logged during page generation
- **Context Information**: Logs show which neuron type and operation encountered the missing citation
- **Rotating Logs**: Files automatically rotate when they reach 1MB (keeps 5 backups)
- **Timestamped Entries**: Each entry includes when the missing citation was encountered

**Example Log Entries**:
```
2025-09-29 17:30:06 - WARNING - Missing citation 'Smith2023' in synonym processing for SAD103
2025-09-29 17:30:06 - WARNING - Missing citation 'Jones2024' in synonym processing for Tm3
```

### Verbose Mode and Debugging

Get detailed information about processing:

```bash
# Enable verbose output
pixi run quickpage --verbose generate -n Dm4

# Enable debug mode
export QUICKPAGE_DEBUG=1
pixi run quickpage generate -n Dm4
```

## Generated Website Features

### Interactive Index Page

The main `index.html` provides:

- **Real-time search** with autocomplete for neuron types
- **Advanced filtering** by cell count, neurotransmitter, brain region
- **Interactive cell count tags** - click to filter by count ranges
- **Automatic hemisphere detection** - generates appropriate pages for available data
- **Responsive design** for mobile and desktop
- **Export functionality** for filtered results

### Individual Neuron Type Pages

Each neuron type page includes comprehensive information:

**Summary Statistics**:
- Cell counts by hemisphere (L, R, combined)
- Neurotransmitter predictions with confidence scores
- Brain region innervation summary
- Morphological classifications

**3D Visualization**:
- Direct links to Neuroglancer with pre-loaded neuron data
- Interactive 3D neuron models
- Layer-by-layer anatomical analysis
- Coordinate system integration

**Connectivity Analysis**:
- Input/output connection tables with partner details
- Connection strength metrics and statistics
- Partner neuron links for cross-referencing
- Hemisphere-specific connectivity patterns

**Spatial Coverage**:
- Hexagonal grid visualizations showing neuron distribution
- Brain region distribution maps
- Hemisphere comparison views
- ROI (Region of Interest) innervation analysis

### Interactive Features

**Data Tables**:
- Sortable columns for all data types
- Searchable content with real-time filtering
- Pagination controls for large datasets
- Exportable data in multiple formats

**Filtering Controls**:
- Connection strength sliders for fine-tuning
- Brain region selections with hierarchical organization
- Hemisphere toggles (L/R/Combined)
- Cell count range selectors

**Navigation**:
- Breadcrumb navigation for easy orientation
- Quick neuron type switcher in header
- Cross-referenced links between related neurons
- Mobile-friendly hamburger menus

## Dataset-Specific Features

### FAFB (FlyWire) Dataset

**Special Features**:
- Adapted for FlyWire-specific data structures
- Handles different soma side nomenclature (CENTER vs MIDDLE)
- Optimized queries for FAFB database schema

**Important Notes**:
- **ROI Checkboxes**: Not available for FAFB datasets due to neuroglancer limitations
- **Soma Sides**: Uses "C" for center instead of "M" for middle
- **Template Selection**: Automatically uses FAFB-specific neuroglancer templates

**Why No ROI Checkboxes?**
FAFB neuroglancer data lacks reliable ROI visualization support. The system automatically detects FAFB datasets and removes ROI checkboxes to prevent user confusion. ROI statistics are still displayed for reference.

### CNS, Hemibrain, and Optic-Lobe Datasets

**Full Feature Set**:
- Complete ROI checkbox functionality for 3D visualization
- Standard soma side classifications (L, R, M)
- Full neuroglancer integration with mesh overlays
- Complete connectivity visualization

### Dataset Detection

The system automatically detects dataset type and adapts functionality:

- **FAFB Detection**: Dataset name contains "fafb" (case-insensitive)
- **Other Datasets**: Assume full ROI visualization capability
- **Automatic Adaptation**: No user configuration required

## Understanding the Interface

### ROI (Region of Interest) Features

**For CNS, Hemibrain, and Optic-Lobe Datasets**:

```
ROI Innervation (15 ROIs)
┌───┬─────────────────┬──────────┬─────────┬─────────┐
│ ☑ │ ROI Name        │ ∑ In     │ % In    │ % Out   │
├───┼─────────────────┼──────────┼─────────┼─────────┤
│ ☐ │ AL(R)           │ 1,234    │ 15.2%   │ 8.7%    │
│ ☑ │ AVLP(R)         │ 2,567    │ 31.1%   │ 22.4%   │
│ ☐ │ ...             │ ...      │ ...     │ ...     │
└───┴─────────────────┴──────────┴─────────┴─────────┘
```

**Interactive Behavior**:
1. **Click to Toggle**: Click any ROI checkbox to show/hide that region in neuroglancer
2. **Visual Feedback**: Checked boxes (☑) show active ROIs, unchecked (☐) show inactive
3. **Real-time Updates**: Neuroglancer viewer updates immediately when checkboxes change
4. **Multi-selection**: Multiple ROIs can be selected simultaneously
5. **Persistent State**: ROI selections maintained during navigation

**For FAFB Dataset**:

```
ROI Innervation (15 ROIs)
┌─────────────────┬──────────┬─────────┬─────────┐
│ ROI Name        │ ∑ In     │ % In    │ % Out   │
├─────────────────┼──────────┼─────────┼─────────┤
│ GNG             │ 1,234    │ 15.2%   │ 8.7%    │
│ SEZ             │ 2,567    │ 31.1%   │ 22.4%   │
│ ...             │ ...      │ ...     │ ...     │
└─────────────────┴──────────┴─────────┴─────────┘
```

**View-Only Mode**:
1. **Statistical Reference**: ROI table provides innervation data for analysis
2. **No Interactive Elements**: Checkboxes not displayed to avoid confusion
3. **Clean Interface**: Maintains professional appearance without false promises
4. **Data Accuracy**: All ROI statistics remain accurate and useful

### Connectivity Tables

**Table Columns**:
- **Partner**: Neuron type that connects to/from the main neuron type
- **#**: Number of partner neurons of this type
- **NT**: Neurotransmitter (ACh, Glu, GABA, etc.)
- **Conns**: Average connections per neuron of the main type
- **CV**: Coefficient of variation for connections per neuron (measures variability)
- **%**: Percentage of total input/output connections

**Coefficient of Variation (CV)**:
- Measures how variable the connection strengths are across partner neurons
- Formula: CV = standard deviation / mean of connections per neuron
- Provides normalized measure comparable across different connection scales
- **Interpretation Guide**:
  - **CV = 0.0**: No variation (single partner neuron)
  - **Low CV (0.0-0.3)**: Consistent connection strengths across partners
  - **Medium CV (0.3-0.7)**: Moderate variation in connection strengths  
  - **High CV (0.7+)**: High variation, some partners much stronger than others

**CV Usage Examples**:
- CV = 0.25 for L1 partners: Most L1 neurons have similar connection counts
- CV = 0.75 for Tm9 partners: Few strong Tm9 connections, many weak ones
- CV = 0.0 for Mi1 partners: Only one Mi1 neuron connects (no variation)

**Combined Pages (e.g., Dm4.html)**:
- Shows merged entries: "L1 - 545 connections" (combining L1(L) + L1(R))
- CV values are weighted averages: CV = Σ(cv_i × count_i) / Σ(count_i)
- Example: L1(L) CV=0.25 (20 neurons) + L1(R) CV=0.30 (8 neurons) → L1 CV=0.268
- Cleaner visualization with reduced redundancy
- Neuroglancer links include neurons from both hemispheres

**Individual Hemisphere Pages (e.g., Dm4_L.html)**:
- Automatically generated when hemisphere-specific data exists
- Shows hemisphere-specific data exactly as stored in database
- No combination or modification of original data
- Direct neuroglancer links to hemisphere-specific neurons

**CV Applications and Benefits**:

*Research Applications*:
- **Connection Pattern Analysis**: Identify partner types with consistent vs variable connectivity
- **Circuit Reliability**: Low CV indicates reliable circuit components, high CV suggests specialization
- **Developmental Studies**: Compare CV across developmental stages to study connection refinement
- **Comparative Analysis**: Use CV to compare connection reliability across different neuron types

*Data Quality Assessment*:
- **Reconstruction Quality**: Unusually high CV may indicate incomplete reconstructions
- **Biological vs Technical Variation**: Distinguish natural biological variation from technical artifacts
- **Partner Classification**: CV helps validate partner type classifications and groupings

*Practical Usage*:
- **Circuit Modeling**: Use CV to inform computational models of circuit variability
- **Experimental Design**: Target high-CV partners for detailed experimental validation
- **Literature Comparison**: Compare CV values with published electrophysiology data

### Tooltip System

Rich HTML tooltips provide additional context throughout the interface:

**Basic Tooltips**:
- Hover over "?" icons for detailed explanations
- Rich HTML content with formatted text and lists
- Automatic positioning to stay within viewport

**Usage Examples**:
- Neuroglancer explanations and usage tips
- Data field definitions and calculations
- Feature descriptions and limitations

**Mobile Support**:
- Touch-friendly sizing and positioning
- Simplified layouts for small screens
- Responsive text sizing

### Understanding the Data

**Neuron Counts**: 
- Based on reconstructed neurons in the dataset
- May vary between hemispheres due to reconstruction completeness
- Combined counts represent total across both hemispheres

**Connectivity**: 
- Verified synaptic connections from electron microscopy
- Connection weights represent synapse counts
- Partner percentages calculated relative to total connections

**Hemisphere Classifications**: 
- Based on anatomical position of cell body (soma)
- L = Left hemisphere, R = Right hemisphere
- C/M = Center/Middle (combined or midline neurons)

**ROI Data**: 
- Regions of Interest with innervation statistics
- Pre/Post counts indicate input/output synapses
- Percentages show relative innervation strength

**Neurotransmitter Predictions**: 
- Computational predictions requiring experimental validation
- Confidence scores indicate prediction reliability
- Multiple predictions possible for single neuron type

## Troubleshooting

### Citation Issues

**Missing Citations in Pages**

If you notice citations are missing or showing as broken links:

1. Check the citation log file:
   ```bash
   cat output/.log/missing_citations.log
   ```

2. Add missing citations to `input/citations.csv`:
   ```csv
   Smith2023,10.1234/example,Smith et al. 2023 - Example Paper
   Jones2024,https://doi.org/10.5678/jones,Jones et al. 2024
   ```

3. Regenerate affected pages:
   ```bash
   pixi run quickpage generate -n YourNeuronType
   ```

**Citation Log File Not Created**

If `output/.log/missing_citations.log` doesn't exist:
- Ensure the output directory is writable
- Check that pages are being generated (citations are only logged during generation)
- Verify that there are actually missing citations to log

**Large Citation Log Files**

Citation logs automatically rotate when they reach 1MB:
- Up to 5 backup files are kept (`.log.1`, `.log.2`, etc.)
- Check for repeated missing citations that should be added to `citations.csv`
- Old backup files can be safely deleted if disk space is needed

### Common Issues

**Authentication Problems**
```bash
# Verify token is set
echo $NEUPRINT_APPLICATION_CREDENTIALS

# Test connection
pixi run quickpage test-connection

# Check configuration
pixi run quickpage --verbose test-connection
```

**Connection Issues**
```bash
# Test with verbose output
pixi run quickpage --verbose test-connection

# Try different server
# Edit config.yaml neuprint.server setting

# Check network connectivity
ping neuprint.janelia.org
```

**Performance Issues**
```bash
# Check cache status
pixi run quickpage cache --action stats

# Clear corrupted cache
pixi run quickpage cache --action clear

# Enable performance monitoring
export QUICKPAGE_PROFILE=1
```

**Missing Output**
```bash
# Verify generation completed
ls -la output/

# Regenerate with verbose output
pixi run quickpage --verbose generate -n YourNeuronType

# Check for errors
pixi run quickpage --verbose create-list
```

**ROI Checkboxes Not Working**

For CNS/Hemibrain/Optic-Lobe datasets:
1. Check browser JavaScript console for errors
2. Verify neuroglancer viewer loads properly
3. Ensure checkbox elements are present in HTML
4. Try refreshing the page

For FAFB datasets:
- This is expected behavior - FAFB doesn't support ROI checkboxes
- ROI data is still accurate for analysis purposes
- Use other navigation methods in neuroglancer

### Debug Mode

Enable detailed troubleshooting:

```bash
export QUICKPAGE_DEBUG=1
export QUICKPAGE_PROFILE=1
pixi run quickpage --verbose generate -n Dm4
```

This provides:
- Detailed operation logging
- Performance timing information
- Database query details
- Cache operation tracking
- Memory usage statistics

### Getting Help

1. **Check built-in help**: `pixi run quickpage --help`
2. **Test connection**: `pixi run quickpage test-connection`
3. **Review configuration**: Verify your `config.yaml`
4. **Check cache**: `pixi run quickpage cache --action stats`
5. **Use verbose mode**: Add `--verbose` to any command
6. **Check logs**: Look for error messages in console output

### Browser Compatibility

**Recommended Browsers**: 
- Chrome 90+ (recommended for best performance)
- Firefox 88+
- Safari 14+
- Edge 90+

**Required Features**: 
- JavaScript enabled
- SVG support for visualizations
- CSS3 support for responsive design

**Mobile Support**: 
- Responsive design works on tablets and phones
- Touch-friendly interface elements
- Optimized for smaller screens

## Reference

### File Organization

```
output/
├── index.html              # Main navigation and search
├── types.html              # Filterable neuron types list
├── help.html               # Built-in documentation
├── types/                  # Individual neuron pages (auto-generated)
│   ├── Dm4.html           # Combined view (if multiple hemispheres)
│   ├── Dm4_L.html         # Left hemisphere (if data exists)
│   ├── Dm4_R.html         # Right hemisphere (if data exists)
│   └── Dm4_C.html         # Center/midline (if data exists)
├── eyemaps/                # Spatial visualization images
│   ├── Dm4_ME_R.png       # Region-specific eyemaps
│   └── Dm4_LO_L.png
├── static/                 # CSS, JavaScript, and assets
│   ├── css/
│   │   └── neuron-page.css
│   ├── js/
│   │   ├── neuron-page.js
│   │   └── neuroglancer-*.js
│   └── images/
├── .log/                   # System logs (hidden)
│   ├── missing_citations.log    # Missing citation tracking
│   ├── missing_citations.log.1  # Log rotation backups
│   └── missing_citations.log.2
└── .cache/                 # Performance cache (hidden)
    ├── database/          # Database query cache
    ├── templates/         # Compiled template cache
    └── resources/         # Static resource cache
```

### Configuration Reference

```yaml
# Complete configuration example
neuprint:
  server: "neuprint.janelia.org"      # NeuPrint server URL
  dataset: "hemibrain:v1.2.1"         # Dataset identifier
  token: "your-token"                 # Access token (optional if using env var)

output:
  directory: "output"                 # Output directory
  template_dir: "templates"           # Custom templates directory
  generate_json: true                # Export JSON data alongside HTML

html:
  title_prefix: "Neuron Catalog"     # Page title prefix
  include_connectivity: true         # Include connection data

cache:
  enabled: true                      # Enable caching system
  ttl: 3600                         # Time-to-live in seconds
  max_memory_mb: 512                # Maximum memory cache size
  directory: ".cache"               # Cache directory

visualization:
  hex_size: 20                      # Hexagon size for grid visualizations
  spacing_factor: 1.1               # Spacing between hexagons
  default_colors:                   # Default color scheme
    - "#1f77b4"
    - "#ff7f0e"
    - "#2ca02c"

neuron_types:                        # Predefined neuron types
  - name: "Dm4"
    description: "Dorsal medulla neuron"
    query_type: "standard"
  - name: "LC10"
    description: "Lobula columnar neuron"
    query_type: "custom"
    custom_query: "MATCH (n:Neuron) WHERE n.type = 'LC10' RETURN n"
```

### Command Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `generate` | Create neuron type pages | `pixi run quickpage generate -n Dm4` |
| `create-list` | Generate index page | `pixi run quickpage create-list` |
| `generate-all` | Process all known types | `pixi run quickpage generate-all` |
| `test-connection` | Verify NeuPrint access | `pixi run quickpage test-connection` |
| `cache` | Manage cache system | `pixi run quickpage cache --action stats` |
| `queue` | Batch processing | `pixi run quickpage queue --action status` |

### Performance Tips

1. **Use Caching**: Cache provides up to 97.9% speed improvement on subsequent runs
2. **Process in Batches**: Use queue system for multiple neuron types
3. **Clean Cache Periodically**: Remove expired entries with `cache --action clean`
4. **Monitor Progress**: Use verbose mode for long-running operations
5. **Optimize Configuration**: Adjust cache settings based on available memory

### Data Citation

When using QuickPage-generated data in publications:

**Required Citations**:
1. **Original neuPrint database** and dataset version
2. **QuickPage version** used for generation  
3. **Generation date** of the catalog
4. **Specific filtering** or configuration applied

**Example Citation**:
```
Neuron data analysis generated using QuickPage v2.0 from neuPrint database 
(neuprint.janelia.org), dataset: hemibrain v1.2.1, catalog generated: 2024-01-15.
Connectivity data from Scheffer et al. (2020). ROI analysis performed using 
standard QuickPage configuration with automatic hemisphere detection.
```

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `NEUPRINT_APPLICATION_CREDENTIALS` | NeuPrint API token | `your-token-string` |
| `QUICKPAGE_CONFIG_PATH` | Custom config file path | `/path/to/config.yaml` |
| `QUICKPAGE_CACHE_DIR` | Cache directory override | `/tmp/quickpage_cache` |
| `QUICKPAGE_DEBUG` | Enable debug logging | `1` or `true` |
| `QUICKPAGE_PROFILE` | Enable performance profiling | `1` or `true` |

### Keyboard Shortcuts

When viewing generated pages:

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + F` | Search within page |
| `Ctrl/Cmd + Shift + F` | Search across all tables |
| `Escape` | Clear search filters |
| `Tab` | Navigate between interactive elements |
| `Enter` | Activate focused element |

### Dataset-Specific Notes

**Hemibrain Dataset**:
- Most complete connectivity data
- Full ROI visualization support
- Standard soma side classifications
- Comprehensive neurotransmitter predictions

**CNS Dataset**:
- Focus on central nervous system
- Complete feature support
- Standard data format
- Good performance characteristics

**Optic-Lobe Dataset**:
- Specialized for visual system neurons
- Full neuroglancer integration
- Rich connectivity analysis
- Optimized eyemap visualizations

**FAFB (FlyWire) Dataset**:
- Largest dataset with ongoing updates
- Limited ROI visualization (by design)
- Special soma side handling (CENTER vs MIDDLE)
- Automated template selection

### Frequently Asked Questions

**Q: Why don't I see ROI checkboxes for my FAFB dataset?**
A: This is intentional. FAFB neuroglancer data doesn't support reliable ROI visualization, so checkboxes are hidden to prevent confusion. ROI statistics are still accurate and displayed.

**Q: How do I generate pages for all neuron types?**
A: Use `pixi run quickpage generate-all` to process all known neuron types, or use the queue system for more control.

**Q: Can I customize the HTML output?**
A: Yes, you can provide custom templates by setting `template_dir` in your configuration and creating modified versions of the template files.

**Q: How do I improve generation speed?**
A: Enable caching (default), use batch processing with queues, and ensure adequate memory allocation. Cache provides significant performance improvements.

**Q: What browsers are supported?**
A: Modern browsers (Chrome, Firefox, Safari, Edge) with JavaScript enabled. Chrome is recommended for optimal performance.

**Q: How do I export data from the generated pages?**
A: Use the export functions in data tables, or enable JSON export in configuration to generate machine-readable data alongside HTML.

**Q: How does automatic page generation work?**
A: QuickPage analyzes your neuron data and automatically creates the appropriate pages:
- For neuron types with multiple hemispheres (L/R/M): Creates individual hemisphere pages AND a combined page
- For neuron types with only one hemisphere: Creates only that hemisphere's page (no combined page)
- No manual soma-side specification needed - the system detects and generates optimal page sets automatically

**Q: Can I still generate hemisphere-specific pages?**
A: Yes, but it's now automatic! QuickPage will generate hemisphere-specific pages (e.g., Dm4_L.html, Dm4_R.html) whenever hemisphere-specific data exists. You don't need to specify --soma-side anymore.

---

This user guide provides comprehensive coverage of QuickPage's features and functionality. For technical implementation details, see the [Developer Guide](developer-guide.md).
