from typing import Protocol, Optional
from app.models.user import User

class UserRepository(Protocol):
    """Repository interface for user data persistence ."""

    def get_by_email(self, email: str) -> User | None:
        pass

    def create(self, first_name: str, last_name: str, email: str, password_hash: str) -> User:
        pass
