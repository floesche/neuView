"""
Configuration management for QuickPage.
"""

import yaml
import toml
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
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


@dataclass
class NeuronTypeConfig:
    """Neuron type configuration."""
    name: str
    description: str = ""
    query_type: str = "type"


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
    neuron_types: List[NeuronTypeConfig]
    html: HtmlConfig
    custom: Dict[str, Any] = field(default_factory=dict)
    
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
        
        # Load custom configuration if it exists
        custom_config = {}
        custom_path = config_file.parent / "quickpage_custom.toml"
        if custom_path.exists():
            with open(custom_path, 'r') as f:
                custom_config = toml.load(f)
        
        # Parse configuration sections
        neuprint_data = data['neuprint'].copy()
        
        # Override token from environment if available
        env_token = os.getenv('NEUPRINT_TOKEN')
        if env_token:
            neuprint_data['token'] = env_token
        
        neuprint_config = NeuPrintConfig(**neuprint_data)
        output_config = OutputConfig(**data['output'])
        html_config = HtmlConfig(**data.get('html', {}))
        
        neuron_types = [
            NeuronTypeConfig(**nt) for nt in data.get('neuron_types', [])
        ]
        
        return cls(
            neuprint=neuprint_config,
            output=output_config,
            neuron_types=neuron_types,
            html=html_config,
            custom=custom_config
        )
    
    def get_neuron_type_config(self, name: str) -> Optional[NeuronTypeConfig]:
        """Get configuration for a specific neuron type."""
        for nt in self.neuron_types:
            if nt.name == name:
                return nt
        return None
    
    def get_custom_setting(self, key: str, default: Any = None) -> Any:
        """Get a custom setting from the custom configuration."""
        keys = key.split('.')
        value = self.custom
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
