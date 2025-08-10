"""
Dependency injection container for QuickPage.

This module provides a simple dependency injection container for managing
service registration and resolution, enabling loose coupling between
components and better testability.
"""

from typing import TypeVar, Type, Dict, Any, Callable, Optional, get_type_hints
from dataclasses import dataclass
import inspect
import logging

T = TypeVar('T')
logger = logging.getLogger(__name__)


@dataclass
class ServiceInfo:
    """Information about a registered service."""
    interface: Type
    implementation: Any
    singleton: bool
    instance: Optional[Any] = None


class Container:
    """
    Simple dependency injection container.

    Supports:
    - Service registration by type
    - Factory function registration
    - Singleton and transient lifetimes
    - Constructor injection
    - Circular dependency detection
    """

    def __init__(self):
        self._services: Dict[Type, ServiceInfo] = {}
        self._factories: Dict[Type, Callable] = {}
        self._resolution_stack: set = set()

    def register_singleton(self, interface: Type[T], implementation: T) -> 'Container':
        """
        Register a singleton service.

        Args:
            interface: The interface type
            implementation: The implementation instance or class

        Returns:
            Self for method chaining
        """
        self._services[interface] = ServiceInfo(
            interface=interface,
            implementation=implementation,
            singleton=True
        )
        logger.debug(f"Registered singleton {interface.__name__}")
        return self

    def register_transient(self, interface: Type[T], implementation: Type[T]) -> 'Container':
        """
        Register a transient service (new instance each time).

        Args:
            interface: The interface type
            implementation: The implementation class

        Returns:
            Self for method chaining
        """
        self._services[interface] = ServiceInfo(
            interface=interface,
            implementation=implementation,
            singleton=False
        )
        logger.debug(f"Registered transient {interface.__name__}")
        return self

    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> 'Container':
        """
        Register a factory function for creating instances.

        Args:
            interface: The interface type
            factory: Factory function that creates instances

        Returns:
            Self for method chaining
        """
        self._factories[interface] = factory
        logger.debug(f"Registered factory for {interface.__name__}")
        return self

    def resolve(self, interface: Type[T]) -> T:
        """
        Resolve a service instance.

        Args:
            interface: The interface type to resolve

        Returns:
            Instance of the requested service

        Raises:
            ValueError: If service is not registered or circular dependency detected
        """
        # Check for circular dependencies
        if interface in self._resolution_stack:
            raise ValueError(f"Circular dependency detected for {interface.__name__}")

        self._resolution_stack.add(interface)

        try:
            return self._resolve_internal(interface)
        finally:
            self._resolution_stack.discard(interface)

    def _resolve_internal(self, interface: Type[T]) -> T:
        """Internal resolution logic."""
        # Check factories first
        if interface in self._factories:
            return self._factories[interface]()

        # Check registered services
        if interface not in self._services:
            raise ValueError(f"Service {interface.__name__} not registered")

        service_info = self._services[interface]

        # Return existing singleton instance
        if service_info.singleton and service_info.instance is not None:
            return service_info.instance

        # Create new instance
        instance = self._create_instance(service_info.implementation)

        # Store singleton instance
        if service_info.singleton:
            service_info.instance = instance

        return instance

    def _create_instance(self, implementation: Any) -> Any:
        """Create an instance with constructor injection."""
        # If it's already an instance, return it
        if not inspect.isclass(implementation):
            return implementation

        # Get constructor parameters
        try:
            signature = inspect.signature(implementation.__init__)
            type_hints = get_type_hints(implementation.__init__)
        except (ValueError, AttributeError):
            # No constructor or no type hints, try to create without args
            return implementation()

        # Resolve constructor dependencies
        kwargs = {}
        for param_name, param in signature.parameters.items():
            if param_name == 'self':
                continue

            param_type = type_hints.get(param_name)
            if param_type is None:
                if param.default is not param.empty:
                    # Has default value, skip
                    continue
                else:
                    raise ValueError(
                        f"Cannot resolve parameter '{param_name}' for {implementation.__name__}: "
                        f"no type hint provided"
                    )

            # Resolve the dependency
            try:
                dependency = self.resolve(param_type)
                kwargs[param_name] = dependency
            except ValueError as e:
                if param.default is not param.empty:
                    # Has default value, skip
                    continue
                else:
                    raise ValueError(
                        f"Cannot resolve dependency '{param_name}' of type {param_type.__name__} "
                        f"for {implementation.__name__}: {e}"
                    )

        return implementation(**kwargs)

    def is_registered(self, interface: Type) -> bool:
        """Check if a service is registered."""
        return interface in self._services or interface in self._factories

    def get_registered_services(self) -> Dict[str, str]:
        """Get information about registered services."""
        info = {}

        for interface, service_info in self._services.items():
            impl_name = (
                service_info.implementation.__name__
                if inspect.isclass(service_info.implementation)
                else str(type(service_info.implementation).__name__)
            )
            lifecycle = "singleton" if service_info.singleton else "transient"
            info[interface.__name__] = f"{impl_name} ({lifecycle})"

        for interface in self._factories:
            info[interface.__name__] = "factory"

        return info

    def clear(self):
        """Clear all registered services."""
        self._services.clear()
        self._factories.clear()
        self._resolution_stack.clear()
        logger.debug("Container cleared")


# Global container instance
_container = Container()


def get_container() -> Container:
    """Get the global container instance."""
    return _container


def setup_container(container: Container) -> Container:
    """
    Set up the container with common service registrations.

    Args:
        container: The container to configure

    Returns:
        The configured container
    """
    # This will be called by the application startup to register services
    # For now, return the container as-is
    return container
