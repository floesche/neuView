"""
HTML page generator using Jinja2 templates.
"""

from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader
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
            from .json_generator import JsonGenerator
            json_generator = JsonGenerator(self.config, str(self.output_dir))
            json_output_path = json_generator.generate_json_from_neuron_type(neuron_type_obj)
            if json_output_path:
                return f"{str(output_path)}, JSON: {json_output_path}"
        
        return str(output_path)
    
    def _generate_filename(self, neuron_type: str, soma_side: str) -> str:
        """Generate output filename based on neuron type and soma side."""
        # Clean neuron type name for filename
        clean_type = neuron_type.replace('/', '_').replace(' ', '_')
        
        # Handle different soma side formats
        if soma_side in ['all', 'both']:
            return f"{clean_type}_neuron_report.html"
        else:
            # Use the soma side directly (L, R, M, or legacy left/right)
            soma_side_suffix = soma_side
            if soma_side_suffix == 'left':
                soma_side_suffix = 'L'
            elif soma_side_suffix == 'right':
                soma_side_suffix = 'R'
            return f"{clean_type}_{soma_side_suffix}_neuron_report.html"
    
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
