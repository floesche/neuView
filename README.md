# QuickPage

A Python CLI tool that generates HTML pages for neuron types using data from NeuPrint.

## Features

- **CLI Interface**: Built with Click for easy command-line usage
- **NeuPrint Integration**: Fetches neuron data directly from NeuPrint servers
- **Dataset Adapters**: Automatically handles differences between datasets (CNS, Hemibrain, Optic-lobe)
- **HTML Generation**: Creates beautiful HTML reports using Jinja2 templates
- **Plume CSS**: Modern, responsive design using Plume CSS framework
- **NeuronType Class**: Object-oriented interface for neuron data with lazy loading
- **Configurable**: YAML configuration with TOML overrides
- **Soma Side Filtering**: Generate reports for left, right, or both hemispheres
- **Pixi Management**: Uses Pixi for dependency and environment management

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd quickpage
```

2. Install dependencies using Pixi (configuration is in pyproject.toml):
```bash
pixi install
```

3. Set up your NeuPrint token:

   **Option 1: Using .env file (recommended):**
   ```bash
   pixi run setup-env
   # Edit .env and add your NeuPrint token
   ```

   **Option 2: Manual .env setup:**
   ```bash
   cp .env.example .env
   # Edit .env and add your NeuPrint token
   ```

   **Option 3: Environment variable:**
   ```bash
   export NEUPRINT_TOKEN="your-token-here"
   ```

   **Option 4: Configuration file:**
   ```bash
   # Add to config.yaml:
   # token: "your-token-here"
   ```

## Configuration

### Main Configuration (`config.yaml`)

```yaml
neuprint:
  server: "neuprint.janelia.org"
  dataset: "hemibrain:v1.2.1"
  token: ""  # Optional, can use NEUPRINT_TOKEN env var

output:
  directory: "output"
  template_dir: "templates"

neuron_types:
  - name: "LC10"
    description: "Lobula Columnar 10"
    query_type: "type"
  - name: "LPLC2"
    description: "Lobula Plate Lobula Columnar 2"
    query_type: "type"

html:
  title_prefix: "Neuron Type Report"
  css_framework: "plume"
  include_images: true
  include_connectivity: true
```

### Custom Neuron Type Settings

You can add custom settings for specific neuron types directly in `config.yaml`:

```yaml
neuron_types:
  - name: "LPLC2"
    description: "Lobula Plate Lobula Columnar 2"
    query_type: "type"
    soma_side: "both"
    min_synapse_count: 10

# Additional configurations for neuron types not in the main list
custom_neuron_types:
  LC10:
    soma_side: "both"
    min_synapse_count: 5

# Additional output settings
output:
  directory: "output"
  template_dir: "templates"
  include_3d_view: true
  generate_json: true
```

## Usage

### Basic Commands

```bash
# Show help
pixi run dev

# Test NeuPrint connection
quickpage test-connection

# List configured neuron types
quickpage list-types

# Generate pages for all configured neuron types
quickpage generate

# Generate page for specific neuron type
quickpage generate --neuron-type LC10

# Generate for specific soma side
quickpage generate --neuron-type LC10 --soma-side left

# Use custom output directory
quickpage generate --output-dir /path/to/output
```

### Advanced Usage

```bash
# Use custom configuration file
quickpage -c my_config.yaml generate

# Verbose output for debugging
quickpage -v generate --neuron-type LC10
```

## Project Structure

```
quickpage/
├── src/quickpage/
│   ├── __init__.py           # Package initialization
│   ├── cli.py                # Click CLI interface
│   ├── config.py             # Configuration management
│   ├── neuprint_connector.py # NeuPrint data fetching
│   ├── neuron_type.py        # NeuronType data model
│   ├── dataset_adapters.py   # Dataset-specific adapters
│   └── page_generator.py     # HTML page generation
├── templates/                # Jinja2 HTML templates
├── output/                   # Generated HTML files
├── docs/                     # Documentation
│   ├── neuron_type.md        # NeuronType class documentation
│   └── dataset_adapters.md   # Dataset adapter documentation
├── examples/                 # Example scripts
│   ├── neuron_type_example.py # NeuronType usage example
│   └── dataset_adapter_example.py # Dataset adapter example
├── config.yaml              # Main configuration
├── .env.example             # Environment variables template
├── pixi.toml                # Pixi dependencies (legacy)
└── pyproject.toml           # Python package & Pixi configuration
```

## NeuronType Class

The `NeuronType` class provides an object-oriented interface for working with neuron data:

```python
from quickpage import Config, NeuPrintConnector, NeuronType
from quickpage.config import NeuronTypeConfig

