# neuView Developer Guide

A comprehensive guide for developers working on the neuView neuron visualization platform. This guide covers architecture, development setup, implementation details, and contribution guidelines.

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

neuView is a modern Python CLI tool that generates beautiful HTML pages for neuron types using data from NeuPrint. Built with Domain-Driven Design (DDD) architecture for maintainability and extensibility.

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

neuView follows Domain-Driven Design principles with clean architecture:

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
cd neuview
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
pixi run neuview test-connection
```

### CLI Changes in v2.0

**Simplified Page Generation**: The `--soma-side` parameter has been removed from all CLI commands. neuView now automatically detects available soma sides and generates appropriate pages:

```bash
# OLD (v1.x): Manual soma-side specification
pixi run neuview generate -n Dm4 --soma-side left

# NEW (v2.0): Automatic detection and generation
pixi run neuview generate -n Dm4
# Automatically generates: Dm4_L.html, Dm4_R.html, Dm4.html (if multi-hemisphere)
```

**Benefits**:
- **Simplified UX**: No need to understand soma-side concepts
- **Comprehensive Output**: Always generates optimal page set
- **Error Reduction**: Eliminates invalid soma-side specifications
- **Future-Proof**: Adapts to any neuron type's data distribution

### Development Commands

neuView uses pixi for task management with separate commands for different types of work:

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

# Get help for the neuview CLI
pixi run help

# Generate test dataset (normal set)
pixi run test-set

# Generate test dataset without index
pixi run test-set-no-index

# Extract and fill from config
pixi run extract-and-fill [config_file] [test_category]
```

#### Version Management Tasks

The project includes automated version management for releases:

```bash
# Increment patch version and create git tag
pixi run increment-version

# Manual script execution
python scripts/increment_version.py
python scripts/increment_version.py --dry-run
```

**Version Increment Script**

The `increment_version.py` script automatically manages project versioning by:

1. **Reading current version**: Uses `git tag --list --sort=-version:refname` to find the latest semantic version tag
2. **Incrementing patch version**: Increases patch by 1 (e.g., `v2.7.1` → `v2.7.2`)  
3. **Creating git tag**: Creates an annotated tag with descriptive message

**Version Format**

- Expects/creates semantic versioning: `v{major}.{minor}.{patch}`
- The `v` prefix is optional when reading, always added when creating
- Handles missing patch numbers by defaulting to 0

**Safety Features**

- Validates version format before processing
- Warns about uncommitted changes but continues
- Checks for duplicate tags to prevent conflicts
- Does not auto-push tags (manual `git push origin <tag>` required)
- Supports `--dry-run` mode for testing

**Example Output**

```
Starting version increment process...
Current latest version: v2.7.1
Parsed version: major=2, minor=7, patch=1
New version: v2.7.2
Warning: There are uncommitted changes in the repository
Successfully created git tag: v2.7.2
Version successfully incremented from v2.7.1 to v2.7.2
```

**Error Handling**

The script will exit with error code 1 if:
- No valid semantic version tags are found
- Git commands fail
- Tag already exists
- Version format is invalid

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
    def __init__(self, config: Config):
        self.config = config
        self.service_container = ServiceContainer()
        self._setup_services()
    
    def generate_page(self, neuron_type: str) -> Result[str]:
        """Generate complete neuron type pages with automatic soma side detection."""
        pass
    
    def generate_index(self) -> Result[str]:
        """Generate the main index page with search and filtering."""
        pass
    
    def test_connection(self) -> Result[bool]:
        """Test connectivity to NeuPrint database."""
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

### NeuronType Class

Core domain entity representing a neuron type:

