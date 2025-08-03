"""
Configuration management for QuickPage.
"""

import yaml
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv


@dataclass
class NeuPrintConfig:
    """NeuPrint server configuration."""
    server: str
    dataset: str
    token: Optional[str] = None


@dataclass
class OutputConfig:
    """Output configuration."""
    directory: str
    template_dir: str
    include_3d_view: bool = False
    generate_json: bool = False


@dataclass
class DiscoveryConfig:
    """Auto-discovery configuration for neuron types."""
    max_types: int = 10
    min_neuron_count: int = 5
    type_filter: Optional[str] = None
    exclude_types: list[str] = field(default_factory=list)
    include_only: list[str] = field(default_factory=list)


@dataclass
class NeuronTypeConfig:
    """Neuron type configuration."""
    name: str
    description: str = ""
    query_type: str = "type"
    soma_side: str = "both"
    min_synapse_count: int = 0


@dataclass
class HtmlConfig:
    """HTML generation configuration."""
    title_prefix: str = "Neuron Type Report"
    css_framework: str = "pulse"
    include_images: bool = True
    include_connectivity: bool = True


@dataclass
class Config:
    """Main configuration class."""
    neuprint: NeuPrintConfig
    output: OutputConfig
    discovery: DiscoveryConfig
    html: HtmlConfig
    neuron_types: list["NeuronTypeConfig"] = field(default_factory=list)
    
    @classmethod
    def load(cls, config_path: str) -> 'Config':
        """Load configuration from YAML file."""
        # Load environment variables from .env file if it exists
        env_file = Path('.env')
        if env_file.exists():
            load_dotenv(env_file)
        
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r') as f:
            data = yaml.safe_load(f)
        
        # Parse configuration sections
        neuprint_data = data['neuprint'].copy()
        
        # Override token from environment if available
        env_token = os.getenv('NEUPRINT_TOKEN')
        if env_token:
            neuprint_data['token'] = env_token
        
        neuprint_config = NeuPrintConfig(**neuprint_data)
        output_config = OutputConfig(**data['output'])
        discovery_config = DiscoveryConfig(**data.get('discovery', {}))
        html_config = HtmlConfig(**data.get('html', {}))
        
        neuron_types = [
            NeuronTypeConfig(**nt) for nt in data.get('neuron_types', [])
        ]
        
        return cls(
            neuprint=neuprint_config,
            output=output_config,
            discovery=discovery_config,
            html=html_config,
            neuron_types=neuron_types
        )
    
    def get_neuron_type_config(self, name: str) -> Optional[NeuronTypeConfig]:
        """Get configuration for a specific neuron type."""
        for nt in self.neuron_types:
            if nt.name == name:
                return nt
        return None
