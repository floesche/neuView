# QuickPage Developer Guide

This guide provides comprehensive technical documentation for QuickPage developers, covering architecture, implementation details, development workflows, and contribution guidelines.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Development Setup](#development-setup)
- [Core Components](#core-components)
- [Performance Optimizations](#performance-optimizations)
- [Frontend Implementation](#frontend-implementation)
- [Template Architecture](#template-architecture)
  - [Template Structure](#template-structure)
  - [Template Implementation Details](#template-implementation-details)
  - [Interactive Features Implementation](#interactive-features-implementation)
  - [Template Migration and Maintenance](#template-migration-and-maintenance)
  - [Template Debugging and Validation](#template-debugging-and-validation)
  - [Template Implementation Best Practices](#template-implementation-best-practices)
- [Hexagon Grid Visualization](#hexagon-grid-visualization)
  - [HexagonGridGenerator Architecture](#hexagongridgenerator-architecture)
  - [Data Structures and Formats](#data-structures-and-formats)
  - [Coordinate System Implementation](#coordinate-system-implementation)
  - [Color Mapping System](#color-mapping-system)
  - [Output Format Implementation](#output-format-implementation)
  - [Template Integration](#template-integration)
  - [Performance Considerations](#performance-considerations)
  - [Testing and Validation](#testing-and-validation)
- [Testing Strategy](#testing-strategy)
- [Implementation Details](#implementation-details)
- [Development Workflow](#development-workflow)
- [Contributing](#contributing)
- [Additional Documentation](#additional-documentation)

## Architecture Overview

QuickPage is built using Domain-Driven Design (DDD) principles with a clean architecture approach.

### Key Architectural Principles

- **Domain-Driven Design**: Business logic is encapsulated in domain entities and services
- **CQRS Pattern**: Command Query Responsibility Segregation for better maintainability
- **Result Pattern**: Explicit error handling without exceptions
- **Dependency Injection**: Testable and modular service architecture
- **Rich Domain Model**: Type-safe entities, value objects, and business logic
- **Async Operations**: Non-blocking operations for better performance

### Project Structure (Domain-Driven Design)

```
quickpage/
├── src/quickpage/           # Application source code
│   ├── domain/             # Domain layer (business logic)
│   │   ├── entities/       # Domain entities
│   │   ├── value_objects/  # Value objects
│   │   └── services/       # Domain services
│   ├── application/        # Application layer (use cases)
│   │   ├── commands/       # Command handlers
│   │   ├── queries/        # Query handlers
│   │   └── services/       # Application services
│   ├── infrastructure/     # Infrastructure layer
│   │   ├── database/       # Database adapters
│   │   ├── external/       # External service adapters
│   │   └── repositories/   # Repository implementations
│   ├── presentation/       # Presentation layer
│   │   ├── cli/           # CLI interface
│   │   └── web/           # Web interface (future)
│   └── shared/            # Shared utilities and cross-cutting concerns
├── templates/             # Jinja2 HTML templates
├── static/               # Static assets (CSS, JS, images)
├── docs/                 # Documentation
├── test/                 # Test files
└── examples/             # Example configurations and scripts
```

### Key Components

- **NeuPrintConnector**: Handles communication with NeuPrint database
- **PageGenerator**: Orchestrates HTML page generation
- **CacheManager**: Manages persistent and in-memory caching
- **ConfigManager**: Handles configuration loading and validation
- **TemplateEngine**: Jinja2-based HTML template rendering
- **DatasetAdapters**: Handle differences between NeuPrint datasets
- **NeuronType**: Core domain entity representing neuron types
- **NeuronSearch**: Client-side search functionality
- **ROIStrategy**: Dataset-specific ROI categorization logic

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Pixi package manager (recommended)
- Git
- NeuPrint access token

### Initial Setup

1. **Clone and setup:**
```bash
git clone <repository-url>
cd quickpage
pixi install
pixi run setup-env
```

2. **Configure development environment:**
```bash
# Copy and edit configuration
cp config.example.yaml config.yaml
# Add your NeuPrint token to .env file
```

3. **Run tests to verify setup:**
```bash
pixi run dev
```

### Development Commands

```bash
# Development shortcuts
pixi run clean-output       # Clean output directory
pixi run setup-env          # Create .env file from template
pixi run dev                # Show quickpage help

# Queue and batch processing
pixi run fill-all           # Fill queue with all neuron types
pixi run pop-all            # Process all items in queue
pixi run create-list        # Generate index page

# Test sets for development
pixi run test-set           # Generate test set with index
pixi run test-set-no-index  # Generate test set without index
pixi run test-set-only-weird # Generate only problematic types

# Complete pipeline
pixi run create-all-pages   # Full pipeline: clean, fill, process, index
```

## Core Components

### NeuronType Class

The `NeuronType` class is the core domain entity representing a neuron type with lazy loading and convenient access methods:

```python
@dataclass
class NeuronType:
    name: str
    description: str
    query_type: str
    soma_side: Optional[str] = None
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    def get_cache_key(self) -> str:
        """Generate unique cache key for this neuron type"""
        return f"{self.name}_{self.soma_side or 'all'}"
    
    def supports_soma_side(self, side: str) -> bool:
        """Check if neuron type supports specific soma side"""
        return side in self.get_available_soma_sides()
    
    def get_neuron_count(self, side: Optional[str] = None) -> int:
        """Get neuron count for specific soma side or total"""
        if side:
            return getattr(self.summary, f"{side}_count", 0)
        return self.summary.total_count
    
    def get_synapse_stats(self) -> Dict[str, float]:
        """Get synapse statistics"""
        return {
            'avg_pre': self.summary.avg_pre_synapses,
            'avg_post': self.summary.avg_post_synapses,
            'total_pre': self.summary.total_pre_synapses,
            'total_post': self.summary.total_post_synapses
        }
    
    @property
    def is_fetched(self) -> bool:
        """Check if data has been fetched from NeuPrint"""
        return self._neurons is not None
```

#### Key Features

- **Lazy Loading**: Data is fetched from NeuPrint only when first accessed
- **Soma Side Filtering**: Generate reports for left, right, middle, or all hemispheres
- **Convenience Methods**: Easy access to common statistics and counts
- **PageGenerator Integration**: Direct integration with HTML generation

#### Usage Example

```python
from quickpage import Config, NeuPrintConnector, NeuronType
from quickpage.config import NeuronTypeConfig

# Load configuration and create connector
config = Config.load("config.yaml")
connector = NeuPrintConnector(config)

# Create neuron type configuration
lc4_config = NeuronTypeConfig(
    name="LC4",
    description="Lobula Columnar Type 4 neurons",
    query_type="type"
)

# Create NeuronType instance
lc4_neurons = NeuronType("LC4", lc4_config, connector, soma_side='both')

# Access data (fetches automatically when needed)
print(f"Total neurons: {lc4_neurons.get_neuron_count()}")
print(f"Left neurons: {lc4_neurons.get_neuron_count('left')}")
print(f"Right neurons: {lc4_neurons.get_neuron_count('right')}")

# Generate HTML page
from quickpage import PageGenerator
generator = PageGenerator(config, "output/")
output_file = generator.generate_page_from_neuron_type(lc4_neurons)
```

### Dataset Adapters

The QuickPage dataset adapter system handles differences between NeuPrint datasets (hemibrain, CNS, optic-lobe) by providing dataset-specific processing while maintaining a consistent interface.

#### Architecture

Different NeuPrint datasets have varying database structures:

- **CNS**: Has dedicated `somaSide` column with 'L'/'R' values
- **Hemibrain**: Usually has `somaSide` column, sometimes needs extraction from instance names
- **Optic-Lobe**: Requires extracting soma side from instance names using regex patterns

#### Base DatasetAdapter Class

```python
class DatasetAdapter:
    """Base class for dataset-specific adaptations"""
    
    def __init__(self, dataset_info: DatasetInfo):
        self.dataset_info = dataset_info
    
    def extract_soma_side(self, neurons_df: pd.DataFrame) -> pd.DataFrame:
        """Extract soma side information from neuron data"""
        raise NotImplementedError
    
    def normalize_columns(self, neurons_df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names if needed"""
        return neurons_df
    
    def get_synapse_counts(self, neurons_df: pd.DataFrame) -> Tuple[int, int]:
        """Return (pre_total, post_total)"""
        pre_total = neurons_df['pre'].sum() if 'pre' in neurons_df.columns else 0
        post_total = neurons_df['post'].sum() if 'post' in neurons_df.columns else 0
        return int(pre_total), int(post_total)
    
    def query_central_brain_rois(self, all_rois: List[str]) -> List[str]:
        """Get list of central brain ROIs for this dataset"""
        raise NotImplementedError
    
    def categorize_rois(self, all_rois: List[str]) -> Dict[str, List[str]]:
        """Categorize ROIs into functional groups"""
        raise NotImplementedError
```

#### Built-in Adapters

**CNSAdapter** - For CNS dataset:
```python
class CNSAdapter(DatasetAdapter):
    def extract_soma_side(self, neurons_df):
        # Uses existing somaSide column
        return neurons_df
    
    def query_central_brain_rois(self, all_rois):
        # CNS-specific central brain definition
        central_brain_patterns = [
            r'^FB$', r'^PB$', r'^EB$', r'^NO$',
            r'^BU.*', r'^LAL.*', r'^CRE.*'
        ]
        return self._filter_rois_by_patterns(all_rois, central_brain_patterns)
```

**HemibrainAdapter** - For Hemibrain dataset:
```python
class HemibrainAdapter(DatasetAdapter):
    def extract_soma_side(self, neurons_df):
        # Uses somaSide column with regex fallback
        if 'somaSide' not in neurons_df.columns:
            pattern = r'_([LR])$'
            extracted = neurons_df['instance'].str.extract(pattern, expand=False)
            neurons_df['somaSide'] = extracted.fillna('U')
        return neurons_df
```

**OpticLobeAdapter** - For Optic-lobe dataset:
```python
class OpticLobeAdapter(DatasetAdapter):
    def extract_soma_side(self, neurons_df):
        # Extract from instance names using regex
        pattern = r'_([LR])(?:_|$)'
        extracted = neurons_df['instance'].str.extract(pattern, expand=False)
        neurons_df['somaSide'] = extracted.fillna('U')
        return neurons_df
    
    def categorize_rois(self, all_rois):
        return {
            'layers': [roi for roi in all_rois if self._is_layer_roi(roi)],
            'columns': [roi for roi in all_rois if self._is_column_roi(roi)],
            'neuropils': [roi for roi in all_rois if self._is_neuropil_roi(roi)]
        }
```

#### Automatic Detection

The system automatically selects the right adapter based on dataset name:

```python
def detect_dataset_adapter(server: str, dataset: str) -> DatasetAdapter:
    """Automatically detect and return appropriate dataset adapter"""
    if "hemibrain" in dataset.lower():
        return HemibrainAdapter(dataset)
    elif "cns" in dataset.lower():
        return CNSAdapter(dataset)
    elif "optic" in dataset.lower():
        return OpticLobeAdapter(dataset)
    else:
        return DefaultAdapter(dataset)
```

#### Usage Examples

```python
# Automatic detection
config = Config.load("config.yaml")  # dataset: "cns"
connector = NeuPrintConnector(config)  # Uses CNSAdapter automatically

# Manual adapter selection
from quickpage import get_dataset_adapter
cns_adapter = get_dataset_adapter('cns')
neurons_df = pd.DataFrame(...)  # Your neuron data
processed_df = cns_adapter.extract_soma_side(neurons_df)
```

### ROI Query Strategies

QuickPage implements dataset-specific ROI categorization strategies for handling different brain region structures across datasets.

#### ROI Strategy Architecture

```python
class ROIQueryStrategy:
    """Base class for dataset-specific ROI queries"""
    
    def query_central_brain_rois(self, all_rois: List[str]) -> List[str]:
        """Define what constitutes 'central brain' for this dataset"""
        raise NotImplementedError
    
    def query_primary_rois(self, all_rois: List[str]) -> List[str]:
        """Get primary ROIs for this dataset"""
        raise NotImplementedError
    
    def categorize_rois(self, all_rois: List[str]) -> Dict[str, List[str]]:
        """Categorize ROIs into functional groups"""
        raise NotImplementedError
    
    def filter_rois_by_type(self, all_rois: List[str], roi_type: str) -> List[str]:
        """Filter ROIs by type (layers, columns, neuropils)"""
        raise NotImplementedError
```

#### Integration with Page Generation

```python
def _get_dataset_specific_roi_analysis(self, connector, roi_counts_df, neurons_df):
    """Get ROI analysis using dataset-specific strategies."""
    from .dataset_adapters import DatasetAdapterFactory
    
    dataset_name = connector.config.neuprint.dataset
    adapter = DatasetAdapterFactory.create_adapter(dataset_name)
    
    if roi_counts_df is not None and not roi_counts_df.empty:
        all_rois = roi_counts_df['roi'].unique().tolist()
    else:
        return {}
    
    roi_analysis = {
        'central_brain_rois': adapter.query_central_brain_rois(all_rois),
        'primary_rois': adapter.query_primary_rois(all_rois),
        'roi_categories': adapter.categorize_rois(all_rois),
        'layer_rois': adapter.filter_rois_by_type(all_rois, 'layers'),
        'column_rois': adapter.filter_rois_by_type(all_rois, 'columns')
    }
    
    return roi_analysis
```

## Performance Optimizations

QuickPage implements several layers of caching for optimal performance.

### Persistent Cache System

#### How It Works

The cache system operates on multiple levels:

1. **Neuron Data Cache**: Stores complete neuron information
2. **ROI Hierarchy Cache**: Global cache for ROI structure
3. **Column Cache**: Expensive column queries cached for 24 hours
4. **Soma Sides Cache**: Per-neuron-type soma side information
5. **Meta Query Cache**: Database metadata queries

#### Cache Features

- **Persistent Storage**: Survives application restarts
- **Automatic Expiration**: Different TTL for different cache types
- **Memory + Disk**: In-memory for performance, disk for persistence
- **Cross-session Benefits**: Cache shared across different runs
- **Intelligent Invalidation**: Smart cache invalidation strategies

### Cache Implementation Details

#### Global ROI Hierarchy Cache

```python
_GLOBAL_CACHE = {
    'roi_hierarchy': None,           # ROI hierarchy data
    'meta_data': None,              # Meta query results  
    'dataset_info': {},             # Dataset information by server
    'cache_timestamp': None         # Cache creation time
}

def _get_roi_hierarchy(self) -> Dict[str, Any]:
    """Get ROI hierarchy with global caching"""
    cache_key = f"{self.server}_{self.dataset}"
    
    if _GLOBAL_CACHE['roi_hierarchy'] and cache_key in _GLOBAL_CACHE['roi_hierarchy']:
        return _GLOBAL_CACHE['roi_hierarchy'][cache_key]
    
    # Fetch from database
    hierarchy = self._fetch_roi_hierarchy_from_db()
    
    # Update global cache
    if not _GLOBAL_CACHE['roi_hierarchy']:
        _GLOBAL_CACHE['roi_hierarchy'] = {}
    _GLOBAL_CACHE['roi_hierarchy'][cache_key] = hierarchy
    
    return hierarchy
```

#### Column Cache Optimization

The most expensive query in QuickPage scans all neurons for column information:

```python
def _get_all_possible_columns_from_dataset(self) -> List[Dict[str, Any]]:
    """Get all possible columns with persistent caching"""
    cache_key = f"{self.server}_{self.dataset}"
    cache_file = self._get_column_cache_path(cache_key)
    
    # Try to load from cache
    if cache_file.exists():
        cached_data = self._load_column_cache(cache_file)
        if cached_data and not self._is_cache_expired(cached_data, hours=24):
            return cached_data['columns']
    
    # Fetch from database (expensive operation)
    columns = self._fetch_columns_from_database()
    
    # Save to cache
    self._save_column_cache(cache_file, columns, cache_key)
    
    return columns
```

#### Performance Results

- **Column Cache**: 80.6% performance improvement
- **ROI Hierarchy**: 88.9% cache hit rate
- **Overall Generation**: Up to 97.9% speed improvement on subsequent runs
- **Cross-session Persistence**: Benefits survive application restarts

### Cache Management

```python
class CacheManager:
    """Manages all caching operations"""
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        return {
            'neuron_hit_rate': self._calculate_hit_rate('neuron'),
            'roi_hit_rate': self._calculate_hit_rate('roi'),
            'column_hit_rate': self._calculate_hit_rate('column'),
            'total_cache_size': self._get_total_cache_size(),
            'cache_files': self._count_cache_files(),
        }
    
    def clear_all_caches(self) -> None:
        """Clear all cache types"""
        self._clear_memory_cache()
        self._clear_disk_cache()
        self._clear_global_cache()
```

## Frontend Implementation

### Neuron Search System

QuickPage includes a sophisticated client-side neuron search system with real-time autocomplete functionality.

#### Architecture Overview

- **Build-time Generation**: Neuron types embedded during page generation from `queue.yaml`
- **Client-side Search**: No server requests, instant results
- **Intelligent Ranking**: Exact matches first, then starts-with, then contains
- **Keyboard Navigation**: Arrow keys, Enter, and Escape support
- **Smart File Detection**: Automatically finds the correct HTML file for each neuron type

#### Implementation

**Search Class:**
```javascript
class NeuronSearch {
    constructor(inputId = 'menulines') {
        this.input = document.getElementById(inputId);
        this.neuronTypes = NEURON_TYPES_DATA || []; // Embedded at build time
        this.filteredTypes = [];
        this.currentIndex = -1;
        this.isDropdownVisible = false;
        this.clickingDropdown = false;
        
        this.createDropdown();
        this.bindEvents();
    }
    
    search(query) {
        if (!query.trim()) {
            this.hideDropdown();
            return;
        }
        
        const lowerQuery = query.toLowerCase();
        this.filteredTypes = this.neuronTypes
            .filter(type => type.toLowerCase().includes(lowerQuery))
            .sort((a, b) => this.rankSearchResult(a, b, lowerQuery))
            .slice(0, 10); // Limit to 10 results
        
        this.showDropdown();
    }
    
    rankSearchResult(a, b, query) {
        const aLower = a.toLowerCase();
        const bLower = b.toLowerCase();
        
        // Exact matches first
        if (aLower === query && bLower !== query) return -1;
        if (bLower === query && aLower !== query) return 1;
        
        // Starts with query
        const aStarts = aLower.startsWith(query);
        const bStarts = bLower.startsWith(query);
        if (aStarts && !bStarts) return -1;
        if (bStarts && !aStarts) return 1;
        
        // Alphabetical order
        return a.localeCompare(b);
    }
}
```

#### Build-time Generation

The search functionality is generated during page creation:

```python
def _generate_neuron_search_js(self):
    """Generate neuron-search.js with embedded neuron types"""
    js_file_path = self.output_dir / 'static' / 'js' / 'neuron-search.js'
    
    if js_file_path.exists():
        return  # Don't overwrite existing file
    
    # Get neuron types from queue
    neuron_types = self.queue_service.get_queued_neuron_types()
    if not neuron_types:
        neuron_types = self._get_fallback_neuron_types()
    
    # Generate JavaScript file from template
    template = self.template_env.get_template('static/js/neuron-search.js.template')
    js_content = template.render(neuron_types=neuron_types)
    
    js_file_path.parent.mkdir(parents=True, exist_ok=True)
    js_file_path.write_text(js_content)
```

#### File Detection Strategy

The search system tests multiple filename patterns:

```javascript
navigateToNeuronType(neuronType) {
    const patterns = [
        `${neuronType}.html`,
        `${neuronType.toLowerCase()}.html`,
        `${neuronType}_both.html`,
        `${neuronType.toLowerCase()}_both.html`,
        `${neuronType}_all.html`,
        `${neuronType.toLowerCase()}_all.html`
    ];
    
    // Test each pattern and navigate to first existing file
    this.testAndNavigate(patterns, 0);
}
```

### Filtering System Architecture

The frontend implements a sophisticated filtering system with real-time updates.

#### Filter State Management

```javascript
class FilterManager {
    constructor() {
        this.filters = {
            search: '',
            cellCount: { min: null, max: null },
            neurotransmitter: new Set(),
            brainRegion: new Set(),
            customFilters: new Map()
        };
        this.debounceTimeout = null;
    }
    
    updateFilter(filterType, value) {
        this.filters[filterType] = value;
        this.debounceUpdate();
    }
    
    debounceUpdate() {
        clearTimeout(this.debounceTimeout);
        this.debounceTimeout = setTimeout(() => {
            this.applyFilters();
        }, 300);
    }
    
    applyFilters() {
        const cards = document.querySelectorAll('.neuron-card');
        let visibleCount = 0;
        
        cards.forEach(card => {
            const isVisible = this.matchesAllFilters(card);
            card.style.display = isVisible ? 'block' : 'none';
            if (isVisible) visibleCount++;
        });
        
        this.updateVisibleCount(visibleCount);
    }
}
```

#### Cell Count Filter Implementation

The cell count filter provides interactive range selection with intelligent 10th percentile ranges:

```javascript
function createCellCountFilter() {
    // Ranges calculated from actual data distribution
    const ranges = [
        { min: 1, max: 10, label: '1-10' },
        { min: 11, max: 50, label: '11-50' },
        { min: 51, max: 100, label: '51-100' },
        { min: 101, max: 500, label: '101-500' },
        { min: 501, max: null, label: '500+' }
    ];
    
    ranges.forEach(range => {
        const tag = createFilterTag(range.label, () => {
            filterManager.updateFilter('cellCount', range);
        });
        
        // Add click-to-filter functionality
        tag.addEventListener('click', () => {
            filterManager.toggleCellCountRange(range);
        });
        
        container.appendChild(tag);
    });
}

// Interactive cell count tags on neuron cards
function makeInteractiveCellCountTags() {
    document.querySelectorAll('[data-cell-count]').forEach(element => {
        const cellCount = parseInt(element.dataset.cellCount);
        element.style.cursor = 'pointer';
        element.style.color = '#0066cc';
        
        element.addEventListener('click', (e) => {
            e.preventDefault();
            const range = determineRangeForCount(cellCount);
            filterManager.updateFilter('cellCount', range);
        });
    });
}
```

### Tooltip System Implementation

#### Core Architecture

The tooltip system provides rich hover information:

```javascript
class TooltipManager {
    constructor() {
        this.tooltip = this.createTooltipElement();
        this.currentTarget = null;
        this.hideTimeout = null;
    }
    
    createTooltipElement() {
        const tooltip = document.createElement('div');
        tooltip.className = 'custom-tooltip';
        tooltip.style.cssText = `
            position: absolute;
            background: #333;
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 14px;
            max-width: 300px;
            z-index: 1000;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s ease;
        `;
        document.body.appendChild(tooltip);
        return tooltip;
    }
    
    show(target, content) {
        clearTimeout(this.hideTimeout);
        this.tooltip.innerHTML = content;
        this.positionTooltip(target);
        this.tooltip.style.opacity = '1';
        this.currentTarget = target;
    }
    
    positionTooltip(target) {
        const rect = target.getBoundingClientRect();
        const tooltipRect = this.tooltip.getBoundingClientRect();
        
        let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
        let top = rect.top - tooltipRect.height - 10;
        
        // Boundary detection and adjustment
        if (left < 10) left = 10;
        if (left + tooltipRect.width > window.innerWidth - 10) {
            left = window.innerWidth - tooltipRect.width - 10;
        }
        if (top < 10) {
            top = rect.bottom + 10; // Show below if no space above
        }
        
        this.tooltip.style.left = `${left}px`;
        this.tooltip.style.top = `${top}px`;
    }
}
```

### Clickable Soma Sides Implementation

Individual neuron pages include clickable soma side navigation with dynamic updates:

```html
<!-- Soma Side Navigation -->
<div class="soma-side-nav">
    {% for side_info in soma_sides_data %}
    <a href="{{ side_info.filename }}" 
       class="soma-side-link {% if side_info.side == current_soma_side %}active{% endif %}"
       data-side="{{ side_info.side }}"
       data-count="{{ side_info.count }}">
        <span class="side-label">{{ side_info.display_name }}</span>
        <span class="side-count">[{{ side_info.count }}]</span>
    </a>
    {% endfor %}
</div>
```

**JavaScript Enhancement:**
```javascript
// Enhanced soma side navigation with AJAX loading
class SomaSideNavigator {
    constructor() {
        this.bindSomaSideLinks();
    }
    
    bindSomaSideLinks() {
        document.querySelectorAll('.soma-side-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const side = link.dataset.side;
                const count = link.dataset.count;
                
                // Update active state
                this.updateActiveState(link);
                
                // Load content dynamically (optional)
                this.loadSomaSideContent(side);
                
                // Update URL without page reload
                this.updateURL(link.href);
            });
        });
    }
    
    updateActiveState(activeLink) {
        // Remove active class from all links
        document.querySelectorAll('.soma-side-link').forEach(link => {
            link.classList.remove('active');
        });
        
        // Add active class to clicked link
        activeLink.classList.add('active');
    }
}
```

### Server-Side Dropdown Population

Filter options are populated server-side for consistency and include advanced categorization:

```python
def get_filter_options(neuron_types: List[NeuronType]) -> Dict[str, List[str]]:
    """Collect all unique filter options from neuron types"""
    options = {
        'neurotransmitters': set(),
        'brain_regions': set(),
        'cell_counts': [],
        'soma_sides': set(),
        'class_hierarchy': set()
    }
    
    for neuron_type in neuron_types:
        # Collect neurotransmitters
        if neuron_type.consensus_nt:
            options['neurotransmitters'].add(neuron_type.consensus_nt)
        if neuron_type.celltype_predicted_nt:
            options['neurotransmitters'].add(neuron_type.celltype_predicted_nt)
        
        # Collect brain regions using dataset-specific ROI categorization
        roi_categories = neuron_type.roi_analysis.get('roi_categories', {})
        for category, rois in roi_categories.items():
            options['brain_regions'].update(rois)
        
        # Collect cell counts for intelligent range calculation
        options['cell_counts'].append(neuron_type.total_count)
        
        # Collect soma sides
        if neuron_type.soma_sides_available:
            options['soma_sides'].update(neuron_type.soma_sides_available)
        
        # Collect class hierarchy information
        if hasattr(neuron_type, 'class_hierarchy'):
            options['class_hierarchy'].add(neuron_type.class_hierarchy)
    
    return {
        'neurotransmitters': sorted(options['neurotransmitters']),
        'brain_regions': sorted(options['brain_regions']),
        'cell_count_ranges': calculate_intelligent_ranges(options['cell_counts']),
        'soma_sides': sorted(options['soma_sides']),
        'class_hierarchy': sorted(options['class_hierarchy'])
    }

def calculate_intelligent_ranges(cell_counts: List[int]) -> List[Dict]:
    """Calculate cell count ranges using 10th percentiles"""
    if not cell_counts:
        return []
    
    sorted_counts = sorted(cell_counts)
    percentiles = [np.percentile(sorted_counts, i*10) for i in range(11)]
    
    ranges = []
    for i in range(10):
        min_val = int(percentiles[i]) if i > 0 else 1
        max_val = int(percentiles[i+1]) if i < 9 else None
        
        label = f"{min_val}-{max_val}" if max_val else f"{min_val}+"
        ranges.append({
            'min': min_val,
            'max': max_val,
            'label': label,
            'percentile': f"{i*10}-{(i+1)*10}th"
        })
    
    return ranges
```

## Template Architecture

QuickPage uses a modular Jinja2 template architecture for generating HTML pages. The template system has been refactored from a monolithic approach to a maintainable, component-based design.

### Template Structure

#### Base Template (`base.html`)
The foundation template that provides:
- Common HTML document structure (doctype, html, head, body)
- CSS imports block with all required stylesheets
- Template blocks for customization (title, css, extra_head, header, content, footer, extra_scripts)
- Responsive design foundation
- Bootstrap integration

#### Macro Library (`macros.html`)
Contains 9 reusable macros for common UI components:
- `stat_card()` - Statistic display cards
- `data_table()` - Standardized table rendering with DataTables integration
- `layer_table()` - Layer analysis table components
- `connectivity_table()` - Connection table rendering
- `iframe_embed()` - Iframe components for Neuroglancer
- `grid_row()` - Bootstrap grid layouts
- `roi_row()` - ROI table row rendering
- `layer_row_labels()` - Layer table labels

#### Modular Sections (`sections/`)
Each major page component is isolated:
- `header.html` - Page header with neuron type and count
- `summary_stats.html` - Summary statistics cards
- `analysis_details.html` - Analysis detail cards
- `neuroglancer.html` - Neuroglancer iframe embed
- `layer_analysis.html` - Layer analysis tables (243 lines)
- `roi_innervation.html` - ROI data table with filtering
- `connectivity.html` - Upstream/downstream connection tables
- `footer.html` - Page footer with generation info
- `neuron_page_scripts.html` - JavaScript template with direct variable access

### Template Implementation Details

#### JavaScript Template Approach
Instead of external JavaScript files, QuickPage uses a JavaScript template that maintains direct access to Jinja2 variables:

```jinja2
<!-- In neuron_page.html -->
{% block extra_scripts %}
<script>
{% include "sections/neuron_page_scripts.html" %}
</script>
{% endblock %}
```

**Benefits:**
- Direct template variable access without JSON serialization
- Conditional rendering based on data availability
- Template consistency within Jinja2 ecosystem
- Simplified debugging with accessible template variables

#### Template Inheritance Pattern
```jinja2
<!-- Main template extends base -->
{% extends "base.html" %}
{% from "macros.html" import stat_card, data_table %}

{% block title %}{{ neuron_type }} - Analysis{% endblock %}

{% block content %}
    {% include "sections/header.html" %}
    {% include "sections/summary_stats.html" %}
    {% if roi_summary %}
        {% include "sections/roi_innervation.html" %}
    {% endif %}
{% endblock %}
```

### Interactive Features Implementation

#### DataTables Integration
Tables are initialized with specific configurations:
```javascript
$('#table-id').DataTable({
    "order": [[ column, "desc" ]],
    "pageLength": -1,
    "paging": false,
    "responsive": true,
    "initComplete": function(settings, json) {
        createSliderInHeader('table-id');
        setupSlider('slider-id', 'value-id', this.api());
    }
});
```

#### Logarithmic Slider Implementation
Sliders use logarithmic scales for filtering:
- **ROI sliders:** Range -1.4 to 2 (represents 0.04% to 100%)
- **Connection sliders:** Range -1 to 3 (represents 0.1 to 1000 connections)

```javascript
var actualValue = Math.pow(10, parseFloat(slider.value));
var logValue = Math.log10(minValue);
```

#### Cumulative Percentage Calculations
Precise calculations using template-generated lookup objects:
```javascript
var roiPreciseData = {};
{% for roi in roi_summary %}
roiPreciseData['{{ roi.name }}'] = {
    inputPrecise: {{ roi.post_percentage }},
    outputPrecise: {{ roi.pre_percentage }}
};
{% endfor %}
```

### Template Migration and Maintenance

#### Zero-Breaking-Change Migration
The template refactoring was designed for seamless deployment:
- Template name unchanged: `neuron_page.html`
- Python code requires no modifications
- All template context variables used identically
- 100% backward compatibility maintained

#### Performance Optimizations
- **Template caching:** Better caching with smaller, modular files
- **Conditional includes:** Only render sections when data exists
- **Direct variable access:** No JSON serialization overhead
- **Reduced complexity:** Cleaner execution paths

#### Development Workflow
1. **Start with base template:** Extend `base.html` for consistent structure
2. **Use existing sections:** Include relevant section templates
3. **Create custom sections:** Add new sections in `templates/sections/`
4. **Leverage macros:** Use existing macros for consistency
5. **Add interactivity:** Include JavaScript in `extra_scripts` block
6. **Test thoroughly:** Verify all functionality works correctly

### Template Debugging and Validation

#### Common Issues and Solutions
1. **Sliders not appearing:** Check CSS classes and initComplete callback
2. **Filtering not working:** Verify column indices and filter function registration
3. **Cumulative percentages incorrect:** Validate data lookup keys match table content

#### Validation Script
```javascript
function validateTemplate() {
    const tests = {
        'jQuery loaded': typeof $ !== 'undefined',
        'DataTables available': typeof $.fn.DataTable !== 'undefined',
        'ROI table exists': $('#roi-table').length > 0,
        'ROI table initialized': $('#roi-table').hasClass('dataTable'),
        'ROI slider exists': $('#roi-percentage-slider').length > 0
    };
    return Object.values(tests).every(Boolean);
}
```

### Template Context Requirements

All original template variables are preserved:
- `roi_summary` - ROI data array
- `connectivity.upstream/downstream` - Connection data
- `neuron_data.type` - Neuron type string
- `summary` - Summary statistics object
- `layer_analysis` - Layer analysis data
- `neuroglancer_url` - Visualization URL
- `config` - Configuration object
- `generation_time` - Timestamp

### Creating Custom Templates

#### Example: Custom Analysis Page
```jinja2
{% extends "base.html" %}
{% from "macros.html" import stat_card %}

{% block title %}Custom Analysis - {{ analysis_name }}{% endblock %}

{% block content %}
    {% include "sections/header.html" %}
    {{ stat_card(custom_value, "Custom Metric", "highlight-stat") }}
    {% include "sections/connectivity.html" %}
{% endblock %}

{% block extra_scripts %}
<script>
$(document).ready(function() {
    // Custom functionality
});
</script>
{% endblock %}
```

### Template Implementation Best Practices

This section covers the current template implementation patterns, state management approaches, and best practices that ensure robust functionality and maintainability.

#### Modular Template Architecture

The current template system uses a modular architecture that promotes maintainability and reusability:

**Architecture Components**:
- **Base template**: `base.html` (31 lines) - Common layout and structure
- **Macro library**: `macros.html` (179 lines) - Reusable template components
- **Main template**: `neuron_page.html` (415 lines) - Page-specific content
- **Section templates**: 8 modular sections (~440 total lines) - Feature-specific components

**Template Usage Pattern**:
```python
# Standard template rendering
template = self.env.get_template('neuron_page.html')
context = {
    'roi_summary': roi_summary,
    'connectivity': connectivity,
    'neuron_data': neuron_data,
    'summary': summary,
    # ... all required variables
}
rendered_html = template.render(context)
```

**Benefits of Modular Design**:
- **Maintainability**: Each component has a single responsibility
- **Reusability**: Sections and macros can be shared across templates
- **Caching**: Smaller files improve template caching performance
- **Debugging**: Easier to isolate and fix issues in specific components

#### JavaScript Integration Patterns

**DataTables Configuration**:
The current implementation uses proper initialization timing for interactive components:

```javascript
$('#table-id').DataTable({
    "order": [[ column, "desc" ]],
    "pageLength": -1,
    "paging": false,
    "responsive": true,
    "initComplete": function(settings, json) {
        createSliderInHeader('table-id');
        setupSlider('slider-id', 'value-id', this.api());
    }
});
```

**Slider Configuration**:
Current slider ranges are optimized for data visualization:
- **ROI sliders**: Range `-1.4` to `2` (represents 0.04% to 100%)
- **Connection sliders**: Range `-1` to `3` (represents 0.1 to 1000 connections)
- **Column targeting**: Filters target percentage columns for accurate results

```javascript
// Filter configuration for percentage-based filtering
$.fn.dataTable.ext.search.push(createConnectionsFilter('upstream-table', 4));
$.fn.dataTable.ext.search.push(createConnectionsFilter('downstream-table', 4));
```

#### Data Access and Calculation Patterns

**Template Data Consistency**:
Templates use consistent formatting for neuron type display with conditional soma side information:

```html
<!-- Current template pattern -->
<td><strong>{{- partner.get('type', 'Unknown') -}}{% if partner.get('soma_side') %} ({{-partner.get('soma_side') -}}){% endif %}</strong></td>
```

**Robust Data Access**:
JavaScript uses a fallback pattern for reliable data retrieval:

```javascript
// Data lookup with fallback mechanism
function getPreciseValue(roiName, uPD, dPD, data, percentageCol) {
    if (uPD[roiName] !== undefined) {
        return uPD[roiName];
    } else if (dPD[roiName] !== undefined) {
        return dPD[roiName];
    } else {
        // Fallback: parse from table cell
        var percentageCell = data[percentageCol];
        var parsedPercentage = parseFloat(percentageCell.replace('%', ''));
        return !isNaN(parsedPercentage) ? parsedPercentage : 0;
    }
}
```

#### Interactive State Management

The application uses native HTML state management patterns for optimal performance and maintainability.

**Checkbox State Management**:
Connectivity and ROI tables use direct checkbox state access without additional data attributes:

```javascript
// Checkbox state operations
function syncConnectivityCheckboxes() {
    checkbox.checked = allOn;
    // State automatically preserved by DataTables DOM persistence
}

function isCheckboxSelected(checkbox) {
    return checkbox.checked; // Direct state access
}
```

**State Preservation**:
DataTables preserves DOM elements during filtering operations, which means:
- Checkbox `checked` properties persist automatically
- No additional state tracking mechanisms required
- Standard HTML form behavior maintained

**View Indicator Click Handling**:
View indicator tags use explicit text-to-value mapping for filter operations:

```javascript
// Click handler for view indicator tags
function handleTagClick(tagName) {
    let somaValue;
    if (tagName === "only L") {
        somaValue = "left";
    } else if (tagName === "only R") {
        somaValue = "right";
    } else if (tagName === "only M") {
        somaValue = "middle";
    } else if (tagName === "Undefined") {
        somaValue = "undefined";
    } else {
        somaValue = tagName.toLowerCase();
    }
    
    // Apply filter or toggle off if already active
    currentFilter = (currentFilter === somaValue) ? "all" : somaValue;
}
```

**Visual Highlighting Logic**:
The highlighting system uses independent evaluation for each tag type:

```javascript
// Highlighting logic for view indicators
function shouldHighlight(indicator, currentSomaFilter) {
    return (currentSomaFilter === "left" && indicator.hasClass("left")) ||
           (currentSomaFilter === "right" && indicator.hasClass("right")) ||
           (currentSomaFilter === "middle" && indicator.hasClass("middle")) ||
           (currentSomaFilter === "undefined" && indicator.hasClass("undefined"));
}
```

**Multi-Tag Support**:
For neuron types with multiple soma assignments (e.g., R8d with both "Undefined" and "only L"):
- Each tag operates independently
- Clicking any tag sets the corresponding filter
- Visual highlighting works for each tag separately
- Toggle behavior preserved (click twice to reset to "all")

#### Template Context Variables

The template system requires specific context variables for proper rendering:

```python
# Required template context
TEMPLATE_CONTEXT = {
    'roi_summary': [],           # ROI data array
    'connectivity': {},          # Upstream/downstream connections
    'neuron_data': {},          # Neuron type information
    'summary': {},              # Summary statistics
    'layer_analysis': {},       # Layer analysis data
    'neuroglancer_url': '',     # 3D visualization URL
    'config': {},               # Configuration object
    'generation_time': '',      # Timestamp
}
```

**Context Usage Pattern**:
```python
def render_neuron_page(self, neuron_data):
    context = self.build_template_context(neuron_data)
    template = self.env.get_template('neuron_page.html')
    return template.render(context)
```

#### Validation and Testing

**Template Functionality Validation**:
```javascript
function validateTemplateCore() {
    const tests = {
        'jQuery loaded': typeof $ !== 'undefined',
        'DataTables available': typeof $.fn.DataTable !== 'undefined',
        'ROI table exists': $('#roi-table').length > 0,
        'ROI table initialized': $('#roi-table').hasClass('dataTable'),
        'ROI slider exists': $('#roi-percentage-slider').length > 0,
        'Upstream table exists': $('#upstream-table').length > 0,
        'Downstream table exists': $('#downstream-table').length > 0,
    };
    
    console.log('Template Validation Results:');
    Object.entries(tests).forEach(([test, passed]) => {
        console.log(`${passed ? '✅' : '❌'} ${test}`);
    });
    
    return Object.values(tests).every(Boolean);
}
```

**Interactive Features Validation**:
```javascript
function validateInteractiveFeatures() {
    const tests = {
        // State management
        'Connectivity checkboxes exist': $('.connectivity-table input[type="checkbox"]').length > 0,
        'ROI checkboxes exist': $('.roi-table input[type="checkbox"]').length > 0,
        'Checkboxes use native state': $('[data-toggle-state]').length === 0,
        
        // View indicators
        'View indicator tags exist': $('.view-indicator').length > 0,
        'Click handlers work': $('.view-indicator').first().click().length > 0,
        'Highlighting function exists': typeof updateHighlighting === 'function',
        
        // Filtering
        'Soma filter available': $('#soma-filter').length > 0,
        'Filter handlers active': $('#soma-filter').data('events') !== undefined,
    };
    
    return Object.values(tests).every(Boolean);
}
```

**Manual Testing Checklist**:

*Basic Template Functionality:*
1. Verify all DataTables initialize correctly
2. Test slider functionality with logarithmic scales
3. Confirm cumulative percentages calculate accurately
4. Validate filtering works on all tables
5. Check responsive design on different screen sizes
6. Ensure all CSS classes are preserved
7. Verify JavaScript executes without errors

*Interactive Features Testing:*
8. **State Management**:
   - Test checkbox state persistence through table filtering
   - Verify native HTML form behavior
   - Confirm "Select All" / "Deselect All" functionality
   - Check DOM uses standard attributes only

9. **View Indicator Functionality**:
   - Test multi-tag neuron types (e.g., R8d with "Undefined" + "only L")
   - Verify independent tag operation and correct filter mapping
   - Test toggle behavior (double-click to reset)
   - Confirm proper text-to-value translation

10. **Visual Feedback**:
    - Test highlighting with soma side filter dropdown
    - Verify independent highlighting for multi-tag cards
    - Confirm visual consistency across different tag combinations
    - Check filter state feedback is clear and accurate

11. **Integration Testing**:
    - Test all interactive elements together
    - Verify state consistency across operations
    - Confirm performance under typical usage patterns

#### Performance Characteristics

**Template Rendering**:
- **Modular Architecture**: 12 focused files with clear responsibilities
- **Efficient Caching**: Smaller template files improve caching performance
- **Conditional Rendering**: Components only render when data is available
- **Memory Optimization**: Better organization reduces memory footprint

**JavaScript Performance**:
- **External Scripts**: Separate files enable better debugging and caching
- **Direct Variable Access**: Template variables used directly without serialization
- **Lazy Loading**: JavaScript components initialize only when needed
- **Optimized DOM Operations**: Minimal attribute manipulation and efficient state management

#### Development Best Practices

**Template Development Guidelines**:
- **Use Base Template**: Always extend `base.html` for consistent structure
- **Leverage Macros**: Use existing macros from `macros.html` for common components
- **Modular Sections**: Create new sections in `templates/sections/` for specific features
- **Conditional Rendering**: Use `{% if %}` blocks to render sections only when data exists
- **Consistent Context**: Follow established variable naming conventions

**JavaScript Integration Guidelines**:
- **Initialization Timing**: Use DataTables `initComplete` callbacks for proper timing
- **State Management**: Rely on native HTML state mechanisms (checkbox.checked, etc.)
- **Event Handling**: Use proper event prevention and delegation patterns
- **Performance**: Minimize DOM operations and use efficient selectors

**Testing Requirements**:
- **Template Validation**: Verify all required elements are present and functional
- **Interactive Testing**: Test all user interactions and state management
- **Cross-Browser**: Ensure compatibility across supported browsers
- **Performance**: Validate rendering performance with realistic data sets

### Specialized Template Features

The template system includes specialized components for advanced neuron analysis visualizations.

#### Eyemaps Visualization

The eyemaps feature provides spatial coverage analysis for visual system neurons:

**Template Structure**:
```jinja2
<!-- Main eyemaps controller -->
{% if column_analysis.comprehensive_region_grids %}
<section id="eyemaps">
    <h2>Population spatial coverage</h2>
    {% if soma_side == 'both' %}
        {% include "sections/eyemaps_both.html" %}
    {% else %}
        {% include "sections/eyemaps_single.html" %}
    {% endif %}
</section>
{% endif %}
```

**Implementation Features**:
- **Multi-format support**: SVG, PNG, and base64-encoded images
- **Regional analysis**: ME, LO, LOP regions with left/right hemisphere breakdown
- **Dual visualization modes**: Synapse density and cell count grids
- **Responsive layout**: Bootstrap grid system for different screen sizes
- **Conditional rendering**: Only displays when comprehensive region grid data exists

**Data Requirements**:
```python
column_analysis = {
    'comprehensive_region_grids': {
        'ME_L': {
            'synapse_density': '/path/to/me_left_synapse.svg',
            'cell_count': '/path/to/me_left_cells.svg'
        },
        'ME_R': {
            'synapse_density': '/path/to/me_right_synapse.svg', 
            'cell_count': '/path/to/me_right_cells.svg'
        },
        # ... additional regions (LO_L, LO_R, LOP_L, LOP_R)
    }
}
```

**Template Logic**:
- **Region iteration**: Loops through ['ME', 'LO', 'LOP'] regions
- **Side iteration**: Processes both 'L' and 'R' hemispheres
- **Key generation**: Creates region_side_key format (e.g., 'ME_L', 'LO_R')
- **Format detection**: Handles .svg, .png files and base64 data
- **Fallback content**: Shows "No data available" when grids missing

**CSS Classes**:
- `.grid-image`: Styling for hexagonal grid visualizations
- `.no-data-text`: Placeholder text styling for missing data
- Bootstrap responsive classes: `col-md-4`, `col-sm-6`, `col-xs-12`

#### Custom Filter Templates

The template system supports custom Jinja2 filters for specialized processing:

**PNG Data Detection**:
```python
@app.template_filter('is_png_data')
def is_png_data(value):
    """Check if value is base64-encoded PNG data"""
    return isinstance(value, str) and value.startswith('data:image/png;base64,')
```

**Usage in Templates**:
```jinja2
{% if image_data | is_png_data %}
    <img src="{{ image_data }}" alt="Base64 Image" />
{% elif image_data.endswith('.svg') %}
    <object data="{{ image_data }}" type="image/svg+xml">
        <img src="{{ image_data }}" alt="SVG Fallback" />
    </object>
{% endif %}
```

#### Advanced Template Patterns

**Conditional Section Includes**:
```jinja2
<!-- Only include complex sections when data exists -->
{% if layer_analysis and layer_analysis.containers %}
    {% include "sections/layer_analysis.html" %}
{% endif %}

{% if column_analysis.comprehensive_region_grids %}
    {% include "sections/eyemaps.html" %}
{% endif %}
```

**Dynamic Template Selection**:
```jinja2
<!-- Choose template based on data characteristics -->
{% if soma_side == 'both' %}
    {% include "sections/bilateral_analysis.html" %}
{% else %}
    {% include "sections/unilateral_analysis.html" %}
{% endif %}
```

**Safe HTML Rendering**:
```jinja2
<!-- Handle both file paths and embedded SVG content -->
{% if svg_content.startswith('<svg') %}
    {{ svg_content | safe }}
{% else %}
    <object data="{{ svg_content }}" type="image/svg+xml"></object>
{% endif %}
```

## Hexagon Grid Visualization

QuickPage includes a sophisticated hexagonal grid visualization system for spatial neuron analysis, particularly useful for visual system neurons in datasets like the optic lobe connectome.

### HexagonGridGenerator Architecture

The `HexagonGridGenerator` class provides hexagonal grid visualization capabilities with support for multiple output formats and consistent styling.

#### Core Features
- **Multi-format Output**: SVG and PNG generation with consistent styling
- **Region-Specific Analysis**: Separate visualizations for ME, LO, LOP brain regions
- **Dual Metrics**: Support for both synapse density and cell count visualizations
- **Global Color Scaling**: Consistent color ranges across regions for comparison
- **Interactive Elements**: SVG tooltips and embedded interactive features

#### Class Structure
```python
class HexagonGridGenerator:
    def __init__(self, hex_size: int = 6, spacing_factor: float = 1.1):
        """Initialize hexagon grid generator with size and spacing parameters"""
        self.hex_size = hex_size
        self.spacing_factor = spacing_factor
        
    def generate_region_hexagonal_grids(
        self,
        column_summary: List[Dict],
        neuron_type: str, 
        soma_side: str,
        output_format: str = 'svg'
    ) -> Dict[str, Dict[str, str]]:
        """Generate separate grids for each brain region"""
        
    def generate_single_region_grid(
        self,
        region_columns: List[Dict],
        metric_type: str,
        region_name: str,
        global_min: Optional[float] = None,
        global_max: Optional[float] = None,
        neuron_type: Optional[str] = None,
        soma_side: Optional[str] = None,
        output_format: str = 'svg'
    ) -> str:
        """Generate hexagonal grid for single region"""
```

### Data Structures and Formats

#### Column Data Requirements
The visualization system expects column data with specific structure:
```python
column_data = {
    'hex1_dec': int,           # Decimal hex1 coordinate
    'hex2_dec': int,           # Decimal hex2 coordinate  
    'region': str,             # Brain region ('ME', 'LO', 'LOP')
    'side': str,               # Side ('left', 'right')
    'hex1': str,               # Hex string for hex1
    'hex2': str,               # Hex string for hex2
    'total_synapses': float,   # Total synapse count
    'neuron_count': int,       # Number of neurons
    'column_name': str         # Descriptive column name
}
```

#### Hexagon Data Structure
Internal hexagon representation for visualization:
```python
hexagon_data = {
    'x': float,                # X coordinate in pixel space
    'y': float,                # Y coordinate in pixel space
    'value': float,            # Data value for coloring
    'color': str,              # Hex color code
    'region': str,             # Brain region
    'side': str,               # Side
    'hex1': str,               # Hex1 identifier
    'hex2': str,               # Hex2 identifier
    'neuron_count': int,       # Number of neurons
    'column_name': str         # Column identifier
}
```

### Coordinate System Implementation

#### Axial Coordinate Transformation
The system uses axial coordinates for proper hexagonal grid layout:
```python
def hex_to_axial(hex1_coord: int, hex2_coord: int) -> Tuple[int, int]:
    """Convert hex coordinates to axial coordinates"""
    q = -(hex1_coord - hex2_coord) - 3
    r = -hex2_coord
    return q, r

def axial_to_pixel(q: int, r: int, hex_size: float) -> Tuple[float, float]:
    """Convert axial coordinates to pixel coordinates"""
    x = hex_size * (3.0/2 * q)
    y = hex_size * (math.sqrt(3.0)/2 * q + math.sqrt(3.0) * r)
    return x, y
```

### Color Mapping System

#### 5-Tier Color Scheme
Implements consistent red color scheme across all visualizations:
```python
COLOR_TIERS = [
    "#fee5d9",  # Lightest (0-20th percentile)
    "#fcbba1",  # Light (20-40th percentile)
    "#fc9272",  # Medium (40-60th percentile)
    "#ef6548",  # Dark (60-80th percentile)  
    "#a50f15"   # Darkest (80-100th percentile)
]

def get_color_for_value(value: float, min_val: float, max_val: float) -> str:
    """Assign color based on normalized value within global range"""
    if max_val == min_val:
        return COLOR_TIERS[0]
    
    normalized = (value - min_val) / (max_val - min_val)
    tier_index = min(int(normalized * 5), 4)
    return COLOR_TIERS[tier_index]
```

### Output Format Implementation

#### SVG Generation
Direct SVG creation with embedded interactivity:
```python
def generate_svg_hexagon(hexagon: Dict, hex_size: float) -> str:
    """Generate SVG hexagon with tooltip"""
    points = []
    for i in range(6):
        angle = math.pi / 3 * i
        point_x = hexagon['x'] + hex_size * math.cos(angle)
        point_y = hexagon['y'] + hex_size * math.sin(angle)
        points.append(f"{point_x:.2f},{point_y:.2f}")
    
    return f'''
    <polygon points="{' '.join(points)}" 
             fill="{hexagon['color']}" 
             stroke="#333" 
             stroke-width="0.5">
        <title>{hexagon['column_name']}: {hexagon['value']}</title>
    </polygon>
    '''
```

#### PNG Generation
High-quality raster output using PIL:
```python
def generate_png_from_svg(svg_content: str, width: int = 800, height: int = 600) -> str:
    """Convert SVG to base64-encoded PNG"""
    import cairosvg
    from PIL import Image
    import io
    import base64
    
    # Convert SVG to PNG bytes
    png_bytes = cairosvg.svg2png(
        bytestring=svg_content.encode('utf-8'),
        output_width=width,
        output_height=height
    )
    
    # Encode as base64 for embedding
    png_base64 = base64.b64encode(png_bytes).decode('utf-8')
    return f"data:image/png;base64,{png_base64}"
```

### Template Integration

#### Eyemaps Template System
The hexagon visualization integrates with the template system through the eyemaps feature:
```jinja2
<!-- In sections/eyemaps.html -->
{% if column_analysis.comprehensive_region_grids %}
<section id="eyemaps">
    <h2>Population spatial coverage</h2>
    {% for region in ['ME', 'LO', 'LOP'] %}
        {% for side in ['L', 'R'] %}
            {% set region_side_key = region + '_' + side %}
            {% if column_analysis.comprehensive_region_grids.get(region_side_key) %}
                <div class="col-md-4">
                    {% if region_side_key.synapse_density | is_png_data %}
                        <img src="{{ region_side_key.synapse_density }}" 
                             alt="Synapse Density for {{ region }} ({{ side }})" 
                             class="grid-image" />
                    {% else %}
                        {{ region_side_key.synapse_density | safe }}
                    {% endif %}
                </div>
            {% endif %}
        {% endfor %}
    {% endfor %}
</section>
{% endif %}
```

#### Context Data Structure
Template context requires specific data structure:
```python
context['column_analysis'] = {
    'comprehensive_region_grids': {
        'ME_L': {
            'synapse_density': svg_or_png_content,
            'cell_count': svg_or_png_content
        },
        'ME_R': {
            'synapse_density': svg_or_png_content,
            'cell_count': svg_or_png_content
        },
        # Additional regions: LO_L, LO_R, LOP_L, LOP_R
    }
}
```

### Performance Considerations

#### Optimization Strategies
- **SVG Caching**: Cache generated SVG content for repeated requests
- **Lazy Generation**: Generate visualizations only when needed
- **Batch Processing**: Process multiple regions efficiently
- **Memory Management**: Clean up large image data after use

#### Error Handling
```python
def safe_generate_grid(self, column_data: List[Dict], **kwargs) -> Optional[str]:
    """Generate grid with comprehensive error handling"""
    try:
        if not column_data:
            return None
            
        return self.generate_single_region_grid(column_data, **kwargs)
        
    except ValueError as e:
        logger.warning(f"Invalid data for hexagon generation: {e}")
        return None
    except Exception as e:
        logger.error(f"Hexagon generation failed: {e}")
        return None
```

### Testing and Validation

#### Unit Test Structure
```python
def test_hexagon_coordinate_conversion():
    """Test coordinate system transformations"""
    generator = HexagonGridGenerator()
    
    # Test axial conversion
    q, r = generator.hex_to_axial(31, 16)
    assert q == -18
    assert r == -16
    
    # Test pixel conversion
    x, y = generator.axial_to_pixel(q, r, 6.0)
    assert abs(x - (-162.0)) < 0.1
    assert abs(y - (-55.4)) < 0.1

def test_color_mapping():
    """Test color tier assignment"""
    generator = HexagonGridGenerator()
    
    # Test color assignment
    color = generator.get_color_for_value(50.0, 0.0, 100.0)
    assert color == "#fc9272"  # Medium tier for 50th percentile
```

#### Example Usage
A complete working example is available in `examples/example_hexagon_usage.py` demonstrating:
- Sample data creation with proper column structure
- Region-specific grid generation for ME, LO, LOP regions
- Both SVG and PNG output format generation
- File saving and base64 data handling
- Integration with the main PageGenerator workflow

The example shows practical usage patterns and can be used as a starting point for custom implementations.

### Template Customization and Extensions

The modular template architecture enables extensive customization for specific research needs and dataset types.

#### Creating Custom Page Templates

**Basic Custom Template**:
```jinja2
{% extends "base.html" %}
{% from "macros.html" import stat_card, data_table %}

{% block title %}Custom Analysis - {{ analysis_name }}{% endblock %}

{% block content %}
    {% include "sections/header.html" %}
    
    <!-- Custom analysis section -->
    <section class="custom-analysis">
        <h2>{{ analysis_title }}</h2>
        <div class="row">
            {% for metric in custom_metrics %}
                <div class="col-md-4">
                    {{ stat_card(metric.value, metric.label, metric.css_class) }}
                </div>
            {% endfor %}
        </div>
    </section>
    
    {% include "sections/connectivity.html" %}
{% endblock %}

{% block extra_scripts %}
<script>
$(document).ready(function() {
    // Custom JavaScript functionality
    initCustomAnalysis();
});
</script>
{% endblock %}
```

**Dataset-Specific Templates**:
```jinja2
<!-- optic_lobe_neuron.html -->
{% extends "neuron_page.html" %}

{% block content %}
    {{ super() }}
    
    <!-- Add optic lobe specific sections -->
    {% if column_analysis.comprehensive_region_grids %}
        {% include "sections/eyemaps.html" %}
    {% endif %}
    
    {% if visual_pathway_analysis %}
        {% include "sections/visual_pathways.html" %}
    {% endif %}
{% endblock %}
```

#### Advanced Macro Development

**Creating Reusable Components**:
```jinja2
<!-- In macros.html -->
{% macro analysis_chart(data, chart_type="bar", title="", css_class="") %}
<div class="analysis-chart {{ css_class }}">
    {% if title %}
        <h3>{{ title }}</h3>
    {% endif %}
    <div class="chart-container" data-chart-type="{{ chart_type }}">
        {% for item in data %}
            <div class="chart-item" data-value="{{ item.value }}">
                <span class="label">{{ item.label }}</span>
                <span class="value">{{ item.value }}</span>
                <div class="bar" style="width: {{ (item.value / data|map(attribute='value')|max * 100)|round(1) }}%"></div>
            </div>
        {% endfor %}
    </div>
</div>
{% endmacro %}

{% macro region_comparison_table(regions, metrics, neuron_type) %}
<table class="table table-striped region-comparison">
    <thead>
        <tr>
            <th>Region</th>
            {% for metric in metrics %}
                <th>{{ metric.display_name }}</th>
            {% endfor %}
        </tr>
    </thead>
    <tbody>
        {% for region in regions %}
            <tr>
                <td><strong>{{ region.name }}</strong></td>
                {% for metric in metrics %}
                    <td>
                        {% set value = region.get(metric.key, 'N/A') %}
                        {% if metric.formatter == 'percentage' %}
                            {{ "%.1f%%"|format(value) if value != 'N/A' else 'N/A' }}
                        {% elif metric.formatter == 'count' %}
                            {{ "{:,}".format(value) if value != 'N/A' else 'N/A' }}
                        {% else %}
                            {{ value }}
                        {% endif %}
                    </td>
                {% endfor %}
            </tr>
        {% endfor %}
    </tbody>
</table>
{% endmacro %}
```

#### Custom Filter Development

**Registering Custom Jinja2 Filters**:
```python
# In page_generator.py or template setup
@env.filter('format_scientific')
def format_scientific(value, precision=2):
    """Format numbers in scientific notation"""
    if isinstance(value, (int, float)) and value != 0:
        return f"{value:.{precision}e}"
    return str(value)

@env.filter('neuron_type_link')
def neuron_type_link(neuron_type, base_url="/"):
    """Generate links to neuron type pages"""
    safe_name = neuron_type.replace(' ', '_').replace('/', '_')
    return f"{base_url}{safe_name}.html"

@env.filter('hemisphere_badge')
def hemisphere_badge(soma_side):
    """Generate Bootstrap badges for hemisphere information"""
    badges = {
        'L': '<span class="badge badge-primary">Left</span>',
        'R': '<span class="badge badge-success">Right</span>',
        'M': '<span class="badge badge-warning">Middle</span>',
        'undefined': '<span class="badge badge-secondary">Undefined</span>'
    }
    return badges.get(soma_side, '<span class="badge badge-light">Unknown</span>')
```

**Using Custom Filters in Templates**:
```jinja2
<!-- Scientific notation for large numbers -->
<td>{{ synapse_count | format_scientific(1) }}</td>

<!-- Automatic neuron type linking -->
<a href="{{ partner_type | neuron_type_link }}">{{ partner_type }}</a>

<!-- Hemisphere badges -->
{{ neuron.soma_side | hemisphere_badge | safe }}
```

#### Template Extension Patterns

**Conditional Template Loading**:
```python
# In Python code - dynamic template selection
def get_template_for_dataset(dataset_name, neuron_type):
    """Select appropriate template based on dataset and neuron type"""
    template_map = {
        'optic-lobe': {
            'visual_neurons': 'optic_lobe_visual.html',
            'default': 'optic_lobe_neuron.html'
        },
        'hemibrain': {
            'central_complex': 'hemibrain_cx.html',
            'default': 'hemibrain_neuron.html'
        },
        'default': 'neuron_page.html'
    }
    
    dataset_templates = template_map.get(dataset_name, template_map['default'])
    if isinstance(dataset_templates, dict):
        # Check for neuron type specific template
        for pattern, template in dataset_templates.items():
            if pattern != 'default' and pattern in neuron_type.lower():
                return template
        return dataset_templates['default']
    return dataset_templates
```

**Multi-level Template Inheritance**:
```jinja2
<!-- base_neuron.html - extends base.html -->
{% extends "base.html" %}

{% block content %}
    {% include "sections/header.html" %}
    {% block neuron_content %}{% endblock %}
    {% include "sections/footer.html" %}
{% endblock %}

<!-- dataset_specific.html - extends base_neuron.html -->
{% extends "base_neuron.html" %}

{% block neuron_content %}
    {% block dataset_sections %}{% endblock %}
    {% include "sections/connectivity.html" %}
{% endblock %}

<!-- final_template.html - extends dataset_specific.html -->
{% extends "dataset_specific.html" %}

{% block dataset_sections %}
    {% include "sections/summary_stats.html" %}
    {% include "sections/roi_innervation.html" %}
{% endblock %}
```

#### Performance Optimization for Custom Templates

**Template Caching Strategies**:
```python
# Enhanced caching for custom templates
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os

def setup_template_environment(template_dir, cache_dir=None):
    """Setup optimized template environment"""
    loader = FileSystemLoader(template_dir)
    
    env = Environment(
        loader=loader,
        autoescape=select_autoescape(['html', 'xml']),
        cache_size=400,  # Increased cache size
        auto_reload=False,  # Disable in production
    )
    
    if cache_dir:
        # Enable bytecode caching
        env.bytecode_cache = FileSystemBytecodeCache(cache_dir)
    
    return env
```

**Lazy Loading for Large Templates**:
```jinja2
<!-- Conditional expensive sections -->
{% if show_detailed_connectivity %}
    {% include "sections/detailed_connectivity.html" %}
{% else %}
    <div class="lazy-load-placeholder" data-section="detailed_connectivity">
        <button class="btn btn-primary" onclick="loadDetailedConnectivity()">
            Load Detailed Connectivity Analysis
        </button>
    </div>
{% endif %}
```

#### Documentation for Custom Templates

**Template Documentation Format**:
```jinja2
{#
Template: custom_analysis.html
Purpose: Generate custom neuron analysis pages with specialized metrics
Context Requirements:
  - neuron_data: Basic neuron information
  - custom_metrics: List of custom analysis metrics
  - analysis_config: Configuration for analysis display
  - connectivity: Standard connectivity data (optional)
Dependencies:
  - base.html: Base template with standard structure
  - macros.html: UI component macros
  - sections/header.html: Standard header section
Example Usage:
  template = env.get_template('custom_analysis.html')
  context = {
      'neuron_data': neuron_info,
      'custom_metrics': calculated_metrics,
      'analysis_config': analysis_settings
  }
#}
```

## Testing Strategy

### Unit Testing

#### Cell Count Filter Tests

```python
def test_cell_count_ranges():
    """Test cell count range generation"""
    counts = [5, 15, 25, 150, 750]
    ranges = calculate_cell_count_ranges(counts)
    
    expected = [
        {'min': 1, 'max': 10, 'label': '1-10'},
        {'min': 11, 'max': 50, 'label': '11-50'},
        {'min': 51, 'max': 100, 'label': '51-100'},
        {'min': 101, 'max': 500, 'label': '101-500'},
        {'min': 501, 'max': None, 'label': '500+'}
    ]
    
    assert ranges == expected
```

#### JavaScript Compatibility Tests

```python
def test_javascript_compatibility():
    """Test that generated HTML works with JavaScript filters"""
    neuron_data = create_test_neuron_data()
    html = generate_types_page(neuron_data)
    
    # Parse HTML and verify data attributes
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.find_all(class_='neuron-card')
    
    for card in cards:
        assert card.get('data-cell-count')
        assert card.get('data-neurotransmitter')
        assert card.get('data-brain-regions')
```

### Integration Testing

Integration tests verify the complete workflow:

```python
def test_complete_generation_workflow():
    """Test complete neuron page generation"""
    config = load_test_config()
    connector = NeuPrintConnector(config)
    generator = PageGenerator(connector, config)
    
    # Test generation
    result = generator.generate_neuron_page('Dm4', 'both')
    assert result.is_success()
    
    # Verify output files
    output_path = Path('test_output/types/Dm4_both.html')
    assert output_path.exists()
    
    # Verify HTML structure
    html_content = output_path.read_text()
    assert '<title>' in html_content
    assert 'data-cell-count' in html_content
```

### Browser Testing

Automated browser testing using Selenium:

```python
def test_filter_functionality_browser():
    """Test filtering in actual browser"""
    driver = webdriver.Chrome()
    driver.get('file://' + str(Path('test_output/index.html').absolute()))
    
    # Test search filter
    search_input = driver.find_element(By.ID, 'search-input')
    search_input.send_keys('Dm4')
    
    # Wait for filtering to complete
    WebDriverWait(driver, 2).until(
        lambda d: d.find_element(By.ID, 'neuron-count').text != '0'
    )
    
    # Verify results
    visible_cards = driver.find_elements(
        By.CSS_SELECTOR, '.neuron-card:not([style*="display: none"])'
    )
    assert len(visible_cards) > 0
```

## Implementation Details

### Balance Index Enhancement

The balance index feature calculates hemisphere bias for neuron types with enhanced consistency across soma side pages:

```python
def calculate_log_ratio(left_count: int, right_count: int) -> float:
    """Calculate log ratio for hemisphere balance"""
    if left_count is None or right_count is None:
        return None
    
    # Add pseudocounts to avoid division by zero
    adjusted_left = left_count + 0.5
    adjusted_right = right_count + 0.5
    
    # Calculate log2 ratio: positive = left bias, negative = right bias
    ratio = math.log2(adjusted_left / adjusted_right)
    return round(ratio, 2)

def get_hemisphere_balance_analysis(neuron_type: NeuronType) -> Dict[str, Any]:
    """Get comprehensive hemisphere balance analysis"""
    total_left = neuron_type.get_neuron_count('left')
    total_right = neuron_type.get_neuron_count('right')
    
    analysis = {
        'total_left': total_left,
        'total_right': total_right,
        'log_ratio': calculate_log_ratio(total_left, total_right),
        'balance_interpretation': interpret_balance(calculate_log_ratio(total_left, total_right))
    }
    
    return analysis

def interpret_balance(log_ratio: float) -> str:
    """Interpret log ratio values for user understanding"""
    if log_ratio is None:
        return "Unknown - insufficient data"
    elif abs(log_ratio) < 0.1:
        return "Balanced"
    elif log_ratio > 1.0:
        return "Strong left bias"
    elif log_ratio > 0.5:
        return "Moderate left bias"
    elif log_ratio > 0.1:
        return "Slight left bias"
    elif log_ratio < -1.0:
        return "Strong right bias"
    elif log_ratio < -0.5:
        return "Moderate right bias"
    else:
        return "Slight right bias"
```

**Enhanced Template Implementation:**
```html
<!-- Summary Stats Template with Consistent Data -->
<div class="stat-card">
    <h3>Total Neurons</h3>
    <div class="stat-value">{{ hemisphere_analysis.total_left + hemisphere_analysis.total_right }}</div>
    
    <!-- Consistent across all soma side pages -->
    <div class="hemisphere-breakdown">
        <div class="hemisphere-counts">
            <span class="left-count" title="{{ hemisphere_analysis.total_left }} left hemisphere neurons">
                L: {{ hemisphere_analysis.total_left }}
            </span>
            <span class="right-count" title="{{ hemisphere_analysis.total_right }} right hemisphere neurons">
                R: {{ hemisphere_analysis.total_right }}
            </span>
        </div>
        
        {% if hemisphere_analysis.log_ratio is not none %}
        <div class="balance-analysis">
            <span class="log-ratio" title="Log2 ratio: {{ hemisphere_analysis.log_ratio }}">
                Balance: {{ hemisphere_analysis.balance_interpretation }}
            </span>
            <div class="balance-details">
                <small>Log₂ ratio: {{ hemisphere_analysis.log_ratio }}</small>
            </div>
        </div>
        {% endif %}
    </div>
</div>

<!-- Consistent Side Cards showing complete hemisphere data -->
<div class="side-cards">
    <div class="stat-card left-side">
        <h3>Left Hemisphere</h3>
        <div class="stat-value">{{ hemisphere_analysis.total_left }}</div>
        <div class="stat-description">Complete left hemisphere count</div>
    </div>
    
    <div class="stat-card right-side">
        <h3>Right Hemisphere</h3>
        <div class="stat-value">{{ hemisphere_analysis.total_right }}</div>
        <div class="stat-description">Complete right hemisphere count</div>
    </div>
</div>
```

#### Key Features

1. **Consistent Total Neurons Card**: Shows complete neuron type count across all soma side pages
2. **Enhanced Balance Interpretation**: Human-readable balance descriptions
3. **Robust Edge Case Handling**: Graceful handling of None values and zero counts
4. **Detailed Tooltips**: Explanatory tooltips for balance metrics
5. **Cross-Page Consistency**: Identical values displayed on L, R, and both pages

### Unique ID Implementation

Each neuron page includes unique identifiers for consistency:

```python
def generate_unique_id(neuron_type: str, soma_side: str, timestamp: datetime) -> str:
    """Generate unique identifier for neuron page"""
    components = [
        neuron_type,
        soma_side,
        timestamp.strftime('%Y%m%d_%H%M%S'),
        hashlib.md5(f"{neuron_type}_{soma_side}".encode()).hexdigest()[:8]
    ]
    return '_'.join(components)
```

### Help Page Implementation

The help page provides dynamic, context-aware documentation:

```python
def generate_help_page(config: Config) -> str:
    """Generate dynamic help page based on current configuration"""
    template_context = {
        'server': config.neuprint.server,
        'dataset': config.neuprint.dataset,
        'neuron_types': config.neuron_types,
        'features': get_available_features(config),
        'examples': generate_usage_examples(config),
        'troubleshooting': get_troubleshooting_info(config)
    }
    
    return render_template('help.html', **template_context)
```

### Neuroglancer Integration

QuickPage includes sophisticated Neuroglancer integration for 3D visualization with soma side selection support:

```javascript
class NeuroglancerIntegration {
    constructor(server, dataset) {
        this.server = server;
        this.dataset = dataset;
        this.baseUrl = 'https://neuroglancer.janelia.org/';
    }
    
    generateViewerUrl(bodyIds, options = {}) {
        const config = {
            'navigation': {'pose': this.getDefaultPose()},
            'showSlices': options.showSlices || false,
            'layout': options.layout || '3d',
            'layers': [
                this.createDatasetLayer(),
                this.createNeuronLayer(bodyIds, options)
            ]
        };
        
        // Add dataset-specific optimizations
        if (this.dataset.includes('optic-lobe')) {
            config.layers.push(this.createOpticLobeContext());
        }
        
        const encoded = this.encodeConfig(config);
        return `${this.baseUrl}#!${encoded}`;
    }
    
    createNeuronLayer(bodyIds, options = {}) {
        const layer = {
            'type': 'segmentation',
            'source': `neuprint://${this.server}/${this.dataset}`,
            'segments': bodyIds,
            'name': options.name || 'Selected Neurons'
        };
        
        // Add soma side specific styling
        if (options.somaSide) {
            layer.segmentColors = this.generateSomaSideColors(bodyIds, options.somaSide);
        }
        
        return layer;
    }
    
    generateSomaSideColors(bodyIds, somaSide) {
        const colors = {
            'left': '#ff4444',    // Red for left
            'right': '#4444ff',   // Blue for right
            'middle': '#44ff44',  // Green for middle
            'both': '#ffff44'     // Yellow for both
        };
        
        const segmentColors = {};
        bodyIds.forEach(bodyId => {
            segmentColors[bodyId] = colors[somaSide] || colors['both'];
        });
        
        return segmentColors;
    }
    
    createOpticLobeContext() {
        return {
            'type': 'segmentation',
            'source': `neuprint://${this.server}/${this.dataset}`,
            'name': 'Optic Lobe Context',
            'visible': false,
            'segments': this.getOpticLobeContextSegments()
        };
    }
}

// Server-side Neuroglancer URL generation
class NeuroglancerUrlGenerator:
    """Server-side Neuroglancer URL generation with soma side support"""
    
    def __init__(self, config: Config):
        self.server = config.neuprint.server
        self.dataset = config.neuprint.dataset
        self.base_url = "https://neuroglancer.janelia.org/"
    
    def generate_soma_side_url(self, body_ids: List[int], soma_side: str, 
                              neuron_type: str) -> str:
        """Generate Neuroglancer URL for specific soma side"""
        config = {
            "navigation": {"pose": self.get_dataset_pose()},
            "showSlices": False,
            "layout": "3d",
            "layers": [
                self.create_dataset_layer(),
                self.create_soma_side_layer(body_ids, soma_side, neuron_type)
            ]
        }
        
        # Add dataset-specific enhancements
        if "optic-lobe" in self.dataset:
            config["layers"].extend(self.create_optic_lobe_context())
        
        encoded = self.encode_config(config)
        return f"{self.base_url}#!{encoded}"
    
    def create_soma_side_layer(self, body_ids: List[int], soma_side: str, 
                              neuron_type: str) -> Dict:
        """Create layer with soma side specific styling"""
        return {
            "type": "segmentation",
            "source": f"neuprint://{self.server}/{self.dataset}",
            "segments": body_ids,
            "name": f"{neuron_type} ({soma_side.upper()})",
            "segmentColors": self.generate_soma_side_colors(body_ids, soma_side)
        }
```

#### Enhanced Template Integration

```html
<!-- Neuroglancer Links with Soma Side Support -->
<div class="neuroglancer-links">
    <h3>3D Visualization</h3>
    
    <!-- All neurons link -->
    <a href="{{ neuroglancer_url_all }}" 
       target="_blank" 
       class="neuroglancer-link primary">
        <span class="icon">🧠</span>
        View All {{ neuron_type.name }} in Neuroglancer
        <span class="count">[{{ neuron_type.total_count }} neurons]</span>
    </a>
    
    <!-- Soma side specific links -->
    {% if neuron_type.soma_sides_available|length > 1 %}
    <div class="soma-side-neuroglancer">
        {% for side in neuron_type.soma_sides_available %}
        {% if side != 'both' %}
        <a href="{{ neuroglancer_urls[side] }}" 
           target="_blank" 
           class="neuroglancer-link soma-side-link"
           data-side="{{ side }}">
            <span class="side-indicator {{ side }}"></span>
            {{ side|title }} Side Only
            <span class="count">[{{ neuron_type.get_soma_side_count(side) }} neurons]</span>
        </a>
        {% endif %}
        {% endfor %}
    </div>
    {% endif %}
    
    <!-- Context options -->
    <div class="neuroglancer-options">
        <label class="checkbox-option">
            <input type="checkbox" id="show-context" onchange="updateNeuroglancerLinks()">
            Include brain context
        </label>
        <label class="checkbox-option">
            <input type="checkbox" id="show-slices" onchange="updateNeuroglancerLinks()">
            Show brain slices
        </label>
    </div>
</div>
```

### Synonym and FlyWire Tag Filtering

QuickPage includes advanced filtering capabilities for neuron synonyms and FlyWire integration:

```python
class SynonymFilteringService:
    """Handle neuron type synonym filtering and FlyWire tag integration"""
    
    def __init__(self, config: Config):
        self.config = config
        self.synonym_mappings = self.load_synonym_mappings()
        self.flywire_tags = self.load_flywire_tags()
    
    def filter_by_synonyms(self, neuron_types: List[str], 
                          search_term: str) -> List[str]:
        """Filter neuron types by name or synonyms"""
        results = []
        search_lower = search_term.lower()
        
        for neuron_type in neuron_types:
            # Direct name match
            if search_lower in neuron_type.lower():
                results.append(neuron_type)
                continue
            
            # Synonym match
            synonyms = self.synonym_mappings.get(neuron_type, [])
            if any(search_lower in syn.lower() for syn in synonyms):
                results.append(neuron_type)
                continue
            
            # FlyWire tag match
            flywire_tags = self.flywire_tags.get(neuron_type, [])
            if any(search_lower in tag.lower() for tag in flywire_tags):
                results.append(neuron_type)
        
        return results
    
    def get_all_searchable_terms(self, neuron_type: str) -> List[str]:
        """Get all searchable terms for a neuron type"""
        terms = [neuron_type]
        terms.extend(self.synonym_mappings.get(neuron_type, []))
        terms.extend(self.flywire_tags.get(neuron_type, []))
        return list(set(terms))  # Remove duplicates

# Frontend integration
function enhancedNeuronSearch(query) {
    const searchTerms = query.toLowerCase().split(/\s+/);
    
    return NEURON_TYPES_DATA.filter(neuronType => {
        const typeData = NEURON_SEARCH_INDEX[neuronType];
        if (!typeData) return false;
        
        // Search in name, synonyms, and FlyWire tags
        const searchableText = [
            typeData.name,
            ...(typeData.synonyms || []),
            ...(typeData.flywire_tags || [])
        ].join(' ').toLowerCase();
        
        return searchTerms.every(term => searchableText.includes(term));
    });
}
```

## Optimization and Performance

### Cache System Architecture

QuickPage implements a sophisticated multi-level caching system for optimal performance:

#### Cache Types and Performance Results

1. **Neuron Data Cache**: 50.0% hit rate
2. **ROI Hierarchy Cache**: 88.9% hit rate  
3. **Column Cache**: 80.6% performance improvement
4. **Soma Sides Cache**: 100% hit rate for repeat queries
5. **Meta Query Cache**: Automatic database metadata caching

#### Implementation Results

**Performance Metrics:**
- **First run**: ~18.18s (cache miss - expected)
- **Second run**: ~0.38s (97.9% improvement) 
- **Bulk generation**: Progressive cache warming improves performance
- **Cross-session persistence**: Benefits survive application restarts

#### Optimization Summary

```python
# Cache performance monitoring
class CachePerformanceMonitor:
    def generate_performance_report(self) -> Dict[str, Any]:
        return {
            'cache_hit_rates': {
                'neuron_data': self.calculate_hit_rate('neuron'),
                'roi_hierarchy': self.calculate_hit_rate('roi'), 
                'column_cache': self.calculate_hit_rate('column'),
                'soma_sides': self.calculate_hit_rate('soma_sides'),
                'meta_queries': self.calculate_hit_rate('meta')
            },
            'performance_improvements': {
                'single_generation': '97.9%',
                'column_queries': '80.6%', 
                'roi_hierarchy': '88.9%',
                'overall_speedup': '20-50x faster'
            },
            'query_elimination': {
                'column_scans': 'Eliminated expensive all-neuron scans',
                'roi_fetches': 'Minimal fetching with global cache',
                'soma_queries': '0 per-type queries after caching',
                'meta_queries': 'Automatic caching of database metadata'
            }
        }
```

### Single Query Profiler

QuickPage includes detailed query profiling for performance optimization:

```python
class QueryProfiler:
    """Profile individual Cypher queries for optimization"""
    
    def profile_query(self, query: str, params: Dict = None) -> Dict[str, Any]:
        """Profile a single Cypher query with detailed metrics"""
        start_time = time.perf_counter()
        
        # Execute with profiling
        profiled_query = f"PROFILE {query}"
        result = self.client.fetch_custom(profiled_query, params or {})
        
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        
        return {
            'query': query,
            'execution_time_ms': execution_time * 1000,
            'result_count': len(result) if result is not None else 0,
            'query_plan': self.extract_query_plan(result),
            'optimization_suggestions': self.generate_optimization_suggestions(query, execution_time)
        }
    
    def batch_profile_queries(self, queries: List[str]) -> Dict[str, Any]:
        """Profile multiple queries and generate comparative analysis"""
        profiles = []
        total_time = 0
        
        for query in queries:
            profile = self.profile_query(query)
            profiles.append(profile)
            total_time += profile['execution_time_ms']
        
        return {
            'individual_profiles': profiles,
            'total_execution_time_ms': total_time,
            'slowest_query': max(profiles, key=lambda p: p['execution_time_ms']),
            'optimization_opportunities': self.identify_optimization_opportunities(profiles)
        }
```

## Development Workflow

### Code Style and Patterns

#### Python Conventions

- **PEP 8**: Follow Python style guidelines
- **Type Hints**: Use type hints for all function signatures
- **Docstrings**: Google-style docstrings for all public functions
- **Error Handling**: Use Result pattern instead of exceptions

```python
from typing import Result, List, Optional

def fetch_neuron_data(neuron_type: str) -> Result[NeuronData, Error]:
    """
    Fetch neuron data from NeuPrint.
    
    Args:
        neuron_type: Name of the neuron type to fetch
        
    Returns:
        Result containing NeuronData on success or Error on failure
        
    Raises:
        None - Uses Result pattern for error handling
    """
    try:
        data = self._query_neuprint(neuron_type)
        return Result.success(NeuronData.from_dict(data))
    except Exception as e:
        return Result.failure(Error.from_exception(e))
```

#### JavaScript Conventions

- **ES6+**: Use modern JavaScript features
- **Modules**: Organize code into logical modules
- **Error Handling**: Graceful error handling with user feedback
- **Performance**: Debounce user inputs, efficient DOM manipulation

```javascript
// Modern JavaScript patterns
class FilterManager {
    constructor() {
        this.filters = new Map();
        this.subscribers = new Set();
    }
    
    updateFilter(key, value) {
        this.filters.set(key, value);
        this.notifySubscribers();
    }
    
    notifySubscribers() {
        this.subscribers.forEach(callback => {
            try {
                callback(this.filters);
            } catch (error) {
                console.error('Filter callback error:', error);
            }
        });
    }
}
```

### Template Conventions

- **Semantic HTML**: Use appropriate HTML5 semantic elements
- **Accessibility**: Include ARIA labels and proper heading hierarchy
- **Progressive Enhancement**: Ensure functionality without JavaScript
- **Mobile-First**: Responsive design starting with mobile

```html
<!-- Semantic, accessible template structure -->
<section class="neuron-summary" role="main" aria-labelledby="summary-heading">
    <h2 id="summary-heading">{{ neuron_type.name }} Summary</h2>
    
    <div class="summary-stats" role="region" aria-label="Neuron statistics">
        {% for stat in summary_stats %}
            <article class="stat-card">
                <h3>{{ stat.label }}</h3>
                <div class="stat-value" aria-describedby="stat-{{ loop.index }}-desc">
                    {{ stat.value }}
                </div>
                {% if stat.description %}
                    <div id="stat-{{ loop.index }}-desc" class="stat-description">
                        {{ stat.description }}
                    </div>
                {% endif %}
            </article>
        {% endfor %}
    </div>
</section>
```

### Future Considerations

#### Potential Enhancements

1. **WebSocket Support**: Real-time updates from NeuPrint
2. **Progressive Web App**: Offline functionality and app-like experience
3. **Advanced Visualizations**: Interactive plots and charts
4. **Collaborative Features**: User annotations and sharing
5. **API Endpoint**: REST API for programmatic access

#### Scalability Considerations

1. **Database Connection Pooling**: Efficient database resource management
2. **Horizontal Scaling**: Support for multiple NeuPrint instances
3. **Content Delivery Network**: Static asset optimization
4. **Microservices Architecture**: Break into smaller, focused services

## Additional Documentation

The hexagon visualization system has been fully integrated into this developer guide. For other specialized components and data files, refer to:

- **[Input Directory](../input/README.md)**: Documentation for CSV data files including brain regions, citations, and YouTube video mappings that enhance generated websites with metadata and external references.

## Contributing

### Setting Up for Development

1. **Fork the repository** and clone your fork
2. **Create a feature branch**: `git checkout -b feature/new-feature`
3. **Install development dependencies**: `pixi install`
4. **Verify setup**: `pixi run dev`
5. **Make your changes** following the coding standards
6. **Write tests** for new functionality
7. **Update documentation** as needed
8. **Submit a pull request**

### Pull Request Guidelines

- **Clear Description**: Explain what your changes do and why
- **Tests**: Include tests for new features and bug fixes
- **Documentation**: Update relevant documentation
- **Code Style**: Follow existing code style and conventions
- **Atomic Commits**: Make focused, single-purpose commits
- **Rebase**: Keep commit history clean

### Testing Your Changes

```bash
# Test connection to NeuPrint
quickpage test-connection

# Generate test data using the queue system
pixi run test-set

# Clean output directory
pixi run clean-output

# Verify development setup
pixi run dev
```

### Code Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and quality checks
2. **Peer Review**: At least one team member reviews the code
3. **Documentation Review**: Ensure documentation is updated
4. **Manual Testing**: Test changes in development environment
5. **Final Approval**: Maintainer approves and merges

---

This developer guide provides comprehensive technical documentation for contributing to QuickPage. For user-focused documentation, see the [User Guide](user-guide.md).