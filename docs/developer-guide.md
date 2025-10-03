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

neuView is organized into four distinct layers:

- **Presentation Layer**: CLI Commands, Templates, Static Assets, HTML Generation
- **Application Layer**: Services, Orchestrators, Command Handlers, Factories  
- **Domain Layer**: Entities, Value Objects, Domain Services, Business Logic
- **Infrastructure Layer**: Database, File System, External APIs, Caching, Adapters

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
Clone the repository and navigate to the project directory.

2. **Install dependencies:**
Install dependencies using `pixi install`.

3. **Set up environment:**
Set up the environment using `pixi run setup-env` and edit the .env file with your NeuPrint token.

4. **Verify setup:**
Test the connection using `pixi run neuview test-connection`.

### CLI Changes in v2.0

**Simplified Page Generation**: The `--soma-side` parameter has been removed from all CLI commands. neuView now automatically detects available soma sides and generates appropriate pages:

In v2.0, automatic detection and generation replaces manual soma-side specification. The `generate` command with a neuron name automatically detects and generates appropriate pages for all soma sides.

**Benefits**:
- **Simplified UX**: No need to understand soma-side concepts
- **Comprehensive Output**: Always generates optimal page set
- **Error Reduction**: Eliminates invalid soma-side specifications
- **Future-Proof**: Adapts to any neuron type's data distribution

### Development Commands

neuView uses pixi for task management with separate commands for different types of work:

#### Testing Tasks

**Unit Tests** - Fast, isolated tests for individual components:
Run unit tests using `pixi run unit-test` or `pixi run unit-test-verbose` for detailed output. You can target specific test files or test classes as needed.

**Integration Tests** - End-to-end tests for component interactions:
Run integration tests using `pixi run integration-test` or `pixi run integration-test-verbose`. These can be targeted to specific integration test files.

**General Testing**:
Run all tests using `pixi run test`, `pixi run test-verbose`, or `pixi run test-coverage` for coverage reporting.

#### Code Quality Tasks

Format code using `pixi run format` and check code quality using `pixi run check`.

#### Content Generation Tasks

Content generation tasks include cleaning output (`clean-output`), filling the processing queue (`fill-all`, `fill [neuron_type]`), processing items (`pop-all`, `pop [count]`), and the complete workflow (`create-all-pages`).

#### Development Support Tasks

Development support tasks include environment setup (`setup-env`), CLI help (`help`), test dataset generation (`test-set`, `test-set-no-index`), and configuration extraction (`extract-and-fill`).

#### Version Management Tasks

The project includes automated version management for releases:

Version management includes incrementing versions using `pixi run increment-version` or running the script directly with optional dry-run mode.

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

The version increment process analyzes the current version, calculates the new version, creates a git tag, and reports the successful increment.

**Error Handling**

The script will exit with error code 1 if:
- No valid semantic version tags are found
- Git commands fail
- Tag already exists
- Version format is invalid

#### Task Usage Patterns

**Development Workflow**:
Typical development workflow: 1) Setup environment, 2) Run tests during development, 3) Check code quality, 4) Run full test suite before commit.

**Content Generation Workflow**:
Content generation can be done with the complete workflow command or step-by-step using individual commands for cleaning, filling, processing, and creating the index.

**Testing Workflow**:
Use unit tests for fast feedback during development, and comprehensive integration tests with coverage before release.

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

See the `PageGenerator` class in `src/neuview/page_generator.py` for the complete implementation, including the `__init__`, `generate_page`, `generate_index`, and `test_connection` methods.

### PageGenerationOrchestrator

Coordinates the complex page generation workflow through a multi-step process including request validation, data fetching, connectivity processing, visualization generation, template rendering, and output saving.

See the `PageGenerationOrchestrator` class and its `generate_page` method in `src/neuview/models/page_generation.py`.

### NeuronType Class

Core domain entity representing a neuron type with methods for cache key generation, neuron counting, and synapse statistics.

See the `NeuronType` class in `src/neuview/models/domain_models.py` for the complete implementation including `__init__`, `get_cache_key`, `get_neuron_count`, and `get_synapse_stats` methods.

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

Dependency injection using a service container with service registration and singleton management.

See the `ServiceContainer` class in `src/neuview/services/page_generation_container.py` for the complete implementation including the `__init__`, `register`, and `get` methods.

### Service Development Pattern

Standard pattern for implementing new services with configuration injection, caching integration, error handling, input validation, and core processing logic.

Refer to any service class in `src/neuview/services/` for examples of this pattern, such as `DatabaseQueryService` in `src/neuview/services/database_query_service.py` or `CacheService` in `src/neuview/services/cache_service.py`.

## Data Processing Pipeline

