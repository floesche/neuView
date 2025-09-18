# FafbAdapter Soma Side Extraction Fixes

## Problem Summary

The FafbAdapter was not correctly extracting soma side information from FAFB (FlyWire) dataset neurons. This was causing issues with soma side filtering and analysis for the flywire-fafb dataset.

## Root Causes Identified

### 1. **Incorrect Factory Mapping (Primary Issue)**
The `DatasetAdapterFactory` was configured to return an `OpticLobeAdapter` instead of `FafbAdapter` for the "flywire-fafb" dataset:

```python
# BEFORE (incorrect):
"flywire-fafb": OpticLobeAdapter,

# AFTER (fixed):
"flywire-fafb": FafbAdapter,
```

This meant that the `FafbAdapter` class existed but was never actually used, so any improvements to its soma side extraction logic would have no effect.

### 2. **Incomplete Soma Side Extraction Logic**
The original `FafbAdapter.extract_soma_side()` method was overly simplistic:

**Problems:**
- Only looked for a "side" column (which may not exist in FAFB data)
- No regex pattern for extracting from instance names
- No fallback mechanism when the "side" column was missing
- Lacked the sophisticated extraction logic used by other adapters

### 3. **Missing Regex Configuration**
The `FafbAdapter` was not configured with a `soma_side_extraction` regex pattern in its `DatasetInfo`, unlike the `OpticLobeAdapter` which had a comprehensive pattern.

## Solutions Implemented

### 1. Fixed Factory Mapping
Updated `DatasetAdapterFactory` to correctly map "flywire-fafb" to `FafbAdapter`:

```python
_adapters: Dict[str, Type[DatasetAdapter]] = {
    "cns": CNSAdapter,
    "hemibrain": HemibrainAdapter,
    "optic-lobe": OpticLobeAdapter,
    "flywire-fafb": FafbAdapter,  # ✅ Now correctly uses FafbAdapter
}
```

### 2. Added Regex Pattern Configuration
Added sophisticated regex pattern to `FafbAdapter`'s `DatasetInfo`:

```python
dataset_info = DatasetInfo(
    name="flywire-fafb",
    soma_side_extraction=r"(?:_|-|\()([LRMlrm])(?:_|\)|$|[^a-zA-Z])",  # ✅ Added regex pattern
    pre_synapse_column="pre",
    post_synapse_column="post",
    roi_columns=["inputRois", "outputRois"],
)
```

This regex pattern extracts L/R/M (left/right/middle) from various instance name formats:
- `LC4_L` (underscore pattern)
- `LPLC2_R_001` (underscore with additional text)
- `VES022(L)` (parentheses pattern)  
- `VES023-R` (dash pattern)
- `T4_m_medulla` (lowercase, gets converted to uppercase)

### 3. Enhanced Extraction Logic
Completely rewrote the `extract_soma_side()` method with a robust priority system:

```python
def extract_soma_side(self, neurons_df: pd.DataFrame) -> pd.DataFrame:
    """Extract soma side from instance names using regex."""
    neurons_df = neurons_df.copy()

    # Priority 1: Existing somaSide column
    if "somaSide" in neurons_df.columns:
        neurons_df["somaSide"] = neurons_df["somaSide"].fillna("U")
        return neurons_df

    # Priority 2: FAFB-specific "side" column
    if "side" in neurons_df.columns:
        neurons_df["somaSide"] = neurons_df["side"].str.upper().fillna("U")
        return neurons_df

    # Priority 3: Extract from instance names using regex
    if "instance" in neurons_df.columns and self.dataset_info.soma_side_extraction:
        pattern = self.dataset_info.soma_side_extraction
        extracted = neurons_df["instance"].str.extract(pattern, expand=False)
        neurons_df["somaSide"] = extracted.str.upper().fillna("U")
    else:
        neurons_df["somaSide"] = "U"

    return neurons_df
```

## Features of the Fix

### ✅ **Multi-Pattern Support**
Handles various instance naming conventions:
- Underscore patterns: `LC4_L`, `LPLC2_R_001`
- Parentheses patterns: `VES022(L)`, `VES023(R)`
- Dash patterns: `VES022-L`, `VES023-R`
- Complex patterns: `T4_L_medulla`, `complex(R)_name`

### ✅ **Case Insensitive with Normalization**
- Accepts both uppercase and lowercase side indicators (`L`, `l`, `R`, `r`, `M`, `m`)
- Always converts to uppercase for consistency

### ✅ **Priority-Based Column Handling**
1. **Existing `somaSide` column** - preserves existing data, fills NaN with "U"
2. **FAFB-specific `side` column** - converts to uppercase, fills NaN with "U"  
3. **Instance name extraction** - uses regex pattern to extract from names
4. **Fallback** - marks all as "U" (unknown) if no extraction possible

### ✅ **Robust Error Handling**
- Handles missing columns gracefully
- Fills NaN/None values with "U" (unknown)
- Works with empty DataFrames
- Never fails due to missing data

## Verification

The fix has been verified with comprehensive tests covering:

- ✅ Factory correctly returns `FafbAdapter` for "flywire-fafb"
- ✅ Regex pattern correctly configured
- ✅ Extraction works for all supported patterns
- ✅ Priority system works correctly (somaSide > side > instance extraction)
- ✅ NaN/None values properly handled
- ✅ Case insensitive extraction with uppercase normalization
- ✅ Fallback behavior for missing data

## Impact

This fix ensures that:

1. **FAFB neurons can be properly filtered by soma side** (left/right/middle)
2. **The system uses the correct adapter** for flywire-fafb datasets
3. **Soma side extraction is robust and comprehensive** for various naming conventions
4. **Data integrity is maintained** with proper fallback handling

The fix maintains backward compatibility and doesn't break any existing functionality for other dataset adapters.