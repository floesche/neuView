"""
Example usage of ROI query strategies for different datasets.

This demonstrates how to use the new ROI query architecture to handle
dataset-specific ROI definitions and queries.
"""

from src.quickpage.dataset_adapters import (
    DatasetAdapterFactory,
    CNSRoiQueryStrategy,
    OpticLobeRoiQueryStrategy,
    HemibrainRoiQueryStrategy
)


def example_optic_lobe_roi_queries():
    """Demonstrate ROI queries for optic-lobe dataset."""
    print("=== Optic Lobe ROI Query Examples ===\n")

    # Get the adapter for optic-lobe dataset
    adapter = DatasetAdapterFactory.create_adapter('optic-lobe')

    # Sample ROI list that might come from NeuPrint
    sample_rois = [
        'ME(R)', 'ME(L)', 'LO(R)', 'LO(L)', 'LOP(R)', 'LOP(L)',
        'AME(R)', 'AME(L)', 'LA(R)', 'LA(L)',
        'ME_R_layer_1', 'ME_R_layer_2', 'ME_L_layer_1', 'ME_L_layer_2',
        'LO_R_layer_3', 'LO_L_layer_3',
        'ME_R_col_A1_T1', 'ME_L_col_B2_T3', 'LO_R_col_C1_T2',
        'FB(R)', 'FB(L)', 'PB', 'EB', 'NO(R)', 'NO(L)',
        'SMP(R)', 'SMP(L)', 'CRE(R)', 'CRE(L)',
        'some_other_region'
    ]

    # Query central brain ROIs (everything NOT optic system)
    central_brain = adapter.query_central_brain_rois(sample_rois)
    print("Central Brain ROIs:")
    for roi in sorted(central_brain):
        print(f"  - {roi}")
    print()

    # Query primary ROIs
    primary_rois = adapter.query_primary_rois(sample_rois)
    print("Primary ROIs:")
    for roi in sorted(primary_rois):
        print(f"  - {roi}")
    print()

    # Categorize all ROIs
    categories = adapter.categorize_rois(sample_rois)
    print("ROI Categories:")
    for category, rois in categories.items():
        if rois:  # Only show non-empty categories
            print(f"  {category}:")
            for roi in sorted(rois):
                print(f"    - {roi}")
    print()

    # Filter by specific types
    layers = adapter.filter_rois_by_type(sample_rois, 'layers')
    print("Layer ROIs:")
    for roi in sorted(layers):
        print(f"  - {roi}")
    print()

    columns = adapter.filter_rois_by_type(sample_rois, 'columns')
    print("Column ROIs:")
    for roi in sorted(columns):
        print(f"  - {roi}")
    print()

    optic_regions = adapter.filter_rois_by_type(sample_rois, 'optic_regions')
    print("Optic Region ROIs:")
    for roi in sorted(optic_regions):
        print(f"  - {roi}")
    print("\n" + "="*50 + "\n")


def example_cns_roi_queries():
    """Demonstrate ROI queries for CNS dataset."""
    print("=== CNS ROI Query Examples ===\n")

    adapter = DatasetAdapterFactory.create_adapter('cns')

    # Sample CNS ROIs
    sample_rois = [
        'centralBrain', 'CentralBrain(R)', 'CentralBrain(L)',
        'FB(R)', 'FB(L)', 'PB', 'EB', 'NO(R)', 'NO(L)',
        'MB(R)', 'MB(L)', 'LH(R)', 'LH(L)', 'AL(R)', 'AL(L)',
        'VNC', 'T1(R)', 'T1(L)', 'T2(R)', 'T2(L)', 'T3(R)', 'T3(L)',
        'some_other_region', 'detailed_subregion_xyz'
    ]

    central_brain = adapter.query_central_brain_rois(sample_rois)
    print("Central Brain ROIs:")
    for roi in sorted(central_brain):
        print(f"  - {roi}")
    print()

    primary_rois = adapter.query_primary_rois(sample_rois)
    print("Primary ROIs:")
    for roi in sorted(primary_rois):
        print(f"  - {roi}")
    print()

    categories = adapter.categorize_rois(sample_rois)
    print("ROI Categories:")
    for category, rois in categories.items():
        if rois:
            print(f"  {category}:")
            for roi in sorted(rois):
                print(f"    - {roi}")
    print("\n" + "="*50 + "\n")


def example_hemibrain_roi_queries():
    """Demonstrate ROI queries for Hemibrain dataset."""
    print("=== Hemibrain ROI Query Examples ===\n")

    adapter = DatasetAdapterFactory.create_adapter('hemibrain')

    # Sample Hemibrain ROIs
    sample_rois = [
        'FB(R)', 'FB(L)', 'PB', 'EB', 'NO(R)', 'NO(L)',
        'MB(R)', 'MB(L)', 'LH(R)', 'LH(L)', 'AL(R)', 'AL(L)',
        'ME(R)', 'ME(L)', 'LO(R)', 'LO(L)', 'LOP(R)', 'LOP(L)',
        'SLP(R)', 'SLP(L)', 'SIP(R)', 'SIP(L)',
        'optic_tract_R', 'optic_tract_L',
        'some_central_region', 'detailed_roi'
    ]

    central_brain = adapter.query_central_brain_rois(sample_rois)
    print("Central Brain ROIs:")
    for roi in sorted(central_brain):
        print(f"  - {roi}")
    print()

    categories = adapter.categorize_rois(sample_rois)
    print("ROI Categories:")
    for category, rois in categories.items():
        if rois:
            print(f"  {category}:")
            for roi in sorted(rois):
                print(f"    - {roi}")
    print("\n" + "="*50 + "\n")


