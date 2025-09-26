"""
Strategy Pattern Exceptions for QuickPage

This module contains all the custom exceptions used by the strategy pattern
implementations. These exceptions provide specific error handling for different
types of strategy operations and failure modes.
"""


class StrategyError(Exception):
    """
    Base exception for strategy-related errors.

    All strategy-specific exceptions inherit from this base class,
    allowing for unified error handling across different strategy types.
    """

    pass


class TemplateError(StrategyError):
    """
    Base exception for template strategy errors.

    This is the parent class for all template-related errors including
    loading, parsing, validation, and rendering failures.
    """

    pass


class TemplateNotFoundError(TemplateError):
    """
    Exception raised when a template is not found.

    This exception is raised when a template strategy cannot locate
    the requested template file in any of the configured search paths.
    """

    pass


class TemplateLoadError(TemplateError):
    """
    Exception raised when a template cannot be loaded.

    This exception is raised when a template file exists but cannot be
    loaded due to syntax errors, encoding issues, or other loading problems.
    """

    pass


class TemplateRenderError(TemplateError):
    """
    Exception raised when template rendering fails.

    This exception is raised when template rendering fails due to missing
    variables, rendering logic errors, or other runtime issues.
    """

    pass


class ResourceError(StrategyError):
    """
    Base exception for resource strategy errors.

    This is the parent class for all resource-related errors including
    loading, metadata retrieval, and resource manipulation failures.
    """

    pass


class ResourceNotFoundError(ResourceError):
    """
    Exception raised when a resource is not found.

    This exception is raised when a resource strategy cannot locate
    the requested resource in any of the configured locations.
    """

    pass


class ResourceLoadError(ResourceError):
    """
    Exception raised when a resource cannot be loaded.

    This exception is raised when a resource exists but cannot be loaded
    due to permission issues, corruption, network errors, or other problems.
    """

    pass


class CacheError(StrategyError):
    """
    Base exception for cache strategy errors.

    This exception is raised when cache operations fail due to storage
    issues, serialization problems, or other cache-related errors.
    """

    pass
