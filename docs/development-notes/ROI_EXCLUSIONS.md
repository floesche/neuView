# ROI Exclusions from Innervation Tables

## Overview

Specific ROIs are excluded from the ROI Innervation tables to improve clarity and focus on meaningful ROI regions. These exclusions remove overly broad or redundant ROI categories that don't provide useful analysis granularity.

## Dataset-Specific Exclusions

### Optic-Lobe Dataset

**Excluded ROIs:**
- `OL(R)` - Right Optic Lobe
- `OL(L)` - Left Optic Lobe

**Reason for Exclusion:**
- These are overly broad parent regions that encompass many specific ROIs
- More specific regions (ME, LO, LOP, AME, LA) provide better analysis granularity
- Avoiding redundant information in the innervation table

**Retained ROIs:**
- `ME(R)`, `ME(L)` - Medulla regions
- `LO(R)`, `LO(L)` - Lobula regions  
- `LOP(R)`, `LOP(L)` - Lobula plate regions
- `AME(R)`, `AME(L)` - Accessory medulla regions
- `LA(R)`, `LA(L)` - Lamina regions
- Central brain regions (FB, PB, EB, NO, SMP, etc.)

### CNS Dataset

**Excluded ROIs:**
- `Optic(R)` - Right Optic region
- `Optic(L)` - Left Optic region

**Reason for Exclusion:**
- These are broad parent categories that encompass visual system components
- More specific visual ROIs (ME, LO) provide better analysis detail
- Reduces clutter in the innervation analysis

**Retained ROIs:**
- `ME(R)`, `ME(L)` - Medulla regions
- `LO(R)`, `LO(L)` - Lobula regions
- `AL(R)`, `AL(L)` - Antennal lobe regions
- `MB(R)`, `MB(L)` - Mushroom body regions
- `CX`, `PB`, `FB`, `EB` - Central complex components

### Hemibrain Dataset

**No specific exclusions currently implemented.**

All primary ROIs are included in the innervation table for hemibrain dataset analysis.

## Implementation Details

### Dataset Adapter Level

ROI exclusions are implemented in the dataset-specific ROI strategies:

```python
class CNSRoiQueryStrategy(RoiQueryStrategy):
    def get_primary_rois(self, all_rois: List[str]) -> List[str]:
        excluded_rois = {'Optic(R)', 'Optic(L)'}  # Exclude these from CNS ROI table
        
        primary_rois = []
        for roi in all_rois:
            if roi in excluded_rois:
                continue
            # ... rest of filtering logic

class OpticLobeRoiQueryStrategy(RoiQueryStrategy):
    def get_primary_rois(self, all_rois: List[str]) -> List[str]:
        excluded_rois = {'OL(R)', 'OL(L)'}  # Exclude these from optic-lobe ROI table
        
        primary_rois = []
        for roi in all_rois:
            if roi in excluded_rois:
                continue
            # ... rest of filtering logic
```

### Page Generator Level

ROI exclusions are also enforced in the page generator's primary ROI detection:

```python
def _get_primary_rois(self, connector):
    # Dataset-specific primary ROIs
    if 'optic' in dataset_name:
        optic_primary = {
            'ME(R)', 'ME(L)', 'LO(R)', 'LO(L)',  # OL(R), OL(L) removed
            'LOP(R)', 'LOP(L)', 'AME(R)', 'AME(L)', 'LA(R)', 'LA(L)'
        }
    elif 'cns' in dataset_name:
        cns_primary = {
            'ME(R)', 'ME(L)', 'LO(R)', 'LO(L)',  # Optic(R), Optic(L) removed
            'AL(R)', 'AL(L)', 'MB(R)', 'MB(L)', 'CX', 'PB', 'FB', 'EB'
        }
```

## Impact on Analysis

### Before Exclusions

ROI Innervation table for optic-lobe dataset might show:
```
| ROI | Pre-synapses | Post-synapses | Total |
|-----|--------------|---------------|-------|
| OL(R) | 1250 | 890 | 2140 |
| ME(R) | 450 | 230 | 680 |
| LO(R) | 380 | 195 | 575 |
| LOP(R) | 320 | 165 | 485 |
```

### After Exclusions

ROI Innervation table for optic-lobe dataset shows:
```
| ROI | Pre-synapses | Post-synapses | Total |
|-----|--------------|---------------|-------|
| ME(R) | 450 | 230 | 680 |
| LO(R) | 380 | 195 | 575 |
| LOP(R) | 320 | 165 | 485 |
| AME(R) | 180 | 95 | 275 |
| LA(R) | 120 | 60 | 180 |
```

## Benefits

1. **Improved Clarity**: Removes redundant parent region information
2. **Better Granularity**: Focuses on specific ROI regions for analysis
3. **Reduced Clutter**: Cleaner innervation tables with relevant information
4. **Consistent Analysis**: Standardized approach across datasets
5. **Meaningful Comparisons**: Facilitates comparison of specific ROI innervation

## Testing

Use `test_roi_exclusions.py` to verify:
- ✅ Excluded ROIs don't appear in primary ROI lists
- ✅ Excluded ROIs don't appear in ROI innervation tables
- ✅ Expected ROIs are still included
- ✅ Dataset adapters properly filter ROIs
- ✅ Page generator respects exclusions

## Configuration

ROI exclusions are currently hardcoded in the dataset adapters and page generator. Future enhancements could include:

- Configuration file-based exclusions
- User-customizable ROI filtering
- Dynamic exclusion rules based on analysis context

## Migration Notes

### Existing Behavior
- All primary ROIs (including broad parent regions) were shown
- ROI innervation tables included redundant information
- Analysis could be cluttered with overly broad categories

### New Behavior
- Dataset-specific ROI exclusions applied
- Cleaner, more focused innervation tables
- Better analysis granularity and clarity
- Consistent approach across different datasets