def example_custom_roi_strategy():
    """Example of creating a custom ROI strategy for a new dataset."""
    print("=== Custom ROI Strategy Example ===\n")

    from src.quickpage.dataset_adapters import RoiQueryStrategy

    class CustomDatasetRoiStrategy(RoiQueryStrategy):
        """Custom ROI strategy for a hypothetical dataset."""

        def get_central_brain_rois(self, all_rois):
            # Custom logic: central brain ROIs contain 'central' or 'brain'
            return [roi for roi in all_rois
                   if 'central' in roi.lower() or 'brain' in roi.lower()]

        def get_primary_rois(self, all_rois):
            # Custom logic: primary ROIs are short names with parentheses
            import re
            primary_pattern = r'^[A-Z]{2,4}\([LR]\)$'
            return [roi for roi in all_rois if re.match(primary_pattern, roi)]

        def categorize_rois(self, all_rois):
            return {
                'central': self.get_central_brain_rois(all_rois),
                'primary': self.get_primary_rois(all_rois),
                'sensory': [roi for roi in all_rois if 'sensory' in roi.lower()],
                'motor': [roi for roi in all_rois if 'motor' in roi.lower()],
                'other': [roi for roi in all_rois
                         if not any(keyword in roi.lower()
                                  for keyword in ['central', 'brain', 'sensory', 'motor'])]
            }

        def filter_rois_by_type(self, all_rois, roi_type):
            categories = self.categorize_rois(all_rois)
            return categories.get(roi_type, [])

    # Demonstrate the custom strategy
    custom_strategy = CustomDatasetRoiStrategy()
    sample_rois = [
        'CentralBrain(R)', 'CentralBrain(L)',
        'FB(R)', 'FB(L)', 'PB', 'EB',
        'sensory_region_1', 'motor_cortex_R',
        'some_other_area', 'specialized_nucleus'
    ]

    print("Custom Strategy Results:")
    categories = custom_strategy.categorize_rois(sample_rois)
    for category, rois in categories.items():
        if rois:
            print(f"  {category}:")
            for roi in sorted(rois):
                print(f"    - {roi}")
    print()


def example_integration_with_neuprint_data():
    """Example showing how to integrate with actual NeuPrint data."""
    print("=== Integration with NeuPrint Data Example ===\n")

    # This would be how you'd use it in your actual page generation code
    def analyze_neuron_type_rois(dataset_name, neuron_type, roi_data):
        """
        Analyze ROI data for a neuron type using dataset-specific strategies.

        Args:
            dataset_name: Name of the dataset (e.g., 'optic-lobe', 'cns')
            neuron_type: Name of the neuron type
            roi_data: DataFrame or list of ROIs from NeuPrint
        """
        # Get appropriate adapter for the dataset
        adapter = DatasetAdapterFactory.create_adapter(dataset_name)

        # Extract ROI names (assuming roi_data is a DataFrame with 'roi' column)
        if hasattr(roi_data, 'columns') and 'roi' in roi_data.columns:
            all_rois = roi_data['roi'].unique().tolist()
        else:
            all_rois = list(roi_data)  # Assume it's already a list

        # Use dataset-specific queries
        analysis = {
            'neuron_type': neuron_type,
            'dataset': dataset_name,
            'total_rois': len(all_rois),
            'central_brain_rois': adapter.query_central_brain_rois(all_rois),
            'primary_rois': adapter.query_primary_rois(all_rois),
            'roi_categories': adapter.categorize_rois(all_rois)
        }

        return analysis

    # Example usage
    mock_optic_lobe_rois = [
        'ME(R)', 'ME(L)', 'LO(R)', 'LO(L)', 'ME_R_layer_1', 'ME_L_layer_2',
        'FB(R)', 'FB(L)', 'PB', 'EB'
    ]

    analysis = analyze_neuron_type_rois(
        'optic-lobe',
        'T4',
        mock_optic_lobe_rois
    )

    print(f"Analysis for {analysis['neuron_type']} in {analysis['dataset']}:")
    print(f"  Total ROIs: {analysis['total_rois']}")
    print(f"  Central Brain ROIs: {len(analysis['central_brain_rois'])}")
    print(f"  Primary ROIs: {len(analysis['primary_rois'])}")
    print("  Categories:")
    for category, rois in analysis['roi_categories'].items():
        if rois:
            print(f"    {category}: {len(rois)} ROIs")
    print()


if __name__ == "__main__":
    """Run all examples."""
    example_optic_lobe_roi_queries()
    example_cns_roi_queries()
    example_hemibrain_roi_queries()
    example_custom_roi_strategy()
    example_integration_with_neuprint_data()

    print("=== Summary ===")
    print("The ROI query strategy pattern allows you to:")
    print("1. Define dataset-specific ROI categorization logic")
    print("2. Query 'central brain' regions differently for each dataset")
    print("3. Filter ROIs by functional types (layers, columns, ROIs)")
    print("4. Easily extend to new datasets by creating new strategy classes")
    print("5. Maintain clean separation between ROI logic and data processing")
