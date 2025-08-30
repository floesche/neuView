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

# Import new refactored services
from .page_generation_service import PageGenerationService
from .cache_service import CacheService
from .roi_processing_service import ROIProcessingService
from .soma_detection_service import SomaDetectionService
from .queue_file_manager import QueueFileManager
from .queue_processor import QueueProcessor
from .connection_test_service import ConnectionTestService
from .service_container import ServiceContainer


__all__ = [
    # Modular services from this package
    "IndexService",
    "ROIHierarchyService",
    "NeuronNameService",
    "ROIAnalysisService",
    "IndexGeneratorService",
    "NeuronDiscoveryService",

    # New refactored services
    "PageGenerationService",
    "CacheService",
    "ROIProcessingService",
    "SomaDetectionService",
    "QueueFileManager",
    "QueueProcessor",
    "ConnectionTestService",
    "ServiceContainer",
]
