# QuickPage

A modern Python CLI tool that generates HTML pages for neuron types using data from NeuPrint. Built with Domain-Driven Design (DDD) architecture for maintainability and extensibility.

## Features

### Core Features
- **Modern CLI Interface**: Built with Click and async support for responsive commands
- **NeuPrint Integration**: Fetches neuron data directly from NeuPrint servers with intelligent caching
- **Dataset Adapters**: Automatically handles differences between datasets (CNS, Hemibrain, Optic-lobe)
- **HTML Generation**: Creates beautiful HTML reports using Jinja2 templates with custom filters
- **Plume CSS**: Modern, responsive design using Plume CSS framework
- **Soma Side Filtering**: Generate reports for left, right, middle, or all hemispheres
- **Pixi Management**: Uses Pixi for dependency and environment management

### Architecture
- **Domain-Driven Design**: Clean architecture with proper separation of concerns
- **CQRS Pattern**: Command Query Responsibility Segregation for better maintainability  
- **Result Pattern**: Explicit error handling without exceptions
- **Dependency Injection**: Testable and modular service architecture
- **Rich Domain Model**: Type-safe entities, value objects, and business logic
- **Async Operations**: Non-blocking operations for better performance

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

### Quick Start

```bash
# Test connection to NeuPrint
pixi run quickpage test-connection

# List available neuron types
pixi run quickpage list-types --max-results 10

# Generate page for a specific neuron type
pixi run quickpage generate --neuron-type Dm4

# Inspect detailed statistics
pixi run quickpage inspect Dm4
```

### CLI Commands

#### Test Connection
```bash
# Basic connection test
quickpage test-connection

# Detailed connection test with dataset info
quickpage test-connection --detailed --timeout 60
```

#### List Available Neuron Types
```bash
# List random neuron types (default)
quickpage list-types

# List types alphabetically
quickpage list-types --sorted --max-results 20

# Show soma side information
quickpage list-types --show-soma-sides --show-statistics

# Filter by pattern
quickpage list-types --filter-pattern "LC" --sorted
```

#### Generate HTML Pages
```bash
# Generate for specific neuron type (all sides)
quickpage generate --neuron-type Dm4

# Generate for specific soma side
quickpage generate --neuron-type LC10a --soma-side left

# Generate with custom options
quickpage generate --neuron-type LPLC2 \
  --soma-side right \
  --output-dir custom_output \
  --template custom \
  --min-synapses 50 \
  --no-connectivity

# Bulk generation (auto-discover types)
quickpage generate --soma-side all --max-concurrent 3
```

#### Inspect Neuron Types
```bash
# Basic inspection
quickpage inspect Dm4

# Inspect with filters
quickpage inspect LC10a --soma-side left --min-synapses 10
```

### Advanced Usage

#### Verbose Mode
```bash
# Enable verbose logging for debugging
quickpage --verbose generate --neuron-type Dm4
quickpage --verbose test-connection --detailed
```

#### Custom Configuration
```bash
# Use custom config file
quickpage --config my_config.yaml generate --neuron-type Dm4
```

### Pixi Task Shortcuts

```bash
# Show help
pixi run dev

# Test NeuPrint connection
pixi run test-connection

# List neuron types
pixi run list-types

# Generate page for Dm4
pixi run generate-dm4

# Inspect Dm4 statistics
pixi run inspect-dm4

# Generate pages (auto-discover types)
pixi run generate
```

## Project Structure (Domain-Driven Design)

```
quickpage/
├── src/quickpage/
│   ├── core/                     # Domain Layer
│   │   ├── entities/            # Domain entities (Neuron, NeuronCollection)
│   │   ├── value_objects/       # Value objects (BodyId, SynapseCount, etc.)
│   │   └── ports/               # Domain interfaces (repositories, services)
│   ├── application/             # Application Layer  
│   │   ├── commands/            # Command objects (CQRS write side)
│   │   ├── queries/             # Query objects (CQRS read side)
│   │   └── services/            # Application services (orchestration)
│   ├── infrastructure/          # Infrastructure Layer
│   │   ├── repositories/        # Data access implementations
│   │   └── adapters/            # External service adapters
│   ├── presentation/            # Presentation Layer
│   │   └── cli.py               # CLI interface
│   ├── shared/                  # Shared Components
│   │   ├── result.py            # Result pattern for error handling
│   │   └── container.py         # Dependency injection container
│   ├── __init__.py              # Package initialization
│   ├── cli.py                   # Main CLI interface (DDD-based)
│   ├── config.py                # Configuration management
│   ├── neuprint_connector.py    # Legacy NeuPrint connector
│   ├── neuron_type.py           # Legacy NeuronType model
│   ├── dataset_adapters.py      # Dataset-specific adapters
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