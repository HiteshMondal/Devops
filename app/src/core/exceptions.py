"""
Custom exception hierarchy.

OOP concept: inheritance. All app-specific errors derive from a common
base so callers can catch `AppError` broadly or a specific subtype
narrowly.
"""


class AppError(Exception):
    """Base class for all application errors."""


class NotFoundError(AppError):
    """Raised when a requested entity does not exist."""


class ValidationError(AppError):
    """Raised when input data fails validation."""


class CyclicDependencyError(AppError):
    """Raised when a deployment dependency graph contains a cycle."""


class CircuitOpenError(AppError):
    """Raised when an operation is rejected because the circuit breaker is open."""


class RateLimitExceededError(AppError):
    """Raised when a caller exceeds the allowed request rate."""