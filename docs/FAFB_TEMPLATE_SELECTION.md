# FAFB Template Selection

This document explains how QuickPage automatically selects the appropriate Neuroglancer template based on the dataset being used.

## Overview

When generating Neuroglancer URLs, QuickPage now automatically detects if the dataset is FAFB (FlyWire Adult Fly Brain) and uses the appropriate template:

- **FAFB datasets**: Uses `templates/neuroglancer-fafb.js.jinja`
- **Other datasets**: Uses `templates/neuroglancer.js.jinja`

## How It Works

The template selection is handled in the `URLGenerationService.generate_neuroglancer_url()` method:

1. The service checks if "fafb" appears in the dataset name (case-insensitive)
2. If detected, it loads the FAFB-specific template
3. Otherwise, it loads the standard template

## Dataset Detection

The detection is case-insensitive and looks for "fafb" anywhere in the dataset name. Examples:

- `flywire-fafb:v783b` → Uses FAFB template ✓
- `FLYWIRE-FAFB:V783B` → Uses FAFB template ✓
- `some-FAFB-dataset:v1` → Uses FAFB template ✓
- `hemibrain:v1.2.1` → Uses standard template ✓
- `cns:v1.0` → Uses standard template ✓

## Template Differences

### Standard Template (`neuroglancer.js.jinja`)
- Designed for CNS, hemibrain, and optic-lobe datasets
- Uses standard neuroglancer layer configurations
- Standard coordinate system and scaling

### FAFB Template (`neuroglancer-fafb.js.jinja`)
- Optimized for FlyWire FAFB dataset
- Uses FlyWire-specific data sources and layer configurations
- Different coordinate system and scaling appropriate for FAFB data
- Includes FAFB-specific segmentation layers and synapse annotations

## Configuration

The template selection is automatic and requires no additional configuration. The dataset name in your `config.yaml` file determines which template is used:

```yaml
neuprint:
  server: "neuprint-cns.janelia.org"
  dataset: "flywire-fafb:v783b"  # This will trigger FAFB template
```

## Logging

Template selection is logged at DEBUG level:

```
DEBUG - Using Neuroglancer template: neuroglancer-fafb.js.jinja for dataset: flywire-fafb:v783b
```

## Testing

The template selection logic is thoroughly tested in `test/services/test_url_generation_service.py` with test cases covering:

- Standard datasets use standard template
- FAFB datasets use FAFB template
- Case-insensitive detection
- Proper logging
- Error handling and fallback behavior

## Adding New Dataset Types

To add support for additional dataset types:

1. Create a new template file in the `templates/` directory
2. Modify the detection logic in `URLGenerationService.generate_neuroglancer_url()`
3. Add appropriate test cases

Example modification:
```python
# In url_generation_service.py
if "fafb" in self.config.neuprint.dataset.lower():
    template_name = "neuroglancer-fafb.js.jinja"
elif "new-dataset-type" in self.config.neuprint.dataset.lower():
    template_name = "neuroglancer-new-dataset.js.jinja"
else:
    template_name = "neuroglancer.js.jinja"
```
