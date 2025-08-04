"""
HTML page generator using Jinja2 templates.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, Template
import pandas as pd
from datetime import datetime

from .config import Config


class PageGenerator:
    """Generate HTML pages for neuron types."""
    
    def __init__(self, config: Config, output_dir: str):
        """Initialize the page generator."""
        self.config = config
        self.output_dir = Path(output_dir)
        self.template_dir = Path(config.output.template_dir)
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Jinja2 environment
        self._setup_jinja_env()
    
    def _setup_jinja_env(self):
        """Set up Jinja2 environment with templates."""
        # Create template directory if it doesn't exist
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
        
        # Add custom filters
        self.env.filters['format_number'] = self._format_number
        self.env.filters['format_percentage'] = self._format_percentage
    

    def generate_page(self, neuron_type: str, neuron_data: Dict[str, Any], 
                     soma_side: str) -> str:
        """
        Generate an HTML page for a neuron type.
        
        Args:
            neuron_type: The neuron type name
            neuron_data: Data returned from NeuPrintConnector
            soma_side: Soma side filter used
            
        Returns:
            Path to the generated HTML file
        """
        # Load template
        template = self.env.get_template('neuron_page.html')
        
        # Prepare template context
        context = {
            'config': self.config,
            'neuron_data': neuron_data,
            'neuron_type': neuron_type,
            'soma_side': soma_side,
            'summary': neuron_data['summary'],
            'neurons_df': neuron_data['neurons'],
            'connectivity': neuron_data.get('connectivity', {}),
            'generation_time': datetime.now()
        }
        
        # Render template
        html_content = template.render(**context)
        
        # Generate output filename
        output_filename = self._generate_filename(neuron_type, soma_side)
        output_path = self.output_dir / output_filename
        
        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(output_path)
    
    def generate_page_from_neuron_type(self, neuron_type_obj) -> str:
        """
        Generate an HTML page from a NeuronType object.
        
        Args:
            neuron_type_obj: NeuronType instance with data
            
        Returns:
            Path to the generated HTML file
        """
        # Import here to avoid circular imports
        from .neuron_type import NeuronType
        
        if not isinstance(neuron_type_obj, NeuronType):
            raise TypeError("Expected NeuronType object")
        
        # Load template
        template = self.env.get_template('neuron_page.html')
        
        # Get data from neuron type object
        neuron_data = neuron_type_obj.to_dict()
        
        # Prepare template context
        context = {
            'config': self.config,
            'neuron_data': neuron_data,
            'neuron_type': neuron_type_obj.name,
            'soma_side': neuron_type_obj.soma_side,
            'summary': neuron_data['summary'],
            'neurons_df': neuron_data['neurons'],
            'connectivity': neuron_data.get('connectivity', {}),
            'generation_time': datetime.now(),
            'neuron_type_obj': neuron_type_obj  # Provide access to the object itself
        }
        
        # Render template
        html_content = template.render(**context)
        
        # Generate output filename
        output_filename = self._generate_filename(neuron_type_obj.name, neuron_type_obj.soma_side)
        output_path = self.output_dir / output_filename
        
        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Generate JSON file if enabled
        if self.config.output.generate_json:
            json_output_path = self._generate_json_file(neuron_type_obj)
            if json_output_path:
                return f"{str(output_path)}, JSON: {json_output_path}"
        
        return str(output_path)
    
    def _generate_filename(self, neuron_type: str, soma_side: str) -> str:
        """Generate output filename based on neuron type and soma side."""
        # Clean neuron type name for filename
        clean_type = neuron_type.replace('/', '_').replace(' ', '_')
        
        if soma_side == 'both':
            return f"{clean_type}_neuron_report.html"
        else:
            return f"{clean_type}_{soma_side}_neuron_report.html"
    
    def _generate_json_file(self, neuron_type_obj) -> str:
        """
        Generate a JSON file containing neuron type data.
        
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
        
        # Prepare JSON data structure
        json_data = {
            'neuron_type': str(neuron_type_obj.name),
            'soma_side': str(neuron_type_obj.soma_side),
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
                        'weight': int(conn.get('weight', 0)) if conn.get('weight') is not None else 0,
                        'count': int(conn.get('count', 0)) if conn.get('count') is not None else 0
                    } for conn in connectivity.upstream
                ],
                'downstream_partners': [
                    {
                        'partner_type': str(conn.get('type', 'Unknown')),
                        'weight': int(conn.get('weight', 0)) if conn.get('weight') is not None else 0,
                        'count': int(conn.get('count', 0)) if conn.get('count') is not None else 0
                    } for conn in connectivity.downstream
                ]
            },
            'roi_list': [str(roi) for roi in roi_list],
            'neurons': neurons_list,
            'metadata': {
                'generation_time': datetime.now().isoformat(),
                'dataset': str(getattr(self.config.neuprint, 'dataset', 'Unknown')),
                'server': str(getattr(self.config.neuprint, 'server', 'Unknown')),
                'description': str(neuron_type_obj.description)
            }
        }
        
        # Generate JSON filename
        clean_type = neuron_type_obj.name.replace('/', '_').replace(' ', '_')
        if neuron_type_obj.soma_side == 'both':
            json_filename = f"{clean_type}_neuron_data.json"
        else:
            json_filename = f"{clean_type}_{neuron_type_obj.soma_side}_neuron_data.json"
        
        json_output_path = self.output_dir / json_filename
        
        # Write JSON file
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        return str(json_output_path)
    
    def _format_number(self, value: Any) -> str:
        """Format numbers with commas."""
        if isinstance(value, (int, float)):
            return f"{value:,}"
        return str(value)
    
    def _format_percentage(self, value: Any) -> str:
        """Format numbers as percentages."""
        if isinstance(value, (int, float)):
            return f"{value:.1f}%"
        return str(value)
