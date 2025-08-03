# NeuronType Class

The `NeuronType` class is a data model that encapsulates neuron data fetched from NeuPrint and provides a clean, object-oriented interface for working with neuron types.

## Overview

The `NeuronType` class:
- Fetches data from NeuPrint using the `NeuPrintConnector`
- Encapsulates all neuron data and metadata
- Provides lazy loading (data is fetched when first needed)
- Offers convenient methods for accessing neuron statistics
- Can be passed directly to the `PageGenerator` for HTML generation

## Basic Usage

```python
from quickpage import Config, NeuPrintConnector, NeuronType
from quickpage.config import NeuronTypeConfig

# Load configuration and create connector
config = Config.load("config.yaml")
connector = NeuPrintConnector(config)

# Create neuron type configuration
lc4_config = NeuronTypeConfig(
    name="LC4",
    description="Lobula Columnar Type 4 neurons",
    query_type="type"
)

# Create NeuronType instance
lc4_neurons = NeuronType("LC4", lc4_config, connector, soma_side='both')

# Access data (fetches automatically when needed)
print(f"Total neurons: {lc4_neurons.get_neuron_count()}")
print(f"Left neurons: {lc4_neurons.get_neuron_count('left')}")
print(f"Right neurons: {lc4_neurons.get_neuron_count('right')}")
```

## Key Features

### Lazy Loading
Data is fetched from NeuPrint only when first accessed:

```python
neuron_type = NeuronType("LC4", config, connector)
print(neuron_type.is_fetched)  # False

# This triggers data fetching
count = neuron_type.get_neuron_count()
print(neuron_type.is_fetched)  # True
```

### Data Access Properties

```python
# Raw DataFrames
neurons_df = neuron_type.neurons      # Main neuron data
roi_df = neuron_type.roi_counts       # ROI count data

# Summary statistics
summary = neuron_type.summary
print(f"Total count: {summary.total_count}")
print(f"Type name: {summary.type_name}")

# Connectivity data
connectivity = neuron_type.connectivity
print(f"Upstream partners: {len(connectivity.upstream)}")
print(f"Downstream partners: {len(connectivity.downstream)}")
```

### Convenience Methods

```python
# Get neuron counts
total = neuron_type.get_neuron_count()
left = neuron_type.get_neuron_count('left')
right = neuron_type.get_neuron_count('right')

# Get synapse statistics
stats = neuron_type.get_synapse_stats()
print(f"Average presynapses: {stats['avg_pre']}")
print(f"Average postsynapses: {stats['avg_post']}")
```

### Soma Side Filtering

```python
# Get all neurons
all_neurons = NeuronType("LC4", config, connector, soma_side='both')

# Get only left-side neurons
left_neurons = NeuronType("LC4", config, connector, soma_side='left')

# Get only right-side neurons
right_neurons = NeuronType("LC4", config, connector, soma_side='right')
```

## Integration with PageGenerator

The `NeuronType` class can be passed directly to the page generator:

```python
from quickpage import PageGenerator

generator = PageGenerator(config, "output/")
output_file = generator.generate_page_from_neuron_type(neuron_type)
```

Or convert to dictionary format for the traditional method:

```python
neuron_data = neuron_type.to_dict()
output_file = generator.generate_page(neuron_type.name, neuron_data, neuron_type.soma_side)
```

## Data Classes

### NeuronSummary
Contains summary statistics:
- `total_count`: Total number of neurons
- `left_count`: Number of left-side neurons
- `right_count`: Number of right-side neurons
- `type_name`: Neuron type name
- `soma_side`: Soma side filter used
- `total_pre_synapses`: Total presynapses across all neurons
- `total_post_synapses`: Total postsynapses across all neurons
- `avg_pre_synapses`: Average presynapses per neuron
- `avg_post_synapses`: Average postsynapses per neuron

### ConnectivityData
Contains connectivity information:
- `upstream`: List of upstream partners
- `downstream`: List of downstream partners
- `note`: Additional notes about connectivity

## Error Handling

```python
try:
    neuron_type = NeuronType("InvalidType", config, connector)
    count = neuron_type.get_neuron_count()
except RuntimeError as e:
    print(f"Failed to fetch neuron data: {e}")
```

## Examples

See `examples/neuron_type_example.py` for a complete working example that demonstrates all features of the `NeuronType` class.
