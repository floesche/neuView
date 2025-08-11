"""
JSON data generator for neuron types.
"""

import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from .config import Config


class JsonGenerator:
    """Generate JSON data files for neuron types."""

    def __init__(self, config: Config, output_dir: str):
        """Initialize the JSON generator."""
        self.config = config
        self.output_dir = Path(output_dir)

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_json_from_neuron_type(self, neuron_type_obj) -> str:
        """
        Generate a JSON file from a NeuronType object.

        Args:
            neuron_type_obj: NeuronType instance with data

        Returns:
            Path to the generated JSON file
        """
        # Import here to avoid circular imports
        from .neuron_type import NeuronType

        if not isinstance(neuron_type_obj, NeuronType):
            raise TypeError("Expected NeuronType object")

        # Get data from neuron type object
        neuron_data = neuron_type_obj.to_dict()
        summary = neuron_type_obj.summary
        connectivity = neuron_type_obj.connectivity

        # Extract ROI list from neurons dataframe
        roi_list = []
        if hasattr(neuron_type_obj, '_roi_counts') and neuron_type_obj._roi_counts is not None:
            roi_list = neuron_type_obj._roi_counts.index.tolist() if not neuron_type_obj._roi_counts.empty else []

        # Extract neuron list with detailed information
        neurons_list = []
        if neuron_data['neurons'] is not None and not neuron_data['neurons'].empty:
            neurons_df = neuron_data['neurons']
            for _, neuron in neurons_df.iterrows():
                neuron_info = {
                    'body_id': str(neuron.name),
                    'instance': str(neuron.get('instance', 'N/A')),
                    'pre_synapses': int(neuron.get('pre', 0)),
                    'post_synapses': int(neuron.get('post', 0))
                }

                # Add soma location if available
                if 'somaLocation' in neuron:
                    soma_loc = neuron['somaLocation']
                    if isinstance(soma_loc, (list, tuple)):
                        neuron_info['soma_location'] = [float(x) for x in soma_loc]
                    else:
                        neuron_info['soma_location'] = str(soma_loc)
                elif 'somaSide' in neuron:
                    neuron_info['soma_side'] = str(neuron['somaSide'])

                neurons_list.append(neuron_info)

        # Generate column analysis data
        from .page_generator import PageGenerator
        temp_generator = PageGenerator(self.config, str(self.output_dir))
        column_analysis = temp_generator._analyze_column_roi_data(
            neuron_data.get('roi_counts'),
            neuron_data.get('neurons'),
            neuron_type_obj.soma_side,
            neuron_type_obj.name
        )

        # Prepare JSON data structure
        json_data = self._build_json_structure(neuron_type_obj, summary, connectivity, roi_list, neurons_list, column_analysis)

        # Generate JSON filename and write file
        json_output_path = self._generate_json_file(neuron_type_obj, json_data)

        return str(json_output_path)

    def _build_json_structure(self, neuron_type_obj, summary, connectivity, roi_list, neurons_list, column_analysis=None) -> Dict[str, Any]:
        """
        Build the JSON data structure.

        Args:
            neuron_type_obj: NeuronType instance
            summary: Summary statistics
            connectivity: Connectivity data
            roi_list: List of ROI names
            neurons_list: List of neuron details
            column_analysis: Column-based ROI analysis data

        Returns:
            Dictionary containing the complete JSON structure
        """
        # Map soma side codes to descriptive names for metadata
        soma_side_names = {
            'L': 'left',
            'R': 'right',
            'M': 'middle',
            'all': 'all sides',
            'both': 'all sides',  # backward compatibility
            'left': 'left',      # backward compatibility
            'right': 'right'     # backward compatibility
        }

        soma_side_description = soma_side_names.get(neuron_type_obj.soma_side, neuron_type_obj.soma_side)

        return {
            'neuron_type': str(neuron_type_obj.name),
            'soma_side': str(neuron_type_obj.soma_side),
            'soma_side_description': soma_side_description,
            'summary': {
                'total_cells': int(summary.total_count),
                'left_cells': int(summary.left_count),
                'right_cells': int(summary.right_count),
                'total_pre_synapses': int(summary.total_pre_synapses),
                'total_post_synapses': int(summary.total_post_synapses),
                'avg_pre_synapses': float(round(summary.avg_pre_synapses, 2)),
                'avg_post_synapses': float(round(summary.avg_post_synapses, 2))
            },
            'connectivity': {
                'upstream_connections': int(len(connectivity.upstream)),
                'downstream_connections': int(len(connectivity.downstream)),
                'upstream_partners': [
                    {
                        'partner_type': str(conn.get('type', 'Unknown')),
                        'neurotransmitter': str(conn.get('neurotransmitter', 'Unknown')),
                        'weight': int(conn.get('weight', 0)) if conn.get('weight') is not None else 0,
                        'connections_per_neuron': float(conn.get('connections_per_neuron', 0)) if conn.get('connections_per_neuron') is not None else 0,
                        'percentage': float(conn.get('percentage', 0)) if conn.get('percentage') is not None else 0
                    } for conn in connectivity.upstream
                ],
                'downstream_partners': [
                    {
                        'partner_type': str(conn.get('type', 'Unknown')),
                        'neurotransmitter': str(conn.get('neurotransmitter', 'Unknown')),
                        'weight': int(conn.get('weight', 0)) if conn.get('weight') is not None else 0,
                        'connections_per_neuron': float(conn.get('connections_per_neuron', 0)) if conn.get('connections_per_neuron') is not None else 0,
                        'percentage': float(conn.get('percentage', 0)) if conn.get('percentage') is not None else 0
                    } for conn in connectivity.downstream
                ]
            },
            'roi_list': [str(roi) for roi in roi_list],
            'neurons': neurons_list,
            'column_analysis': column_analysis if column_analysis else None,
            'filtering': {
                'soma_side_filter': str(neuron_type_obj.soma_side),
                'filtered_neuron_count': len(neurons_list),
                'note': f"Data filtered to include only neurons with soma side: {soma_side_description}" if neuron_type_obj.soma_side not in ['all', 'both'] else "Data includes all neurons regardless of soma side"
            },
            'metadata': {
                'generation_time': datetime.now().isoformat(),
                'dataset': str(getattr(self.config.neuprint, 'dataset', 'Unknown')),
                'server': str(getattr(self.config.neuprint, 'server', 'Unknown')),
                'description': str(neuron_type_obj.description)
            }
        }

    def _generate_json_file(self, neuron_type_obj, json_data: Dict[str, Any]) -> Path:
        """
        Generate the JSON filename and write the file.

        Args:
            neuron_type_obj: NeuronType instance
            json_data: JSON data to write

        Returns:
            Path to the generated JSON file
        """
        # Generate JSON filename with same naming scheme as HTML files
        clean_type = neuron_type_obj.name.replace('/', '_').replace(' ', '_')

        # Handle different soma side formats with same naming scheme as HTML
        if neuron_type_obj.soma_side in ['all', 'both']:
            # General data for neuron type (multiple sides available)
            json_filename = f"{clean_type}.json"
        else:
            # Specific data for single side
            soma_side_suffix = neuron_type_obj.soma_side
            if soma_side_suffix == 'left':
                soma_side_suffix = 'L'
            elif soma_side_suffix == 'right':
                soma_side_suffix = 'R'
            elif soma_side_suffix == 'middle':
                soma_side_suffix = 'M'
            json_filename = f"{clean_type}_{soma_side_suffix}.json"

        # Create .data subdirectory if it doesn't exist
        data_dir = self.output_dir / '.data'
        data_dir.mkdir(exist_ok=True)

        json_output_path = data_dir / json_filename

        # Write JSON file
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        return json_output_path
