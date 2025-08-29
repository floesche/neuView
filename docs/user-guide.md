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
- [Generated Website Features](#generated-website-features)
- [Spatial Coverage Visualization](#spatial-coverage-visualization)
- [Data Citation and Documentation](#data-citation-and-documentation)

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
- **YouTube Integration**: Educational videos linked to relevant neuron types
- **Citation Links**: Scientific references with direct links to research papers
- **Brain Region Translation**: User-friendly full names for anatomical abbreviations
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
    soma_side: "combined"

# Additional configurations for neuron types not in the main list
custom_neuron_types:
  LC10:
    soma_side: "combined"
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
# List all types (default: 10 results)
quickpage list-types

# List all types without limit
quickpage list-types --all

# Sort results alphabetically
quickpage list-types --sorted

# Show soma side distribution
quickpage list-types --show-soma-sides

# Show neuron counts and statistics
quickpage list-types --show-statistics

# Filter by pattern (regex)
quickpage list-types --filter-pattern "LC.*"

# Combine options
quickpage list-types --all --sorted --show-statistics
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

# Inspect specific soma side
quickpage inspect Dm4 --soma-side left

# Inspect all soma sides
quickpage inspect Dm4 --soma-side all
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
pixi run clean-output       # Clean output directory
pixi run setup-env          # Create .env file from template
pixi run dev                # Show quickpage help

# Queue and batch processing
pixi run fill-all           # Fill queue with all neuron types
pixi run pop-all            # Process all items in queue
pixi run create-list        # Generate index page

# Test sets for development
pixi run test-set           # Generate test set with index
pixi run test-set-no-index  # Generate test set without index
pixi run test-set-only-weird # Generate only problematic types

# Complete pipeline
pixi run create-all-pages   # Full pipeline: clean, fill, process, index
```

### Advanced Pixi Tasks

For development and testing, additional pixi tasks are available:

```bash
# Queue management tasks
pixi run fill-type          # Fill queue for specific neuron type
                            # Usage: pixi run fill-type NEURON_TYPE

# Specialized test sets
pixi run test-set-weird-pages      # Queue problematic neuron types for testing
pixi run test-set-no-index         # Generate test pages without index
pixi run test-set-only-weird       # Test only problematic types with index

# These tasks are designed for development and debugging workflows
```

**Note**: The `fill-type` task accepts arguments. For example:
```bash
# Fill queue for a specific neuron type
pixi run fill-type Dm4

# Fill queue without arguments (processes all types)
pixi run fill-type
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

# Combined hemispheres (default)
quickpage generate -n Dm4 --soma-side combined

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
│   ├── Dm4.html           # Combined hemispheres
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
quickpage fill-queue -n Dm4

# Add with specific soma side and output directory
quickpage fill-queue -n Dm4 --soma-side left --output-dir custom_output

# Add with PNG image format instead of SVG
quickpage fill-queue -n Dm4 --image-format png

# Process next item in queue
quickpage pop

# Check queue contents by listing files in output/.queue/ directory
ls output/.queue/
```

#### Benefits
- **Batch Processing**: Process large numbers of neuron types efficiently
- **Resume Capability**: Stop and resume processing at any time
- **Progress Tracking**: Monitor completion status
- **Search Integration**: Queue data powers the search functionality

## Generated Website Features

QuickPage generates interactive websites with comprehensive neuron analysis pages. Understanding these features helps you make the most of the generated content.

### Index Page Features

The main index page serves as the entry point for exploring your dataset:

#### Filter Options
- **Neuron Type Filter**: Use the search box to filter neurons by type name. Supports partial matching and real-time filtering
- **Hemisphere Filter**: Choose between "All", "Left", "Right", or "Middle" to filter neurons by soma hemisphere location
- **Synapse Count Filters**: Use slider controls to filter neurons based on presynaptic and postsynaptic synapse counts
- **ROI Filter**: Filter by specific regions of interest (brain regions)
- **Region Filter**: Filter by broader anatomical regions that group related ROIs
- **Neurotransmitter Filter**: Filter by predicted neurotransmitter type (Acetylcholine, GABA, Glutamate, etc.)
- **Cell Count Filter**: Filter by the number of neurons in each type

#### Interactive Features
- **Sortable Tables**: Click column headers to sort data in ascending/descending order
- **Global Search**: Use the search box to quickly find specific entries across all columns
- **Pagination**: Browse through large datasets using pagination controls
- **Column Visibility**: Toggle column visibility using the column visibility button
- **Combined Filtering**: All filters work together for refined searches

### Individual Neuron Type Pages

Each neuron type links to a comprehensive analysis page with detailed information:

#### Summary Statistics
- **Neuron Count**: Total count with hemisphere distribution breakdown
- **Synapse Statistics**: Average presynaptic and postsynaptic synapse counts
- **Balance Analysis**: Log ratio calculations for hemisphere balance assessment
- **Anatomical Distribution**: Breakdown across major brain regions

#### 3D Visualization Integration
- **Neuroglancer Viewer**: Embedded 3D brain visualization showing neuron morphology
- **Interactive Navigation**: Zoom, rotate, and navigate through brain volume
- **Contextual Viewing**: View neuron reconstructions in anatomical context
- **Direct Links**: Access to external Neuroglancer for advanced analysis

#### Layer Analysis
- **Regional Breakdown**: Detailed analysis of neuron presence across brain layers (LA, ME, LO, LOP, AME, Central Brain)
- **Quantitative Analysis**: Neuron distribution within anatomical layers
- **Interactive Tables**: Layer-specific statistics with sorting and filtering
- **Coverage Analysis**: Complete coverage showing all anatomical areas

#### ROI Innervation Analysis
- **Comprehensive ROI Data**: Complete table of Region of Interest innervation with full anatomical names
- **Synapse Distribution**: Breakdown of presynaptic vs postsynaptic connections
- **Percentage Filtering**: Logarithmic slider controls for exploring connection strength
- **Cumulative Analysis**: Running totals for understanding distribution patterns
- **Search Functionality**: Quick finding of specific brain regions

#### Connectivity Analysis
- **Upstream Connections**: Detailed analysis of neurons providing input
- **Downstream Connections**: Comprehensive view of neurons receiving output
- **Connection Strength**: Quantitative synapse count data for each connection
- **Partner Identification**: Clear identification of connecting neuron types
- **Percentage Breakdown**: Relative connection strengths within neuron type
- **Interactive Filtering**: Slider controls for connection strength thresholds
- **Educational Videos**: YouTube links to visual demonstrations and explanations (when available)
- **Scientific References**: Clickable citations linking to original research papers

### Interactive Elements

#### Data Tables
- **Sorting**: Click any column header to sort data
- **Filtering**: Real-time filtering without page reloads
- **Search**: Global search across all table data
- **Responsive Design**: Tables adapt to different screen sizes
- **Export Capability**: Print-friendly formatting

#### Filtering Controls
- **Logarithmic Sliders**: Intuitive filtering of percentage and count data
- **Real-time Updates**: Immediate response to filter changes
- **Visual Feedback**: Clear indication of applied filters
- **Reset Options**: Easy removal of filters
- **Combined Logic**: Multiple filters work together

#### User Experience Features
- **Tooltip Help**: Hover tooltips provide additional information
- **Mobile Optimization**: Touch-friendly controls for tablets and smartphones
- **Bookmarkable URLs**: Save direct links to specific neuron types
- **Shareable Content**: URLs can be shared with colleagues
- **Print Support**: Browser print function works with all pages

### Understanding the Data

#### Neuron Counts
- Numbers represent individual reconstructed neurons in the dataset
- Not all neurons of a type may be reconstructed
- Counts reflect the current state of the dataset at generation time

#### Connectivity Information
- Based on synaptic connections identified in electron microscopy data
- Connection strengths represent actual synaptic counts
- Percentages show relative connection strengths within each neuron type

#### Hemisphere Classifications
- **Left/Right**: Neurons located in respective brain hemispheres
- **Middle**: Neurons crossing midline or in central structures
- **Undefined**: Neurons without clear hemisphere assignment

#### ROI (Regions of Interest)
ROIs represent anatomically defined brain regions based on:
- Established neuroanatomical boundaries
- Functional organization principles
- Developmental origins
- Published brain atlases

#### Neurotransmitter Predictions
Neurotransmitter assignments are computational predictions based on:
- Connectivity patterns analysis
- Gene expression data
- Machine learning models
- Known neurotransmitter markers

**Note**: These are predictions and should be validated experimentally.

### Technical Requirements

#### Browser Compatibility
- **Modern browsers recommended**: Chrome, Firefox, Safari, Edge
- **JavaScript required**: Enable JavaScript for full functionality
- **Responsive design**: Works on desktop, tablet, and mobile devices

#### Performance Considerations
- **Large datasets**: Some neuron types may take time to load connectivity data
- **Interactive features**: All filtering and sorting happens client-side for responsiveness
- **Caching**: Browser caching improves performance on subsequent visits

### Data Reliability and Limitations

#### Data Sources
- All data sourced from neuPrint database
- Based on electron microscopy connectome data
- Neuron reconstructions are manually proofread
- Data undergoes continuous quality control

#### Known Limitations
- Dataset represents snapshot of specific brain samples
- Not all neuron types may be completely reconstructed
- Some rare neuron types may have limited representation
- Connectivity patterns may vary between individual flies
- Some connections may be missed due to reconstruction gaps

## Spatial Coverage Visualization

QuickPage generates interactive hexagonal grid visualizations that show the spatial coverage of neuron populations across different brain regions. This feature is particularly useful for visual system neurons in datasets like the optic lobe connectome.

### What are Hexagon Grids?

Hexagonal grids provide a spatial representation of neuron distribution and activity across anatomically defined brain columns. Each hexagon represents a specific location in the brain tissue, with colors indicating the density or count of neurons in that region.

### Available Visualizations

#### Brain Regions Covered
- **ME (Medulla)**: Inner visual processing region
- **LO (Lobula)**: Outer visual processing region  
- **LOP (Lobula Plate)**: Motion processing region

Each region is analyzed separately for left (L) and right (R) hemispheres.

#### Visualization Types

**Synapse Density Maps**:
- Show the density of synaptic connections in each brain column
- Useful for understanding connectivity patterns
- Colors represent relative synapse density from light (low) to dark red (high)

**Cell Count Maps**:
- Display the number of individual neurons in each column
- Help identify population distribution patterns
- Colors indicate neuron count from sparse (light) to dense (dark red) populations

### Understanding the Color Scheme

The hexagon grids use a consistent 5-tier red color scheme:

1. **Very Light Red** (#fee5d9): Lowest values (0-20th percentile)
2. **Light Red** (#fcbba1): Low values (20-40th percentile)
3. **Medium Red** (#fc9272): Moderate values (40-60th percentile)
4. **Dark Red** (#ef6548): High values (60-80th percentile)
5. **Very Dark Red** (#a50f15): Highest values (80-100th percentile)

### How to Use the Visualizations

#### Viewing Spatial Coverage
1. **Navigate to a neuron type page** that includes spatial data
2. **Scroll to the "Population spatial coverage" section**
3. **View the hexagonal grids** organized by brain region and hemisphere
4. **Compare patterns** across different regions and sides

#### Interpreting the Data
- **Dark regions**: High neuron density or synapse activity
- **Light regions**: Low neuron density or synapse activity
- **Empty areas**: No detected neurons in those columns
- **Patterns**: Look for clustering, gradients, or specific distributions

#### Interactive Features
- **Hover tooltips** (in SVG format): Show exact values for each hexagon
- **Scalable graphics**: Zoom in browsers for detailed examination
- **Print-friendly**: High-quality output suitable for publications

### Comparing Regions and Hemispheres

#### Regional Differences
- **ME vs LO vs LOP**: Compare how neuron types distribute across visual processing stages
- **Functional patterns**: Identify region-specific clustering or spread patterns
- **Processing hierarchy**: Understand how neurons organize across visual pathways

#### Hemisphere Analysis
- **Left vs Right comparison**: Identify bilateral symmetry or asymmetry
- **Lateralization patterns**: Detect hemisphere-specific distributions
- **Developmental insights**: Understand bilateral development patterns

### Data Interpretation Guidelines

#### What the Visualizations Show
- **Spatial distribution**: Where neurons are located within brain regions
- **Population density**: How densely neurons are packed in different areas
- **Connectivity patterns**: Where synaptic activity is concentrated
- **Functional organization**: How neurons organize to process information

#### What to Look For
- **Clustering**: Groups of neurons in specific areas
- **Gradients**: Smooth transitions from high to low density
- **Boundaries**: Sharp transitions between different regions
- **Symmetry**: Patterns that mirror across hemispheres
- **Gaps**: Areas with little or no neuron presence

#### Scientific Applications
- **Circuit mapping**: Understanding how visual circuits are organized
- **Developmental studies**: Tracking how neuron patterns form
- **Comparative analysis**: Comparing patterns across neuron types
- **Functional correlation**: Relating spatial patterns to behavior

### Technical Details for Users

#### Data Sources
- Based on electron microscopy reconstructions from neuPrint database
- Spatial coordinates derived from anatomical column assignments
- Synapse data from verified synaptic connections

#### Visualization Formats
- **SVG format**: Interactive, scalable graphics with hover tooltips
- **PNG format**: High-resolution images suitable for presentations
- **Responsive design**: Adapts to different screen sizes

#### Browser Requirements
- **Modern browsers**: Chrome, Firefox, Safari, Edge recommended
- **JavaScript enabled**: Required for interactive features
- **SVG support**: Necessary for full functionality

### Limitations and Considerations

#### Data Limitations
- **Reconstruction completeness**: Not all neurons may be fully reconstructed
- **Column boundaries**: Anatomical boundaries are approximations
- **Sample representation**: Data from specific brain samples
- **Resolution limits**: Limited by imaging resolution

#### Interpretation Cautions
- **Statistical significance**: Consider sample sizes when interpreting patterns
- **Individual variation**: Patterns may vary between individual flies
- **Methodological factors**: Reconstruction methods may affect apparent distributions
- **Comparative analysis**: Best used for relative comparisons rather than absolute values

## Data Citation and Documentation

When using data generated by QuickPage, proper citation and documentation practices ensure reproducibility and acknowledge data sources.

### Citing Generated Data

When using data from QuickPage-generated catalogs, include:

1. **Original neuPrint database and dataset**
2. **Specific dataset version** (e.g., hemibrain v1.2, optic-lobe v1.0)
3. **Generation date** of the catalog
4. **QuickPage version** used for generation

**Example Citation Format**:
```
Data generated using QuickPage v1.0 from neuPrint database 
(neuprint.janelia.org), dataset: hemibrain v1.2, 
catalog generated: 2024-01-15.
```

### Generated Documentation

QuickPage automatically creates comprehensive documentation for each generated website:

#### Catalog README
Each generated website includes a detailed README with:
- **Dataset information**: Source, version, generation timestamp
- **Usage instructions**: How to navigate and use the interactive features
- **Data explanations**: Understanding neuron counts, connectivity, and classifications
- **Technical requirements**: Browser compatibility and performance notes
- **Data limitations**: Known constraints and reliability information

#### Interactive Help Pages
Generated websites include built-in help featuring:
- **Filter explanations**: How to use search, hemisphere, and synapse count filters
- **Table interactions**: Sorting, pagination, and column visibility controls
- **Data interpretations**: Understanding percentages, balance metrics, and connectivity
- **Glossary**: Definitions of neuroanatomical terms and data types

### Data Reliability Guidelines

#### Understanding Data Sources
- **Electron microscopy**: Based on verified synaptic connections
- **Manual proofreading**: Neuron reconstructions undergo quality control
- **Continuous updates**: Data receives ongoing improvements and corrections
- **Sample representation**: Reflects specific brain samples, may vary between individuals

#### Data Limitations to Note
- **Reconstruction gaps**: Some connections may be missed due to incomplete reconstructions
- **Rare neuron types**: Limited representation may affect statistical reliability
- **Prediction accuracy**: Neurotransmitter predictions require experimental validation
- **Version dependencies**: Results may change with dataset updates

### Documentation Best Practices

#### For Researchers
- **Version tracking**: Always note the specific dataset version used
- **Generation metadata**: Include catalog generation date in publications
- **Method documentation**: Describe filtering and analysis criteria used
- **Data validation**: Cross-reference findings with original neuPrint database

#### For Data Sharing
- **Complete attribution**: Include all citation requirements
- **Version control**: Maintain records of dataset and QuickPage versions
- **Methodology notes**: Document any custom configurations or filters applied
- **Update notifications**: Note if analysis used updated dataset versions

---

This user guide provides comprehensive coverage of QuickPage functionality. For technical implementation details, architecture information, and development workflows, see the [Developer Guide](developer-guide.md).