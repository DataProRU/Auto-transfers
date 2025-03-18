"""Type definitions for accounts models."""

from typing import Protocol


class UserProtocol(Protocol):
    """Protocol for User model."""

    id: int
    full_name: str
    phone: str
    role: str
    is_active: bool
    is_staff: bool
    is_superuser: bool
    date_joined: str
    last_login: str | None

    class Roles:
        """User roles."""

        USER = "user"
        ADMIN = "admin"
        STAFF = "staff"
