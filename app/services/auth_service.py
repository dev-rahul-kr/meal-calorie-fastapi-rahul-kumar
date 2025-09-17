from typing import Tuple
from app.ports.user_repository import UserRepository
from app.core import security

class AuthService:
    def __init__(self, users: UserRepository):
        self._users = users

    def register(self, *, first_name: str, last_name: str, email: str, raw_password: str):
        existing = self._users.get_by_email(email)
        if existing:
            raise ValueError("Email already registered")
        password_hash = security.hash_password(raw_password)
        return self._users.create(first_name, last_name, email, password_hash)

    def login(self, *, email: str, raw_password: str) -> Tuple[str, object]:
        user = self._users.get_by_email(email)
        if not user or not security.verify_password(raw_password, user.password_hash):
            raise ValueError("Invalid Credentials")
        token = security.create_access_token(subject=str(user.id), extra={"email": user.email})
        return token, user
