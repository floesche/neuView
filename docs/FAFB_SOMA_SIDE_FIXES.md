# FAFB Soma Side Display Fixes

## Problem Summary

Two issues were identified with FAFB (FlyWire) dataset handling:

1. **Missing R/C/L navigation buttons in hamburger menu**: FAFB neuron pages were missing the right (R), center (C), and left (L) navigation buttons that allow users to switch between different soma sides of the same neuron type.

2. **Missing soma side information in connectivity tables**: FAFB partner neurons in the connectivity tables were not displaying their soma side information (e.g., "(L)" for left, "(C)" for center), while this information was properly displayed for CNS dataset partners.

3. **Unknown soma side warnings**: The system was generating warnings like "Unknown soma side: center" because FAFB uses "center" instead of "middle" for the combined view.

## Root Cause Analysis

The issues were caused by differences in how FAFB stores soma side information in the neuPrint database compared to other datasets:

### Standard Datasets (CNS, Hemibrain)
- Store soma side information in the `somaSide` property
- Use single-letter codes: "L", "R", "M" (left, right, middle)

### FAFB Dataset  
- May store soma side information in the `side` property instead of `somaSide`
- May use full words: "LEFT", "RIGHT", "CENTER" or mixed case variants
- Some neurons might have `somaSide` while others have `side`
- Uses "CENTER" instead of "MIDDLE" for the combined view

## Solutions Implemented

### 1. Fixed Soma Side Navigation Buttons (`NeuronSelectionService`)

**File**: `quickpage/src/quickpage/services/neuron_selection_service.py`

**Changes**: Modified the `get_available_soma_sides()` method to handle FAFB-specific properties:

```python
# Handle FAFB-specific property names
if connector.dataset_adapter.dataset_info.name == "flywire-fafb":
    # FAFB might use 'side' property instead of 'somaSide'
    query = f"""
        MATCH (n:Neuron)
        WHERE n.type = "{neuron_type}" AND (n.somaSide IS NOT NULL OR n.side IS NOT NULL)
        RETURN DISTINCT
            CASE
                WHEN n.somaSide IS NOT NULL THEN n.somaSide
                WHEN n.side IS NOT NULL THEN
                    CASE n.side
                        WHEN 'LEFT' THEN 'L'
                        WHEN 'RIGHT' THEN 'R'
                        WHEN 'CENTER' THEN 'C'
                        WHEN 'MIDDLE' THEN 'C'
                        WHEN 'left' THEN 'L'
                        WHEN 'right' THEN 'R'
                        WHEN 'center' THEN 'C'
                        WHEN 'middle' THEN 'C'
                        ELSE n.side
                    END
                ELSE NULL
            END as somaSide
        ORDER BY somaSide
        """
```

**Features**:
- ✅ Checks both `somaSide` and `side` properties
- ✅ Converts full words ("LEFT", "RIGHT", "CENTER") to single letters ("L", "R", "C")
- ✅ Handles legacy "MIDDLE" mapping to "C" for backward compatibility
- ✅ Handles case variations (both uppercase and lowercase)
- ✅ Maintains backward compatibility with standard datasets

### 2. Fixed Connectivity Partner Soma Side Display (`NeuPrintConnector`)

**File**: `quickpage/src/quickpage/neuprint_connector.py`

**Changes**: Updated both upstream and downstream connectivity queries to handle FAFB-specific soma side properties:

#### Upstream Partners Query
```python
if self.dataset_adapter.dataset_info.name == "flywire-fafb":
    upstream_query = f"""
        MATCH (upstream:Neuron)-[c:ConnectsTo]->(target:Neuron)
        WHERE target.bodyId IN {body_ids}
        RETURN upstream.type as partner_type,
                CASE
                    WHEN upstream.somaSide IS NOT NULL THEN upstream.somaSide
                    WHEN upstream.side IS NOT NULL THEN
                        CASE upstream.side
                            WHEN 'LEFT' THEN 'L'
                            WHEN 'RIGHT' THEN 'R'
                            WHEN 'CENTER' THEN 'C'
                            WHEN 'MIDDLE' THEN 'C'
                            WHEN 'left' THEN 'L'
                            WHEN 'right' THEN 'R'
                            WHEN 'center' THEN 'C'
                            WHEN 'middle' THEN 'C'
                            ELSE upstream.side
                        END
                    ELSE ''
                END as soma_side,
               -- ... rest of query
        """
```

#### Downstream Partners Query
Similar logic applied to downstream partner queries with the same case handling and property fallback mechanism.

**Features**:
- ✅ Handles both `somaSide` and `side` properties for partner neurons
- ✅ Converts FAFB full-word format to standard single-letter format
- ✅ Maps FAFB "CENTER" to "C" and legacy "MIDDLE" to "C"
- ✅ Case-insensitive conversion
- ✅ Graceful fallback to empty string if no soma side information available

### 3. Enhanced DatabaseQueryService (Future-Proofing)

**File**: `quickpage/src/quickpage/services/database_query_service.py`

