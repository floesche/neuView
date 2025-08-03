# Dataset Adapters

The QuickPage dataset adapter system handles differences between NeuPrint datasets (hemibrain, CNS, optic-lobe) by providing dataset-specific processing while maintaining a consistent interface.

## Overview

Different NeuPrint datasets have varying database structures:

- **CNS**: Has dedicated `somaSide` column with 'L'/'R' values
- **Hemibrain**: Usually has `somaSide` column, sometimes needs extraction from instance names
- **Optic-Lobe**: Requires extracting soma side from instance names using regex patterns

The adapter system automatically detects the dataset type and applies appropriate processing.

## Architecture

### DatasetAdapter (Base Class)
All adapters inherit from this abstract base class:

```python
from quickpage import DatasetAdapter

class CustomAdapter(DatasetAdapter):
    def extract_soma_side(self, neurons_df):
        # Extract soma side information
        pass
    
    def normalize_columns(self, neurons_df):
        # Normalize column names if needed
        pass
    
    def get_synapse_counts(self, neurons_df):
        # Return (pre_total, post_total)
        pass
```

### Built-in Adapters

#### CNSAdapter
For CNS dataset (`neuprint-cns.janelia.org`):
- Uses existing `somaSide` column
- Standard column names
- Direct synapse count access

#### HemibrainAdapter  
For Hemibrain dataset (`neuprint.janelia.org`):
- Uses `somaSide` column when available
- Falls back to extracting from instance names with pattern `_([LR])$`
- Standard column names

#### OpticLobeAdapter
For Optic-lobe dataset (`neuprint.janelia.org` with optic-lobe dataset):
- Extracts soma side from instance names using regex `_([LR])(?:_|$)`
- Handles patterns like: `LC4_L`, `LPLC2_R_001`, `T4_L_medulla`
- Standard column names

## Usage

### Automatic Detection
The system automatically selects the right adapter based on dataset name:

```python
from quickpage import Config, NeuPrintConnector

config = Config.load("config.yaml")  # dataset: "cns"
connector = NeuPrintConnector(config)  # Uses CNSAdapter automatically
```

### Manual Adapter Selection
You can also get adapters directly:

```python
from quickpage import get_dataset_adapter

# Get adapter for specific dataset
cns_adapter = get_dataset_adapter('cns')
optic_adapter = get_dataset_adapter('optic-lobe:v1.1')
hemibrain_adapter = get_dataset_adapter('hemibrain')

# Use adapter directly
import pandas as pd
neurons_df = pd.DataFrame(...)  # Your neuron data
processed_df = adapter.extract_soma_side(neurons_df)
filtered_df = adapter.filter_by_soma_side(processed_df, 'left')
```

## Configuration

You can customize adapter behavior in `config.yaml`:

```yaml
# Dataset-specific configurations (optional)
dataset_config:
  optic-lobe:
    soma_side_extraction: "_([LR])(?:_|$)"  # Custom regex pattern
    instance_patterns:
      - "LC4_L"
      - "LPLC2_R_001" 
      - "T4_L_medulla"
  
  cns:
    soma_side_column: "somaSide"  # Column name for soma side
  
  hemibrain:
    soma_side_column: "somaSide"
    fallback_extraction: "_([LR])$"  # Fallback regex if column missing
```

## Soma Side Extraction

### CNS Dataset
```python
# Has dedicated column
somaSide
L
R
L
R
```

### Optic-Lobe Dataset
```python
# Extract from instance names
instance          -> somaSide
LC4_L             -> L
LC4_R             -> R  
LPLC2_L_001       -> L
LPLC2_R_002       -> R
T4_L_medulla      -> L
T4_R_medulla      -> R
```

### Hemibrain Dataset
```python
# Usually has column, but can extract if missing
instance          -> somaSide
LC4_L             -> L
LC4_R             -> R
```

## Adding Custom Adapters

### 1. Create Adapter Class
```python
from quickpage import DatasetAdapter, DatasetInfo

class MyCustomAdapter(DatasetAdapter):
    def __init__(self):
        dataset_info = DatasetInfo(
            name="my-dataset",
            soma_side_extraction=r"_([LR])_",
            pre_synapse_column="presynapses",
            post_synapse_column="postsynapses"
        )
        super().__init__(dataset_info)
    
    def extract_soma_side(self, neurons_df):
        # Your custom extraction logic
        neurons_df = neurons_df.copy()
        if 'customSide' in neurons_df.columns:
            neurons_df['somaSide'] = neurons_df['customSide']
        else:
            # Extract using regex pattern
            pattern = self.dataset_info.soma_side_extraction
            extracted = neurons_df['instance'].str.extract(pattern, expand=False)
            neurons_df['somaSide'] = extracted.fillna('U')
        return neurons_df
    
    def normalize_columns(self, neurons_df):
        # Rename columns if needed
        column_mapping = {
            'pre_syn': 'pre',
            'post_syn': 'post'
        }
        return neurons_df.rename(columns=column_mapping)
    
    def get_synapse_counts(self, neurons_df):
        pre_total = neurons_df['pre'].sum() if 'pre' in neurons_df.columns else 0
        post_total = neurons_df['post'].sum() if 'post' in neurons_df.columns else 0
        return int(pre_total), int(post_total)
```

### 2. Register Adapter
```python
from quickpage import DatasetAdapterFactory

DatasetAdapterFactory.register_adapter('my-dataset', MyCustomAdapter)
```

### 3. Use Custom Adapter
```python
# Update config.yaml
neuprint:
  dataset: "my-dataset"

# The system will automatically use your custom adapter
```

## Testing Adapters

Use the example script to test adapter behavior:

```bash
pixi run python examples/dataset_adapter_example.py
```

This shows:
- Supported datasets
- Adapter selection for each dataset
- Soma side extraction simulation
- Real data testing with current configuration

## Error Handling

Adapters handle common issues:

```python
# Missing soma side information
try:
    filtered_df = adapter.filter_by_soma_side(neurons_df, 'left')
except ValueError as e:
    print(f"Cannot filter by soma side: {e}")

# Unknown dataset
adapter = get_dataset_adapter('unknown-dataset')
# Returns CNSAdapter as default with warning
```

## Best Practices

1. **Use automatic detection**: Let the system choose the right adapter based on dataset name
2. **Test with real data**: Use the example scripts to verify adapter behavior
3. **Handle missing data**: Adapters should gracefully handle missing columns
4. **Document patterns**: Include example instance names in custom adapters
5. **Validate regex**: Test regex patterns with actual dataset instance names

## Migration Guide

If you have existing code that manually handles dataset differences:

### Before (Manual Handling)
```python
# Manual soma side extraction
if dataset == 'optic-lobe':
    neurons_df['somaSide'] = neurons_df['instance'].str.extract(r'_([LR])')
elif dataset == 'cns':
    # somaSide column already exists
    pass
```

### After (Using Adapters)
```python
# Automatic handling
connector = NeuPrintConnector(config)  # Uses appropriate adapter
# All dataset differences handled automatically
```

The adapter system provides a clean, extensible way to handle dataset differences while maintaining backward compatibility.