# Create neuron type instance
config = Config.load("config.yaml")
connector = NeuPrintConnector(config)
nt_config = NeuronTypeConfig(name="LC4", description="Motion detection neurons")
lc4_neurons = NeuronType("LC4", nt_config, connector, soma_side='both')

# Access data (automatically fetches when needed)
print(f"Total neurons: {lc4_neurons.get_neuron_count()}")
print(f"Left neurons: {lc4_neurons.get_neuron_count('left')}")
print(f"Average presynapses: {lc4_neurons.get_synapse_stats()['avg_pre']}")

# Generate HTML page
from quickpage import PageGenerator
generator = PageGenerator(config, "output/")
output_file = generator.generate_page_from_neuron_type(lc4_neurons)
```

**Key Features:**
- Lazy loading of data from NeuPrint
- Convenient access methods for common statistics
- Soma side filtering (left, right, both)
- Direct integration with PageGenerator
- Type-safe data structures

See [`docs/neuron_type.md`](docs/neuron_type.md) and [`examples/neuron_type_example.py`](examples/neuron_type_example.py) for detailed documentation and examples.

## Dataset Adapters

QuickPage automatically handles differences between NeuPrint datasets:

- **CNS Dataset**: Uses dedicated `somaSide` column
- **Hemibrain Dataset**: Uses `somaSide` column or extracts from instance names  
- **Optic-Lobe Dataset**: Extracts soma side from instance names using regex patterns

The system automatically detects your dataset and applies the appropriate processing:

```yaml
# config.yaml
neuprint:
  server: "neuprint-cns.janelia.org"
  dataset: "cns"  # Automatically uses CNSAdapter

# OR for optic-lobe
neuprint:
  server: "neuprint.janelia.org" 
  dataset: "optic-lobe:v1.1"  # Automatically uses OpticLobeAdapter
```

See [`docs/dataset_adapters.md`](docs/dataset_adapters.md) and [`examples/dataset_adapter_example.py`](examples/dataset_adapter_example.py) for detailed information.

## HTML Output

Generated HTML pages include:

- **Summary Statistics**: Total neuron count, hemisphere distribution, synapse counts
- **Neuron Details Table**: Individual neuron information with Body IDs and synapse counts
- **Connectivity Analysis**: Upstream and downstream connections with neurotransmitter data
- **Responsive Design**: Works on desktop and mobile devices
- **Modern Styling**: Clean, professional appearance using Plume CSS

### File Organization

- **HTML files**: Stored in the output directory (e.g., `output/`)
  - General pages: `NEURONTYPE.html` (for multiple soma sides)
  - Specific pages: `NEURONTYPE_[RLM].html` (for single soma sides)
- **JSON data files**: Stored in hidden `.data` subdirectory (e.g., `output/.data/`)
  - Same naming pattern as HTML files but with `.json` extension
  - Contains structured data for programmatic access

### Auto-Detection Logic

When using `--soma-side all` (default), the system automatically:
- **Multiple sides available**: Generates both general and specific pages
- **Single side available**: Generates only the specific page for that side
- **No data available**: Skips generation with appropriate messaging

## Data Classes

### NeuPrintConnector

Handles all communication with NeuPrint servers:

- Connection management and authentication
- Neuron data fetching with filtering
- Summary statistics calculation
- Connectivity analysis

### PageGenerator

Manages HTML page creation:

- Jinja2 template rendering
- File output management
- Custom template filters
- Responsive design integration

### Config

Configuration management system:

- YAML primary configuration
- TOML override support
- Environment variable integration
- Type-safe configuration classes

## Development

### Running Tests

```bash
# Test connection to NeuPrint
pixi run quickpage test-connection

# Generate sample report
pixi run quickpage generate --neuron-type LC10
```

### Adding Custom Templates

1. Create new template in `templates/` directory
2. Use Jinja2 syntax with available context variables:
   - `config`: Configuration object
   - `neuron_data`: NeuPrint data
   - `summary`: Summary statistics
   - `neurons_df`: Pandas DataFrame of neurons

### Extending Functionality

- Add new CLI commands in `cli.py`
- Extend NeuPrint queries in `neuprint_connector.py`
- Create custom template filters in `page_generator.py`
- Add configuration options in `config.py`

## Troubleshooting

### Common Issues

1. **Authentication Error**: Ensure your NeuPrint token is correctly set
2. **No Data Found**: Check neuron type names and dataset availability
3. **Template Errors**: Verify Jinja2 template syntax and variable names

### Debug Mode

Run with verbose flag for detailed error information:

```bash
quickpage -v generate --neuron-type YourNeuronType
```

## License

This project is licensed under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request


# ToDo List

- ROI table only for connected or for all ROIs?
- QR Code page
- Hierarchy of ROIs
- Definition of Synapses
- Definition of Primary ROI