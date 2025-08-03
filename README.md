# QuickPage

A Python CLI tool that generates HTML pages for neuron types using data from NeuPrint.

## Features

- **CLI Interface**: Built with Click for easy command-line usage
- **NeuPrint Integration**: Fetches neuron data directly from NeuPrint servers
- **HTML Generation**: Creates beautiful HTML reports using Jinja2 templates
- **Plume CSS**: Modern, responsive design using Plume CSS framework
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

### Custom Configuration (`quickpage_custom.toml`)

Override default settings for specific use cases:

```toml
[neuron_types]
LC10 = { soma_side = "both", min_synapse_count = 5 }
LPLC2 = { soma_side = "both", min_synapse_count = 10 }

[output]
include_3d_view = true
generate_json = true
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
│   └── page_generator.py     # HTML page generation
├── templates/                # Jinja2 HTML templates
├── output/                   # Generated HTML files
├── config.yaml              # Main configuration
├── quickpage_custom.toml     # Custom overrides
├── pixi.toml                 # Pixi dependencies
└── pyproject.toml           # Python package configuration
```

## HTML Output

Generated HTML pages include:

- **Summary Statistics**: Total neuron count, hemisphere distribution, synapse counts
- **Neuron Details Table**: Individual neuron information with Body IDs and synapse counts
- **Responsive Design**: Works on desktop and mobile devices
- **Modern Styling**: Clean, professional appearance using Pulse CSS

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
