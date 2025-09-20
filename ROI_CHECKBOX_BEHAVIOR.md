# ROI Checkbox Behavior in QuickPage

## Overview

ROI (Region of Interest) checkboxes in the ROI Innervation table allow users to toggle visualization of specific brain regions in the Neuroglancer viewer. However, checkbox availability depends on the dataset being used.

## Dataset-Specific Behavior

### FAFB Dataset (flywire-fafb:v783b)

**Checkbox Status**: ❌ **Not Available**

- ROI checkboxes are **not displayed** in the ROI Innervation table
- This is intentional - FAFB neuroglancer data lacks reliable ROI visualization support
- ROI names and statistics are still shown in the table for reference
- Table layout and formatting remain consistent

**Why No Checkboxes for FAFB?**
- The underlying neuroglancer template for FAFB does not contain correct ROI mesh/annotation data
- Clicking checkboxes would have no visual effect in the neuroglancer viewer
- Removing checkboxes prevents user confusion and false expectations

### CNS, Hemibrain, and Optic-Lobe Datasets

**Checkbox Status**: ✅ **Fully Functional**

- ROI checkboxes are displayed for all ROIs in the innervation table
- Clicking checkboxes toggles ROI visibility in the neuroglancer viewer
- Visual feedback shows selected/deselected state
- ROI regions are properly highlighted in the 3D visualization

## User Experience

### What Users See

#### FAFB Dataset
```
ROI Innervation (15 ROIs)
┌─────────────────┬──────────┬─────────┬─────────┐
│ ROI Name        │ ∑ In     │ % In    │ % Out   │
├─────────────────┼──────────┼─────────┼─────────┤
│ GNG             │ 1,234    │ 15.2%   │ 8.7%    │
│ SEZ             │ 2,567    │ 31.1%   │ 22.4%   │
│ ...             │ ...      │ ...     │ ...     │
└─────────────────┴──────────┴─────────┴─────────┘
```
*Note: No checkboxes present - clean table layout*

#### CNS/Hemibrain/Optic-Lobe Datasets
```
ROI Innervation (15 ROIs)
┌───┬─────────────────┬──────────┬─────────┬─────────┐
│ ☑ │ ROI Name        │ ∑ In     │ % In    │ % Out   │
├───┼─────────────────┼──────────┼─────────┼─────────┤
│ ☐ │ AL(R)           │ 1,234    │ 15.2%   │ 8.7%    │
│ ☑ │ AVLP(R)         │ 2,567    │ 31.1%   │ 22.4%   │
│ ☐ │ ...             │ ...      │ ...     │ ...     │
└───┴─────────────────┴──────────┴─────────┴─────────┘
```
*Note: Checkboxes allow ROI visualization control*

### Interactive Behavior

#### For Datasets with Checkboxes (CNS, Hemibrain, Optic-Lobe)

1. **Click to Toggle**: Click any ROI checkbox to show/hide that region in neuroglancer
2. **Visual Feedback**: Checked boxes (☑) show active ROIs, unchecked (☐) show inactive ones
3. **Real-time Updates**: Neuroglancer viewer updates immediately when checkboxes change
4. **Multi-selection**: Multiple ROIs can be selected simultaneously
5. **Persistent State**: ROI selections are maintained during navigation

#### For FAFB Dataset

1. **View Only**: ROI table provides statistical information without interaction
2. **Navigation**: Use other navigation methods (coordinates, neuron selection)
3. **Data Analysis**: ROI statistics remain accurate and useful for analysis
4. **No False Promises**: Interface clearly indicates ROI visualization is not available

## Technical Details

### How Dataset Detection Works

The system automatically detects dataset type using:

1. **Template-based Detection**: Dataset name passed from server configuration
2. **Layer-based Detection**: Neuroglancer layer inspection (fallback method)
3. **Runtime Adaptation**: JavaScript conditionally creates checkboxes based on detection

### Dataset Identification

- **FAFB Detection**: Dataset name contains "fafb" OR neuroglancer layers contain "flywire-fafb:v783b"
- **Other Datasets**: All other datasets assume ROI visualization capability

## Troubleshooting

### Expected Behavior Not Observed

**Problem**: ROI checkboxes appear for FAFB dataset
- **Check**: Verify dataset configuration shows "flywire-fafb:v783b"
- **Solution**: Clear browser cache and reload the page
- **Contact**: Report as potential configuration issue

**Problem**: ROI checkboxes missing for CNS/Hemibrain datasets
- **Check**: Verify dataset name doesn't contain "fafb"
- **Solution**: Check neuroglancer template contains proper ROI layers
- **Contact**: Report as potential template issue

**Problem**: ROI checkboxes present but not functional
- **Check**: Verify neuroglancer viewer loads properly
- **Solution**: Check browser console for JavaScript errors
- **Contact**: Report as potential neuroglancer integration issue

### Browser Compatibility

- **Supported**: All modern browsers (Chrome, Firefox, Safari, Edge)
- **Required**: JavaScript enabled
- **Recommended**: Latest browser version for optimal performance

## Developer Notes

### Customization

To modify ROI checkbox behavior:

1. **Dataset Detection**: Update detection logic in `neuroglancer-url-generator.js`
2. **Conditional Logic**: Modify `syncRoiCheckboxes()` function
3. **Styling**: Update ROI-related CSS classes for visual customization

### Adding New Datasets

When adding datasets:

1. **With ROI Support**: No changes needed - checkboxes will appear automatically
2. **Without ROI Support**: Add dataset detection to disable checkboxes
3. **Testing**: Verify checkbox behavior matches ROI data availability

## Summary

ROI checkboxes provide an intuitive way to explore brain regions in supported datasets, while FAFB users receive a clean interface that doesn't promise functionality that cannot be delivered. This approach ensures consistent user experience across all dataset types while maintaining the scientific accuracy and utility of the ROI innervation data.