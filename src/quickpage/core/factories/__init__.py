"""
Domain Factories for QuickPage Core Domain

Domain factories are responsible for creating complex domain objects and aggregates.
They encapsulate the construction logic and ensure that domain invariants are
maintained during object creation. Factories are particularly useful for:

- Complex entity creation with validation
- Aggregate reconstruction from persistence
- Creating entities with computed values
- Handling circular dependencies during creation
- Ensuring consistency across related objects

Key Principles:
- Encapsulate complex construction logic
- Maintain domain invariants during creation
- Provide different creation strategies
- Handle validation and error cases
- Support aggregate reconstruction
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from uuid import UUID, uuid4

from ..entities import Neuron, NeuronCollection
from ..value_objects import (
    BodyId, NeuronTypeName, SomaSide, SynapseStatistics,
    SynapseCount, RoiName
)
from ...shared.result import Result, Ok, Err


class DomainFactory(ABC):
    """Base class for all domain factories."""

    def validate_creation_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate data before entity creation. Return list of validation errors."""
        return []


class NeuronFactory(DomainFactory):
    """
    Factory for creating Neuron entities with proper validation and invariants.

    This factory handles the complex logic of creating neurons from various
    data sources (database, external APIs, user input) while ensuring all
    domain rules are followed.
    """

    def create_from_neuprint_data(
        self,
        neuprint_data: Dict[str, Any]
    ) -> Result[Neuron, str]:
        """
        Create a neuron from NeuPrint database data.

        Args:
            neuprint_data: Raw data from NeuPrint query

        Returns:
            Result containing the created neuron or error message
        """
        try:
            # Validate required fields
            validation_errors = self._validate_neuprint_data(neuprint_data)
            if validation_errors:
                return Err(f"Invalid NeuPrint data: {', '.join(validation_errors)}")

            # Extract and convert basic fields
            body_id = BodyId(neuprint_data['bodyId'])
            neuron_type = NeuronTypeName(neuprint_data.get('type', 'Unknown'))
            soma_side = SomaSide(neuprint_data.get('somaLocation', 'unknown'))

            # Create synapse statistics
            pre_count = neuprint_data.get('pre', 0)
            post_count = neuprint_data.get('post', 0)

            synapse_stats = SynapseStatistics(
                pre_synapses=SynapseCount(pre_count),
                post_synapses=SynapseCount(post_count),
                total=SynapseCount(pre_count + post_count)
            )

            # Process ROI data
            roi_counts = {}
            roi_data = neuprint_data.get('roiInfo', {})

            for roi_name, roi_info in roi_data.items():
                if isinstance(roi_info, dict):
                    # NeuPrint format: {'pre': x, 'post': y}
                    total_roi_synapses = roi_info.get('pre', 0) + roi_info.get('post', 0)
                else:
                    # Simple format: roi_name -> count
                    total_roi_synapses = roi_info

                if total_roi_synapses > 0:
                    roi_counts[RoiName(roi_name)] = SynapseCount(total_roi_synapses)

            # Create the neuron
            neuron = Neuron(
                body_id=body_id,
                neuron_type=neuron_type,
                soma_side=soma_side,
                synapse_stats=synapse_stats,
                roi_counts=roi_counts
            )

            # Additional validation after creation
            if not neuron.is_valid():
                return Err(f"Created neuron failed validation: {body_id}")

            return Ok(neuron)

        except Exception as e:
            return Err(f"Failed to create neuron from NeuPrint data: {str(e)}")

    def create_from_user_input(
        self,
        body_id: int,
        neuron_type: str,
        soma_side: str,
        pre_synapses: int,
        post_synapses: int,
        roi_data: Optional[Dict[str, int]] = None
    ) -> Result[Neuron, str]:
        """
        Create a neuron from user input with validation.

        Args:
            body_id: Neuron body ID
            neuron_type: Type name
            soma_side: Soma side location
            pre_synapses: Pre-synapse count
            post_synapses: Post-synapse count
            roi_data: Optional ROI synapse counts

        Returns:
            Result containing the created neuron or error message
        """
        try:
            # Validate input parameters
            if body_id <= 0:
                return Err("Body ID must be positive")

            if pre_synapses < 0 or post_synapses < 0:
                return Err("Synapse counts cannot be negative")

            if not neuron_type or not neuron_type.strip():
                return Err("Neuron type cannot be empty")

            # Create value objects
            body_id_vo = BodyId(body_id)
            neuron_type_vo = NeuronTypeName(neuron_type.strip())
            soma_side_vo = SomaSide(soma_side)

            synapse_stats = SynapseStatistics(
                pre_synapses=SynapseCount(pre_synapses),
                post_synapses=SynapseCount(post_synapses),
                total=SynapseCount(pre_synapses + post_synapses)
            )

            # Process ROI data
            roi_counts = {}
            if roi_data:
                for roi_name, count in roi_data.items():
                    if count > 0:
                        roi_counts[RoiName(roi_name)] = SynapseCount(count)

            neuron = Neuron(
                body_id=body_id_vo,
                neuron_type=neuron_type_vo,
                soma_side=soma_side_vo,
                synapse_stats=synapse_stats,
                roi_counts=roi_counts
            )

            return Ok(neuron)

        except Exception as e:
            return Err(f"Failed to create neuron from user input: {str(e)}")

    def create_test_neuron(
        self,
        body_id: Optional[int] = None,
        neuron_type: Optional[str] = None,
        **kwargs
    ) -> Neuron:
        """
        Create a test neuron with reasonable defaults.

        Args:
            body_id: Optional specific body ID
            neuron_type: Optional specific type
            **kwargs: Additional overrides

        Returns:
            A valid test neuron
        """
        import random

        body_id = body_id or random.randint(100000, 999999)
        neuron_type = neuron_type or "TestNeuron"

        defaults = {
            'soma_side': 'left',
            'pre_synapses': random.randint(50, 500),
            'post_synapses': random.randint(50, 500),
            'roi_data': {
                'TestROI1': random.randint(10, 100),
                'TestROI2': random.randint(10, 100)
            }
        }

        defaults.update(kwargs)

        result = self.create_from_user_input(
            body_id=body_id,
            neuron_type=neuron_type,
            **defaults
        )

        if result.is_err():
            raise ValueError(f"Failed to create test neuron: {result.error}")

        return result.value

    def _validate_neuprint_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate NeuPrint data structure."""
        errors = []

        if 'bodyId' not in data:
            errors.append("Missing required field: bodyId")
        elif not isinstance(data['bodyId'], int) or data['bodyId'] <= 0:
            errors.append("bodyId must be a positive integer")

        # Type is optional but if present should be non-empty
        if 'type' in data and not data['type']:
            errors.append("type cannot be empty if provided")

        # Validate synapse counts
        for field in ['pre', 'post']:
            if field in data:
                if not isinstance(data[field], int) or data[field] < 0:
                    errors.append(f"{field} must be a non-negative integer")

        return errors


class NeuronCollectionFactory(DomainFactory):
    """
    Factory for creating NeuronCollection aggregates.

    This factory handles the creation of neuron collections from various
    sources and ensures that all collection invariants are maintained.
    """

    def __init__(self, neuron_factory: Optional[NeuronFactory] = None):
        self.neuron_factory = neuron_factory or NeuronFactory()

    def create_from_neuprint_results(
        self,
        neuron_type: str,
        neuprint_results: List[Dict[str, Any]],
        fetched_from: Optional[str] = None
    ) -> Result[NeuronCollection, str]:
        """
        Create a neuron collection from NeuPrint query results.

        Args:
            neuron_type: The neuron type name
            neuprint_results: List of neuron data from NeuPrint
            fetched_from: Optional source identifier

        Returns:
            Result containing the created collection or error message
        """
        try:
            type_name = NeuronTypeName(neuron_type)
            collection = NeuronCollection(
                type_name=type_name,
                fetched_from=fetched_from or "NeuPrint"
            )

            created_neurons = []
            failed_neurons = []

            for neuron_data in neuprint_results:
                neuron_result = self.neuron_factory.create_from_neuprint_data(neuron_data)

                if neuron_result.is_ok():
                    neuron = neuron_result.value

                    # Validate that neuron type matches collection
                    if neuron.neuron_type != type_name:
                        failed_neurons.append(
                            f"Neuron {neuron.body_id} type mismatch: "
                            f"expected {type_name}, got {neuron.neuron_type}"
                        )
                        continue

                    collection.add_neuron(neuron)
                    created_neurons.append(neuron)

                else:
                    failed_neurons.append(neuron_result.error)

            if not created_neurons:
                return Err(
                    f"No valid neurons created for type {neuron_type}. "
                    f"Errors: {'; '.join(failed_neurons)}"
                )

            if failed_neurons:
                # Log warnings about failed neurons but still return success
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Some neurons failed to create for type {neuron_type}: "
                    f"{'; '.join(failed_neurons[:5])}"  # Log first 5 errors
                )

            return Ok(collection)

        except Exception as e:
            return Err(f"Failed to create collection from NeuPrint results: {str(e)}")

    def create_from_neurons(
        self,
        neurons: List[Neuron],
        collection_type: Optional[str] = None
    ) -> Result[NeuronCollection, str]:
        """
        Create a collection from existing neuron entities.

        Args:
            neurons: List of neuron entities
            collection_type: Optional override for collection type

        Returns:
            Result containing the created collection or error message
        """
        try:
            if not neurons:
                return Err("Cannot create collection from empty neuron list")

            # Determine collection type
            if collection_type:
                type_name = NeuronTypeName(collection_type)
            else:
                # Use the type from the first neuron
                type_name = neurons[0].neuron_type

            collection = NeuronCollection(type_name=type_name)

            type_mismatches = []
            for neuron in neurons:
                if neuron.neuron_type != type_name:
                    type_mismatches.append(str(neuron.body_id))
                    continue

                collection.add_neuron(neuron)

            if type_mismatches:
                return Err(
                    f"Type mismatch for neurons: {', '.join(type_mismatches)}. "
                    f"Expected type: {type_name}"
                )

            if collection.is_empty():
                return Err("No valid neurons added to collection")

            return Ok(collection)

        except Exception as e:
            return Err(f"Failed to create collection from neurons: {str(e)}")

    def create_test_collection(
        self,
        neuron_type: str = "TestNeuron",
        neuron_count: int = 10,
        include_bilateral: bool = True,
        **kwargs
    ) -> NeuronCollection:
        """
        Create a test neuron collection with specified characteristics.

        Args:
            neuron_type: Type name for all neurons
            neuron_count: Number of neurons to create
            include_bilateral: Whether to include both left and right neurons
            **kwargs: Additional parameters for neuron creation

        Returns:
            A test neuron collection
        """
        import random

        type_name = NeuronTypeName(neuron_type)
        collection = NeuronCollection(type_name=type_name, fetched_from="TestFactory")

        sides = ['left', 'right'] if include_bilateral else ['left']

        for i in range(neuron_count):
            # Distribute neurons across sides
            side = sides[i % len(sides)] if include_bilateral else 'left'

            neuron_kwargs = {
                'soma_side': side,
                **kwargs
            }

            neuron = self.neuron_factory.create_test_neuron(
                body_id=100000 + i,
                neuron_type=neuron_type,
                **neuron_kwargs
            )

            collection.add_neuron(neuron)

        return collection

    def merge_collections(
        self,
        collections: List[NeuronCollection]
    ) -> Result[NeuronCollection, str]:
        """
        Merge multiple collections of the same type.

        Args:
            collections: List of collections to merge

        Returns:
            Result containing the merged collection or error message
        """
        try:
            if not collections:
                return Err("Cannot merge empty collection list")

            # Validate all collections have the same type
            first_type = collections[0].type_name
            for collection in collections[1:]:
                if collection.type_name != first_type:
                    return Err(
                        f"Cannot merge collections of different types: "
                        f"{first_type} vs {collection.type_name}"
                    )

            # Create merged collection
            merged = NeuronCollection(
                type_name=first_type,
                fetched_from=f"Merged from {len(collections)} collections"
            )

            # Add all neurons, handling duplicates
            duplicate_count = 0
            for collection in collections:
                for neuron in collection.neurons:
                    if neuron not in merged.neurons:
                        merged.add_neuron(neuron)
                    else:
                        duplicate_count += 1

            if duplicate_count > 0:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Merged collections, {duplicate_count} duplicates removed")

            return Ok(merged)

        except Exception as e:
            return Err(f"Failed to merge collections: {str(e)}")


class AggregateFactory(DomainFactory):
    """
    Factory for reconstructing aggregates from persistence.

    This factory is responsible for recreating domain aggregates from
    stored data, ensuring all invariants are maintained and domain
    events are properly handled.
    """

    def __init__(
        self,
        neuron_factory: Optional[NeuronFactory] = None,
        collection_factory: Optional[NeuronCollectionFactory] = None
    ):
        self.neuron_factory = neuron_factory or NeuronFactory()
        self.collection_factory = collection_factory or NeuronCollectionFactory(self.neuron_factory)

    def reconstruct_collection_from_snapshot(
        self,
        snapshot_data: Dict[str, Any]
    ) -> Result[NeuronCollection, str]:
        """
        Reconstruct a neuron collection from a persistence snapshot.

        Args:
            snapshot_data: Serialized collection data

        Returns:
            Result containing the reconstructed collection or error message
        """
        try:
            # Validate snapshot structure
            required_fields = ['type_name', 'neurons', 'created_at']
            missing_fields = [f for f in required_fields if f not in snapshot_data]
            if missing_fields:
                return Err(f"Missing required fields in snapshot: {', '.join(missing_fields)}")

            # Reconstruct collection metadata
            type_name = NeuronTypeName(snapshot_data['type_name'])
            created_at = datetime.fromisoformat(snapshot_data['created_at'])
            fetched_from = snapshot_data.get('fetched_from')

            collection = NeuronCollection(
                type_name=type_name,
                created_at=created_at,
                fetched_from=fetched_from
            )

            # Reconstruct neurons
            for neuron_data in snapshot_data['neurons']:
                neuron_result = self._reconstruct_neuron_from_data(neuron_data)
                if neuron_result.is_ok():
                    collection.add_neuron(neuron_result.value)
                else:
                    return Err(f"Failed to reconstruct neuron: {neuron_result.error}")

            return Ok(collection)

        except Exception as e:
            return Err(f"Failed to reconstruct collection from snapshot: {str(e)}")

    def _reconstruct_neuron_from_data(self, neuron_data: Dict[str, Any]) -> Result[Neuron, str]:
        """Reconstruct a neuron from serialized data."""
        try:
            # Extract basic fields
            body_id = BodyId(neuron_data['body_id'])
            neuron_type = NeuronTypeName(neuron_data['neuron_type'])
            soma_side = SomaSide(neuron_data['soma_side'])

            # Reconstruct synapse statistics
            stats_data = neuron_data['synapse_stats']
            synapse_stats = SynapseStatistics(
                pre_synapses=SynapseCount(stats_data['pre_synapses']),
                post_synapses=SynapseCount(stats_data['post_synapses']),
                total=SynapseCount(stats_data['total'])
            )

            # Reconstruct ROI counts
            roi_counts = {}
            for roi_name, count in neuron_data.get('roi_counts', {}).items():
                roi_counts[RoiName(roi_name)] = SynapseCount(count)

            neuron = Neuron(
                body_id=body_id,
                neuron_type=neuron_type,
                soma_side=soma_side,
                synapse_stats=synapse_stats,
                roi_counts=roi_counts
            )

            return Ok(neuron)

        except Exception as e:
            return Err(f"Failed to reconstruct neuron: {str(e)}")


# Export all factories
__all__ = [
    'DomainFactory',
    'NeuronFactory',
    'NeuronCollectionFactory',
    'AggregateFactory'
]
