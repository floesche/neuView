"""
Domain Events System for QuickPage

This module provides a robust domain events system that enables decoupled
communication between different parts of the domain and across bounded contexts.
Domain events represent something interesting that happened in the domain.

Key Concepts:
- Domain Events: Immutable objects representing domain occurrences
- Event Publisher: Publishes events to registered handlers
- Event Handlers: Process events asynchronously
- Event Store: Optional persistence for events (event sourcing)

Benefits:
- Loose coupling between domain components
- Side effects are handled separately from core business logic
- Enables event sourcing and audit trails
- Supports integration between bounded contexts
- Makes the system more testable and maintainable
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Awaitable, Type, Union
from datetime import datetime
from uuid import uuid4, UUID
import asyncio
import logging
from enum import Enum

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DomainEvent(ABC):
    """
    Base class for all domain events.

    Domain events are immutable objects that represent something
    interesting that happened in the domain. They should contain
    all the information needed to understand what occurred.
    """
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=datetime.now)
    event_version: int = field(default=1)
    correlation_id: Optional[UUID] = field(default=None)
    causation_id: Optional[UUID] = field(default=None)

    @property
    @abstractmethod
    def event_type(self) -> str:
        """Return the event type identifier."""
        pass

    @property
    def aggregate_id(self) -> Optional[str]:
        """Return the ID of the aggregate that generated this event."""
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        result = {
            'event_id': str(self.event_id),
            'event_type': self.event_type,
            'occurred_at': self.occurred_at.isoformat(),
            'event_version': self.event_version,
            'correlation_id': str(self.correlation_id) if self.correlation_id else None,
            'causation_id': str(self.causation_id) if self.causation_id else None,
            'aggregate_id': self.aggregate_id,
        }

        # Add event-specific data
        for key, value in self.__dict__.items():
            if key not in result and not key.startswith('_'):
                if hasattr(value, 'to_dict'):
                    result[key] = value.to_dict()
                elif isinstance(value, (str, int, float, bool, type(None))):
                    result[key] = value
                elif isinstance(value, (datetime,)):
                    result[key] = value.isoformat()
                elif isinstance(value, (UUID,)):
                    result[key] = str(value)
                else:
                    result[key] = str(value)

        return result


class EventPriority(Enum):
    """Event processing priorities."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


EventHandler = Callable[[DomainEvent], Awaitable[None]]


@dataclass
class EventSubscription:
    """Represents a subscription to domain events."""
    handler: EventHandler
    event_types: List[Type[DomainEvent]]
    priority: EventPriority = EventPriority.NORMAL
    retry_count: int = 3
    timeout: float = 30.0
    subscription_id: UUID = field(default_factory=uuid4)

    def matches_event(self, event: DomainEvent) -> bool:
        """Check if this subscription should handle the given event."""
        return any(isinstance(event, event_type) for event_type in self.event_types)


@dataclass
class EventProcessingResult:
    """Result of event processing."""
    success: bool
    error: Optional[Exception] = None
    processing_time: Optional[float] = None
    retry_count: int = 0


