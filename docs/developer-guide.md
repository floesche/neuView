# QuickPage Developer Guide

A comprehensive guide to understanding and contributing to the QuickPage neuron visualization system.

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture Overview](#architecture-overview)
- [Getting Started](#getting-started)
- [Core Components](#core-components)
- [Service Architecture](#service-architecture)
- [Data Processing Pipeline](#data-processing-pipeline)
- [Visualization System](#visualization-system)
- [Template System](#template-system)
- [Performance & Caching](#performance--caching)
- [Development Patterns](#development-patterns)
- [Testing Strategy](#testing-strategy)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Project Overview

QuickPage is a modern Python CLI tool that generates interactive HTML pages for neuron types using data from NeuPrint. The system is built with Domain-Driven Design (DDD) principles and features a service-oriented architecture for maintainability and extensibility.

### Key Features

- **Multi-Dataset Support**: Automatic adaptation for CNS, Hemibrain, and Optic-lobe datasets
- **High Performance**: Up to 97.9% speed improvement with persistent caching
- **Interactive Web Interface**: Advanced filtering, search, and visualization
- **Hexagon Grid Visualization**: Beautiful eyemap representations
- **Rich Analytics**: Hemisphere balance, connectivity stats, ROI summaries
- **Template-Driven**: Flexible Jinja2-based template system

### Technology Stack

- **Backend**: Python 3.9+, pandas, numpy
- **Database**: NeuPrint (Neo4j-based)
- **Templates**: Jinja2
- **Frontend**: Modern HTML5, CSS3, JavaScript (ES6+)
- **Visualization**: SVG-based hexagon grids, DataTables
- **Build System**: Pixi (conda-forge based)

## Architecture Overview

QuickPage follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI Interface Layer                      │
│                   (commands.py, cli.py)                    │
├─────────────────────────────────────────────────────────────┤
│                   Application Layer                         │
│            (PageGenerator, Orchestrator)                   │
├─────────────────────────────────────────────────────────────┤
│                    Service Layer                           │
│    (30+ specialized services for different concerns)       │
├─────────────────────────────────────────────────────────────┤
│                   Domain Layer                             │
│         (Models, DTOs, Business Logic)                     │
├─────────────────────────────────────────────────────────────┤
│                Infrastructure Layer                        │
│    (NeuPrint Connector, File System, Cache)               │
└─────────────────────────────────────────────────────────────┘
```

### Key Architectural Principles

1. **Service-Oriented Architecture**: Each concern is handled by a dedicated service
2. **Dependency Injection**: Services are injected via factory patterns
3. **Strategy Pattern**: Multiple implementations for different datasets and operations
4. **Command/Query Separation**: Clear distinction between read and write operations
5. **Result Pattern**: Explicit error handling without exceptions where appropriate
6. **Template-Driven**: All output is generated through configurable templates

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Pixi package manager
- NeuPrint access token
- Git

### Development Setup

1. **Clone and setup the project:**
```bash
git clone <repository-url>
cd quickpage
pixi install
```

2. **Configure environment:**
```bash
pixi run setup-env
# Edit .env file with your NeuPrint token
echo "NEUPRINT_TOKEN=your_token_here" >> .env
echo "NEUPRINT_SERVER=neuprint.janelia.org" >> .env
```

3. **Verify installation:**
```bash
quickpage test-connection
```

4. **Generate a test page:**
```bash
quickpage generate -n Dm4
```

### Development Commands

```bash
# Run all tests
pixi run test

# Run development server (for template development)
pixi run dev

# Run performance analysis
pixi run performance-analysis

# Clean caches
pixi run clean-cache

# Generate test dataset
pixi run test-set
```

## Core Components

### PageGenerator

The main application class that orchestrates page generation:

```python
from quickpage import PageGenerator

# Create with default configuration
generator = PageGenerator()

# Generate a page
result = generator.generate_page("Dm4")
```

Key responsibilities:
- Service container management
- Template environment setup
- High-level page generation orchestration

### PageGenerationOrchestrator

Handles the complete page generation workflow:

```python
class PageGenerationOrchestrator:
    def generate_page(self, request: PageGenerationRequest) -> PageGenerationResponse:
        # 1. Load and validate neuron data
        # 2. Run analysis pipeline
        # 3. Generate template context
        # 4. Render templates
        # 5. Generate static resources
        # 6. Create output files
```

### NeuronType Class

Core domain model representing a neuron type:

```python
class NeuronType:
    def __init__(self, name: str, side: SomaSide = None):
        self.name = name
        self.side = side
        self.data = None
        self._cache_key = None
    
    def get_cache_key(self) -> str:
        """Generate unique cache key for this neuron type"""
    
    def get_neuron_count(self) -> int:
        """Get total neuron count"""
    
    def get_synapse_stats(self) -> Dict[str, Any]:
        """Get synapse statistics"""
```

## Service Architecture

The system uses over 30 specialized services, each handling a specific concern:

### Core Services

#### Data Services
- **DatabaseQueryService**: NeuPrint database interactions
- **NeuronDataService**: Neuron data fetching and processing
- **DataProcessingService**: Raw data transformation
- **NeuronSelectionService**: Neuron filtering and selection

#### Analysis Services
- **ROIAnalysisService**: Region of interest analysis
- **LayerAnalysisService**: Layer-specific analysis
- **ColumnAnalysisService**: Column data analysis
- **PartnerAnalysisService**: Connectivity partner analysis

#### Content Services
- **TemplateContextService**: Template data preparation
- **URLGenerationService**: URL and link generation
- **CitationService**: Scientific citation handling
- **YouTubeService**: Video content integration

#### Infrastructure Services
- **CacheService**: Multi-level caching system
- **FileService**: File system operations
- **ResourceManagerService**: Static resource handling
- **BrainRegionService**: Brain region data management

### Service Container Pattern

Services are managed through a dependency injection container:

```python
class ServiceContainer:
    def __init__(self):
        self._services = {}
        self._factories = {}
    
    def register(self, service_type: type, factory: callable):
        """Register a service factory"""
        self._factories[service_type] = factory
    
    def get(self, service_type: type):
        """Get or create a service instance"""
        if service_type not in self._services:
            factory = self._factories[service_type]
            self._services[service_type] = factory()
        return self._services[service_type]
```

### Service Development Pattern

When creating new services, follow this pattern:

```python
class ExampleService:
    def __init__(self, dependency_service: DependencyService):
        self.dependency_service = dependency_service
        self.logger = logging.getLogger(__name__)
    
    def process_data(self, input_data: Any) -> Result[ProcessedData, Error]:
        """Process data with explicit error handling"""
        try:
            # Validate input
            if not self._validate_input(input_data):
                return Result.error("Invalid input data")
            
            # Process data
            processed = self._do_processing(input_data)
            
            # Return success result
            return Result.success(processed)
            
        except Exception as e:
            self.logger.error(f"Processing failed: {e}")
            return Result.error(f"Processing failed: {e}")
    
    def _validate_input(self, data: Any) -> bool:
        """Private validation method"""
        return data is not None
    
    def _do_processing(self, data: Any) -> ProcessedData:
        """Private processing method"""
        return ProcessedData(data)
```

## Data Processing Pipeline

### Dataset Adapters

The system automatically adapts to different datasets using the adapter pattern:

```python
class DatasetAdapter:
    """Base class for dataset-specific adaptations"""
    
    def extract_soma_side(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract soma side information"""
        raise NotImplementedError
    
    def normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names and types"""
        return df
    
    def categorize_rois(self, rois: List[str]) -> Dict[str, List[str]]:
        """Categorize ROIs by type"""
        return {"unknown": rois}

class CNSAdapter(DatasetAdapter):
    def extract_soma_side(self, df: pd.DataFrame) -> pd.DataFrame:
        # CNS-specific soma side extraction
        pass

class HemibrainAdapter(DatasetAdapter):
    def extract_soma_side(self, df: pd.DataFrame) -> pd.DataFrame:
        # Hemibrain-specific soma side extraction
        pass
```

### Data Flow

1. **Raw Data Acquisition**: NeuPrint queries fetch raw neuron data
2. **Dataset Detection**: System automatically detects dataset type
3. **Adapter Selection**: Appropriate dataset adapter is selected
4. **Data Transformation**: Raw data is normalized and enriched
5. **Analysis Pipeline**: Multiple analysis services process the data
6. **Template Context**: Processed data is formatted for templates
7. **Output Generation**: HTML and static files are generated

### ROI Query Strategies

Different datasets require different ROI querying approaches:

```python
class ROIQueryStrategy:
    def query_central_brain_rois(self, neuron_df: pd.DataFrame) -> List[str]:
        """Query central brain ROIs for given neurons"""
        raise NotImplementedError
    
    def categorize_rois(self, rois: List[str]) -> Dict[str, List[str]]:
        """Categorize ROIs by anatomical type"""
        raise NotImplementedError
```

## Visualization System

### Hexagon Grid Generator

The system generates beautiful hexagon grid visualizations:

```python
class HexagonGridGenerator:
    def __init__(self, hex_size: float = 10.0, spacing_factor: float = 1.1):
        self.hex_size = hex_size
        self.spacing_factor = spacing_factor
    
    def generate_region_hexagonal_grids(self, 
                                      region_data: Dict[str, Any],
                                      region_columns: List[str]) -> Dict[str, Any]:
        """Generate hexagon grids for all regions"""
        
    def generate_single_region_grid(self, 
                                  region_name: str,
                                  column_data: pd.DataFrame,
                                  columns: List[str]) -> Dict[str, Any]:
        """Generate a single hexagon grid"""
```

### Coordinate System

The visualization uses an axial coordinate system:

```python
def hex_to_axial(row: int, col: int) -> Tuple[int, int]:
    """Convert hex grid coordinates to axial coordinates"""
    q = col
    r = row - (col - (col & 1)) // 2
    return q, r

def axial_to_pixel(q: int, r: int, hex_size: float) -> Tuple[float, float]:
    """Convert axial coordinates to pixel coordinates"""
    x = hex_size * (3/2 * q)
    y = hex_size * (math.sqrt(3)/2 * q + math.sqrt(3) * r)
    return x, y
```

### Color Mapping

A sophisticated 5-tier color system maps data values to colors:

```python
def get_color_for_value(value: float, 
                       max_value: float, 
                       color_scheme: str = "blues") -> str:
    """Map a value to a color in the specified scheme"""
    if value == 0:
        return "#f0f0f0"  # Light gray for zero
    
    # Calculate tier (1-5)
    tier = min(5, max(1, int((value / max_value) * 5) + 1))
    
    # Return color based on tier and scheme
    return COLOR_SCHEMES[color_scheme][tier - 1]
```

## Template System

### Template Architecture

The template system uses Jinja2 with a sophisticated strategy pattern:

```python
class TemplateStrategy:
    def load_template(self, template_name: str) -> Template:
        """Load a template by name"""
        raise NotImplementedError
    
    def render_template(self, template: Template, context: Dict[str, Any]) -> str:
        """Render a template with given context"""
        raise NotImplementedError

class JinjaTemplateStrategy(TemplateStrategy):
    def __init__(self, template_dir: Path):
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self._setup_filters()
    
    def _setup_filters(self):
        """Setup custom Jinja2 filters"""
        self.env.filters['percentage'] = PercentageFormatter.format
        self.env.filters['scientific'] = NumberFormatter.scientific
        self.env.filters['neurotransmitter'] = NeurotransmitterFormatter.format
```

### Template Structure

```
templates/
├── base.html              # Base template with common layout
├── macros.html           # Reusable template macros
├── neuron_page.html      # Main neuron page template
├── index.html            # Index page template
├── help.html             # Help page template
└── sections/             # Modular template sections
    ├── header.html
    ├── navigation.html
    ├── filters.html
    ├── statistics.html
    ├── connectivity.html
    ├── eyemaps.html
    └── footer.html
```

### Template Context

Templates receive a rich context object:

```python
class TemplateContext:
    neuron_type: NeuronType
    statistics: Dict[str, Any]
    connectivity_data: Dict[str, Any]
    roi_analysis: Dict[str, Any]
    eyemaps: Dict[str, Any]
    filter_options: Dict[str, Any]
    urls: URLCollection
    metadata: Dict[str, Any]
```

### Custom Template Filters

```python
# Percentage formatting
{{ value | percentage }}  # 0.156 -> "15.6%"

# Scientific notation
{{ value | scientific }}  # 1234567 -> "1.23 × 10⁶"

# Neurotransmitter formatting
{{ nt_list | neurotransmitter }}  # ["GABA", "ACh"] -> "GABA, ACh"

# Color mapping
{{ value | color_for_neurons(max_value) }}  # Returns hex color
```

## Performance & Caching

### Multi-Level Cache System

The system implements sophisticated caching at multiple levels:

```python
class CacheService:
    def __init__(self):
        self.memory_cache = {}        # In-memory cache
        self.file_cache = FileCache() # Persistent file cache
        self.database_cache = {}      # Database query cache
    
    def get_cached_data(self, cache_key: str) -> Optional[Any]:
        """Get data from cache with fallback hierarchy"""
        # Try memory cache first
        if cache_key in self.memory_cache:
            return self.memory_cache[cache_key]
        
        # Try file cache
        data = self.file_cache.get(cache_key)
        if data is not None:
            self.memory_cache[cache_key] = data
            return data
        
        return None
```

### Cache Types

1. **Memory Cache**: Fast in-memory storage for frequently accessed data
2. **Persistent Cache**: File-based cache that survives application restarts
3. **Database Cache**: Caches expensive NeuPrint queries
4. **Template Cache**: Compiled template caching
5. **Resource Cache**: Static file and image caching

### Performance Optimizations

- **Lazy Loading**: Data is loaded only when needed
- **Chunk Processing**: Large datasets are processed in chunks
- **Connection Pooling**: Database connections are reused
- **Async Processing**: Non-blocking operations where possible
- **Memory Management**: Automatic cleanup of unused cache entries

### Performance Monitoring

```python
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
    
    def start_timer(self, operation: str):
        """Start timing an operation"""
        self.start_times[operation] = time.time()
    
    def end_timer(self, operation: str):
        """End timing and record metrics"""
        if operation in self.start_times:
            duration = time.time() - self.start_times[operation]
            self.metrics[operation] = duration
            del self.start_times[operation]
```

## Development Patterns

### Error Handling

Use the Result pattern for explicit error handling:

```python
from quickpage.result import Result

def process_neuron_data(neuron_name: str) -> Result[NeuronData, str]:
    try:
        # Validate input
        if not neuron_name:
            return Result.error("Neuron name cannot be empty")
        
        # Process data
        data = fetch_neuron_data(neuron_name)
        if data is None:
            return Result.error(f"No data found for neuron: {neuron_name}")
        
        return Result.success(data)
        
    except Exception as e:
        return Result.error(f"Processing failed: {str(e)}")

# Usage
result = process_neuron_data("Dm4")
if result.is_success():
    data = result.value
    # Use data
else:
    error = result.error
    # Handle error
```

### Configuration Management

Use the type-safe configuration system:

```python
from quickpage.config import Config

# Load configuration
config = Config()

# Access configuration values
neuprint_server = config.neuprint.server
cache_ttl = config.cache.ttl
template_dir = config.templates.directory

# Override configuration
config = Config(override={
    'neuprint': {'server': 'custom-server.com'},
    'cache': {'enabled': False}
})
```

### Service Registration

Register services with the container:

```python
def create_page_generator():
    """Factory function to create a fully configured PageGenerator"""
    container = ServiceContainer()
    
    # Register core services
    container.register(DatabaseQueryService, 
                      lambda: DatabaseQueryService(config.neuprint))
    container.register(CacheService,
                      lambda: CacheService(config.cache))
    
    # Register analysis services
    container.register(ROIAnalysisService,
                      lambda: ROIAnalysisService(
                          container.get(DatabaseQueryService),
                          container.get(CacheService)
                      ))
    
    return PageGenerator(container)
```

### Type Safety

Use type hints throughout:

```python
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass

@dataclass
class AnalysisRequest:
    neuron_name: str
    side: Optional[SomaSide] = None
    include_partners: bool = True
    threshold_config: Optional[ThresholdConfig] = None

def analyze_neuron(request: AnalysisRequest) -> AnalysisResults:
    """Analyze a neuron with type-safe parameters"""
    pass
```

## Testing Strategy

### Test Structure

```
test/
├── unit/                 # Unit tests for individual components
│   ├── test_services/    # Service-specific tests
│   ├── test_models/      # Model tests
│   └── test_utils/       # Utility function tests
├── integration/          # Integration tests
│   ├── test_database/    # Database integration tests
│   ├── test_templates/   # Template rendering tests
│   └── test_workflows/   # End-to-end workflow tests
├── performance/          # Performance tests
└── fixtures/            # Test data and fixtures
```

### Unit Testing

```python
import pytest
from quickpage.services.roi_analysis_service import ROIAnalysisService

class TestROIAnalysisService:
    @pytest.fixture
    def service(self):
        mock_db = MockDatabaseService()
        mock_cache = MockCacheService()
        return ROIAnalysisService(mock_db, mock_cache)
    
    def test_analyze_rois_success(self, service):
        # Arrange
        neuron_data = create_test_neuron_data()
        
        # Act
        result = service.analyze_rois(neuron_data)
        
        # Assert
        assert result.is_success()
        assert len(result.value.central_brain_rois) > 0
    
    def test_analyze_rois_empty_data(self, service):
        # Arrange
        empty_data = pd.DataFrame()
        
        # Act
        result = service.analyze_rois(empty_data)
        
        # Assert
        assert result.is_error()
        assert "empty" in result.error.lower()
```

### Integration Testing

```python
def test_complete_page_generation():
    """Test the complete page generation workflow"""
    # Arrange
    generator = create_test_page_generator()
    
    # Act
    result = generator.generate_page("Dm4")
    
    # Assert
    assert result.is_success()
    
    # Verify output files exist
    output_dir = Path("test_output")
    assert (output_dir / "Dm4.html").exists()
    assert (output_dir / "static").exists()
    
    # Verify HTML content
    html_content = (output_dir / "Dm4.html").read_text()
    assert "Dm4" in html_content
    assert "neuron-page" in html_content
```

### Test Data Factory

```python
class TestDataFactory:
    @staticmethod
    def create_neuron_data(name: str = "TestNeuron") -> pd.DataFrame:
        """Create test neuron data"""
        return pd.DataFrame({
            'type': [name],
            'pre': [100],
            'post': [80],
            'roi': ['MB(R)'],
            'soma_side': ['R']
        })
    
    @staticmethod
    def create_connectivity_data() -> pd.DataFrame:
        """Create test connectivity data"""
        return pd.DataFrame({
            'pre_type': ['NeuronA'],
            'post_type': ['NeuronB'],
            'weight': [5],
            'roi': ['MB(R)']
        })
```

## Configuration

### Configuration Files

The system uses YAML-based configuration:

```yaml
# config.yaml
neuprint:
  server: "neuprint.janelia.org"
  dataset: "hemibrain:v1.2.1"
  
cache:
  enabled: true
  ttl: 3600
  max_memory_mb: 512
  
templates:
  directory: "templates"
  auto_reload: false
  
performance:
  chunk_size: 1000
  max_workers: 4
  
visualization:
  hex_size: 10.0
  spacing_factor: 1.1
  default_colors: "blues"
```

### Environment Variables

```bash
# .env file
NEUPRINT_TOKEN=your_token_here
NEUPRINT_SERVER=neuprint.janelia.org
QUICKPAGE_DEBUG=true
QUICKPAGE_CACHE_DIR=/tmp/quickpage_cache
```

### Configuration Validation

```python
@dataclass
class NeuPrintConfig:
    server: str
    dataset: str
    token: Optional[str] = None
    
    def __post_init__(self):
        if not self.server:
            raise ValueError("NeuPrint server must be specified")
        if not self.token:
            self.token = os.getenv('NEUPRINT_TOKEN')
```

## API Reference

### Core Classes

#### PageGenerator

```python
class PageGenerator:
    def __init__(self, config: Optional[Config] = None):
        """Initialize with optional configuration override"""
    
    def generate_page(self, neuron_name: str, 
                     side: Optional[SomaSide] = None) -> Result[str, str]:
        """Generate a single neuron page"""
    
    def generate_index(self) -> Result[str, str]:
        """Generate the index page"""
    
    def test_connection(self) -> Result[bool, str]:
        """Test NeuPrint connection"""
```

#### NeuronType

```python
class NeuronType:
    name: str
    side: Optional[SomaSide]
    data: Optional[pd.DataFrame]
    
    def get_cache_key(self) -> str
    def supports_soma_side(self) -> bool
    def get_neuron_count(self) -> int
    def get_synapse_stats(self) -> Dict[str, Any]
    def is_fetched(self) -> bool
```

#### Result Pattern

```python
class Result[T, E]:
    @staticmethod
    def success(value: T) -> "Result[T, E]"
    
    @staticmethod
    def error(error: E) -> "Result[T, E]"
    
    def is_success(self) -> bool
    def is_error(self) -> bool
    
    @property
    def value(self) -> T
    
    @property
    def error(self) -> E
    
    def map(self, func: Callable[[T], U]) -> "Result[U, E]"
    def flat_map(self, func: Callable[[T], "Result[U, E]"]) -> "Result[U, E]"
```

### Service Interfaces

#### DatabaseQueryService

```python
class DatabaseQueryService:
    def fetch_neuron_data(self, neuron_name: str) -> pd.DataFrame
    def fetch_connectivity_data(self, neuron_name: str) -> pd.DataFrame
    def fetch_roi_hierarchy(self) -> Dict[str, Any]
    def test_connection(self) -> bool
```

#### CacheService

```python
class CacheService:
    def get(self, key: str) -> Optional[Any]
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None
    def invalidate(self, key: str) -> None
    def clear_all(self) -> None
    def get_stats(self) -> Dict[str, Any]
```

## Troubleshooting

### Common Issues

#### NeuPrint Connection Failures

```python
# Test connection
result = generator.test_connection()
if result.is_error():
    print(f"Connection failed: {result.error}")
    
# Check token
token = os.getenv('NEUPRINT_TOKEN')
if not token:
    print("NEUPRINT_TOKEN environment variable not set")
```

#### Template Rendering Errors

```python
# Validate template syntax
def validate_template(template_path: Path) -> bool:
    try:
        env = Environment(loader=FileSystemLoader(template_path.parent))
        template = env.get_template(template_path.name)
        template.render({})  # Try empty context
        return True
    except Exception as e:
        print(f"Template error: {e}")
        return False
```

#### Cache Issues

```python
# Clear specific cache
cache_service.invalidate(f"neuron_data:{neuron_name}")

# Clear all caches
cache_service.clear_all()

# Check cache stats
stats = cache_service.get_stats()
print(f"Cache hit rate: {stats['hit_rate']:.2%}")
```

#### Performance Issues

```python
# Enable performance monitoring
generator.enable_performance_monitoring(True)

# Generate with profiling
result = generator.generate_page("Dm4")
metrics = generator.get_performance_metrics()

for operation, duration in metrics.items():
    print(f"{operation}: {duration:.2f}s")
```

### Debugging Tools

#### Log Configuration

```python
import logging

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Service-specific logging
logger = logging.getLogger('quickpage.services.database_query_service')
logger.setLevel(logging.DEBUG)
```

#### Development Mode

```python
# Create generator in development mode
config = Config(override={
    'templates': {'auto_reload': True},
    'cache': {'enabled': False},
    'debug': True
})
generator = PageGenerator(config)
```

## Contributing

### Code Style

- Follow PEP 8 for Python code
- Use type hints throughout
- Write docstrings for all public methods
- Use meaningful variable and function names
- Keep functions small and focused

### Pull Request Process

1. **Fork the repository** and create a feature branch
2. **Write tests** for new functionality
3. **Ensure all tests pass** (`pixi run test`)
4. **Update documentation** as needed
5. **Submit a pull request** with clear description

### Development Workflow

```bash
# Start development
git checkout -b feature/new-service
pixi install

# Make changes and test
pixi run test
pixi run lint

# Test with real data
quickpage generate -n Dm4

# Commit and push
git commit -m "Add new service for X"
git push origin feature/new-service
```

### Adding New Services

1. **Create service class** in `src/quickpage/services/`
2. **Add service interface** with clear method signatures
3. **Write comprehensive tests** in `test/unit/test_services/`
4. **Register service** in the service container
5. **Update documentation** in this guide

### Performance Considerations

- **Profile before optimizing**: Use the built-in performance tools
- **Cache appropriately**: Balance memory usage and performance
- **Use lazy loading**: Don't fetch data until needed
- **Minimize database queries**: Batch operations when possible
- **Test with realistic data**: Use actual NeuPrint datasets for testing

---

For more specific questions or detailed examples, please refer to the source code or open an issue on the project repository.