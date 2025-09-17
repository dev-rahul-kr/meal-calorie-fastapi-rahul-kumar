from sqlalchemy import select
from sqlalchemy.orm import Session
from app.ports.user_repository import UserRepository
from app.models.user import User


class SqlAlchemyUserRepository(UserRepository):
    """Concrete implementation of UserRepository using SQLAlchemy."""

    def __init__(self, db: Session):
        self._db = db

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self._db.execute(stmt).scalar_one_or_none()

    def create(self, first_name: str, last_name: str, email: str, password_hash: str) -> User:
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=password_hash,
        )
        self._db.add(user)
        self._db.flush()
        return user
