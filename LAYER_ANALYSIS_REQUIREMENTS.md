# Layer-Based ROI Analysis Requirements

## Overview

The Layer-Based ROI Analysis table for the optic-lobe dataset follows specific visibility and content requirements to ensure consistent and comprehensive synapse reporting.

## Requirements

### 1. Table Visibility Condition

**The table appears if and only if:**
- The neuron type has **more than 0 connections** in ANY layer of ME, LO, or LOP
- Layer pattern: `(ME|LO|LOP)_[RL]_layer_*`

**Examples:**
- ✅ Shows table: Neuron has synapses in `ME_R_layer_1`
- ✅ Shows table: Neuron has synapses in `LO_L_layer_3` and `LOP_R_layer_2`
- ❌ Hides table: Neuron has no layer connections (only central brain, AME, LA)

### 2. Always Show Core Entries

**When the table appears, it ALWAYS shows these entries (even if 0 synapses):**

#### Central Brain (Consolidated)
- **Entry name:** "central brain"
- **Content:** Sum of all ROIs that are NOT:
  - `LA`, `LO`, `LOP`, `ME`, `AME`
  - Layer patterns: `*_[RL]_layer_*`
  - Column patterns: `*_[RL]_col_*`
- **Examples included:** PVLP, FB(L), FB(R), PB, EB, NO(L), SMP(R), etc.

#### LA (Individual Entry)
- **Entry name:** "LA"
- **Content:** Sum of all LA-related ROIs
- **Examples included:** LA(L), LA(R), LA_L, LA_R, etc.

#### AME (Individual Entry)
- **Entry name:** "AME"
- **Content:** Sum of all AME-related ROIs
- **Examples included:** AME(L), AME(R), AME_L, AME_R, etc.

### 3. Show All Dataset Layers

**The table shows ALL layer entries that exist in the dataset, including:**
- All `ME_[RL]_layer_*` patterns found in the dataset
- All `LO_[RL]_layer_*` patterns found in the dataset
- All `LOP_[RL]_layer_*` patterns found in the dataset

**Even if the specific neuron type has 0 connections in those layers.**

#### Example Dataset Layers:
```
ME_R_layer_1, ME_R_layer_2, ME_L_layer_1, ME_L_layer_2
LO_R_layer_3, LO_L_layer_3
LOP_R_layer_1, LOP_R_layer_2, LOP_L_layer_1, LOP_L_layer_2
```

### 4. Default to Zero

**When a neuron type has no connections in a region/layer:**
- The entry still appears in the table
- Pre-synapses: 0
- Post-synapses: 0
- Total: 0

## Example Table Output

For LPLC2 neurons in optic-lobe dataset:

| Region | Soma Side | Layer | Pre-synapses | Post-synapses | Total |
|--------|-----------|-------|--------------|---------------|-------|
| central brain | Both | — | 456 | 89 | 545 |
| LA | Both | — | 23 | 7 | 30 |
| AME | Both | — | 0 | 0 | 0 |
| ME | R | 1 | 234 | 12 | 246 |
| ME | R | 2 | 189 | 8 | 197 |
| ME | L | 1 | 0 | 0 | 0 |
| ME | L | 2 | 145 | 23 | 168 |
| LO | R | 3 | 67 | 4 | 71 |
| LO | L | 3 | 0 | 0 | 0 |
| LOP | R | 1 | 89 | 15 | 104 |
| LOP | R | 2 | 0 | 0 | 0 |
| LOP | L | 1 | 0 | 0 | 0 |
| LOP | L | 2 | 0 | 0 | 0 |

## Implementation Details

### Visibility Logic
```python
# Check for any layer connections
layer_pattern = r'^(ME|LO|LOP)_[RL]_layer_\d+$'
layer_rois = roi_df[roi_df['roi'].str.match(layer_pattern, na=False)]
has_layer_connections = not layer_rois.empty

if not has_layer_connections:
    return None  # Hide table
```

### Core Entries Logic
```python
# Always add these entries
entries = [
    create_central_brain_entry(),  # Consolidated
    create_la_entry(),            # Individual
    create_ame_entry(),           # Individual
]
```

### All Layers Logic
```python
# Find all layer patterns in entire dataset
all_dataset_rois = roi_df['roi'].unique().tolist()
for roi in all_dataset_rois:
    match = re.match(layer_pattern, roi)
    if match:
        add_layer_entry(region, side, layer_num)  # Even if 0 synapses
```

## Benefits

1. **Consistent Display**: Table always shows same structure when visible
2. **Complete Information**: No missing synapse data for regions/layers
3. **Clear Zero Indication**: Explicitly shows when neuron has no connections
4. **Comprehensive Coverage**: All dataset layers visible for comparison
5. **Logical Grouping**: Central brain consolidated, LA/AME individual

## Testing

Use `test_layer_analysis_requirements.py` to verify:
- ✅ Table visibility based on layer connections
- ✅ Core entries always present (central brain, LA, AME)
- ✅ All dataset layers shown (even with 0 connections)
- ✅ Zero values properly displayed
- ✅ HTML output matches requirements

## Migration Notes

### Before
- Table showed only regions with >0 synapses
- Missing entries caused confusion about synapse totals
- Inconsistent display across neuron types

### After
- Table shows consistent structure for all neuron types
- Complete synapse accounting with explicit zeros
- Predictable layout for analysis and comparison