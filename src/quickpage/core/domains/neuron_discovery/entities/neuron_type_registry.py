"""
NeuronTypeRegistry aggregate root for the neuron discovery domain.

This module contains the NeuronTypeRegistry aggregate which is responsible for
maintaining the consistency and business rules around neuron type discovery,
registration, and validation within the connectome dataset.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime
from uuid import UUID, uuid4

from ..value_objects import (
    NeuronTypeId, NeuronTypeClassification, DiscoveryTimestamp, TypeAvailability
)
from ..events import (
    NeuronTypeDiscovered, NeuronTypeRegistryUpdated, NeuronTypeValidated, NeuronTypeInvalidated
)
from ....shared.domain_events import DomainEvent


@dataclass
class NeuronTypeMetadata:
    """Value object containing metadata about a neuron type."""
    classification: NeuronTypeClassification
    discovery_timestamp: DiscoveryTimestamp
    availability: TypeAvailability
    total_instances: int
    bilateral_instances: int
    unilateral_instances: int
    data_quality_score: float
    last_validated: datetime
    tags: Set[str] = field(default_factory=set)
    description: Optional[str] = None

    def is_high_quality(self) -> bool:
        """Check if neuron type has high data quality."""
        return self.data_quality_score >= 0.8 and self.total_instances >= 10

    def is_bilateral(self) -> bool:
        """Check if neuron type has bilateral representation."""
        return self.bilateral_instances > 0

    def needs_validation(self) -> bool:
        """Check if neuron type needs revalidation."""
        days_since_validation = (datetime.now() - self.last_validated).days
        return days_since_validation > 30


@dataclass
class NeuronTypeEntry:
    """Entity representing a single neuron type entry in the registry."""
    type_id: NeuronTypeId
    metadata: NeuronTypeMetadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1

    def update_metadata(self, new_metadata: NeuronTypeMetadata) -> None:
        """Update metadata and increment version."""
        self.metadata = new_metadata
        self.updated_at = datetime.now()
        self.version += 1

    def add_tag(self, tag: str) -> None:
        """Add a tag to the neuron type."""
        self.metadata.tags.add(tag)
        self.updated_at = datetime.now()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the neuron type."""
        self.metadata.tags.discard(tag)
        self.updated_at = datetime.now()

    def mark_validated(self) -> None:
        """Mark the neuron type as recently validated."""
        self.metadata.last_validated = datetime.now()
        self.updated_at = datetime.now()

    def is_stale(self) -> bool:
        """Check if the entry is stale and needs updating."""
        days_since_update = (datetime.now() - self.updated_at).days
        return days_since_update > 7