```python
class NeuronType:
    def __init__(self, name: str, description: str = None, custom_query: str = None):
        self.name = name
        self.description = description
        self.custom_query = custom_query
    
    def get_cache_key(self) -> str:
        """Generate unique cache key for this neuron type."""
        pass
    
    def get_neuron_count(self) -> int:
        """Get total number of neurons of this type."""
        pass
    
    def get_synapse_stats(self) -> Dict[str, int]:
        """Get synapse statistics for this neuron type."""
        pass
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
    def __init__(self):
        self._services = {}
        self._singletons = {}
    
    def register(self, service_name: str, factory: Callable, singleton: bool = True):
        """Register a service factory."""
        pass
    
    def get(self, service_name: str) -> Any:
        """Retrieve a service instance."""
        if service_name in self._singletons:
            return self._singletons[service_name]
        
        factory = self._services[service_name]
        instance = factory()
        
        if singleton:
            self._singletons[service_name] = instance
        
        return instance
```

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
    
    def extract_soma_side(self, neuron_data: Dict) -> str:
        """Extract soma side information from neuron data."""
        pass
    
    def normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names and types."""
        pass
    
    def categorize_rois(self, roi_list: List[str]) -> Dict[str, List[str]]:
        """Categorize ROIs by brain region."""
        pass

class CNSAdapter(DatasetAdapter):
    def extract_soma_side(self, neuron_data: Dict) -> str:
        return neuron_data.get('somaSide', '')

class HemibrainAdapter(DatasetAdapter):
    def extract_soma_side(self, neuron_data: Dict) -> str:
        return neuron_data.get('somaSide', '')
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

neuView v2.0 introduces automatic page generation that eliminates the need for manual soma-side specification. The system intelligently analyzes neuron data and generates the optimal set of pages.

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

### Hexagon Grid Generator

Generates spatial visualizations for neuron distribution:

```python
class HexagonGridGenerator:
    def __init__(self, hex_size: int = 20, spacing_factor: float = 1.1):
        self.hex_size = hex_size
        self.spacing_factor = spacing_factor
    
    def generate_region_hexagonal_grids(self, neuron_data: Dict) -> Dict[str, str]:
        """Generate hexagonal grids for all brain regions."""
        pass
    
    def generate_single_region_grid(self, region_name: str, 
                                   neuron_positions: List[Tuple[float, float]]) -> str:
        """Generate SVG hexagonal grid for a single region."""
        pass
```

### Coordinate System

Mathematical functions for hexagonal grid coordinate conversion:

```python
def hex_to_axial(hex_coord: Tuple[int, int]) -> Tuple[int, int]:
    """Convert hexagonal coordinates to axial coordinates."""
    q, r = hex_coord
    return (q, r)

def axial_to_pixel(axial_coord: Tuple[int, int], size: int) -> Tuple[float, float]:
    """Convert axial coordinates to pixel coordinates."""
    q, r = axial_coord
    x = size * (3/2 * q)
    y = size * (math.sqrt(3)/2 * q + math.sqrt(3) * r)
    return (x, y)
```

### Color Mapping

Dynamic color assignment based on data values:

```python
def get_color_for_value(value: float, min_val: float, max_val: float, 
                       color_scheme: str = 'viridis') -> str:
    """Map a numeric value to a color in the specified scheme."""
    if max_val == min_val:
        return '#808080'  # Gray for constant values
    
    normalized = (value - min_val) / (max_val - min_val)
    
    if color_scheme == 'viridis':
        # Viridis color mapping
        pass
    elif color_scheme == 'plasma':
        # Plasma color mapping
        pass
    
    return color_hex
```

## Template System

### Template Architecture

Jinja2-based template system with custom extensions:

```python
class TemplateStrategy:
    def load_template(self, template_name: str) -> Template:
        """Load and parse a template file."""
        pass
    
    def render_template(self, template: Template, context: Dict) -> str:
        """Render template with provided context."""
        pass

class JinjaTemplateStrategy(TemplateStrategy):
    def __init__(self, template_dir: str):
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self._setup_filters()
    
    def _setup_filters(self):
        """Register custom Jinja2 filters."""
        self.env.filters['format_number'] = format_number_filter
        self.env.filters['safe_url'] = safe_url_filter
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

```python
def format_number_filter(value: Union[int, float], precision: int = 1) -> str:
    """Format numbers with appropriate precision and thousand separators."""
    if isinstance(value, (int, float)) and not math.isnan(value):
        if value >= 1000000:
            return f"{value/1000000:.{precision}f}M"
        elif value >= 1000:
            return f"{value/1000:.{precision}f}K"
        else:
            return f"{value:,.{precision}f}"
    return str(value)


```

## Performance & Caching

### Multi-Level Cache System

neuView implements a sophisticated caching system with multiple levels:

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

neuView uses a comprehensive testing strategy with clear separation between unit and integration tests. Tests are organized by type and use pytest markers for selective execution.

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

- **Integration tests**: Focus on component interactions
  - Format: `test_[workflow_or_integration_scenario]`
  - Example: `test_end_to_end_male_cns_workflow`

### Performance Guidelines

- **Unit tests**: Should complete in under 1 second total
- **Integration tests**: May take several seconds due to file I/O and component setup
- **Full test suite**: Typically < 10 seconds

### CI/CD Integration

Tests are executed in GitHub Actions with separate jobs for better reporting:

```yaml
# Unit tests (fast feedback)
unit-tests:
  name: Unit Tests
  steps:
    - name: Run unit tests
      run: pixi run unit-test-verbose

# Integration tests (comprehensive)
integration-tests:
  name: Integration Tests
  steps:
    - name: Run integration tests
      env:
        NEUPRINT_TOKEN: ${{ secrets.FRANKS_NEUPRINT_TOKEN }}
      run: pixi run integration-test-verbose
```

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

### Adding New Tests

When adding new features:

1. **Add unit tests** for individual components
2. **Add integration tests** if the feature involves multiple components
3. **Use appropriate markers** (`@pytest.mark.unit` or `@pytest.mark.integration`)
4. **Follow naming conventions**
5. **Ensure proper cleanup** of resources in integration tests

### Test Data Factory

Centralized test data creation:

```python
class TestDataFactory:
    @staticmethod
    def create_neuron_data(neuron_type: str = "TestNeuron") -> Dict:
        """Create standardized test neuron data."""
        return {
            'type': neuron_type,
            'somaSide': 'L',  # Default for testing
            'bodyId': 123456789,
            'status': 'Traced',
            # ... additional fields
        }
    
    @staticmethod 
    def create_connectivity_data(partner_count: int = 5) -> List[Dict]:
        """Create test connectivity data."""
        return [
            {
                'partner_type': f'Partner{i}',
                'soma_side': 'L' if i % 2 else 'R',
                'weight': 100 - i * 10,
                'connection_count': 50 - i * 5
            }
            for i in range(partner_count)
        ]
```

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
- `NEUVIEW_CONFIG_PATH`: Custom configuration file path
- `NEUVIEW_CACHE_DIR`: Cache directory override
- `NEUVIEW_DEBUG`: Enable debug logging
- `NEUVIEW_PROFILE`: Enable performance profiling

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

#### NeuronType

Core domain entity:

```python
class NeuronType:
    name: str
    description: Optional[str]
    custom_query: Optional[str]
```

#### Result Pattern

For explicit error handling:

```python
class Result[T]:
    @staticmethod
    def success(value: T) -> 'Result[T]':
        """Create successful result."""
        pass
    
    @staticmethod
    def failure(error: str) -> 'Result[T]':
        """Create failed result."""
        pass
    
    def is_success(self) -> bool:
        """Check if result represents success."""
        pass
    
    @property
    def value(self) -> T:
        """Get success value or raise exception."""
        pass
    
    @property
    def error(self) -> str:
        """Get error message or None."""
        pass
```

### Service Interfaces

#### DatabaseQueryService

```python
class DatabaseQueryService:
    def execute_query(self, query: str, parameters: Dict = None) -> Result[List[Dict]]:
        """Execute database query with parameters."""
        pass
```

#### CacheService

```python
class CacheService:
    def get(self, key: str) -> Optional[Any]:
        """Retrieve cached value."""
        pass
    
    def set(self, key: str, value: Any, ttl: int = None):
        """Store value in cache."""
        pass
```

#### CitationService

```python
class CitationService:
    def load_citations(self) -> Dict[str, Tuple[str, str]]:
        """Load citations from CSV file."""
        pass
    
    def get_citation(self, citation_key: str) -> Optional[Tuple[str, str]]:
        """Get citation information for a specific key."""
        pass
    
    def create_citation_link(self, citation_key: str, link_text: Optional[str] = None, 
                           output_dir: Optional[str] = None) -> str:
        """Create HTML link for citation with automatic missing citation logging."""
        pass
```

## Dataset Aliases

### Overview

neuView supports dataset aliases to handle different naming conventions for the same underlying dataset type. This is particularly useful when working with datasets that may have different names but use the same database structure and query patterns.

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
# In src/neuview/dataset_adapters.py
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
class FAFBAdapter(DatasetAdapter):
    def extract_soma_side(self, neuron_data: Dict) -> str:
        """Extract soma side with FAFB-specific handling."""
        # Check somaSide first (standard property)
        if 'somaSide' in neuron_data and neuron_data['somaSide']:
            return neuron_data['somaSide']
        
        # Fall back to FAFB-specific 'side' property
        if 'side' in neuron_data and neuron_data['side']:
            side = neuron_data['side'].upper()
            if side == 'LEFT':
                return 'L'
            elif side == 'RIGHT':
                return 'R'  
            elif side in ['CENTER', 'MIDDLE']:
                return 'C'
        
        return ''
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

#### Connectivity Checkbox Self-Reference Detection

Automatic checkbox disabling when partner type matches current neuron type and bodyId is already visible in neuroglancer:

**Problem**: Users could add the same neuron instance multiple times to the neuroglancer viewer by selecting connectivity partners that reference the current neuron itself.

**Solution**: Detect self-reference conditions and disable checkboxes automatically.

**Implementation**:

1. **HTML Template Changes** (`templates/sections/connectivity.html.jinja`):
```html
<td class="p-c"
    data-body-ids='{{ partner | get_partner_body_ids("upstream", connected_bids) | tojson }}'
    data-partner-type='{{ partner.get('type', 'Unknown') }}'>
```

2. **JavaScript Data** (`templates/sections/neuron_page_scripts.html.jinja`):
```javascript
const neuroglancerData = {
    // ... existing properties
    currentNeuronType: {{ neuron_data.type | tojson }}
};
```

3. **Checkbox Logic** (`templates/static/js/neuroglancer-url-generator.js.jinja`):
```javascript
// Check if we should disable this checkbox based on partner type and current neuron
const partnerType = td.dataset.partnerType;
const currentNeuronType = pd.currentNeuronType;
const shouldDisable = partnerType && currentNeuronType &&
                     partnerType === currentNeuronType &&
                     bodyIds.some(id => (pd.visibleNeurons || []).includes(id) || 
                                       (pd.visibleNeurons || []).includes(String(id)));

if (hasNoBodyIds || shouldDisable) {
    if (shouldDisable) {
        console.log("[CHECKBOX] Disabling checkbox for self-reference:", partnerType);
        td.classList.add("self-reference");
    }
    checkbox.disabled = true;
    checkbox.checked = false;
}
```

4. **CSS Styling** (`static/css/neuron-page.css`):
```css
.p-c.self-reference input[type="checkbox"] {
    background-color: #888 !important;
    cursor: not-allowed;
    opacity: 0.6;
}
```

**Logic Flow**:
```
For each connectivity partner:
├── Empty bodyIds? → Disable (existing behavior)
├── Partner type === Current type?
│   ├── No → Enable normally
│   └── Yes → Any bodyIds in visible neurons?
│       ├── No → Enable normally  
│       └── Yes → Disable (self-reference)
```

**Example**: For neuron type AN02A005 with visible neurons [123456, 789012]:
- LC10 partner with [111111, 222222] → Enabled ✅
- AN02A005 partner with [123456] → Disabled ❌ (self-reference)
- T4 partner with [333333, 444444] → Enabled ✅

**Testing**:
- Manual: Use `test_checkbox/test_checkbox_disable.html` for demonstration
- Integration: Generate pages for self-connecting neuron types (e.g., AN02A005)
- Console: Check for debug messages like `[CHECKBOX] Disabling checkbox for self-reference`

**Performance**: O(n×m) complexity where n = partners, m = visible neurons. Minimal impact due to small datasets.

**Browser Support**: Standard JavaScript (IE11+) using `dataset` API, `Array.includes()`, and CSS `:disabled`.

**Troubleshooting**:
1. **Checkbox not disabling**: Verify `data-partner-type` attribute and `currentNeuronType` in pageData
2. **Styling issues**: Confirm `.self-reference` CSS class is applied and styles are loaded
3. **Console errors**: Check neuroglancer data initialization and function load order

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

```python
def test_cv_calculation():
    """Test CV calculation with various scenarios."""
    # High variation case
    partner_weights = [10, 50, 20, 80, 15]  # High variability
    num_neurons = 5
    connections_per_neuron = [w / num_neurons for w in partner_weights]
    mean_conn = sum(connections_per_neuron) / len(connections_per_neuron)
    # ... CV calculation ...
    assert 0.7 <= cv <= 1.0, "High variation should have CV > 0.7"

def test_cv_combination():
    """Test CV weighted averaging for L/R combination."""
    l1_l_cv, l1_l_count = 0.25, 10
    l1_r_cv, l1_r_count = 0.30, 8
    expected_cv = (l1_l_cv * l1_l_count + l1_r_cv * l1_r_count) / (l1_l_count + l1_r_count)
    # Test service combination...
    assert abs(result_cv - expected_cv) < 0.001, "CV combination should be weighted average"
```

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
neuview test-connection

# Check configuration
neuview --verbose test-connection

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
neuview cache --action clear

# Check cache statistics
neuview cache --action stats

# Clean expired entries only
neuview cache --action clean
```

#### Performance Issues

**Symptoms**:
- Slow page generation
- High memory usage
- Database timeouts

**Investigation**:
- Enable performance profiling: `NEUVIEW_PROFILE=1`
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

neuView includes dedicated citation logging for tracking missing citations:

```python
# Citation logging is automatically configured
# Log files are created in output/.log/missing_citations.log

# View citation issues
cat output/.log/missing_citations.log

# Monitor in real-time
tail -f output/.log/missing_citations.log

# Integration in services
from neuview.utils.text_utils import TextUtils

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
- Dedicated logger (`neuview.missing_citations`)
- No interference with other system logs

#### Development Mode

```bash
export NEUVIEW_DEBUG=1
export NEUVIEW_PROFILE=1
neuview --verbose generate -n Dm4
```

This enables:
- Detailed operation logging
- Performance timing information
- Memory usage tracking
- Cache operation details
- Database query logging

### Logging Architecture

neuView uses a multi-layer logging system for different concerns:

#### System Loggers

```python
# Main application logger
logger = logging.getLogger(__name__)

# Dedicated citation logger
citation_logger = logging.getLogger("neuview.missing_citations")
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
    
    citation_logger = logging.getLogger("neuview.missing_citations")
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
cd neuview
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

This developer guide provides comprehensive coverage of neuView's architecture, implementation patterns, and development practices. For user-focused documentation, see the [User Guide](user-guide.md).