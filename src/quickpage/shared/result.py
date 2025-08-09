"""
Result pattern for explicit error handling.

The Result pattern is a functional programming concept that represents
the result of an operation that can either succeed or fail, without
using exceptions for control flow.
"""

from typing import TypeVar, Generic, Union, Callable, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

T = TypeVar('T')  # Success type
E = TypeVar('E')  # Error type
U = TypeVar('U')  # Mapped type


class Result(Generic[T, E], ABC):
    """
    Abstract base class for Result types.

    A Result represents either a successful value (Ok) or an error (Err).
    This pattern allows for explicit error handling without exceptions.
    """

    @abstractmethod
    def is_ok(self) -> bool:
        """Return True if this is a successful result."""
        pass

    @abstractmethod
    def is_err(self) -> bool:
        """Return True if this is an error result."""
        pass

    @abstractmethod
    def unwrap(self) -> T:
        """
        Return the success value or raise an exception if this is an error.

        Raises:
            ValueError: If this is an Err result
        """
        pass

    @abstractmethod
    def unwrap_or(self, default: T) -> T:
        """Return the success value or the default if this is an error."""
        pass

    @abstractmethod
    def unwrap_or_else(self, func: Callable[[E], T]) -> T:
        """Return the success value or call func with the error."""
        pass

    @abstractmethod
    def map(self, func: Callable[[T], U]) -> 'Result[U, E]':
        """Transform the success value if this is Ok, otherwise return the error."""
        pass

    @abstractmethod
    def map_err(self, func: Callable[[E], U]) -> 'Result[T, U]':
        """Transform the error value if this is Err, otherwise return the success."""
        pass

    @abstractmethod
    def and_then(self, func: Callable[[T], 'Result[U, E]']) -> 'Result[U, E]':
        """Chain operations that return Results (flatMap/bind operation)."""
        pass


@dataclass(frozen=True)
class Ok(Result[T, E]):
    """
    Represents a successful result.

    Contains the success value of type T.
    """
    value: T

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def unwrap(self) -> T:
        return self.value

    def unwrap_or(self, default: T) -> T:
        return self.value

    def unwrap_or_else(self, func: Callable[[E], T]) -> T:
        return self.value

    def map(self, func: Callable[[T], U]) -> 'Result[U, E]':
        try:
            return Ok(func(self.value))
        except Exception as e:
            # If the mapping function raises an exception, convert to Err
            return Err(e)  # type: ignore

    def map_err(self, func: Callable[[E], U]) -> 'Result[T, U]':
        return Ok(self.value)  # type: ignore

    def and_then(self, func: Callable[[T], 'Result[U, E]']) -> 'Result[U, E]':
        try:
            return func(self.value)
        except Exception as e:
            return Err(e)  # type: ignore

    def __str__(self) -> str:
        return f"Ok({self.value})"

    def __repr__(self) -> str:
        return f"Ok({repr(self.value)})"


@dataclass(frozen=True)
class Err(Result[T, E]):
    """
    Represents an error result.

    Contains the error value of type E.
    """
    error: E

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def unwrap(self) -> T:
        raise ValueError(f"Called unwrap() on an Err result: {self.error}")

    def unwrap_or(self, default: T) -> T:
        return default

    def unwrap_or_else(self, func: Callable[[E], T]) -> T:
        return func(self.error)

    def map(self, func: Callable[[T], U]) -> 'Result[U, E]':
        return Err(self.error)  # type: ignore

    def map_err(self, func: Callable[[E], U]) -> 'Result[T, U]':
        try:
            return Err(func(self.error))
        except Exception as e:
            return Err(e)  # type: ignore

    def and_then(self, func: Callable[[T], 'Result[U, E]']) -> 'Result[U, E]':
        return Err(self.error)  # type: ignore

    def __str__(self) -> str:
        return f"Err({self.error})"

    def __repr__(self) -> str:
        return f"Err({repr(self.error)})"


# Convenience functions for creating Results
def ok(value: T) -> Result[T, Any]:
    """Create a successful Result."""
    return Ok(value)


def err(error: E) -> Result[Any, E]:
    """Create an error Result."""
    return Err(error)


def from_exception(func: Callable[[], T]) -> Result[T, Exception]:
    """
    Execute a function and return a Result, catching any exceptions.

    Args:
        func: Function to execute

    Returns:
        Ok with the function result, or Err with the caught exception
    """
    try:
        return Ok(func())
    except Exception as e:
        return Err(e)


async def from_async_exception(func: Callable[[], T]) -> Result[T, Exception]:
    """
    Execute an async function and return a Result, catching any exceptions.

    Args:
        func: Async function to execute

    Returns:
        Ok with the function result, or Err with the caught exception
    """
    try:
        result = await func()
        return Ok(result)
    except Exception as e:
        return Err(e)


def collect_results(results: list[Result[T, E]]) -> Result[list[T], E]:
    """
    Collect a list of Results into a single Result.

    If all Results are Ok, returns Ok with a list of all values.
    If any Result is Err, returns the first error encountered.

    Args:
        results: List of Results to collect

    Returns:
        Ok with list of values, or first Err encountered
    """
    values = []
    for result in results:
        if result.is_err():
            return result  # type: ignore
        values.append(result.unwrap())
    return Ok(values)


def partition_results(results: list[Result[T, E]]) -> tuple[list[T], list[E]]:
    """
    Partition a list of Results into successful values and errors.

    Args:
        results: List of Results to partition

    Returns:
        Tuple of (successful_values, errors)
    """
    successes = []
    errors = []

    for result in results:
        if result.is_ok():
            successes.append(result.unwrap())
        else:
            errors.append(result.error)

    return successes, errors


# Type alias for common Result patterns
StrResult = Result[str, str]
IntResult = Result[int, str]
BoolResult = Result[bool, str]
OptionalResult = Result[Optional[T], str]


# Export all public types and functions
__all__ = [
    'Result',
    'Ok',
    'Err',
    'ok',
    'err',
    'from_exception',
    'from_async_exception',
    'collect_results',
    'partition_results',
    'StrResult',
    'IntResult',
    'BoolResult',
    'OptionalResult'
]