@dataclass
class NeuronTypeRegistry:
    """
    Aggregate root for managing neuron type discovery and registration.

    This aggregate is responsible for maintaining consistency rules around
    neuron type discovery, validation, and metadata management. It ensures
    that the registry remains consistent and business rules are enforced.
    """
    registry_id: UUID = field(default_factory=uuid4)
    entries: Dict[NeuronTypeId, NeuronTypeEntry] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    discovery_session_id: Optional[str] = None
    version: int = 1

    # Domain events (cleared after being processed)
    _domain_events: List[DomainEvent] = field(default_factory=list, init=False)

    def register_neuron_type(
        self,
        type_id: NeuronTypeId,
        metadata: NeuronTypeMetadata
    ) -> None:
        """
        Register a new neuron type in the registry.

        Business Rules:
        - Type ID must be unique within the registry
        - Metadata must be valid and complete
        - Classification must be appropriate for the type
        """
        if type_id in self.entries:
            # Update existing entry
            self.entries[type_id].update_metadata(metadata)
            self._add_domain_event(
                NeuronTypeRegistryUpdated(
                    registry_id=self.registry_id,
                    type_id=type_id,
                    updated_at=datetime.now()
                )
            )
        else:
            # Create new entry
            entry = NeuronTypeEntry(type_id=type_id, metadata=metadata)
            self.entries[type_id] = entry

            self._add_domain_event(
                NeuronTypeDiscovered(
                    registry_id=self.registry_id,
                    type_id=type_id,
                    classification=metadata.classification,
                    discovered_at=metadata.discovery_timestamp.value
                )
            )

        self._update_registry_timestamp()

    def validate_neuron_type(self, type_id: NeuronTypeId) -> bool:
        """
        Validate a neuron type entry.

        Returns True if validation successful, False otherwise.
        Raises ValueError if type doesn't exist.
        """
        if type_id not in self.entries:
            raise ValueError(f"Neuron type {type_id} not found in registry")

        entry = self.entries[type_id]

        # Perform validation logic
        is_valid = self._perform_validation_checks(entry)

        if is_valid:
            entry.mark_validated()
            self._add_domain_event(
                NeuronTypeValidated(
                    registry_id=self.registry_id,
                    type_id=type_id,
                    validated_at=datetime.now()
                )
            )
        else:
            self._add_domain_event(
                NeuronTypeInvalidated(
                    registry_id=self.registry_id,
                    type_id=type_id,
                    invalidated_at=datetime.now(),
                    reason="Failed validation checks"
                )
            )

        self._update_registry_timestamp()
        return is_valid

    def get_neuron_type(self, type_id: NeuronTypeId) -> Optional[NeuronTypeEntry]:
        """Get a neuron type entry by ID."""
        return self.entries.get(type_id)

    def get_all_types(self) -> List[NeuronTypeEntry]:
        """Get all neuron type entries."""
        return list(self.entries.values())

    def get_types_by_classification(
        self,
        classification: NeuronTypeClassification
    ) -> List[NeuronTypeEntry]:
        """Get neuron types by their classification."""
        return [
            entry for entry in self.entries.values()
            if entry.metadata.classification == classification
        ]

    def get_high_quality_types(self) -> List[NeuronTypeEntry]:
        """Get neuron types with high data quality."""
        return [
            entry for entry in self.entries.values()
            if entry.metadata.is_high_quality()
        ]

    def get_bilateral_types(self) -> List[NeuronTypeEntry]:
        """Get neuron types with bilateral representation."""
        return [
            entry for entry in self.entries.values()
            if entry.metadata.is_bilateral()
        ]

    def get_types_needing_validation(self) -> List[NeuronTypeEntry]:
        """Get neuron types that need revalidation."""
        return [
            entry for entry in self.entries.values()
            if entry.metadata.needs_validation()
        ]

    def get_stale_entries(self) -> List[NeuronTypeEntry]:
        """Get entries that haven't been updated recently."""
        return [
            entry for entry in self.entries.values()
            if entry.is_stale()
        ]

    def remove_neuron_type(self, type_id: NeuronTypeId) -> bool:
        """
        Remove a neuron type from the registry.

        Business Rule: Only allow removal of invalid or obsolete types.
        """
        if type_id not in self.entries:
            return False

        entry = self.entries[type_id]

        # Business rule: Don't allow removal of high-quality, recently validated types
        if entry.metadata.is_high_quality() and not entry.metadata.needs_validation():
            raise ValueError(
                f"Cannot remove high-quality, recently validated type {type_id}"
            )

        del self.entries[type_id]
        self._update_registry_timestamp()

        return True

    def get_statistics(self) -> dict:
        """Get registry statistics."""
        total_types = len(self.entries)
        high_quality_types = len(self.get_high_quality_types())
        bilateral_types = len(self.get_bilateral_types())
        need_validation = len(self.get_types_needing_validation())

        return {
            'total_types': total_types,
            'high_quality_types': high_quality_types,
            'bilateral_types': bilateral_types,
            'types_needing_validation': need_validation,
            'quality_ratio': high_quality_types / total_types if total_types > 0 else 0,
            'bilateral_ratio': bilateral_types / total_types if total_types > 0 else 0,
            'last_updated': self.last_updated
        }

    def clear_domain_events(self) -> List[DomainEvent]:
        """Get and clear all domain events."""
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events

    def _perform_validation_checks(self, entry: NeuronTypeEntry) -> bool:
        """Perform validation checks on a neuron type entry."""
        # Validation logic
        if entry.metadata.total_instances <= 0:
            return False

        if entry.metadata.data_quality_score < 0.1:
            return False

        if not entry.metadata.availability.is_available():
            return False

        return True

    def _update_registry_timestamp(self) -> None:
        """Update the registry's last updated timestamp and version."""
        self.last_updated = datetime.now()
        self.version += 1

    def _add_domain_event(self, event: DomainEvent) -> None:
        """Add a domain event to be published."""
        self._domain_events.append(event)

    def __len__(self) -> int:
        """Return the number of registered neuron types."""
        return len(self.entries)

    def __contains__(self, type_id: NeuronTypeId) -> bool:
        """Check if a neuron type is registered."""
        return type_id in self.entries

    def __str__(self) -> str:
        return f"NeuronTypeRegistry({len(self.entries)} types, v{self.version})"
