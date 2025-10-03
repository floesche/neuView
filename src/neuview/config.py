"""
Configuration management for neuView.
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


@dataclass
class DiscoveryConfig:
    """Auto-discovery configuration for neuron types."""

    max_types: int = 10
    type_filter: Optional[str] = None
    exclude_types: list[str] = field(default_factory=list)
    include_only: list[str] = field(default_factory=list)
    randomize: bool = True


@dataclass
class NeuronTypeConfig:
    """Neuron type configuration."""

    name: str
    description: str = ""
    query_type: str = "type"
    soma_side: str = "combined"


@dataclass
class HtmlConfig:
    """HTML generation configuration."""

    title_prefix: str = "Neuron Type Report"
    github_repo: Optional[str] = None
    youtube_channel: Optional[str] = None


@dataclass
class Config:
    """Main configuration class."""

    neuprint: NeuPrintConfig
    output: OutputConfig
    discovery: DiscoveryConfig
    html: HtmlConfig
    neuron_types: list["NeuronTypeConfig"] = field(default_factory=list)

    @classmethod
    def load(cls, config_path: str) -> "Config":
        """Load configuration from YAML file."""
        # Load environment variables from .env file if it exists
        env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file)

        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_file, "r") as f:
            data = yaml.safe_load(f)

        # Parse configuration sections
        neuprint_data = data["neuprint"].copy()

        # Override token from environment if available
        env_token = os.getenv("NEUPRINT_TOKEN")
        if env_token:
            neuprint_data["token"] = env_token

        neuprint_config = NeuPrintConfig(**neuprint_data)
        output_config = OutputConfig(**data["output"])
        discovery_config = DiscoveryConfig(**data.get("discovery", {}))
        html_config = HtmlConfig(**data.get("html", {}))

        neuron_types = [NeuronTypeConfig(**nt) for nt in data.get("neuron_types", [])]

        return cls(
            neuprint=neuprint_config,
            output=output_config,
            discovery=discovery_config,
            html=html_config,
            neuron_types=neuron_types,
        )

    def get_neuprint_token(self) -> str:
        """
        Get the NeuPrint token with proper fallback handling.

        Returns the token from config or environment variable.
        Raises ValueError if no token is found.
        """
        # First try config token
        if self.neuprint.token:
            return self.neuprint.token

        # Fall back to environment variable
        env_token = os.getenv("NEUPRINT_TOKEN")
        if env_token:
            return env_token

        # No token found
        raise ValueError(
            "NeuPrint token not found. Set it in one of these ways:\n"
            "1. Create a .env file with NEUPRINT_TOKEN=your_token\n"
            "2. Set NEUPRINT_TOKEN environment variable\n"
            "3. Add token to config.yaml"
        )

    def get_neuron_type_config(self, name: str) -> Optional[NeuronTypeConfig]:
        """Get configuration for a specific neuron type."""
        for nt in self.neuron_types:
            if nt.name == name:
                return nt
        return None

    @classmethod
    def create_minimal_for_testing(cls) -> "Config":
        """Create minimal configuration for testing purposes."""
        neuprint_config = NeuPrintConfig(
            server="test.neuprint.janelia.org", dataset="test", token="test_token"
        )

        output_config = OutputConfig(
            directory="/tmp/test_output", template_dir="templates"
        )

        discovery_config = DiscoveryConfig()
        html_config = HtmlConfig()

        return cls(
            neuprint=neuprint_config,
            output=output_config,
            discovery=discovery_config,
            html=html_config,
            neuron_types=[],
        )

    @classmethod
    def create_default(cls) -> "Config":
        """Create default configuration."""
        neuprint_config = NeuPrintConfig(
            server="neuprint.janelia.org", dataset="hemibrain:v1.2.1"
        )

        output_config = OutputConfig(directory="output", template_dir="templates")

        discovery_config = DiscoveryConfig()
        html_config = HtmlConfig()

        return cls(
            neuprint=neuprint_config,
            output=output_config,
            discovery=discovery_config,
            html=html_config,
            neuron_types=[],
        )

    @classmethod
    def from_file(cls, config_file: str) -> "Config":
        """Load configuration from file (alias for load method)."""
        return cls.load(config_file)

    @classmethod
    def from_dict(cls, config_dict: dict) -> "Config":
        """Create Config from dictionary."""
        # Initialize from dictionary
        neuprint_data = config_dict["neuprint"].copy()

        # Override token from environment if available
        env_token = os.getenv("NEUPRINT_TOKEN")
        if env_token:
            neuprint_data["token"] = env_token

        neuprint_config = NeuPrintConfig(**neuprint_data)
        output_config = OutputConfig(**config_dict["output"])
        discovery_config = DiscoveryConfig(**config_dict.get("discovery", {}))
        html_config = HtmlConfig(**config_dict.get("html", {}))
        neuron_types = [
            NeuronTypeConfig(**nt) for nt in config_dict.get("neuron_types", [])
        ]

        return cls(
            neuprint=neuprint_config,
            output=output_config,
            discovery=discovery_config,
            html=html_config,
            neuron_types=neuron_types,
        )
