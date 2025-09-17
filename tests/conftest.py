# tests/conftest.py
import os

# --- set env EARLY (before importing app code) ---
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "testsecret")
os.environ.setdefault("USDA_API_KEY", "dummy")
os.environ.setdefault("RATE_LIMIT_PER_MIN", "10000")
os.environ.setdefault("LOGIN_RATE_LIMIT_PER_MIN", "10000")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.session import get_db
from app.main import app

@pytest.fixture(scope="session")
def engine():
    eng = create_engine(os.environ["DATABASE_URL"], future=True)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)

@pytest.fixture()
def db_session(engine):
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    db = SessionLocal()
    try:
        yield db
        db.rollback()
    finally:
        db.close()

@pytest.fixture(autouse=True)
def override_db(db_session):
    def _get_db():
        try:
            yield db_session
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise
    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture()
def client():
    return TestClient(app)
