"""Type definitions for accounts models."""

from typing import Protocol


class UserProtocol(Protocol):
    """Protocol for User model."""

    id: int
    full_name: str
    phone: str
    role: str

    class Roles:
        """User roles."""

        USER = "user"
