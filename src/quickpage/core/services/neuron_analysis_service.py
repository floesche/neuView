"""
Neuron Analysis Domain Service

This domain service provides complex analysis operations for neurons and neuron collections
that don't belong to any single entity. It coordinates between multiple domain objects
to perform sophisticated analysis and quality assessment operations.
"""

from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
import statistics

from ..entities import Neuron, NeuronCollection
from ..value_objects import (
    SynapseCount, RoiName, SomaSide, NeuronTypeName, BodyId, SynapseStatistics
)


@dataclass
class NeuronAnalysisResult:
    """Value object containing results of neuron analysis."""
    analyzed_at: datetime
    total_neurons: int
    quality_score: float
    outliers: List[BodyId]
    statistical_summary: Dict[str, float]
    recommendations: List[str]

    def is_high_quality(self) -> bool:
        """Check if the analysis indicates high quality data."""
        return self.quality_score >= 0.8

    def has_outliers(self) -> bool:
        """Check if outliers were detected."""
        return len(self.outliers) > 0


@dataclass
class ConnectivityPattern:
    """Value object representing a connectivity pattern."""
    pattern_type: str
    strength: float
    participating_neurons: List[BodyId]
    roi_involvement: List[RoiName]
    confidence: float

    def is_significant(self) -> bool:
        """Check if the pattern is statistically significant."""
        return self.confidence >= 0.95 and self.strength >= 0.3