### Dataset Adapters

Different datasets require different data processing approaches. See the `DatasetAdapter` base class and its implementations (`CNSAdapter`, `HemibrainAdapter`, `FAFBAdapter`) in `src/neuview/dataset_adapters.py` for methods like `extract_soma_side`, `normalize_columns`, and `categorize_rois`.

### Data Flow

Raw NeuPrint Data → Dataset Adapter → Cache Layer → Service Processing → Template Rendering

1. **Data Extraction**: NeuPrint queries return raw database results
2. **Adaptation**: Dataset-specific adapters normalize the data
3. **Caching**: Processed data is cached for performance
4. **Analysis**: Services perform connectivity and ROI analysis with CV calculation
5. **Rendering**: Template system generates final HTML

### Connectivity Data Processing with CV

The connectivity processing pipeline includes statistical analysis including coefficient of variation (CV) calculation. See the connectivity query methods and CV calculation logic in `src/neuview/services/data_processing_service.py` and `src/neuview/services/connectivity_combination_service.py`.

The partner data structure includes the calculated CV value for template rendering.

### Automatic Page Generation System

neuView v2.0 introduces automatic page generation that eliminates the need for manual soma-side specification. The system intelligently analyzes neuron data and generates the optimal set of pages.

#### Architecture Overview

The automatic page generation system analyzes soma side distribution, determines which pages to generate based on data availability, and creates appropriate side-specific and combined pages. See the `SomaDetectionService` and its `generate_pages_with_auto_detection` method in the relevant service files.

#### Detection Logic

The system uses sophisticated logic to determine which pages to generate based on soma side distribution, counting sides with data, and handling unknown soma side counts. See the `_should_generate_combined_page` function implementation for the complete logic.

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

The automatic system maintains backward compatibility while removing user-facing complexity. The `GeneratePageCommand` class has been simplified by removing the `soma_side` parameter, allowing the system to auto-detect appropriate pages to generate. See `src/neuview/models/page_generation.py` for the updated command structure.

#### Performance Considerations

- **Data Analysis**: Single query analyzes all soma sides simultaneously
- **Parallel Generation**: Individual pages generated concurrently when possible
- **Cache Efficiency**: Shared data fetching across multiple page generations
- **Memory Management**: Automatic cleanup after page generation completes

### ROI Query Strategies

Different strategies for querying region of interest data including methods for querying central brain ROIs and categorizing ROI data by region type. See the ROI-related services in `src/neuview/services/` for the complete implementation.

## Visualization System

### Hexagon Grid Generator

Generates spatial visualizations for neuron distribution with configurable hex size and spacing. The system includes methods for generating hexagonal grids for multiple brain regions and individual regions. See the visualization-related services in `src/neuview/services/` for the complete implementation.

### Coordinate System

Mathematical functions for hexagonal grid coordinate conversion including hex-to-axial and axial-to-pixel coordinate transformations. See the coordinate system functions in the visualization services.

### Color Mapping

Dynamic color assignment based on data values with support for multiple color schemes including viridis and plasma. See the `get_color_for_value` function in the visualization services for the complete color mapping implementation.

## Template System

### Template Architecture

Jinja2-based template system with custom extensions for loading, parsing, and rendering templates with custom filters. See the `TemplateStrategy` and `JinjaTemplateStrategy` classes in `src/neuview/services/jinja_template_service.py` for the complete implementation including custom filter registration.

### Template Structure

The template system is organized with base layout templates, individual neuron type page templates, index templates with search functionality, and neuron type listing templates. JavaScript templates include neuroglancer URL generation and neuron page functionality. See the `templates/` directory for the complete template structure.

### Template Context

Structured data passed to templates includes neuron data, connectivity data, ROI data, visualization data, and metadata. See the `TemplateContext` class and its `to_dict` method for the complete context structure used in template rendering.

### Connectivity Table Template Processing

The connectivity template handles CV display with proper fallbacks including safe fallback values, descriptive tooltips, logical column positioning, and consistent implementation for both upstream and downstream tables. See the connectivity table templates in `templates/` for the complete HTML structure and Jinja2 template logic.

### Custom Template Filters

Custom template filters provide number formatting with appropriate precision and thousand separators, handling millions, thousands, and standard number formatting. See the `format_number_filter` function and other custom filters in the template service implementation.

## Performance & Caching

### Multi-Level Cache System

neuView implements a sophisticated caching system with multiple levels:

neuView implements a sophisticated multi-level caching system with memory, file, and database cache backends, along with cache population strategies. See the `CacheService` class in `src/neuview/services/cache_service.py` for the complete implementation including the `get_cached_data` method with fallback logic.

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