class EventPublisher:
    """
    Domain event publisher that manages event subscriptions and publishing.

    This is the central component of the domain events system that:
    - Manages event subscriptions
    - Publishes events to appropriate handlers
    - Handles retries and error recovery
    - Provides metrics and monitoring capabilities
    """

    def __init__(self):
        self._subscriptions: List[EventSubscription] = []
        self._processing_stats: Dict[str, Any] = {
            'total_published': 0,
            'total_processed': 0,
            'total_failed': 0,
            'average_processing_time': 0.0
        }
        self._event_store: Optional['EventStore'] = None

    def subscribe(
        self,
        handler: EventHandler,
        event_types: Union[Type[DomainEvent], List[Type[DomainEvent]]],
        priority: EventPriority = EventPriority.NORMAL,
        retry_count: int = 3,
        timeout: float = 30.0
    ) -> UUID:
        """
        Subscribe a handler to one or more event types.

        Args:
            handler: Async function to handle events
            event_types: Event type(s) to subscribe to
            priority: Processing priority
            retry_count: Number of retries on failure
            timeout: Handler timeout in seconds

        Returns:
            Subscription ID for later unsubscribing
        """
        if not isinstance(event_types, list):
            event_types = [event_types]

        subscription = EventSubscription(
            handler=handler,
            event_types=event_types,
            priority=priority,
            retry_count=retry_count,
            timeout=timeout
        )

        self._subscriptions.append(subscription)

        logger.info(
            f"Subscribed handler to events: {[et.__name__ for et in event_types]}"
        )

        return subscription.subscription_id

    def unsubscribe(self, subscription_id: UUID) -> bool:
        """
        Unsubscribe a handler using its subscription ID.

        Args:
            subscription_id: The subscription ID returned by subscribe()

        Returns:
            True if subscription was found and removed
        """
        for i, subscription in enumerate(self._subscriptions):
            if subscription.subscription_id == subscription_id:
                self._subscriptions.pop(i)
                logger.info(f"Unsubscribed handler {subscription_id}")
                return True

        return False

    async def publish(self, event: DomainEvent) -> List[EventProcessingResult]:
        """
        Publish a domain event to all matching subscribers.

        Args:
            event: The domain event to publish

        Returns:
            List of processing results for each handler
        """
        logger.debug(f"Publishing event: {event.event_type} ({event.event_id})")

        # Store event if event store is configured
        if self._event_store:
            await self._event_store.store_event(event)

        # Find matching subscriptions
        matching_subscriptions = [
            sub for sub in self._subscriptions if sub.matches_event(event)
        ]

        # Sort by priority (highest first)
        matching_subscriptions.sort(key=lambda x: x.priority.value, reverse=True)

        # Process events
        results = []
        for subscription in matching_subscriptions:
            result = await self._process_event(event, subscription)
            results.append(result)

        # Update stats
        self._update_stats(event, results)

        logger.debug(
            f"Published event {event.event_type} to {len(matching_subscriptions)} handlers"
        )

        return results

    async def publish_many(self, events: List[DomainEvent]) -> Dict[UUID, List[EventProcessingResult]]:
        """
        Publish multiple events.

        Args:
            events: List of events to publish

        Returns:
            Dictionary mapping event IDs to their processing results
        """
        results = {}
        for event in events:
            results[event.event_id] = await self.publish(event)
        return results

    def set_event_store(self, event_store: 'EventStore') -> None:
        """Set an event store for persisting events."""
        self._event_store = event_store

    def get_stats(self) -> Dict[str, Any]:
        """Get event processing statistics."""
        return self._processing_stats.copy()

    def clear_subscriptions(self) -> None:
        """Clear all subscriptions (useful for testing)."""
        self._subscriptions.clear()

    async def _process_event(
        self,
        event: DomainEvent,
        subscription: EventSubscription
    ) -> EventProcessingResult:
        """Process a single event with a subscription handler."""
        start_time = asyncio.get_event_loop().time()

        for attempt in range(subscription.retry_count + 1):
            try:
                # Execute handler with timeout
                await asyncio.wait_for(
                    subscription.handler(event),
                    timeout=subscription.timeout
                )

                processing_time = asyncio.get_event_loop().time() - start_time

                return EventProcessingResult(
                    success=True,
                    processing_time=processing_time,
                    retry_count=attempt
                )

            except asyncio.TimeoutError as e:
                logger.warning(
                    f"Handler timeout for event {event.event_type} "
                    f"(attempt {attempt + 1}/{subscription.retry_count + 1})"
                )
                if attempt == subscription.retry_count:
                    return EventProcessingResult(
                        success=False,
                        error=e,
                        retry_count=attempt
                    )

            except Exception as e:
                logger.error(
                    f"Handler error for event {event.event_type}: {e} "
                    f"(attempt {attempt + 1}/{subscription.retry_count + 1})",
                    exc_info=True
                )
                if attempt == subscription.retry_count:
                    return EventProcessingResult(
                        success=False,
                        error=e,
                        retry_count=attempt
                    )

                # Wait before retry
                await asyncio.sleep(0.1 * (attempt + 1))

        # This should never be reached, but just in case
        return EventProcessingResult(
            success=False,
            error=Exception("Unexpected error in event processing")
        )

    def _update_stats(self, event: DomainEvent, results: List[EventProcessingResult]) -> None:
        """Update processing statistics."""
        self._processing_stats['total_published'] += 1

        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]

        self._processing_stats['total_processed'] += len(successful_results)
        self._processing_stats['total_failed'] += len(failed_results)

        # Update average processing time
        if successful_results:
            processing_times = [r.processing_time for r in successful_results if r.processing_time]
            if processing_times:
                current_avg = self._processing_stats['average_processing_time']
                new_avg = sum(processing_times) / len(processing_times)
                self._processing_stats['average_processing_time'] = (current_avg + new_avg) / 2