class NeuronAnalysisService:
    """
    Domain service for neuron analysis operations.

    This service provides complex analysis capabilities that coordinate
    between multiple neurons and collections to derive insights about
    neuron populations, connectivity patterns, and data quality.
    """

    def analyze_neuron_collection_quality(
        self,
        collection: NeuronCollection
    ) -> NeuronAnalysisResult:
        """
        Perform comprehensive quality analysis on a neuron collection.

        This method evaluates data completeness, consistency, outlier detection,
        and overall quality metrics for the entire collection.
        """
        if collection.is_empty():
            return NeuronAnalysisResult(
                analyzed_at=datetime.now(),
                total_neurons=0,
                quality_score=0.0,
                outliers=[],
                statistical_summary={},
                recommendations=["Collection is empty"]
            )

        # Calculate statistical metrics
        synapse_counts = [neuron.get_total_synapses().value for neuron in collection.neurons]
        pre_counts = [neuron.synapse_stats.pre_synapses.value for neuron in collection.neurons]
        post_counts = [neuron.synapse_stats.post_synapses.value for neuron in collection.neurons]

        statistical_summary = {
            'mean_synapses': statistics.mean(synapse_counts),
            'median_synapses': statistics.median(synapse_counts),
            'std_dev_synapses': statistics.stdev(synapse_counts) if len(synapse_counts) > 1 else 0,
            'mean_pre_synapses': statistics.mean(pre_counts),
            'mean_post_synapses': statistics.mean(post_counts),
            'pre_post_ratio_avg': statistics.mean(pre_counts) / statistics.mean(post_counts) if statistics.mean(post_counts) > 0 else 0
        }

        # Detect outliers using IQR method
        outliers = self._detect_outliers(collection, synapse_counts)

        # Calculate quality score
        quality_score = self._calculate_quality_score(collection, statistical_summary, outliers)

        # Generate recommendations
        recommendations = self._generate_recommendations(collection, statistical_summary, outliers)

        return NeuronAnalysisResult(
            analyzed_at=datetime.now(),
            total_neurons=len(collection.neurons),
            quality_score=quality_score,
            outliers=[neuron.body_id for neuron in outliers],
            statistical_summary=statistical_summary,
            recommendations=recommendations
        )

    def compare_neuron_collections(
        self,
        collection1: NeuronCollection,
        collection2: NeuronCollection
    ) -> Dict[str, any]:
        """
        Compare two neuron collections and identify differences and similarities.

        This analysis helps understand relationships between different neuron types
        or the same type across different datasets.
        """
        if collection1.is_empty() or collection2.is_empty():
            return {
                'comparison_valid': False,
                'reason': 'One or both collections are empty'
            }

        analysis1 = self.analyze_neuron_collection_quality(collection1)
        analysis2 = self.analyze_neuron_collection_quality(collection2)

        return {
            'comparison_valid': True,
            'collection1_stats': analysis1.statistical_summary,
            'collection2_stats': analysis2.statistical_summary,
            'size_difference': len(collection2.neurons) - len(collection1.neurons),
            'quality_difference': analysis2.quality_score - analysis1.quality_score,
            'synapse_count_similarity': self._calculate_distribution_similarity(
                [n.get_total_synapses().value for n in collection1.neurons],
                [n.get_total_synapses().value for n in collection2.neurons]
            ),
            'roi_overlap': len(set(collection1.get_unique_rois()) & set(collection2.get_unique_rois())),
            'common_rois': list(set(collection1.get_unique_rois()) & set(collection2.get_unique_rois())),
            'unique_to_collection1': list(set(collection1.get_unique_rois()) - set(collection2.get_unique_rois())),
            'unique_to_collection2': list(set(collection2.get_unique_rois()) - set(collection1.get_unique_rois()))
        }

    def identify_connectivity_patterns(
        self,
        collection: NeuronCollection,
        min_pattern_strength: float = 0.3
    ) -> List[ConnectivityPattern]:
        """
        Identify significant connectivity patterns within a neuron collection.

        This method analyzes ROI distributions and synapse patterns to identify
        common connectivity motifs and significant patterns.
        """
        if collection.is_empty():
            return []

        patterns = []

        # Analyze ROI co-occurrence patterns
        roi_patterns = self._analyze_roi_cooccurrence(collection)
        for pattern_data in roi_patterns:
            if pattern_data['strength'] >= min_pattern_strength:
                patterns.append(ConnectivityPattern(
                    pattern_type="roi_cooccurrence",
                    strength=pattern_data['strength'],
                    participating_neurons=pattern_data['neurons'],
                    roi_involvement=pattern_data['rois'],
                    confidence=pattern_data['confidence']
                ))

        # Analyze synapse ratio patterns
        ratio_patterns = self._analyze_synapse_ratio_patterns(collection)
        for pattern_data in ratio_patterns:
            if pattern_data['strength'] >= min_pattern_strength:
                patterns.append(ConnectivityPattern(
                    pattern_type="synapse_ratio",
                    strength=pattern_data['strength'],
                    participating_neurons=pattern_data['neurons'],
                    roi_involvement=pattern_data.get('rois', []),
                    confidence=pattern_data['confidence']
                ))

        return patterns

    def assess_bilateral_symmetry(
        self,
        collection: NeuronCollection
    ) -> Dict[str, any]:
        """
        Assess bilateral symmetry in a neuron collection.

        This analysis compares left and right hemisphere neurons to evaluate
        symmetry in count, synapse distribution, and connectivity patterns.
        """
        left_neurons = collection.get_neurons_by_side('left')
        right_neurons = collection.get_neurons_by_side('right')

        if not left_neurons or not right_neurons:
            return {
                'has_bilateral_data': False,
                'left_count': len(left_neurons),
                'right_count': len(right_neurons),
                'symmetry_score': 0.0
            }

        # Count symmetry
        count_ratio = min(len(left_neurons), len(right_neurons)) / max(len(left_neurons), len(right_neurons))

        # Synapse distribution symmetry
        left_synapses = [n.get_total_synapses().value for n in left_neurons]
        right_synapses = [n.get_total_synapses().value for n in right_neurons]

        synapse_symmetry = self._calculate_distribution_similarity(left_synapses, right_synapses)

        # ROI distribution symmetry
        left_rois = set()
        right_rois = set()

        for neuron in left_neurons:
            left_rois.update(neuron.roi_counts.keys())

        for neuron in right_neurons:
            right_rois.update(neuron.roi_counts.keys())

        roi_overlap = len(left_rois & right_rois)
        roi_union = len(left_rois | right_rois)
        roi_symmetry = roi_overlap / roi_union if roi_union > 0 else 0

        # Overall symmetry score
        symmetry_score = (count_ratio + synapse_symmetry + roi_symmetry) / 3

        return {
            'has_bilateral_data': True,
            'left_count': len(left_neurons),
            'right_count': len(right_neurons),
            'count_ratio': count_ratio,
            'synapse_symmetry': synapse_symmetry,
            'roi_symmetry': roi_symmetry,
            'symmetry_score': symmetry_score,
            'left_unique_rois': list(left_rois - right_rois),
            'right_unique_rois': list(right_rois - left_rois),
            'common_rois': list(left_rois & right_rois)
        }

    def _detect_outliers(
        self,
        collection: NeuronCollection,
        synapse_counts: List[int]
    ) -> List[Neuron]:
        """Detect outlier neurons using statistical methods."""
        if len(synapse_counts) < 4:
            return []

        # Use IQR method for outlier detection
        q1 = statistics.quantiles(synapse_counts, n=4)[0]
        q3 = statistics.quantiles(synapse_counts, n=4)[2]
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = []
        for neuron in collection.neurons:
            synapse_count = neuron.get_total_synapses().value
            if synapse_count < lower_bound or synapse_count > upper_bound:
                outliers.append(neuron)

        return outliers

    def _calculate_quality_score(
        self,
        collection: NeuronCollection,
        stats: Dict[str, float],
        outliers: List[Neuron]
    ) -> float:
        """Calculate overall quality score for the collection."""
        score = 1.0

        # Penalize for too many outliers
        outlier_ratio = len(outliers) / len(collection.neurons)
        if outlier_ratio > 0.1:  # More than 10% outliers
            score -= 0.2

        # Penalize for very low synapse counts
        if stats['mean_synapses'] < 10:
            score -= 0.3

        # Penalize for very high coefficient of variation
        cv = stats['std_dev_synapses'] / stats['mean_synapses'] if stats['mean_synapses'] > 0 else 0
        if cv > 1.0:  # Very high variability
            score -= 0.2

        # Bonus for good bilateral representation
        if collection.has_bilateral_neurons():
            score += 0.1

        # Bonus for having ROI data
        if collection.get_unique_rois():
            score += 0.1

        return max(0.0, min(1.0, score))

    def _generate_recommendations(
        self,
        collection: NeuronCollection,
        stats: Dict[str, float],
        outliers: List[Neuron]
    ) -> List[str]:
        """Generate recommendations based on analysis results."""
        recommendations = []

        if len(outliers) > 0:
            recommendations.append(f"Review {len(outliers)} outlier neurons for data quality issues")

        if stats['mean_synapses'] < 10:
            recommendations.append("Low average synapse count may indicate incomplete data")

        if not collection.has_bilateral_neurons():
            recommendations.append("Consider including bilateral data for more complete analysis")

        if len(collection.get_unique_rois()) < 3:
            recommendations.append("Limited ROI coverage may affect connectivity analysis")

        cv = stats['std_dev_synapses'] / stats['mean_synapses'] if stats['mean_synapses'] > 0 else 0
        if cv > 1.0:
            recommendations.append("High variability in synapse counts warrants investigation")

        if len(collection.neurons) < 5:
            recommendations.append("Small sample size may limit statistical reliability")

        return recommendations

    def _calculate_distribution_similarity(
        self,
        dist1: List[float],
        dist2: List[float]
    ) -> float:
        """Calculate similarity between two distributions."""
        if not dist1 or not dist2:
            return 0.0

        # Simple similarity based on mean and standard deviation comparison
        mean1, mean2 = statistics.mean(dist1), statistics.mean(dist2)
        std1 = statistics.stdev(dist1) if len(dist1) > 1 else 0
        std2 = statistics.stdev(dist2) if len(dist2) > 1 else 0

        mean_similarity = 1.0 - abs(mean1 - mean2) / max(mean1, mean2) if max(mean1, mean2) > 0 else 1.0
        std_similarity = 1.0 - abs(std1 - std2) / max(std1, std2) if max(std1, std2) > 0 else 1.0

        return (mean_similarity + std_similarity) / 2

    def _analyze_roi_cooccurrence(self, collection: NeuronCollection) -> List[Dict]:
        """Analyze which ROIs commonly co-occur in neurons."""
        # Simplified implementation - in practice would use more sophisticated analysis
        roi_pairs = {}

        for neuron in collection.neurons:
            rois = list(neuron.roi_counts.keys())
            for i in range(len(rois)):
                for j in range(i + 1, len(rois)):
                    pair = tuple(sorted([rois[i], rois[j]]))
                    roi_pairs[pair] = roi_pairs.get(pair, 0) + 1

        patterns = []
        total_neurons = len(collection.neurons)

        for (roi1, roi2), count in roi_pairs.items():
            if count >= 3:  # Minimum threshold
                strength = count / total_neurons
                confidence = min(1.0, count / 5)  # Simple confidence measure

                participating_neurons = []
                for neuron in collection.neurons:
                    if roi1 in neuron.roi_counts and roi2 in neuron.roi_counts:
                        participating_neurons.append(neuron.body_id)

                patterns.append({
                    'rois': [roi1, roi2],
                    'strength': strength,
                    'confidence': confidence,
                    'neurons': participating_neurons
                })

        return patterns

    def _analyze_synapse_ratio_patterns(self, collection: NeuronCollection) -> List[Dict]:
        """Analyze patterns in pre/post synapse ratios."""
        ratios = []
        neurons_by_ratio = {}

        for neuron in collection.neurons:
            if neuron.synapse_stats.post_synapses.value > 0:
                ratio = neuron.synapse_stats.pre_synapses.value / neuron.synapse_stats.post_synapses.value
                ratios.append(ratio)

                # Categorize ratios
                if ratio < 0.5:
                    category = "post_dominant"
                elif ratio > 2.0:
                    category = "pre_dominant"
                else:
                    category = "balanced"

                if category not in neurons_by_ratio:
                    neurons_by_ratio[category] = []
                neurons_by_ratio[category].append(neuron.body_id)

        patterns = []
        total_neurons = len(collection.neurons)

        for category, neurons in neurons_by_ratio.items():
            if len(neurons) >= 3:  # Minimum pattern size
                strength = len(neurons) / total_neurons
                confidence = min(1.0, len(neurons) / 5)

                patterns.append({
                    'pattern_type': category,
                    'strength': strength,
                    'confidence': confidence,
                    'neurons': neurons
                })

        return patterns
