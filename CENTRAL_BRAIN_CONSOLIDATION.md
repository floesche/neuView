# Central Brain Consolidation in Layer-Based ROI Analysis

## Overview

For the optic-lobe dataset, the Layer-Based ROI Analysis now consolidates all central brain regions under a single "central brain" summary entry, rather than listing each central brain ROI individually.

## What Gets Consolidated

### Individual Entries (NOT consolidated):
- **Layer patterns**: `(ME|LO|LOP)_[RL]_layer_*`
  - Examples: `ME_R_layer_1`, `LO_L_layer_3`, `LOP_R_layer_2`
- **Column patterns**: `(ME|LO|LOP)_[RL]_col_*`
  - Examples: `ME_R_col_A1_T1`, `LO_L_col_B2_T3`

### Consolidated Under "central brain":
All ROIs that are **NOT**:
- `LA`, `LO`, `LOP`, `ME`, `AME` (basic optic regions)
- Layer patterns: `*_[RL]_layer_*`
- Column patterns: `*_[RL]_col_*`

**Examples of consolidated ROIs:**
- `PVLP`, `PVLP(L)`, `PVLP(R)`
- `FB(L)`, `FB(R)`, `PB`, `EB`
- `NO(L)`, `NO(R)`, `SMP(L)`, `SMP(R)`
- `CRE(L)`, `CRE(R)`, `LAL(L)`, `LAL(R)`
- Any other non-optic neuropils

## Before vs After

### Before (Individual Listing):
```
Layer-Based ROI Analysis:
├── ME_R_layer_1: 150 synapses
├── LO_L_layer_2: 89 synapses
├── PVLP: 45 synapses
├── FB(L): 23 synapses
├── FB(R): 31 synapses
├── PB: 12 synapses
├── NO(L): 8 synapses
└── SMP(R): 5 synapses
```

### After (Consolidated):
```
Layer-Based ROI Analysis:
├── ME_R_layer_1: 150 synapses
├── LO_L_layer_2: 89 synapses
└── central brain: 124 synapses
    (consolidates PVLP + FB(L) + FB(R) + PB + NO(L) + SMP(R))
```

## Implementation Details

The consolidation uses the optic-lobe dataset's ROI strategy to:

1. **Identify all central brain ROIs** using `adapter.query_central_brain_rois()`
2. **Sum synapses across all central brain regions**
3. **Create single "central brain" entry** with combined totals
4. **Exclude individual central brain ROIs** from the table

## Benefits

1. **Cleaner Display**: Reduces table clutter by grouping related regions
2. **Dataset-Specific Logic**: Uses proper optic-lobe central brain definition
3. **Preserved Detail**: Layer/column analysis remains granular
4. **Consistent Totals**: All synapses still accounted for, just grouped logically

## Code Location

- **Main logic**: `src/quickpage/page_generator.py` in `_analyze_layer_roi_data()`
- **ROI strategy**: `src/quickpage/dataset_adapters.py` in `OpticLobeRoiQueryStrategy`
- **Template display**: `templates/neuron_page.html` in Layer-Based ROI Analysis section

## Testing

Use `test_central_brain_consolidation.py` to verify:
- Central brain ROIs are properly identified
- Synapses are correctly summed
- Individual central brain entries are excluded
- Final HTML shows consolidated "central brain" entry

## Example Output

For LPLC2 neurons in optic-lobe dataset:

| Region | Soma Side | Layer | Pre-synapses | Post-synapses | Total |
|--------|-----------|-------|--------------|---------------|-------|
| ME | R | 1 | 234 | 12 | 246 |
| ME | R | 2 | 189 | 8 | 197 |
| LO | L | 3 | 145 | 23 | 168 |
| central brain | Both | — | 456 | 89 | 545 |

The "central brain" row represents the sum of all PVLP, FB, PB, EB, NO, SMP, CRE and other non-optic neuropil synapses.