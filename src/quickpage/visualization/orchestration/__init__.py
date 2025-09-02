"""
Orchestration module for eyemap generation workflows.

This module provides orchestration services that coordinate complex eyemap generation
workflows while maintaining single responsibility principles. The orchestration layer
sits between the main EyemapGenerator interface and the underlying processing services.

Key Components:
- GridGenerationOrchestrator: Coordinates multi-region grid generation workflows
- RequestProcessor: Handles request validation and preprocessing
- ResultAssembler: Assembles and post-processes generation results
- PerformanceManager: Manages performance optimization and monitoring
- Command objects: Encapsulate specific generation operations

Design Principles:
- Single Responsibility: Each class has one clear purpose
- Dependency Injection: All dependencies are injected rather than created
- Error Handling: Comprehensive error context and recovery
- Performance: Optimized workflows with monitoring integration
"""

# Temporarily disable orchestration imports to fix basic system
# TODO: Re-enable after fixing import issues

# from .grid_generation_orchestrator import GridGenerationOrchestrator
# from .request_processor import RequestProcessor
# from .result_assembler import ResultAssembler
# from .performance_manager import PerformanceManager
# from .commands import (
#     GridGenerationCommand,
#     ComprehensiveGridGenerationCommand,
#     SingleRegionGridGenerationCommand
# )

__all__ = [
    # 'GridGenerationOrchestrator',
    # 'RequestProcessor',
    # 'ResultAssembler',
    # 'PerformanceManager',
    # 'GridGenerationCommand',
    # 'ComprehensiveGridGenerationCommand',
    # 'SingleRegionGridGenerationCommand'
]
