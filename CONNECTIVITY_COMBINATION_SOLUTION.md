# Connectivity Combination Solution

## Overview

This document describes the implementation of connectivity table combination for combined pages in the QuickPage system. The solution addresses the requirement to combine L/R connectivity entries in combined pages while preserving separate entries for individual side pages.

## Problem Statement

**Original Issue**: On combined pages (e.g., TM3.html), the connectivity table showed separate entries for left and right soma sides:
- `L1 (R)` - 300 connections
- `L1 (L)` - 245 connections

**Requirement**: For combined pages, these should be merged into a single entry:
- `L1` - 545 connections (combined from both sides)

**Additional Requirements**:
1. Individual side pages (L, R, M) should remain unchanged
2. When the combined entry checkbox is selected, neurons from both sides should be added to neuroglancer
3. Weights, connections, and percentages should be properly aggregated
4. Most common neurotransmitter should be preserved

## Solution Architecture

The solution consists of three main components:

### 1. ConnectivityCombinationService
**File**: `src/quickpage/services/connectivity_combination_service.py`

Core service responsible for:
- Processing connectivity data based on soma side
- Combining L/R entries for the same partner type
- Recalculating percentages after combination
- Retrieving combined body IDs for neuroglancer integration

### 2. Enhanced PartnerAnalysisService
**File**: `src/quickpage/services/partner_analysis_service.py`

Updated to:
- Detect combined entries (empty `soma_side`)
- Delegate body ID retrieval to connectivity combination service
- Maintain backward compatibility with existing functionality

### 3. Enhanced TemplateContextService
**File**: `src/quickpage/services/template_context_service.py`

Modified to:
- Process connectivity data using the combination service
- Apply combination logic only for combined pages (`soma_side="combined"`)
- Pass processed connectivity data to templates

## Implementation Details

### Data Processing Flow

```
Original Database Data → ConnectivityCombinationService → Template Display
```

1. **Input**: Raw connectivity data from NeuPrint connector
2. **Processing**: Combination service processes data based on `soma_side`
3. **Output**: Modified connectivity data for template rendering

### Combination Logic

For each direction (upstream/downstream):

1. **Group by Partner Type**: Group all partners by their `type` field
2. **Merge Groups**: For each partner type:
   - Single entry: Remove soma side label for display
   - Multiple entries: Combine weights, connections, and select most common neurotransmitter
3. **Recalculate Percentages**: Update percentages based on new combined totals
4. **Sort by Weight**: Maintain descending weight order

### Body ID Retrieval

When a combined entry checkbox is selected:

1. **Detect Combined Entry**: Check if `soma_side` is empty
2. **Collect from Both Sides**: Retrieve body IDs from both `{type}_L` and `{type}_R` keys
3. **Deduplicate**: Remove duplicates while preserving order
4. **Return Combined List**: Include neurons from all relevant sides

## Code Examples

### Basic Usage

```python
from quickpage.services.connectivity_combination_service import ConnectivityCombinationService

service = ConnectivityCombinationService()

# Process for combined page
combined_data = service.process_connectivity_for_display(
    connectivity_data, 
    soma_side="combined"
)

# Process for individual side page (unchanged)
left_data = service.process_connectivity_for_display(
    connectivity_data, 
    soma_side="left"
)
```

### Body ID Retrieval

```python
# Combined entry (from template)
partner_data = {"type": "L1", "soma_side": ""}

# Get body IDs for neuroglancer
body_ids = service.get_combined_body_ids(
    partner_data, 
    "upstream", 
    connected_bids
)
# Returns: [L1_L_neurons] + [L1_R_neurons]
```

## Before/After Comparison

### TM3 Combined Page Example

**Before**:
```
Upstream Partners:
1. L1 (R) - 300 connections (55.0%)
2. L1 (L) - 245 connections (45.0%)
3. Tm9 (L) - 180 connections (100.0%)
4. Mi1 (R) - 120 connections (100.0%)
```

**After**:
```
Upstream Partners:
1. L1 - 545 connections (64.5%)
2. Tm9 - 180 connections (21.3%)  
3. Mi1 - 120 connections (14.2%)
```

### Individual Side Pages

Individual side pages (TM3_L.html, TM3_R.html) remain **completely unchanged**.

## Service Integration

### Service Factory Updates

Both `PageGeneratorServiceFactory` and `PageGenerationContainer` have been updated to:

1. Create `ConnectivityCombinationService` instance
2. Pass it to `PartnerAnalysisService` constructor
3. Register the service in the dependency injection container

