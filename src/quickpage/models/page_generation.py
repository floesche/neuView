"""
Page Generation Models

This module contains data models for page generation requests, responses,
and related data structures to provide type safety and clear interfaces.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
from pathlib import Path


class PageGenerationMode(Enum):
    """Mode for page generation indicating data source."""
    FROM_RAW_DATA = "raw_data"
    FROM_NEURON_TYPE = "neuron_type"


@dataclass
class PageGenerationRequest:
    """Request object for page generation containing all necessary parameters."""

    # Core identification
    neuron_type: str
    soma_side: str

    # Data source (either neuron_data OR neuron_type_obj should be provided)
    neuron_data: Optional[Dict[str, Any]] = None
    neuron_type_obj: Optional[Any] = None  # NeuronType object

    # Dependencies
    connector: Any = None  # NeuPrint connector

    # Output options
    image_format: str = 'svg'
    embed_images: bool = False
    uncompress: bool = False

    # Analysis options
    run_roi_analysis: bool = True
    run_layer_analysis: bool = True
    run_column_analysis: bool = True

    # Visualization options
    hex_size: int = 6
    spacing_factor: float = 1.1

    @property
    def mode(self) -> PageGenerationMode:
        """Determine the generation mode based on provided data."""
        if self.neuron_type_obj is not None:
            return PageGenerationMode.FROM_NEURON_TYPE
        else:
            return PageGenerationMode.FROM_RAW_DATA

    def get_neuron_data(self) -> Dict[str, Any]:
        """Get neuron data regardless of source mode."""
        if self.mode == PageGenerationMode.FROM_NEURON_TYPE:
            if self.neuron_type_obj is not None:
                return self.neuron_type_obj.to_dict()
            return {}
        else:
            return self.neuron_data or {}

    def get_neuron_name(self) -> str:
        """Get neuron type name regardless of source mode."""
        if self.mode == PageGenerationMode.FROM_NEURON_TYPE:
            if self.neuron_type_obj is not None:
                return self.neuron_type_obj.name
            return ""
        else:
            return self.neuron_type

    def get_soma_side(self) -> str:
        """Get soma side regardless of source mode."""
        if self.mode == PageGenerationMode.FROM_NEURON_TYPE:
            if self.neuron_type_obj is not None:
                return self.neuron_type_obj.soma_side
            return ""
        else:
            return self.soma_side

    def validate(self) -> bool:
        """Validate that the request has required data."""
        if not self.neuron_type:
            return False

        if self.mode == PageGenerationMode.FROM_RAW_DATA:
            return self.neuron_data is not None and self.connector is not None
        elif self.mode == PageGenerationMode.FROM_NEURON_TYPE:
            return self.neuron_type_obj is not None and self.connector is not None

        return False


@dataclass
class AnalysisResults:
    """Container for all analysis results."""

    roi_summary: Optional[Dict[str, Any]] = None
    layer_analysis: Optional[Dict[str, Any]] = None
    column_analysis: Optional[Dict[str, Any]] = None

    def has_any_analysis(self) -> bool:
        """Check if any analysis results are available."""
        return any([
            self.roi_summary is not None,
            self.layer_analysis is not None,
            self.column_analysis is not None
        ])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template context."""
        # Always provide expected keys to prevent template errors
        result = {
            'roi_summary': self.roi_summary,
            'layer_analysis': self.layer_analysis,
            'column_analysis': self.column_analysis
        }

        return result


@dataclass
class URLCollection:
    """Container for all generated URLs."""

    neuroglancer_url: Optional[str] = None
    neuprint_url: Optional[str] = None
    soma_side_links: Optional[Dict[str, str]] = None
    youtube_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template context."""
        return {
            'neuroglancer_url': self.neuroglancer_url,
            'neuprint_url': self.neuprint_url,
            'soma_side_links': self.soma_side_links or {},
            'youtube_url': self.youtube_url
        }


@dataclass
class PageGenerationContext:
    """Complete context for page generation."""

    request: PageGenerationRequest
    analysis_results: AnalysisResults
    urls: URLCollection
    neuroglancer_vars: Optional[Dict[str, Any]] = None
    type_region: Optional[str] = None
    additional_context: Dict[str, Any] = field(default_factory=dict)

    def to_template_context(self) -> Dict[str, Any]:
        """Convert to dictionary suitable for template rendering."""
        context = {
            'neuron_type': self.request.get_neuron_name(),
            'soma_side': self.request.get_soma_side(),
            'neuron_data': self.request.get_neuron_data(),
            'connectivity_data': self.request.get_neuron_data().get('connectivity', {}),
            **self.analysis_results.to_dict(),
            **self.urls.to_dict(),
            **self.additional_context
        }

        if self.neuroglancer_vars:
            context.update(self.neuroglancer_vars)

        if self.type_region:
            context['type_region'] = self.type_region

        return context


@dataclass
class PageGenerationResponse:
    """Response object containing the result of page generation."""

    output_path: str
    success: bool = True
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    # Metadata about the generation
    template_name: str = 'neuron_page.html.jinja'
    generation_time_ms: Optional[float] = None
    file_size_bytes: Optional[int] = None

    @classmethod
    def success_response(cls, output_path: str, **kwargs) -> 'PageGenerationResponse':
        """Create a successful response."""
        return cls(output_path=output_path, success=True, **kwargs)

    @classmethod
    def error_response(cls, error_message: str, **kwargs) -> 'PageGenerationResponse':
        """Create an error response."""
        return cls(
            output_path="",
            success=False,
            error_message=error_message,
            **kwargs
        )

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)

    def get_output_path(self) -> Optional[Path]:
        """Get output path as Path object if successful."""
        if self.success and self.output_path:
            return Path(self.output_path)
        return None


@dataclass
class AnalysisConfiguration:
    """Configuration for what analyses to run."""

    run_roi_analysis: bool = True
    run_layer_analysis: bool = True
    run_column_analysis: bool = True

    # Analysis-specific options
    column_analysis_options: Dict[str, Any] = field(default_factory=dict)
    layer_analysis_options: Dict[str, Any] = field(default_factory=dict)
    roi_analysis_options: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_request(cls, request: PageGenerationRequest) -> 'AnalysisConfiguration':
        """Create analysis configuration from page generation request."""
        return cls(
            run_roi_analysis=getattr(request, 'run_roi_analysis', True),
            run_layer_analysis=getattr(request, 'run_layer_analysis', True),
            run_column_analysis=getattr(request, 'run_column_analysis', True),
            column_analysis_options={
                'file_type': request.image_format,
                'save_to_files': not request.embed_images
            }
        )

    def should_run_any_analysis(self) -> bool:
        """Check if any analysis should be run."""
        return any([
            self.run_roi_analysis,
            self.run_layer_analysis,
            self.run_column_analysis
        ])
