"""
Services Package

This package contains specialized services that were refactored from the original
monolithic IndexService class. Each service has a focused responsibility and can
be tested and maintained independently.

Core application services (commands, basic services, service container) are in
core_services.py, while this package contains the specialized services for
index creation and related functionality.

Specialized Services:
- IndexService: Coordinates index page creation
- ROIHierarchyService: Manages ROI hierarchy data and caching
- NeuronNameService: Handles neuron name to filename conversion
- ROIAnalysisService: Analyzes ROI data for neuron types
- IndexGeneratorService: Generates various index and helper pages

These services work together to replace the original large IndexService class
while maintaining the same functionality with better separation of concerns.
"""

# Import modular services from this package
from .index_service import IndexService
from .roi_hierarchy_service import ROIHierarchyService
from .neuron_name_service import NeuronNameService
from .roi_analysis_service import ROIAnalysisService
from .index_generator_service import IndexGeneratorService
from .neuron_discovery_service import NeuronDiscoveryService
from .neuron_statistics_service import NeuronStatisticsService
from .layer_analysis_service import LayerAnalysisService
from .column_analysis_service import ColumnAnalysisService
from .url_generation_service import URLGenerationService
from .resource_manager_service import ResourceManagerService
from .template_context_service import TemplateContextService
from .data_processing_service import DataProcessingService
from .database_query_service import DatabaseQueryService

# Import new refactored services
from .page_generation_service import PageGenerationService
from .cache_service import CacheService
from .roi_processing_service import ROIProcessingService
from .soma_detection_service import SomaDetectionService
from .queue_file_manager import QueueFileManager
from .queue_processor import QueueProcessor
from .connection_test_service import ConnectionTestService
from .service_container import ServiceContainer

# Import newly extracted services from page_generator refactoring
from .file_service import FileService
from .threshold_service import ThresholdService
from .threshold_config import (
    ThresholdConfig, ThresholdProfile, ThresholdSettings,
    ThresholdType, ThresholdMethod, get_threshold_config, configure_thresholds
)
from .youtube_service import YouTubeService
from .page_generation_orchestrator import PageGenerationOrchestrator

# Phase 1 extracted services from PageGenerator refactoring
from .brain_region_service import BrainRegionService
from .citation_service import CitationService
from .neuron_search_service import NeuronSearchService
from .partner_analysis_service import PartnerAnalysisService
from .jinja_template_service import JinjaTemplateService

# Phase 3 managers and strategies
from ..managers import TemplateManager, ResourceManager, DependencyManager
from ..strategies import TemplateStrategy, ResourceStrategy, CacheStrategy
from ..strategies.template import (
    JinjaTemplateStrategy,
    StaticTemplateStrategy,
    CompositeTemplateStrategy,
    CachedTemplateStrategy
)
from ..strategies.resource import (
    UnifiedResourceStrategy,
    CompositeResourceStrategy
)
from ..strategies.cache import (
    MemoryCacheStrategy,
    FileCacheStrategy,
    CompositeCacheStrategy
)


__all__ = [
    # Modular services from this package
    "IndexService",
    "ROIHierarchyService",
    "NeuronNameService",
    "ROIAnalysisService",
    "IndexGeneratorService",
    "NeuronDiscoveryService",
    "NeuronStatisticsService",
    "LayerAnalysisService",
    "ColumnAnalysisService",
    "URLGenerationService",
    "ResourceManagerService",
    "TemplateContextService",
    "DataProcessingService",
    "DatabaseQueryService",

    # New refactored services
    "PageGenerationService",
    "CacheService",
    "ROIProcessingService",
    "SomaDetectionService",
    "QueueFileManager",
    "QueueProcessor",
    "ConnectionTestService",
    "ServiceContainer",

    # Newly extracted services from page_generator refactoring
    "FileService",
    "ThresholdService",
    "ThresholdConfig",
    "ThresholdProfile",
    "ThresholdSettings",
    "ThresholdType",
    "ThresholdMethod",
    "get_threshold_config",
    "configure_thresholds",
    "YouTubeService",
    "PageGenerationOrchestrator",

    # Phase 1 extracted services from PageGenerator refactoring
    "BrainRegionService",
    "CitationService",
    "NeuronSearchService",
    "PartnerAnalysisService",
    "JinjaTemplateService",

    # Phase 3 managers and strategies
    "TemplateManager",
    "ResourceManager",
    "DependencyManager",
    "TemplateStrategy",
    "ResourceStrategy",
    "CacheStrategy",
    "JinjaTemplateStrategy",
    "StaticTemplateStrategy",
    "CompositeTemplateStrategy",
    "CachedTemplateStrategy",
    "UnifiedResourceStrategy",
    "CompositeResourceStrategy",
    "MemoryCacheStrategy",
    "FileCacheStrategy",
    "CompositeCacheStrategy",
]