### Template Context Integration

The `TemplateContextService` automatically:

1. Detects the target `soma_side` from the page generation request
2. Applies combination logic for `soma_side="combined"`
3. Passes through unchanged data for individual sides
4. Provides processed connectivity data to templates

## Testing

### Test Coverage

The solution includes comprehensive tests:

1. **Basic Combination**: Tests L/R entry merging
2. **Individual Side Passthrough**: Ensures unchanged behavior for side pages
3. **Body ID Retrieval**: Tests combined neuroglancer integration
4. **Percentage Recalculation**: Verifies correct percentage updates
5. **Edge Cases**: Handles empty data, missing partners, etc.

### Test Files

- `test_connectivity_minimal.py`: Core combination logic tests
- `test_body_id_combination.py`: Body ID retrieval tests  
- `demo_connectivity_combination.py`: End-to-end demonstration

### Running Tests

```bash
cd quickpage
python test_connectivity_minimal.py
python test_body_id_combination.py
python demo_connectivity_combination.py
```

## Performance Considerations

### Minimal Overhead

- Processing only occurs for combined pages
- Individual side pages have zero performance impact
- Combination logic is O(n) where n is number of partners
- Body ID retrieval uses efficient dictionary lookups

### Memory Usage

- Creates new data structures only for combined pages
- Original data preserved for individual side pages
- Minimal memory overhead for duplicate removal

## Backward Compatibility

### Guaranteed Compatibility

✅ **Individual Side Pages**: Completely unchanged behavior  
✅ **Existing Templates**: No template modifications required  
✅ **Database Queries**: No changes to connectivity data retrieval  
✅ **Neuroglancer Integration**: Enhanced but backward compatible  
✅ **API Interfaces**: All existing interfaces preserved  

### Migration Notes

- No migration required
- Solution is additive, not modifying existing functionality
- Can be safely deployed without affecting existing pages

## Configuration

### Default Behavior

- **Combined Pages** (`soma_side="combined"`): Automatic L/R combination
- **Individual Pages** (`soma_side="left|right|middle"`): Original behavior
- **No Configuration Required**: Works automatically based on page type

### Customization Options

The `ConnectivityCombinationService` can be customized for:

- Different combination strategies
- Custom neurotransmitter selection logic
- Alternative percentage calculation methods
- Specialized body ID retrieval patterns

## Troubleshooting

### Common Issues

**Issue**: Combined entries not showing combined data
- **Check**: Verify `soma_side="combined"` is passed to service
- **Solution**: Ensure page generation uses correct soma side parameter

**Issue**: Body IDs not including both sides
- **Check**: Verify partner entry has empty `soma_side` field
- **Solution**: Ensure combination service properly processes partner data

**Issue**: Percentages don't sum to 100%
- **Check**: Verify `_recalculate_percentages` is called after combination
- **Solution**: Check combination logic includes percentage recalculation

### Debug Information

Enable debug logging to trace combination process:

```python
import logging
logging.getLogger('quickpage.services.connectivity_combination_service').setLevel(logging.DEBUG)
```

## Future Enhancements

### Potential Improvements

1. **Configurable Combination Rules**: Allow custom rules for which sides to combine
2. **Statistical Aggregation Options**: Support for median, mode, or other aggregation methods
3. **Performance Optimization**: Caching for frequently accessed combinations
4. **Extended Soma Side Support**: Handle additional soma side types beyond L/R

### Extension Points

The solution is designed for extensibility:

- `ConnectivityCombinationService` can be subclassed for custom behavior
- Processing pipeline allows additional transformation steps
- Body ID retrieval supports custom side mapping strategies

## Implementation Timeline

- ✅ **Phase 1**: Core combination logic implemented
- ✅ **Phase 2**: Service integration completed  
- ✅ **Phase 3**: Body ID retrieval functionality added
- ✅ **Phase 4**: Comprehensive testing completed
- ✅ **Phase 5**: Documentation and examples created

## Summary

This solution successfully addresses the connectivity combination requirements by:

1. **Combining L/R entries** in combined pages while preserving individual side behavior
2. **Maintaining full backward compatibility** with existing functionality
3. **Providing seamless neuroglancer integration** with combined body ID retrieval
4. **Including comprehensive testing** to ensure reliability
5. **Delivering production-ready code** with proper error handling and documentation

The implementation is minimal, efficient, and ready for immediate deployment in the QuickPage system.