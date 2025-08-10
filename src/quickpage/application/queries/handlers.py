"""
CQRS Query Handlers for QuickPage Application

This module implements the Query side of Command Query Responsibility Segregation (CQRS).
Query handlers are responsible for:
- Processing read-only queries
- Returning DTOs instead of domain entities
- Optimizing for read performance
- Providing different views of the data

Key Principles:
- Queries don't modify state
- Return DTOs optimized for specific use cases
- Can bypass domain model for performance
- Support different projections of the same data
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Generic, TypeVar
from datetime import datetime

from ...core.entities import Neuron, NeuronCollection
from ...core.value_objects import NeuronTypeName, SomaSide, BodyId, RoiName
from ...core.ports import NeuronRepository, ConnectivityRepository
from ...core.specifications import (
    Specification, HighQualityNeuronSpecification, BilateralNeuronSpecification,
    SomaSideSpecification, HasRoiSpecification
)
from ...shared.result import Result, Ok, Err

# Generic types for queries and results
Q = TypeVar('Q')  # Query type
R = TypeVar('R')  # Result type


# Base Query and Handler interfaces

class Query(ABC):
    """Base class for all queries."""
    pass


class QueryHandler(ABC, Generic[Q, R]):
    """Base class for all query handlers."""

    @abstractmethod
    async def handle(self, query: Q) -> Result[R, str]:
        """Handle the query and return a result."""
        pass


# DTOs (Data Transfer Objects) for query results

@dataclass
class NeuronSummaryDTO:
    """DTO for neuron summary information."""
    body_id: int
    neuron_type: str
    soma_side: str
    total_synapses: int
    pre_synapses: int
    post_synapses: int
    pre_post_ratio: float
    roi_count: int
    primary_rois: List[str]  # Top 3 ROIs by synapse count

    @classmethod
    def from_neuron(cls, neuron: Neuron) -> 'NeuronSummaryDTO':
        """Create DTO from domain entity."""
        # Calculate primary ROIs
        roi_items = list(neuron.roi_counts.items())
        roi_items.sort(key=lambda x: x[1].value, reverse=True)
        primary_rois = [roi.value for roi, _ in roi_items[:3]]

        post_count = neuron.synapse_stats.post_synapses.value
        pre_post_ratio = (
            neuron.synapse_stats.pre_synapses.value / post_count
            if post_count > 0 else 0.0
        )

        return cls(
            body_id=neuron.body_id.value,
            neuron_type=str(neuron.neuron_type),
            soma_side=str(neuron.soma_side),
            total_synapses=neuron.get_total_synapses().value,
            pre_synapses=neuron.synapse_stats.pre_synapses.value,
            post_synapses=neuron.synapse_stats.post_synapses.value,
            pre_post_ratio=pre_post_ratio,
            roi_count=len(neuron.roi_counts),
            primary_rois=primary_rois
        )


@dataclass
class NeuronTypeStatisticsDTO:
    """DTO for neuron type statistics."""
    type_name: str
    total_count: int
    left_count: int
    right_count: int
    middle_count: int
    bilateral_ratio: float
    avg_synapses: float
    median_synapses: float
    std_dev_synapses: float
    quality_score: float
    top_rois: List[Dict[str, Any]]  # ROI name and average synapse count

    @classmethod
    def from_collection_and_analysis(
        cls,
        collection: NeuronCollection,
        analysis_result: Any
    ) -> 'NeuronTypeStatisticsDTO':
        """Create DTO from collection and analysis result."""
        stats = collection.calculate_statistics()

        # Calculate additional statistics
        synapse_counts = [n.get_total_synapses().value for n in collection.neurons]
        import statistics as stat_module

        median_synapses = stat_module.median(synapse_counts) if synapse_counts else 0
        std_dev = stat_module.stdev(synapse_counts) if len(synapse_counts) > 1 else 0

        # Calculate bilateral ratio
        total = len(collection.neurons)
        bilateral_ratio = (stats.left_count + stats.right_count) / total if total > 0 else 0

        # Get top ROIs by frequency and average synapse count
        roi_stats = {}
        for neuron in collection.neurons:
            for roi, count in neuron.roi_counts.items():
                if roi.value not in roi_stats:
                    roi_stats[roi.value] = {'total': 0, 'neurons': 0}
                roi_stats[roi.value]['total'] += count.value
                roi_stats[roi.value]['neurons'] += 1

        top_rois = []
        for roi_name, data in roi_stats.items():
            avg_count = data['total'] / data['neurons']
            top_rois.append({
                'name': roi_name,
                'avg_synapses': avg_count,
                'neuron_count': data['neurons']
            })

        top_rois.sort(key=lambda x: x['avg_synapses'], reverse=True)
        top_rois = top_rois[:10]  # Top 10 ROIs

        return cls(
            type_name=str(stats.type_name),
            total_count=stats.total_count,
            left_count=stats.left_count,
            right_count=stats.right_count,
            middle_count=stats.middle_count,
            bilateral_ratio=bilateral_ratio,
            avg_synapses=stats.avg_pre_synapses + stats.avg_post_synapses,
            median_synapses=median_synapses,
            std_dev_synapses=std_dev,
            quality_score=getattr(analysis_result, 'quality_score', 0.8),
            top_rois=top_rois
        )


@dataclass
class ConnectivitySummaryDTO:
    """DTO for connectivity summary."""
    source_type: str
    target_types: List[Dict[str, Any]]  # target type and connection strength
    input_types: List[Dict[str, Any]]   # input type and connection strength
    connection_count: int
    avg_connection_strength: float


# Query classes

@dataclass
class GetNeuronTypeDetailQuery(Query):
    """Query to get detailed information about a neuron type."""
    neuron_type: str
    soma_side: Optional[str] = None
    include_connectivity: bool = False
    include_individual_neurons: bool = False
    min_synapse_count: int = 0


@dataclass
class SearchNeuronsQuery(Query):
    """Query to search neurons with various filters."""
    neuron_type: Optional[str] = None
    soma_side: Optional[str] = None
    min_synapses: Optional[int] = None
    max_synapses: Optional[int] = None
    required_rois: List[str] = None
    high_quality_only: bool = False
    limit: int = 100
    offset: int = 0


@dataclass
class GetNeuronTypeComparisonQuery(Query):
    """Query to compare multiple neuron types."""
    neuron_types: List[str]
    comparison_metrics: List[str] = None  # e.g., ['synapse_count', 'roi_distribution', 'bilateral_symmetry']


@dataclass
class GetConnectivityPatternQuery(Query):
    """Query to analyze connectivity patterns."""
    neuron_type: str
    pattern_type: str = 'all'  # 'input', 'output', 'bidirectional', 'all'
    min_connection_strength: float = 0.1
    include_indirect: bool = False


# Result DTOs

@dataclass
class NeuronTypeDetailResult:
    """Result for detailed neuron type query."""
    statistics: NeuronTypeStatisticsDTO
    connectivity: Optional[ConnectivitySummaryDTO]
    individual_neurons: List[NeuronSummaryDTO]
    quality_assessment: Dict[str, Any]
    bilateral_analysis: Dict[str, Any]


@dataclass
class NeuronSearchResult:
    """Result for neuron search query."""
    neurons: List[NeuronSummaryDTO]
    total_count: int
    filtered_count: int
    search_criteria: Dict[str, Any]
    facets: Dict[str, List[Dict[str, Any]]]  # For UI faceted search


@dataclass
class NeuronTypeComparisonResult:
    """Result for neuron type comparison query."""
    comparison_matrix: Dict[str, Dict[str, float]]
    similarities: List[Dict[str, Any]]
    differences: List[Dict[str, Any]]
    recommendations: List[str]


# Query Handlers

class GetNeuronTypeDetailQueryHandler(QueryHandler[GetNeuronTypeDetailQuery, NeuronTypeDetailResult]):
    """Handler for detailed neuron type queries."""

    def __init__(
        self,
        neuron_repository: NeuronRepository,
        connectivity_repository: ConnectivityRepository,
        analysis_service: Any  # Would import from domain services
    ):
        self.neuron_repository = neuron_repository
        self.connectivity_repository = connectivity_repository
        self.analysis_service = analysis_service

    async def handle(self, query: GetNeuronTypeDetailQuery) -> Result[NeuronTypeDetailResult, str]:
        """Handle the detailed neuron type query."""
        try:
            neuron_type = NeuronTypeName(query.neuron_type)
            soma_side = SomaSide(query.soma_side) if query.soma_side else SomaSide('all')

            # Get neuron collection
            collection_result = await self.neuron_repository.find_by_type_and_side(
                neuron_type, soma_side
            )

            if collection_result.is_err():
                return Err(collection_result.error)

            collection = collection_result.value

            if collection.is_empty():
                return Err(f"No neurons found for type {query.neuron_type}")

            # Filter by minimum synapse count if specified
            if query.min_synapse_count > 0:
                spec = SynapseCountRangeSpecification(min_count=query.min_synapse_count)
                filtered_neurons = [n for n in collection.neurons if spec.is_satisfied_by(n)]
                collection.neurons = filtered_neurons

            # Perform analysis
            analysis_result = self.analysis_service.analyze_neuron_collection_quality(collection)
            bilateral_analysis = self.analysis_service.assess_bilateral_symmetry(collection)

            # Create statistics DTO
            statistics = NeuronTypeStatisticsDTO.from_collection_and_analysis(
                collection, analysis_result
            )

            # Get connectivity if requested
            connectivity = None
            if query.include_connectivity:
                connectivity_result = await self.connectivity_repository.get_connectivity_for_type(
                    neuron_type
                )
                if connectivity_result.is_ok():
                    # Convert to DTO (would need actual connectivity data structure)
                    connectivity = ConnectivitySummaryDTO(
                        source_type=query.neuron_type,
                        target_types=[],  # Would populate from actual data
                        input_types=[],   # Would populate from actual data
                        connection_count=0,
                        avg_connection_strength=0.0
                    )

            # Get individual neurons if requested
            individual_neurons = []
            if query.include_individual_neurons:
                individual_neurons = [
                    NeuronSummaryDTO.from_neuron(neuron)
                    for neuron in collection.neurons
                ]

            result = NeuronTypeDetailResult(
                statistics=statistics,
                connectivity=connectivity,
                individual_neurons=individual_neurons,
                quality_assessment={
                    'score': analysis_result.quality_score,
                    'outlier_count': len(analysis_result.outliers),
                    'recommendations': analysis_result.recommendations
                },
                bilateral_analysis=bilateral_analysis
            )

            return Ok(result)

        except Exception as e:
            return Err(f"Failed to get neuron type details: {str(e)}")


class SearchNeuronsQueryHandler(QueryHandler[SearchNeuronsQuery, NeuronSearchResult]):
    """Handler for neuron search queries."""

    def __init__(self, neuron_repository: NeuronRepository):
        self.neuron_repository = neuron_repository

    async def handle(self, query: SearchNeuronsQuery) -> Result[NeuronSearchResult, str]:
        """Handle the neuron search query."""
        try:
            # Build search criteria
            search_criteria = {
                'neuron_type': query.neuron_type,
                'soma_side': query.soma_side,
                'min_synapses': query.min_synapses,
                'max_synapses': query.max_synapses,
                'required_rois': query.required_rois or [],
                'high_quality_only': query.high_quality_only
            }

            # Get initial collection
            if query.neuron_type:
                neuron_type = NeuronTypeName(query.neuron_type)
                soma_side = SomaSide(query.soma_side) if query.soma_side else SomaSide('all')

                collection_result = await self.neuron_repository.find_by_type_and_side(
                    neuron_type, soma_side
                )

                if collection_result.is_err():
                    return Err(collection_result.error)

                collection = collection_result.value
            else:
                # Would need a method to get all neurons or specific filtering
                return Err("Neuron type must be specified for search")

            # Apply specifications for filtering
            filtered_neurons = collection.neurons

            # Apply synapse count filters
            if query.min_synapses is not None or query.max_synapses is not None:
                min_count = query.min_synapses or 0
                max_count = query.max_synapses or float('inf')
                spec = SynapseCountRangeSpecification(min_count, max_count)
                filtered_neurons = [n for n in filtered_neurons if spec.is_satisfied_by(n)]

            # Apply ROI filters
            if query.required_rois:
                for roi_name in query.required_rois:
                    roi = RoiName(roi_name)
                    spec = HasRoiSpecification(roi)
                    filtered_neurons = [n for n in filtered_neurons if spec.is_satisfied_by(n)]

            # Apply quality filter
            if query.high_quality_only:
                spec = HighQualityNeuronSpecification()
                filtered_neurons = [n for n in filtered_neurons if spec.is_satisfied_by(n)]

            # Apply pagination
            total_filtered = len(filtered_neurons)
            start_idx = query.offset
            end_idx = min(start_idx + query.limit, total_filtered)
            paginated_neurons = filtered_neurons[start_idx:end_idx]

            # Convert to DTOs
            neuron_dtos = [NeuronSummaryDTO.from_neuron(neuron) for neuron in paginated_neurons]

            # Generate facets for UI
            facets = self._generate_facets(filtered_neurons)

            result = NeuronSearchResult(
                neurons=neuron_dtos,
                total_count=len(collection.neurons),
                filtered_count=total_filtered,
                search_criteria=search_criteria,
                facets=facets
            )

            return Ok(result)

        except Exception as e:
            return Err(f"Failed to search neurons: {str(e)}")

    def _generate_facets(self, neurons: List[Neuron]) -> Dict[str, List[Dict[str, Any]]]:
        """Generate facets for filtered search results."""
        # Soma side facets
        soma_sides = {}
        for neuron in neurons:
            side = str(neuron.soma_side)
            soma_sides[side] = soma_sides.get(side, 0) + 1

        # ROI facets
        roi_counts = {}
        for neuron in neurons:
            for roi in neuron.roi_counts.keys():
                roi_name = roi.value
                roi_counts[roi_name] = roi_counts.get(roi_name, 0) + 1

        # Synapse count ranges
        synapse_ranges = {
            '0-99': 0,
            '100-499': 0,
            '500-999': 0,
            '1000-4999': 0,
            '5000+': 0
        }

        for neuron in neurons:
            count = neuron.get_total_synapses().value
            if count < 100:
                synapse_ranges['0-99'] += 1
            elif count < 500:
                synapse_ranges['100-499'] += 1
            elif count < 1000:
                synapse_ranges['500-999'] += 1
            elif count < 5000:
                synapse_ranges['1000-4999'] += 1
            else:
                synapse_ranges['5000+'] += 1

        return {
            'soma_side': [
                {'name': side, 'count': count}
                for side, count in soma_sides.items()
            ],
            'roi': [
                {'name': roi, 'count': count}
                for roi, count in sorted(roi_counts.items(), key=lambda x: x[1], reverse=True)[:20]
            ],
            'synapse_range': [
                {'name': range_name, 'count': count}
                for range_name, count in synapse_ranges.items() if count > 0
            ]
        }


class GetNeuronTypeComparisonQueryHandler(QueryHandler[GetNeuronTypeComparisonQuery, NeuronTypeComparisonResult]):
    """Handler for neuron type comparison queries."""

    def __init__(
        self,
        neuron_repository: NeuronRepository,
        analysis_service: Any
    ):
        self.neuron_repository = neuron_repository
        self.analysis_service = analysis_service

    async def handle(self, query: GetNeuronTypeComparisonQuery) -> Result[NeuronTypeComparisonResult, str]:
        """Handle the neuron type comparison query."""
        try:
            # Get collections for all requested types
            collections = {}
            for type_name in query.neuron_types:
                neuron_type = NeuronTypeName(type_name)
                collection_result = await self.neuron_repository.find_by_type(neuron_type)

                if collection_result.is_err():
                    continue  # Skip types that can't be found

                collections[type_name] = collection_result.value

            if len(collections) < 2:
                return Err("Need at least 2 valid neuron types for comparison")

            # Perform pairwise comparisons
            comparison_matrix = {}
            similarities = []
            differences = []

            type_names = list(collections.keys())
            for i in range(len(type_names)):
                comparison_matrix[type_names[i]] = {}
                for j in range(len(type_names)):
                    if i != j:
                        comparison_result = self.analysis_service.compare_neuron_collections(
                            collections[type_names[i]],
                            collections[type_names[j]]
                        )

                        similarity_score = comparison_result.get('synapse_count_similarity', 0)
                        comparison_matrix[type_names[i]][type_names[j]] = similarity_score

                        if similarity_score > 0.8:
                            similarities.append({
                                'type1': type_names[i],
                                'type2': type_names[j],
                                'similarity': similarity_score,
                                'common_features': ['high_synapse_similarity']
                            })
                        elif similarity_score < 0.3:
                            differences.append({
                                'type1': type_names[i],
                                'type2': type_names[j],
                                'difference_score': 1 - similarity_score,
                                'key_differences': ['synapse_count_distribution']
                            })

            # Generate recommendations
            recommendations = []
            if len(similarities) > 0:
                recommendations.append("Some neuron types show high similarity - consider grouping analysis")
            if len(differences) > len(similarities):
                recommendations.append("Neuron types show significant differences - individual analysis recommended")

            result = NeuronTypeComparisonResult(
                comparison_matrix=comparison_matrix,
                similarities=similarities,
                differences=differences,
                recommendations=recommendations
            )

            return Ok(result)

        except Exception as e:
            return Err(f"Failed to compare neuron types: {str(e)}")


# Query Bus for handling queries

class QueryBus:
    """Central query bus that routes queries to appropriate handlers."""

    def __init__(self):
        self._handlers: Dict[type, QueryHandler] = {}

    def register_handler(self, query_type: type, handler: QueryHandler) -> None:
        """Register a query handler for a specific query type."""
        self._handlers[query_type] = handler

    async def handle(self, query: Query) -> Result[Any, str]:
        """Handle a query by routing it to the appropriate handler."""
        query_type = type(query)

        if query_type not in self._handlers:
            return Err(f"No handler registered for query type {query_type.__name__}")

        handler = self._handlers[query_type]
        return await handler.handle(query)

    def clear_handlers(self) -> None:
        """Clear all registered handlers (useful for testing)."""
        self._handlers.clear()


# Global query bus instance
_global_query_bus: Optional[QueryBus] = None


def get_query_bus() -> QueryBus:
    """Get the global query bus instance."""
    global _global_query_bus
    if _global_query_bus is None:
        _global_query_bus = QueryBus()
    return _global_query_bus


def set_query_bus(query_bus: QueryBus) -> None:
    """Set the global query bus instance."""
    global _global_query_bus
    _global_query_bus = query_bus


async def execute_query(query: Query) -> Result[Any, str]:
    """Convenience function to execute a query using the global query bus."""
    return await get_query_bus().handle(query)