class EventStore(ABC):
    """Abstract base class for event stores."""

    @abstractmethod
    async def store_event(self, event: DomainEvent) -> None:
        """Store a domain event."""
        pass

    @abstractmethod
    async def get_events(
        self,
        aggregate_id: Optional[str] = None,
        event_type: Optional[str] = None,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None
    ) -> List[DomainEvent]:
        """Retrieve stored events based on criteria."""
        pass


class InMemoryEventStore(EventStore):
    """Simple in-memory event store for testing and development."""

    def __init__(self):
        self._events: List[DomainEvent] = []

    async def store_event(self, event: DomainEvent) -> None:
        """Store event in memory."""
        self._events.append(event)

    async def get_events(
        self,
        aggregate_id: Optional[str] = None,
        event_type: Optional[str] = None,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None
    ) -> List[DomainEvent]:
        """Retrieve events from memory based on criteria."""
        filtered_events = self._events

        if aggregate_id:
            filtered_events = [e for e in filtered_events if e.aggregate_id == aggregate_id]

        if event_type:
            filtered_events = [e for e in filtered_events if e.event_type == event_type]

        if from_timestamp:
            filtered_events = [e for e in filtered_events if e.occurred_at >= from_timestamp]

        if to_timestamp:
            filtered_events = [e for e in filtered_events if e.occurred_at <= to_timestamp]

        return filtered_events

    def clear(self) -> None:
        """Clear all stored events."""
        self._events.clear()


# Global event publisher instance
_global_publisher: Optional[EventPublisher] = None


def get_event_publisher() -> EventPublisher:
    """Get the global event publisher instance."""
    global _global_publisher
    if _global_publisher is None:
        _global_publisher = EventPublisher()
    return _global_publisher


def set_event_publisher(publisher: EventPublisher) -> None:
    """Set the global event publisher instance."""
    global _global_publisher
    _global_publisher = publisher


async def publish_event(event: DomainEvent) -> List[EventProcessingResult]:
    """Convenience function to publish an event using the global publisher."""
    return await get_event_publisher().publish(event)


def subscribe_to_events(
    handler: EventHandler,
    event_types: Union[Type[DomainEvent], List[Type[DomainEvent]]],
    priority: EventPriority = EventPriority.NORMAL,
    retry_count: int = 3,
    timeout: float = 30.0
) -> UUID:
    """Convenience function to subscribe to events using the global publisher."""
    return get_event_publisher().subscribe(
        handler=handler,
        event_types=event_types,
        priority=priority,
        retry_count=retry_count,
        timeout=timeout
    )


__all__ = [
    'DomainEvent',
    'EventPriority',
    'EventHandler',
    'EventSubscription',
    'EventProcessingResult',
    'EventPublisher',
    'EventStore',
    'InMemoryEventStore',
    'get_event_publisher',
    'set_event_publisher',
    'publish_event',
    'subscribe_to_events',
]