**Changes**: Updated the `get_partner_body_ids()` method with the same FAFB-specific logic to ensure consistency across all database query services.

**Features**:
- ✅ Consistent handling across all query services
- ✅ Same property fallback and case conversion logic
- ✅ Maintains system-wide consistency

### 4. Fixed Partner Analysis Service (Eliminated Warnings)

**File**: `quickpage/src/quickpage/services/partner_analysis_service.py`

**Changes**: Updated `get_partner_body_ids()` to recognize "C" and "center" as valid soma sides to eliminate "Unknown soma side: center" warnings.

**Features**:
- ✅ Recognizes both "C" and "center" as valid FAFB soma sides
- ✅ Eliminates warning messages about unknown soma sides
- ✅ Handles partner connectivity data correctly for FAFB center neurons

### 5. Enhanced HTML Link Generation

**File**: `quickpage/src/quickpage/utils/html_utils.py`

**Changes**: Updated `create_neuron_link()` to properly display and link FAFB center neurons.

**Features**:
- ✅ Displays FAFB center partners as "(C)" in connectivity tables
- ✅ Links FAFB center partners to combined pages (no suffix)
- ✅ Maintains consistent display formatting across datasets

### 6. Updated File Service

**File**: `quickpage/src/quickpage/services/file_service.py`

**Changes**: Enhanced `generate_filename()` to handle FAFB center side mapping to combined pages.

**Features**:
- ✅ Maps FAFB "center" to combined page filenames (no suffix)
- ✅ Consistent filename generation across all services
- ✅ Proper handling of FAFB-specific soma side conventions

## Technical Implementation Details

### Query Strategy
The solution uses a **fallback hierarchy** in Cypher queries:

1. **Primary**: Check for `somaSide` property (standard)
2. **Secondary**: Check for `side` property (FAFB-specific)  
3. **Conversion**: Map full words to single letters
4. **Fallback**: Use empty string or NULL if no soma side data

### Case Handling
```cypher
CASE n.side
    WHEN 'LEFT' THEN 'L'
    WHEN 'RIGHT' THEN 'R' 
    WHEN 'CENTER' THEN 'C'
    WHEN 'MIDDLE' THEN 'C'
    WHEN 'left' THEN 'L'
    WHEN 'right' THEN 'R'
    WHEN 'center' THEN 'C'
    WHEN 'middle' THEN 'C'
    ELSE n.side
END
```

### Dataset Detection
```python
if connector.dataset_adapter.dataset_info.name == "flywire-fafb":
    # Use FAFB-specific query
else:
    # Use standard query
```

## Impact and Results

### ✅ R/C/L Navigation Buttons Now Available for FAFB
- FAFB neuron pages now show the hamburger menu with R/C/L buttons
- Users can navigate between left, right, and combined views of FAFB neurons
- Consistent navigation experience across all datasets

### ✅ Connectivity Tables Show Partner Soma Sides
- FAFB partner neurons in connectivity tables now display soma side information: "Partner (L)", "Partner (R)", "Partner (C)", etc.
- FAFB center partners display as "(C)" and link to combined pages
- Consistent with CNS dataset partner display
- Enhanced usability for analyzing lateralized connectivity patterns

### ✅ Eliminated Warning Messages
- No more "Unknown soma side: center" warnings in logs
- System properly recognizes FAFB "center" as a valid soma side
- Clean log output during FAFB data processing

### ✅ Backward Compatibility Maintained
- No impact on existing CNS, Hemibrain, or Optic Lobe datasets
- Standard datasets continue to work exactly as before
- Clean separation of dataset-specific logic

### ✅ Robust Error Handling
- Graceful handling of missing properties
- No crashes when soma side information is unavailable
- Fallback behavior preserves system stability

## Verification

The fixes can be verified by:

1. **Navigation Test**: Visit a FAFB neuron page and check that R/C/L buttons appear in the hamburger menu
2. **Connectivity Test**: Check that FAFB partners in connectivity tables show soma side labels
3. **Cross-Dataset Test**: Ensure CNS and other datasets still work correctly
4. **Edge Case Test**: Test with neurons that have missing or unusual soma side data

## Future Considerations

1. **Database Schema**: If FAFB standardizes on `somaSide` property, the FAFB-specific logic can be simplified
2. **Performance**: The CASE statements add minimal overhead but could be optimized if needed
3. **Extensibility**: The pattern can be extended to other FAFB-specific property differences

## Files Modified

- `quickpage/src/quickpage/services/neuron_selection_service.py` - Navigation button queries
- `quickpage/src/quickpage/neuprint_connector.py` - Connectivity partner queries
- `quickpage/src/quickpage/services/database_query_service.py` - Consistency across query services
- `quickpage/src/quickpage/services/partner_analysis_service.py` - Eliminated warnings
- `quickpage/src/quickpage/utils/html_utils.py` - Link generation and display
- `quickpage/src/quickpage/services/file_service.py` - Filename generation
- `quickpage/src/quickpage/dataset_adapters.py` - FAFB adapter center mapping
- `quickpage/docs/FAFB_SOMA_SIDE_FIXES.md` (this documentation)