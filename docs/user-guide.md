# neuView User Guide

A comprehensive guide for users of neuView, a modern Python CLI tool that generates interactive HTML pages for neuron types using data from NeuPrint. This guide covers installation, configuration, usage, and troubleshooting for all supported datasets.

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

Get up and running with neuView in minutes:

1. **Install neuView**:
   Clone the repository and install dependencies using pixi.

2. **Configure your connection**:
   Set up your environment and add your NeuPrint token using `pixi run setup-env`.

3. **Generate your first page**:
   Generate pages using `pixi run neuview generate -n [neuron_type]`.

4. **View the results**: 
   Open `output/index.html` in your browser to see your interactive neuron catalog

## Installation

### Prerequisites

- **pixi** package manager ([installation guide](https://pixi.sh/latest/))
- **Git** for cloning the repository
- **NeuPrint access token** (get from [neuprint.janelia.org](https://neuprint.janelia.org))

### Installation Steps

Clone the repository, navigate to the project directory, install dependencies using pixi, and verify the installation using the version and help commands.

### Setting Up Authentication

**Option 1: Environment File (Recommended with pixi)**
Set up the environment file template using `pixi run setup-env` and edit the .env file with your NeuPrint token.

**Option 2: Environment Variable**
Set the environment variable `NEUPRINT_APPLICATION_CREDENTIALS` to your token value.

**Option 3: Configuration File**
For the complete configuration structure, see the example configuration files in the project root directory.

**Getting Your Token**:
1. Visit [neuprint.janelia.org](https://neuprint.janelia.org)
2. Log in with your Google account
3. Click on your profile icon → "Account"
4. Copy your "Auth Token"

## Configuration

### Basic Configuration

neuView uses a `config.yaml` file for project settings. A default configuration is included:

neuView uses a `config.yaml` file for project settings with sections for NeuPrint server configuration, output settings, and HTML generation options. See the default configuration files for the complete structure and available options.

### Dataset-Specific Configurations

neuView includes pre-configured settings for different datasets:

- `config/config.cns.yaml` - Central Nervous System dataset
- `config/config.optic-lobe.yaml` - Optic Lobe dataset
- `config/config.fafb.yaml` - FAFB (FlyWire) dataset
- `config/config.example.yaml` - Template configuration

Use a specific configuration:
Use dataset-specific configurations with the `-c` flag to specify alternative configuration files.

### Dataset Aliases

neuView supports dataset aliases to handle different naming conventions for the same underlying dataset. This allows you to use alternative dataset names in your configuration without any warnings.

#### Supported Aliases

**CNS Dataset Aliases:**
- `male-cns` → Uses CNS adapter
- `male-cns:v0.9` → Uses CNS adapter  
- `male-cns:v1.0` → Uses CNS adapter

#### Usage Example

Configure your YAML file with the appropriate NeuPrint server, dataset alias, and token. The system will automatically resolve aliases like `male-cns:v0.9` to use the correct adapter.

This configuration will work seamlessly without any warnings. The system automatically:
- Recognizes `male-cns:v0.9` as a CNS dataset
- Uses the appropriate CNS adapter
- Handles all CNS-specific database queries correctly

#### Adding New Aliases

If you need support for additional dataset aliases, please refer to the Developer Guide for implementation details.

### Custom Neuron Types

Define custom neuron type settings in the configuration file using the neuron_types and custom_neuron_types sections. See the configuration examples for the complete structure and available options.

## Basic Usage

### Essential Commands

Essential commands include testing your connection (`neuview test-connection`), generating single or multiple neuron type pages (`neuview generate -n [type]`), inspecting neuron types (`neuview create-list`), and creating the main index page (`neuview generate-all`). All commands are run using the `pixi run` prefix.

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

Manage caching with commands for viewing statistics, cleaning expired entries, and clearing all cache data.

## Advanced Features

### Batch Processing with Queue System

Process multiple neuron types efficiently using the queue system:

Queue management commands allow adding neuron types to the processing queue, processing the entire queue, viewing queue status, and clearing the queue.

### Automatic Page Generation

neuView automatically detects available soma sides and generates all appropriate pages. For neuron types with data on multiple sides, it creates individual hemisphere pages plus a combined view. For single-hemisphere types, it creates only the relevant side page.

**Automatic Detection Logic**:
- **Multiple hemispheres**: Creates individual side pages + combined page
- **Single hemisphere**: Creates only the relevant side page
- **Mixed data**: Handles unknown/unassigned soma sides intelligently
- **No user intervention required**: System analyzes data and creates optimal page set

### Custom Templates

Use custom HTML templates by specifying a template directory in your configuration file's output section.

### Citation Management

neuView automatically tracks missing citations and logs them for easy maintenance:

**Monitoring Missing Citations**: Check the missing citations log file in `output/.log/missing_citations.log` to monitor citation issues after page generation.

**Adding Missing Citations**

When citations are missing, add them to `input/citations.csv` using the format: citation_key, DOI_or_URL, full_citation_text.

**Citation Log Features**

- **Automatic Tracking**: Missing citations are logged during page generation
- **Context Information**: Logs show which neuron type and operation encountered the missing citation
- **Rotating Logs**: Files automatically rotate when they reach 1MB (keeps 5 backups)
- **Timestamped Entries**: Each entry includes when the missing citation was encountered

**Example Log Entries**: Log entries include timestamps, warning level, missing citation key, and context about which neuron type and operation encountered the issue.

### Verbose Mode and Debugging

Get detailed information about processing:

Enable verbose output with the `--verbose` flag or debug mode by setting the `NEUVIEW_DEBUG` environment variable.

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
- **Synonym and Flywire Type Filtering**: Click on synonym tags (blue) or Flywire type tags (green) to filter neuron types by additional naming information

#### Advanced Filtering System

The Types page provides comprehensive filtering capabilities through multiple mechanisms designed for efficient neuron type exploration.

##### Basic Filters

Available through dropdown controls:

- **ROI (Region of Interest)**: Filter by brain regions where neurons are found
- **Neurotransmitter**: Filter by consensus or predicted neurotransmitter type
- **Dimorphism**: Filter by sexual dimorphism characteristics
- **Cell Class Hierarchy**: Filter by superclass, class, or subclass
- **Soma Side**: Filter by hemisphere (left, right, middle, undefined)

##### Tag-Based Filters

Advanced filters activated by clicking colored tags within neuron type cards:

**Synonym Filtering**:
- **Purpose**: Find all neuron types that have alternative names or synonyms from various naming conventions
- **How to Use**:
  1. Look for blue synonym tags on neuron type cards
  2. Click any synonym tag to activate the synonym filter
  3. Only neuron types with synonyms will be displayed
  4. All synonym tags across all visible cards will be highlighted in blue
  5. Click any synonym tag again to deactivate the filter
- **Use Cases**:
  - Finding neuron types with historical or alternative naming
  - Identifying types referenced in multiple studies
  - Discovering naming conventions across different datasets

**Flywire Type Filtering**:
- **Purpose**: Find neuron types that have meaningful Flywire cross-references (Flywire synonyms that differ from the neuron type name)
- **How to Use**:
  1. Look for green Flywire type tags on neuron type cards
  2. Click any Flywire type tag to activate the Flywire filter
  3. Only neuron types with displayable Flywire types will be shown
  4. All Flywire type tags across all visible cards will be highlighted in green
  5. Click any Flywire type tag again to deactivate the filter
- **Important Note**: This filter only shows neuron types where the Flywire synonym is different from the neuron type name:
  - ✅ `Tm3` with Flywire synonym `CB1031` → Will be shown (meaningful cross-reference)
  - ❌ `AOTU019` with Flywire synonym `AOTU019` → Will not be shown (not meaningful)
- **Use Cases**:
  - Finding neuron types with cross-dataset references
  - Identifying types mapped to Flywire connectome
  - Discovering meaningful alternative identifiers for comparative analysis

##### Text Search Filter

**Real-time text-based search** that searches across:
- Neuron type names
- Synonym names  
- Flywire type names
- Instant filtering as you type

##### Filter Behavior

**Independence**:
- Each filter type works independently
- Multiple basic filters can be combined (ROI + neurotransmitter, etc.)
- Only one tag-based filter (synonym OR Flywire) can be active at a time

**Interaction Rules**:
- Clicking a synonym tag while a Flywire filter is active will switch to synonym filtering
- Clicking a Flywire tag while a synonym filter is active will switch to Flywire filtering
- Basic dropdown filters can be combined with tag-based filters

**Visual Feedback**:
- Active filters are clearly indicated through:
  - Highlighted tags (blue for synonyms, green for Flywire types)
  - Updated filter status messages
  - Real-time count updates of visible results

**Reset Options**:
- **Individual Reset**: Click the same tag type again to deactivate
- **Clear All**: Use the "Clear Filters" button to reset all filters
- **Filter Switch**: Click a different tag type to switch filters
- **Page Refresh**: Reloads with no active filters

##### Troubleshooting Filters

**Common Issues**:

*"No results found"*
- Check if multiple restrictive filters are applied
- Try clearing all filters and starting over
- Verify the dataset contains the expected data

*"Flywire filter shows no results"*
- This dataset may not have meaningful Flywire cross-references
- Remember that identical Flywire synonyms are not considered displayable

*"Tags not highlighting correctly"*
- Ensure JavaScript is enabled
- Check for browser console errors
- Try refreshing the page

**Performance Considerations**:
- Large datasets (>1000 neuron types) may experience slower filter response
- Consider using basic filters first to reduce the working set
- Text search is debounced to prevent excessive filtering during typing

##### Best Practices

1. **Start Broad**: Use basic filters first to narrow down the dataset
2. **Combine Strategically**: Combine complementary filters (e.g., ROI + neurotransmitter)
3. **Use Tag Filters for Discovery**: Use synonym/Flywire filters to find cross-referenced types
4. **Check Filter Status**: Always verify which filters are active via visual indicators

This comprehensive filtering system helps researchers quickly identify neuron types that have been cross-referenced with external databases or have alternative naming information available, making data exploration and comparative analysis more efficient.

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

1. Check the citation log file in `output/.log/missing_citations.log`

2. Add missing citations to `input/citations.csv` using the format: citation_key, DOI_or_URL, full_citation_text

3. Regenerate affected pages using the `neuview generate` command

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
Verify your token is set, test the connection, and check configuration using the appropriate neuview commands with verbose output for detailed information.

**Connection Issues**
Test with verbose output, try different server settings in your config.yaml file, and check network connectivity to the NeuPrint server.

**Performance Issues**
Check cache status, clear corrupted cache if needed, and enable performance monitoring with environment variables.

**Missing Output**
Verify generation completed by checking the output directory, regenerate with verbose output, and check for errors using the verbose flag.

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

Set the NEUVIEW_DEBUG and NEUVIEW_PROFILE environment variables and run neuview with the verbose flag.

This provides:
- Detailed operation logging
- Performance timing information
- Database query details
- Cache operation tracking
- Memory usage statistics

### Getting Help

1. **Check built-in help**: `pixi run neuview --help`
2. **Test connection**: `pixi run neuview test-connection`
3. **Review configuration**: Verify your `config.yaml`
4. **Check cache**: `pixi run neuview cache --action stats`
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

The configuration structure includes sections for NeuPrint server settings, output directories, HTML generation options, caching configuration, visualization parameters, and neuron type definitions. See the example configuration files for the complete YAML structure and available options.

### Command Reference

Available commands include `generate` for creating neuron type pages, `create-list` for generating index pages, `generate-all` for processing all known types, `test-connection` for verifying NeuPrint access, `cache` for managing the cache system, and `queue` for batch processing. All commands are run with the `pixi run neuview` prefix.

### Performance Tips

1. **Use Caching**: Cache provides up to 97.9% speed improvement on subsequent runs
2. **Process in Batches**: Use queue system for multiple neuron types
3. **Clean Cache Periodically**: Remove expired entries with `cache --action clean`
4. **Monitor Progress**: Use verbose mode for long-running operations
5. **Optimize Configuration**: Adjust cache settings based on available memory

### Data Citation

When using neuView-generated data in publications:

**Required Citations**:
1. **Original neuPrint database** and dataset version
2. **neuView version** used for generation  
3. **Generation date** of the catalog
4. **Specific filtering** or configuration applied

**Example Citation**: Include neuView version, neuPrint database details, dataset version, generation date, and any specific configuration or filtering applied. Reference original dataset publications and specify any custom analysis parameters used.

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `NEUPRINT_APPLICATION_CREDENTIALS` | NeuPrint API token | `your-token-string` |
| `NEUVIEW_CONFIG_PATH` | Custom config file path | `/path/to/config.yaml` |
| `NEUVIEW_CACHE_DIR` | Cache directory override | `/tmp/neuview_cache` |
| `NEUVIEW_DEBUG` | Enable debug logging | `1` or `true` |
| `NEUVIEW_PROFILE` | Enable performance profiling | `1` or `true` |

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
A: Use `pixi run neuview generate-all` to process all known neuron types, or use the queue system for more control.

**Q: Can I customize the HTML output?**
A: Yes, you can provide custom templates by setting `template_dir` in your configuration and creating modified versions of the template files.

**Q: How do I improve generation speed?**
A: Enable caching (default), use batch processing with queues, and ensure adequate memory allocation. Cache provides significant performance improvements.

**Q: What browsers are supported?**
A: Modern browsers (Chrome, Firefox, Safari, Edge) with JavaScript enabled. Chrome is recommended for optimal performance.

**Q: How do I export data from the generated pages?**
A: Use the export functions in data tables, or enable JSON export in configuration to generate machine-readable data alongside HTML.

**Q: How does automatic page generation work?**
A: neuView analyzes your neuron data and automatically creates the appropriate pages:
- For neuron types with multiple hemispheres (L/R/M): Creates individual hemisphere pages AND a combined page
- For neuron types with only one hemisphere: Creates only that hemisphere's page (no combined page)
- No manual soma-side specification needed - the system detects and generates optimal page sets automatically

**Q: Can I still generate hemisphere-specific pages?**
A: Yes, but it's now automatic! neuView will generate hemisphere-specific pages (e.g., Dm4_L.html, Dm4_R.html) whenever hemisphere-specific data exists. You don't need to specify --soma-side anymore.

---

This user guide provides comprehensive coverage of neuView's features and functionality. For technical implementation details, see the [Developer Guide](developer-guide.md).
