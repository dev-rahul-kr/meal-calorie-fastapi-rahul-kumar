from typing import Mapping, Any, Optional
from app.adapters.db.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.core.security import hash_password

class FakeUSDAClient:
    def __init__(self, data: Mapping[str, Any] | None = None, err: Exception | None = None):
        self._data, self._err = data or {"foods": []}, err
    async def search(self, query: str, *, page_size: Optional[int] = None) -> Mapping[str, Any]:
        if self._err: raise self._err
        return self._data

def make_user(db, email="u1@example.com", password="pass12345"):
    repo = SqlAlchemyUserRepository(db)
    return repo.create("Rahul","T", email, hash_password(password))

def usda_food(**kw):
    base = {"description":"Chicken Salad","labelNutrients":{"calories":{"value":250}},
            "servingSize":100,"servingSizeUnit":"g","ingredients":"chicken, mayo"}
    base.update(kw); return base