Performance monitoring includes timing operations and collecting metrics with start/end timer functionality and elapsed time tracking. See the performance monitoring implementation in the relevant service files for timer management and metrics collection.

## Development Patterns

### Error Handling

Consistent error handling using the Result pattern with input validation, data fetching, processing, and comprehensive exception handling for database connections, validation errors, and unexpected errors. See the `Result` class in `src/neuview/result.py` and error handling patterns throughout the service classes.

### Configuration Management

Hierarchical configuration system with dataclass-based configuration structure supporting NeuPrint, cache, output, and HTML configurations. Configuration can be loaded from YAML files or environment variables. See the `Config` class and related configuration classes in `src/neuview/config.py`.

### Service Registration

Dependency injection setup with factory functions for creating fully configured page generators. Core services, analysis services, and content services are registered with the service container. See the `create_page_generator` function in `src/neuview/builders/page_generator_builder.py` for the complete service registration implementation.

### Type Safety

Using type hints and validation with dataclass-based request objects and Result return types for type-safe parameter handling. See the domain models in `src/neuview/models/domain_models.py` for examples of type-safe analysis request structures.

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

See `test/test_dataset_adapters.py` for examples of unit tests, particularly the `TestDatasetAdapterFactory` class and its `test_male_cns_alias_resolution` method.

#### Integration Tests (`@pytest.mark.integration`)
End-to-end tests that verify component interactions and real-world scenarios.

**Characteristics:**
- Slower execution (may involve file I/O)
- Test component interactions
- Uses real configuration files
- Tests end-to-end workflows
- May use temporary files/resources

See `test/test_male_cns_integration.py` for examples of integration tests, particularly the `TestMaleCNSIntegration` class and its `test_config_with_male_cns_creates_cns_adapter` method.

### Test Execution

#### Pixi Tasks
Various pixi tasks are available for running unit tests, integration tests, all tests, and tests with coverage. Use the verbose variants for detailed output during development.

#### Selective Execution
Tests can be executed selectively by targeting specific test files, test classes, or individual test methods using pytest's selection syntax.

### Test Structure

Tests are organized in the `test/` directory with separate files for unit tests (like `test_dataset_adapters.py`) and integration tests (like `test_male_cns_integration.py`). Service-specific tests, visualization component tests, and test fixtures are organized in subdirectories.

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

Tests are executed in GitHub Actions with separate jobs for better reporting. Unit tests provide fast feedback, while integration tests run comprehensively with required environment variables like NEUPRINT_TOKEN for database access. See the GitHub Actions workflow files for the complete CI/CD configuration.

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

