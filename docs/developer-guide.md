# QuickPage Developer Guide

A comprehensive guide for developers working on the QuickPage neuron visualization platform. This guide covers architecture, development setup, implementation details, and contribution guidelines.

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
- [Dataset Aliases](#dataset-aliases)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Dataset-Specific Implementations](#dataset-specific-implementations)
- [Feature Implementation Guides](#feature-implementation-guides)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Project Overview

QuickPage is a modern Python CLI tool that generates beautiful HTML pages for neuron types using data from NeuPrint. Built with Domain-Driven Design (DDD) architecture for maintainability and extensibility.

### Key Features

- **🔌 NeuPrint Integration**: Direct data fetching with intelligent caching
- **📱 Modern Web Interface**: Responsive design with advanced filtering
- **⚡ High Performance**: Up to 97.9% speed improvement with persistent caching
- **🧠 Multi-Dataset Support**: Automatic adaptation for CNS, Hemibrain, Optic-lobe, FAFB
- **🎨 Beautiful Reports**: Clean, accessible HTML pages with interactive features
- **🔍 Advanced Search**: Real-time filtering by cell count, neurotransmitter, brain regions

### Technology Stack

- **Backend**: Python 3.8+, asyncio for async processing
- **Data Layer**: NeuPrint API, persistent caching with SQLite
- **Frontend**: Modern HTML5, CSS3, vanilla JavaScript
- **Templates**: Jinja2 with custom filters and extensions
- **Testing**: pytest with comprehensive coverage
- **Package Management**: pixi for reproducible environments

## Architecture Overview

QuickPage follows Domain-Driven Design principles with clean architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│  CLI Commands, Templates, Static Assets, HTML Generation    │
├─────────────────────────────────────────────────────────────┤
│                    Application Layer                         │
│     Services, Orchestrators, Command Handlers, Factories    │
├─────────────────────────────────────────────────────────────┤
│                     Domain Layer                            │
│   Entities, Value Objects, Domain Services, Business Logic  │
├─────────────────────────────────────────────────────────────┤
│                  Infrastructure Layer                        │
│    Database, File System, External APIs, Caching, Adapters │
└─────────────────────────────────────────────────────────────┘
```

### Key Architectural Principles

- **Separation of Concerns**: Clear boundaries between layers
- **Dependency Inversion**: High-level modules don't depend on low-level modules
- **Single Responsibility**: Each component has one well-defined purpose
- **Open/Closed Principle**: Open for extension, closed for modification
- **Command/Query Separation**: Clear distinction between data modification and retrieval
- **Result Pattern**: Explicit error handling with Result<T> types
- **Service Container**: Dependency injection for loose coupling

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pixi package manager
- NeuPrint access token
- Git for version control

### Development Setup

1. **Clone the repository:**
```bash
git clone <repository-url>
cd quickpage
```

2. **Install dependencies:**
```bash
pixi install
```

3. **Set up environment:**
```bash
pixi run setup-env
# Edit .env file with your NeuPrint token
```

4. **Verify setup:**
```bash
pixi run quickpage test-connection
```

### CLI Changes in v2.0

**Simplified Page Generation**: The `--soma-side` parameter has been removed from all CLI commands. QuickPage now automatically detects available soma sides and generates appropriate pages:

```bash
# OLD (v1.x): Manual soma-side specification
pixi run quickpage generate -n Dm4 --soma-side left

# NEW (v2.0): Automatic detection and generation
pixi run quickpage generate -n Dm4
# Automatically generates: Dm4_L.html, Dm4_R.html, Dm4.html (if multi-hemisphere)
```

**Benefits**:
- **Simplified UX**: No need to understand soma-side concepts
- **Comprehensive Output**: Always generates optimal page set
- **Error Reduction**: Eliminates invalid soma-side specifications
- **Future-Proof**: Adapts to any neuron type's data distribution

### Development Commands

QuickPage uses pixi for task management with separate commands for different types of work:

#### Testing Tasks

**Unit Tests** - Fast, isolated tests for individual components:
```bash
# Run all unit tests
pixi run unit-test

# Run unit tests with verbose output
pixi run unit-test-verbose

# Examples with specific files/tests:
pixi run unit-test-verbose test/test_dataset_adapters.py
pixi run unit-test-verbose test/test_dataset_adapters.py::TestMaleCNSAliasUnit
```

**Integration Tests** - End-to-end tests for component interactions:
```bash
# Run all integration tests
pixi run integration-test

# Run integration tests with verbose output
pixi run integration-test-verbose

# Examples:
pixi run integration-test-verbose test/test_male_cns_integration.py
```

**General Testing**:
```bash
# Run all tests (unit + integration)
pixi run test

# Run all tests with verbose output
pixi run test-verbose

# Run tests with coverage reporting
pixi run test-coverage
```

#### Code Quality Tasks

```bash
# Format code with ruff
pixi run format

# Check code quality and linting
pixi run check
```

#### Content Generation Tasks

```bash
# Clean generated output
pixi run clean-output

# Fill processing queue with all neuron types
pixi run fill-all

# Process all items in queue
pixi run pop-all

# Fill queue with specific neuron type
pixi run fill-type <neuron_type>

# Create index/list page
pixi run create-list

# Complete workflow: clean → fill → process → index
pixi run create-all-pages
```

#### Development Support Tasks

```bash
# Setup development environment
pixi run setup-env

# Get help for the quickpage CLI
pixi run help

# Generate test dataset (normal set)
pixi run test-set

# Generate test dataset without index
pixi run test-set-no-index

# Extract and fill from config
pixi run extract-and-fill [config_file] [test_category]
```

#### Task Usage Patterns

**Development Workflow**:
```bash
# 1. Setup environment (first time)
pixi run setup-env

# 2. Run tests during development
pixi run unit-test-verbose

# 3. Check code quality
pixi run format
pixi run check

# 4. Run full test suite before commit
pixi run test-verbose
```

**Content Generation Workflow**:
```bash
# Complete page generation
pixi run create-all-pages

# Or step by step:
pixi run clean-output
pixi run fill-all
pixi run pop-all
pixi run create-list
```

**Testing Workflow**:
```bash
# Fast feedback during development
pixi run unit-test

# Comprehensive testing before release
pixi run integration-test
pixi run test-coverage
```

#### Performance Notes

- **Unit tests**: Complete in ~1 second
- **Integration tests**: May take several seconds due to I/O
- **Full test suite**: Typically < 10 seconds
- **Page generation**: Varies based on dataset size

#### Environment Requirements

Most development tasks require the `dev` environment, which is automatically used by the configured tasks. Some tasks require authentication:
- `NEUPRINT_TOKEN` - Required for database integration tests
- Set in `.env` file or environment variables

## Core Components

### PageGenerator

The main orchestrator that coordinates page generation across all services.

```python
class PageGenerator:
    def __init__(
        self,
        config: Config,
        output_dir: str,
        queue_service=None,
        cache_manager=None,
        services=None,
        container=None,
        copy_mode: str = "check_exists",
    ):
        """Initialize the page generator with configuration and services."""
        self.config = config
        self.output_dir = output_dir
        self.copy_mode = copy_mode
        # Initialize services from container or services dict
        if container:
            self._init_from_container(container)
        elif services:
            self._init_from_services(services)
        else:
            # Use service factory as fallback
            pass

    def generate_page_unified(self, request: PageGenerationRequest):
        """Generate an HTML page using the unified orchestrator workflow."""
        return self.orchestrator.generate_page(request)

    @staticmethod
    def generate_filename(neuron_type: str, soma_side: str) -> str:
        """Generate HTML filename for a neuron type and soma side."""
        return FileService.generate_filename(neuron_type, soma_side)

    def clean_dynamic_files_for_neuron(
        self, neuron_type: str, soma_side: str = None
    ) -> bool:
        """Clean dynamic files for a specific neuron type."""
        pass
```

### PageGenerationOrchestrator

Coordinates the complex page generation workflow:

```python
class PageGenerationOrchestrator:
    def generate_page(self, request: PageGenerationRequest) -> Result[GeneratedPage]:
        # 1. Validate request
        # 2. Fetch neuron data
        # 3. Process connectivity
        # 4. Generate visualizations
        # 5. Render templates
        # 6. Save outputs
        pass
```

### Neuron Type Domain Models

The system uses several domain models for representing neuron types:

```python
class NeuronTypeName:
    """Value object representing a neuron type name."""
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("NeuronTypeName cannot be empty")

class NeuronTypeConnectivity:
    """Represents connectivity data for a neuron type."""
    type_name: NeuronTypeName
    upstream_partners: List[ConnectivityPartner] = field(default_factory=list)
    downstream_partners: List[ConnectivityPartner] = field(default_factory=list)

class NeuronTypeStatistics:
    """Statistics for a neuron type."""
    type_name: NeuronTypeName
    total_count: int = 0
    soma_side_counts: Dict[str, int] = field(default_factory=dict)
    synapse_stats: Dict[str, float] = field(default_factory=dict)
    roi_stats: Dict[str, Dict[str, int]] = field(default_factory=dict)
    connectivity: Optional[NeuronTypeConnectivity] = None
    computed_at: datetime = field(default_factory=datetime.now)

class NeuronTypeConfig:
    """Neuron type configuration."""
    name: str
    description: str = ""
    query_type: str = "type"
    soma_side: str = "combined"
```

## Service Architecture

### Core Services

The application is built around a comprehensive service architecture:

#### Data Services
- **NeuPrintConnector**: Database connection and query execution
- **DatabaseQueryService**: Structured query building and execution
- **CacheService**: Multi-level caching with persistence
- **DataProcessingService**: Data transformation and validation

#### Analysis Services
- **PartnerAnalysisService**: Connectivity analysis and partner identification
- **ROIAnalysisService**: Region of interest analysis and statistics
- **ConnectivityCombinationService**: Automatic L/R hemisphere combination for connectivity
- **ROICombinationService**: Automatic L/R hemisphere combination for ROI data

#### Content Services
- **TemplateContextService**: Template data preparation and processing
- **ResourceManagerService**: Static asset management
- **NeuroglancerJSService**: Neuroglancer integration and URL generation
- **URLGenerationService**: Dynamic URL creation
- **CitationService**: Citation data management and HTML link generation
- **CitationLoggingService**: Automatic tracking and logging of missing citations

#### Infrastructure Services
- **FileService**: File operations and path management
- **ConfigurationService**: Configuration loading and validation
- **LoggingService**: Structured logging and monitoring

### Service Container Pattern

Dependency injection using a service container:

```python
class ServiceContainer:
    def __init__(self, config, copy_mode: str = "check_exists"):
        """Initialize service container.
        
        Args:
            config: Configuration object
            copy_mode: Static file copy mode ("check_exists" for pop, "force_all" for generate)
        """
        self.config = config
        self.copy_mode = copy_mode
        self._services = {}
        # Service instance storage
        self._neuprint_connector = None
        self._page_generator = None
        self._cache_manager = None
        self._template_manager = None
        self._resource_manager_v3 = None

    def _get_or_create_service(self, service_name: str, factory_func):
        """Generic method to get or create a service."""
        if service_name not in self._services:
            self._services[service_name] = factory_func()
        return self._services[service_name]

    @property
    def neuprint_connector(self):
        """Get or create NeuPrint connector."""
        def create():
            from ..neuprint_connector import NeuPrintConnector
            return NeuPrintConnector(self.config)
        return self._get_or_create_service("neuprint_connector", create)

    @property
    def page_generator(self):
        """Get or create page generator using factory."""
        def create():
            from .page_generator_service_factory import PageGeneratorServiceFactory
            return PageGeneratorServiceFactory.create_page_generator(
                self.config, self.config.output.directory, self.queue_service,
                self.cache_manager, self.copy_mode
            )
        return self._get_or_create_service("page_generator", create)

    @property 
    def cache_manager(self):
        """Get or create cache manager."""
        def create():
            from ..cache import create_cache_manager
            return create_cache_manager(self.config.output.directory)
        return self._get_or_create_service("cache_manager", create)

    def cleanup(self):
        """Clean up services and resources."""
        self._services.clear()
### Service Development Pattern

Standard pattern for implementing new services:

```python
class ExampleService:
    def __init__(self, config: Config, cache_service: CacheService):
        self.config = config
        self.cache = cache_service
        self.logger = logging.getLogger(__name__)

    def process_data(self, input_data: Dict[str, Any]) -> Result[ProcessedData]:
        """Main service method with error handling."""
        try:
            # Validate input
            validation_result = self._validate_input(input_data)
            if not validation_result.is_success():
                return validation_result

            # Process data
            processed = self._do_processing(input_data)
            return Result.success(processed)

        except Exception as e:
            self.logger.error(f"Processing failed: {e}")
            return Result.failure(f"Processing error: {e}")

    def _validate_input(self, data: Dict) -> Result[bool]:
        """Input validation logic."""
        pass

    def _do_processing(self, data: Dict) -> ProcessedData:
        """Core processing logic."""
        pass
```

## Data Processing Pipeline

### Dataset Adapters

Different datasets require different data processing approaches:

```python
class DatasetAdapter:
    """Base adapter for dataset-specific processing."""

    def __init__(self, dataset_info: DatasetInfo, roi_strategy: RoiQueryStrategy):
        self.dataset_info = dataset_info
        self.roi_strategy = roi_strategy

    def extract_soma_side(self, neurons_df: pd.DataFrame) -> pd.DataFrame:
        """Extract soma side information from neuron data."""
        pass

    def normalize_columns(self, neurons_df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names and types."""
        pass

    def get_synapse_counts(self, neurons_df: pd.DataFrame) -> Tuple[int, int]:
        """Get synapse counts from dataset."""
        pass

    def filter_by_soma_side(self, neurons_df: pd.DataFrame, soma_side: str) -> pd.DataFrame:
        """Filter neurons by soma side."""
        pass

    def categorize_rois(self, roi_data: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize ROI data by region type."""
        pass

class CNSAdapter(DatasetAdapter):
    def __init__(self):
        dataset_info = DatasetInfo(
            name="cns",
            soma_side_column="somaSide",
            pre_synapse_column="pre",
            post_synapse_column="post",
            roi_columns=["inputRois", "outputRois"],
        )
        roi_strategy = CNSRoiQueryStrategy()
        super().__init__(dataset_info, roi_strategy)

    def extract_soma_side(self, neurons_df: pd.DataFrame) -> pd.DataFrame:
        """CNS has a dedicated somaSide column."""
        neurons_df = neurons_df.copy()
        if "somaSide" in neurons_df.columns:
            neurons_df["somaSide"] = neurons_df["somaSide"].fillna("U")
            return neurons_df
        else:
            neurons_df["somaSide"] = "U"  # Unknown
            return neurons_df

    def normalize_columns(self, neurons_df: pd.DataFrame) -> pd.DataFrame:
        """CNS columns are already in standard format."""
        return neurons_df

    def get_synapse_counts(self, neurons_df: pd.DataFrame) -> Tuple[int, int]:
        """Get synapse counts from CNS dataset."""
        pre_total = neurons_df[self.dataset_info.pre_synapse_column].sum() if self.dataset_info.pre_synapse_column in neurons_df.columns else 0
        post_total = neurons_df[self.dataset_info.post_synapse_column].sum() if self.dataset_info.post_synapse_column in neurons_df.columns else 0
        return int(pre_total), int(post_total)

class HemibrainAdapter(DatasetAdapter):
    def __init__(self):
        dataset_info = DatasetInfo(
            name="hemibrain",
            soma_side_column="somaSide",
            pre_synapse_column="pre",
            post_synapse_column="post",
            roi_columns=["inputRois", "outputRois"],
        )
        roi_strategy = HemibrainRoiQueryStrategy()
        super().__init__(dataset_info, roi_strategy)

    def extract_soma_side(self, neurons_df: pd.DataFrame) -> pd.DataFrame:
        """Hemibrain typically has somaSide column."""
        if "somaSide" in neurons_df.columns:
            return neurons_df
        else:
            neurons_df = neurons_df.copy()
            if "instance" in neurons_df.columns:
                # Extract from instance names like "neuronType_R" or "neuronType_L"
                neurons_df["somaSide"] = neurons_df["instance"].str.extract(r"_([LR])$")[0]
                neurons_df["somaSide"] = neurons_df["somaSide"].fillna("U")
            else:
                neurons_df["somaSide"] = "U"
            return neurons_df

    def normalize_columns(self, neurons_df: pd.DataFrame) -> pd.DataFrame:
        """Normalize Hemibrain columns."""
        return neurons_df

    def get_synapse_counts(self, neurons_df: pd.DataFrame) -> Tuple[int, int]:
        """Get synapse counts from Hemibrain dataset."""
        pre_total = neurons_df[self.dataset_info.pre_synapse_column].sum() if self.dataset_info.pre_synapse_column in neurons_df.columns else 0
        post_total = neurons_df[self.dataset_info.post_synapse_column].sum() if self.dataset_info.post_synapse_column in neurons_df.columns else 0
        return int(pre_total), int(post_total)
```

### Data Flow

```
Raw NeuPrint Data → Dataset Adapter → Cache Layer → Service Processing → Template Rendering
```

1. **Data Extraction**: NeuPrint queries return raw database results
2. **Adaptation**: Dataset-specific adapters normalize the data
3. **Caching**: Processed data is cached for performance
4. **Analysis**: Services perform connectivity and ROI analysis with CV calculation
5. **Rendering**: Template system generates final HTML

### Connectivity Data Processing with CV

The connectivity processing pipeline includes statistical analysis:

```python
# 1. Raw connectivity query collects individual partner weights
upstream_query = """
MATCH (upstream:Neuron)-[c:ConnectsTo]->(target:Neuron)
WHERE target.bodyId IN {body_ids}
RETURN upstream.type, upstream.somaSide, c.weight, upstream.bodyId
"""

# 2. Group and aggregate with CV calculation
for record in query_results:
    partner_id = record["partner_bodyId"]
    type_soma_data[key]["partner_weights"][partner_id] += weight

# 3. Calculate coefficient of variation
partner_weights = list(data["partner_weights"].values())
connections_per_neuron = [w / len(body_ids) for w in partner_weights]
mean_conn = sum(connections_per_neuron) / len(connections_per_neuron)
variance = sum((x - mean_conn) ** 2 for x in connections_per_neuron) / len(connections_per_neuron)
cv = (variance ** 0.5) / mean_conn if mean_conn > 0 else 0

# 4. Include in partner data structure
partner_data["coefficient_of_variation"] = round(cv, 3)
```
```

### Automatic Page Generation System

QuickPage v2.0 introduces automatic page generation that eliminates the need for manual soma-side specification. The system intelligently analyzes neuron data and generates the optimal set of pages.

#### Architecture Overview

```python
class SomaDetectionService:
    """Service for automatic soma side detection and multi-page generation."""

    async def generate_pages_with_auto_detection(self, command: GeneratePageCommand) -> Result[str, str]:
        """Generate multiple pages based on available soma sides."""
        # 1. Analyze soma side distribution
        soma_counts = await self.get_soma_side_distribution(neuron_type)

        # 2. Determine which pages to generate
        should_generate_combined = self._should_generate_combined_page(soma_counts)

        # 3. Generate appropriate pages
        generated_files = []

        # Generate side-specific pages
        for side in ['left', 'right', 'middle']:
            if soma_counts.get(side, 0) > 0:
                page_result = await self._generate_page_for_soma_side(command, neuron_type, side)
                if page_result.is_ok():
                    generated_files.append(page_result.unwrap())

        # Generate combined page if appropriate
        if should_generate_combined:
            combined_result = await self._generate_page_for_soma_side(command, neuron_type, "combined")
            if combined_result.is_ok():
                generated_files.append(combined_result.unwrap())

        return Ok(", ".join(generated_files))
```

#### Detection Logic

The system uses sophisticated logic to determine which pages to generate:

```python
def _should_generate_combined_page(self, soma_counts: Dict[str, int]) -> bool:
    """Determine if a combined page should be generated."""
    left_count = soma_counts.get("left", 0)
    right_count = soma_counts.get("right", 0)
    middle_count = soma_counts.get("middle", 0)
    total_count = soma_counts.get("total", 0)

    # Count sides with data
    sides_with_data = sum(1 for count in [left_count, right_count, middle_count] if count > 0)

    # Calculate unknown soma side count
    unknown_count = total_count - left_count - right_count - middle_count

    # Generate combined page if:
    # 1. Multiple sides have data, OR
    # 2. No soma side data exists but neurons are present, OR
    # 3. Unknown soma sides exist alongside any assigned side
    should_generate_combined = (
        sides_with_data > 1
        or (sides_with_data == 0 and total_count > 0)
        or (unknown_count > 0 and sides_with_data > 0)
    )

    # Override: Don't generate combined page for single-side neuron types
    if sides_with_data == 1 and unknown_count == 0:
        should_generate_combined = False

    return should_generate_combined
```

#### Page Generation Scenarios

**Scenario 1: Multi-hemisphere neuron type (e.g., Dm4)**
- Data: 45 left neurons, 42 right neurons
- Generated pages: `Dm4_L.html`, `Dm4_R.html`, `Dm4.html` (combined)
- Rationale: Multiple hemispheres warrant both individual and combined views

**Scenario 2: Single-hemisphere neuron type (e.g., LC10)**
- Data: 0 left neurons, 23 right neurons
- Generated pages: `LC10_R.html` only
- Rationale: No combined page needed for single-hemisphere types

**Scenario 3: Mixed data with unknowns**
- Data: 15 left neurons, 8 unknown-side neurons
- Generated pages: `NeuronType_L.html`, `NeuronType.html` (combined)
- Rationale: Unknown neurons justify a combined view alongside specific side

**Scenario 4: No soma side information**
- Data: 30 neurons, all unknown sides
- Generated pages: `NeuronType.html` (combined only)
- Rationale: Without hemisphere data, only combined view is meaningful

#### Integration with Legacy Code

The automatic system maintains backward compatibility while removing user-facing complexity:

```python
# OLD: Manual soma-side specification
command = GeneratePageCommand(
    neuron_type=NeuronTypeName("Dm4"),
    soma_side=SomaSide.from_string("left"),  # REMOVED
    output_directory=output_dir
)

# NEW: Automatic detection
command = GeneratePageCommand(
    neuron_type=NeuronTypeName("Dm4"),
    # soma_side parameter removed - system auto-detects
    output_directory=output_dir
)
```

#### Performance Considerations

- **Data Analysis**: Single query analyzes all soma sides simultaneously
- **Parallel Generation**: Individual pages generated concurrently when possible
- **Cache Efficiency**: Shared data fetching across multiple page generations
- **Memory Management**: Automatic cleanup after page generation completes

### ROI Query Strategies

Different strategies for querying region of interest data:

```python
class ROIQueryStrategy:
    def query_central_brain_rois(self, neuron_types: List[str]) -> List[Dict]:
        """Query ROIs specific to central brain regions."""
        pass

    def categorize_rois(self, roi_data: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize ROI data by region type."""
        pass
```

## Visualization System

### Eyemap Visualization

The visualization system uses specialized eyemap generators and coordinate systems. The actual implementation uses:

- `HexagonCoordinateSystem` for coordinate transformations
- Eyemap generators in the `visualization` module
- SVG generation through template rendering
- Data-driven grid layouts based on neuron positioning data

### Coordinate System

The `HexagonCoordinateSystem` class provides coordinate conversion methods:

```python
class HexagonCoordinateSystem:
    def hex_to_axial(self, hex1: int, hex2: int, min_hex1: int = 0, min_hex2: int = 0) -> AxialCoordinate:
        """Convert hexagonal coordinates to axial coordinates."""
        # Normalize coordinates
        hex1_coord = hex1 - min_hex1
        hex2_coord = hex2 - min_hex2
        
        # Convert to axial coordinates
        q = -(hex1_coord - hex2_coord) - 3
        r = -hex2_coord
        
        return AxialCoordinate(q=q, r=r)

    def axial_to_pixel(self, axial: AxialCoordinate, mirror_side: Optional[str] = None) -> PixelCoordinate:
        """Convert axial coordinates to pixel coordinates with optional mirroring."""
        x = self.effective_size * (3/2 * axial.q)
        y = self.effective_size * (math.sqrt(3)/2 * axial.q + math.sqrt(3) * axial.r)

        # Apply mirroring if needed
        if mirror_side:
            if hasattr(mirror_side, "value"):
                # It's a SomaSide enum
                mirror_side_str = mirror_side.value
            else:
                # It's already a string
                mirror_side_str = str(mirror_side)

            if mirror_side_str.lower() in ["left", "l"]:
                x = -x

        return PixelCoordinate(x=x, y=y)
```

### Color Mapping

Color mapping is handled by visualization services and eyemap generators. The system supports various color schemes for data visualization, but the specific implementation depends on the visualization type and data being displayed.

## Template System

### Template Architecture

Jinja2-based template system with custom extensions:

```python
class TemplateStrategy:
    def load_template(self, template_path: str) -> Any:
        """Load a template from the given path."""
        pass

    def render_template(self, template: Any, context: Dict[str, Any]) -> str:
        """Render a template with the given context."""
        pass
    
    def validate_template(self, template_path: str) -> bool:
        """Validate that a template is syntactically correct."""
        pass
    
    def list_templates(self, template_dir: Path) -> List[str]:
        """List all templates in the given directory."""
        pass
    
    def get_template_dependencies(self, template_path: str) -> List[str]:
        """Get dependencies (includes, extends, etc.) for a template."""
        pass
    
    def supports_template(self, template_path: str) -> bool:
        """Check if this strategy can handle the given template."""
        pass

class JinjaTemplateStrategy(TemplateStrategy):
    def __init__(self, template_dirs: List[str], auto_reload: bool = True, cache_size: int = 400):
        """Initialize Jinja template strategy with multiple template directories."""
        self.template_dirs = [Path(d) for d in template_dirs]
        self.auto_reload = auto_reload
        self.cache_size = cache_size
        self._environment = None
        self._custom_filters = {}
        self._custom_globals = {}

    def _ensure_environment(self) -> Environment:
        """Ensure Jinja2 environment is initialized."""
        if self._environment is None:
            loader = FileSystemLoader([str(d) for d in self.template_dirs])
            self._environment = Environment(
                loader=loader,
                auto_reload=self.auto_reload,
                cache_size=self.cache_size
            )
        return self._environment

```

### Template Structure

```
templates/
├── base.html.jinja              # Base layout template
├── neuron-page.html.jinja       # Individual neuron type pages
├── index.html.jinja             # Main index with search
├── types.html.jinja             # Neuron type listing
└── static/
    ├── js/
    │   ├── neuroglancer-url-generator.js.jinja
    │   └── neuron-page.js.jinja
    └── css/
        └── neuron-page.css.jinja
```

### Template Context

Structured data passed to templates:

```python
class TemplateContext:
    def __init__(self):
        self.neuron_data = {}
        self.connectivity_data = {}
        self.roi_data = {}
        self.visualization_data = {}
        self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for template rendering."""
        pass
```

### Connectivity Table Template Processing

The connectivity template handles CV display with proper fallbacks:

```html
<!-- Upstream connectivity table with CV column -->
<table id="upstream-table" class="display">
    <thead>
        <tr>
            <th>upstream<br />partner</th>
            <th title="number of partner neurons">#</th>
            <th title="neurotransmitter">NT</th>
            <th title="connections per {{ neuron_data.type }}">
                <span style="text-decoration:underline #333 2px;">conns</span><br />
                {{ neuron_data.type }}
            </th>
            <th title="Coefficient of variation for connections per neuron">CV</th>
            <th title="Percentage of Input">%<br/>In</th>
        </tr>
    </thead>
    <tbody>
        {% for partner in connectivity.upstream %}
        <tr id="u{{ loop.index0 }}">
            <td class="p-c">{{ partner.get('type', 'Unknown') }}</td>
            <td>{{ partner.get('partner_neuron_count', 0) }}</td>
            <td>{{ partner.get('neurotransmitter', 'Unknown') }}</td>
            <td>{{ partner.get('connections_per_neuron', 0) | format_conn_count }}</td>
            <td>{{ partner.get('coefficient_of_variation', 0) }}</td>
            <td>{{ partner.get('percentage', 0) | format_percentage }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

**CV Template Features**:
- Safe fallback: `partner.get('coefficient_of_variation', 0)` returns 0 if CV not available
- Descriptive tooltip explains CV meaning for users
- Positioned between connections and percentage columns for logical flow
- Same implementation for both upstream and downstream tables

### Custom Template Filters

The template system uses utility services for number formatting:

```python
# Number formatting is handled by utility services
# Available through template context via services like:
# - number_formatter.format_number()
# - percentage_formatter.format_percentage()
# - synapse_formatter (for synapse counts)
```


## Performance & Caching

### Multi-Level Cache System

QuickPage implements a sophisticated caching system with multiple levels:

```python
class CacheService:
    def __init__(self, config: CacheConfig):
        self.config = config
        self.memory_cache = {}
        self.file_cache = FileCacheBackend(config.cache_dir)
        self.database_cache = DatabaseCacheBackend(config.db_path)

    def get_cached_data(self, cache_key: str, fetch_func: Callable) -> Any:
        """Multi-level cache retrieval with fallback."""
        # Level 1: Memory cache
        if cache_key in self.memory_cache:
            return self.memory_cache[cache_key]

        # Level 2: File cache
        file_data = self.file_cache.get(cache_key)
        if file_data is not None:
            self.memory_cache[cache_key] = file_data
            return file_data

        # Level 3: Database cache
        db_data = self.database_cache.get(cache_key)
        if db_data is not None:
            self.memory_cache[cache_key] = db_data
            self.file_cache.set(cache_key, db_data)
            return db_data

        # Cache miss - fetch and populate
        fresh_data = fetch_func()
        self._populate_all_levels(cache_key, fresh_data)
        return fresh_data
```

### Cache Types

- **Memory Cache**: In-memory LRU cache for immediate access
- **File Cache**: Persistent file-based cache surviving process restarts
- **Database Cache**: SQLite-based cache for complex queries
- **HTTP Cache**: Response caching for NeuPrint API calls

### Performance Optimizations

Key optimizations implemented:

- **Database Connection Pooling**: Reuse connections across requests
- **Batch Query Processing**: Combine multiple queries into single requests
- **Lazy Loading**: Load data only when needed
- **Asynchronous Processing**: Non-blocking I/O for improved throughput
- **Compressed Storage**: Gzip compression for cached data

### Performance Monitoring

```python
class PerformanceMonitor:
    def __init__(self):
        self.timers = {}
        self.metrics = defaultdict(list)

    def start_timer(self, operation: str):
        """Start timing an operation."""
        self.timers[operation] = time.time()

    def end_timer(self, operation: str) -> float:
        """End timing and record duration."""
        if operation in self.timers:
            duration = time.time() - self.timers[operation]
            self.metrics[operation].append(duration)
            del self.timers[operation]
            return duration
        return 0.0
```

## Development Patterns

### Error Handling

Consistent error handling using the Result pattern:

```python
def process_neuron_data(neuron_type: str) -> Result[NeuronData]:
    """Process neuron data with comprehensive error handling."""
    try:
        # Validate input
        if not neuron_type or not isinstance(neuron_type, str):
            return Result.failure("Invalid neuron type provided")

        # Fetch data
        data_result = fetch_neuron_data(neuron_type)
        if not data_result.is_success():
            return data_result

        # Process data
        processed = process_data(data_result.value)
        return Result.success(processed)

    except DatabaseConnectionError as e:
        logger.error(f"Database connection failed: {e}")
        return Result.failure(f"Database unavailable: {e}")
    except ValidationError as e:
        logger.warning(f"Data validation failed: {e}")
        return Result.failure(f"Invalid data: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error processing {neuron_type}")
        return Result.failure(f"Processing failed: {e}")
```

### Configuration Management

Hierarchical configuration system:

```python
@dataclass
class Config:
    neuprint: NeuPrintConfig
    cache: CacheConfig
    output: OutputConfig
    html: HtmlConfig

    @classmethod
    def from_file(cls, config_path: str) -> 'Config':
        """Load configuration from YAML file."""
        pass

    @classmethod
    def from_env(cls) -> 'Config':
        """Load configuration from environment variables."""
        pass
```

### Service Registration

Dependency injection setup:

```python
def create_page_generator(config: Config) -> PageGenerator:
    """Factory function to create fully configured PageGenerator."""
    container = ServiceContainer()

    # Register core services
    container.register('cache_service',
                      lambda: CacheService(config.cache))
    container.register('database_service',
                      lambda: DatabaseQueryService(config.neuprint))

    # Register analysis services
    container.register('connectivity_service',
                      lambda: PartnerAnalysisService(
                          container.get('database_service'),
                          container.get('cache_service')
                      ))

    # Register content services
    container.register('template_service',
                      lambda: TemplateContextService(config))

    return PageGenerator(config, container)
```

### Type Safety

Using type hints and validation:

```python
@dataclass
class AnalysisRequest:
    neuron_type: str
    include_connectivity: bool = True
    include_rois: bool = True

def analyze_neuron(request: AnalysisRequest) -> Result[AnalysisResult]:
    """Analyze neuron with type-safe parameters."""
    pass
```

## Testing Strategy

### Overview

QuickPage uses a comprehensive testing strategy with clear separation between unit and integration tests. Tests are organized by type and use pytest markers for selective execution.

### Test Categories

#### Unit Tests (`@pytest.mark.unit`)
Fast, isolated tests that focus on individual components without external dependencies.

**Characteristics:**
- Fast execution (< 1 second total)
- No file I/O operations
- No external service dependencies
- Test single methods/functions
- Mock external dependencies when needed

**Example:**
```python
@pytest.mark.unit
class TestDatasetAdapterFactory:
    """Unit tests for DatasetAdapterFactory."""

    @pytest.mark.unit
    def test_male_cns_alias_resolution(self):
        """Test that male-cns resolves to cns adapter."""
        adapter = DatasetAdapterFactory.create_adapter("male-cns:v0.9")
        assert isinstance(adapter, CNSAdapter)
        assert adapter.dataset_info.name == "cns"
```

#### Integration Tests (`@pytest.mark.integration`)
End-to-end tests that verify component interactions and real-world scenarios.

**Characteristics:**
- Slower execution (may involve file I/O)
- Test component interactions
- Uses real configuration files
- Tests end-to-end workflows
- May use temporary files/resources

**Example:**
```python
@pytest.mark.integration
class TestMaleCNSIntegration:
    """Integration tests for male-cns dataset configuration."""

    @pytest.mark.integration
    def test_config_with_male_cns_creates_cns_adapter(self):
        """Integration test: config file with male-cns creates CNS adapter."""
        # Create temporary config file
        config_content = """
neuprint:
  server: "neuprint-cns.janelia.org"
  dataset: "male-cns:v0.9"
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml") as f:
            f.write(config_content)
            config = Config.from_file(f.name)

            # Test component integration
            connector = NeuPrintConnector(config)
            assert isinstance(connector.dataset_adapter, CNSAdapter)
```

### Test Execution

#### Pixi Tasks
```bash
# Run unit tests only (fast feedback)
pixi run unit-test

# Run unit tests with verbose output
pixi run unit-test-verbose

# Run integration tests only
pixi run integration-test

# Run integration tests with verbose output
pixi run integration-test-verbose

# Run all tests
pixi run test

# Run all tests with verbose output
pixi run test-verbose

# Run tests with coverage
pixi run test-coverage
```

#### Selective Execution
```bash
# Run specific test file
pixi run unit-test-verbose test/test_dataset_adapters.py

# Run specific test class
pixi run test test/test_dataset_adapters.py::TestMaleCNSAliasUnit

# Run specific test method
pixi run test test/test_dataset_adapters.py::TestMaleCNSAliasUnit::test_male_cns_base_name_alias_resolution
```

### Test Structure

Current test organization:

```
test/
├── test_dataset_adapters.py        # Unit tests for factory and adapters
│   ├── TestDatasetAdapterFactory   # General factory tests
│   └── TestMaleCNSAliasUnit       # Focused unit tests for aliases
├── test_male_cns_integration.py    # Integration tests
│   └── TestMaleCNSIntegration     # End-to-end integration scenarios
├── services/                       # Service-specific tests
├── visualization/                  # Visualization component tests
└── fixtures/                      # Test data and fixtures
```

### Naming Conventions

- **Unit tests**: Focus on single method/function behavior
  - Format: `test_[specific_behavior]`
  - Example: `test_male_cns_base_name_alias_resolution`


### Testing Implementation

Testing is implemented using pytest with fixtures and factories. The actual test classes use the existing service implementations rather than mock services like `ROIAnalysisService` (which doesn't exist in the codebase).

Tests focus on:
- Service integration testing
- Template rendering validation
- Data processing pipeline verification
- Configuration loading and validation


### Test Data and Fixtures

#### Unit Test Data
- Hardcoded test values for predictable behavior
- Use of mock objects for external dependencies
- Parameterized tests for multiple similar scenarios

#### Integration Test Data
- Temporary configuration files created during test execution
- Real project configuration files when available
- Cleanup of temporary resources after tests

### Dataset Alias Testing

Special focus on testing dataset alias functionality:

```python
# Unit tests for alias resolution
def test_male_cns_versioned_alias_resolution(self):
    """Test versioned male-cns aliases resolve correctly."""
    test_cases = ["male-cns:v0.9", "male-cns:v1.0", "male-cns:latest"]

    for dataset_name in test_cases:
        adapter = DatasetAdapterFactory.create_adapter(dataset_name)
        assert isinstance(adapter, CNSAdapter)
        assert adapter.dataset_info.name == "cns"

# Integration tests for end-to-end workflows
def test_end_to_end_male_cns_workflow(self):
    """Test complete workflow with male-cns configuration."""
    # Tests config loading → adapter creation → service integration
```

### Debugging Failed Tests

#### Unit Test Failures
```bash
# Run specific failing test with verbose output
pixi run unit-test-verbose test/path/to/test.py::TestClass::test_method

# Check test markers
pytest --markers
```

#### Integration Test Failures
```bash
# Check environment setup
pixi run setup-env

# Verify token configuration
echo $NEUPRINT_TOKEN

# Run with verbose debugging
pixi run integration-test-verbose --tb=long
```

### Test Data Creation

Test data creation is handled through existing factories and fixtures in the test suite, focusing on integration with actual services rather than mock data factories.

## Configuration

### Configuration Files

YAML-based configuration system:

```yaml
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
  hex_size: 20
  spacing_factor: 1.1
  default_colors: ["#1f77b4", "#ff7f0e", "#2ca02c"]
```

### Environment Variables

Environment variable support for sensitive configuration:

- `NEUPRINT_APPLICATION_CREDENTIALS`: NeuPrint API token
- `QUICKPAGE_CONFIG_PATH`: Custom configuration file path
- `QUICKPAGE_CACHE_DIR`: Cache directory override
- `QUICKPAGE_DEBUG`: Enable debug logging
- `QUICKPAGE_PROFILE`: Enable performance profiling

### Configuration Validation

Automatic validation with clear error messages:

```python
@dataclass
class NeuPrintConfig:
    server: str
    dataset: str
    token: Optional[str] = None

    def __post_init__(self):
        if not self.server:
            raise ValueError("NeuPrint server URL is required")
        if not self.dataset:
            raise ValueError("Dataset name is required")
```

## API Reference

### Core Classes

#### PageGenerator

Main interface for page generation:

```python
class PageGenerator:
    def __init__(self, config: Config, container: ServiceContainer):
        """Initialize with configuration and service container."""
        pass

    def generate_page(self, neuron_type: str) -> Result[GeneratedPage]:
        """Generate complete neuron type pages with automatic detection."""
        pass

    def generate_index(self) -> Result[str]:
        """Generate main index page."""
        pass

    def test_connection(self) -> Result[bool]:
        """Test NeuPrint database connectivity."""
        pass
```

#### NeuronType Models

```python
class NeuronTypeName:
    value: str

class NeuronTypeStatistics:
    type_name: NeuronTypeName
    total_count: int = 0
    soma_side_counts: Dict[str, int] = field(default_factory=dict)
    synapse_stats: Dict[str, float] = field(default_factory=dict)
```

#### Result Pattern

For explicit error handling:

```python
class Result(Generic[T, E]):
    """A Result type that represents either success (Ok) or failure (Err)."""
    
    def is_ok(self) -> bool:
        """Check if this is a success result."""
        return isinstance(self, Ok)

    def is_err(self) -> bool:
        """Check if this is an error result."""
        return isinstance(self, Err)

    def unwrap(self) -> T:
        """Get the success value or raise an exception if this is an error."""
        if self.is_ok():
            return self.value
        else:
            raise ValueError(f"Called unwrap() on Err value: {self.error}")

    def unwrap_or(self, default: T) -> T:
        """Get the success value or return the default if this is an error."""
        if self.is_ok():
            return self.value
        else:
            return default

    def map(self, func: Callable[[T], Any]) -> "Result":
        """Apply a function to the success value if Ok, otherwise return the Err."""
        if self.is_ok():
            try:
                return Ok(func(self.value))
            except Exception as e:
                return Err(str(e))
        else:
            return self

    def and_then(self, func: Callable[[T], "Result"]) -> "Result":
        """Chain operations that return Results."""
        if self.is_ok():
            try:
                return func(self.value)
            except Exception as e:
                return Err(str(e))
        else:
            return self


@dataclass
class Ok(Result[T, E]):
    """Success variant of Result."""
    value: T

@dataclass  
class Err(Result[T, E]):
    """Error variant of Result."""
    error: E
```

### Service Interfaces

The system uses several core services for data processing and management:

#### PageGenerationOrchestrator

```python
class PageGenerationOrchestrator:
    """Orchestrates the complete page generation workflow."""

    def __init__(self, page_generator):
        self.page_generator = page_generator

    def generate_page(self, neuron_type_name: str, soma_side: str = "combined") -> Result:
        """Generate a complete neuron page."""
        pass
```

#### ConnectivityCombinationService

```python
class ConnectivityCombinationService:
    """Service for combining L/R connectivity entries in combined pages."""

    def combine_connectivity_partners(self, partners: List[Dict]) -> List[Dict]:
        """Combine L/R partners for the same neuron types."""
        pass
```

#### ROICombinationService

```python
class ROICombinationService:
    """Service for combining L/R ROI entries in combined pages."""

    def combine_roi_data(self, roi_data: List[Dict]) -> List[Dict]:
        """Combine L/R ROI entries."""
        pass
```

#### ServiceContainer

```python
class ServiceContainer:
    """Simple service container for dependency management."""

    def __init__(self, config, copy_mode: str = "check_exists"):
        self.config = config
        self.copy_mode = copy_mode

    def get_service(self, service_name: str):
        """Retrieve a service instance."""
        pass
```

## Dataset Aliases

### Overview

QuickPage supports dataset aliases to handle different naming conventions for the same underlying dataset type. This is particularly useful when working with datasets that may have different names but use the same database structure and query patterns.

### Current Aliases

#### CNS Dataset Aliases
The following aliases are configured to use the CNS adapter:

- `male-cns` → `cns`
- `male-cns:v0.9` → `cns` (versioned)
- `male-cns:v1.0` → `cns` (versioned)

### Implementation

Dataset aliases are handled by the `DatasetAdapterFactory`:

```python
class DatasetAdapterFactory:
    _adapters: Dict[str, Type[DatasetAdapter]] = {
        "cns": CNSAdapter,
        "hemibrain": HemibrainAdapter,
        "optic-lobe": OpticLobeAdapter,
        "flywire-fafb": FafbAdapter,
    }

    # Dataset aliases - map alternative names to canonical names
    _aliases: Dict[str, str] = {
        "male-cns": "cns",
    }

    @classmethod
    def create_adapter(cls, dataset_name: str) -> DatasetAdapter:
        """Create appropriate adapter for the dataset."""
        # Handle versioned dataset names
        base_name = dataset_name.split(":")[0] if ":" in dataset_name else dataset_name

        # Resolve aliases
        resolved_name = cls._aliases.get(base_name, base_name)

        if dataset_name in cls._adapters:
            return cls._adapters[dataset_name]()
        elif base_name in cls._adapters:
            return cls._adapters[base_name]()
        elif resolved_name in cls._adapters:
            return cls._adapters[resolved_name]()
        else:
            # Default to CNS adapter for unknown datasets
            print(f"Warning: Unknown dataset '{dataset_name}', using CNS adapter as default")
            return CNSAdapter()
```

### Configuration Example

```yaml
# config.yaml
neuprint:
  server: "neuprint-cns.janelia.org"
  dataset: "male-cns:v0.9"  # This will use the CNS adapter
```

This configuration will:
- Resolve `male-cns:v0.9` → `male-cns` (base name) → `cns` (alias resolution)
- Create a `CNSAdapter` instance
- Set `dataset_info.name` to `"cns"`
- **Not produce any warnings**

### Adding New Aliases

To add a new dataset alias:

```python
# In src/quickpage/dataset_adapters.py
class DatasetAdapterFactory:
    _aliases: Dict[str, str] = {
        "male-cns": "cns",
        "female-cns": "cns",  # Example: add female-cns alias
        "new-hemibrain": "hemibrain",  # Example: add hemibrain alias
    }
```

### Versioned Datasets

Dataset aliases work with versioned dataset names:
- `male-cns:v0.9` → `cns`
- `male-cns:v1.0` → `cns`
- `male-cns:latest` → `cns`

### Error Handling

If a dataset name (including aliases) is not recognized:
1. Prints a warning message
2. Falls back to using the `CNSAdapter` as the default
3. Continues execution

Example warning:
```
Warning: Unknown dataset 'unknown-dataset:v1.0', using CNS adapter as default
```

## Dataset-Specific Implementations

### FAFB Dataset Handling

FAFB (FlyWire Adult Fly Brain) requires special handling due to data structure differences:

#### Soma Side Property Differences

FAFB stores soma side information differently than other datasets:

**Standard Datasets (CNS, Hemibrain)**:
- Property: `somaSide`
- Values: "L", "R", "M"

**FAFB Dataset**:
- Property: `side` OR `somaSide`
- Values: "LEFT", "RIGHT", "CENTER" or "left", "right", "center"

#### FAFB Adapter Implementation

```python
class FafbAdapter(DatasetAdapter):
    def __init__(self):
        dataset_info = DatasetInfo(
            name="flywire-fafb",
            soma_side_extraction=r"(?:_|-|\()([LRMlrm])(?:_|\)|$|[^a-zA-Z])",
            pre_synapse_column="pre",
            post_synapse_column="post",
            roi_columns=["inputRois", "outputRois"],
        )
        roi_strategy = OpticLobeRoiQueryStrategy()
        super().__init__(dataset_info, roi_strategy)

    def extract_soma_side(self, neurons_df: pd.DataFrame) -> pd.DataFrame:
        """Extract soma side from instance names using regex."""
        neurons_df = neurons_df.copy()

        if "somaSide" in neurons_df.columns:
            neurons_df["somaSide"] = neurons_df["somaSide"].fillna("U")
            return neurons_df

        # Check for FAFB-specific "side" column first
        if "side" in neurons_df.columns:
            side_mapping = {
                "LEFT": "L", "RIGHT": "R", "CENTER": "M", "MIDDLE": "M",
                "L": "L", "R": "R", "C": "M", "M": "M",
            }
            neurons_df["somaSide"] = (
                neurons_df["side"].str.upper().map(side_mapping).fillna("U")
            )
            return neurons_df

        # Extract from instance names using regex pattern
        if "instance" in neurons_df.columns and self.dataset_info.soma_side_extraction:
            pattern = self.dataset_info.soma_side_extraction
            extracted = neurons_df["instance"].str.extract(pattern, expand=False)
            neurons_df["somaSide"] = extracted.str.upper().fillna("U")
        else:
            neurons_df["somaSide"] = "U"

        return neurons_df
```

#### FAFB Query Modifications

Database queries require FAFB-specific property handling:

```cypher
-- FAFB-specific query with property fallback
MATCH (n:Neuron)
WHERE n.type = "Dm4"
RETURN n.bodyId,
       CASE
           WHEN n.somaSide IS NOT NULL THEN n.somaSide
           WHEN n.side IS NOT NULL THEN
               CASE n.side
                   WHEN 'LEFT' THEN 'L'
                   WHEN 'RIGHT' THEN 'R'
                   WHEN 'CENTER' THEN 'C'
                   WHEN 'MIDDLE' THEN 'C'
                   WHEN 'left' THEN 'L'
                   WHEN 'right' THEN 'R'
                   WHEN 'center' THEN 'C'
                   WHEN 'middle' THEN 'C'
                   ELSE n.side
               END
           ELSE ''
       END as soma_side
```

#### FAFB ROI Checkbox Behavior

FAFB datasets don't support ROI visualization in Neuroglancer, requiring conditional UI:

**Implementation**: Dataset-aware JavaScript that disables ROI checkboxes for FAFB:

```javascript
// Dataset detection
const IS_FAFB_DATASET = DATASET_NAME.toLowerCase().includes("fafb");

function syncRoiCheckboxes() {
  document.querySelectorAll("td.roi-cell").forEach((td) => {
    if (IS_FAFB_DATASET) {
      // Skip checkbox creation for FAFB datasets
      td.style.width = "250px";
      td.style.maxWidth = "250px";
      return;
    }
    // Regular checkbox logic for other datasets
  });
}
```

#### FAFB Neuroglancer Template Selection

Automatic template selection based on dataset:

```python
def get_neuroglancer_template(self) -> str:
    """Select appropriate neuroglancer template based on dataset."""
    if "fafb" in self.config.neuprint.dataset.lower():
        return "neuroglancer-fafb.js.jinja"
    else:
        return "neuroglancer.js.jinja"
```

### Dataset Detection Patterns

Centralized dataset type detection:

```python
class DatasetTypeDetector:
    @staticmethod
    def is_fafb(dataset_name: str) -> bool:
        """Detect if dataset is FAFB type."""
        return "fafb" in dataset_name.lower()

    @staticmethod
    def is_cns(dataset_name: str) -> bool:
        """Detect if dataset is CNS type."""
        return "cns" in dataset_name.lower()

    @staticmethod
    def is_hemibrain(dataset_name: str) -> bool:
        """Detect if dataset is Hemibrain type."""
        return "hemibrain" in dataset_name.lower()
```

## Feature Implementation Guides

### Connectivity Combination Implementation

For combined pages (automatically generated when multiple hemispheres exist), connectivity entries are automatically merged:

#### Problem
Combined pages showed separate entries:
- `L1 (R)` - 300 connections
- `L1 (L)` - 245 connections

#### Solution
`ConnectivityCombinationService` merges these into:
- `L1` - 545 connections (combined)

#### Implementation

```python
class ConnectivityCombinationService:
    def combine_connectivity_partners(self, partners: List[Dict]) -> List[Dict]:
        """Combine L/R partners for the same neuron types."""
        # Group partners by type
        grouped = defaultdict(list)
        for partner in partners:
            base_type = self._extract_base_type(partner['type'])
            grouped[base_type].append(partner)

        combined = []
        for base_type, type_partners in grouped.items():
            if len(type_partners) == 1:
                # Single entry - automatically remove soma side label for combined view
                partner = type_partners[0].copy()
                partner['type'] = base_type
                combined.append(partner)
            else:
                # Multiple entries - automatically combine them
                combined_partner = self._combine_partners(base_type, type_partners)
                combined.append(combined_partner)

        return combined

    def _combine_partners(self, base_type: str, partners: List[Dict]) -> Dict:
        """Combine multiple partner entries."""
        combined = {
            'type': base_type,
            'weight': sum(p['weight'] for p in partners),
            'connection_count': sum(p['connection_count'] for p in partners),
            'body_ids': []
        }

        # Combine body IDs from all partners
        for partner in partners:
            if 'body_ids' in partner:
                combined['body_ids'].extend(partner['body_ids'])

        # Select most common neurotransmitter
        neurotransmitters = [p.get('neurotransmitter') for p in partners if p.get('neurotransmitter')]
        if neurotransmitters:
            combined['neurotransmitter'] = Counter(neurotransmitters).most_common(1)[0][0]

        return combined
```

### ROI Combination Implementation

Similar to connectivity, ROI entries are automatically combined for multi-hemisphere pages:

#### Problem
Combined pages showed separate ROI entries:
- `ME_L` - 2500 pre, 1800 post synapses
- `ME_R` - 2000 pre, 1200 post synapses

#### Solution
`ROICombinationService` merges these into:
- `ME` - 4500 pre, 3000 post synapses (combined)

#### Implementation

```python
class ROICombinationService:
    # ROI naming patterns to detect sided ROIs
    ROI_SIDE_PATTERNS = [
        r'^(.+)_([LR])$',           # ME_L, ME_R
        r'^(.+)\(([LR])\)$',        # ME(L), ME(R)
        r'^(.+)_([LR])_(.+)$',      # ME_L_layer_1, ME_R_layer_1
        r'^(.+)\(([LR])\)_(.+)$',   # ME(L)_col_2, ME(R)_col_2
    ]

    def combine_roi_data(self, roi_data: List[Dict]) -> List[Dict]:
        """Combine L/R ROI entries."""
        # Extract base names and group
        grouped = defaultdict(list)
        for roi in roi_data:
            base_name = self._extract_base_roi_name(roi['roi'])
            grouped[base_name].append(roi)

        combined = []
        for base_name, roi_entries in grouped.items():
            if len(roi_entries) == 1:
                # Single entry - just use base name
                entry = roi_entries[0].copy()
                entry['roi'] = base_name
                combined.append(entry)
            else:
                # Multiple entries - combine them
                combined_entry = self._combine_roi_entries(base_name, roi_entries)
                combined.append(combined_entry)

        return combined

    def _combine_roi_entries(self, base_name: str, entries: List[Dict]) -> Dict:
        """Combine multiple ROI entries."""
        return {
            'roi': base_name,
            'pre': sum(e.get('pre', 0) for e in entries),
            'post': sum(e.get('post', 0) for e in entries),
            'downstream': sum(e.get('downstream', 0) for e in entries),
            'upstream': sum(e.get('upstream', 0) for e in entries)
        }
```

### Coefficient of Variation (CV) Implementation

The CV feature adds variability analysis to connectivity tables, showing how consistent connection strengths are within each partner type.

#### Problem
Connectivity tables only showed average connection counts but provided no insight into the variability of connections across individual partner neurons.

#### Solution
Added coefficient of variation calculation and display:
- CV = standard deviation / mean of connections per neuron
- Values range from 0 (no variation) to higher values (more variation)
- Provides normalized measure comparable across different scales

#### Data Collection Implementation

Modified `neuprint_connector.py` to track individual partner neuron weights:

```python
# In connectivity query processing
type_soma_data[key] = {
    "type": record["partner_type"],
    "soma_side": soma_side,
    "total_weight": 0,
    "connection_count": 0,
    "neurotransmitters": {},
    "partner_body_ids": set(),
    "partner_weights": {},  # NEW: Track weights per partner neuron
}

# Track weights per partner neuron for CV calculation
partner_id = record["partner_bodyId"]
if partner_id not in type_soma_data[key]["partner_weights"]:
    type_soma_data[key]["partner_weights"][partner_id] = 0
type_soma_data[key]["partner_weights"][partner_id] += int(record["weight"])

### Synonym and Flywire Type Filtering Implementation

The Types page includes specialized filtering functionality for synonym and Flywire type tags that allows users to filter neuron types based on additional naming information.

#### Problem
Users needed a way to quickly identify neuron types that have:
1. Synonyms (alternative names from various naming conventions)
2. Flywire types that are different from the neuron type name (meaningful cross-references)

The challenge was ensuring that clicking on Flywire tags only shows cards with displayable Flywire types (different from the neuron name), not just any Flywire synonym.

#### Solution
Implemented independent filtering for synonym and Flywire type tags with proper handling of displayable vs. non-displayable Flywire types.

#### Template Data Structure

The template receives processed data with separate attributes:

```jinja2
<div class="neuron-card-wrapper"
     data-synonyms="{{ neuron.synonyms if neuron.synonyms else "" }}"
     data-flywire-types="{{ neuron.flywire_types if neuron.flywire_types else "" }}"
     data-processed-synonyms="{% if neuron.processed_synonyms %}{{ neuron.processed_synonyms.keys() | list | join(',') }}{% endif %}"
     data-processed-flywire-types="{% if neuron.processed_flywire_types %}{{ displayable_types | join(',') }}{% endif %}">
```

Key data attributes:
- `data-synonyms`: Raw synonym data
- `data-processed-synonyms`: Processed synonyms ready for display
- `data-flywire-types`: Raw Flywire synonym data (may include same-as-name)
- `data-processed-flywire-types`: Only Flywire types different from neuron name

#### JavaScript Filter Implementation

Independent filter variables track each filter type:

```javascript
// Track filter state
let currentSynonymFilter = "all";
let currentFlywireTypeFilter = "all";

// Separate click handlers for each tag type
if (tagElement.hasClass("synonym-tag")) {
    currentSynonymFilter = currentSynonymFilter !== "all" ? "all" : "synonyms-present";
} else if (tagElement.hasClass("flywire-type-tag")) {
    currentFlywireTypeFilter = currentFlywireTypeFilter !== "all" ? "all" : "flywire-types-present";
}
```

#### Filter Logic Implementation

**Synonym Filter:**
```javascript
const matchesSynonym = (() => {
    if (selectedSynonym === "all") return true;

    const synonyms = cardWrapper.data("synonyms") || "";
    const processedSynonyms = cardWrapper.data("processed-synonyms") || "";

    if (selectedSynonym === "synonyms-present") {
        return synonyms !== "" || processedSynonyms !== "";
    }
    return false;
})();
```

**Flywire Filter (Critical Implementation):**
```javascript
const matchesFlywireType = (() => {
    if (selectedFlywireType === "all") return true;

    const processedFlywireTypes = cardWrapper.data("processed-flywire-types") || "";

    if (selectedFlywireType === "flywire-types-present") {
        // Only check processed flywire types - these contain only displayable (different) types
        return processedFlywireTypes !== "";
    }
    return false;
})();
```

#### Visual Feedback Implementation

Independent highlighting for each filter type:

```javascript
// Update synonym tag highlighting
$("#filtered-results-container .synonym-tag").removeClass("selected");
if (currentSynonymFilterValue !== "all") {
    $("#filtered-results-container .synonym-tag").addClass("selected");
}

// Update flywire type tag highlighting
$("#filtered-results-container .flywire-type-tag").removeClass("selected");
if (currentFlywireTypeFilterValue !== "all") {
    $("#filtered-results-container .flywire-type-tag").addClass("selected");
}
```

#### Key Implementation Details

1. **Displayable Flywire Types**: The critical distinction is that `processedFlywireTypes` contains only Flywire synonyms that differ from the neuron type name. For example:
   - AOTU019 with Flywire synonym "AOTU019" → Not in `processedFlywireTypes`
   - Tm3 with Flywire synonym "CB1031" → Included in `processedFlywireTypes`

2. **Independent Filtering**: Each filter type works independently - only one can be active at a time.

3. **Filter Reset**: Clicking a tag of a different type automatically resets the other filter and switches to the new one.

4. **CSS Integration**: Uses existing CSS classes `.synonym-tag.selected` and `.flywire-type-tag.selected` for visual feedback.

#### Data Flow

1. **Backend Processing**: Creates `processed_synonyms` and `processed_flywire_types` with only displayable items
2. **Template Rendering**: Outputs data attributes for both raw and processed data
3. **JavaScript Filtering**: Uses appropriate data attribute based on filter type
4. **Visual Feedback**: Highlights all tags of the active filter type

This implementation ensures perfect alignment between what users see (displayed tags) and what the filter shows (matching cards).

#### CSS Integration

The filtering system uses existing CSS classes for visual feedback:

```css
/* Synonym tags */
.synonym-tag {
    background-color: #f0f4ff;
    color: #4338ca;
    border-color: #e0e7ff;
    cursor: pointer;
}

.synonym-tag.selected {
    background-color: #4338ca;
    color: white;
    border-color: #3730a3;
    box-shadow: 0 2px 4px rgba(67, 56, 202, 0.3);
}

/* Flywire type tags */
.flywire-type-tag {
    background-color: #ecfdf5;
    color: #059669;
    border-color: #d1fae5;
    cursor: pointer;
}

.flywire-type-tag.selected {
    background-color: #059669;
    color: white;
    border-color: #047857;
    box-shadow: 0 2px 4px rgba(5, 150, 105, 0.3);
}
```

#### Performance Considerations

1. **DOM Queries**: Filters cache jQuery selections to avoid repeated DOM queries
2. **Event Delegation**: Uses delegated event handlers for dynamic content
3. **Debouncing**: Text search includes debouncing to prevent excessive filtering
4. **Data Attributes**: Uses data attributes for efficient filtering logic

#### Testing Strategy

The filtering implementation can be tested with:

```javascript
// Test filter state management
console.assert(currentSynonymFilter === "all", "Initial state should be 'all'");

// Test filter logic
const testCard = $(".neuron-card-wrapper").first();
const hasDisplayableFlywire = testCard.data("processed-flywire-types") !== "";
console.log("Card has displayable flywire types:", hasDisplayableFlywire);

// Test visual feedback
const activeFilters = $(".synonym-tag.selected, .flywire-type-tag.selected").length;
console.log("Number of active filter tags:", activeFilters);
```

#### Future Enhancements

Planned improvements:
1. **Filter Combinations**: Allow synonym AND Flywire filters simultaneously
2. **Filter Persistence**: Save filter state in URL parameters
3. **Advanced Search**: Boolean operators for complex queries
4. **Performance**: Virtual scrolling for large datasets

```

#### CV Calculation

```python
# Calculate coefficient of variation for connections per neuron
partner_weights = list(data["partner_weights"].values())
if len(partner_weights) > 1:
    # Convert to connections per target neuron
    connections_per_target = [w / len(body_ids) for w in partner_weights]
    mean_conn = sum(connections_per_target) / len(connections_per_target)
    variance = sum((x - mean_conn) ** 2 for x in connections_per_target) / len(connections_per_target)
    std_dev = variance**0.5
    cv = (std_dev / mean_conn) if mean_conn > 0 else 0
else:
    cv = 0  # No variation with only one partner neuron

# Add to partner data
upstream_partners.append({
    "type": data["type"],
    "soma_side": data["soma_side"],
    "neurotransmitter": most_common_nt,
    "weight": weight,
    "connections_per_neuron": connections_per_neuron,
    "coefficient_of_variation": round(cv, 3),  # NEW: CV field
    "percentage": percentage,
    "partner_neuron_count": len(data["partner_body_ids"]),
})
```

#### CV Combination for L/R Entries

Enhanced `ConnectivityCombinationService` to properly combine CV values:

```python
def _merge_partner_group(self, partner_type: str, partners: List[Dict[str, Any]]) -> Dict[str, Any]:
    combined = {
        "type": partner_type,
        "soma_side": "",
        "weight": 0,
        "connections_per_neuron": 0,
        "coefficient_of_variation": 0,  # NEW: CV field
        "percentage": 0,
        "neurotransmitter": "Unknown",
        "partner_neuron_count": 0,
    }

    # Track CV data weighted by partner neuron count for combined CV calculation
    cv_data = []

    for partner in partners:
        # ... existing combination logic ...

        # Collect CV data weighted by partner count
        cv = partner.get("coefficient_of_variation", 0)
        partner_count = partner.get("partner_neuron_count", 0)
        if partner_count > 0:
            cv_data.append((cv, partner_count))

    # Calculate combined coefficient of variation (weighted average)
    if cv_data:
        total_weight_for_cv = sum(count for _, count in cv_data)
        if total_weight_for_cv > 0:
            weighted_cv = sum(cv * count for cv, count in cv_data) / total_weight_for_cv
            combined["coefficient_of_variation"] = round(weighted_cv, 3)

    return combined
```

#### Template Integration

Added CV column to connectivity tables in `connectivity.html.jinja`:

```html
<!-- Upstream table header -->
<th title="Coefficient of variation for connections per neuron">CV</th>

<!-- Upstream table data -->
<td>{{- partner.get('coefficient_of_variation', 0) -}}</td>

<!-- Downstream table header -->
<th title="Coefficient of variation for connections per neuron">CV</th>

<!-- Downstream table data -->
<td>{{- partner.get('coefficient_of_variation', 0) -}}</td>
```

#### CV Interpretation

| CV Range | Interpretation | Biological Meaning |
|----------|---------------|-------------------|
| 0.0 | No variation | Single partner neuron |
| 0.0 - 0.3 | Low variation | Consistent connection strengths |
| 0.3 - 0.7 | Medium variation | Moderate variability |
| 0.7+ | High variation | Some partners much stronger |

#### Testing Implementation

Testing for CV functionality is integrated into the service tests for `ConnectivityCombinationService` and related components. The CV calculation and combination logic is validated through integration tests rather than standalone unit tests.

### Neuroglancer Integration Fixes

#### Problem
Neuroglancer JavaScript errors due to placeholder mismatches:

```javascript
// Error: Expected array, but received: "VISIBLE_NEURONS_PLACEHOLDER"
"segments": "VISIBLE_NEURONS_PLACEHOLDER"
```

#### Solution
Correct placeholder types in template generation:

```python
# Before (incorrect)
template_vars = {
    "visible_neurons": "VISIBLE_NEURONS_PLACEHOLDER",  # STRING - causes error
}

# After (correct)
template_vars = {
    "visible_neurons": [],  # EMPTY ARRAY - valid JSON
}
```

#### Flexible Dataset Layer Detection

```javascript
// Before (CNS-only)
const cnsSegLayer = neuroglancerState.layers.find(l => l.name === "cns-seg");

// After (multi-dataset)
const mainSegLayer = neuroglancerState.layers.find(
  l => l.type === "segmentation" && l.segments !== undefined &&
       (l.name === "cns-seg" || l.name === "flywire-fafb:v783b")
);
```

### HTML Tooltip System Implementation

Rich tooltips for enhanced user experience:

#### Basic Structure

```html
<div class="html-tooltip">
    <div class="tooltip-content">
        <!-- Rich HTML content -->
        <h4>Title</h4>
        <p>Description with <strong>formatting</strong></p>
        <ul>
            <li>Feature 1</li>
            <li>Feature 2</li>
        </ul>
    </div>
    <!-- Trigger element -->
    ?
</div>
```

#### JavaScript Implementation

```javascript
function initializeHtmlTooltips() {
    document.querySelectorAll('.html-tooltip').forEach(tooltip => {
        const content = tooltip.querySelector('.tooltip-content');

        tooltip.addEventListener('mouseenter', () => {
            content.style.display = 'block';
            positionTooltip(tooltip, content);
        });

        tooltip.addEventListener('mouseleave', () => {
            content.style.display = 'none';
        });
    });
}

function positionTooltip(trigger, content) {
    // Automatic positioning to prevent viewport overflow
    const triggerRect = trigger.getBoundingClientRect();
    const contentRect = content.getBoundingClientRect();

    // Default: above the trigger
    let top = triggerRect.top - contentRect.height - 10;
    let left = triggerRect.left + (triggerRect.width / 2) - (contentRect.width / 2);

    // Adjust for viewport overflow
    if (top < 0) {
        // Show below if no room above
        top = triggerRect.bottom + 10;
    }

    if (left < 0) {
        left = 10;  // Left margin
    } else if (left + contentRect.width > window.innerWidth) {
        left = window.innerWidth - contentRect.width - 10;  // Right margin
    }

    content.style.top = `${top}px`;
    content.style.left = `${left}px`;
}
```

## Troubleshooting

### Common Issues

#### NeuPrint Connection Failures

**Symptoms**:
- Connection timeout errors
- Authentication failures
- Dataset not found errors

**Debugging**:
```bash
# Test connection
quickpage test-connection

# Check configuration
quickpage --verbose test-connection

# Verify token
echo $NEUPRINT_APPLICATION_CREDENTIALS
```

**Solutions**:
- Verify NeuPrint token is valid and not expired
- Check network connectivity to neuprint.janelia.org
- Ensure dataset name matches exactly (case-sensitive)
- Try different NeuPrint server endpoints

#### Template Rendering Errors

**Symptoms**:
- Jinja2 template syntax errors
- Missing template files
- Context variable errors

**Debugging**:
```python
def validate_template(template_path: str) -> Result[bool]:
    """Validate template syntax and required variables."""
    try:
        env = Environment(loader=FileSystemLoader(os.path.dirname(template_path)))
        template = env.get_template(os.path.basename(template_path))

        # Test render with minimal context
        template.render({})
        return Result.success(True)
    except Exception as e:
        return Result.failure(f"Template error: {e}")
```

**Solutions**:
- Check template syntax with Jinja2 linter
- Verify all required template variables are provided
- Check file permissions on template directory
- Ensure template inheritance chain is correct

#### Cache Issues

**Symptoms**:
- Stale data being served
- Cache corruption errors
- Excessive memory usage

**Solutions**:
```bash
# Clear all caches
quickpage cache --action clear

# Check cache statistics
quickpage cache --action stats

# Clean expired entries only
quickpage cache --action clean
```

#### Performance Issues

**Symptoms**:
- Slow page generation
- High memory usage
- Database timeouts

**Investigation**:
- Enable performance profiling: `QUICKPAGE_PROFILE=1`
- Check cache hit rates
- Monitor database query performance
- Review memory usage patterns

### Debugging Tools

#### Log Configuration

Enable detailed logging:

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)
```

#### Citation Logging

QuickPage includes dedicated citation logging for tracking missing citations:

```python
# Citation logging is automatically configured
# Log files are created in output/.log/missing_citations.log

# View citation issues
cat output/.log/missing_citations.log

# Monitor in real-time
tail -f output/.log/missing_citations.log

# Integration in services
from quickpage.utils.text_utils import TextUtils

# Logging happens automatically when output_dir is provided
processed_synonyms = TextUtils.process_synonyms(
    synonyms_string=synonyms_raw,
    citations=citations_dict,
    neuron_type="TestNeuron",
    output_dir="/path/to/output"  # Enables citation logging
)
```

**Citation Log Features**:
- Rotating log files (1MB max, keeps 5 backups)
- Timestamped entries with context information
- UTF-8 encoding for international characters
- Dedicated logger (`quickpage.missing_citations`)
- No interference with other system logs

#### Development Mode

```bash
export QUICKPAGE_DEBUG=1
export QUICKPAGE_PROFILE=1
quickpage --verbose generate -n Dm4
```

This enables:
- Detailed operation logging
- Performance timing information
- Memory usage tracking
- Cache operation details
- Database query logging

### Logging Architecture

QuickPage uses a multi-layer logging system for different concerns:

#### System Loggers

```python
# Main application logger
logger = logging.getLogger(__name__)

# Dedicated citation logger
citation_logger = logging.getLogger("quickpage.missing_citations")
citation_logger.setLevel(logging.WARNING)
citation_logger.propagate = False  # Isolated from parent loggers
```

#### Citation Logging Implementation

The citation logging system automatically tracks missing citations:

```python
def _setup_citation_logger(cls, output_dir: str):
    """Set up dedicated logger for missing citations."""
    log_dir = Path(output_dir) / ".log"
    log_dir.mkdir(parents=True, exist_ok=True)

    citation_logger = logging.getLogger("quickpage.missing_citations")
    citation_logger.setLevel(logging.WARNING)
    citation_logger.propagate = False

    # File handler with rotation
    log_file = log_dir / "missing_citations.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    citation_logger.addHandler(file_handler)

    return citation_logger
```

#### Integration Points

Citation logging is integrated into:

1. **TextUtils.process_synonyms()**: Logs missing citations during synonym processing
2. **CitationService.create_citation_link()**: Logs missing citations during link creation
3. **Template rendering**: Automatic context passing for logging

#### Log File Management

- **Location**: `output/.log/missing_citations.log`
- **Rotation**: Automatic when file reaches 1MB
- **Backups**: Up to 5 backup files kept
- **Format**: Timestamped with context information
- **Encoding**: UTF-8 for international support

## Contributing

### Code Style

Follow these coding standards:

- **PEP 8**: Python code style guide
- **Type Hints**: Use type annotations for all public APIs
- **Docstrings**: Google-style docstrings for all classes and functions
- **Error Handling**: Use Result pattern for fallible operations
- **Testing**: Minimum 90% test coverage for new code

### Pull Request Process

1. **Fork** the repository and create a feature branch
2. **Implement** changes following coding standards
3. **Test** thoroughly with unit and integration tests
4. **Document** changes in relevant documentation files
5. **Submit** pull request with clear description of changes

### Development Workflow

#### Setting Up Development Environment

```bash
# Clone and setup
git clone <repository-url>
cd quickpage
pixi install

# Create feature branch
git checkout -b feature/your-feature-name

# Install pre-commit hooks
pixi run pre-commit install
```

#### Running Tests

```bash
# Unit tests
pixi run test

# With coverage
pixi run test-coverage

# Integration tests
pixi run test-integration

# Performance tests
pixi run test-performance
```

### Adding New Services

When adding new services, follow this pattern:

1. **Define Interface**: Create abstract base class defining the service contract
2. **Implement Service**: Create concrete implementation with proper error handling
3. **Register Service**: Add to service container factory
4. **Write Tests**: Comprehensive unit and integration tests
5. **Update Documentation**: Add to this developer guide

### Performance Considerations

When contributing code:

- **Cache Appropriately**: Use existing cache layers for expensive operations
- **Minimize Database Queries**: Batch queries when possible
- **Handle Large Datasets**: Consider memory usage for large neuron types
- **Profile Changes**: Use performance profiling to verify no regressions
- **Optimize Critical Paths**: Focus on page generation performance

---

This developer guide provides comprehensive coverage of QuickPage's architecture, implementation patterns, and development practices. For user-focused documentation, see the [User Guide](user-guide.md).