Special focus on testing dataset alias functionality with comprehensive test coverage for alias resolution, dataset adapter creation, and configuration handling. See the dataset alias tests in the test files for examples of alias validation and integration testing including versioned alias resolution and end-to-end workflow testing.
```

### Debugging Failed Tests

#### Unit Test Failures
Run specific failing tests with verbose output using pytest selection syntax. Check test markers to understand test categorization.

#### Integration Test Failures
Verify environment setup, token configuration, and run tests with verbose debugging and traceback options to diagnose integration test issues.

### Adding New Tests

When adding new features:

1. **Add unit tests** for individual components
2. **Add integration tests** if the feature involves multiple components
3. **Use appropriate markers** (`@pytest.mark.unit` or `@pytest.mark.integration`)
4. **Follow naming conventions**
5. **Ensure proper cleanup** of resources in integration tests

### Test Data Factory

Centralized test data creation with factory methods for creating standardized test neuron data and connectivity data with configurable parameters. See the `TestDataFactory` class methods `create_neuron_data` and `create_connectivity_data` in the test files for examples of test data generation.

## Configuration

### Configuration Files

YAML-based configuration system with sections for NeuPrint server settings, caching configuration, template settings, performance parameters, and visualization options. See the default configuration files and `src/neuview/config.py` for the complete configuration structure and available options.

### Environment Variables

Environment variable support for sensitive configuration:

- `NEUPRINT_APPLICATION_CREDENTIALS`: NeuPrint API token
- `NEUVIEW_CONFIG_PATH`: Custom configuration file path
- `NEUVIEW_CACHE_DIR`: Cache directory override
- `NEUVIEW_DEBUG`: Enable debug logging
- `NEUVIEW_PROFILE`: Enable performance profiling

### Configuration Validation

Automatic validation with clear error messages using dataclass post-initialization validation. See the `NeuPrintConfig` class and its `__post_init__` method in `src/neuview/config.py` for examples of configuration validation with meaningful error messages.

## API Reference

### Core Classes

#### PageGenerator

Main interface for page generation with methods for initialization, page generation with automatic detection, index generation, and connection testing. See the `PageGenerator` class in `src/neuview/page_generator.py` for the complete API including method signatures and return types.

#### NeuronType

Core domain entity with name, optional description, and optional custom query fields. See the `NeuronType` class in `src/neuview/models/domain_models.py` for the complete dataclass definition.

#### Result Pattern

For explicit error handling with success and failure states, value retrieval, and error handling methods. See the `Result` class in `src/neuview/result.py` for the complete implementation including `success`, `failure`, `is_success`, `value`, and `error` methods.



### Service Interfaces

#### DatabaseQueryService

Database query execution with parameterized queries returning Result types. See the `DatabaseQueryService` class and its `execute_query` method in `src/neuview/services/database_query_service.py`.

#### CacheService

Cache value retrieval and storage with optional TTL support. See the `CacheService` class and its `get` and `set` methods in `src/neuview/services/cache_service.py`.

#### CitationService

Citation management including loading citations from CSV files, retrieving citation information, and creating HTML citation links with automatic missing citation logging. See the `CitationService` class in `src/neuview/services/citation_service.py` for the complete implementation including `load_citations`, `get_citation`, and `create_citation_link` methods.

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

Dataset aliases are handled by the `DatasetAdapterFactory` which maps alternative names to canonical names and creates appropriate adapter instances. See the `DatasetAdapterFactory` class in `src/neuview/dataset_adapters.py` for the complete implementation including the `_adapters` dictionary, `_aliases` mapping, and `create_adapter` method with versioned dataset handling and alias resolution.

### Configuration Example

Configuration files can use dataset aliases like `male-cns:v0.9` which will resolve to the appropriate adapter through base name extraction and alias resolution, creating the correct adapter instance without warnings. See the example configuration files for proper alias usage in YAML configuration format.

### Adding New Aliases

To add a new dataset alias, update the `_aliases` dictionary in the `DatasetAdapterFactory` class in `src/neuview/dataset_adapters.py` to map the new alias name to the canonical dataset name.

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

FAFB datasets don't support ROI visualization in Neuroglancer, requiring conditional UI with dataset-aware JavaScript that disables ROI checkboxes for FAFB datasets. See the `syncRoiCheckboxes` function and dataset detection logic in the JavaScript templates for the complete implementation.

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

Dataset-specific template selection for neuroglancer integration based on dataset name detection. See the `get_neuroglancer_template` method in the template services for conditional template selection logic.

### Dataset Detection Patterns

Common patterns for dataset type detection using case-insensitive string matching. See the `DatasetTypeDetector` class methods `is_fafb`, `is_cns`, and `is_hemibrain` in the dataset-related services for the complete detection pattern implementations.

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

The connectivity combination logic groups partners by base type, handles single and multiple entries differently, and combines weights, connection counts, and body IDs. See the `ConnectivityCombinationService` class in `src/neuview/services/connectivity_combination_service.py` for the complete implementation including the `combine_connectivity_partners` and `_combine_partners` methods.

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

The ROI combination service uses pattern matching to detect sided ROIs and groups them for combination. It handles both single and multiple entries, combining pre/post synapse counts and upstream/downstream data. See the `ROICombinationService` class in `src/neuview/services/` for the complete implementation including ROI naming patterns, `combine_roi_data`, and `_combine_roi_entries` methods.

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

Citation logging is automatically enabled when an output directory is provided to text processing utilities. See the `TextUtils.process_synonyms` method and related text processing functions for automatic citation logging integration.

**Citation Log Features**:
- Rotating log files (1MB max, keeps 5 backups)
- Timestamped entries with context information
- UTF-8 encoding for international characters
- Dedicated logger (`neuview.missing_citations`)
- No interference with other system logs

#### Development Mode

Enable development mode by setting the `NEUVIEW_DEBUG` and `NEUVIEW_PROFILE` environment variables and running neuview with the `--verbose` flag.

This enables:
- Detailed operation logging
- Performance timing information
- Memory usage tracking
- Cache operation details
- Database query logging

### Logging Architecture

neuView uses a multi-layer logging system for different concerns including main application logging and dedicated citation logging with isolated loggers.

#### System Loggers

The system uses separate loggers for main application events and citation tracking. See the logging configuration in the service files for logger setup and configuration.

#### Citation Logging Implementation

The citation logging system automatically tracks missing citations with dedicated logger setup, log directory creation, file rotation handling, and custom formatting. See the `_setup_citation_logger` method in the citation service for the complete implementation including rotating file handlers and UTF-8 encoding support.

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

Clone the repository, install dependencies with pixi, create feature branches using git, and install pre-commit hooks for code quality.

#### Running Tests

Run various test suites including unit tests, coverage reporting, integration tests, and performance tests using the appropriate pixi run commands.

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